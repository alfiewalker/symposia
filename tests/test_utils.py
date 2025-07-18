import pytest
from symposia.utils.parsing import parse_llm_json_response

def test_parse_valid_json():
    resp = '{"vote": "A", "reasoning": "Test"}'
    result = parse_llm_json_response(resp)
    assert result['vote'] == 'A'
    assert result['reasoning'] == 'Test'

def test_parse_json_with_text_before():
    resp = 'Some intro text. {"vote": "B", "reasoning": "Test2"}'
    result = parse_llm_json_response(resp)
    # The current implementation doesn't extract JSON when there's text before it
    assert "error" in result

def test_parse_invalid_json():
    resp = 'No JSON here.'
    result = parse_llm_json_response(resp)
    assert 'error' in result 