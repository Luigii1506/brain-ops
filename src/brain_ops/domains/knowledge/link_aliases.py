"""Link alias resolution — redirect ambiguous wikilinks to canonical entities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


# =========================================================
# ALIASES PARA WIKI HISTÓRICA
# =========================================================
#
# 3 niveles de confianza:
#
# 1) SAFE_LINK_ALIASES — se aplican automáticamente con `brain fix-links`
# 2) SPELLING_VARIANTS — variantes ortográficas, sin acento, transliteraciones
# 3) RISKY_ALIASES — casos ambiguos, NO aplicar sin contexto
#
# Regla: no incluir self-mappings ("Esparta": "Esparta")
#
# Ejemplo en Obsidian:
#   [[Persia]] → [[Imperio Persa|Persia]]
#   [[Alejandro]] → [[Alejandro Magno|Alejandro]]
# =========================================================


def _drop_identity(alias_map: dict[str, str]) -> dict[str, str]:
    """Elimina entradas donde alias == canonical."""
    return {a: c for a, c in alias_map.items() if a.strip() != c.strip()}


# ---------------------------------------------------------
# SAFE — se aplican automáticamente
# ---------------------------------------------------------

SAFE_LINK_ALIASES: dict[str, str] = _drop_identity({
    # IMPERIOS / REINOS / ESTADOS
    "Persia": "Imperio Persa",
    "Imperio persa": "Imperio Persa",
    "Imperio Aqueménida": "Imperio Persa",
    "Imperio aqueménida": "Imperio Persa",
    "Imperio aquemenida": "Imperio Persa",
    "Aqueménidas": "Imperio Persa",
    "Aqueménida": "Imperio Persa",

    "Imperio sasánida": "Imperio Sasánida",
    "Imperio sasanida": "Imperio Sasánida",
    "Sasánidas": "Imperio Sasánida",
    "Sasanidas": "Imperio Sasánida",

    "Partia": "Imperio Parto",
    "Imperio parto": "Imperio Parto",
    "Partos": "Imperio Parto",

    "Asiria": "Imperio Asirio",
    "Imperio asirio": "Imperio Asirio",
    "Neoasiria": "Imperio Neoasirio",
    "Imperio neoasirio": "Imperio Neoasirio",

    # "Babilonia" es ambiguo (ciudad vs imperio) — movido a RISKY
    "Imperio babilónico": "Imperio Babilónico",
    "Imperio babilonico": "Imperio Babilónico",
    "Neobabilonia": "Imperio Neobabilónico",
    "Imperio neobabilónico": "Imperio Neobabilónico",
    "Imperio neobabilonico": "Imperio Neobabilónico",
    "Caldea": "Imperio Neobabilónico",

    "Sumer": "Civilización sumeria",
    "Sumeria": "Civilización sumeria",
    "Acad": "Imperio acadio",
    "Akkad": "Imperio acadio",
    "Imperio acadio": "Imperio acadio",

    "Hititas": "Imperio Hitita",
    "Imperio hitita": "Imperio Hitita",
    "Mitani": "Reino de Mitani",
    "Urartu": "Reino de Urartu",
    "Elam": "Civilización elamita",

    # "Bizancio" es ambiguo (ciudad antigua vs imperio) — movido a RISKY
    "Imperio bizantino": "Imperio Bizantino",
    "Imperio romano de oriente": "Imperio Bizantino",

    "Cartago": "Imperio Cartaginés",
    "Cártago": "Imperio Cartaginés",
    "Imperio cartaginés": "Imperio Cartaginés",
    "Imperio cartagines": "Imperio Cartaginés",

    # "Macedonia" NO incluido — la nota se llama Macedonia.md y ya es la entidad correcta
    "Reino macedonio": "Macedonia",
    "Reino de Macedonia": "Macedonia",  # redirect inverso: si alguien escribe el nombre largo
    "Epiro": "Reino de Epiro",
    "Ponto": "Reino del Ponto",
    "Pérgamo": "Reino de Pérgamo",
    "Pergamo": "Reino de Pérgamo",
    "Capadocia": "Reino de Capadocia",
    "Bitinia": "Reino de Bitinia",

    "Imperio seléucida": "Imperio seléucida",
    "Imperio seleucida": "Imperio seléucida",
    "Seléucidas": "Imperio seléucida",
    "Seleucidas": "Imperio seléucida",
    "Reino seléucida": "Imperio seléucida",
    "Reino seleucida": "Imperio seléucida",

    "Imperio ptolemaico": "Reino ptolemaico",
    "Ptolemaicos": "Reino ptolemaico",
    "Egipto ptolemaico": "Reino ptolemaico",

    "Liga Délica": "Liga de Delos",
    "Liga Delica": "Liga de Delos",
    "Liga aquea": "Liga Aquea",
    "Liga etolia": "Liga Etolia",
    "Liga corintia": "Liga de Corinto",

    # PERSONAS — MUNDO GRIEGO
    "Clístenes": "Clístenes de Atenas",
    "Clistenes": "Clístenes de Atenas",
    "Leónidas": "Leónidas I",
    "Leonidas": "Leónidas I",

    # PERSONAS — MACEDONIA / HELENISMO
    "Alejandro": "Alejandro Magno",
    "Alejandro III": "Alejandro Magno",
    "Alejandro III de Macedonia": "Alejandro Magno",
    "Filipo": "Filipo II de Macedonia",
    "Filipo II": "Filipo II de Macedonia",
    "Filipo de Macedonia": "Filipo II de Macedonia",
    # "Olimpia" es ambiguo (persona vs santuario/ciudad) — movido a RISKY
    "Casandro": "Casandro de Macedonia",
    "Pirro": "Pirro de Epiro",

    # PERSONAS — MUNDO PERSA
    "Ciro": "Ciro el Grande",
    "Ciro II": "Ciro el Grande",
    "Cambises": "Cambises II",
    "Jerjes": "Jerjes I",

    # PERSONAS — MUNDO ROMANO
    "César": "Julio César",
    "Cesar": "Julio César",
    "Octavio": "Augusto",
    "Octaviano": "Augusto",
    "Pompeyo": "Pompeyo Magno",
    "Bruto": "Marco Junio Bruto",
    "Casio": "Cayo Casio Longino",
    "Constantino": "Constantino I",
    "Justiniano": "Justiniano I",

    # PERSONAS — EGIPTO / MESOPOTAMIA
    "Akhenatón": "Akenatón",
    "Akhenaton": "Akenatón",
    "Amenhotep IV": "Akenatón",
    "Ramsés": "Ramsés II",
    "Ramses": "Ramsés II",
    "Keops": "Jufu",
    "Kefrén": "Jafra",
    "Kefren": "Jafra",
    "Sargón": "Sargón de Acad",
    "Sargon": "Sargón de Acad",
    "Nabucodonosor": "Nabucodonosor II",

    # REGIONES / CIVILIZACIONES
    "Hélade": "Antigua Grecia",
    "Helade": "Antigua Grecia",
    "Grecia antigua": "Antigua Grecia",
    "Mundo griego": "Antigua Grecia",
    "Mundo helénico": "Antigua Grecia",
    "Mundo helenico": "Antigua Grecia",
    "Mundo helenístico": "Período helenístico",
    "Mundo helenistico": "Período helenístico",
    "Helenismo": "Período helenístico",
    "Mesopotamia": "Antigua Mesopotamia",
    "Oriente Próximo": "Antiguo Oriente Próximo",
    "Oriente Proximo": "Antiguo Oriente Próximo",
    "Asia Menor": "Anatolia",
    "Bactria": "Bactriana",

    # GUERRAS / CONFLICTOS
    "Guerras persas": "Guerras médicas",
    "Guerras del Peloponeso": "Guerra del Peloponeso",
    "Periodo helenistico": "Período helenístico",

    # BATALLAS
    "Maratón": "Batalla de Maratón",
    "Maraton": "Batalla de Maratón",
    "Termópilas": "Batalla de las Termópilas",
    "Termopilas": "Batalla de las Termópilas",
    "Salamina": "Batalla de Salamina",
    "Platea": "Batalla de Platea",
    "Mícale": "Batalla de Mícale",
    "Micale": "Batalla de Mícale",
    "Queronea": "Batalla de Queronea",
    "Gránico": "Batalla del Gránico",
    "Granico": "Batalla del Gránico",
    "Issos": "Batalla de Issos",
    "Arbela": "Batalla de Gaugamela",
    "Hidaspes": "Batalla del Hidaspes",
    "Accio": "Batalla de Accio",
    "Actium": "Batalla de Accio",
    # "Filipos" es ambiguo (ciudad vs batalla) — movido a RISKY
    "Adrianópolis": "Batalla de Adrianópolis",
    "Adrianopolis": "Batalla de Adrianópolis",
    "Milvio": "Batalla del Puente Milvio",

    # OBRAS / TEXTOS
    "República": "La República",
    "Republica": "La República",

    # INSTITUCIONES
    "Senado": "Senado romano",
    "Ekklesia": "Ekklesía",
})


# ---------------------------------------------------------
# SPELLING VARIANTS — variantes ortográficas sin acento
# ---------------------------------------------------------

SPELLING_VARIANTS: dict[str, str] = _drop_identity({
    "Socrates": "Sócrates",
    "Platon": "Platón",
    "Aristoteles": "Aristóteles",
    "Herodoto": "Heródoto",
    "Tucidides": "Tucídides",
    "Temistocles": "Temístocles",
    "Milciades": "Milcíades",
    "Alcibiades": "Alcibíades",
    "Solon": "Solón",
    "Dracon": "Dracón",
    "Pisistrato": "Pisístrato",
    "Pelopidas": "Pelópidas",
    "Hesiodo": "Hesíodo",
    "Pindaro": "Píndaro",
    "Pitagoras": "Pitágoras",
    "Parmenides": "Parménides",
    "Heraclito": "Heráclito",
    "Democrito": "Demócrito",
    "Sofocles": "Sófocles",
    "Euripides": "Eurípides",
    "Aristofanes": "Aristófanes",
    "Antipatro": "Antípatro",
    "Dario": "Darío III",
    "Artajerjes": "Artajerjes I",
    "Ramses II": "Ramsés II",
    "Akenaton": "Akenatón",
    "Tutankamon": "Tutankamón",
    "Tutankhamon": "Tutankamón",
    "Julio Cesar": "Julio César",
    "Ciceron": "Cicerón",
    "Anibal": "Aníbal",
    "Neron": "Nerón",
    "Caligula": "Calígula",
    "Alejandria": "Alejandría",
    "Persepolis": "Persépolis",
    "Ilion": "Troya",
    "Iliada": "Ilíada",
    "Teogonia": "Teogonía",
    "Anabasis": "Anábasis",
})


# ---------------------------------------------------------
# RISKY — NO aplicar automáticamente sin contexto
# ---------------------------------------------------------

RISKY_ALIASES: dict[str, str] = _drop_identity({
    # Estados / regiones / ciudades ambiguos
    "Roma": "República Romana",
    "Egipto": "Antiguo Egipto",
    "Grecia": "Antigua Grecia",
    "Siria": "Siria seléucida",
    "Persas": "Imperio Persa",
    "Macedonios": "Reino de Macedonia",
    "Babilonia": "Imperio Babilónico",  # puede ser la ciudad
    "Bizancio": "Imperio Bizantino",  # puede ser la ciudad antigua
    "Olimpia": "Olimpia de Epiro",  # puede ser el santuario
    "Filipos": "Batalla de Filipos",  # puede ser la ciudad

    # Personas con múltiples homónimos
    "Darío": "Darío III",
    "Ptolomeo": "Ptolomeo I Sóter",
    "Seleuco": "Seleuco I Nicátor",
    "Antíoco": "Antíoco III el Grande",
    "Antígono": "Antígono I Monoftalmos",
    "Demetrio": "Demetrio I Poliorcetes",
    "Cleopatra": "Cleopatra VII",
    "Ramsés": "Ramsés II",
})

# Merge safe + spelling for default use by fix-links
ALL_SAFE_ALIASES: dict[str, str] = {**SAFE_LINK_ALIASES, **SPELLING_VARIANTS}


def resolve_alias(term: str, *, allow_risky: bool = False) -> str | None:
    """Devuelve nombre canónico si encuentra alias exacto, o None."""
    if term in SAFE_LINK_ALIASES:
        return SAFE_LINK_ALIASES[term]
    if term in SPELLING_VARIANTS:
        return SPELLING_VARIANTS[term]
    if allow_risky and term in RISKY_ALIASES:
        return RISKY_ALIASES[term]
    return None


# =========================================================
# LINK FIXING
# =========================================================

@dataclass(slots=True, frozen=True)
class LinkFixResult:
    notes_scanned: int
    notes_fixed: int
    fixes: tuple[tuple[str, str, str], ...]  # (file, old_link, new_link)

    def to_dict(self) -> dict[str, object]:
        return {
            "notes_scanned": self.notes_scanned,
            "notes_fixed": self.notes_fixed,
            "fixes": [{"file": f, "old": o, "new": n} for f, o, n in self.fixes],
        }


def fix_ambiguous_links(
    vault_path: Path,
    aliases: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    include_risky: bool = False,
    excluded_parts: set[str] | None = None,
) -> LinkFixResult:
    """Scan vault notes and replace [[alias]] with [[canonical|alias]].

    Example: [[Persia]] → [[Imperio Persa|Persia]]
    This preserves the display text while linking to the correct entity.
    """
    if aliases is None:
        aliases = dict(ALL_SAFE_ALIASES)
        if include_risky:
            aliases.update(RISKY_ALIASES)
    if excluded_parts is None:
        excluded_parts = {".git", ".obsidian", ".brain-ops", "Templates"}

    notes_scanned = 0
    fixes: list[tuple[str, str, str]] = []

    for md_file in sorted(vault_path.rglob("*.md")):
        if any(part in md_file.parts for part in excluded_parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        notes_scanned += 1
        new_content = content
        file_fixed = False

        for alias, canonical in aliases.items():
            if md_file.stem == canonical:
                continue

            pattern = re.compile(rf"\[\[{re.escape(alias)}\]\]")

            already_fixed = f"[[{canonical}|{alias}]]"
            if already_fixed in new_content:
                continue

            replacement = f"[[{canonical}|{alias}]]"
            matches = pattern.findall(new_content)
            if matches:
                new_content = pattern.sub(replacement, new_content)
                rel_path = str(md_file.relative_to(vault_path))
                for _ in matches:
                    fixes.append((rel_path, f"[[{alias}]]", replacement))
                file_fixed = True

        if file_fixed and not dry_run:
            md_file.write_text(new_content, encoding="utf-8")

    notes_fixed = len({f for f, _, _ in fixes})
    return LinkFixResult(
        notes_scanned=notes_scanned,
        notes_fixed=notes_fixed,
        fixes=tuple(fixes),
    )


def add_alias_to_frontmatter(
    note_path: Path,
    aliases: list[str],
) -> bool:
    """Add aliases to a note's frontmatter for Obsidian search."""
    from brain_ops.frontmatter import dump_frontmatter, split_frontmatter

    try:
        content = note_path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(content)

        existing = fm.get("aliases", [])
        if not isinstance(existing, list):
            existing = [existing] if existing else []

        added = False
        for alias in aliases:
            if alias not in existing:
                existing.append(alias)
                added = True

        if added:
            fm["aliases"] = existing
            note_path.write_text(dump_frontmatter(fm, body), encoding="utf-8")
            return True
    except Exception:
        pass
    return False


__all__ = [
    "ALL_SAFE_ALIASES",
    "LinkFixResult",
    "RISKY_ALIASES",
    "SAFE_LINK_ALIASES",
    "SPELLING_VARIANTS",
    "add_alias_to_frontmatter",
    "fix_ambiguous_links",
    "resolve_alias",
]
