"""
Unit tests for WeeklyDigestResult schema
Validates: Requirements 6.5
"""
import pytest
from pydantic import ValidationError
from typing import List

from app.schemas.article import ArticleSchema, AIAnalysis, WeeklyDigestResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ai_analysis(**kwargs):
    defaults = dict(
        is_hardcore=True,
        reason="Solid deep-dive on distributed tracing.",
        actionable_takeaway="Try OpenTelemetry in your next service.",
        tinkering_index=3,
    )
    defaults.update(kwargs)
    return AIAnalysis(**defaults)


def make_article(
    title="Test Article",
    url="https://example.com/article",
    category="AI",
    source_name="TestSource",
    ai_analysis=None,
):
    return ArticleSchema(
        title=title,
        url=url,
        content_preview="A short preview of the article content.",
        source_category=category,
        source_name=source_name,
        ai_analysis=ai_analysis,
    )


def make_digest_result(
    page_id="page-abc123",
    page_url="https://notion.so/page-abc123",
    article_count=3,
    top_articles=None,
):
    if top_articles is None:
        top_articles = [make_article(title=f"Article {i}") for i in range(3)]
    return WeeklyDigestResult(
        page_id=page_id,
        page_url=page_url,
        article_count=article_count,
        top_articles=top_articles,
    )


# ---------------------------------------------------------------------------
# Field completeness
# ---------------------------------------------------------------------------

class TestWeeklyDigestResultFields:
    def test_has_page_id_field(self):
        """WeeklyDigestResult exposes a page_id field."""
        result = make_digest_result()
        assert hasattr(result, "page_id")

    def test_has_page_url_field(self):
        """WeeklyDigestResult exposes a page_url field."""
        result = make_digest_result()
        assert hasattr(result, "page_url")

    def test_has_article_count_field(self):
        """WeeklyDigestResult exposes an article_count field."""
        result = make_digest_result()
        assert hasattr(result, "article_count")

    def test_has_top_articles_field(self):
        """WeeklyDigestResult exposes a top_articles field."""
        result = make_digest_result()
        assert hasattr(result, "top_articles")

    def test_all_four_fields_present(self):
        """WeeklyDigestResult has exactly the four required fields."""
        fields = set(WeeklyDigestResult.model_fields.keys())
        assert fields == {"page_id", "page_url", "article_count", "top_articles"}


# ---------------------------------------------------------------------------
# Type correctness
# ---------------------------------------------------------------------------

class TestWeeklyDigestResultTypes:
    def test_page_id_is_str(self):
        """page_id field is of type str."""
        result = make_digest_result(page_id="some-id")
        assert isinstance(result.page_id, str)

    def test_page_url_is_str(self):
        """page_url field is of type str."""
        result = make_digest_result(page_url="https://notion.so/abc")
        assert isinstance(result.page_url, str)

    def test_article_count_is_int(self):
        """article_count field is of type int."""
        result = make_digest_result(article_count=5)
        assert isinstance(result.article_count, int)

    def test_top_articles_is_list(self):
        """top_articles field is a list."""
        result = make_digest_result()
        assert isinstance(result.top_articles, list)

    def test_top_articles_elements_are_article_schema(self):
        """Each element in top_articles is an ArticleSchema instance."""
        articles = [make_article(title=f"Article {i}") for i in range(2)]
        result = make_digest_result(top_articles=articles)
        for article in result.top_articles:
            assert isinstance(article, ArticleSchema)


# ---------------------------------------------------------------------------
# Valid instantiation
# ---------------------------------------------------------------------------

