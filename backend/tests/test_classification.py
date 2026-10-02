from events.classifiers.rule_based import RuleBasedEventClassifier
from events.domain.types import EventClassificationInput
from events.models import EventFormat


def test_developer_meetup_is_topical_and_networking_relevant() -> None:
    result = RuleBasedEventClassifier().classify(
        EventClassificationInput(
            title="UtahJS Community Meetup",
            description="JavaScript talks, small group discussion, and networking.",
        )
    )

    assert "software_engineering" in result.career_fields
    assert "frontend_engineering" in result.career_fields
    assert result.format == EventFormat.IN_PERSON
    assert result.networking_relevant
    assert result.networking_strength >= 0.8


def test_prerecorded_tutorial_has_low_networking_strength() -> None:
    result = RuleBasedEventClassifier().classify(
        EventClassificationInput(
            title="Python course on demand",
            description="A prerecorded self-paced tutorial.",
        )
    )

    assert "software_engineering" in result.career_fields
    assert result.format == EventFormat.ASYNCHRONOUS
    assert result.networking_strength < 0.1
    assert not result.networking_relevant
