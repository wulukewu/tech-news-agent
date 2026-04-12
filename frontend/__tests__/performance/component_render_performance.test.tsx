/**
 * Component render performance tests.
 * Measures render times for critical components and generates baseline metrics.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import fs from 'fs';
import path from 'path';

// Mock components for testing (replace with actual imports)
const MockArticleCard = ({ article }: { article: any }) => (
  <div data-testid="article-card">
    <h3>{article.title}</h3>
    <p>{article.summary}</p>
  </div>
);

const MockFeedList = ({ feeds }: { feeds: any[] }) => (
  <div data-testid="feed-list">
    {feeds.map((feed, index) => (
      <div key={index} data-testid="feed-item">
        <h4>{feed.title}</h4>
        <p>{feed.description}</p>
      </div>
    ))}
  </div>
);

const MockDashboard = ({ articles, feeds }: { articles: any[]; feeds: any[] }) => (
  <div data-testid="dashboard">
    <h1>Dashboard</h1>
    <MockFeedList feeds={feeds} />
    <div data-testid="articles-section">
      {articles.map((article, index) => (
        <MockArticleCard key={index} article={article} />
      ))}
    </div>
  </div>
);

interface PerformanceMetrics {
  componentName: string;
  renderTime: number;
  reRenderTime?: number;
  propsSize: number;
  timestamp: string;
}

interface PerformanceBaseline {
  timestamp: string;
  components: PerformanceMetrics[];
  summary: {
    averageRenderTime: number;
    slowestComponent: string;
    fastestComponent: string;
    totalComponentsTested: number;
  };
}

class ComponentPerformanceMeasurer {
  private queryClient: QueryClient;
  private baselines: PerformanceMetrics[] = [];

  constructor() {
    this.queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  }

  /**
   * Wrapper component with providers
   */
  private TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={this.queryClient}>
      <ThemeProvider attribute="class" defaultTheme="light">
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );

  /**
   * Measure render performance of a component
   */
  async measureComponentRender<T extends Record<string, any>>(
    componentName: string,
    Component: React.ComponentType<T>,
    props: T,
    iterations: number = 10
  ): Promise<PerformanceMetrics> {
    const renderTimes: number[] = [];
    const propsSize = JSON.stringify(props).length;

    // Warm up
    render(
      <this.TestWrapper>
        <Component {...props} />
      </this.TestWrapper>
    );

    // Measure multiple renders
    for (let i = 0; i < iterations; i++) {
      const startTime = performance.now();

      const { unmount } = render(
        <this.TestWrapper>
          <Component {...props} />
        </this.TestWrapper>
      );

      const endTime = performance.now();
      renderTimes.push(endTime - startTime);

      unmount();
    }

    const averageRenderTime = renderTimes.reduce((sum, time) => sum + time, 0) / renderTimes.length;

    const metrics: PerformanceMetrics = {
      componentName,
      renderTime: averageRenderTime,
      propsSize,
      timestamp: new Date().toISOString(),
    };

    this.baselines.push(metrics);
    return metrics;
  }

  /**
   * Measure re-render performance
   */
  async measureComponentReRender<T extends Record<string, any>>(
    componentName: string,
    Component: React.ComponentType<T>,
    initialProps: T,
    updatedProps: T,
    iterations: number = 10
  ): Promise<number> {
    const reRenderTimes: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const { rerender } = render(
        <this.TestWrapper>
          <Component {...initialProps} />
        </this.TestWrapper>
      );

      const startTime = performance.now();

      rerender(
        <this.TestWrapper>
          <Component {...updatedProps} />
        </this.TestWrapper>
      );

      const endTime = performance.now();
      reRenderTimes.push(endTime - startTime);
    }

    const averageReRenderTime =
      reRenderTimes.reduce((sum, time) => sum + time, 0) / reRenderTimes.length;

    // Update the existing metrics
    const existingMetrics = this.baselines.find((m) => m.componentName === componentName);
    if (existingMetrics) {
      existingMetrics.reRenderTime = averageReRenderTime;
    }

    return averageReRenderTime;
  }

  /**
   * Generate test data
   */
  private generateTestData() {
    const articles = Array.from({ length: 20 }, (_, i) => ({
      id: i + 1,
      title: `Test Article ${i + 1}`,
      summary: `This is a test summary for article ${
        i + 1
      }. It contains some sample text to simulate real content.`,
      url: `https://example.com/article-${i + 1}`,
      publishedAt: new Date().toISOString(),
      source: `Source ${(i % 5) + 1}`,
    }));

    const feeds = Array.from({ length: 10 }, (_, i) => ({
      id: i + 1,
      title: `Test Feed ${i + 1}`,
      description: `This is a test description for feed ${i + 1}`,
      url: `https://example.com/feed-${i + 1}`,
      category: `Category ${(i % 3) + 1}`,
    }));

    return { articles, feeds };
  }

  /**
   * Run all performance measurements
   */
  async measureAllComponents(): Promise<PerformanceBaseline> {
    console.log('Starting component render performance measurement...');

    const testData = this.generateTestData();
    const { articles, feeds } = testData;

    // Measure individual components
    await this.measureComponentRender('ArticleCard', MockArticleCard, { article: articles[0] });
    await this.measureComponentRender('FeedList', MockFeedList, { feeds: feeds.slice(0, 5) });
    await this.measureComponentRender('Dashboard', MockDashboard, {
      articles: articles.slice(0, 10),
      feeds: feeds.slice(0, 5),
    });

    // Measure re-renders
    await this.measureComponentReRender(
      'ArticleCard',
      MockArticleCard,
      { article: articles[0] },
      { article: articles[1] }
    );

    await this.measureComponentReRender(
      'FeedList',
      MockFeedList,
      { feeds: feeds.slice(0, 5) },
      { feeds: feeds.slice(1, 6) }
    );

    // Calculate summary
    const renderTimes = this.baselines.map((m) => m.renderTime);
    const averageRenderTime = renderTimes.reduce((sum, time) => sum + time, 0) / renderTimes.length;
    const slowestComponent = this.baselines.reduce((prev, current) =>
      prev.renderTime > current.renderTime ? prev : current
    ).componentName;
    const fastestComponent = this.baselines.reduce((prev, current) =>
      prev.renderTime < current.renderTime ? prev : current
    ).componentName;

    const baseline: PerformanceBaseline = {
      timestamp: new Date().toISOString(),
      components: this.baselines,
      summary: {
        averageRenderTime,
        slowestComponent,
        fastestComponent,
        totalComponentsTested: this.baselines.length,
      },
    };

    return baseline;
  }

  /**
   * Save baseline to file
   */
  saveBaseline(baseline: PerformanceBaseline): string {
    const outputDir = path.join(__dirname, '../../scripts/performance/baselines');

    // Ensure directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(outputDir, `component_baseline_${timestamp}.json`);

    fs.writeFileSync(outputFile, JSON.stringify(baseline, null, 2));

    return outputFile;
  }
}