class TestWeeklyDigestResultInstantiation:
    def test_instantiation_with_minimal_valid_data(self):
        """WeeklyDigestResult can be instantiated with all required fields."""
        result = WeeklyDigestResult(
            page_id="page-001",
            page_url="https://notion.so/page-001",
            article_count=0,
            top_articles=[],
        )
        assert result.page_id == "page-001"
        assert result.page_url == "https://notion.so/page-001"
        assert result.article_count == 0
        assert result.top_articles == []

    def test_instantiation_with_multiple_articles(self):
        """WeeklyDigestResult stores all provided articles in top_articles."""
        articles = [make_article(title=f"Article {i}") for i in range(5)]
        result = WeeklyDigestResult(
            page_id="page-xyz",
            page_url="https://notion.so/page-xyz",
            article_count=5,
            top_articles=articles,
        )
        assert len(result.top_articles) == 5

    def test_instantiation_with_articles_containing_ai_analysis(self):
        """WeeklyDigestResult accepts articles that include ai_analysis."""
        article = make_article(ai_analysis=make_ai_analysis())
        result = WeeklyDigestResult(
            page_id="page-ai",
            page_url="https://notion.so/page-ai",
            article_count=1,
            top_articles=[article],
        )
        assert result.top_articles[0].ai_analysis is not None
        assert result.top_articles[0].ai_analysis.is_hardcore is True

    def test_field_values_are_preserved(self):
        """WeeklyDigestResult preserves exact values passed during construction."""
        articles = [make_article()]
        result = WeeklyDigestResult(
            page_id="exact-id",
            page_url="https://notion.so/exact",
            article_count=42,
            top_articles=articles,
        )
        assert result.page_id == "exact-id"
        assert result.page_url == "https://notion.so/exact"
        assert result.article_count == 42
        assert len(result.top_articles) == 1


# ---------------------------------------------------------------------------
# Validation errors for invalid data
# ---------------------------------------------------------------------------

class TestWeeklyDigestResultValidation:
    def test_missing_page_id_raises_validation_error(self):
        """WeeklyDigestResult raises ValidationError when page_id is missing."""
        with pytest.raises(ValidationError):
            WeeklyDigestResult(
                page_url="https://notion.so/page",
                article_count=1,
                top_articles=[],
            )

    def test_missing_page_url_raises_validation_error(self):
        """WeeklyDigestResult raises ValidationError when page_url is missing."""
        with pytest.raises(ValidationError):
            WeeklyDigestResult(
                page_id="page-001",
                article_count=1,
                top_articles=[],
            )

    def test_missing_article_count_raises_validation_error(self):
        """WeeklyDigestResult raises ValidationError when article_count is missing."""
        with pytest.raises(ValidationError):
            WeeklyDigestResult(
                page_id="page-001",
                page_url="https://notion.so/page",
                top_articles=[],
            )

    def test_missing_top_articles_raises_validation_error(self):
        """WeeklyDigestResult raises ValidationError when top_articles is missing."""
        with pytest.raises(ValidationError):
            WeeklyDigestResult(
                page_id="page-001",
                page_url="https://notion.so/page",
                article_count=1,
            )

    def test_article_count_as_string_raises_validation_error(self):
        """WeeklyDigestResult raises ValidationError when article_count is a non-numeric string."""
        with pytest.raises(ValidationError):
            WeeklyDigestResult(
                page_id="page-001",
                page_url="https://notion.so/page",
                article_count="not-a-number",
                top_articles=[],
            )

    def test_top_articles_as_non_list_raises_validation_error(self):
        """WeeklyDigestResult raises ValidationError when top_articles is not a list."""
        with pytest.raises(ValidationError):
            WeeklyDigestResult(
                page_id="page-001",
                page_url="https://notion.so/page",
                article_count=1,
                top_articles="not-a-list",
            )

    def test_top_articles_with_invalid_element_raises_validation_error(self):
        """WeeklyDigestResult raises ValidationError when top_articles contains a non-ArticleSchema item."""
        with pytest.raises(ValidationError):
            WeeklyDigestResult(
                page_id="page-001",
                page_url="https://notion.so/page",
                article_count=1,
                top_articles=[{"invalid": "dict"}],
            )


# ===========================================================================
# Property-based tests for NotionService.build_digest_blocks
# ===========================================================================

from hypothesis import given, settings as h_settings, assume
from hypothesis import strategies as st

from app.services.notion_service import NotionService


# ---------------------------------------------------------------------------
# Hypothesis strategy: generate ArticleSchema with ai_analysis
# ---------------------------------------------------------------------------

