"""2GIS firm-id discovery (Step A) — match branches without a firm_id to a 2GIS firm.

Orchestrates the offline browser collector and applies matches in Python so the matching
rule (name + geo) stays the single, tested source of truth (app.services.twogis.pick_firm):

  1. select branches with no twogis_firm_id (optionally one city),
  2. hand them to scripts/twogis/collect_firms.mjs (headless browser → firm candidates),
  3. pick_firm() each, store firm_id + aggregate rating on the branch,
  4. immediately pull reviews (Step B) for the newly matched firms.

Heavy + occasional. Once a branch has a firm_id, daily freshness comes from
refresh_2gis_reviews.py (no browser). Run:

    python -m app.scripts.discover_2gis_firms --city Алматы --limit 50
"""

import argparse
import json
import logging
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Clinic, ClinicBranch
from app.services.twogis import Firm, pick_firm
from app.services.twogis_sync import apply_firm_match, refresh_reviews

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
COLLECTOR = _BACKEND_ROOT / "scripts" / "twogis" / "collect_firms.mjs"

# Our city label → 2gis.kz url slug.
CITY_PATH = {
    "Астана": "astana",
    "Алматы": "almaty",
    "Шымкент": "shymkent",
    "Караганда": "karaganda",
    "Актобе": "aktobe",
    "Атырау": "atyrau",
    "Тараз": "taraz",
    "Павлодар": "pavlodar",
    "Усть-Каменогорск": "ust-kamenogorsk",
    "Семей": "semey",
    "Костанай": "kostanay",
    "Кызылорда": "kyzylorda",
    "Уральск": "uralsk",
    "Петропавловск": "petropavl",
    "Актау": "aktau",
    "Темиртау": "temirtau",
    "Туркестан": "turkestan",
    "Кокшетау": "kokshetau",
    "Экибастуз": "ekibastuz",
}


def _branches_without_firm(session, city: str | None, limit: int | None) -> list[dict]:
    stmt = (
        select(ClinicBranch.id, Clinic.name, ClinicBranch.city, ClinicBranch.lat, ClinicBranch.lng)
        .join(Clinic, Clinic.id == ClinicBranch.clinic_id)
        .where(
            ClinicBranch.twogis_firm_id.is_(None),
            ClinicBranch.lat.is_not(None),
            ClinicBranch.lng.is_not(None),
        )
        .order_by(ClinicBranch.id)
    )
    if city:
        stmt = stmt.where(ClinicBranch.city == city)
    if limit:
        stmt = stmt.limit(limit)
    rows = []
    for bid, name, city_name, lat, lng in session.execute(stmt):
        path = CITY_PATH.get(city_name)
        if not path:
            continue
        rows.append(
            {"branch_id": bid, "clinic": name, "city_path": path, "lat": lat, "lon": lng}
        )
    return rows


def _run_collector(branches: list[dict]) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        in_path = Path(tmp) / "branches.json"
        out_path = Path(tmp) / "firms.json"
        in_path.write_text(json.dumps(branches, ensure_ascii=False), encoding="utf-8")
        cmd = ["node", str(COLLECTOR), str(in_path), str(out_path)]
        logger.info("running collector for %d branches…", len(branches))
        subprocess.run(cmd, check=True, cwd=str(COLLECTOR.parent))
        return json.loads(out_path.read_text(encoding="utf-8"))


def _ingest_chunk(session, chunk: list[dict], results: list[dict]) -> list[int]:
    by_id = {b["branch_id"]: b for b in chunk}
    matched_ids: list[int] = []
    for row in results:
        meta = by_id.get(row["branch_id"])
        branch = session.get(ClinicBranch, row["branch_id"])
        if meta is None or branch is None:
            continue
        firms = [
            Firm(
                firm_id=f["firm_id"],
                name=f.get("name") or "",
                address=f.get("address"),
                lat=f["lat"],
                lon=f["lon"],
                rating=f.get("rating"),
                reviews_count=f.get("reviews_count"),
            )
            for f in row.get("firms") or []
            if f.get("lat") is not None and f.get("lon") is not None
        ]
        match = pick_firm(meta["clinic"], meta["lat"], meta["lon"], firms)
        if match is None:
            continue
        apply_firm_match(session, branch, match.firm)
        matched_ids.append(branch.id)
    return matched_ids


def discover(
    city: str | None, limit: int | None, refresh: bool, chunk_size: int = 25
) -> dict[str, int]:
    """Commit per chunk so a long backfill is crash-safe and resumable (a branch that
    already got a firm_id is excluded from the next run's candidate set)."""
    session = SessionLocal()
    try:
        branches = _branches_without_firm(session, city, limit)
        total = len(branches)
        if total == 0:
            return {"branches": 0, "matched": 0, "no_match": 0}

        matched = 0
        for start in range(0, total, chunk_size):
            chunk = branches[start : start + chunk_size]
            results = _run_collector(chunk)
            matched_ids = _ingest_chunk(session, chunk, results)
            session.commit()
            if refresh and matched_ids:
                refresh_reviews(session, ttl_days=0, branch_ids=matched_ids)
            matched += len(matched_ids)
            logger.info(
                "discovery progress: %d/%d branches, %d matched so far",
                min(start + chunk_size, total), total, matched,
            )

        return {"branches": total, "matched": matched, "no_match": total - matched}
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="2GIS firm-id discovery (Step A).")
    parser.add_argument("--city", default=None, help="restrict to one city (e.g. Алматы)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-refresh", action="store_true", help="skip Step B after matching")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    stats = discover(args.city, args.limit, refresh=not args.no_refresh)
    print(
        f"2GIS discovery: {stats['matched']} matched / {stats['no_match']} no_match "
        f"of {stats['branches']} branches"
    )


if __name__ == "__main__":
    main()
