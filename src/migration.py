# migration.py
import json
import uuid
from typing import List

from .models import Cycle, Pregnancy
from .sqlite_store import SQLiteStore


def migrate_json_to_sqlite(
    cycles: List[Cycle], pregnancies: List[Pregnancy], store: SQLiteStore
):
    cur = store.conn.cursor()

    # Keep only the latest pregnancy for each start_date
    latest_preg_by_start_date = {}
    for preg in pregnancies:
        existing = latest_preg_by_start_date.get(preg.start_date)
        if not existing or preg.id > existing.id:
            latest_preg_by_start_date[preg.start_date] = preg

    # Map old pregnancy ID -> new SQLite ID
    old_to_new_preg_id = {}
    for start_date, preg in latest_preg_by_start_date.items():
        new_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO pregnancies
            (id, start_date, confirmed, end_date, notes, custom_due_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                new_id,
                preg.start_date.isoformat(),
                int(preg.confirmed),
                preg.end_date.isoformat() if preg.end_date else None,
                preg.notes,
                preg.custom_due_date.isoformat() if preg.custom_due_date else None,
            ),
        )
        # Map all old pregnancies with this start_date to the new SQLite ID
        for old_preg in [p for p in pregnancies if p.start_date == start_date]:
            old_to_new_preg_id[old_preg.id] = new_id
        print(f"[Migration] Inserted pregnancy {preg.id} as new ID {new_id}")

    for cycle in cycles:
        # Determine old pregnancy ID for this cycle
        old_preg_id = getattr(cycle, "pregnancy_id", None)
        sqlite_preg_id = None
        if old_preg_id:
            sqlite_preg_id = old_to_new_preg_id.get(old_preg_id)
            if sqlite_preg_id:
                print(
                    f"[Migration] Linking cycle {cycle.start_date} to pregnancy ID {sqlite_preg_id}"
                )
            else:
                print(
                    f"[Migration] WARNING: Cycle {cycle.start_date} has a pregnancy reference that was not found"
                )

        # Insert cycle
        cur.execute(
            """
            INSERT INTO cycles
            (start_date, duration, pregnancy_id)
            VALUES (?, ?, ?)
            """,
            (cycle.start_date.isoformat(), cycle.duration, sqlite_preg_id),
        )

        # Get the SQLite cycle ID
        cur.execute(
            "SELECT id FROM cycles WHERE start_date = ?",
            (cycle.start_date.isoformat(),),
        )
        row = cur.fetchone()
        if not row:
            print(f"[Migration] WARNING: Failed to insert cycle {cycle.start_date}")
            continue

        cycle_id = row["id"]

        # Insert day entries
        for day in cycle.days:
            cur.execute(
                """
                INSERT INTO day_entries
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

    # Perform a safety check to ensure all cycles with pregnancies are properly linked
    cur.execute("SELECT start_date, pregnancy_id FROM cycles")
    unlinked = []
    for row in cur.fetchall():
        if row["pregnancy_id"] is not None:
            cur.execute(
                "SELECT id FROM pregnancies WHERE id = ?", (row["pregnancy_id"],)
            )
            if not cur.fetchone():
                unlinked.append(row["start_date"])

    if unlinked:
        print(
            f"[Migration WARNING] The following cycles have pregnancy IDs that were not found in SQLite: {unlinked}"
        )
    else:
        print("[Migration] All cycles with pregnancies are properly linked.")

    print(
        f"[Migration] Completed migration of {len(old_to_new_preg_id)} pregnancies and {len(cycles)} cycles."
    )
