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
  Cpu,
  Terminal,
  Layers,
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
        return Terminal;
      case 'advanced':
        return Layers;
      case 'expert':
        return Zap;
      default:
        return BookOpen;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'basic':
        return 'text-green-500 dark:text-green-400';
      case 'intermediate':
        return 'text-blue-500 dark:text-blue-400';
      case 'advanced':
        return 'text-purple-500 dark:text-purple-400';
      case 'expert':
        return 'text-fuchsia-500 dark:text-fuchsia-400';
      default:
        return 'text-muted-foreground';
    }
  };

  const getLevelBgClasses = (level: string) => {
    switch (level) {
      case 'basic':
        return 'bg-green-50/40 border border-green-100/50 dark:bg-green-950/10 dark:border-green-900/20 text-green-900 dark:text-green-100';
      case 'intermediate':
        return 'bg-blue-50/40 border border-blue-100/50 dark:bg-blue-950/10 dark:border-blue-900/20 text-blue-900 dark:text-blue-100';
      case 'advanced':
        return 'bg-purple-50/40 border border-purple-100/50 dark:bg-purple-950/10 dark:border-purple-900/20 text-purple-900 dark:text-purple-100';
      case 'expert':
        return 'bg-fuchsia-50/40 border border-fuchsia-100/50 dark:bg-fuchsia-950/10 dark:border-fuchsia-900/20 text-fuchsia-900 dark:text-fuchsia-100';
      default:
        return 'bg-muted border border-border text-foreground';
    }
  };

  const getLevelTranslationKeys = (levelValue: string) => {
    switch (levelValue) {
      case 'basic':
        return { labelKey: 'tinkering-index.level-2', descKey: 'tinkering-index.level-2-desc' };
      case 'intermediate':
        return { labelKey: 'tinkering-index.level-3', descKey: 'tinkering-index.level-3-desc' };
      case 'advanced':
        return { labelKey: 'tinkering-index.level-4', descKey: 'tinkering-index.level-4-desc' };
      case 'expert':
        return { labelKey: 'tinkering-index.level-5', descKey: 'tinkering-index.level-5-desc' };
      default:
        return { labelKey: 'tinkering-index.level-2', descKey: 'tinkering-index.level-2-desc' };
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-purple-600 dark:text-purple-400 animate-pulse" />
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
            <Cpu className="h-5 w-5 text-purple-600 dark:text-purple-400" />
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
            <Cpu className="h-5 w-5 text-purple-600 dark:text-purple-400" />
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
                    const { labelKey, descKey } = getLevelTranslationKeys(level.value);
                    const label = t(labelKey as any);
                    const description = t(descKey as any);
                    return (
                      <SelectItem key={level.value} value={level.value}>
                        <div className="flex items-center gap-2">
                          <Icon className={`h-4 w-4 ${getLevelColor(level.value)}`} />
                          <span className="font-medium">{label}</span>
                          <span className="text-xs text-muted-foreground">{description}</span>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {currentLevel &&
              (() => {
                const { labelKey, descKey } = getLevelTranslationKeys(currentLevel.value);
                const label = t(labelKey as any);
                const description = t(descKey as any);
                return (
                  <div
                    className={`p-4 rounded-xl flex items-center gap-3 transition-all duration-300 animate-in fade-in-0 zoom-in-95 ${getLevelBgClasses(currentLevel.value)}`}
                  >
                    {(() => {
                      const Icon = getLevelIcon(currentLevel.value);
                      return (
                        <div className="p-2 rounded-lg bg-background/50 shadow-sm border border-border/20 backdrop-blur-sm">
                          <Icon
                            className={`h-6 w-6 ${getLevelColor(currentLevel.value)} animate-pulse`}
                          />
                        </div>
                      );
                    })()}
                    <div>
                      <p className="font-semibold text-sm leading-tight">{label}</p>
                      <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                        {description}
                      </p>
                    </div>
                  </div>
                );
              })()}

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