ai_analysis_strategy = st.builds(
    AIAnalysis,
    is_hardcore=st.booleans(),
    reason=st.text(min_size=1, max_size=200),
    actionable_takeaway=st.text(max_size=200),
    tinkering_index=st.integers(min_value=1, max_value=5),
)

article_strategy = st.builds(
    ArticleSchema,
    title=st.text(min_size=1, max_size=100),
    url=st.just("https://example.com/article"),
    content_preview=st.text(max_size=200),
    source_category=st.sampled_from(["AI", "DevOps", "Security", "Web", "Cloud"]),
    source_name=st.text(min_size=1, max_size=50),
    ai_analysis=ai_analysis_strategy,
)

stats_strategy = st.fixed_dictionaries({
    "total_fetched": st.integers(min_value=0),
    "hardcore_count": st.integers(min_value=0),
    "run_date": st.text(min_size=1),
})


# ---------------------------------------------------------------------------
# Helper: extract all blocks of a given type (top-level only)
# ---------------------------------------------------------------------------

def blocks_of_type(blocks: list, block_type: str) -> list:
    return [b for b in blocks if b.get("type") == block_type]


def get_rich_text_content(block: dict) -> str:
    """Extract plain text from a block's rich_text list."""
    block_type = block["type"]
    inner = block.get(block_type, {})
    rich_text = inner.get("rich_text", [])
    return "".join(part.get("text", {}).get("content", "") for part in rich_text)


# ---------------------------------------------------------------------------
# Property 3: Stats Callout exists
# ---------------------------------------------------------------------------

# Feature: notion-weekly-digest, Property 3: 統計摘要 Callout 存在且包含正確資料
@given(stats=stats_strategy)
@h_settings(max_examples=100)
def test_stats_callout_present(stats):
    """Validates: Requirements 3.1"""
    blocks = NotionService.build_digest_blocks([], "intro", stats)
    callouts = blocks_of_type(blocks, "callout")
    assert len(callouts) >= 1, "Expected at least one callout block"

    # At least one callout must contain both total_fetched and hardcore_count
    found = False
    for callout in callouts:
        text = get_rich_text_content(callout)
        if str(stats["total_fetched"]) in text and str(stats["hardcore_count"]) in text:
            found = True
            break
    assert found, (
        f"No callout contains both total_fetched={stats['total_fetched']} "
        f"and hardcore_count={stats['hardcore_count']}"
    )


# ---------------------------------------------------------------------------
# Property 4: Each source_category maps to one heading_2
# ---------------------------------------------------------------------------

# Feature: notion-weekly-digest, Property 4: 每個 source_category 對應一個 heading_2 Block
@given(articles=st.lists(article_strategy, min_size=1))
@h_settings(max_examples=100)
def test_category_headings(articles):
    """Validates: Requirements 3.2"""
    blocks = NotionService.build_digest_blocks(articles, "intro", {"total_fetched": 0, "hardcore_count": 0, "run_date": "2025-01-01"})
    headings = blocks_of_type(blocks, "heading_2")

    unique_categories = list(dict.fromkeys(a.source_category for a in articles))

    assert len(headings) == len(unique_categories), (
        f"Expected {len(unique_categories)} heading_2 blocks, got {len(headings)}"
    )

    heading_texts = [get_rich_text_content(h) for h in headings]
    for cat in unique_categories:
        assert any(cat in t for t in heading_texts), (
            f"No heading_2 found for category '{cat}'"
        )


# ---------------------------------------------------------------------------
# Property 5: Each article has a toggle block with tinkering index
# ---------------------------------------------------------------------------

