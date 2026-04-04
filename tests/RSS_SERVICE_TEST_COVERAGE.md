# RSS Service Test Coverage Summary

## Task 2.5: 撰寫 RSS Service 的單元測試

This document summarizes the complete test coverage for the RSS Service, demonstrating that all requirements specified in task 2.5 are fully covered.

## Test Files

1. **tests/test_rss_service.py** - Core RSS service functionality tests
2. **tests/test_rss_service_fetch_new_articles.py** - Deduplication and fetch_new_articles tests
3. **tests/test_rss_service_additional.py** - Additional tests for complete coverage

## Requirements Coverage

### Task 2.5 Requirements

| Requirement                            | Test(s)                                                                                                                                                                | Status |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 測試 fetch_new_articles 過濾已存在文章 | `test_returns_only_new_articles`                                                                                                                                       | ✅     |
| 測試時效性過濾（舊文章被排除）         | `test_filters_old_articles_and_logs_count`, `test_default_time_window_filters_correctly`                                                                               | ✅     |
| 測試 published_at 缺失時使用當前時間   | `test_uses_current_time_when_published_at_missing`, `test_missing_all_date_fields`, `test_malformed_date_string`, `test_article_with_missing_published_at_is_included` | ✅     |
| 測試個別 feed 失敗不影響其他 feed      | `test_continues_when_one_feed_raises`, `test_fetch_all_feeds_failure_propagates`                                                                                       | ✅     |
| 測試可配置的時間窗口                   | `test_respects_configurable_time_window`, `test_custom_time_window_1_day`, `test_custom_time_window_30_days`                                                           | ✅     |
| 測試預設 7 天時間窗口                  | `test_default_days_to_fetch_is_7`, `test_default_time_window_filters_correctly`                                                                                        | ✅     |

### Specification Requirements

| Requirement | Description                                                      | Test(s)                                                                                                                                      | Status |
| ----------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 2.7         | URL checking fails for specific article, continue with remaining | `test_continues_on_check_failure`, `test_logs_error_on_check_failure`                                                                        | ✅     |
| 11.1        | Only fetch articles within time window                           | `test_filters_old_articles_and_logs_count`, `test_default_time_window_filters_correctly`                                                     | ✅     |
| 11.2        | Parse published_at timestamp from RSS entries                    | `test_returns_utc_datetime_from_published_parsed`, `test_falls_back_to_updated_parsed`                                                       | ✅     |
| 11.3        | Use current timestamp when published_at not available            | `test_returns_now_when_no_date_fields`, `test_returns_now_on_malformed_struct`, `test_missing_all_date_fields`, `test_malformed_date_string` | ✅     |
| 11.4        | Filter out articles older than time window                       | `test_filters_old_articles_and_logs_count`, `test_returns_articles_within_cutoff`                                                            | ✅     |
| 11.5        | Time window configurable via parameter                           | `test_respects_configurable_time_window`, `test_custom_time_window_1_day`, `test_custom_time_window_30_days`                                 | ✅     |
| 11.6        | Default to 7 days when not configured                            | `test_default_days_to_fetch_is_7`, `test_default_time_window_filters_correctly`                                                              | ✅     |
| 11.7        | Log count of articles filtered by time window                    | `test_filters_old_articles_and_logs_count`                                                                                                   | ✅     |

## Test Details

### tests/test_rss_service.py (14 tests)

#### TestParseDate (4 tests)

- `test_returns_utc_datetime_from_published_parsed` - Validates parsing from published_parsed
- `test_falls_back_to_updated_parsed` - Validates fallback to updated_parsed
- `test_returns_now_when_no_date_fields` - Validates current time when no dates
- `test_returns_now_on_malformed_struct` - Validates current time on malformed data

#### TestProcessSingleFeed (7 tests)

- `test_returns_articles_within_cutoff` - Validates time filtering
- `test_returns_empty_list_on_fetch_error` - Validates error handling
- `test_article_has_correct_source_metadata` - Validates metadata population
- `test_content_preview_truncated_to_800_chars` - Validates schema compatibility
- `test_filters_old_articles_and_logs_count` - Validates filtering and logging (Req 11.1, 11.4, 11.7)
- `test_respects_configurable_time_window` - Validates configurable window (Req 11.5, 11.6)
- `test_uses_current_time_when_published_at_missing` - Validates fallback time (Req 11.2, 11.3)

#### TestFetchAllFeeds (3 tests)

- `test_aggregates_articles_from_all_sources` - Validates aggregation
- `test_returns_empty_list_for_no_sources` - Validates empty input
- `test_continues_when_one_feed_raises` - Validates resilience (Req 2.7, 7.2)

### tests/test_rss_service_fetch_new_articles.py (5 tests)

#### TestFetchNewArticles (5 tests)

- `test_returns_only_new_articles` - Validates deduplication (Req 2.3, 2.4, 2.5)
- `test_returns_empty_list_when_no_articles_fetched` - Validates empty result handling
- `test_returns_all_articles_when_none_exist` - Validates all-new scenario
- `test_continues_on_check_failure` - Validates error resilience (Req 2.7)
- `test_logs_statistics` - Validates logging (Req 2.6)

