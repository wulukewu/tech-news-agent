'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, ThumbsUp, ThumbsDown, Meh } from 'lucide-react';
import { toast } from '@/lib/toast';
import { getReminderHistory, submitFeedback, type ReminderHistoryItem } from '@/lib/api/reminders';

export default function ReminderHistoryPage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['reminder-history'],
    queryFn: () => getReminderHistory(50),
  });

  const handleFeedback = async (
    articleId: string,
    feedback: 'accurate' | 'inaccurate' | 'not_interested'
  ) => {
    try {
      await submitFeedback(articleId, feedback);
      toast.success('反饋已記錄');
      refetch();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || '提交反饋失敗');
    }
  };

  if (isLoading) {
    return (
      <div className="h-40 flex items-center justify-center text-muted-foreground">Loading...</div>
    );
  }

  const history = data?.history || [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-lg font-semibold">提醒歷史記錄</h2>
        <p className="text-sm text-muted-foreground mt-1">查看所有智能提醒記錄和反饋</p>
      </div>

      {history.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            還沒有提醒記錄。當你加入文章到閱讀清單或評高分時，系統會發送智能提醒。
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {history.map((item: ReminderHistoryItem, index) => (
            <Card key={index}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={item.trigger_type === 'add' ? 'default' : 'secondary'}>
                      {item.trigger_type === 'add' ? '加入文章' : '評分觸發'}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      相似度 {Math.round(item.similarity_score * 100)}%
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(item.sent_at).toLocaleString('zh-TW')}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">觸發文章：</p>
                  <p className="font-medium">{item.trigger_article.title}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">推薦文章：</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium flex-1">{item.recommended_article.title}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => window.open(item.recommended_article.url, '_blank')}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="flex items-center gap-2">
                    {item.clicked_at && (
                      <Badge variant="outline" className="text-green-600">
                        已點擊
                      </Badge>
                    )}
                    {item.user_feedback && (
                      <Badge variant="outline">
                        {item.user_feedback === 'accurate'
                          ? '準確'
                          : item.user_feedback === 'inaccurate'
                            ? '不準確'
                            : '不感興趣'}
                      </Badge>
                    )}
                  </div>

                  {!item.user_feedback && (
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleFeedback(item.recommended_article.url, 'accurate')}
                      >
                        <ThumbsUp className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleFeedback(item.recommended_article.url, 'inaccurate')}
                      >
                        <ThumbsDown className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          handleFeedback(item.recommended_article.url, 'not_interested')
                        }
                      >
                        <Meh className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
