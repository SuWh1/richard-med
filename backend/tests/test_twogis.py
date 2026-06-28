import httpx

from app.models import Clinic, ClinicBranch, ClinicReview
from app.services import twogis, twogis_sync
from app.services.twogis import Firm, name_matches, parse_reviews_payload, pick_firm

# --- pure: name matching ---


def test_should_match_brand_token_ignoring_generic_suffix():
    assert name_matches("Invitro", "Invitro, сеть медицинских лабораторий")


def test_should_match_across_cyrillic_latin_transliteration():
    assert name_matches("KDL Olymp", "КДЛ Олимп, медицинская лаборатория")


def test_should_not_match_on_generic_words_alone():
    assert not name_matches("Invitro лаборатория", "Helix лаборатория")


# --- pure: geo + firm pick ---


def test_should_compute_haversine_distance_roughly():
    # ~111 km per degree of latitude
    d = twogis.haversine_m(43.0, 76.0, 44.0, 76.0)
    assert 110_000 < d < 112_000


def test_should_pick_nearest_name_matching_firm_within_radius():
    firms = [
        Firm("1", "Helix", None, 43.2350, 76.9550, 4.8, 10),  # closest but wrong name
        Firm("2", "Invitro", None, 43.2353, 76.9553, 4.4, 99),
    ]
    match = pick_firm("Invitro", 43.2350, 76.9550, firms, radius_m=500)
    assert match is not None
    assert match.firm.firm_id == "2"


def test_should_reject_when_only_other_clinics_are_nearby():
    firms = [Firm("1", "Helix", None, 43.2350, 76.9550, 4.8, 10)]
    assert pick_firm("Invitro", 43.2350, 76.9550, firms, radius_m=500) is None


def test_should_reject_name_match_beyond_radius():
    firms = [Firm("2", "Invitro", None, 43.2600, 76.9550, 4.4, 99)]
    assert pick_firm("Invitro", 43.2350, 76.9550, firms, radius_m=500) is None


# --- pure: reviews payload parse ---

PAYLOAD = {
    "meta": {"branch_rating": 4.9, "branch_reviews_count": 155, "org_rating": 4.8},
    "reviews": [
        {
            "id": "1",
            "rating": 5,
            "text": "Отличная клиника",
            "date_created": "2026-04-26T16:41:34.379839+07:00",
            "user": {"name": "Aizhan"},
            "official_answer": {"text": "Спасибо!"},
        },
        {"id": "2", "rating": 4, "text": "   ", "user": {"name": "Empty"}},
    ],
}


def test_should_parse_aggregate_rating_and_reviews():
    result = parse_reviews_payload(PAYLOAD, sample=5)
    assert result.rating == 4.9
    assert result.reviews_count == 155
    assert len(result.reviews) == 1  # blank-text review skipped
    r = result.reviews[0]
    assert r.author == "Aizhan"
    assert r.rating == 5
    assert r.official_answer == "Спасибо!"
    assert r.review_date is not None


def test_should_respect_sample_limit():
    payload = {
        "meta": {"branch_rating": 5.0, "branch_reviews_count": 3},
        "reviews": [{"id": str(i), "rating": 5, "text": f"r{i}"} for i in range(5)],
    }
    assert len(parse_reviews_payload(payload, sample=2).reviews) == 2


# --- DB sync ---


def _branch(db_session, *, firm_id="70000001088237756"):
    clinic = Clinic(name="Invitro", source_name="twogis_test")
    db_session.add(clinic)
    db_session.flush()
    branch = ClinicBranch(
        clinic_id=clinic.id, city="Алматы", address="ул. Достык, 89",
        lat=43.235, lng=76.955, twogis_firm_id=firm_id,
    )
    db_session.add(branch)
    db_session.flush()
    return branch


def test_should_write_reviews_and_aggregate_to_branch(db_session):
    branch = _branch(db_session)
    from datetime import UTC, datetime

    result = parse_reviews_payload(PAYLOAD, sample=5)
    written = twogis_sync.apply_reviews(db_session, branch, result, datetime.now(UTC))
    db_session.flush()

    assert written == 1
    assert branch.rating == 4.9
    assert branch.reviews_count == 155
    assert branch.rating_synced_at is not None
    rows = db_session.query(ClinicReview).filter_by(branch_id=branch.id).all()
    assert len(rows) == 1
    assert rows[0].source == "2gis"


def test_should_replace_existing_reviews_on_refresh(db_session):
    from datetime import UTC, datetime

    branch = _branch(db_session)
    result = parse_reviews_payload(PAYLOAD, sample=5)
    twogis_sync.apply_reviews(db_session, branch, result, datetime.now(UTC))
    db_session.flush()
    twogis_sync.apply_reviews(db_session, branch, result, datetime.now(UTC))
    db_session.flush()
    rows = db_session.query(ClinicReview).filter_by(branch_id=branch.id).all()
    assert len(rows) == 1  # not duplicated


def test_should_refresh_only_branches_with_firm_id_via_step_b(db_session):
    with_firm = _branch(db_session, firm_id="111")
    _branch(db_session, firm_id=None)  # no firm id → skipped

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "meta": {"branch_rating": 4.7, "branch_reviews_count": 42},
                "reviews": [{"id": "9", "rating": 5, "text": "Хорошо"}],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    stats = twogis_sync.refresh_reviews(
        db_session, ttl_days=0, delay_sec=0, branch_ids=[with_firm.id], client=client
    )

    assert stats.attempted == 1
    assert stats.updated == 1
    db_session.refresh(with_firm)
    assert with_firm.rating == 4.7
    assert with_firm.reviews_count == 42
