'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Brain,
  RefreshCw,
  ToggleLeft,
  ToggleRight,
  Send,
  ChevronDown,
  ChevronUp,
  Save,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/lib/toast';
import {
  getPendingConversations,
  respondToConversation,
  getPreferences,
  getLearningSettings,
  updateLearningSettings,
  triggerLearning,
  getPreferenceSummary,
  updatePreferenceSummary,
  type LearningConversation,
  type PreferenceModel,
  type LearningSettings,
} from '@/lib/api/proactive-learning';
import { useI18n } from '@/contexts/I18nContext';

// ── Helpers ──────────────────────────────────────────────────────────────────

function WeightBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.7 ? 'bg-green-500' : value >= 0.4 ? 'bg-primary' : 'bg-muted-foreground';
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm w-32 truncate capitalize">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemax={100}
        />
      </div>
      <span className="text-xs text-muted-foreground w-8 text-right">{pct}%</span>
    </div>
  );
}

// ── Conversation Card ─────────────────────────────────────────────────────────

function ConversationCard({
  conv,
  onAnswered,
}: {
  conv: LearningConversation;
  onAnswered: (id: string) => void;
}) {
  const { t } = useI18n();
  const [response, setResponse] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const handleSubmit = async () => {
    const answer = selectedOption ?? response.trim();
    if (!answer) return;
    setSubmitting(true);
    try {
      await respondToConversation(conv.id, answer);
      toast.success(t('preferences.response-submitted'));
      onAnswered(conv.id);
    } catch {
      toast.error(t('preferences.response-failed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-lg transition-all group">
      <div className="flex items-start gap-3">
        <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-200 group-hover:scale-110 transition-transform">
          <Brain className="h-5 w-5 animate-pulse" aria-hidden="true" />
        </div>
        <p className="text-sm font-medium leading-relaxed animate-in slide-in-from-right-2 duration-500 delay-100">
          {conv.question}
        </p>
      </div>

      {conv.options ? (
        <div className="flex flex-wrap gap-2 animate-in fade-in duration-500 delay-300">
          {conv.options.filter(Boolean).map((opt, index) => (
            <button
              key={opt}
              onClick={() => setSelectedOption(opt === selectedOption ? null : opt)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-all duration-200 cursor-pointer hover:scale-105 animate-in zoom-in-50 duration-300 ${
                selectedOption === opt
                  ? 'bg-primary text-primary-foreground border-primary scale-105 shadow-md'
                  : 'bg-background hover:bg-muted border-border'
              }`}
              style={{ animationDelay: `${400 + index * 100}ms` }}
            >
              {opt}
            </button>
          ))}
        </div>
      ) : (
        <textarea
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          placeholder={t('preferences.response-placeholder')}
          rows={2}
          className="w-full rounded-lg border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring transition-all duration-300 hover:shadow-sm focus:shadow-md animate-in slide-in-from-bottom-2 duration-500 delay-300"
          aria-label={t('preferences.response-placeholder')}
        />
      )}

      <Button
        size="sm"
        onClick={handleSubmit}
        disabled={submitting || (!selectedOption && !response.trim())}
        className="cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-md animate-in slide-in-from-left-2 duration-500 delay-500"
      >
        <Send
          className="h-3.5 w-3.5 mr-1.5 transition-transform duration-200 hover:translate-x-0.5"
          aria-hidden="true"
        />
        {submitting ? t('preferences.submitting') : t('preferences.submit')}
      </Button>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function PreferencesPage() {
  const { t } = useI18n();
  const [conversations, setConversations] = useState<LearningConversation[]>([]);
  const [prefs, setPrefs] = useState<PreferenceModel | null>(null);
  const [settings, setSettings] = useState<LearningSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [showWeights, setShowWeights] = useState(true);
  const [summary, setSummary] = useState<string>('');
  const [summaryUpdatedAt, setSummaryUpdatedAt] = useState<string | null>(null);
  const [savingSummary, setSavingSummary] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [convData, prefsData, settingsData, summaryData] = await Promise.all([
        getPendingConversations(),
        getPreferences(),
        getLearningSettings(),
        getPreferenceSummary(),
      ]);
      setConversations(convData.conversations);
      setPrefs(prefsData);
      setSettings(settingsData);
      setSummary(summaryData.preference_summary ?? '');
      setSummaryUpdatedAt(summaryData.summary_updated_at);
    } catch {
      toast.error(t('preferences.save-failed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAnswered = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
  };

  const handleToggleLearning = async () => {
    if (!settings) return;
    const newVal = !settings.learning_enabled;
    try {
      await updateLearningSettings({ learning_enabled: newVal });
      setSettings((s) => (s ? { ...s, learning_enabled: newVal } : s));
      toast.success(newVal ? t('preferences.settings-updated') : t('preferences.settings-updated'));
    } catch {
      toast.error(t('preferences.settings-failed'));
    }
  };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const result = await triggerLearning();
      if (result.triggered && result.conversation) {
        setConversations((prev) => [result.conversation!, ...prev]);
        toast.success(t('preferences.new-question'));
      } else {
        toast.success(result.reason ?? t('preferences.no-pending'));
      }
    } catch {
      toast.error(t('preferences.trigger-failed'));
    } finally {
      setTriggering(false);
    }
  };

  const weights = prefs?.category_weights ?? {};
  const hasWeights = Object.keys(weights).length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between animate-in fade-in slide-in-from-top-4 duration-500">
        <div>
          <h1 className="text-2xl font-bold">{t('preferences.title')}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t('preferences.description')}</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTrigger}
            disabled={triggering || settings?.learning_enabled === false}
            className="cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-md animate-in slide-in-from-right-4 duration-500 delay-200"
            aria-label={t('preferences.analyse-now')}
          >
            <RefreshCw
              className={`h-4 w-4 mr-1.5 transition-transform duration-200 ${triggering ? 'animate-spin' : 'hover:rotate-180'}`}
              aria-hidden="true"
            />
            {t('preferences.analyse-now')}
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="h-24 rounded-xl bg-muted animate-pulse"
              style={{ animationDelay: `${i * 200}ms` }}
            />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Settings card */}
          {settings && (
            <div className="rounded-xl border bg-card p-5 shadow-sm animate-in fade-in slide-in-from-left-4 duration-500 delay-300 hover:shadow-lg transition-all">
              <h2 className="text-base font-semibold mb-4">{t('preferences.settings-title')}</h2>
              <div className="flex items-center justify-between">
                <div className="animate-in slide-in-from-left-2 duration-500 delay-400">
                  <p className="text-sm font-medium">{t('preferences.proactive-learning')}</p>
                  <p className="text-xs text-muted-foreground">
                    {t('preferences.conversations-this-week', {
                      current: settings.conversations_this_week,
                      max: settings.max_weekly_conversations,
                    })}
                  </p>
                </div>
                <button
                  onClick={handleToggleLearning}
                  className="cursor-pointer transition-all duration-200 hover:scale-110 animate-in zoom-in-50 duration-500 delay-500"
                  aria-label={
                    settings.learning_enabled
                      ? t('preferences.proactive-learning')
                      : t('preferences.proactive-learning')
                  }
                >
                  {settings.learning_enabled ? (
                    <ToggleRight className="h-8 w-8 text-primary animate-pulse" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-muted-foreground" />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Pending conversations */}
          {conversations.length > 0 && (
            <section
              aria-labelledby="conversations-heading"
              className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-400"
            >
              <h2 id="conversations-heading" className="text-base font-semibold mb-3">
                {t('preferences.pending-questions')}
                <span className="ml-2 text-xs bg-primary/10 text-primary rounded-full px-2 py-0.5 animate-in zoom-in-50 duration-300 delay-500">
                  {conversations.length}
                </span>
              </h2>
              <div className="space-y-3">
                {conversations.map((conv, index) => (
                  <div key={conv.id} style={{ animationDelay: `${600 + index * 150}ms` }}>
                    <ConversationCard conv={conv} onAnswered={handleAnswered} />
                  </div>
                ))}
              </div>
            </section>
          )}

          {conversations.length === 0 && settings?.learning_enabled && (
            <div className="rounded-xl border bg-card p-5 text-center text-sm text-muted-foreground animate-in fade-in slide-in-from-bottom-4 duration-500 delay-600">
              {t('preferences.no-pending')}
            </div>
          )}

          {/* Preference summary */}
          <section
            aria-labelledby="summary-heading"
            className="animate-in fade-in slide-in-from-right-4 duration-500 delay-500"
          >
            <h2 id="summary-heading" className="text-base font-semibold mb-3">
              偏好摘要
            </h2>
            <div className="rounded-xl border bg-card p-5 shadow-sm space-y-3 hover:shadow-lg transition-all">
              <p className="text-xs text-muted-foreground animate-in slide-in-from-top-2 duration-500 delay-600">
                直接在 Discord DM 裡告訴 bot
                你的偏好，每天會自動更新這份摘要。你也可以直接在這裡編輯。
                {summaryUpdatedAt && ` 上次更新：${summaryUpdatedAt.slice(0, 10)}`}
              </p>
              <textarea
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="例如：我喜歡 Rust 和系統設計，偏好進階內容，不喜歡入門教學和 LLM wrapper 文章。"
                rows={4}
                className="w-full rounded-lg border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring transition-all duration-300 hover:shadow-sm focus:shadow-md animate-in slide-in-from-bottom-2 duration-500 delay-700"
              />
              <Button
                size="sm"
                onClick={async () => {
                  setSavingSummary(true);
                  try {
                    await updatePreferenceSummary(summary);
                    toast.success('偏好摘要已儲存');
                  } catch {
                    toast.error('儲存失敗，請稍後再試');
                  } finally {
                    setSavingSummary(false);
                  }
                }}
                disabled={savingSummary}
                className="cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-md animate-in slide-in-from-left-2 duration-500 delay-800"
              >
                <Save className="h-3.5 w-3.5 mr-1.5 transition-transform duration-200 hover:rotate-12" />
                {savingSummary ? '儲存中...' : '儲存'}
              </Button>
            </div>
          </section>

          {/* Category weights */}
          <section
            aria-labelledby="weights-heading"
            className="animate-in fade-in slide-in-from-left-4 duration-500 delay-600"
          >
            <button
              className="flex items-center gap-2 text-base font-semibold mb-3 cursor-pointer hover:text-primary transition-all duration-200 hover:scale-105"
              onClick={() => setShowWeights((v) => !v)}
              aria-expanded={showWeights}
              id="weights-heading"
            >
              {t('preferences.interest-weights')}
              <div className="transition-transform duration-200">
                {showWeights ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </div>
            </button>

            {showWeights && (
              <div className="rounded-xl border bg-card p-5 shadow-sm space-y-3 hover:shadow-lg transition-all animate-in slide-in-from-bottom-4 duration-500">
                {hasWeights ? (
                  Object.entries(weights)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cat, w], index) => (
                      <div
                        key={cat}
                        className="animate-in slide-in-from-left-2 duration-300"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <WeightBar label={cat} value={w} />
                      </div>
                    ))
                ) : (
                  <p className="text-sm text-muted-foreground animate-in fade-in duration-500">
                    {t('preferences.no-weights')}
                  </p>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
