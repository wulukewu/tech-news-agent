'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/lib/toast';
import {
  generateWeeklyInsights,
  getLatestInsights,
  getInsightsHistory,
  type InsightReport,
  type InsightHistoryItem,
  type TrendItem,
  type ClusterItem,
} from '@/lib/api/weekly-insights';

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function TrendIcon({ direction }: { direction: TrendItem['direction'] }) {
  if (direction === 'rising')
    return <TrendingUp className="h-4 w-4 text-green-500" aria-label="Rising" />;
  if (direction === 'declining')
    return <TrendingDown className="h-4 w-4 text-red-500" aria-label="Declining" />;
  return <Minus className="h-4 w-4 text-muted-foreground" aria-label="Stable" />;
}

// Simple inline bar chart using Tailwind
function TrendBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
      <div
        className="h-full rounded-full bg-primary transition-all duration-500"
        style={{ width: `${pct}%` }}
        aria-valuenow={value}
        aria-valuemax={max}
        role="progressbar"
      />
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function ExecutiveSummaryCard({ report }: { report: InsightReport }) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-2">Executive Summary</h2>
      <p className="text-sm text-muted-foreground leading-relaxed">{report.executive_summary}</p>
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
        <span>
          <strong className="text-foreground">{report.article_count}</strong> articles analysed
        </span>
        <span>
          Period: {formatDate(report.period_start)} – {formatDate(report.period_end)}
        </span>
        <span>Generated: {formatDate(report.created_at)}</span>
      </div>
    </div>
  );
}

function TrendsSection({ trends }: { trends: TrendItem[] }) {
  const maxCount = Math.max(...trends.map((t) => t.current_count), 1);
  const rising = trends.filter((t) => t.direction === 'rising');
  const others = trends.filter((t) => t.direction !== 'rising');

  return (
    <section aria-labelledby="trends-heading">
      <h2 id="trends-heading" className="text-lg font-semibold mb-3">
        Technology Trends
      </h2>
      <div className="space-y-2">
        {[...rising, ...others].slice(0, 15).map((trend) => (
          <div
            key={trend.name}
            className="rounded-lg border bg-card px-4 py-3 flex items-center gap-3"
          >
            <TrendIcon direction={trend.direction} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium truncate">{trend.name}</span>
                <span className="text-xs text-muted-foreground ml-2 flex-shrink-0">
                  {trend.current_count} mentions
                </span>
              </div>
              <TrendBar value={trend.current_count} max={maxCount} />
            </div>
            <span className="text-xs text-muted-foreground flex-shrink-0 w-16 text-right capitalize">
              {trend.domain.replace('_', '/')}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ClusterCard({ cluster }: { cluster: ClusterItem }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-muted/40 transition-colors cursor-pointer"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3">
          <span className="font-semibold">{cluster.name}</span>
          <span className="text-xs bg-primary/10 text-primary rounded-full px-2 py-0.5">
            {cluster.article_count} articles
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="px-5 pb-4 space-y-3">
          {cluster.top_keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {cluster.top_keywords.map((kw) => (
                <span
                  key={kw}
                  className="text-xs bg-muted rounded-full px-2 py-0.5 text-muted-foreground"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
          <ul className="space-y-1.5">
            {cluster.top_articles.map((a) => (
              <li key={a.id}>
                <a
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-sm text-primary hover:underline cursor-pointer"
                >
                  <ExternalLink className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
                  <span className="truncate">{a.title}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function HistoryList({
  items,
  onSelect,
}: {
  items: InsightHistoryItem[];
  onSelect: (id: string) => void;
}) {
  return (
    <section aria-labelledby="history-heading">
      <h2 id="history-heading" className="text-lg font-semibold mb-3">
        Report History
      </h2>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <button
              onClick={() => onSelect(item.id)}
              className="w-full text-left rounded-lg border bg-card px-4 py-3 hover:bg-muted/40 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {formatDate(item.period_start)} – {formatDate(item.period_end)}
                </span>
                <span className="text-xs text-muted-foreground">{item.article_count} articles</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {item.executive_summary}
              </p>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function InsightsPage() {
  const [report, setReport] = useState<InsightReport | null>(null);
  const [history, setHistory] = useState<InsightHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadLatest = useCallback(async () => {
    setLoading(true);
    try {
      const [latest, hist] = await Promise.all([getLatestInsights(), getInsightsHistory(1, 5)]);
      setReport(latest);
      setHistory(hist.reports);
    } catch {
      toast.error('Failed to load insights.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLatest();
  }, [loadLatest]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const newReport = await generateWeeklyInsights();
      setReport(newReport);
      toast.success('Weekly insights generated!');
      // Refresh history
      const hist = await getInsightsHistory(1, 5);
      setHistory(hist.reports);
    } catch {
      toast.error('Failed to generate insights. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSelectHistory = async (id: string) => {
    try {
      const { getInsightsById } = await import('@/lib/api/weekly-insights');
      const r = await getInsightsById(id);
      setReport(r);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch {
      toast.error('Failed to load report.');
    }
  };

  return (
    <main id="main-content" className="container mx-auto px-4 py-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Weekly Insights</h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI-powered analysis of this week&apos;s tech articles
          </p>
        </div>
        <Button
          onClick={handleGenerate}
          disabled={generating}
          className="cursor-pointer"
          aria-label="Generate new weekly insights report"
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 ${generating ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
          {generating ? 'Generating…' : 'Generate Report'}
        </Button>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : report ? (
        <div className="space-y-6">
          <ExecutiveSummaryCard report={report} />

          {report.trends.length > 0 && <TrendsSection trends={report.trends} />}

          {report.clusters.length > 0 && (
            <section aria-labelledby="clusters-heading">
              <h2 id="clusters-heading" className="text-lg font-semibold mb-3">
                Theme Clusters
              </h2>
              <div className="space-y-2">
                {report.clusters.map((cluster) => (
                  <ClusterCard key={cluster.name} cluster={cluster} />
                ))}
              </div>
            </section>
          )}

          {report.missed_articles.length > 0 && (
            <section aria-labelledby="missed-heading">
              <h2 id="missed-heading" className="text-lg font-semibold mb-3">
                You Might Have Missed
              </h2>
              <ul className="space-y-2">
                {report.missed_articles.map((a) => (
                  <li key={a.id} className="rounded-lg border bg-card px-4 py-3">
                    <a
                      href={a.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-primary hover:underline cursor-pointer"
                    >
                      <ExternalLink className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                      <span>{a.title}</span>
                    </a>
                    <span className="text-xs text-muted-foreground mt-1 block">
                      Tinkering index: {a.tinkering_index}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {history.length > 0 && <HistoryList items={history} onSelect={handleSelectHistory} />}
        </div>
      ) : (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg mb-4">No insights report yet.</p>
          <Button onClick={handleGenerate} disabled={generating} className="cursor-pointer">
            <RefreshCw
              className={`h-4 w-4 mr-2 ${generating ? 'animate-spin' : ''}`}
              aria-hidden="true"
            />
            {generating ? 'Generating…' : 'Generate First Report'}
          </Button>
        </div>
      )}
    </main>
  );
}
