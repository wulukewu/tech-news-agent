'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, ThumbsUp, ThumbsDown, Meh } from 'lucide-react';
import { toast } from '@/lib/toast';
import { getReminderHistory, submitFeedback, type ReminderHistoryItem } from '@/lib/api/reminders';
import { useI18n } from '@/contexts/I18nContext';

export default function ReminderHistoryPage() {
  const { t, locale } = useI18n();

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
      toast.success(t('pages.reminders.history.feedback-saved'));
      refetch();
    } catch (error: unknown) {
      const apiErrorMsg =
        error && typeof error === 'object' && 'response' in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      toast.error(apiErrorMsg || t('pages.reminders.history.feedback-failed'));
    }
  };

  if (isLoading) {
    return (
      <div className="h-40 flex items-center justify-center text-muted-foreground">
        {t('chat.loading')}
      </div>
    );
  }

  const history = data?.history || [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{t('pages.reminders.history.title')}</h2>
        <p className="text-sm text-muted-foreground mt-1">
          {t('pages.reminders.history.description')}
        </p>
      </div>

      {history.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            {t('pages.reminders.history.empty')}
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
                      {item.trigger_type === 'add'
                        ? t('pages.reminders.history.trigger-add')
                        : t('pages.reminders.history.trigger-rate')}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {t('pages.reminders.match-percentage', {
                        percentage: Math.round(item.similarity_score * 100),
                      })}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(item.sent_at).toLocaleString(locale === 'zh-TW' ? 'zh-TW' : 'en-US')}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t('pages.reminders.history.trigger-article')}
                  </p>
                  <p className="font-medium">{item.trigger_article.title}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">
                    {t('pages.reminders.history.recommended-article')}
                  </p>
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
                        {t('pages.reminders.history.clicked')}
                      </Badge>
                    )}
                    {item.user_feedback && (
                      <Badge variant="outline">
                        {item.user_feedback === 'accurate'
                          ? t('pages.reminders.history.feedback-accurate')
                          : item.user_feedback === 'inaccurate'
                            ? t('pages.reminders.history.feedback-inaccurate')
                            : t('pages.reminders.history.feedback-uninterested')}
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
