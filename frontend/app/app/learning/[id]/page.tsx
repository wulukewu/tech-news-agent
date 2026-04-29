'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  ExternalLink,
  ChevronLeft,
  BarChart3,
  Lightbulb,
  Circle,
} from 'lucide-react';
import { toast } from '@/lib/toast';
import {
  getLearningGoalDetails,
  getLearningProgress,
  getArticleRecommendations,
  markArticleComplete,
  getLearningEvaluation,
} from '@/lib/api/learning-path';

const stageColorMap: Record<string, string> = {
  foundation: 'bg-blue-500',
  intermediate: 'bg-amber-500',
  advanced: 'bg-red-500',
};

const stageLabelMap: Record<string, string> = {
  foundation: '基礎',
  intermediate: '中級',
  advanced: '進階',
};

export default function LearningGoalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const goalId = params.id as string;
  const [selectedStage, setSelectedStage] = useState(1);
  const [selectedTab, setSelectedTab] = useState('path');
  const queryClient = useQueryClient();

  const { data: goalDetails, isLoading } = useQuery({
    queryKey: ['learningGoal', goalId],
    queryFn: () => getLearningGoalDetails(goalId),
  });

  const { data: progress } = useQuery({
    queryKey: ['learningProgress', goalId],
    queryFn: () => getLearningProgress(goalId),
  });

  const { data: recommendations, isLoading: recLoading } = useQuery({
    queryKey: ['recommendations', goalId, selectedStage],
    queryFn: () => getArticleRecommendations(goalId, selectedStage),
    enabled: selectedTab === 'recommendations',
  });

  const { data: evaluation } = useQuery({
    queryKey: ['evaluation', goalId],
    queryFn: () => getLearningEvaluation(goalId),
    enabled: selectedTab === 'evaluation',
  });

  const completeArticleMutation = useMutation({
    mutationFn: ({ articleId }: { articleId: string }) =>
      markArticleComplete(goalId, articleId, { time_spent_minutes: 30, notes: '' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learningProgress', goalId] });
      queryClient.invalidateQueries({ queryKey: ['recommendations', goalId] });
      toast.success('已標記為完成');
    },
    onError: () => toast.error('標記失敗'),
  });

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!goalDetails) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => router.push('/app/learning')} className="mb-4">
          <ChevronLeft className="h-4 w-4 mr-1" /> 返回
        </Button>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">學習目標不存在</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const goal = goalDetails.goal;
  const learningPath = goalDetails.learning_path;
  const stages = learningPath?.stages ?? [];

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Back */}
      <Button variant="ghost" onClick={() => router.push('/app/learning')} className="mb-4 -ml-2">
        <ChevronLeft className="h-4 w-4 mr-1" /> 返回學習路徑
      </Button>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1">{goal.title}</h1>
        {goal.description && (
          <p className="text-muted-foreground text-sm mb-3">{goal.description}</p>
        )}
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <BookOpen className="h-4 w-4" /> {goal.target_skill}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-4 w-4" /> {goal.estimated_hours} 小時
          </span>
          <span className="flex items-center gap-1">
            <TrendingUp className="h-4 w-4" /> 難度 {goal.difficulty_level}/5
          </span>
        </div>

        {progress && (
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">整體進度</span>
              <span className="font-medium">{progress.overall_completion}%</span>
            </div>
            <Progress value={progress.overall_completion} className="h-2" />
          </div>
        )}
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="path">學習路徑</TabsTrigger>
          <TabsTrigger value="recommendations">推薦文章</TabsTrigger>
          <TabsTrigger value="progress">進度 & 評估</TabsTrigger>
        </TabsList>

        {/* Path Tab */}
        <TabsContent value="path" className="space-y-4">
          {stages.length > 0 ? (
            stages.map((stage: any, index: number) => {
              const stageProgress = progress?.stages?.[index];
              const colorClass = stageColorMap[stage.name] ?? 'bg-gray-500';
              const label = stageLabelMap[stage.name] ?? stage.name;
              return (
                <Card key={stage.order}>
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex items-center gap-2">
                        <span className={`inline-block w-2 h-2 rounded-full ${colorClass}`} />
                        <span className="font-semibold">{label} 階段</span>
                        <span className="text-xs text-muted-foreground">
                          {stage.estimated_hours} 小時
                        </span>
                      </div>
                      {stageProgress && (
                        <span className="text-sm font-medium text-muted-foreground shrink-0">
                          {stageProgress.completion_percentage}%
                        </span>
                      )}
                    </div>

                    {stage.description && (
                      <p className="text-sm text-muted-foreground mb-3">{stage.description}</p>
                    )}

                    {stage.skills?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {stage.skills.map((skill: string, i: number) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {stageProgress && (
                      <Progress
                        value={stageProgress.completion_percentage}
                        className="h-1.5 mb-3"
                      />
                    )}

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setSelectedStage(stage.order);
                        setSelectedTab('recommendations');
                      }}
                    >
                      查看推薦文章 →
                    </Button>
                  </CardContent>
                </Card>
              );
            })
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <BookOpen className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground text-sm">學習路徑生成中，請稍候...</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="space-y-4">
          {/* Stage selector */}
          {stages.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-muted-foreground">選擇階段：</span>
              {stages.map((stage: any) => (
                <Button
                  key={stage.order}
                  variant={selectedStage === stage.order ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedStage(stage.order)}
                >
                  {stageLabelMap[stage.name] ?? stage.name}
                </Button>
              ))}
            </div>
          )}

          {recLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : recommendations?.articles?.length ? (
            <div className="space-y-3">
              {recommendations.articles.map((article: any) => (
                <Card key={article.id} className="hover:shadow-sm transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-sm hover:text-primary transition-colors line-clamp-2"
                        >
                          {article.title}
                        </a>
                        <p className="text-xs text-muted-foreground mt-1">{article.reason}</p>
                        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                          {article.category && (
                            <Badge variant="outline" className="text-xs">
                              {article.category}
                            </Badge>
                          )}
                          <span>相關度 {Math.round(article.relevance_score * 100)}%</span>
                        </div>
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <Button size="icon" variant="ghost" className="h-8 w-8" asChild>
                          <a href={article.url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 text-green-600 hover:text-green-700"
                          onClick={() => completeArticleMutation.mutate({ articleId: article.id })}
                          disabled={completeArticleMutation.isPending}
                          title="標記為已讀"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Lightbulb className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground text-sm">
                  目前沒有符合此階段的推薦文章，等待更多文章被抓取後會自動出現
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Progress & Evaluation Tab */}
        <TabsContent value="progress" className="space-y-4">
          {/* Stage progress */}
          {progress ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">各階段進度</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {progress.stages.map((stage: any, i: number) => (
                    <div key={i}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium">
                          {stageLabelMap[stage.name] ?? stage.name} 階段
                        </span>
                        <span className="text-muted-foreground">
                          {stage.articles_completed}/{stage.articles_total} 篇 ·{' '}
                          {stage.completion_percentage}%
                        </span>
                      </div>
                      <Progress value={stage.completion_percentage} className="h-2" />
                    </div>
                  ))}
                </CardContent>
              </Card>

              {progress.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Lightbulb className="h-4 w-4 text-yellow-500" /> 學習建議
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {progress.recommendations.map((rec: string, i: number) => (
                        <li
                          key={i}
                          className="text-sm text-muted-foreground flex items-start gap-2"
                        >
                          <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-muted-foreground shrink-0" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <BarChart3 className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">開始學習後將顯示進度統計</p>
              </CardContent>
            </Card>
          )}

          {/* Evaluation */}
          {evaluation && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">學習成效評估</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: '時間效率', value: evaluation.efficiency_metrics.time_efficiency },
                    { label: '完成率', value: evaluation.efficiency_metrics.completion_rate },
                    { label: '知識保持', value: evaluation.efficiency_metrics.retention_score },
                    { label: '學習一致性', value: evaluation.efficiency_metrics.consistency_score },
                  ].map(({ label, value }) => (
                    <div key={label} className="text-center p-3 rounded-lg bg-muted/50">
                      <div className="text-lg font-bold">{Math.round(value * 100)}%</div>
                      <div className="text-xs text-muted-foreground">{label}</div>
                    </div>
                  ))}
                </div>

                {evaluation.strengths.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-green-600 mb-2">優勢</p>
                    <ul className="space-y-1">
                      {evaluation.strengths.map((s: string, i: number) => (
                        <li
                          key={i}
                          className="text-sm text-muted-foreground flex items-start gap-2"
                        >
                          <CheckCircle className="h-3.5 w-3.5 text-green-500 mt-0.5 shrink-0" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {evaluation.next_steps.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2">下一步</p>
                    <ul className="space-y-1">
                      {evaluation.next_steps.map((s: string, i: number) => (
                        <li
                          key={i}
                          className="text-sm text-muted-foreground flex items-start gap-2"
                        >
                          <Circle className="h-3.5 w-3.5 text-primary mt-0.5 shrink-0" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