# Feature: notion-weekly-digest, Property 5: 每篇文章對應一個含折騰指數的 toggle Block
@given(articles=st.lists(article_strategy, min_size=1))
@h_settings(max_examples=100)
def test_article_toggle_blocks(articles):
    """Validates: Requirements 3.3"""
    blocks = NotionService.build_digest_blocks(articles, "intro", {"total_fetched": 0, "hardcore_count": 0, "run_date": "2025-01-01"})
    toggles = blocks_of_type(blocks, "toggle")

    assert len(toggles) == len(articles), (
        f"Expected {len(articles)} toggle blocks, got {len(toggles)}"
    )

    toggle_texts = [get_rich_text_content(t) for t in toggles]
    for article in articles:
        tinkering_index = article.ai_analysis.tinkering_index if article.ai_analysis else 0
        expected_index_str = str(tinkering_index)
        found = any(
            expected_index_str in text and article.title in text
            for text in toggle_texts
        )
        assert found, (
            f"No toggle found containing tinkering_index={tinkering_index} "
            f"and title='{article.title}'"
        )


# ---------------------------------------------------------------------------
# Property 6: Toggle children structure determined by article data
# ---------------------------------------------------------------------------

# Feature: notion-weekly-digest, Property 6: toggle 子 Block 結構由文章資料決定
@given(article=article_strategy)
@h_settings(max_examples=100)
def test_toggle_children_structure(article):
    """Validates: Requirements 3.4, 3.6"""
    blocks = NotionService.build_digest_blocks([article], "intro", {"total_fetched": 0, "hardcore_count": 0, "run_date": "2025-01-01"})
    toggles = blocks_of_type(blocks, "toggle")
    assert len(toggles) == 1

    toggle = toggles[0]
    children = toggle["toggle"]["children"]

    # Must have a bookmark with the article URL
    bookmarks = [c for c in children if c.get("type") == "bookmark"]
    assert len(bookmarks) == 1
    assert bookmarks[0]["bookmark"]["url"] == str(article.url)

    # Must have a callout with reason
    callouts = [c for c in children if c.get("type") == "callout"]
    reason = article.ai_analysis.reason if article.ai_analysis else ""
    reason_callouts = [
        c for c in callouts
        if reason in get_rich_text_content(c)
    ]
    assert len(reason_callouts) >= 1, f"No callout found with reason='{reason}'"

    # actionable_takeaway: present iff non-empty
    takeaway = (article.ai_analysis.actionable_takeaway or "") if article.ai_analysis else ""
    takeaway_callouts = [
        c for c in callouts
        if takeaway and takeaway in get_rich_text_content(c) and "行動價值" in get_rich_text_content(c)
    ]
    if takeaway:
        assert len(takeaway_callouts) >= 1, (
            f"Expected a takeaway callout for actionable_takeaway='{takeaway}'"
        )
    else:
        # No callout should contain "行動價值" when takeaway is empty
        action_callouts = [
            c for c in callouts
            if "行動價值" in get_rich_text_content(c)
        ]
        assert len(action_callouts) == 0, (
            "Found unexpected 行動價值 callout when actionable_takeaway is empty"
        )


# ---------------------------------------------------------------------------
# Property 7: intro_text is the first paragraph block
# ---------------------------------------------------------------------------

# Feature: notion-weekly-digest, Property 7: intro_text 為 Block 列表的第一個 paragraph
@given(intro_text=st.text())
@h_settings(max_examples=100)
def test_intro_paragraph_first(intro_text):
    """Validates: Requirements 4.3"""
    blocks = NotionService.build_digest_blocks([], intro_text, {"total_fetched": 0, "hardcore_count": 0, "run_date": "2025-01-01"})
    assert len(blocks) >= 1
    first = blocks[0]
    assert first["type"] == "paragraph", f"First block type is '{first['type']}', expected 'paragraph'"
    text = get_rich_text_content(first)
    assert text == intro_text, f"First paragraph text '{text}' != intro_text '{intro_text}'"


# ===========================================================================
# Unit tests for build_digest_blocks (Task 4.6)
# ===========================================================================

