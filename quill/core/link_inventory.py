from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LinkRecord:
    target: str
    label: str
    kind: str


@dataclass(frozen=True, slots=True)
class ImageAltRecord:
    source: str
    alt_text: str
    kind: str


@dataclass(frozen=True, slots=True)
class LinkInventory:
    links: tuple[LinkRecord, ...]
    images: tuple[ImageAltRecord, ...]


_MD_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_MD_LINK_PATTERN = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")
_HTML_LINK_PATTERN = re.compile(r"<a[^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", re.IGNORECASE)
_HTML_IMG_PATTERN = re.compile(r"<img[^>]*>", re.IGNORECASE)
_HTML_ATTR_PATTERN = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)=['\"]([^'\"]*)['\"]")


def collect_link_inventory(text: str) -> LinkInventory:
    links: list[LinkRecord] = []
    images: list[ImageAltRecord] = []
    for alt, source in _MD_IMAGE_PATTERN.findall(text):
        images.append(ImageAltRecord(source=source, alt_text=alt, kind="markdown-image"))
    for label, target in _MD_LINK_PATTERN.findall(text):
        links.append(LinkRecord(target=target, label=label, kind="markdown-link"))
    for target, raw_label in _HTML_LINK_PATTERN.findall(text):
        label = re.sub(r"<[^>]+>", "", raw_label).strip()
        links.append(LinkRecord(target=target, label=label or target, kind="html-link"))
    for raw_img in _HTML_IMG_PATTERN.findall(text):
        attrs = {name.lower(): value for name, value in _HTML_ATTR_PATTERN.findall(raw_img)}
        source = attrs.get("src", "")
        if not source:
            continue
        images.append(
            ImageAltRecord(
                source=source,
                alt_text=attrs.get("alt", ""),
                kind="html-image",
            )
        )
    return LinkInventory(links=tuple(links), images=tuple(images))


def render_link_inventory_report(inventory: LinkInventory) -> str:
    lines = ["Link inventory and alt-text catalog", ""]
    lines.append(f"Links: {len(inventory.links)}")
    for index, link in enumerate(inventory.links, start=1):
        lines.append(f"{index}. [{link.kind}] {link.label} -> {link.target}")
    lines.append("")
    lines.append(f"Images: {len(inventory.images)}")
    for index, image in enumerate(inventory.images, start=1):
        alt = image.alt_text or "(missing alt text)"
        lines.append(f"{index}. [{image.kind}] {image.source} | alt: {alt}")
    return "\n".join(lines)
