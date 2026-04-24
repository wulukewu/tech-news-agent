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
  type LearningConversation,
  type PreferenceModel,
  type LearningSettings,
} from '@/lib/api/proactive-learning';

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
  const [response, setResponse] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const handleSubmit = async () => {
    const answer = selectedOption ?? response.trim();
    if (!answer) return;
    setSubmitting(true);
    try {
      await respondToConversation(conv.id, answer);
      toast.success('Response submitted!');
      onAnswered(conv.id);
    } catch {
      toast.error('Failed to submit response.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm space-y-4">
      <div className="flex items-start gap-3">
        <Brain className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" aria-hidden="true" />
        <p className="text-sm font-medium leading-relaxed">{conv.question}</p>
      </div>

      {conv.options ? (
        <div className="flex flex-wrap gap-2">
          {conv.options.filter(Boolean).map((opt) => (
            <button
              key={opt}
              onClick={() => setSelectedOption(opt === selectedOption ? null : opt)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors cursor-pointer ${
                selectedOption === opt
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-background hover:bg-muted border-border'
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      ) : (
        <textarea
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          placeholder="Type your response…"
          rows={2}
          className="w-full rounded-lg border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
          aria-label="Your response"
        />
      )}

      <Button
        size="sm"
        onClick={handleSubmit}
        disabled={submitting || (!selectedOption && !response.trim())}
        className="cursor-pointer"
      >
        <Send className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
        {submitting ? 'Sending…' : 'Submit'}
      </Button>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function PreferencesPage() {
  const [conversations, setConversations] = useState<LearningConversation[]>([]);
  const [prefs, setPrefs] = useState<PreferenceModel | null>(null);
  const [settings, setSettings] = useState<LearningSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [showWeights, setShowWeights] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [convData, prefsData, settingsData] = await Promise.all([
        getPendingConversations(),
        getPreferences(),
        getLearningSettings(),
      ]);
      setConversations(convData.conversations);
      setPrefs(prefsData);
      setSettings(settingsData);
    } catch {
      toast.error('Failed to load preferences.');
    } finally {
      setLoading(false);
    }
  }, []);

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
      toast.success(newVal ? 'Proactive learning enabled.' : 'Proactive learning disabled.');
    } catch {
      toast.error('Failed to update settings.');
    }
  };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const result = await triggerLearning();
      if (result.triggered && result.conversation) {
        setConversations((prev) => [result.conversation!, ...prev]);
        toast.success('New learning question generated!');
      } else {
        toast.success(result.reason ?? 'No trigger condition met right now.');
      }
    } catch {
      toast.error('Failed to trigger analysis.');
    } finally {
      setTriggering(false);
    }
  };

  const weights = prefs?.category_weights ?? {};
  const hasWeights = Object.keys(weights).length > 0;

  return (
    <main id="main-content" className="container mx-auto px-4 py-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Learning Preferences</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Proactive AI that learns your reading interests
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTrigger}
            disabled={triggering || settings?.learning_enabled === false}
            className="cursor-pointer"
            aria-label="Trigger behavior analysis"
          >
            <RefreshCw
              className={`h-4 w-4 mr-1.5 ${triggering ? 'animate-spin' : ''}`}
              aria-hidden="true"
            />
            Analyse Now
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Settings card */}
          {settings && (
            <div className="rounded-xl border bg-card p-5 shadow-sm">
              <h2 className="text-base font-semibold mb-4">Settings</h2>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Proactive Learning</p>
                  <p className="text-xs text-muted-foreground">
                    {settings.conversations_this_week}/{settings.max_weekly_conversations}{' '}
                    conversations this week
                  </p>
                </div>
                <button
                  onClick={handleToggleLearning}
                  className="cursor-pointer"
                  aria-label={
                    settings.learning_enabled
                      ? 'Disable proactive learning'
                      : 'Enable proactive learning'
                  }
                >
                  {settings.learning_enabled ? (
                    <ToggleRight className="h-8 w-8 text-primary" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-muted-foreground" />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Pending conversations */}
          {conversations.length > 0 && (
            <section aria-labelledby="conversations-heading">
              <h2 id="conversations-heading" className="text-base font-semibold mb-3">
                Pending Questions
                <span className="ml-2 text-xs bg-primary/10 text-primary rounded-full px-2 py-0.5">
                  {conversations.length}
                </span>
              </h2>
              <div className="space-y-3">
                {conversations.map((conv) => (
                  <ConversationCard key={conv.id} conv={conv} onAnswered={handleAnswered} />
                ))}
              </div>
            </section>
          )}

          {conversations.length === 0 && settings?.learning_enabled && (
            <div className="rounded-xl border bg-card p-5 text-center text-sm text-muted-foreground">
              No pending questions. The system will ask when it detects interest changes.
            </div>
          )}

          {/* Category weights */}
          <section aria-labelledby="weights-heading">
            <button
              className="flex items-center gap-2 text-base font-semibold mb-3 cursor-pointer hover:text-primary transition-colors"
              onClick={() => setShowWeights((v) => !v)}
              aria-expanded={showWeights}
              id="weights-heading"
            >
              Interest Weights
              {showWeights ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>

            {showWeights && (
              <div className="rounded-xl border bg-card p-5 shadow-sm space-y-3">
                {hasWeights ? (
                  Object.entries(weights)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cat, w]) => <WeightBar key={cat} label={cat} value={w} />)
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No preference data yet. Start reading and rating articles to build your profile.
                  </p>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
