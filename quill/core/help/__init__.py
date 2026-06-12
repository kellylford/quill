"""QUILL context-sensitive help system.

Provides the topic registry and renderer used by F1 (control help) and
Ctrl+F1 (user guide). The topic data lives in ``topics.json`` and is
loaded once at startup.
"""

from __future__ import annotations

from quill.core.help.renderer import HelpRenderer, HelpTopic, load_topics

__all__ = ["HelpRenderer", "HelpTopic", "load_topics"]
