"""The bundled demo case.

Judges review 24-28 September without you present and with no data of their own.
If the app needs an upload before it shows anything, the 25-point "functionality"
criterion is lost. So one button must run a convincing end-to-end case from data
that ships inside the repo.

Data is inlined rather than read from a CSV: serverless working directories are not
where you expect, and a missing-file error on judging day is an unforced loss.
Replace RECORDS and DEMO_TASK with the real case on the day.
"""

from __future__ import annotations

from typing import Any

DEMO_TASK = (
    "Review the subsidy claims below. Identify claims that look irregular - for example "
    "an amount far outside the norm for the stated hectares, a duplicated registration "
    "number, or a claim date outside the stated season. Flag each suspicious claim with "
    "a clear reason and a severity, then summarise what you found."
)

# fmt: off  (a data table is far easier to edit one record per line)
RECORDS: list[dict[str, Any]] = [
    {
        "id": "C-001",
        "farm": "Aksu Agro",
        "reg": "KZ-4417",
        "hectares": 120,
        "amount_kzt": 2400000,
        "claim_date": "2026-04-12",
    },
    {
        "id": "C-002",
        "farm": "Steppe Grain",
        "reg": "KZ-9903",
        "hectares": 80,
        "amount_kzt": 1600000,
        "claim_date": "2026-04-18",
    },
    {
        "id": "C-003",
        "farm": "Yertis Fields",
        "reg": "KZ-4417",
        "hectares": 95,
        "amount_kzt": 1900000,
        "claim_date": "2026-04-20",
    },
    {
        "id": "C-004",
        "farm": "Kokshe Farm",
        "reg": "KZ-2210",
        "hectares": 15,
        "amount_kzt": 9800000,
        "claim_date": "2026-05-02",
    },
    {
        "id": "C-005",
        "farm": "Turan Seeds",
        "reg": "KZ-7781",
        "hectares": 210,
        "amount_kzt": 4150000,
        "claim_date": "2026-04-29",
    },
    {
        "id": "C-006",
        "farm": "Aral Growers",
        "reg": "KZ-5502",
        "hectares": 60,
        "amount_kzt": 1180000,
        "claim_date": "2025-12-30",
    },
    {
        "id": "C-007",
        "farm": "Ile Valley",
        "reg": "KZ-3390",
        "hectares": 140,
        "amount_kzt": 2760000,
        "claim_date": "2026-05-08",
    },
    {
        "id": "C-008",
        "farm": "Saryarqa Co",
        "reg": "KZ-8814",
        "hectares": 45,
        "amount_kzt": 890000,
        "claim_date": "2026-04-25",
    },
]
# fmt: on

INSTRUCTIONS = (
    "You are a careful analyst. Inspect the data with the tools before concluding. "
    "Flag a record only when you can state the specific evidence for it. "
    "Finish with a short plain-language summary of what you flagged and why."
)
