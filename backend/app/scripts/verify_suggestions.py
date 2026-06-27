"""Verify semantic match suggestions with the LLM and promote confirmed ones to aliases.

Offline batch over the unmatched_services queue. Confirmed → a precise service_alias
(so future parses match it instantly, no LLM call). Rejected → dropped. Undetermined →
left pending for a later run. No-op if GEMINI_API_KEY isn't set.
"""

import os
import time

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Service, ServiceAlias, UnmatchedService
from app.services.llm_verify import get_verifier

_DELAY_S = float(os.getenv("GEMINI_DELAY", "1.5"))
_LIMIT = int(os.getenv("VERIFY_LIMIT", "1000"))


def main() -> None:
    verifier = get_verifier()
    if verifier is None:
        print("GEMINI_API_KEY not set — skipping LLM verification.")
        return

    session = SessionLocal()
    confirmed = rejected = undetermined = 0
    try:
        rows = session.scalars(
            select(UnmatchedService)
            .where(
                UnmatchedService.suggested_service_id.is_not(None),
                UnmatchedService.status == "pending",
            )
            .limit(_LIMIT)
        ).all()
        print(f"verifying {len(rows)} suggestion(s) with {verifier._model}…")

        for item in rows:
            service = session.get(Service, item.suggested_service_id)
            if service is None:
                item.status = "rejected"
                rejected += 1
                continue

            verdict = verifier.verify(item.raw_name, service.name_ru)
            if verdict is True:
                exists = session.scalar(
                    select(ServiceAlias.id).where(
                        ServiceAlias.service_id == service.id,
                        ServiceAlias.alias == item.raw_name,
                    )
                )
                if not exists:
                    session.add(
                        ServiceAlias(
                            service_id=service.id,
                            alias=item.raw_name,
                            source="llm",
                            confidence=0.95,
                        )
                    )
                item.status = "matched"
                confirmed += 1
            elif verdict is False:
                item.status = "rejected"
                rejected += 1
            else:
                undetermined += 1

            if (confirmed + rejected + undetermined) % 20 == 0:
                session.commit()
                print(f"  …{confirmed} confirmed, {rejected} rejected, {undetermined} undetermined")
            time.sleep(_DELAY_S)

        session.commit()
    finally:
        session.close()

    print(f"done: +{confirmed} aliases, {rejected} rejected, {undetermined} undetermined")


if __name__ == "__main__":
    main()
