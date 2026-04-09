from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from brain_ops.domains.knowledge.chunking import ContentChunk
from brain_ops.domains.knowledge.source_blocks import (
    chunk_sidecar_path,
    detect_source_profile,
    load_chunk_sidecar,
    save_chunk_sidecar,
    extract_source_section_blocks,
    section_blocks_to_chunks,
)


class SourceBlocksTestCase(TestCase):
    class _FakeResponse:
        def __init__(self, payload: str) -> None:
            self._payload = payload.encode("utf-8")

        def read(self) -> bytes:
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    def test_detect_source_profile_wikipedia(self) -> None:
        self.assertEqual(
            detect_source_profile("https://es.wikipedia.org/wiki/Albert_Einstein"),
            "wikipedia",
        )

    def test_extract_wikipedia_blocks_ignores_infobox_and_references(self) -> None:
        html = """
        <html>
          <body>
            <div class="mw-parser-output">
              <table class="infobox">
                <tr><th>Educado en</th><td>ETH Zurich</td></tr>
              </table>
              <p>Albert Einstein fue un físico teórico de enorme influencia.</p>
              <p>La introducción resume su vida, obra e impacto histórico.</p>
              <h2><span class="mw-headline">Debate Bohr-Einstein</span></h2>
              <p>Los debates entre Einstein y Bohr fueron centrales para la interpretación de la mecánica cuántica.</p>
              <p>Einstein insistía en la incompletitud de la teoría y Bohr defendía la interpretación dominante.</p>
              <h2><span class="mw-headline">La teoría de campo unificada</span></h2>
              <p>Einstein dedicó sus últimos años a intentar unificar gravitación y electromagnetismo.</p>
              <p>La empresa no tuvo éxito, pero marcó su agenda tardía y su aislamiento intelectual.</p>
              <h2><span class="mw-headline">Referencias</span></h2>
              <ol class="references"><li>ref 1</li></ol>
            </div>
          </body>
        </html>
        """

        blocks = extract_source_section_blocks(
            url="https://es.wikipedia.org/wiki/Albert_Einstein",
            html=html,
            article_title="Albert Einstein",
        )
        titles = [block.title for block in blocks]

        self.assertIn("Lead", titles)
        self.assertIn("Debate Bohr-Einstein", titles)
        self.assertIn("La teoría de campo unificada", titles)
        self.assertNotIn("Educado en", titles)
        self.assertNotIn("Referencias", titles)

        chunks = section_blocks_to_chunks(blocks)
        headings = [chunk.heading for chunk in chunks]
        self.assertIn("Debate Bohr-Einstein", headings)
        self.assertIn("La teoría de campo unificada", headings)

    def test_chunk_sidecar_roundtrip(self) -> None:
        chunks = [
            ContentChunk(
                heading="Trayectoria científica / Debate Bohr-Einstein",
                text="Contenido del debate.",
                char_count=21,
                position=4,
                priority="high",
            )
        ]
        with TemporaryDirectory() as tmpdir:
            raw_file = Path(tmpdir) / "einstein.txt"
            raw_file.write_text("raw", encoding="utf-8")
            sidecar = save_chunk_sidecar(raw_file, source_profile="wikipedia", chunks=chunks)
            self.assertEqual(sidecar, chunk_sidecar_path(raw_file))

            source_profile, loaded = load_chunk_sidecar(raw_file)
            self.assertEqual(source_profile, "wikipedia")
            self.assertIsNotNone(loaded)
            assert loaded is not None
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].heading, chunks[0].heading)

    @patch("brain_ops.domains.knowledge.source_blocks.urlopen")
    def test_extract_wikipedia_blocks_prefers_api_sections(self, mock_urlopen) -> None:
        tocdata_payload = """
        {
          "parse": {
            "tocdata": {
              "sections": [
                {"tocLevel": 1, "hLevel": 2, "line": "Fuentes", "index": "3"},
                {"tocLevel": 1, "hLevel": 2, "line": "Contexto geográfico", "index": "4"},
                {"tocLevel": 2, "hLevel": 3, "line": "Grecia continental europea", "index": "5"}
              ]
            }
          }
        }
        """
        lead_payload = """
        {
          "parse": {
            "text": "<div class=\\"mw-parser-output\\"><p>La Antigua Grecia fue una civilización marítima y urbana de enorme influencia.</p><p>Su legado político, filosófico y cultural marcó el desarrollo del Mediterráneo y de Occidente.</p></div>"
          }
        }
        """
        section_four_payload = """
        {
          "parse": {
            "text": "<div class=\\"mw-parser-output\\"><p>La geografía de Grecia continental combinaba montañas, valles y litorales fragmentados.</p><p>Esa fragmentación favoreció la autonomía de las polis y la dificultad de construir una unidad política estable.</p></div>"
          }
        }
        """
        section_five_payload = """
        {
          "parse": {
            "text": "<div class=\\"mw-parser-output\\"><p>El espacio continental europeo concentró varios de los principales centros políticos del mundo griego.</p><p>La interacción entre llanuras, puertos y sistemas montañosos marcó el desarrollo desigual de cada región.</p></div>"
          }
        }
        """

        mock_urlopen.side_effect = [
            self._FakeResponse(tocdata_payload),
            self._FakeResponse(lead_payload),
            self._FakeResponse(section_four_payload),
            self._FakeResponse(section_five_payload),
        ]

        blocks = extract_source_section_blocks(
            url="https://es.wikipedia.org/wiki/Antigua_Grecia",
            html="""
            <html>
              <head><title>Antigua Grecia - Wikipedia, la enciclopedia libre</title></head>
              <body>
                <div class="mw-parser-output">
                  <h2>Contexto geográfico</h2>
                  <p>fallback html</p>
                </div>
              </body>
            </html>
            """,
            article_title="Antigua Grecia",
        )

        titles = [block.title for block in blocks]
        self.assertIn("Lead", titles)
        self.assertIn("Contexto geográfico", titles)
        self.assertIn("Grecia continental europea", titles)
        self.assertNotIn("Fuentes", titles)

        section = next(block for block in blocks if block.title == "Grecia continental europea")
        self.assertEqual(section.section_path, ["Contexto geográfico", "Grecia continental europea"])
