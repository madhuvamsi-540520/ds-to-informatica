"""Shared Claude API wrapper with rate limiting, cost tracking, and retries."""

import time
import yaml
import os
from pathlib import Path
import anthropic

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


class CostThresholdError(Exception):
    pass


class ClaudeClient:
    def __init__(self):
        self.config = _load_config()
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self._request_times: list[float] = []

    def call(
        self,
        prompt: str,
        accelerator_id: str,
        task_type: str = "design_analysis"
    ) -> dict:
        """
        Call Claude API with rate limiting, cost checking, and retries.
        Returns dict with: content, tokens_input, tokens_output, cost_usd, latency_seconds
        """
        cfg = self.config["claude"]
        cost_limit = self.config["cost_circuit_breaker"].get(
            accelerator_id.lower().replace("-", "").replace("ai", ""), 0.20
        )
        temperature = cfg["temperature"].get(task_type, 0.2)
        max_tokens = cfg["max_tokens"].get(
            {"basic_translation": "basic_translation",
             "cpp_rewriting": "cpp_rewriting",
             "design_review": "design_review",
             "dependency_analysis": "dependency_analysis"}.get(task_type, "design_review"),
            2048
        )

        self._rate_limit()

        last_error = None
        for attempt in range(cfg["retries"]):
            try:
                start = time.time()
                response = self.client.messages.create(
                    model=cfg["model"],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                latency = time.time() - start

                tokens_in = response.usage.input_tokens
                tokens_out = response.usage.output_tokens
                cost = (tokens_in * 3 + tokens_out * 15) / 1_000_000

                if cost > cost_limit:
                    raise CostThresholdError(
                        f"Cost ${cost:.4f} exceeds circuit breaker ${cost_limit} for {accelerator_id}"
                    )

                return {
                    "content": response.content[0].text,
                    "tokens_input": tokens_in,
                    "tokens_output": tokens_out,
                    "cost_usd": round(cost, 6),
                    "latency_seconds": round(latency, 2),
                    "model": cfg["model"]
                }

            except CostThresholdError:
                raise
            except anthropic.RateLimitError:
                wait = cfg["rate_limit"]["batch_delay_seconds"] * (2 ** attempt)
                time.sleep(min(wait, 300))
                last_error = "Rate limit"
            except anthropic.APITimeoutError:
                time.sleep(30)
                last_error = "Timeout"
            except Exception as e:
                last_error = str(e)
                if attempt < cfg["retries"] - 1:
                    time.sleep(10 * (attempt + 1))

        raise RuntimeError(f"Claude API failed after {cfg['retries']} retries: {last_error}")

    def _rate_limit(self):
        now = time.time()
        rpm = self.config["claude"]["rate_limit"]["requests_per_minute"]
        self._request_times = [t for t in self._request_times if now - t < 60]
        if len(self._request_times) >= rpm:
            sleep_for = 60 - (now - self._request_times[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._request_times.append(time.time())
