from __future__ import annotations

import unittest

from swiss_os import hotelleriesuisse_capture as hslca
from swiss_os.hslca_mdc_runtime import extract_records_with_mdc


ROOT = "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis"


class HSLCAWithMDCRuntimeTests(unittest.TestCase):
    def test_live_card_locality_first_is_normalized_to_name_city(self) -> None:
        html = f"""
        <html><body>
          <a href="{ROOT}/hotel-at-home-hotel-locarno">
            <span>Muralto</span><span>@Home Hotel Locarno</span>
          </a>
          <a href="{ROOT}/hotel-hotel-foo">
            <span>Zürich</span><span>Hotel Foo</span>
          </a>
        </body></html>
        """
        records = extract_records_with_mdc(
            html,
            page_url=ROOT,
            page_id="PAGE-001",
            page_position=1,
        )
        self.assertEqual(records[0]["name"], "@Home Hotel Locarno")
        self.assertEqual(records[0]["city"], "Muralto")
        self.assertEqual(records[1]["name"], "Hotel Foo")
        self.assertEqual(records[1]["city"], "Zürich")
        self.assertEqual(records[0]["evidence_ref"], "PAGE-001#record-001")

    def test_mdc_rejects_one_part_card_fail_closed(self) -> None:
        html = f'<a href="{ROOT}/hotel-hotel-foo"><span>Hotel Foo</span></a>'
        with self.assertRaisesRegex(hslca.DirectoryCaptureError, "MDC rejected 1 card"):
            extract_records_with_mdc(
                html,
                page_url=ROOT,
                page_id="PAGE-001",
                page_position=1,
            )

    def test_no_directory_cards_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            hslca.DirectoryCaptureError, "MDC found no directory records"
        ):
            extract_records_with_mdc(
                "<html><body>none</body></html>",
                page_url=ROOT,
                page_id="PAGE-001",
                page_position=1,
            )


if __name__ == "__main__":
    unittest.main()
