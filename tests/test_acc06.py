"""ACC-06 complexity scorer tests."""

import pytest
from migrator.core.dsx_parser import DSXExport, DSXJob, DSXStage
from migrator.accelerators.acc06_scorer import score_job, score_all


def _make_job(name="TEST", job_type="PARALLEL_JOB", stages=None) -> DSXJob:
    return DSXJob(name=name, job_type=job_type, stages=stages or [])


def _make_stage(has_custom=False, routines=None) -> DSXStage:
    return DSXStage(
        name="S1", stage_type="Transformer",
        has_custom_operator=has_custom,
        basic_routines=routines or []
    )


def _cfg():
    return {
        "points_per_stage": 1,
        "points_per_custom_operator": 5,
        "points_per_basic_routine": 3,
        "points_per_sequence_job": 2,
        "complex_threshold": 30,
        "high_complexity_threshold": 50
    }


def test_simple_job_scores_low():
    job = _make_job(stages=[_make_stage() for _ in range(3)])
    result = score_job(job, _cfg())
    assert result["score"] == 3
    assert result["complexity"] == "SIMPLE"
    assert result["requires_claude_review"] is False


def test_custom_operator_adds_five_points():
    job = _make_job(stages=[_make_stage(has_custom=True)])
    result = score_job(job, _cfg())
    assert result["score"] == 6  # 1 stage + 5 custom op


def test_basic_routine_adds_three_points():
    job = _make_job(stages=[_make_stage(routines=["Trim(x)"])])
    result = score_job(job, _cfg())
    assert result["score"] == 4  # 1 stage + 3 routine


def test_sequence_job_adds_two_points():
    job = _make_job(job_type="SEQUENCE_JOB", stages=[_make_stage()])
    result = score_job(job, _cfg())
    assert result["score"] == 3  # 1 stage + 2 sequence


def test_complex_job_flagged_for_claude_review():
    stages = [_make_stage(has_custom=True, routines=["x"]) for _ in range(5)]
    job = _make_job(stages=stages)
    result = score_job(job, _cfg())
    assert result["score"] >= 30
    assert result["requires_claude_review"] is True


def test_high_complexity_classification():
    stages = [_make_stage(has_custom=True, routines=["x", "y"]) for _ in range(7)]
    job = _make_job(stages=stages)
    result = score_job(job, _cfg())
    assert result["complexity"] == "HIGH"


def test_score_all_returns_one_per_job(tmp_path):
    export = DSXExport(jobs=[
        _make_job("JOB_A", stages=[_make_stage()]),
        _make_job("JOB_B", stages=[_make_stage(), _make_stage()])
    ])
    results = score_all(export, str(tmp_path))
    assert len(results) == 2


def test_flags_set_correctly():
    job = _make_job(stages=[_make_stage(has_custom=True, routines=["x"])])
    result = score_job(job, _cfg())
    assert result["has_custom_operators"] is True
    assert result["has_basic_routines"] is True


def test_empty_job_scores_zero():
    job = _make_job(stages=[])
    result = score_job(job, _cfg())
    assert result["score"] == 0
    assert result["complexity"] == "SIMPLE"


def test_medium_complexity():
    # 4 stages with 1 routine each = 4×(1+3) = 16 pts → MEDIUM (10–29)
    job = _make_job(stages=[_make_stage(routines=["x"]) for _ in range(4)])
    result = score_job(job, _cfg())
    assert result["complexity"] == "MEDIUM"
