'use client';
import { logger } from '@/lib/utils/logger';

import { useState } from 'react';
import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BookOpen,
  Target,
  Clock,
  TrendingUp,
  Plus,
  CheckCircle,
  Circle,
  AlertCircle,
  Star,
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
  const [selectedContentType, setSelectedContentType] = useState<string>('all');
  const [articles, setArticles] = useState<any[]>([]);
  const [loadingArticles, setLoadingArticles] = useState(false);
  const queryClient = useQueryClient();

  const { data: goals, isLoading } = useQuery({
    queryKey: ['learningGoals'],
    queryFn: getLearningGoals,
  });

  // Fetch learning content
  const fetchLearningContent = async () => {
    try {
      setLoadingArticles(true);
      const contentTypes =
        selectedContentType === 'all'
          ? ['tutorial', 'guide', 'project', 'reference']
          : [selectedContentType];

      const params = new URLSearchParams({
        content_types: contentTypes.join(','),
        limit: '12',
      });

      const response = await fetch(`/api/learning-content-simple/articles?${params}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setArticles(data.recommendations || []);
      }
    } catch (error) {
      console.error('Failed to fetch learning content:', error);
    } finally {
      setLoadingArticles(false);
    }
  };

  // Load articles when content type changes
  React.useEffect(() => {
    fetchLearningContent();
  }, [selectedContentType]);

  const getDifficultyLabel = (level: number) => {
    const labels = { 1: 'Beginner', 2: 'Intermediate', 3: 'Advanced', 4: 'Expert' };
    return labels[level as keyof typeof labels] || 'Unknown';
  };

  const getTypeColor = (type: string) => {
    const colors = {
      tutorial: 'bg-blue-100 text-blue-800',
      guide: 'bg-green-100 text-green-800',
      project: 'bg-purple-100 text-purple-800',
      reference: 'bg-gray-100 text-gray-800',
      news: 'bg-orange-100 text-orange-800',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const createGoalMutation = useMutation({
    mutationFn: createLearningGoal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learningGoals'] });
      setGoalText('');
      setShowCreateForm(false);
      toast.success('學習目標創建成功！');
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">學習中心</h1>
        <p className="text-gray-600">規劃學習路徑並發現優質教育內容</p>
      </div>

      <Tabs defaultValue="paths" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="paths">學習路徑</TabsTrigger>
          <TabsTrigger value="content">推薦內容</TabsTrigger>
        </TabsList>

        <TabsContent value="paths" className="space-y-6">
          {/* Create Goal Button */}
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">我的學習目標</h2>
            <Button onClick={() => setShowCreateForm(!showCreateForm)}>
              <Plus className="h-4 w-4 mr-2" />
              新增目標
            </Button>
          </div>

          {/* Create Goal Form */}
          {showCreateForm && (
            <Card>
              <CardHeader>
                <CardTitle>創建新的學習目標</CardTitle>
                <CardDescription>描述你想要學習的技能或知識</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="例如：學會 React 開發，掌握 Python 數據分析..."
                  value={goalText}
                  onChange={(e) => setGoalText(e.target.value)}
                  rows={3}
                />
                <div className="flex gap-2">
                  <Button onClick={handleCreateGoal} disabled={createGoalMutation.isPending}>
                    {createGoalMutation.isPending ? '創建中...' : '創建目標'}
                  </Button>
                  <Button variant="outline" onClick={() => setShowCreateForm(false)}>
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
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{goal.target_skill}</span>
                    </div>
                    <div className="flex gap-2 pt-2">
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={() => (window.location.href = `/app/learning/${goal.id}`)}
                      >
                        查看詳情
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleDeleteGoal(goal.id)}>
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
                <Target className="h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">還沒有學習目標</h3>
                <p className="text-gray-600 text-center mb-4">
                  創建你的第一個學習目標，開始個人化的學習旅程
                </p>
                <Button onClick={() => setShowCreateForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  創建目標
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="content" className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">推薦學習內容</h2>
            <div className="flex gap-2">
              <Button
                variant={selectedContentType === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedContentType('all')}
              >
                全部
              </Button>
              <Button
                variant={selectedContentType === 'tutorial' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedContentType('tutorial')}
              >
                教程
              </Button>
              <Button
                variant={selectedContentType === 'guide' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedContentType('guide')}
              >
                指南
              </Button>
              <Button
                variant={selectedContentType === 'project' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedContentType('project')}
              >
                項目
              </Button>
            </div>
          </div>

          {loadingArticles ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : articles.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {articles.map((item: any) => (
                <Card key={item.article.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between mb-2">
                      <Badge className={getTypeColor(item.classification.content_type)}>
                        {item.classification.content_type}
                      </Badge>
                      <div className="flex items-center text-sm text-gray-500">
                        <Star className="h-4 w-4 mr-1" />
                        {item.classification.learning_value_score.toFixed(1)}
                      </div>
                    </div>
                    <CardTitle className="text-base leading-tight">
                      <a
                        href={item.article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-blue-600 transition-colors"
                      >
                        {item.article.title}
                      </a>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                      <div className="flex items-center">
                        <TrendingUp className="h-4 w-4 mr-1" />
                        {getDifficultyLabel(item.classification.difficulty_level)}
                      </div>
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {item.classification.educational_features.estimated_reading_time}min
                      </div>
                    </div>

                    {item.article.ai_summary && (
                      <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                        {item.article.ai_summary}
                      </p>
                    )}

                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">
                        {new Date(item.article.published_at).toLocaleDateString()}
                      </span>
                      <Button size="sm" variant="outline" asChild>
                        <a href={item.article.url} target="_blank" rel="noopener noreferrer">
                          閱讀
                        </a>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <BookOpen className="h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">暫無學習內容</h3>
                <p className="text-gray-600 text-center mb-4">系統正在處理文章，請稍後再試</p>
                <Button onClick={fetchLearningContent}>重新載入</Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
