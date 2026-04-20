'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
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
  Star,
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
  TechnicalDepthLevel,
  TechnicalDepthStats,
} from '@/lib/api/notifications';

interface TinkeringIndexThresholdProps {
  threshold?: number;
  onThresholdChange?: (threshold: number) => void;
  disabled?: boolean;
}

export function TinkeringIndexThreshold({
  threshold: legacyThreshold,
  onThresholdChange: legacyOnChange,
  disabled: legacyDisabled = false,
}: TinkeringIndexThresholdProps) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);

  // Fetch technical depth settings
  const {
    data: settings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['techDepthSettings'],
    queryFn: getTechnicalDepthSettings,
    staleTime: 0,
  });

  // Fetch available levels
  const { data: levels = [] } = useQuery({
    queryKey: ['techDepthLevels'],
    queryFn: getTechnicalDepthLevels,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['techDepthStats'],
    queryFn: getTechnicalDepthStats,
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000,
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: updateTechnicalDepthSettings,
    onMutate: () => {
      setIsSaving(true);
    },
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(['techDepthSettings'], updatedSettings);
      queryClient.invalidateQueries({ queryKey: ['techDepthStats'] });
      toast.success('技術深度設定已更新');

      // Call legacy callback if provided
      if (legacyOnChange && updatedSettings.threshold_numeric) {
        legacyOnChange(updatedSettings.threshold_numeric);
      }
    },
    onError: (error: any) => {
      toast.error('更新失敗，請稍後再試');
    },
    onSettled: () => {
      setIsSaving(false);
    },
  });

  const handleUpdate = (updates: Partial<TechnicalDepthSettings>) => {
    updateMutation.mutate(updates);
  };

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
            技術深度閾值
          </CardTitle>
          <CardDescription>設定接收通知的最低技術深度要求</CardDescription>
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
            技術深度閾值
          </CardTitle>
          <CardDescription>設定接收通知的最低技術深度要求</CardDescription>
        </CardHeader>
        <CardContent>
          <ErrorMessage
            message="無法載入技術深度設定"
            onRetry={() => queryClient.invalidateQueries({ queryKey: ['techDepthSettings'] })}
          />
        </CardContent>
      </Card>
    );
  }

  if (!settings) {
    return null;
  }

  const currentLevel = levels.find((level) => level.value === settings.threshold);
  const LevelIcon = currentLevel ? getLevelIcon(currentLevel.value) : Brain;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-600" />
            <div>
              <CardTitle>技術深度閾值</CardTitle>
              <CardDescription>設定接收通知的最低技術深度要求</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {settings.enabled ? (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm font-medium">已啟用</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-gray-500">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm font-medium">已停用</span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Enable/Disable Switch */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="tech-depth-enabled">啟用技術深度篩選</Label>
            <p className="text-sm text-muted-foreground">只接收符合技術深度要求的文章通知</p>
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
            {/* Threshold Selection */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="tech-depth-threshold">最低技術深度</Label>
                <Select
                  value={settings.threshold}
                  onValueChange={(threshold) => handleUpdate({ threshold })}
                  disabled={isSaving || legacyDisabled}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {levels.map((level) => {
                      const Icon = getLevelIcon(level.value);
                      const colorClass = getLevelColor(level.value);
                      return (
                        <SelectItem key={level.value} value={level.value}>
                          <div className="flex items-center gap-2">
                            <Icon className={`h-4 w-4 ${colorClass}`} />
                            <div>
                              <div className="font-medium">{level.label}</div>
                              <div className="text-xs text-muted-foreground">
                                {level.description}
                              </div>
                            </div>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>

              {/* Current Level Display */}
              {currentLevel && (
                <div className="p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <LevelIcon className={`h-6 w-6 ${getLevelColor(currentLevel.value)}`} />
                    <div>
                      <p className="font-medium">{currentLevel.label}</p>
                      <p className="text-sm text-muted-foreground">{currentLevel.description}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Statistics */}
            {stats && (
              <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg space-y-2">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    篩選效果
                  </span>
                </div>
                <p className="text-sm text-blue-700 dark:text-blue-300">{stats.message}</p>
              </div>
            )}

            {/* Level Explanations */}
            <div className="space-y-3">
              <Label>技術深度說明</Label>
              <div className="space-y-2">
                {levels.map((level) => {
                  const Icon = getLevelIcon(level.value);
                  const colorClass = getLevelColor(level.value);
                  const isSelected = level.value === settings.threshold;

                  return (
                    <div
                      key={level.value}
                      className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                        isSelected ? 'bg-primary/10 border border-primary/20' : 'hover:bg-muted/50'
                      }`}
                    >
                      <Icon className={`h-4 w-4 ${colorClass}`} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{level.label}</span>
                          {isSelected && <CheckCircle className="h-3 w-3 text-primary" />}
                        </div>
                        <p className="text-xs text-muted-foreground">{level.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {!settings.enabled && (
          <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <p className="text-sm text-muted-foreground">
              技術深度篩選已停用，您將接收所有文章的通知，不論其技術深度等級。
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
