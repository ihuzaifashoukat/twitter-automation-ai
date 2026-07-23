"""Tests for xuse.core.llm_service.parsing.extract_json_from_response_text."""

from xuse.core.llm_service.parsing import extract_json_from_response_text


class TestFencedBlocks:
    def test_json_fence_with_surrounding_prose(self):
        text = 'Here is the analysis:\n```json\n{"relevance": 0.9, "sentiment": "positive"}\n```\nHope that helps!'
        data, err = extract_json_from_response_text(text)
        assert err is None
        assert data == {"relevance": 0.9, "sentiment": "positive"}

    def test_fence_language_tag_is_case_insensitive(self):
        data, err = extract_json_from_response_text('```JSON\n{"a": 2}\n```')
        assert err is None
        assert data == {"a": 2}

    def test_first_fence_wins(self):
        text = '```json {"a": 1}``` and then ```json {"b": 2}```'
        data, err = extract_json_from_response_text(text)
        assert err is None
        assert data == {"a": 1}

    def test_fence_takes_precedence_over_prose_braces(self):
        text = 'broken {not json} trailing ```json\n{"ok": true}\n```'
        data, err = extract_json_from_response_text(text)
        assert err is None
        assert data == {"ok": True}


class TestProseEmbeddedJson:
    def test_brace_balanced_extraction_from_prose(self):
        text = 'Sure, here you go: {"action": "reply", "score": 3} — done.'
        data, err = extract_json_from_response_text(text)
        assert err is None
        assert data == {"action": "reply", "score": 3}

    def test_nested_braces_balanced(self):
        text = 'Result: {"outer": {"inner": [1, 2], "s": "x"}, "n": 1} bye'
        data, err = extract_json_from_response_text(text)
        assert err is None
        assert data == {"outer": {"inner": [1, 2], "s": "x"}, "n": 1}

    def test_object_inside_top_level_array_yields_inner_object(self):
        # The extractor scans for '{' only; an array-wrapped object yields the object.
        data, err = extract_json_from_response_text('[{"a": 1}]')
        assert err is None
        assert data == {"a": 1}


class TestCleanupFallbacks:
    def test_smart_quotes_replaced(self):
        text = '{"summary": “great thread”, "score": 5}'
        data, err = extract_json_from_response_text(text)
        assert err is None
        assert data == {"summary": "great thread", "score": 5}

    def test_stray_backticks_removed(self):
        data, err = extract_json_from_response_text('{"count": `7`}')
        assert err is None
        assert data == {"count": 7}

    def test_smart_quotes_inside_fenced_block(self):
        text = '```json\n{"text": “quoted”}\n```'
        data, err = extract_json_from_response_text(text)
        assert err is None
        assert data == {"text": "quoted"}


class TestGiveUpPaths:
    def test_empty_response(self):
        data, err = extract_json_from_response_text("")
        assert data is None
        assert err == "Empty response"

    def test_no_json_candidate(self):
        data, err = extract_json_from_response_text("plain prose, no json at all")
        assert data is None
        assert err == "No JSON candidate found in response"

    def test_top_level_array_without_object_has_no_candidate(self):
        data, err = extract_json_from_response_text("[1, 2, 3]")
        assert data is None
        assert err == "No JSON candidate found in response"

    def test_malformed_candidate_reports_parse_failure(self):
        data, err = extract_json_from_response_text('{"a": 1,,}')
        assert data is None
        assert err is not None
        assert err.startswith("JSON parse failed:")

    def test_unbalanced_braces_report_parse_failure(self):
        data, err = extract_json_from_response_text('{"a": {"b": 1}')
        assert data is None
        assert err is not None
