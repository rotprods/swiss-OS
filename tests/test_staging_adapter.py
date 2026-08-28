from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import zipfile
from xml.sax.saxutils import escape

from swiss_os.staging_adapter import (
    build_cohort_registry,
    cache_records_from_rows,
    extract_workbook,
    read_xlsx_sheet,
    v16_records_from_rows,
)


OBSERVED_AT = "2026-08-28T14:30:00+02:00"
V16_EPOCH = "SV2-059-V16-CANARY-2026-08-27"


def _col(index: int) -> str:
    value = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        value = chr(65 + remainder) + value
    return value


def _sheet_xml(rows: list[list[object]]) -> str:
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            ref = f"{_col(column_index)}{row_index}"
            text = escape(str(value or ""))
            cells.append(
                f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'
            )
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    )


def _write_tiny_workbook(path: Path) -> None:
    cache_rows = [
        [
            "source_page",
            "city",
            "hotel_name",
            "source_url",
            "observed_count",
            "cache_age",
            "evidence_scope",
        ],
        [
            28,
            "Bern",
            "Hotel Cache",
            "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis/hotel-page-28",
            2069,
            "CACHE_5_MONTHS",
            "HISTORICAL_CACHE_DISCOVERY_ONLY",
        ],
    ]
    v16_rows = [
        ["proposed_id", "name", "city", "evidence"],
        [
            "H-0691",
            "Hotel Exact",
            "Genève",
            "https://www.hotelleriesuisse.ch/fr/member/hotel-exact | https://hotel.test",
        ],
        ["H-0692", "Hotel Reject", "Basel", "https://hotel-reject.test"],
    ]
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
<sheet name="Directory_Cache_Observations" sheetId="1" r:id="rId1"/>
<sheet name="V16_Canary" sheetId="2" r:id="rId2"/>
</sheets></workbook>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
</Relationships>"""
    package_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", _sheet_xml(cache_rows))
        archive.writestr("xl/worksheets/sheet2.xml", _sheet_xml(v16_rows))


class StagingAdapterTests(unittest.TestCase):
    def test_read_xlsx_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook = Path(tmpdir) / "tiny.xlsx"
            _write_tiny_workbook(workbook)
            rows = read_xlsx_sheet(workbook, "Directory_Cache_Observations")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["hotel_name"], "Hotel Cache")
            self.assertEqual(rows[0]["_row_number"], 2)

    def test_cache_rows_remain_historical_and_do_not_infer_detail_url(self) -> None:
        rows = [
            {
                "_row_number": 2,
                "source_page": "28",
                "city": "Bern",
                "hotel_name": "Hotel Cache",
                "source_url": "https://www.hotelleriesuisse.ch/de/directory/hotel-page-28",
                "observed_count": "2069",
                "cache_age": "CACHE_5_MONTHS",
                "evidence_scope": "HISTORICAL_CACHE_DISCOVERY_ONLY",
            }
        ]
        records, rejects = cache_records_from_rows(rows, "workbook.xlsx", OBSERVED_AT)
        self.assertEqual(rejects, ())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].evidence_scope, "HISTORICAL_CACHE_DISCOVERY_ONLY")
        self.assertEqual(records[0].detail_url, "")
        self.assertEqual(records[0].locale, "de")

    def test_v16_requires_exact_hotelleriesuisse_url(self) -> None:
        rows = [
            {
                "_row_number": 2,
                "proposed_id": "H-0691",
                "name": "Hotel Exact",
                "city": "Genève",
                "evidence": "https://www.hotelleriesuisse.ch/fr/member/hotel-exact | https://hotel.test",
            },
            {
                "_row_number": 3,
                "proposed_id": "H-0692",
                "name": "Hotel Reject",
                "city": "Basel",
                "evidence": "https://hotel-reject.test",
            },
        ]
        records, rejects = v16_records_from_rows(
            rows, "workbook.xlsx", OBSERVED_AT, V16_EPOCH
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].locale, "fr")
        self.assertEqual(records[0].evidence_scope, "CURRENT_EXACT_ENTITY_DETAIL")
        self.assertEqual(len(rejects), 1)
        self.assertEqual(
            rejects[0].reason_code, "NO_EXACT_HOTELLERIESUISSE_DETAIL_URL"
        )

    def test_registry_hard_locks_and_cohort_separation(self) -> None:
        cache_rows = [
            {
                "_row_number": 2,
                "source_page": "28",
                "city": "Bern",
                "hotel_name": "Hotel Cache",
                "source_url": "https://www.hotelleriesuisse.ch/de/directory/hotel-page-28",
                "observed_count": "2069",
                "cache_age": "CACHE_5_MONTHS",
                "evidence_scope": "HISTORICAL_CACHE_DISCOVERY_ONLY",
            }
        ]
        v16_rows = [
            {
                "_row_number": 2,
                "proposed_id": "H-0691",
                "name": "Hotel Exact",
                "city": "Genève",
                "evidence": "https://www.hotelleriesuisse.ch/fr/member/hotel-exact",
            }
        ]
        cache_records, cache_rejects = cache_records_from_rows(
            cache_rows, "workbook.xlsx", OBSERVED_AT
        )
        v16_records, v16_rejects = v16_records_from_rows(
            v16_rows, "workbook.xlsx", OBSERVED_AT, V16_EPOCH
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = build_cohort_registry(
                cache_records + v16_records,
                cache_rejects + v16_rejects,
                tmpdir,
                OBSERVED_AT,
                171,
                2050,
                "b" * 64,
            )
            self.assertEqual(registry["cohort_count"], 2)
            self.assertFalse(registry["coverage_complete"])
            self.assertEqual(registry["authority_advanced"], False)
            self.assertEqual(registry["h_id_allocations"], 0)
            self.assertEqual(registry["outbound"], "CLOSED")
            self.assertEqual(registry["send_allowed"], 0)
            self.assertTrue((Path(tmpdir) / "STAGING_EVIDENCE_REGISTRY.json").is_file())

    def test_end_to_end_extract_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook = Path(tmpdir) / "tiny.xlsx"
            output = Path(tmpdir) / "out"
            _write_tiny_workbook(workbook)
            registry = extract_workbook(
                workbook,
                output,
                OBSERVED_AT,
                V16_EPOCH,
                171,
                2050,
            )
            self.assertEqual(registry["records_count"], 2)
            self.assertEqual(registry["rejects_count"], 1)
            self.assertEqual(registry["cohort_count"], 2)
            self.assertEqual(registry["ssr_eligible_cohorts"], 0)


if __name__ == "__main__":
    unittest.main()
