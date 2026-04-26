'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BookOpen,
  Target,
  Clock,
  TrendingUp,
  CheckCircle,
  Circle,
  ExternalLink,
  BarChart3,
  Settings,
  Lightbulb,
} from 'lucide-react';
import { toast } from '@/lib/toast';
import {
  getLearningGoalDetails,
  getLearningProgress,
  getArticleRecommendations,
  markArticleComplete,
  getLearningEvaluation,
  type LearningGoalDetails,
  type LearningProgress,
  type ArticleRecommendation,
} from '@/lib/api/learning-path';

const stageColors = {
  foundation: 'bg-blue-500',
  intermediate: 'bg-yellow-500',
  advanced: 'bg-red-500',
};

const stageLabels = {
  foundation: '基礎',
  intermediate: '中級',
  advanced: '進階',
};

export default function LearningGoalDetailPage() {
  const params = useParams();
  const goalId = params.id as string;
  const [selectedStage, setSelectedStage] = useState(1);
  const queryClient = useQueryClient();

  const { data: goalDetails, isLoading: goalLoading } = useQuery({
    queryKey: ['learningGoal', goalId],
    queryFn: () => getLearningGoalDetails(goalId),
  });

  const { data: progress, isLoading: progressLoading } = useQuery({
    queryKey: ['learningProgress', goalId],
    queryFn: () => getLearningProgress(goalId),
  });

  const { data: recommendations, isLoading: recommendationsLoading } = useQuery({
    queryKey: ['recommendations', goalId, selectedStage],
    queryFn: () => getArticleRecommendations(goalId, selectedStage),
  });

  const { data: evaluation } = useQuery({
    queryKey: ['evaluation', goalId],
    queryFn: () => getLearningEvaluation(goalId),
  });

  const completeArticleMutation = useMutation({
    mutationFn: ({
      articleId,
      timeSpent,
      notes,
    }: {
      articleId: string;
      timeSpent: number;
      notes: string;
    }) => markArticleComplete(goalId, articleId, { time_spent_minutes: timeSpent, notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learningProgress', goalId] });
      queryClient.invalidateQueries({ queryKey: ['recommendations', goalId] });
      toast.success('文章標記為已完成');
    },
    onError: () => toast.error('標記失敗'),
  });

  const handleCompleteArticle = (articleId: string) => {
    const timeSpent = Math.floor(Math.random() * 60) + 15; // 15-75 minutes
    completeArticleMutation.mutate({ articleId, timeSpent, notes: '' });
  };

  if (goalLoading || progressLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!goalDetails) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">學習目標不存在</h3>
            <Button onClick={() => (window.location.href = '/app/learning')}>返回學習路徑</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const goal = goalDetails.goal;
  const learningPath = goalDetails.learning_path;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Target className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">{goal.title}</h1>
        </div>
        <p className="text-muted-foreground">{goal.description}</p>

        {/* Goal Stats */}
        <div className="flex gap-6 mt-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">難度 {goal.difficulty_level}/5</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">預估 {goal.estimated_hours} 小時</span>
          </div>
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">目標技能：{goal.target_skill}</span>
          </div>
        </div>

        {/* Overall Progress */}
        {progress && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">整體進度</span>
              <span className="text-sm text-muted-foreground">{progress.overall_completion}%</span>
            </div>
            <Progress value={progress.overall_completion} className="h-2" />
          </div>
        )}
      </div>

      <Tabs defaultValue="path" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="path">學習路徑</TabsTrigger>
          <TabsTrigger value="recommendations">推薦文章</TabsTrigger>
          <TabsTrigger value="progress">學習進度</TabsTrigger>
          <TabsTrigger value="evaluation">成效評估</TabsTrigger>
        </TabsList>

        {/* Learning Path Tab */}
        <TabsContent value="path" className="space-y-6">
          {learningPath && learningPath.stages ? (
            <div className="grid gap-6">
              {learningPath.stages.map((stage: any, index: number) => (
                <Card key={stage.order} className="relative">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge
                          className={`${stageColors[stage.name as keyof typeof stageColors]} text-white`}
                        >
                          階段 {stage.order}
                        </Badge>
                        <CardTitle>
                          {stageLabels[stage.name as keyof typeof stageLabels] || stage.name}
                        </CardTitle>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        {stage.estimated_hours} 小時
                      </div>
                    </div>
                    <CardDescription>{stage.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <h4 className="font-medium">涵蓋技能：</h4>
                      <div className="flex flex-wrap gap-2">
                        {stage.skills.map((skill: string, skillIndex: number) => (
                          <Badge key={skillIndex} variant="outline">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {progress && progress.stages[index] && (
                      <div className="mt-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">階段進度</span>
                          <span className="text-sm text-muted-foreground">
                            {progress.stages[index].completion_percentage}%
                          </span>
                        </div>
                        <Progress
                          value={progress.stages[index].completion_percentage}
                          className="h-2"
                        />
                      </div>
                    )}

                    <Button
                      className="mt-4"
                      onClick={() => {
                        setSelectedStage(stage.order);
                        // Switch to recommendations tab
                        const tabsTrigger = document.querySelector(
                          '[value="recommendations"]'
                        ) as HTMLElement;
                        tabsTrigger?.click();
                      }}
                    >
                      查看推薦文章
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <BookOpen className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">學習路徑生成中</h3>
                <p className="text-muted-foreground">請稍候...</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="space-y-6">
          <div className="flex items-center gap-4 mb-4">
            <span className="font-medium">選擇階段：</span>
            {learningPath?.stages?.map((stage: any) => (
              <Button
                key={stage.order}
                variant={selectedStage === stage.order ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedStage(stage.order)}
              >
                階段 {stage.order}
              </Button>
            ))}
          </div>

          {recommendationsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : recommendations && recommendations.articles.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{recommendations.stage_name} 階段推薦文章</h3>
                <Badge variant="secondary">{recommendations.total_count} 篇文章</Badge>
              </div>

              <div className="grid gap-4">
                {recommendations.articles.map((article: any) => (
                  <Card key={article.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold mb-2">{article.title}</h4>
                          <p className="text-sm text-muted-foreground mb-3">{article.reason}</p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>相關度: {(article.relevance_score * 100).toFixed(0)}%</span>
                            <span>難度匹配: {(article.difficulty_match * 100).toFixed(0)}%</span>
                            {article.category && (
                              <Badge variant="outline">{article.category}</Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2 ml-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => window.open(article.url, '_blank')}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleCompleteArticle(article.id)}
                            disabled={completeArticleMutation.isPending}
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Lightbulb className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">暫無推薦文章</h3>
                <p className="text-muted-foreground">請稍後再試或選擇其他階段</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Progress Tab */}
        <TabsContent value="progress" className="space-y-6">
          {progress ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>學習統計</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">
                        {progress.overall_completion}%
                      </div>
                      <div className="text-sm text-muted-foreground">整體完成度</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">
                        {progress.current_stage}
                      </div>
                      <div className="text-sm text-muted-foreground">當前階段</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">
                        {progress.stages.length}
                      </div>
                      <div className="text-sm text-muted-foreground">總階段數</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-primary">
                        {progress.stages.reduce((sum, stage) => sum + stage.articles_completed, 0)}
                      </div>
                      <div className="text-sm text-muted-foreground">已完成文章</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold">各階段進度</h3>
                {progress.stages.map((stage: any, index: number) => (
                  <Card key={index}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-medium">
                          階段 {stage.order}: {stage.name}
                        </h4>
                        <Badge variant={stage.status === 'completed' ? 'default' : 'secondary'}>
                          {stage.status === 'completed'
                            ? '已完成'
                            : stage.status === 'in_progress'
                              ? '進行中'
                              : '未開始'}
                        </Badge>
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span>完成進度</span>
                          <span>{stage.completion_percentage}%</span>
                        </div>
                        <Progress value={stage.completion_percentage} className="h-2" />

                        <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                          <div>
                            已完成文章: {stage.articles_completed}/{stage.articles_total}
                          </div>
                          <div>學習時間: {stage.time_spent_hours.toFixed(1)} 小時</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {progress.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>學習建議</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {progress.recommendations.map((rec: string, index: number) => (
                        <li key={index} className="flex items-start gap-2">
                          <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">暫無進度數據</h3>
                <p className="text-muted-foreground">開始學習後將顯示進度統計</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Evaluation Tab */}
        <TabsContent value="evaluation" className="space-y-6">
          {evaluation ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>整體表現</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-primary mb-2">
                      {evaluation.overall_performance === 'excellent'
                        ? '優秀'
                        : evaluation.overall_performance === 'good'
                          ? '良好'
                          : evaluation.overall_performance === 'average'
                            ? '一般'
                            : evaluation.overall_performance === 'below_average'
                              ? '待改進'
                              : '需要努力'}
                    </div>
                    <p className="text-muted-foreground">學習表現評級</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>效率指標</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-xl font-bold">
                        {(evaluation.efficiency_metrics.time_efficiency * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">時間效率</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold">
                        {(evaluation.efficiency_metrics.completion_rate * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">完成率</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold">
                        {(evaluation.efficiency_metrics.retention_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">知識保持</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold">
                        {(evaluation.efficiency_metrics.consistency_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">學習一致性</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="grid md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-green-600">學習優勢</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {evaluation.strengths.map((strength: string, index: number) => (
                        <li key={index} className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-orange-600">改進空間</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {evaluation.weaknesses.map((weakness: string, index: number) => (
                        <li key={index} className="flex items-start gap-2">
                          <Circle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{weakness}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>優化建議</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {evaluation.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>下一步行動</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {evaluation.next_steps.map((step: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <Target className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{step}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">暫無評估數據</h3>
                <p className="text-muted-foreground">需要更多學習數據才能生成評估報告</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
