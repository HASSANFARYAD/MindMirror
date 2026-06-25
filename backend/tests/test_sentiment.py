from __future__ import annotations

from services.sentiment_service import (
    DISTORTION_PATTERNS,
    _fallback_analysis,
    _flatten_emotion_result,
    analyze_entry,
    analyze_preview,
    detect_distortions,
)


class TestDistortionDetection:
    def test_catastrophizing(self):
        result = detect_distortions("This is the worst thing that ever happened. It's a disaster.")
        types = [d["type"] for d in result]
        assert "catastrophizing" in types

    def test_all_or_nothing(self):
        result = detect_distortions("I always fail. Nothing works.")
        types = [d["type"] for d in result]
        assert "all_or_nothing" in types

    def test_mind_reading(self):
        result = detect_distortions("They think I'm stupid. Nobody cares about me.")
        types = [d["type"] for d in result]
        assert "mind_reading" in types

    def test_fortune_telling(self):
        result = detect_distortions("I know it will go wrong. I'll never succeed.")
        types = [d["type"] for d in result]
        assert "fortune_telling" in types

    def test_emotional_reasoning(self):
        result = detect_distortions("I feel like a failure. I feel worthless.")
        types = [d["type"] for d in result]
        assert "emotional_reasoning" in types

    def test_personalization(self):
        result = detect_distortions("It's my fault. I caused all of this.")
        types = [d["type"] for d in result]
        assert "personalization" in types

    def test_should_statements(self):
        result = detect_distortions("I should be doing better. I must try harder.")
        types = [d["type"] for d in result]
        assert "should_statements" in types

    def test_overgeneralization(self):
        result = detect_distortions("I always fail at everything. I never succeed.")
        types = [d["type"] for d in result]
        assert "overgeneralization" in types

    def test_multiple_distortions(self):
        result = detect_distortions(
            "I always mess up. It's a disaster. I should be perfect."
        )
        assert len(result) >= 2

    def test_no_distortions(self):
        result = detect_distortions("Today was okay. I had lunch and walked outside.")
        assert result == []

    def test_case_insensitive(self):
        result = detect_distortions("This is a TERRIBLE disaster")
        types = [d["type"] for d in result]
        assert "catastrophizing" in types

    def test_all_patterns_have_entries(self):
        for pattern_type, keywords in DISTORTION_PATTERNS.items():
            assert len(keywords) > 0, f"Pattern {pattern_type} has no keywords"
            for kw in keywords:
                assert len(kw) > 0, f"Empty keyword in {pattern_type}"


class TestFallbackAnalysis:
    def test_positive_text(self):
        result = _fallback_analysis("I feel happy and grateful today. So relieved and calm.")
        assert result["sentiment_score"] > 0
        assert result["sentiment_label"] == "positive"
        assert result["dominant_emotion"] == "joy"

    def test_negative_text(self):
        result = _fallback_analysis("I feel so sad and lonely. I'm angry and upset.")
        assert result["sentiment_score"] < 0

    def test_neutral_text(self):
        result = _fallback_analysis("I went to the store and bought some milk.")
        assert result["sentiment_label"] == "neutral"

    def test_anxious_text(self):
        result = _fallback_analysis("I'm so worried and anxious. I feel afraid.")
        assert result["sentiment_score"] < 0

    def test_always_returns_distortions(self):
        result = _fallback_analysis("I always fail at everything. This is terrible.")
        assert "cognitive_distortions" in result
        assert len(result["cognitive_distortions"]) > 0

    def test_empty_text(self):
        result = _fallback_analysis("")
        assert result["sentiment_score"] >= -1.0
        assert result["sentiment_score"] <= 1.0
        assert result["dominant_emotion"] in ("joy", "sadness", "anger", "fear", "disgust")


class TestFlattenEmotionResult:
    def test_list_of_dicts(self):
        result = _flatten_emotion_result([{"label": "joy", "score": 0.9}])
        assert result == [{"label": "joy", "score": 0.9}]

    def test_nested_list(self):
        result = _flatten_emotion_result([[{"label": "joy", "score": 0.9}]])
        assert result == [{"label": "joy", "score": 0.9}]

    def test_empty_list(self):
        assert _flatten_emotion_result([]) == []

    def test_single_dict(self):
        result = _flatten_emotion_result({"label": "joy", "score": 0.9})
        assert result == [{"label": "joy", "score": 0.9}]

    def test_none(self):
        assert _flatten_emotion_result(None) == []

    def test_filters_non_dicts(self):
        result = _flatten_emotion_result([{"label": "joy"}, "not-a-dict", 42])
        assert result == [{"label": "joy"}]


class TestAnalyzeEntry:
    async def test_entry_with_distortions(self):
        result = await analyze_entry("I always fail. This is a disaster. I feel worthless.")
        assert "sentiment_score" in result
        assert "sentiment_label" in result
        assert "dominant_emotion" in result
        assert "emotions" in result
        assert "cognitive_distortions" in result
        assert len(result["cognitive_distortions"]) > 0

    async def test_entry_no_distortions(self):
        result = await analyze_entry("Today was a nice day. I enjoyed the sunshine.")
        assert "cognitive_distortions" in result
        # May or may not have distortions depending on fallback vs ML

    async def test_sentiment_bands(self):
        positive = await analyze_entry("I'm so happy and grateful!")
        assert positive["sentiment_score"] > -0.5
        assert positive["sentiment_label"] in ("positive", "neutral")


class TestAnalyzePreview:
    async def test_preview_structure(self):
        result = await analyze_preview("This is a test entry for preview.")
        assert "dominant_emotion" in result
        assert "sentiment_score" in result

    async def test_preview_no_distortions(self):
        """Preview should not include distortion analysis."""
        result = await analyze_preview("I always fail. This is terrible.")
        assert "cognitive_distortions" not in result
