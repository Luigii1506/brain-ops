"""Source-aware semantic blocks for structured enrichment planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode, unquote, urlparse
from urllib.request import Request, urlopen

from .chunking import ContentChunk


@dataclass(slots=True, frozen=True)
class SourceSectionBlock:
    title: str
    section_path: list[str]
    level: int
    content_type: str
    text: str
    char_count: int
    source_profile: str


_WIKIPEDIA_NOISE_HEADINGS = {
    "véase también",
    "vease tambien",
    "referencias",
    "fuentes",
    "bibliografía",
    "bibliografia",
    "notas",
    "enlaces externos",
    "enlaces",
    "control de autoridades",
    "proyectos wikimedia",
    "categorías",
    "categorias",
    "categorías ocultas:",
    "categorias ocultas:",
    "material digital",
    "obras",
    "diccionarios y enciclopedias",
    "repositorios digitales",
    "cine",
}

_WIKIPEDIA_DROP_SELECTORS = (
    "script",
    "style",
    "sup.reference",
    "span.mw-editsection",
    "div.reflist",
    "ol.references",
    "div.refbegin",
    "div.navbox",
    "table.navbox",
    "table.vertical-navbox",
    "table.infobox",
    "table.sidebar",
    "div.metadata",
    "table.metadata",
    "div.catlinks",
    "div.printfooter",
    "div.sistersitebox",
    "div.thumb",
    "figure",
    "div.hatnote",
    "div.toc",
)


def detect_source_profile(url: str | None) -> str:
    if not url:
        return "generic_html"
    domain = urlparse(url).netloc.lower()
    if "wikipedia.org" in domain:
        return "wikipedia"
    return "generic_html"


def extract_source_section_blocks(
    *,
    url: str | None,
    html: str | None,
    article_title: str | None = None,
) -> list[SourceSectionBlock]:
    profile = detect_source_profile(url)
    if profile == "wikipedia":
        if html and not _looks_like_live_wikipedia_html(html):
            return extract_wikipedia_section_blocks(html, article_title=article_title)
        if url:
            blocks = extract_wikipedia_api_section_blocks(url, article_title=article_title)
            if blocks:
                return blocks
        if html:
            return extract_wikipedia_section_blocks(html, article_title=article_title)
    return []


def extract_planning_chunks(
    *,
    url: str | None,
    html: str | None,
    article_title: str | None = None,
) -> tuple[str, list[ContentChunk] | None]:
    profile = detect_source_profile(url)
    blocks = extract_source_section_blocks(
        url=url,
        html=html,
        article_title=article_title,
    )
    if not blocks:
        return profile, None
    return profile, section_blocks_to_chunks(blocks)


def extract_wikipedia_section_blocks(
    html: str,
    *,
    article_title: str | None = None,
) -> list[SourceSectionBlock]:
    try:
        from bs4 import BeautifulSoup, Tag
    except ImportError:
        return []

    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("div.mw-parser-output") or soup.select_one("main") or soup.body
    if root is None:
        return []

    for selector in _WIKIPEDIA_DROP_SELECTORS:
        for tag in root.select(selector):
            tag.decompose()

    blocks: list[SourceSectionBlock] = []
    heading_stack: list[str] = []
    current_title = "Lead"
    current_level = 1
    current_parts: list[str] = []

    def flush_current() -> None:
        nonlocal current_parts
        text = _normalize_block_text("\n".join(current_parts))
        title = current_title.strip() or "Lead"
        if len(text) < 80:
            current_parts = []
            return
        if _is_noise_heading(title):
            current_parts = []
            return
        section_path = list(heading_stack) if heading_stack else [title]
        blocks.append(SourceSectionBlock(
            title=title,
            section_path=section_path,
            level=current_level,
            content_type="lead" if title == "Lead" else "narrative_section",
            text=text,
            char_count=len(text),
            source_profile="wikipedia",
        ))
        current_parts = []

    def append_content_from_tag(child: Tag) -> None:
        if child.name == "p":
            text = _normalize_inline_text(child.get_text(" ", strip=True))
            if text:
                current_parts.append(text)
            return

        if child.name in {"ul", "ol"}:
            list_items = []
            for item in child.find_all("li", recursive=False):
                item_text = _normalize_inline_text(item.get_text(" ", strip=True))
                if item_text:
                    list_items.append(f"- {item_text}")
            if list_items:
                current_parts.append("\n".join(list_items))
            return

        if child.name in {"dl", "blockquote"}:
            definition_lines = []
            for item in child.find_all(["dt", "dd", "p"], recursive=False):
                item_text = _normalize_inline_text(item.get_text(" ", strip=True))
                if item_text:
                    definition_lines.append(item_text)
            if definition_lines:
                current_parts.append("\n".join(definition_lines))

    content_tags = {"p", "ul", "ol", "dl", "blockquote"}
    for child in root.find_all(True):
        if not isinstance(child, Tag):
            continue

        if child.name == "div" and any(
            css_class.startswith("mw-heading")
            for css_class in child.get("class", [])
        ):
            heading = child.find(["h2", "h3", "h4"])
            if heading is None:
                continue
            flush_current()
            title = _clean_section_title(heading.get_text(" ", strip=True))
            level = int(heading.name[1])
            current_title = title or "Lead"
            current_level = level
            heading_stack = _update_heading_stack(heading_stack, current_title, level)
            continue

        if child.name in {"h2", "h3", "h4"}:
            if (
                child.parent is not None
                and child.parent.name == "div"
                and any(css_class.startswith("mw-heading") for css_class in child.parent.get("class", []))
            ):
                continue
            flush_current()
            title = _clean_section_title(child.get_text(" ", strip=True))
            level = int(child.name[1])
            current_title = title or "Lead"
            current_level = level
            heading_stack = _update_heading_stack(heading_stack, current_title, level)
            continue

        if child.name not in content_tags:
            continue
        if _is_nested_content_tag(child, root):
            continue
        append_content_from_tag(child)

    flush_current()
    return blocks


def extract_wikipedia_api_section_blocks(
    url: str,
    *,
    article_title: str | None = None,
) -> list[SourceSectionBlock]:
    page_title = _wikipedia_page_title(url, article_title=article_title)
    if not page_title:
        return []

    try:
        tocdata = _fetch_wikipedia_parse_payload(page_title, prop="tocdata")
    except Exception:
        return []

    sections = tocdata.get("parse", {}).get("tocdata", {}).get("sections", [])
    if not isinstance(sections, list):
        return []

    blocks: list[SourceSectionBlock] = []
    lead_text = _fetch_wikipedia_section_text(page_title, section="0")
    if len(lead_text) >= 80:
        blocks.append(SourceSectionBlock(
            title="Lead",
            section_path=["Lead"],
            level=1,
            content_type="lead",
            text=lead_text,
            char_count=len(lead_text),
            source_profile="wikipedia",
        ))

    heading_stack: list[str] = []
    for section in sections:
        if not isinstance(section, dict):
            continue

        title = _clean_section_title(str(section.get("line", "")))
        if not title or _is_noise_heading(title):
            continue

        try:
            level = int(section.get("hLevel") or section.get("level") or 2)
        except (TypeError, ValueError):
            level = 2
        heading_stack = _update_heading_stack(heading_stack, title, level)

        section_index = str(section.get("index", "")).strip()
        if not section_index:
            continue
        text = _fetch_wikipedia_section_text(page_title, section=section_index)
        if len(text) < 80:
            continue

        blocks.append(SourceSectionBlock(
            title=title,
            section_path=list(heading_stack),
            level=level,
            content_type="narrative_section",
            text=text,
            char_count=len(text),
            source_profile="wikipedia",
        ))

    return blocks


def section_blocks_to_chunks(blocks: list[SourceSectionBlock]) -> list[ContentChunk]:
    chunks: list[ContentChunk] = []
    for position, block in enumerate(blocks, 1):
        heading = " / ".join(block.section_path) if len(block.section_path) > 1 else block.title
        chunks.append(ContentChunk(
            heading=heading,
            text=block.text,
            char_count=block.char_count,
            position=position,
        ))
    return chunks


def chunk_sidecar_path(raw_file: Path) -> Path:
    return raw_file.with_suffix(raw_file.suffix + ".chunks.json")


def save_chunk_sidecar(raw_file: Path, *, source_profile: str, chunks: list[ContentChunk]) -> Path:
    sidecar = chunk_sidecar_path(raw_file)
    payload = {
        "source_profile": source_profile,
        "chunks": [
            {
                "heading": chunk.heading,
                "text": chunk.text,
                "char_count": chunk.char_count,
                "position": chunk.position,
                "priority": chunk.priority,
            }
            for chunk in chunks
        ],
    }
    sidecar.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return sidecar


def load_chunk_sidecar(raw_file: Path) -> tuple[str | None, list[ContentChunk] | None]:
    sidecar = chunk_sidecar_path(raw_file)
    if not sidecar.exists():
        return None, None
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    chunks = [
        ContentChunk(
            heading=str(item.get("heading", "")),
            text=str(item.get("text", "")),
            char_count=int(item.get("char_count", 0)),
            position=int(item.get("position", 0)),
            priority=str(item.get("priority", "medium")),
        )
        for item in data.get("chunks", [])
    ]
    return data.get("source_profile"), chunks


def _clean_section_title(value: str) -> str:
    text = value.replace("[ editar ]", "").replace("[editar]", "").strip()
    text = " ".join(text.split())
    return text


def _looks_like_live_wikipedia_html(html: str) -> bool:
    lowered = html.lower()
    return "wikipedia, la enciclopedia libre" in lowered or "wikipedia, the free encyclopedia" in lowered


def _wikipedia_page_title(url: str, *, article_title: str | None = None) -> str | None:
    parsed = urlparse(url)
    if "/wiki/" not in parsed.path:
        slug = ""
    else:
        _, _, slug = parsed.path.partition("/wiki/")
        slug = slug.strip("/")
    if slug:
        return unquote(slug)

    if article_title:
        cleaned = article_title.split(" - Wikipedia", 1)[0].strip()
        cleaned = cleaned.split(" - Wikipedia,", 1)[0].strip()
        if cleaned:
            return cleaned.replace(" ", "_")
    return None


def _fetch_wikipedia_parse_payload(page_title: str, *, prop: str, section: str | None = None) -> dict:
    base = "https://es.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": page_title,
        "prop": prop,
        "format": "json",
        "formatversion": "2",
    }
    if section is not None:
        params["section"] = section
    query = f"{base}?{urlencode(params)}"
    req = Request(query, headers={"User-Agent": "brain-ops/1.0"})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_wikipedia_section_text(page_title: str, *, section: str) -> str:
    try:
        payload = _fetch_wikipedia_parse_payload(page_title, prop="text", section=section)
    except Exception:
        return ""
    html = payload.get("parse", {}).get("text", "")
    if not isinstance(html, str) or not html.strip():
        return ""
    return _extract_wikipedia_fragment_text(html)


def _extract_wikipedia_fragment_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup, Tag
    except ImportError:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("div.mw-parser-output") or soup.body or soup
    for selector in _WIKIPEDIA_DROP_SELECTORS:
        for tag in root.select(selector):
            tag.decompose()

    parts: list[str] = []
    for child in root.find_all(True):
        if not isinstance(child, Tag):
            continue
        if child.name not in {"p", "ul", "ol", "dl", "blockquote"}:
            continue
        if _is_nested_content_tag(child, root):
            continue
        _append_content_from_tag(child, parts)

    return _normalize_block_text("\n".join(parts))


def _append_content_from_tag(child, current_parts: list[str]) -> None:
    if child.name == "p":
        text = _normalize_inline_text(child.get_text(" ", strip=True))
        if text:
            current_parts.append(text)
        return

    if child.name in {"ul", "ol"}:
        list_items = []
        for item in child.find_all("li", recursive=False):
            item_text = _normalize_inline_text(item.get_text(" ", strip=True))
            if item_text:
                list_items.append(f"- {item_text}")
        if list_items:
            current_parts.append("\n".join(list_items))
        return

    if child.name in {"dl", "blockquote"}:
        definition_lines = []
        for item in child.find_all(["dt", "dd", "p"], recursive=False):
            item_text = _normalize_inline_text(item.get_text(" ", strip=True))
            if item_text:
                definition_lines.append(item_text)
        if definition_lines:
            current_parts.append("\n".join(definition_lines))


def _is_noise_heading(title: str) -> bool:
    lowered = title.strip().lower()
    if lowered in _WIKIPEDIA_NOISE_HEADINGS:
        return True
    if lowered.startswith("categorías"):
        return True
    if lowered.startswith("categorias"):
        return True
    return False


def _normalize_inline_text(text: str) -> str:
    return " ".join(text.split())


def _normalize_block_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    compact = [line for line in lines if line]
    return "\n".join(compact).strip()


def _update_heading_stack(stack: list[str], title: str, level: int) -> list[str]:
    if level <= 2:
        return [title]
    if level == 3:
        parent = stack[:1]
        return parent + [title]
    parent = stack[:2]
    return parent + [title]


def _is_nested_content_tag(tag, root) -> bool:
    parent = tag.parent
    while parent is not None and parent is not root:
        if parent.name in {"p", "ul", "ol", "dl", "blockquote", "figure", "table"}:
            return True
        if (
            parent.name == "div"
            and any(css_class.startswith("mw-heading") for css_class in parent.get("class", []))
        ):
            return True
        parent = parent.parent
    return False


__all__ = [
    "SourceSectionBlock",
    "chunk_sidecar_path",
    "detect_source_profile",
    "extract_planning_chunks",
    "extract_source_section_blocks",
    "extract_wikipedia_section_blocks",
    "load_chunk_sidecar",
    "save_chunk_sidecar",
    "section_blocks_to_chunks",
]
