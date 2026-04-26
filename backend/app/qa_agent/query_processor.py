"""
Query Processor for Natural Language Query Parsing

This module implements the QueryProcessor class that handles natural language
query parsing with Chinese and English support, intent classification, keyword
extraction, and query validation.

Requirements: 1.1, 1.2, 1.5
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from app.core.logger import get_logger
from app.qa_agent.constants import (
    ErrorCodes,
    LanguageConstants,
    MessageTemplates,
    PerformanceLimits,
)
from app.qa_agent.models import ConversationContext, ParsedQuery, QueryIntent, QueryLanguage

logger = get_logger(__name__)


class QueryValidationResult:
    """Result of query validation with error details."""

    def __init__(
        self,
        is_valid: bool,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
    ):
        self.is_valid = is_valid
        self.error_code = error_code
        self.error_message = error_message
        self.suggestions = suggestions or []

    def __bool__(self) -> bool:
        """Allow boolean evaluation."""
        return self.is_valid


class QueryProcessor:
    """
    Processes natural language queries with Chinese and English support.

    Handles:
    - Language detection
    - Intent classification
    - Keyword extraction
    - Query validation and error handling
    - Query expansion with conversation context

    Requirements: 1.1, 1.2, 1.5
    """

    def __init__(self):
        """Initialize QueryProcessor with language patterns and intent keywords."""
        self.logger = logger

        # Language detection patterns
        self.chinese_pattern = re.compile(LanguageConstants.CHINESE_CHAR_PATTERN)
        self.english_pattern = re.compile(LanguageConstants.ENGLISH_CHAR_PATTERN)

        # Intent classification keywords (Chinese and English)
        self.intent_keywords = {
            QueryIntent.QUESTION: {
                "zh": [
                    "什麼",
                    "為什麼",
                    "如何",
                    "怎麼",
                    "哪裡",
                    "誰",
                    "何時",
                    "是否",
                    "能否",
                    "可以",
                ],
                "en": ["what", "why", "how", "where", "who", "when", "is", "can", "could", "would"],
            },
            QueryIntent.COMPARISON: {
                "zh": ["比較", "對比", "差異", "區別", "哪個更好", "優缺點", "vs"],
                "en": [
                    "compare",
                    "comparison",
                    "difference",
                    "versus",
                    "vs",
                    "better",
                    "pros and cons",
                ],
            },
            QueryIntent.SUMMARY: {
                "zh": ["總結", "摘要", "概述", "簡介", "介紹"],
                "en": ["summary", "summarize", "overview", "brief", "introduction"],
            },
            QueryIntent.RECOMMENDATION: {
                "zh": ["推薦", "建議", "推薦一些", "有什麼好的", "最好的"],
                "en": ["recommend", "suggestion", "best", "top", "good"],
            },
            QueryIntent.CLARIFICATION: {
                "zh": ["更多", "詳細", "具體", "進一步", "深入"],
                "en": ["more", "detail", "specific", "further", "elaborate"],
            },
            QueryIntent.EXPLORATION: {
                "zh": ["探索", "了解", "學習", "深入研究", "相關"],
                "en": ["explore", "learn", "understand", "dive into", "related"],
            },
        }

        # Stop words for keyword extraction
        self.stop_words = {
            "zh": [
                "的",
                "了",
                "在",
                "是",
                "我",
                "有",
                "和",
                "就",
                "不",
                "人",
                "都",
                "一",
                "一個",
                "上",
                "也",
                "很",
                "到",
                "說",
                "要",
                "去",
                "你",
                "會",
                "著",
                "沒有",
                "看",
                "好",
                "自己",
                "這",
            ],
            "en": [
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "from",
                "as",
                "is",
                "was",
                "are",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "should",
                "could",
                "may",
                "might",
                "can",
                "this",
                "that",
                "these",
                "those",
                "i",
                "you",
                "he",
                "she",
                "it",
                "we",
                "they",
                "what",
                "which",
                "who",
                "when",
                "where",
                "why",
                "how",
            ],
        }

        # Time range patterns - Enhanced for task 4.2
        self.time_patterns = {
            "zh": {
                "今天": timedelta(days=0),
                "昨天": timedelta(days=1),
                "本週": timedelta(weeks=1),
                "上週": timedelta(weeks=2),
                "本月": timedelta(days=30),
                "上月": timedelta(days=60),
                "今年": timedelta(days=365),
                "去年": timedelta(days=730),
                "最近": timedelta(days=7),
                "最近一週": timedelta(days=7),
                "最近兩週": timedelta(days=14),
                "最近一個月": timedelta(days=30),
                "最近三個月": timedelta(days=90),
                "最近半年": timedelta(days=180),
                "過去一年": timedelta(days=365),
            },
            "en": {
                "today": timedelta(days=0),
                "yesterday": timedelta(days=1),
                "this week": timedelta(weeks=1),
                "last week": timedelta(weeks=2),
                "this month": timedelta(days=30),
                "last month": timedelta(days=60),
                "this year": timedelta(days=365),
                "last year": timedelta(days=730),
                "recent": timedelta(days=7),
                "recently": timedelta(days=7),
                "past week": timedelta(days=7),
                "past 2 weeks": timedelta(days=14),
                "past month": timedelta(days=30),
                "past 3 months": timedelta(days=90),
                "past 6 months": timedelta(days=180),
                "past year": timedelta(days=365),
                "last 3 months": timedelta(days=90),
                "last 6 months": timedelta(days=180),
            },
        }

        # Topic/category keywords for filtering - Task 4.2
        self.topic_keywords = {
            "zh": {
                "編程": ["programming", "coding"],
                "人工智能": ["ai", "artificial intelligence", "machine learning"],
                "機器學習": ["machine learning", "ml"],
                "深度學習": ["deep learning", "dl"],
                "網頁開發": ["web development", "frontend", "backend"],
                "移動開發": ["mobile development", "ios", "android"],
                "數據科學": ["data science", "analytics"],
                "雲計算": ["cloud computing", "aws", "azure"],
                "安全": ["security", "cybersecurity"],
                "DevOps": ["devops", "ci/cd"],
            },
            "en": {
                "programming": ["coding", "development"],
                "ai": ["artificial intelligence", "machine learning"],
                "machine learning": ["ml", "ai"],
                "deep learning": ["dl", "neural networks"],
                "web development": ["frontend", "backend", "fullstack"],
                "mobile development": ["ios", "android", "react native"],
                "data science": ["analytics", "data analysis"],
                "cloud computing": ["aws", "azure", "gcp"],
                "security": ["cybersecurity", "infosec"],
                "devops": ["ci/cd", "automation"],
            },
        }

        # Synonym mappings for query expansion - Task 4.2
        self.synonyms = {
            "zh": {
                "學習": ["了解", "掌握", "研究"],
                "最好": ["最佳", "優秀", "推薦"],
                "框架": ["庫", "工具", "平台"],
                "教程": ["指南", "文檔", "資料"],
                "問題": ["錯誤", "bug", "故障"],
            },
            "en": {
                "learn": ["understand", "study", "master"],
                "best": ["top", "recommended", "excellent"],
                "framework": ["library", "tool", "platform"],
                "tutorial": ["guide", "documentation", "resource"],
                "problem": ["issue", "bug", "error"],
            },
        }

    async def parse_query(
        self, query: str, language: str = "auto", context: Optional[ConversationContext] = None
    ) -> ParsedQuery:
        """
        Parse a natural language query and extract structured information.

        Args:
            query: User's natural language query
            language: Language code ("zh", "en", or "auto" for detection)
            context: Optional conversation context for contextual understanding

        Returns:
            ParsedQuery object with extracted information

        Requirements: 1.1, 1.2
        """
        self.logger.info(f"Parsing query: {query[:100]}...")

        # Detect language if auto
        if language == "auto" or language == QueryLanguage.AUTO_DETECT:
            detected_lang = self._detect_language(query)
        else:
            detected_lang = QueryLanguage(language)

        # Classify intent
        intent, confidence = self._classify_intent(query, detected_lang)

        # Extract keywords
        keywords = await self.extract_keywords(query, detected_lang)

        # Extract filters (time range, categories, etc.)
        filters = self._extract_filters(query, detected_lang)

        # Create parsed query
        parsed_query = ParsedQuery(
            original_query=query,
            language=detected_lang,
            intent=intent,
            keywords=keywords,
            filters=filters,
            confidence=confidence,
            processed_at=datetime.utcnow(),
        )

        self.logger.info(
            f"Query parsed - Language: {detected_lang}, Intent: {intent}, "
            f"Confidence: {confidence:.2f}, Keywords: {len(keywords)}"
        )

        return parsed_query

    def _detect_language(self, query: str) -> QueryLanguage:
        """
        Detect the language of the query.

        Args:
            query: Query text

        Returns:
            Detected language (zh or en)

        Requirements: 1.2
        """
        # Count Chinese and English characters
        chinese_chars = len(self.chinese_pattern.findall(query))
        english_chars = len(self.english_pattern.findall(query))

        # Determine language based on character counts
        if chinese_chars > english_chars:
            return QueryLanguage.CHINESE
        elif english_chars > 0:
            return QueryLanguage.ENGLISH
        else:
            # Default to Chinese if no clear language detected
            return QueryLanguage.CHINESE

    def _classify_intent(self, query: str, language: QueryLanguage) -> Tuple[QueryIntent, float]:
        """
        Classify the intent of the query.

        Args:
            query: Query text
            language: Detected language

        Returns:
            Tuple of (intent, confidence_score)

        Requirements: 1.1
        """
        query_lower = query.lower()
        lang_code = language.value

        # Score each intent based on keyword matches
        intent_scores: Dict[QueryIntent, float] = {}

        for intent, keywords_dict in self.intent_keywords.items():
            keywords = keywords_dict.get(lang_code, [])
            matches = sum(1 for keyword in keywords if keyword in query_lower)

            if matches > 0:
                # Calculate confidence based on number of matches
                intent_scores[intent] = min(matches / len(keywords), 1.0)

        # If no specific intent detected, classify as SEARCH
        if not intent_scores:
            # Check if it's a question (contains question mark)
            if "?" in query or "？" in query:
                return QueryIntent.QUESTION, 0.6
            return QueryIntent.SEARCH, 0.5

        # Get intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent, raw_score = best_intent

        # Adjust confidence based on query length and clarity
        confidence = self._adjust_confidence(query, raw_score)

        return intent, confidence

    def _adjust_confidence(self, query: str, raw_score: float) -> float:
        """
        Adjust confidence score based on query characteristics.

        Args:
            query: Query text
            raw_score: Raw confidence score from intent classification

        Returns:
            Adjusted confidence score
        """
        # Penalize very short queries
        if len(query.strip()) < 5:
            raw_score *= 0.5

        # Penalize very long queries (might be unclear)
        if len(query) > 500:
            raw_score *= 0.8

        # Boost confidence for queries with clear structure
        if any(marker in query for marker in ["?", "？", ":", "："]):
            raw_score = min(raw_score * 1.2, 1.0)

        return max(0.0, min(raw_score, 1.0))

    async def extract_keywords(
        self, query: str, language: Optional[QueryLanguage] = None
    ) -> List[str]:
        """
        Extract keywords from the query for search.

        Args:
            query: Query text
            language: Optional language hint

        Returns:
            List of extracted keywords

        Requirements: 1.1
        """
        if language is None:
            language = self._detect_language(query)

        lang_code = language.value

        # Remove punctuation and split into words
        # For Chinese, we'll use character-based splitting
        # For English, we'll use word-based splitting

        if language == QueryLanguage.CHINESE:
            keywords = self._extract_chinese_keywords(query)
        else:
            keywords = self._extract_english_keywords(query)

        # Remove stop words
        stop_words = self.stop_words.get(lang_code, [])
        keywords = [kw for kw in keywords if kw.lower() not in stop_words]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                unique_keywords.append(kw)
                seen.add(kw_lower)

        # Limit to max keywords
        return unique_keywords[: PerformanceLimits.MAX_KEYWORDS_PER_QUERY]

    def _extract_chinese_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from Chinese text.

        Uses simple character-based extraction with common patterns.
        In production, this would use a proper Chinese word segmentation library like jieba.

        Args:
            query: Chinese query text

        Returns:
            List of keywords
        """
        # Remove punctuation
        punctuation = "，。！？；：、" "''（）【】《》〈〉「」『』〔〕…—～·"
        for p in punctuation:
            query = query.replace(p, " ")

        # For now, use simple character-based extraction
        # In production, use jieba or similar library for proper word segmentation
        words = query.split()

        # Filter out single characters and very short words
        keywords = [w.strip() for w in words if len(w.strip()) >= 2]

        return keywords

    def _extract_english_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from English text.

        Args:
            query: English query text

        Returns:
            List of keywords
        """
        # Remove punctuation except hyphens in words
        query = re.sub(r"[^\w\s-]", " ", query)

        # Split into words
        words = query.split()

        # Filter out very short words
        keywords = [w.strip() for w in words if len(w.strip()) >= 2]

        return keywords

    def _extract_filters(self, query: str, language: QueryLanguage) -> Dict[str, any]:
        """
        Extract filters from the query (time range, categories, etc.).
        Enhanced for task 4.2 to support multiple simultaneous filters.

        Args:
            query: Query text
            language: Detected language

        Returns:
            Dictionary of extracted filters

        Requirements: 1.3, 1.4, 4.2
        """
        filters = {}
        lang_code = language.value

        # Extract time range (includes both basic and advanced patterns)
        time_range = self._extract_time_range(query, lang_code)
        if time_range:
            filters["time_range"] = time_range

        # Extract technical depth indicators
        technical_depth = self._extract_technical_depth(query, lang_code)
        if technical_depth:
            filters["technical_depth"] = technical_depth

        # Extract topic/category filters - Task 4.2
        topics = self._extract_topics(query, lang_code)
        if topics:
            filters["topics"] = topics

        return filters

    def _extract_time_range(self, query: str, lang_code: str) -> Optional[Dict[str, datetime]]:
        """
        Extract time range from query.

        Args:
            query: Query text
            lang_code: Language code

        Returns:
            Dictionary with start and end datetime, or None
        """
        query_lower = query.lower()

        # First check advanced patterns (task 4.2) to avoid matching basic patterns
        advanced_range = self._extract_advanced_time_range(query, lang_code)
        if advanced_range:
            return advanced_range

        # Then check basic time patterns
        time_patterns = self.time_patterns.get(lang_code, {})

        for pattern, delta in time_patterns.items():
            if pattern in query_lower:
                end_time = datetime.utcnow()
                start_time = end_time - delta
                return {"start": start_time, "end": end_time}

        return None

    def _extract_technical_depth(self, query: str, lang_code: str) -> Optional[int]:
        """
        Extract technical depth indicator from query.

        Args:
            query: Query text
            lang_code: Language code

        Returns:
            Technical depth level (1-5) or None
        """
        query_lower = query.lower()

        # Technical depth keywords
        depth_keywords = {
            "zh": {
                5: ["深入", "高級", "專業", "進階", "詳細"],
                4: ["技術", "實現", "原理"],
                3: ["中級", "實用"],
                2: ["基礎", "入門", "簡單"],
                1: ["概述", "簡介", "了解"],
            },
            "en": {
                5: ["deep", "advanced", "professional", "detailed", "in-depth"],
                4: ["technical", "implementation", "architecture"],
                3: ["intermediate", "practical"],
                2: ["basic", "beginner", "simple", "introduction"],
                1: ["overview", "brief", "understand"],
            },
        }

        keywords = depth_keywords.get(lang_code, {})

        for depth, words in sorted(keywords.items(), reverse=True):
            if any(word in query_lower for word in words):
                return depth

        return None

    async def expand_query(self, query: str, context: ConversationContext) -> str:
        """
        Expand query using conversation context for follow-up questions.
        Enhanced for Task 8.2 with improved contextual understanding.

        Supports Requirements 4.2, 4.3:
        - Combines previous conversation content with new questions
        - Handles context-related queries like "tell me more about this"
        - Provides intelligent query expansion based on conversation history

        Args:
            query: Current query
            context: Conversation context

        Returns:
            Expanded query with context and synonyms

        Requirements: 1.4, 4.2, 4.3
        """
        # If no context or first turn, apply synonym expansion only
        if not context or len(context.turns) == 0:
            return await self._expand_with_synonyms(query)

        # Enhanced contextual query analysis
        expanded_query = await self._expand_with_context(query, context)

        # Apply synonym expansion to the expanded query
        expanded_query = await self._expand_with_synonyms(expanded_query)

        self.logger.info(f"Expanded query: '{query}' -> '{expanded_query}'")
        return expanded_query

    async def _expand_with_context(self, query: str, context: ConversationContext) -> str:
        """
        Enhanced contextual query expansion for Task 8.2.

        Handles various types of contextual queries:
        - Direct references ("this", "that", "it")
        - Follow-up questions ("tell me more", "what about")
        - Comparative queries ("are there other", "similar ones")
        - Clarification requests ("explain further", "more details")
        """
        query_lower = query.lower()

        # 1. Handle direct contextual references
        if self._has_direct_references(query_lower):
            return self._expand_direct_references(query, context)

        # 2. Handle follow-up question patterns
        if self._is_followup_pattern(query_lower):
            return self._expand_followup_query(query, context)

        # 3. Handle comparative/exploratory queries
        if self._is_comparative_query(query_lower):
            return self._expand_comparative_query(query, context)

        # 4. Handle clarification requests
        if self._is_clarification_request(query_lower):
            return self._expand_clarification_request(query, context)

        # 5. For other queries, check if they're contextually related
        if self._is_contextually_related(query, context):
            return self._expand_related_query(query, context)

        # If no contextual expansion needed, return original query
        return query

    def _has_direct_references(self, query_lower: str) -> bool:
        """Check if query has direct references to previous content."""
        direct_refs = {
            "zh": ["這個", "那個", "它", "他", "她", "這些", "那些", "它們"],
            "en": ["this", "that", "it", "they", "them", "these", "those"],
        }

        for refs in direct_refs.values():
            if any(ref in query_lower for ref in refs):
                return True
        return False

    def _expand_direct_references(self, query: str, context: ConversationContext) -> str:
        """Expand queries with direct references using conversation context."""
        if not context.turns:
            return query

        # Get the most recent response for context
        last_turn = context.turns[-1]
        if last_turn.response and last_turn.response.articles:
            # Use the first article's title as reference context
            article_context = last_turn.response.articles[0].title
            return f"{article_context}: {query}"
        elif context.current_topic:
            return f"{context.current_topic}: {query}"
        else:
            # Use the last query as context
            return f"{last_turn.query} {query}"

    def _is_followup_pattern(self, query_lower: str) -> bool:
        """Enhanced follow-up pattern detection."""
        followup_patterns = {
            "zh": [
                "告訴我更多",
                "更多資訊",
                "詳細說明",
                "進一步",
                "深入了解",
                "還有什麼",
                "其他的",
                "更多關於",
                "補充",
                "擴展",
                "更多細節",
            ],
            "en": [
                "tell me more",
                "more about",
                "more information",
                "elaborate",
                "further details",
                "more details",
                "what else",
                "additional",
                "expand on",
                "more on",
                "continue",
                "go deeper",
            ],
        }

        for patterns in followup_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True
        return False

    def _expand_followup_query(self, query: str, context: ConversationContext) -> str:
        """Expand follow-up queries with relevant context."""
        if not context.turns:
            return query

        # Combine with current topic and recent context
        if context.current_topic:
            base_context = context.current_topic
        else:
            # Use keywords from recent queries
            recent_queries = context.get_recent_queries(count=2)
            base_context = " ".join(recent_queries) if recent_queries else ""

        return f"{base_context} {query}" if base_context else query

    def _is_comparative_query(self, query_lower: str) -> bool:
        """Check if query is asking for comparisons or alternatives."""
        comparative_patterns = {
            "zh": [
                "有其他",
                "還有別的",
                "類似的",
                "相關的",
                "比較",
                "對比",
                "不同的",
                "替代的",
                "另外的選擇",
            ],
            "en": [
                "are there other",
                "other similar",
                "alternatives",
                "related ones",
                "compare",
                "comparison",
                "different",
                "alternative",
                "similar to",
            ],
        }

        for patterns in comparative_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True
        return False

    def _expand_comparative_query(self, query: str, context: ConversationContext) -> str:
        """Expand comparative queries with context for better search."""
        if context.current_topic:
            return f"alternatives to {context.current_topic}: {query}"
        elif context.turns:
            last_query = context.turns[-1].query
            return f"alternatives to {last_query}: {query}"
        return query

    def _is_clarification_request(self, query_lower: str) -> bool:
        """Check if query is requesting clarification or explanation."""
        # More specific clarification patterns that indicate contextual clarification
        clarification_patterns = {
            "zh": [
                "解釋這個",
                "說明這個",
                "澄清",
                "詳細說明",
                "具體解釋",
                "什麼意思",
                "能否解釋",
                "怎麼理解",
                "為什麼這樣",
            ],
            "en": [
                "explain this",
                "clarify this",
                "what does this mean",
                "how does this work",
                "can you explain",
                "elaborate on this",
                "break down this",
                "what do you mean",
            ],
        }

        # Check for contextual clarification patterns (not general "what is" questions)
        for patterns in clarification_patterns.values():
            if any(pattern in query_lower for pattern in patterns):
                return True

        # Additional check for contextual references with clarification intent
        contextual_clarification = [
            "explain that",
            "clarify that",
            "what does that mean",
            "how does that work",
        ]

        return any(pattern in query_lower for pattern in contextual_clarification)

    def _expand_clarification_request(self, query: str, context: ConversationContext) -> str:
        """Expand clarification requests with specific context."""
        if context.current_topic:
            return f"explain {context.current_topic}: {query}"
        elif context.turns:
            # Use the most recent article or topic mentioned
            last_turn = context.turns[-1]
            if last_turn.response and last_turn.response.articles:
                article_title = last_turn.response.articles[0].title
                return f"explain {article_title}: {query}"
        return query

    def _is_contextually_related(self, query: str, context: ConversationContext) -> bool:
        """Check if query is contextually related to ongoing conversation."""
        if not context.current_topic:
            return False

        # Enhanced contextual relatedness detection
        query_words = set(word.lower() for word in query.split() if len(word) > 2)
        topic_words = set(word.lower() for word in context.current_topic.split() if len(word) > 2)

        if not query_words or not topic_words:
            return False

        # Check for direct word overlap
        direct_overlap = len(query_words.intersection(topic_words)) / len(
            query_words.union(topic_words)
        )
        if direct_overlap > 0.1:  # Lower threshold for direct overlap
            return True

        # Check for semantic relatedness using domain knowledge
        ai_related_terms = {
            "artificial",
            "intelligence",
            "ai",
            "machine",
            "learning",
            "ml",
            "deep",
            "neural",
            "network",
            "algorithm",
            "model",
            "data",
            "science",
            "automation",
            "robot",
            "nlp",
            "computer",
            "vision",
            "processing",
            "natural",
            "language",
            "applications",
        }

        tech_related_terms = {
            "technology",
            "software",
            "programming",
            "development",
            "system",
            "application",
            "platform",
            "framework",
            "tool",
            "solution",
            "innovation",
            "digital",
        }

        # Check if both query and topic contain related terms
        query_ai_terms = query_words.intersection(ai_related_terms)
        topic_ai_terms = topic_words.intersection(ai_related_terms)

        if query_ai_terms and topic_ai_terms:
            return True

        query_tech_terms = query_words.intersection(tech_related_terms)
        topic_tech_terms = topic_words.intersection(tech_related_terms)

        if query_tech_terms and topic_tech_terms:
            return True

        return False

    def _expand_related_query(self, query: str, context: ConversationContext) -> str:
        """Expand contextually related queries."""
        if context.current_topic:
            return f"{context.current_topic} {query}"
        return query

    async def _expand_with_synonyms(self, query: str) -> str:
        """
        Expand query with synonyms for better search coverage.
        Task 4.2 enhancement.

        Args:
            query: Original query

        Returns:
            Query with key terms expanded with synonyms
        """
        # Detect language
        language = self._detect_language(query)
        lang_code = language.value

        # Get synonyms for this language
        synonym_dict = self.synonyms.get(lang_code, {})

        # Find and expand key terms
        query_lower = query.lower()
        expanded_terms = []

        for term, synonyms in synonym_dict.items():
            if term in query_lower:
                # Add original term and first synonym
                expanded_terms.append(f"({term} OR {synonyms[0]})")

        # If we found terms to expand, append them to the query
        if expanded_terms:
            expansion = " ".join(expanded_terms)
            return f"{query} {expansion}"

        return query

    async def generate_contextual_suggestions(
        self,
        query: str,
        context: Optional[ConversationContext] = None,
        user_profile: Optional["UserProfile"] = None,
    ) -> List[str]:
        """
        Generate context-aware query suggestions.
        Task 4.2 enhancement.

        Args:
            query: Current or partial query
            context: Optional conversation context
            user_profile: Optional user profile for personalization

        Returns:
            List of suggested queries
        """
        language = self._detect_language(query)
        suggestions = []

        # Start with basic template suggestions
        template_suggestions = self.generate_query_suggestions(query, language)
        suggestions.extend(template_suggestions)

        # Add context-based suggestions if available
        if context and context.current_topic:
            topic = context.current_topic
            if language == QueryLanguage.CHINESE:
                suggestions.extend(
                    [f"關於{topic}的更多細節", f"{topic}的實際應用", f"{topic}與{query}的關係"]
                )
            else:
                suggestions.extend(
                    [
                        f"More details about {topic}",
                        f"Practical applications of {topic}",
                        f"How {topic} relates to {query}",
                    ]
                )

        # Add user history-based suggestions if available
        if user_profile and user_profile.preferred_topics:
            top_topics = user_profile.get_top_topics(limit=2)
            for topic in top_topics:
                if language == QueryLanguage.CHINESE:
                    suggestions.append(f"{query}在{topic}領域的應用")
                else:
                    suggestions.append(f"{query} in {topic}")

        # Remove duplicates and limit
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion.lower())

        return unique_suggestions[:10]  # Limit to 10 suggestions

    def _is_followup_query(self, query: str) -> bool:
        """
        Determine if query is a follow-up question.

        Args:
            query: Query text

        Returns:
            True if query appears to be a follow-up
        """
        query_lower = query.lower()

        # Follow-up indicators
        followup_indicators = {
            "zh": ["這個", "那個", "它", "他", "她", "更多", "還有", "另外", "其他"],
            "en": ["this", "that", "it", "more", "also", "another", "other", "what about"],
        }

        # Check for indicators
        for indicators in followup_indicators.values():
            if any(indicator in query_lower for indicator in indicators):
                return True

        # Check if query is very short (likely a follow-up)
        if len(query.strip()) < 20:
            return True

        return False

    async def validate_query(self, query: str) -> QueryValidationResult:
        """
        Validate query and provide error messages or suggestions.

        Args:
            query: Query text to validate

        Returns:
            QueryValidationResult with validation status and details

        Requirements: 1.5
        """
        # Check if query is empty
        if not query or not query.strip():
            return QueryValidationResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_QUERY,
                error_message="Query cannot be empty",
                suggestions=["Please provide a question or search term"],
            )

        # Check query length
        if len(query) > PerformanceLimits.MAX_QUERY_LENGTH:
            return QueryValidationResult(
                is_valid=False,
                error_code=ErrorCodes.QUERY_TOO_LONG,
                error_message=f"Query exceeds maximum length of {PerformanceLimits.MAX_QUERY_LENGTH} characters",
                suggestions=[
                    "Please shorten your query",
                    "Try breaking it into multiple questions",
                ],
            )

        # Check if query has meaningful content
        if not re.search(r"[a-zA-Z\u4e00-\u9fff]", query):
            return QueryValidationResult(
                is_valid=False,
                error_code=ErrorCodes.INVALID_QUERY,
                error_message="Query must contain letters or characters",
                suggestions=["Please provide a meaningful question"],
            )

        # Parse query to check confidence
        parsed = await self.parse_query(query)

        # Check if query requires clarification
        if parsed.requires_clarification():
            language = parsed.language.value
            clarification_msgs = MessageTemplates.CLARIFICATION_REQUESTS.get(language, [])

            return QueryValidationResult(
                is_valid=True,  # Query is valid but needs clarification
                error_code=None,
                error_message=None,
                suggestions=clarification_msgs,
            )

        # Query is valid
        return QueryValidationResult(is_valid=True)

    def generate_query_suggestions(self, partial_query: str, language: QueryLanguage) -> List[str]:
        """
        Generate query suggestions for unclear or incomplete queries.

        Args:
            partial_query: Incomplete or unclear query
            language: Query language

        Returns:
            List of suggested complete queries

        Requirements: 1.3
        """
        lang_code = language.value

        # Common query templates
        templates = {
            "zh": [
                f"關於{partial_query}的最新文章",
                f"如何{partial_query}",
                f"{partial_query}的教程",
                f"{partial_query}的最佳實踐",
                f"推薦一些{partial_query}相關的文章",
            ],
            "en": [
                f"Latest articles about {partial_query}",
                f"How to {partial_query}",
                f"{partial_query} tutorial",
                f"{partial_query} best practices",
                f"Recommend articles about {partial_query}",
            ],
        }

        return templates.get(lang_code, templates["en"])[:5]

    def _extract_topics(self, query: str, lang_code: str) -> Optional[List[str]]:
        """
        Extract topic/category filters from query.
        Task 4.2 enhancement.

        Args:
            query: Query text
            lang_code: Language code

        Returns:
            List of detected topics or None
        """
        query_lower = query.lower()
        topic_keywords = self.topic_keywords.get(lang_code, {})

        detected_topics = []
        for topic, synonyms in topic_keywords.items():
            # Check if topic or any synonym is in query
            if topic.lower() in query_lower:
                detected_topics.append(topic)
            else:
                for synonym in synonyms:
                    if synonym.lower() in query_lower:
                        detected_topics.append(topic)
                        break

        return detected_topics if detected_topics else None

    def _extract_advanced_time_range(
        self, query: str, lang_code: str
    ) -> Optional[Dict[str, datetime]]:
        """
        Extract advanced time range patterns like "between X and Y" or "last N months".
        Task 4.2 enhancement.

        Args:
            query: Query text
            lang_code: Language code

        Returns:
            Dictionary with start and end datetime, or None
        """
        query_lower = query.lower()

        # Pattern: "last N months/weeks/days"
        import re

        if lang_code == "zh":
            # Pattern: 最近N個月/週/天
            patterns = [
                (r"最近(\d+)個月", lambda n: timedelta(days=int(n) * 30)),
                (r"最近(\d+)週", lambda n: timedelta(weeks=int(n))),
                (r"最近(\d+)天", lambda n: timedelta(days=int(n))),
                (r"過去(\d+)個月", lambda n: timedelta(days=int(n) * 30)),
                (r"過去(\d+)年", lambda n: timedelta(days=int(n) * 365)),
            ]
        else:
            # Pattern: last N months/weeks/days
            patterns = [
                (r"last (\d+) months?", lambda n: timedelta(days=int(n) * 30)),
                (r"last (\d+) weeks?", lambda n: timedelta(weeks=int(n))),
                (r"last (\d+) days?", lambda n: timedelta(days=int(n))),
                (r"past (\d+) months?", lambda n: timedelta(days=int(n) * 30)),
                (r"past (\d+) years?", lambda n: timedelta(days=int(n) * 365)),
            ]

        for pattern, delta_func in patterns:
            match = re.search(pattern, query_lower)
            if match:
                n = match.group(1)
                delta = delta_func(n)
                end_time = datetime.utcnow()
                start_time = end_time - delta
                return {"start": start_time, "end": end_time}

        # Pattern: "between X and Y" (simplified - would need date parsing library for full support)
        if lang_code == "zh":
            between_pattern = r"(從|在).*?(到|至)"
        else:
            between_pattern = r"between .* and"

        if re.search(between_pattern, query_lower):
            # For now, return a default range
            # In production, this would use a date parsing library like dateutil
            self.logger.info("Detected 'between' time pattern but detailed parsing not implemented")
            # Return last 3 months as default
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=90)
            return {"start": start_time, "end": end_time}

        return None
