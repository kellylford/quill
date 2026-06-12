"""Tests for the context-sensitive help infrastructure."""

from __future__ import annotations

from quill.core.help.renderer import load_topics


def test_topics_json_loads() -> None:
    """topics.json must load without errors and return at least one topic."""
    topics = load_topics()
    assert topics, "topics.json loaded no topics"


def test_all_topics_have_required_fields() -> None:
    """Every topic must have a non-empty id, title, and body."""
    topics = load_topics()
    for topic_id, topic in topics.items():
        assert topic.id, f"Topic {topic_id!r} has empty id"
        assert topic.title, f"Topic {topic_id!r} has empty title"
        assert topic.body, f"Topic {topic_id!r} has empty body"


def test_topic_render_live() -> None:
    topics = load_topics()
    for topic in topics.values():
        rendered = topic.render(mode="live")
        assert topic.title in rendered


def test_topic_render_doc() -> None:
    topics = load_topics()
    for topic in topics.values():
        rendered = topic.render(mode="doc")
        assert "###" in rendered
