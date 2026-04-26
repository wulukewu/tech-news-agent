'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import {
  BookOpen,
  Target,
  Clock,
  TrendingUp,
  Plus,
  CheckCircle,
  Circle,
  AlertCircle,
} from 'lucide-react';
import { toast } from '@/lib/toast';
import {
  createLearningGoal,
  getLearningGoals,
  deleteLearningGoal,
  type LearningGoal,
} from '@/lib/api/learning-path';

const statusColors = {
  active: 'bg-blue-500',
  completed: 'bg-green-500',
  paused: 'bg-yellow-500',
  cancelled: 'bg-gray-500',
};

const statusLabels = {
  active: '進行中',
  completed: '已完成',
  paused: '暫停',
  cancelled: '已取消',
};

export default function LearningPathPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [goalText, setGoalText] = useState('');
  const queryClient = useQueryClient();

  const { data: goals, isLoading } = useQuery({
    queryKey: ['learningGoals'],
    queryFn: getLearningGoals,
  });

  const createGoalMutation = useMutation({
    mutationFn: createLearningGoal,
    onSuccess: (data) => {
      if (data.success) {
        queryClient.invalidateQueries({ queryKey: ['learningGoals'] });
        setGoalText('');
        setShowCreateForm(false);
        toast.success('學習目標創建成功！');
      } else {
        toast.error(data.message || '創建失敗');
      }
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

  const handleCreateGoal = () => {
    if (!goalText.trim()) {
      toast.error('請輸入學習目標');
      return;
    }
    createGoalMutation.mutate({ goal_text: goalText });
  };

  const handleDeleteGoal = (goalId: string) => {
    if (confirm('確定要刪除這個學習目標嗎？')) {
      deleteGoalMutation.mutate(goalId);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Target className="h-8 w-8 text-primary" />
            學習路徑
          </h1>
          <p className="text-muted-foreground mt-2">設定學習目標，獲得個人化的學習路徑和文章推薦</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          新增學習目標
        </Button>
      </div>

      {/* Create Goal Form */}
      {showCreateForm && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>創建新的學習目標</CardTitle>
            <CardDescription>
              用自然語言描述你想學習的技能，例如：「我想學習 Kubernetes」
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="我想學習..."
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              className="min-h-[100px]"
            />
            <div className="flex gap-2">
              <Button onClick={handleCreateGoal} disabled={createGoalMutation.isPending}>
                {createGoalMutation.isPending ? '創建中...' : '創建學習目標'}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowCreateForm(false);
                  setGoalText('');
                }}
              >
                取消
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Goals List */}
      {goals && goals.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal: LearningGoal) => (
            <Card key={goal.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{goal.title}</CardTitle>
                    <CardDescription className="mt-1">{goal.description}</CardDescription>
                  </div>
                  <Badge
                    variant="secondary"
                    className={`${statusColors[goal.status as keyof typeof statusColors]} text-white`}
                  >
                    {statusLabels[goal.status as keyof typeof statusLabels]}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Goal Info */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    <span>難度 {goal.difficulty_level}/5</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{goal.estimated_hours} 小時</span>
                  </div>
                </div>

                {/* Target Skill */}
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{goal.target_skill}</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => (window.location.href = `/learning/${goal.id}`)}
                  >
                    查看詳情
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteGoal(goal.id)}
                    disabled={deleteGoalMutation.isPending}
                  >
                    刪除
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">還沒有學習目標</h3>
            <p className="text-muted-foreground text-center mb-4">
              創建你的第一個學習目標，開始個人化的學習旅程
            </p>
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              創建學習目標
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
