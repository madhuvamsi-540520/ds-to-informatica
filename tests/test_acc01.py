"""ACC-01 test cases from spec Section 7.2."""

import pytest
from migrator.core.dsx_parser import parse
from migrator.accelerators.acc01_classifier import classify, load_stage_mapping

FIXTURE = "tests/fixtures/sample.dsx"


def export():
    return parse(FIXTURE)


def test_known_stage_maps_correctly():
    mapping = load_stage_mapping()
    assert mapping["Sequential File"]["idmc_equivalent"] == "Flat File Connector"
    assert mapping["Sequential File"]["equivalency"] == "Direct"


def test_transformer_maps_to_expression():
    mapping = load_stage_mapping()
    assert mapping["Transformer"]["idmc_equivalent"] == "Expression Transformation"


def test_custom_stage_flagged_as_manual():
    mapping = load_stage_mapping()
    assert mapping["Custom Stage"]["equivalency"] == "Manual"
    assert mapping["Custom Stage"]["action"] == "Rewrite"


def test_classify_produces_rows(tmp_path):
    exp = export()
    rows = classify(exp, str(tmp_path / "out.csv"))
    assert len(rows) > 0
    for row in rows:
        assert "stage_name" in row
        assert "idmc_equivalent" in row
        assert "action" in row


def test_classify_detects_basic_routines(tmp_path):
    exp = export()
    rows = classify(exp, str(tmp_path / "out.csv"))
    basic_rows = [r for r in rows if r["has_basic_routines"]]
    assert len(basic_rows) > 0


def test_classify_detects_custom_operators(tmp_path):
    exp = export()
    rows = classify(exp, str(tmp_path / "out.csv"))
    custom_rows = [r for r in rows if r["has_custom_operator"]]
    assert len(custom_rows) > 0


def test_unknown_stage_returns_manual_review(tmp_path):
    from migrator.core.dsx_parser import DSXExport, DSXJob, DSXStage
    exp = DSXExport(jobs=[DSXJob(
        name="TEST_JOB", job_type="PARALLEL_JOB",
        stages=[DSXStage(name="UNKNOWN_STAGE", stage_type="SomeUknownStageXYZ")]
    )])
    rows = classify(exp, str(tmp_path / "out.csv"))
    assert rows[0]["action"] == "Review"
    assert rows[0]["equivalency"] == "Manual"


def test_aggregator_maps_correctly():
    mapping = load_stage_mapping()
    result = mapping.get("Aggregator")
    assert result is not None
    assert result["idmc_equivalent"] == "Aggregator Transformation"


def test_join_maps_to_joiner():
    mapping = load_stage_mapping()
    assert mapping["Join"]["idmc_equivalent"] == "Joiner Transformation"


def test_scd_maps_directly():
    mapping = load_stage_mapping()
    assert mapping["Slowly Changing Dimension"]["equivalency"] == "Direct"


def test_job_flags_generated(tmp_path):
    from migrator.accelerators.acc01_classifier import get_job_flags
    exp = export()
    rows = classify(exp, str(tmp_path / "out.csv"))
    flags = get_job_flags(rows)
    assert len(flags) > 0
    for job_name, flag in flags.items():
        assert "has_basic_routines" in flag
        assert "has_custom_operator" in flag
