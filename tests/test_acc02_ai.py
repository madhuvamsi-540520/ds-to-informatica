"""ACC-02-AI test cases from spec Section 7.2 (T-02-001 through T-02-010)."""

import pytest
from datetime import datetime
from migrator.accelerators.acc02_basic import translate, _try_lookup, _load_basic_map
from migrator.core.models import Acc02Input, ColumnDef
from migrator.core.validator import InputValidationError


def _make_request(code: str, complexity: str = "SIMPLE") -> Acc02Input:
    return Acc02Input(
        job_id="TEST_JOB",
        basic_code=code,
        column_context={
            "input_columns": [ColumnDef(name="Customer_Name", type="VARCHAR")],
            "output_columns": [ColumnDef(name="Customer_Name", type="VARCHAR")]
        },
        complexity_level=complexity
    )


# T-02-001: Simple Trim
def test_trim_translates_via_lookup():
    fn_map = _load_basic_map()
    result, mappings = _try_lookup("Trim(Customer_Name)", fn_map)
    assert result == "LTRIM(RTRIM(Customer_Name))"
    assert len(mappings) == 1
    assert mappings[0].confidence == 100


# T-02-002: Nested Trim + Upcase
def test_upcase_translates_via_lookup():
    fn_map = _load_basic_map()
    result, _ = _try_lookup("Upcase(Status_Code)", fn_map)
    assert result == "UPPER(Status_Code)"


# T-02-003: IsNull
def test_isnull_translates_via_lookup():
    fn_map = _load_basic_map()
    result, _ = _try_lookup("IsNull(Middle_Name)", fn_map)
    assert result == "ISNULL(Middle_Name)"


# T-02-005: DateDiff
def test_datediff_in_lookup():
    fn_map = _load_basic_map()
    assert "DateDiff" in fn_map


# T-02-008: Empty string validation
def test_empty_basic_code_raises_error():
    from migrator.core.validator import validate_basic_code
    with pytest.raises(InputValidationError) as exc:
        validate_basic_code("")
    assert "non-empty" in str(exc.value)


# T-02-009: Code exceeding max length
def test_code_too_long_raises_error():
    from migrator.core.validator import validate_basic_code
    with pytest.raises(InputValidationError) as exc:
        validate_basic_code("x" * 1001)
    assert "1000" in str(exc.value)


# T-02-010: Change function in lookup
def test_change_function_in_lookup():
    fn_map = _load_basic_map()
    assert "Change" in fn_map
    assert "REPLACESTR" in fn_map["Change"]


# Confidence threshold enforces human review
def test_low_confidence_requires_human_review():
    from migrator.core.validator import validate_acc02_output
    import pytest
    with pytest.raises(Exception):
        validate_acc02_output({
            "confidence_level": 50,
            "requires_human_review": False
        }, confidence_threshold=80)


# Lookup table covers all spec-mentioned functions
def test_all_spec_functions_in_lookup():
    fn_map = _load_basic_map()
    required = ["Trim", "Upcase", "Downcase", "Len", "Left", "Right", "IsNull"]
    for fn in required:
        assert fn in fn_map, f"Missing function: {fn}"


# Simple function does not call Claude
def test_simple_expression_no_api_call():
    req = _make_request("Trim(Name)")
    output = translate(req, client=None)
    assert output.translated_expression is not None
    assert output.api_call_metadata is None
    assert output.confidence_level == 100
    assert output.requires_human_review is False
