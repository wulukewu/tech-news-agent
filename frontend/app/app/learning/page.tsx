'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { BookOpen, Target, Clock, TrendingUp, Plus, ChevronRight, Trash2 } from 'lucide-react';
import { toast } from '@/lib/toast';
import {
  createLearningGoal,
  getLearningGoals,
  deleteLearningGoal,
  type LearningGoal,
} from '@/lib/api/learning-path';

const statusConfig = {
  active: {
    label: '進行中',
    className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  completed: {
    label: '已完成',
    className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  },
  paused: {
    label: '暫停',
    className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  },
  cancelled: {
    label: '已取消',
    className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  },
};

export default function LearningPathPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [goalText, setGoalText] = useState('');
  const router = useRouter();
  const queryClient = useQueryClient();

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
      toast.success('學習目標創建成功！');
      if (data.goal_id) router.push(`/app/learning/${data.goal_id}`);
    },
    onError: () => toast.error('創建學習目標失敗'),
  });

  const deleteGoalMutation = useMutation({
    mutationFn: deleteLearningGoal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learningGoals'] });
      toast.success('學習目標已刪除');
    },
    onError: () => toast.error('刪除失敗'),
  });

  const handleCreate = () => {
    if (!goalText.trim()) return toast.error('請輸入學習目標');
    createGoalMutation.mutate({ goal_text: goalText });
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">學習路徑</h1>
          <p className="text-muted-foreground text-sm mt-1">設定目標，系統自動規劃學習計劃</p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)}>
          <Plus className="h-4 w-4 mr-2" />
          新增目標
        </Button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <Card className="mb-6 border-primary/20">
          <CardHeader>
            <CardTitle className="text-base">新增學習目標</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              placeholder="例如：學習 Kubernetes 容器編排、掌握 React 前端開發..."
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              rows={2}
              className="resize-none"
            />
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={createGoalMutation.isPending} size="sm">
                {createGoalMutation.isPending ? '生成中...' : '建立並生成路徑'}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowCreateForm(false)}>
                取消
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
                          {status.label}
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
                          {goal.estimated_hours} 小時
                        </span>
                        <span className="flex items-center gap-1">
                          <TrendingUp className="h-3 w-3" />
                          難度 {goal.difficulty_level}/5
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
                          if (confirm('確定要刪除這個學習目標嗎？')) {
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
            <h3 className="font-semibold mb-1">還沒有學習目標</h3>
            <p className="text-sm text-muted-foreground text-center mb-4">
              輸入你想學的技術，系統會自動生成階段性學習計劃
            </p>
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              建立第一個目標
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