describe('Component Render Performance', () => {
  let measurer: ComponentPerformanceMeasurer;

  beforeEach(() => {
    measurer = new ComponentPerformanceMeasurer();
  });

  it('should measure ArticleCard render performance', async () => {
    const article = {
      id: 1,
      title: 'Test Article',
      summary: 'Test summary',
      url: 'https://example.com',
      publishedAt: new Date().toISOString(),
      source: 'Test Source',
    };

    const metrics = await measurer.measureComponentRender('ArticleCard', MockArticleCard, {
      article,
    });

    expect(metrics.componentName).toBe('ArticleCard');
    expect(metrics.renderTime).toBeGreaterThan(0);
    expect(metrics.propsSize).toBeGreaterThan(0);
  });

  it('should measure FeedList render performance', async () => {
    const feeds = Array.from({ length: 5 }, (_, i) => ({
      id: i + 1,
      title: `Feed ${i + 1}`,
      description: `Description ${i + 1}`,
      url: `https://example.com/feed-${i + 1}`,
    }));

    const metrics = await measurer.measureComponentRender('FeedList', MockFeedList, { feeds });

    expect(metrics.componentName).toBe('FeedList');
    expect(metrics.renderTime).toBeGreaterThan(0);
  });

  it('should generate complete performance baseline', async () => {
    const baseline = await measurer.measureAllComponents();

    expect(baseline.components).toHaveLength(3);
    expect(baseline.summary.totalComponentsTested).toBe(3);
    expect(baseline.summary.averageRenderTime).toBeGreaterThan(0);
    expect(baseline.summary.slowestComponent).toBeTruthy();
    expect(baseline.summary.fastestComponent).toBeTruthy();

    // Save baseline for reference
    const outputFile = measurer.saveBaseline(baseline);
    console.log(`Component performance baseline saved to: ${outputFile}`);

    // Print summary
    console.log('\n=== Component Render Performance Baseline Summary ===');
    console.log(`Timestamp: ${baseline.timestamp}`);
    console.log(`Components tested: ${baseline.summary.totalComponentsTested}`);
    console.log(`Average render time: ${baseline.summary.averageRenderTime.toFixed(2)}ms`);
    console.log(`Slowest component: ${baseline.summary.slowestComponent}`);
    console.log(`Fastest component: ${baseline.summary.fastestComponent}`);

    console.log('\n=== Individual Component Results ===');
    baseline.components.forEach((component) => {
      console.log(`${component.componentName}:`);
      console.log(`  Render time: ${component.renderTime.toFixed(2)}ms`);
      if (component.reRenderTime) {
        console.log(`  Re-render time: ${component.reRenderTime.toFixed(2)}ms`);
      }
      console.log(`  Props size: ${component.propsSize} bytes`);
    });
  });
});
