'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import { BookOpen, Target, Clock, TrendingUp, Plus, ChevronRight, Trash2 } from 'lucide-react';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';
import {
  createLearningGoal,
  getLearningGoals,
  deleteLearningGoal,
  type LearningGoal,
} from '@/lib/api/learning-path';

const statusConfig = {
  active: {
    label: null,
    labelKey: 'status.active',
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  completed: {
    label: null,
    labelKey: 'status.completed',
    className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  },
  paused: {
    label: null,
    labelKey: 'status.paused',
    className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  },
  cancelled: {
    label: null,
    labelKey: 'status.cancelled',
    className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  },
};

export default function LearningPathPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [goalText, setGoalText] = useState('');
  const router = useRouter();
  const queryClient = useQueryClient();
  const { t } = useI18n();

  const { data: goals = [], isLoading } = useQuery({
    queryKey: ['learningGoals'],
    queryFn: getLearningGoals,
  });

  const createGoalMutation = useMutation({
    mutationFn: createLearningGoal,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['learningGoals'] });
      setGoalText('');
      setShowCreateForm(false);
      if (data.suggested_feeds?.length) {
        toast.success(
          t('learning.goal-created-with-feeds', {
            feeds: data.suggested_feeds.map((f) => f.name).join('、'),
          })
        );
      } else {
        toast.success(t('learning.goal-created'));
      }
      if (data.goal_id) router.push(`/app/learning/${data.goal_id}`);
    },
    onError: () => toast.error(t('learning.goal-create-failed')),
  });

  const deleteGoalMutation = useMutation({
    mutationFn: deleteLearningGoal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learningGoals'] });
      toast.success(t('learning.goal-deleted'));
    },
    onError: () => toast.error(t('learning.goal-delete-failed')),
  });

  const handleCreate = () => {
    if (!goalText.trim()) return toast.error(t('errors.required-field'));
    createGoalMutation.mutate({ goal_text: goalText });
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-7 w-32" />
            <Skeleton className="h-4 w-52" />
          </div>
          <Skeleton className="h-9 w-24 rounded-md" />
        </div>
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">{t('learning.title')}</h1>
          <p className="text-muted-foreground text-sm mt-1">{t('learning.subtitle')}</p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('learning.add-goal')}
        </Button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <Card className="mb-6 border-primary/20">
          <CardHeader>
            <CardTitle className="text-base">{t('learning.create-goal-title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              placeholder={t('learning.create-goal-placeholder')}
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              rows={2}
              className="resize-none"
            />
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={createGoalMutation.isPending} size="sm">
                {createGoalMutation.isPending ? '...' : t('learning.create-goal-submit')}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowCreateForm(false)}>
                {t('buttons.cancel')}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Goals List */}
      {goals.length > 0 ? (
        <div className="space-y-3">
          {goals.map((goal: LearningGoal) => {
            const status =
              statusConfig[goal.status as keyof typeof statusConfig] ?? statusConfig.active;
            return (
              <Card
                key={goal.id}
                className="cursor-pointer hover:shadow-md transition-all hover:border-primary/30"
                onClick={() => router.push(`/app/learning/${goal.id}`)}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold truncate">{goal.title}</span>
                        <Badge
                          variant="secondary"
                          className={`text-xs shrink-0 ${status.className}`}
                        >
                          {t(status.labelKey as Parameters<typeof t>[0])}
                        </Badge>
                      </div>
                      {goal.description && (
                        <p className="text-sm text-muted-foreground line-clamp-1 mb-2">
                          {goal.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <BookOpen className="h-3 w-3" />
                          {goal.target_skill}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {t('learning.stage-hours', { hours: goal.estimated_hours })}
                        </span>
                        <span className="flex items-center gap-1">
                          <TrendingUp className="h-3 w-3" />
                          {goal.difficulty_level}/5
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(t('messages.confirm-delete'))) {
                            deleteGoalMutation.mutate(goal.id);
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <ChevronRight className="h-5 w-5 text-muted-foreground" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Target className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="font-semibold mb-1">{t('learning.empty-title')}</h3>
            <p className="text-sm text-muted-foreground text-center mb-4">
              {t('learning.empty-desc')}
            </p>
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              {t('learning.create-first')}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
