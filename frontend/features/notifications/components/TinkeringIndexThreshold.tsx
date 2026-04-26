'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from '@/lib/toast';
import {
  Brain,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  BarChart3,
  BookOpen,
  Zap,
  Target,
} from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';
import {
  getTechnicalDepthSettings,
  updateTechnicalDepthSettings,
  getTechnicalDepthLevels,
  getTechnicalDepthStats,
  TechnicalDepthSettings,
} from '@/lib/api/notifications';

interface TinkeringIndexThresholdProps {
  threshold?: number;
  onThresholdChange?: (threshold: number) => void;
  disabled?: boolean;
}

export function TinkeringIndexThreshold({
  onThresholdChange: legacyOnChange,
  disabled: legacyDisabled = false,
}: TinkeringIndexThresholdProps) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);

  const {
    data: settings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['techDepthSettings'],
    queryFn: getTechnicalDepthSettings,
    staleTime: 0,
  });

  const { data: levels = [] } = useQuery({
    queryKey: ['techDepthLevels'],
    queryFn: getTechnicalDepthLevels,
    staleTime: 5 * 60 * 1000,
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['techDepthStats'],
    queryFn: getTechnicalDepthStats,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const updateMutation = useMutation({
    mutationFn: updateTechnicalDepthSettings,
    onMutate: () => setIsSaving(true),
    onSuccess: (updated) => {
      queryClient.setQueryData(['techDepthSettings'], updated);
      queryClient.invalidateQueries({ queryKey: ['techDepthStats'] });
      toast.success(t('settings.notifications.depth-updated'));
      if (legacyOnChange && updated.threshold_numeric) legacyOnChange(updated.threshold_numeric);
    },
    onError: () => toast.error(t('settings.notifications.send-failed')),
    onSettled: () => setIsSaving(false),
  });

  const handleUpdate = (updates: Partial<TechnicalDepthSettings>) => updateMutation.mutate(updates);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'basic':
        return BookOpen;
      case 'intermediate':
        return Target;
      case 'advanced':
        return TrendingUp;
      case 'expert':
        return Zap;
      default:
        return Brain;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'basic':
        return 'text-green-600';
      case 'intermediate':
        return 'text-blue-600';
      case 'advanced':
        return 'text-orange-600';
      case 'expert':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            {t('settings.notifications.depth-title')}
          </CardTitle>
          <CardDescription>{t('settings.notifications.depth-desc')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            {t('settings.notifications.depth-title')}
          </CardTitle>
          <CardDescription>{t('settings.notifications.depth-desc')}</CardDescription>
        </CardHeader>
        <CardContent>
          <ErrorMessage
            message={t('settings.notifications.depth-load-error')}
            onRetry={() => queryClient.invalidateQueries({ queryKey: ['techDepthSettings'] })}
          />
        </CardContent>
      </Card>
    );
  }

  if (!settings) return null;

  const currentLevel = levels.find((l) => l.value === settings.threshold);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-600" />
            <div>
              <CardTitle>{t('settings.notifications.depth-title')}</CardTitle>
              <CardDescription>{t('settings.notifications.depth-desc')}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            {settings.enabled ? (
              <span className="text-green-600 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4" />
                {t('settings.notifications.status-active')}
              </span>
            ) : (
              <span className="text-muted-foreground flex items-center gap-1.5">
                <AlertCircle className="h-4 w-4" />
                {t('settings.notifications.status-inactive')}
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="tech-depth-enabled">{t('settings.notifications.depth-enable')}</Label>
            <p className="text-sm text-muted-foreground">
              {t('settings.notifications.depth-enable-desc')}
            </p>
          </div>
          <Switch
            id="tech-depth-enabled"
            checked={settings.enabled}
            onCheckedChange={(enabled) => handleUpdate({ enabled })}
            disabled={isSaving || legacyDisabled}
          />
        </div>

        {settings.enabled && (
          <>
            <div className="space-y-2">
              <Label htmlFor="tech-depth-threshold">
                {t('settings.notifications.depth-min-label')}
              </Label>
              <Select
                value={settings.threshold}
                onValueChange={(threshold: 'basic' | 'intermediate' | 'advanced' | 'expert') =>
                  handleUpdate({ threshold })
                }
                disabled={isSaving || legacyDisabled}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {levels.map((level) => {
                    const Icon = getLevelIcon(level.value);
                    return (
                      <SelectItem key={level.value} value={level.value}>
                        <div className="flex items-center gap-2">
                          <Icon className={`h-4 w-4 ${getLevelColor(level.value)}`} />
                          <span className="font-medium">{level.label}</span>
                          <span className="text-xs text-muted-foreground">{level.description}</span>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {currentLevel && (
              <div className="p-4 bg-muted rounded-lg flex items-center gap-3">
                {(() => {
                  const Icon = getLevelIcon(currentLevel.value);
                  return <Icon className={`h-6 w-6 ${getLevelColor(currentLevel.value)}`} />;
                })()}
                <div>
                  <p className="font-medium">{currentLevel.label}</p>
                  <p className="text-sm text-muted-foreground">{currentLevel.description}</p>
                </div>
              </div>
            )}

            {stats && (
              <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-blue-600 flex-shrink-0" />
                <p className="text-sm text-blue-700 dark:text-blue-300">{stats.message}</p>
              </div>
            )}
          </>
        )}

        {!settings.enabled && (
          <div className="p-4 bg-muted rounded-lg">
            <p className="text-sm text-muted-foreground">
              {t('settings.notifications.depth-disabled-hint')}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