### tests/test_rss_service_additional.py (9 tests)

#### TestRSSServiceDefaults (2 tests)

- `test_default_days_to_fetch_is_7` - Validates default value (Req 11.6)
- `test_default_time_window_filters_correctly` - Validates default filtering (Req 11.1, 11.6)

#### TestFetchNewArticlesErrorHandling (2 tests)

- `test_fetch_all_feeds_failure_propagates` - Validates error propagation (Req 2.7, 7.2)
- `test_logs_error_on_check_failure` - Validates error logging (Req 2.7)

#### TestTimeWindowConfiguration (2 tests)

- `test_custom_time_window_1_day` - Validates 1-day window (Req 11.5)
- `test_custom_time_window_30_days` - Validates 30-day window (Req 11.5)

#### TestPublishedAtHandling (3 tests)

- `test_missing_all_date_fields` - Validates missing date handling (Req 11.2, 11.3)
- `test_malformed_date_string` - Validates malformed date handling (Req 11.2, 11.3)
- `test_article_with_missing_published_at_is_included` - Validates inclusion with missing date (Req 11.2, 11.3)

## Test Execution Results

```bash
$ python3 -m pytest tests/test_rss_service.py tests/test_rss_service_fetch_new_articles.py tests/test_rss_service_additional.py -v

================================ test session starts ================================
collected 28 items

tests/test_rss_service.py::TestParseDate::test_returns_utc_datetime_from_published_parsed PASSED
tests/test_rss_service.py::TestParseDate::test_falls_back_to_updated_parsed PASSED
tests/test_rss_service.py::TestParseDate::test_returns_now_when_no_date_fields PASSED
tests/test_rss_service.py::TestParseDate::test_returns_now_on_malformed_struct PASSED
tests/test_rss_service.py::TestProcessSingleFeed::test_returns_articles_within_cutoff PASSED
tests/test_rss_service.py::TestProcessSingleFeed::test_returns_empty_list_on_fetch_error PASSED
tests/test_rss_service.py::TestProcessSingleFeed::test_article_has_correct_source_metadata PASSED
tests/test_rss_service.py::TestProcessSingleFeed::test_content_preview_truncated_to_800_chars PASSED
tests/test_rss_service.py::TestProcessSingleFeed::test_filters_old_articles_and_logs_count PASSED
tests/test_rss_service.py::TestProcessSingleFeed::test_respects_configurable_time_window PASSED
tests/test_rss_service.py::TestProcessSingleFeed::test_uses_current_time_when_published_at_missing PASSED
tests/test_rss_service.py::TestFetchAllFeeds::test_aggregates_articles_from_all_sources PASSED
tests/test_rss_service.py::TestFetchAllFeeds::test_returns_empty_list_for_no_sources PASSED
tests/test_rss_service.py::TestFetchAllFeeds::test_continues_when_one_feed_raises PASSED
tests/test_rss_service_fetch_new_articles.py::TestFetchNewArticles::test_returns_only_new_articles PASSED
tests/test_rss_service_fetch_new_articles.py::TestFetchNewArticles::test_returns_empty_list_when_no_articles_fetched PASSED
tests/test_rss_service_fetch_new_articles.py::TestFetchNewArticles::test_returns_all_articles_when_none_exist PASSED
tests/test_rss_service_fetch_new_articles.py::TestFetchNewArticles::test_continues_on_check_failure PASSED
tests/test_rss_service_fetch_new_articles.py::TestFetchNewArticles::test_logs_statistics PASSED
tests/test_rss_service_additional.py::TestRSSServiceDefaults::test_default_days_to_fetch_is_7 PASSED
tests/test_rss_service_additional.py::TestRSSServiceDefaults::test_default_time_window_filters_correctly PASSED
tests/test_rss_service_additional.py::TestFetchNewArticlesErrorHandling::test_fetch_all_feeds_failure_propagates PASSED
tests/test_rss_service_additional.py::TestFetchNewArticlesErrorHandling::test_logs_error_on_check_failure PASSED
tests/test_rss_service_additional.py::TestTimeWindowConfiguration::test_custom_time_window_1_day PASSED
tests/test_rss_service_additional.py::TestTimeWindowConfiguration::test_custom_time_window_30_days PASSED
tests/test_rss_service_additional.py::TestPublishedAtHandling::test_missing_all_date_fields PASSED
tests/test_rss_service_additional.py::TestPublishedAtHandling::test_malformed_date_string PASSED
tests/test_rss_service_additional.py::TestPublishedAtHandling::test_article_with_missing_published_at_is_included PASSED

================================ 28 passed in 0.05s =================================
```

## Summary

✅ **All 28 tests pass successfully**

✅ **Complete coverage of task 2.5 requirements:**

- fetch_new_articles filtering
- Time-based filtering
- published_at fallback handling
- Individual feed failure resilience
- Configurable time window
- Default 7-day window

✅ **Complete coverage of specification requirements:**

- Requirement 2.7 (error handling)
- Requirements 11.1-11.7 (time filtering and configuration)

The RSS Service unit tests provide comprehensive coverage of all specified functionality, edge cases, and error conditions.