class TestBuildDigestBlocksUnit:
    """Unit tests for NotionService.build_digest_blocks — Requirements 3.6"""

    _default_stats = {"total_fetched": 10, "hardcore_count": 3, "run_date": "2025-07-11"}

    def _make_article(self, title="Test Article", category="AI", takeaway="Some takeaway", tinkering_index=3):
        return ArticleSchema(
            title=title,
            url="https://example.com/article",
            content_preview="Preview text.",
            source_category=category,
            source_name="TestSource",
            ai_analysis=AIAnalysis(
                is_hardcore=True,
                reason="Great article.",
                actionable_takeaway=takeaway,
                tinkering_index=tinkering_index,
            ),
        )

    def test_empty_actionable_takeaway_omits_callout(self):
        """actionable_takeaway == '' must omit the 行動價值 callout from toggle children."""
        article = self._make_article(takeaway="")
        blocks = NotionService.build_digest_blocks([article], "intro", self._default_stats)
        toggles = [b for b in blocks if b["type"] == "toggle"]
        assert len(toggles) == 1
        children = toggles[0]["toggle"]["children"]
        action_callouts = [
            c for c in children
            if c.get("type") == "callout" and "行動價值" in get_rich_text_content(c)
        ]
        assert len(action_callouts) == 0, "Expected no 行動價值 callout when actionable_takeaway is empty"

    def test_non_empty_actionable_takeaway_includes_callout(self):
        """actionable_takeaway != '' must include the 行動價值 callout in toggle children."""
        article = self._make_article(takeaway="Deploy with Docker Compose.")
        blocks = NotionService.build_digest_blocks([article], "intro", self._default_stats)
        toggles = [b for b in blocks if b["type"] == "toggle"]
        children = toggles[0]["toggle"]["children"]
        action_callouts = [
            c for c in children
            if c.get("type") == "callout" and "行動價值" in get_rich_text_content(c)
        ]
        assert len(action_callouts) == 1

    def test_empty_article_list_produces_valid_structure(self):
        """Empty article list → paragraph + callout + divider; no heading_2 or toggle."""
        blocks = NotionService.build_digest_blocks([], "Hello", self._default_stats)

        types = [b["type"] for b in blocks]
        assert types[0] == "paragraph"
        assert "callout" in types
        assert types[-1] == "divider"
        assert "heading_2" not in types
        assert "toggle" not in types

    def test_empty_article_list_paragraph_text(self):
        """Empty article list: first paragraph contains the intro_text."""
        intro = "Weekly intro text."
        blocks = NotionService.build_digest_blocks([], intro, self._default_stats)
        assert get_rich_text_content(blocks[0]) == intro

    def test_stats_callout_contains_values(self):
        """Stats callout text includes total_fetched and hardcore_count values."""
        stats = {"total_fetched": 42, "hardcore_count": 7, "run_date": "2025-07-11"}
        blocks = NotionService.build_digest_blocks([], "intro", stats)
        callouts = [b for b in blocks if b["type"] == "callout"]
        assert any(
            "42" in get_rich_text_content(c) and "7" in get_rich_text_content(c)
            for c in callouts
        )

    def test_toggle_title_format(self):
        """Toggle title follows '[折騰指數 N/5] 文章標題' format."""
        article = self._make_article(title="My Article", tinkering_index=4)
        blocks = NotionService.build_digest_blocks([article], "intro", self._default_stats)
        toggles = [b for b in blocks if b["type"] == "toggle"]
        title_text = get_rich_text_content(toggles[0])
        assert "[折騰指數 4/5]" in title_text
        assert "My Article" in title_text

    def test_last_block_is_divider(self):
        """The last block is always a divider."""
        blocks = NotionService.build_digest_blocks([], "intro", self._default_stats)
        assert blocks[-1]["type"] == "divider"

    def test_multiple_categories_produce_multiple_headings(self):
        """Multiple distinct source_categories produce one heading_2 each."""
        articles = [
            self._make_article(title="A1", category="AI"),
            self._make_article(title="D1", category="DevOps"),
            self._make_article(title="A2", category="AI"),
        ]
        blocks = NotionService.build_digest_blocks(articles, "intro", self._default_stats)
        headings = [b for b in blocks if b["type"] == "heading_2"]
        assert len(headings) == 2
        heading_texts = [get_rich_text_content(h) for h in headings]
        assert any("AI" in t for t in heading_texts)
        assert any("DevOps" in t for t in heading_texts)
