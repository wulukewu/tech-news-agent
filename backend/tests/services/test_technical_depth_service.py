from app.services.technical_depth_service import TechnicalDepthLevel, TechnicalDepthService


def test_estimate_article_depth_tinkering_index():
    # Test mapping of tinkering_index to TechnicalDepthLevel
    # tinkering_index <= 2 -> basic
    assert (
        TechnicalDepthService.estimate_article_depth("", "", tinkering_index=1)
        == TechnicalDepthLevel.BASIC.value
    )
    assert (
        TechnicalDepthService.estimate_article_depth("", "", tinkering_index=2)
        == TechnicalDepthLevel.BASIC.value
    )

    # tinkering_index == 3 -> intermediate
    assert (
        TechnicalDepthService.estimate_article_depth("", "", tinkering_index=3)
        == TechnicalDepthLevel.INTERMEDIATE.value
    )

    # tinkering_index == 4 -> advanced
    assert (
        TechnicalDepthService.estimate_article_depth("", "", tinkering_index=4)
        == TechnicalDepthLevel.ADVANCED.value
    )

    # tinkering_index == 5 -> expert
    assert (
        TechnicalDepthService.estimate_article_depth("", "", tinkering_index=5)
        == TechnicalDepthLevel.EXPERT.value
    )


def test_estimate_article_depth_fallback():
    # Test that it falls back to keyword heuristics when tinkering_index is None
    # "algorithm" is an expert keyword
    assert (
        TechnicalDepthService.estimate_article_depth(
            "this is about algorithm complexity optimization", tinkering_index=None
        )
        == TechnicalDepthLevel.EXPERT.value
    )

    # Empty content should return basic
    assert (
        TechnicalDepthService.estimate_article_depth("", tinkering_index=None)
        == TechnicalDepthLevel.BASIC.value
    )
