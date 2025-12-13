# migration.py
import json

from .models import Cycle, Pregnancy
from .sqlite_store import SQLiteStore


def migrate_json_to_sqlite(
    cycles: list[Cycle], pregnancies: list[Pregnancy], store: SQLiteStore
):
    cur = store.conn.cursor()

    # pregnancies
    for preg in pregnancies:
        cur.execute(
            """
            INSERT OR IGNORE INTO pregnancies
            (id, start_date, confirmed, end_date, notes, custom_due_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                preg.id,
                preg.start_date.isoformat(),
                int(preg.confirmed),
                preg.end_date.isoformat() if preg.end_date else None,
                preg.notes,
                preg.custom_due_date.isoformat() if preg.custom_due_date else None,
            ),
        )

    # cycles
    for cycle in cycles:
        cur.execute(
            """
            INSERT OR IGNORE INTO cycles
            (start_date, duration, pregnancy_id)
            VALUES (?, ?, ?)
            """,
            (
                cycle.start_date.isoformat(),
                cycle.duration,
                cycle.pregnancy_id if cycle.pregnancy_id else None,
            ),
        )
        cur.execute(
            "SELECT id FROM cycles WHERE start_date = ?",
            (cycle.start_date.isoformat(),),
        )
        row = cur.fetchone()
        if row is None:
            continue

        cycle_id = row["id"]

        for day in cycle.days:
            cur.execute(
                """
                INSERT OR IGNORE INTO day_entries
                (cycle_id, date, mood, temperature, flow, notes, symptoms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cycle_id,
                    day.date.isoformat(),
                    day.mood,
                    day.temperature,
                    day.flow,
                    day.notes,
                    json.dumps(day.symptoms),
                ),
            )

    store.conn.commit()
