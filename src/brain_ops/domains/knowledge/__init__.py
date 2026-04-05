"""Knowledge operations domain."""

from brain_ops.domains.knowledge.capture import (
    CapturePlan,
    build_capture_body,
    build_capture_frontmatter,
    infer_capture_title,
    infer_capture_type,
    plan_capture_note,
)
from brain_ops.domains.knowledge.audit import (
    AuditNoteAnalysis,
    KNOWN_NOTE_TYPES,
    SYSTEM_LIKE_TYPES,
    accumulate_audit_note,
    analyze_audit_note,
    infer_audit_note_type,
    looks_like_moc_note,
)
from brain_ops.domains.knowledge.improvement import improve_body
from brain_ops.domains.knowledge.inbox import (
    InboxDisposition,
    infer_inbox_note_type,
    looks_structured,
    normalize_inbox_note,
    plan_inbox_disposition,
)
from brain_ops.domains.knowledge.linking import (
    build_note_terms,
    existing_wikilinks,
    insert_links,
    score_terms,
    suggest_link_candidate,
    tokenize,
)
from brain_ops.domains.knowledge.normalization import normalize_note_frontmatter
from brain_ops.domains.knowledge.promotion import (
    default_target_type,
    ensure_related_note_link,
    extract_sections,
    materialize_source_promotion,
    materialize_stub_promotion,
    normalize_promoted_title,
)
from brain_ops.domains.knowledge.projects import ProjectScaffoldNotePlan, plan_project_scaffold
from brain_ops.domains.knowledge.research import (
    merge_research_block,
    render_research_block,
    research_query_candidates,
    research_search_results,
    research_summary_text,
)
from brain_ops.domains.knowledge.review import (
    ReviewNoteAnalysis,
    accumulate_review_note,
    analyze_review_note,
    is_possible_orphan_note,
    is_stale_project_note,
)

__all__ = [
    "build_capture_body",
    "build_capture_frontmatter",
    "CapturePlan",
    "infer_capture_title",
    "infer_capture_type",
    "plan_capture_note",
    "accumulate_audit_note",
    "AuditNoteAnalysis",
    "analyze_audit_note",
    "accumulate_review_note",
    "analyze_review_note",
    "build_note_terms",
    "existing_wikilinks",
    "infer_audit_note_type",
    "infer_inbox_note_type",
    "InboxDisposition",
    "improve_body",
    "insert_links",
    "is_possible_orphan_note",
    "is_stale_project_note",
    "KNOWN_NOTE_TYPES",
    "looks_structured",
    "looks_like_moc_note",
    "default_target_type",
    "normalize_inbox_note",
    "normalize_note_frontmatter",
    "plan_inbox_disposition",
    "ensure_related_note_link",
    "extract_sections",
    "materialize_source_promotion",
    "materialize_stub_promotion",
    "merge_research_block",
    "normalize_promoted_title",
    "plan_project_scaffold",
    "ProjectScaffoldNotePlan",
    "render_research_block",
    "research_query_candidates",
    "research_search_results",
    "research_summary_text",
    "ReviewNoteAnalysis",
    "score_terms",
    "suggest_link_candidate",
    "SYSTEM_LIKE_TYPES",
    "tokenize",
]
