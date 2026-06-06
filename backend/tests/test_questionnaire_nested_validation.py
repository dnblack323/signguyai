"""
Unit tests for questionnaire submission validation helpers.

Covers the nested-section walk, conditional visibility evaluation, and
empty-answer detection used by POST /questionnaires/public/{id}/submit.
"""

from routes.questionnaires import (
    iter_questionnaire_questions,
    _answer_is_empty,
    _question_is_visible,
)


def test_iter_walks_top_level_and_sections():
    q = {
        "questions": [{"id": "a", "type": "text", "label": "A"}],
        "sections": [
            {"title": "S1", "questions": [{"id": "b", "type": "text", "label": "B"}]},
            {"title": "S2", "questions": [{"id": "c", "type": "email", "label": "C"}]},
        ],
    }
    ids = [item["id"] for item in iter_questionnaire_questions(q)]
    assert ids == ["a", "b", "c"]


def test_iter_handles_missing_keys():
    assert list(iter_questionnaire_questions({})) == []
    assert list(iter_questionnaire_questions({"questions": None, "sections": None})) == []


def test_answer_is_empty():
    assert _answer_is_empty(None)
    assert _answer_is_empty("")
    assert _answer_is_empty("   ")
    assert _answer_is_empty([])
    assert _answer_is_empty({})
    assert not _answer_is_empty("x")
    assert not _answer_is_empty(["x"])
    assert not _answer_is_empty(0)  # numeric zero is a real answer


def test_visibility_no_conditional_is_visible():
    assert _question_is_visible({"id": "q"}, {})


def test_visibility_equals():
    q = {"id": "q", "conditional": {"depends_on": "p", "operator": "equals", "value": "yes"}}
    assert _question_is_visible(q, {"p": "yes"})
    assert not _question_is_visible(q, {"p": "no"})
    assert not _question_is_visible(q, {})


def test_visibility_not_equals():
    q = {"id": "q", "conditional": {"depends_on": "p", "operator": "not_equals", "value": "yes"}}
    assert _question_is_visible(q, {"p": "no"})
    assert not _question_is_visible(q, {"p": "yes"})


def test_visibility_contains_list_and_string():
    q = {"id": "q", "conditional": {"depends_on": "p", "operator": "contains", "value": "banner"}}
    assert _question_is_visible(q, {"p": ["banner", "sign"]})
    assert _question_is_visible(q, {"p": "i want a banner please"})
    assert not _question_is_visible(q, {"p": ["sign"]})


def test_visibility_numeric_operators():
    gt = {"id": "q", "conditional": {"depends_on": "p", "operator": "greater_than", "value": 10}}
    lt = {"id": "q", "conditional": {"depends_on": "p", "operator": "less_than", "value": 10}}
    assert _question_is_visible(gt, {"p": 11})
    assert not _question_is_visible(gt, {"p": 5})
    assert _question_is_visible(lt, {"p": 5})
    assert not _question_is_visible(lt, {"p": 50})
    # Non-numeric answer fails closed for numeric operators.
    assert not _question_is_visible(gt, {"p": "abc"})


def test_visibility_unknown_operator_fails_open():
    q = {"id": "q", "conditional": {"depends_on": "p", "operator": "weird", "value": 1}}
    assert _question_is_visible(q, {"p": 1})
