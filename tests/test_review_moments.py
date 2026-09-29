from datetime import datetime, timezone
from uuid import UUID

from app.models import AIObservation, AIReviewMoment, Analysis, CoachReview
from app.seed import DEMO_ATHLETE_ID
from app.services.review_moments import rank_review_moments


def result():
    return {"repetitions": [
        {"repetition": 1, "bottom_s": 1.0, "min_knee_angle": 100, "max_trunk_from_vertical": 20},
        {"repetition": 2, "bottom_s": 4.0, "min_knee_angle": 120, "max_trunk_from_vertical": 38},
        {"repetition": 3, "bottom_s": 8.0, "min_knee_angle": 102, "max_trunk_from_vertical": 22},
        {"repetition": 4, "bottom_s": 12.0, "min_knee_angle": 118, "max_trunk_from_vertical": 35},
    ]}


def test_moments_rank_and_limit_to_three(monkeypatch):
    monkeypatch.setenv("AI_REVIEW_MOMENTS_MAX", "3")
    moments = rank_review_moments(result())
    assert len(moments) <= 3
    assert moments == sorted(moments, key=lambda item: item["priority_score"], reverse=True)


def test_moments_fuse_nearby_events(monkeypatch):
    monkeypatch.setenv("AI_REVIEW_MOMENT_WINDOW_S", "2")
    moments = rank_review_moments(result(), [
        {"repetition": 2, "timestamp": 4.0, "title": "IA", "description": "A", "severity": "priority", "confidence": "high"},
        {"repetition": 2, "timestamp": 4.5, "title": "IA cercana", "description": "B", "severity": "review", "confidence": "medium"},
    ])
    assert len([item for item in moments if 3 <= item["timestamp"] <= 6]) == 1


def test_no_repetitions_has_no_suggestions():
    assert rank_review_moments({"repetitions": []}) == []


def test_coach_reads_and_decides_a_suggested_moment(client, session):
    analysis = Analysis(
        id="review-moment-analysis", athlete_id=DEMO_ATHLETE_ID, status="COMPLETED",
        exercise="Sentadilla", original_filename="squat.mp4", video_path="uploads/squat.mp4",
        annotated_video_path="results/review-moment-analysis/annotated.mp4", progress=100,
        result={"video": {"duration_s": 10}, "repetitions": []}, completed_at=datetime.now(timezone.utc),
    )
    session.add(analysis)
    session.commit()
    observation = AIObservation(
        analysis_id=analysis.id, body="Revisar tronco", repetition_number=2, timestamp_s=4.2,
        category="review_moment", severity="priority", title="Mayor inclinación del tronco",
        description="La repetición se aleja del promedio.", confidence="high", model="deterministic-review-moments",
    )
    session.add(observation)
    session.flush()
    coach_id = UUID("00000000-0000-4000-8000-000000000002")
    review = CoachReview(analysis_id=analysis.id, athlete_id=DEMO_ATHLETE_ID, coach_id=coach_id, status="IN_REVIEW")
    moment = AIReviewMoment(
        analysis_id=analysis.id, observation_id=observation.id, repetition_number=2, timestamp_s=4.2,
        reason="Desviación respecto del promedio.", confidence="high", priority_score=.95,
    )
    session.add_all([review, moment])
    session.commit()

    detail = client.get(f"/api/coach/reviews/{review.id}?coach_id={coach_id}")
    assert detail.status_code == 200
    assert detail.json()["review_moments"][0]["timestamp"] == 4.2
    assert detail.json()["ai_observations"] == []

    decision_url = f"/api/coach/reviews/{review.id}/ai-observations/{observation.id}?coach_id={coach_id}"
    assert client.patch(decision_url, json={"decision": "CONFIRMED"}).json()["decision"] == "CONFIRMED"
    assert client.patch(decision_url, json={"decision": "DISMISSED"}).json()["decision"] == "DISMISSED"
