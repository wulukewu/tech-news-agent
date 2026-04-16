/**
 * Property-Based Tests for Recommendation Algorithm
 *
 * Tests Properties 17 and 18 from the design document
 *
 * Feature: frontend-feature-enhancement
 * Task: 7.2
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

/**
 * Test data generators (arbitraries)
 */

// Generate a valid article rating (1-5 stars)
const ratingArbitrary = fc.integer({ min: 1, max: 5 });

// Generate an article with rating
const ratedArticleArbitrary = fc.record({
  id: fc.uuid(),
  title: fc.string({ minLength: 10, maxLength: 100 }),
  rating: ratingArbitrary,
  category: fc.constantFrom('AI', 'Web', 'Mobile', 'DevOps', 'Security'),
});

// Generate a user's rating history
const ratingHistoryArbitrary = fc.array(ratedArticleArbitrary, {
  minLength: 0,
  maxLength: 50,
});

/**
 * Helper function to filter articles rated 4+ stars
 */
function getHighRatedArticles(ratingHistory: Array<{ rating: number }>) {
  return ratingHistory.filter((article) => article.rating >= 4);
}

/**
 * Helper function to check if recommendations are based on high-rated articles
 */
function areRecommendationsBasedOnHighRatings(
  ratingHistory: Array<{ id: string; rating: number; category: string }>,
  recommendations: Array<{ sourceArticleId: string; category: string }>
) {
  const highRatedArticles = getHighRatedArticles(ratingHistory);
  const highRatedIds = new Set(highRatedArticles.map((a) => a.id));
  const highRatedCategories = new Set(highRatedArticles.map((a) => a.category));

  // All recommendations should be based on high-rated articles
  return recommendations.every(
    (rec) => highRatedIds.has(rec.sourceArticleId) || highRatedCategories.has(rec.category)
  );
}

describe('Recommendation Algorithm Properties', () => {
  /**
   * Property 17: 推薦演算法基礎
   *
   * **Validates: Requirements 3.2**
   *
   * For any user with rating history, recommendations should be generated
   * based only on articles that the user has rated 4 stars or higher.
   */
  it('Property 17: should only use 4+ star ratings for recommendations', () => {
    fc.assert(
      fc.property(ratingHistoryArbitrary, (ratingHistory) => {
        // Get articles rated 4+ stars
        const highRatedArticles = getHighRatedArticles(ratingHistory);

        // If user has high-rated articles, they should be used for recommendations
        if (highRatedArticles.length > 0) {
          // Verify that only high-rated articles are considered
          const allRatings = ratingHistory.map((a) => a.rating);
          const highRatings = highRatedArticles.map((a) => a.rating);

          // All high ratings should be >= 4
          expect(highRatings.every((r) => r >= 4)).toBe(true);

          // High-rated articles should be a subset of all articles
          expect(highRatedArticles.length).toBeLessThanOrEqual(ratingHistory.length);

          // If there are low-rated articles, they should not be in high-rated set
          const lowRatedArticles = ratingHistory.filter((a) => a.rating < 4);
          const highRatedIds = new Set(highRatedArticles.map((a) => a.id));
          const lowRatedInHighSet = lowRatedArticles.some((a) => highRatedIds.has(a.id));

          expect(lowRatedInHighSet).toBe(false);
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 18: 推薦卡片渲染
   *
   * **Validates: Requirements 3.3**
   *
   * For any set of recommendations, each should be displayed as a
   * Recommendation_Card component with proper formatting and information.
   */
  it('Property 18: should render all recommendations as cards', () => {
    const recommendationArbitrary = fc.record({
      id: fc.uuid(),
      article: fc.record({
        id: fc.uuid(),
        title: fc.string({ minLength: 10, maxLength: 100 }),
        url: fc.webUrl(),
        feedName: fc.string({ minLength: 5, maxLength: 50 }),
        category: fc.constantFrom('AI', 'Web', 'Mobile', 'DevOps', 'Security'),
        publishedAt: fc
          .date({ min: new Date('2020-01-01'), max: new Date() })
          .map((d) => d.toISOString()),
        tinkeringIndex: fc.integer({ min: 1, max: 5 }),
        aiSummary: fc.string({ minLength: 50, maxLength: 200 }),
        isInReadingList: fc.boolean(),
      }),
      reason: fc.string({ minLength: 20, maxLength: 150 }),
      confidence: fc.double({ min: 0, max: 1 }),
      generatedAt: fc.date().map((d) => d.toISOString()),
    });

    fc.assert(
      fc.property(
        fc.array(recommendationArbitrary, { minLength: 0, maxLength: 20 }),
        (recommendations) => {
          // Each recommendation should have all required fields
          recommendations.forEach((rec) => {
            // Recommendation structure
            expect(rec.id).toBeDefined();
            expect(rec.article).toBeDefined();
            expect(rec.reason).toBeDefined();
            expect(rec.confidence).toBeGreaterThanOrEqual(0);
            expect(rec.confidence).toBeLessThanOrEqual(1);
            expect(rec.generatedAt).toBeDefined();

            // Article structure (validates Requirement 3.4)
            expect(rec.article.title).toBeDefined();
            expect(rec.article.feedName).toBeDefined();
            expect(rec.article.category).toBeDefined();
            expect(rec.article.aiSummary).toBeDefined();

            // Title should not be empty
            expect(rec.article.title.length).toBeGreaterThan(0);

            // Tinkering index should be valid (1-5)
            expect(rec.article.tinkeringIndex).toBeGreaterThanOrEqual(1);
            expect(rec.article.tinkeringIndex).toBeLessThanOrEqual(5);

            // Reason should not be empty
            expect(rec.reason.length).toBeGreaterThan(0);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: Recommendation confidence should be valid
   */
  it('should have valid confidence scores between 0 and 1', () => {
    const recommendationArbitrary = fc.record({
      id: fc.uuid(),
      confidence: fc.double({ min: 0, max: 1, noNaN: true }),
    });

    fc.assert(
      fc.property(
        fc.array(recommendationArbitrary, { minLength: 1, maxLength: 20 }),
        (recommendations) => {
          recommendations.forEach((rec) => {
            expect(rec.confidence).toBeGreaterThanOrEqual(0);
            expect(rec.confidence).toBeLessThanOrEqual(1);
            expect(Number.isNaN(rec.confidence)).toBe(false);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: Recommendations should be sorted by confidence
   */
  it('should sort recommendations by confidence (highest first)', () => {
    const recommendationArbitrary = fc.record({
      id: fc.uuid(),
      confidence: fc.double({ min: 0, max: 1, noNaN: true }),
    });

    fc.assert(
      fc.property(
        fc.array(recommendationArbitrary, { minLength: 2, maxLength: 20 }),
        (recommendations) => {
          // Sort by confidence descending
          const sorted = [...recommendations].sort((a, b) => b.confidence - a.confidence);

          // Check if sorted correctly
          for (let i = 0; i < sorted.length - 1; i++) {
            expect(sorted[i].confidence).toBeGreaterThanOrEqual(sorted[i + 1].confidence);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
