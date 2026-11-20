import datetime as dt
import unittest
from zoneinfo import ZoneInfo

from monitor import build_payload, parse_bcb_rows


class IndicatorTests(unittest.TestCase):
    def test_parses_bcb_decimal(self):
        rows = parse_bcb_rows([{"data": "19/11/2026", "valor": "5,7000"}])
        self.assertEqual(rows[0][1], 5.7)

    def test_five_percent_decline(self):
        rows = [
            (dt.date(2025, 11, 21), 6.00),
            (dt.date(2026, 11, 20), 5.70),
        ]
        payload = build_payload(
            rows,
            dt.datetime(2026, 11, 21, 8, 15, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )
        self.assertAlmostEqual(payload["latest"]["drop_pct"], 5.0, places=3)
        self.assertEqual(payload["latest"]["max_12m"], 6.0)
        self.assertEqual(payload["latest"]["close"], 5.7)


if __name__ == "__main__":
    unittest.main()
