from datetime import datetime

from app.scripts.load_2gis_reviews import parse_review, row_rating


def test_should_parse_review_with_date():
    raw = {"rating": 5, "date": "2026-04-26", "user": "Айжан", "text": "отлично"}

    parsed = parse_review(raw)

    assert parsed["author"] == "Айжан"
    assert parsed["rating"] == 5
    assert parsed["text"] == "отлично"
    assert isinstance(parsed["review_date"], datetime)
    assert parsed["review_date"].year == 2026


def test_should_tolerate_missing_fields_in_review():
    parsed = parse_review({"text": "ok"})

    assert parsed["author"] is None
    assert parsed["rating"] is None
    assert parsed["review_date"] is None
    assert parsed["text"] == "ok"


def test_should_extract_branch_rating_from_ok_row():
    row = {
        "status": "ok", "id": "42", "firm_id": "70000001",
        "rating": 4.7, "reviews_count": 120,
    }

    assert row_rating(row) == (42, "70000001", 4.7, 120)


def test_should_skip_non_ok_rows():
    assert row_rating({"status": "no_match", "id": "9"}) is None
