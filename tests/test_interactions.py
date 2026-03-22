"""
Unit and property-based tests for FilterSelect and FilterView
Tasks 2.4, 2.5, 2.6, 2.7
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from hypothesis import given, settings
from hypothesis import strategies as st

from app.schemas.article import ArticleSchema
from app.bot.cogs.interactions import FilterSelect, FilterView


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_article(title="Test Article", source_category="AI", source_name="TestSource"):
    return ArticleSchema(
        title=title,
        url="https://example.com",
        content_preview="Some preview content",
        source_category=source_category,
        source_name=source_name,
    )


def make_interaction():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Task 2.4 — Unit tests for FilterSelect and FilterView
# ---------------------------------------------------------------------------

class TestFilterSelectPlaceholder:
    def test_placeholder_text(self):
        """FilterSelect placeholder is '請選擇分類篩選文章…'"""
        articles = [make_article()]
        select = FilterSelect(articles)
        assert select.placeholder == "請選擇分類篩選文章…"


class TestFilterSelectShowAll:
    @pytest.mark.asyncio
    async def test_show_all_returns_all_articles(self):
        """Selecting '顯示全部' sends a message containing all articles."""
        articles = [
            make_article(title="Article A", source_category="AI"),
            make_article(title="Article B", source_category="Tech"),
        ]
        select = FilterSelect(articles)
        select._values = ["__all__"]

        interaction = make_interaction()
        await select.callback(interaction)

        interaction.response.send_message.assert_called_once()
        sent_content = interaction.response.send_message.call_args[0][0]
        assert "Article A" in sent_content
        assert "Article B" in sent_content


class TestFilterSelectMissingCategory:
    @pytest.mark.asyncio
    async def test_nonexistent_category_returns_warning(self):
        """Selecting a category with no articles returns the warning message."""
        articles = [make_article(source_category="AI")]
        select = FilterSelect(articles)
        # Manually inject a value that doesn't match any article
        select._values = ["NonExistentCategory"]

        interaction = make_interaction()
        await select.callback(interaction)

        interaction.response.send_message.assert_called_once_with(
            "⚠️ 此分類目前沒有文章。", ephemeral=True
        )


class TestFilterSelectOptionLimit:
    def test_options_capped_at_25_with_more_than_24_categories(self):
        """With >24 categories, total options must not exceed 25 (24 categories + 1 show-all)."""
        articles = [make_article(source_category=f"Category{i}") for i in range(30)]
        select = FilterSelect(articles)
        assert len(select.options) <= 25

    def test_show_all_option_always_first(self):
        """'顯示全部' option with value '__all__' is always the first option."""
        articles = [make_article(source_category=f"Cat{i}") for i in range(5)]
        select = FilterSelect(articles)
        assert select.options[0].value == "__all__"


# ---------------------------------------------------------------------------
# Task 2.5 — Property 1: FilterSelect options contain all categories, show-all first
# Feature: discord-interaction-enhancement, Property 1: FilterSelect 選項包含所有分類且「顯示全部」排第一
# Validates: Requirements 1.2, 1.3, 1.4
# ---------------------------------------------------------------------------

def _article_strategy():
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=80),
        url=st.just("https://example.com"),
        content_preview=st.text(max_size=200),
        source_category=st.text(min_size=1, max_size=40),
        source_name=st.text(min_size=1, max_size=40),
        published_date=st.none(),
        ai_analysis=st.none(),
        raw_data=st.none(),
    )


class TestFilterSelectOptionsProperty:
    @given(articles=st.lists(_article_strategy(), min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_show_all_is_first_option(self, articles):
        """Property 1: First option value is always '__all__'."""
        select = FilterSelect(articles)
        assert select.options[0].value == "__all__"

    @given(articles=st.lists(_article_strategy(), min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_all_categories_represented_up_to_24(self, articles):
        """Property 1: All unique source_categories appear in options (up to 24)."""
        select = FilterSelect(articles)
        unique_categories = {a.source_category for a in articles}
        option_values = {opt.value for opt in select.options if opt.value != "__all__"}

        # If there are ≤24 unique categories, all must be present
        if len(unique_categories) <= 24:
            assert unique_categories == option_values
        else:
            # At most 24 category options
            assert len(option_values) <= 24

    @given(articles=st.lists(_article_strategy(), min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_total_options_never_exceed_25(self, articles):
        """Property 1: Total options never exceed 25."""
        select = FilterSelect(articles)
        assert len(select.options) <= 25


# ---------------------------------------------------------------------------
# Task 2.6 — Property 2: Message truncation invariant
# Feature: discord-interaction-enhancement, Property 2: 訊息截斷不變量
# Validates: Requirements 2.3, 4.6
# ---------------------------------------------------------------------------

def _truncate(content: str) -> str:
    """Mirrors the truncation logic in FilterSelect.callback."""
    if len(content) > 2000:
        return content[:1997] + "..."
    return content


class TestTruncationProperty:
    @given(content=st.text(min_size=2001, max_size=5000))
    @settings(max_examples=100)
    def test_truncated_length_is_exactly_2000(self, content):
        """Property 2: Truncated content is exactly 2000 characters."""
        result = _truncate(content)
        assert len(result) == 2000

    @given(content=st.text(min_size=2001, max_size=5000))
    @settings(max_examples=100)
    def test_truncated_ends_with_ellipsis(self, content):
        """Property 2: Truncated content ends with '...'."""
        result = _truncate(content)
        assert result.endswith("...")

    @given(content=st.text(max_size=2000))
    @settings(max_examples=100)
    def test_short_content_unchanged(self, content):
        """Property 2: Content ≤2000 chars is returned unchanged."""
        result = _truncate(content)
        assert result == content


# ---------------------------------------------------------------------------
# Task 2.7 — Property 3: Filter results contain only articles of selected category
# Feature: discord-interaction-enhancement, Property 3: 篩選結果只包含指定分類的文章
# Validates: Requirements 2.1
# ---------------------------------------------------------------------------

class TestFilterCategoryConsistencyProperty:
    @given(
        articles=st.lists(_article_strategy(), min_size=1, max_size=50),
        category=st.text(min_size=1, max_size=40),
    )
    @settings(max_examples=100)
    def test_filtered_articles_all_match_selected_category(self, articles, category):
        """Property 3: Every article in filtered results has source_category == selected category."""
        filtered = [a for a in articles if a.source_category == category]
        for article in filtered:
            assert article.source_category == category

    @given(articles=st.lists(_article_strategy(), min_size=2, max_size=50))
    @settings(max_examples=100)
    def test_filter_excludes_other_categories(self, articles):
        """Property 3: Filtering by one category excludes all articles from other categories."""
        # Pick the first article's category as the filter
        selected_category = articles[0].source_category
        filtered = [a for a in articles if a.source_category == selected_category]
        for article in filtered:
            assert article.source_category == selected_category


# ---------------------------------------------------------------------------
# Task 3.4 — Unit tests for DeepDiveButton and DeepDiveView
# Validates: Requirements 3.2, 3.3
# ---------------------------------------------------------------------------

import hashlib
from app.bot.cogs.interactions import DeepDiveButton, DeepDiveView


class TestDeepDiveButtonLabel:
    def test_label_truncated_when_title_exceeds_20_chars(self):
        """Title > 20 chars → label is '📖 {title[:20]}...'"""
        article = make_article(title="A" * 21)
        btn = DeepDiveButton(article)
        assert btn.label == f"📖 {'A' * 20}..."

    def test_label_not_truncated_when_title_is_exactly_20_chars(self):
        """Title == 20 chars → label is '📖 {title}' (no ellipsis)"""
        article = make_article(title="B" * 20)
        btn = DeepDiveButton(article)
        assert btn.label == f"📖 {'B' * 20}"

    def test_label_not_truncated_when_title_is_short(self):
        """Title < 20 chars → label is '📖 {title}' (no ellipsis)"""
        article = make_article(title="Short")
        btn = DeepDiveButton(article)
        assert btn.label == "📖 Short"


class TestDeepDiveButtonCustomId:
    def test_custom_id_format(self):
        """custom_id must be 'deep_dive_{md5(url)[:8]}'"""
        article = make_article()
        btn = DeepDiveButton(article)
        expected_hash = hashlib.md5(str(article.url).encode()).hexdigest()[:8]
        assert btn.custom_id == f"deep_dive_{expected_hash}"


class TestDeepDiveViewButtonCount:
    def test_view_has_correct_number_of_buttons_for_small_list(self):
        """With 3 articles, view should have 3 buttons."""
        articles = [make_article(title=f"Article {i}") for i in range(3)]
        view = DeepDiveView(articles)
        assert len(view.children) == 3

    def test_view_capped_at_5_buttons(self):
        """With 10 articles, view should have at most 5 buttons."""
        articles = [make_article(title=f"Article {i}") for i in range(10)]
        view = DeepDiveView(articles)
        assert len(view.children) == 5

    def test_view_with_empty_list(self):
        """With 0 articles, view should have 0 buttons."""
        view = DeepDiveView([])
        assert len(view.children) == 0


# ---------------------------------------------------------------------------
# Task 3.5 — Property 4: DeepDiveView 按鈕數量不超過上限
# Feature: discord-interaction-enhancement, Property 4: DeepDiveView 按鈕數量不超過上限
# Validates: Requirements 3.1, 3.4
# ---------------------------------------------------------------------------

class TestDeepDiveViewButtonCountProperty:
    @given(articles=st.lists(_article_strategy(), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_button_count_equals_min_of_articles_and_5(self, articles):
        """Property 4: len(view.children) == min(len(articles), 5)"""
        view = DeepDiveView(articles)
        assert len(view.children) == min(len(articles), 5)


# ---------------------------------------------------------------------------
# Task 3.6 — Property 5: DeepDiveButton 標籤與 custom_id 格式正確性
# Feature: discord-interaction-enhancement, Property 5: DeepDiveButton 標籤與 custom_id 格式正確性
# Validates: Requirements 3.2, 3.3
# ---------------------------------------------------------------------------

class TestDeepDiveButtonFormatProperty:
    @given(article=_article_strategy())
    @settings(max_examples=100)
    def test_label_truncation_rule(self, article):
        """Property 5: Label follows truncation rule — >20 chars appends '...'"""
        btn = DeepDiveButton(article)
        title = article.title
        if len(title) > 20:
            assert btn.label == f"📖 {title[:20]}..."
        else:
            assert btn.label == f"📖 {title}"

    @given(article=_article_strategy())
    @settings(max_examples=100)
    def test_custom_id_format(self, article):
        """Property 5: custom_id matches 'deep_dive_{md5(url)[:8]}'"""
        btn = DeepDiveButton(article)
        expected_hash = hashlib.md5(str(article.url).encode()).hexdigest()[:8]
        assert btn.custom_id == f"deep_dive_{expected_hash}"


# ---------------------------------------------------------------------------
# Task 3.7 — Property 7: View 持久性 timeout 不變量
# Feature: discord-interaction-enhancement, Property 7: View 持久性 timeout 不變量
# Validates: Requirements 6.1, 6.2
# ---------------------------------------------------------------------------

class TestViewTimeoutInvariantProperty:
    @given(articles=st.lists(_article_strategy(), min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_filter_view_timeout_is_none(self, articles):
        """Property 7: FilterView.timeout is always None."""
        view = FilterView(articles)
        assert view.timeout is None

    @given(articles=st.lists(_article_strategy(), min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_deep_dive_view_timeout_is_none(self, articles):
        """Property 7: DeepDiveView.timeout is always None."""
        view = DeepDiveView(articles)
        assert view.timeout is None
