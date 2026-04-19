/**
 * AddCustomFeedDialog Component
 *
 * Dialog for adding custom RSS feeds with URL validation
 *
 * Validates: Requirements 4.4, 4.5
 * - 4.4: THE Feed_Management_Dashboard SHALL allow users to add custom RSS feeds with URL validation
 * - 4.5: THE Feed_Management_Dashboard SHALL provide feed preview functionality before subscribing
 */

import { useState } from 'react';
import { Plus, Loader2, ExternalLink } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';

export interface FeedPreview {
  title: string;
  description?: string;
  url: string;
  category?: string;
  articleCount?: number;
  lastUpdated?: string;
}

export interface AddCustomFeedDialogProps {
  onAddFeed: (url: string, name?: string, category?: string) => Promise<void>;
  onPreviewFeed?: (url: string) => Promise<FeedPreview | null>;
}

export function AddCustomFeedDialog({ onAddFeed, onPreviewFeed }: AddCustomFeedDialogProps) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [preview, setPreview] = useState<FeedPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const { t } = useI18n();

  const validateUrl = (url: string): boolean => {
    try {
      const urlObj = new URL(url);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handlePreview = async () => {
    if (!url.trim()) {
      toast.error(t('forms.feed-dialog.url-required'));
      return;
    }

    if (!validateUrl(url)) {
      toast.error(t('forms.feed-dialog.url-invalid'));
      return;
    }

    if (!onPreviewFeed) {
      toast.info(t('forms.feed-dialog.preview-not-implemented'));
      return;
    }

    try {
      setPreviewing(true);
      const previewData = await onPreviewFeed(url);

      if (previewData) {
        setPreview(previewData);
        // Auto-fill name and category from preview
        if (!name && previewData.title) {
          setName(previewData.title);
        }
        if (!category && previewData.category) {
          setCategory(previewData.category);
        }
        toast.success(t('forms.feed-dialog.preview-success'));
      } else {
        toast.error(t('forms.feed-dialog.preview-failed'));
      }
    } catch {
      toast.error(t('forms.feed-dialog.preview-error'));
    } finally {
      setPreviewing(false);
    }
  };

  const handleAdd = async () => {
    if (!url.trim()) {
      toast.error(t('forms.feed-dialog.url-required'));
      return;
    }

    if (!validateUrl(url)) {
      toast.error(t('forms.feed-dialog.url-invalid'));
      return;
    }

    try {
      setLoading(true);
      await onAddFeed(url, name || undefined, category || undefined);
      toast.success(t('forms.feed-dialog.add-success'));

      // Reset form
      setUrl('');
      setName('');
      setCategory('');
      setPreview(null);
      setOpen(false);
    } catch {
      toast.error(t('forms.feed-dialog.add-failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setUrl('');
    setName('');
    setCategory('');
    setPreview(null);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Plus className="w-4 h-4" />
          {t('buttons.add')} {t('forms.labels.feed-name')}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t('forms.feed-dialog.title')}</DialogTitle>
          <DialogDescription>{t('forms.feed-dialog.description')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="feed-url">{t('forms.labels.feed-url')} *</Label>
            <div className="flex gap-2">
              <Input
                id="feed-url"
                placeholder={t('forms.placeholders.feed-url')}
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading || previewing}
              />
              <Button
                variant="secondary"
                onClick={handlePreview}
                disabled={!url.trim() || loading || previewing}
              >
                {previewing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {t('buttons.previewing')}
                  </>
                ) : (
                  t('buttons.preview')
                )}
              </Button>
            </div>
          </div>

          {preview && (
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{preview.title}</CardTitle>
                    {preview.description && (
                      <CardDescription className="mt-2">{preview.description}</CardDescription>
                    )}
                  </div>
                  <a
                    href={preview.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {preview.category && (
                    <Badge variant="secondary">
                      {t('forms.feed-dialog.category-label')}: {preview.category}
                    </Badge>
                  )}
                  {preview.articleCount !== undefined && (
                    <Badge variant="outline">
                      {t('forms.feed-dialog.article-count')}: {preview.articleCount}
                    </Badge>
                  )}
                  {preview.lastUpdated && (
                    <Badge variant="outline">
                      {t('forms.feed-dialog.last-updated')}: {preview.lastUpdated}
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-2">
            <Label htmlFor="feed-name">
              {t('forms.labels.feed-name')} ({t('forms.labels.optional')})
            </Label>
            <Input
              id="feed-name"
              placeholder={t('forms.placeholders.feed-name')}
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading || previewing}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="feed-category">
              {t('forms.labels.feed-category')} ({t('forms.labels.optional')})
            </Label>
            <Input
              id="feed-category"
              placeholder={t('forms.placeholders.feed-category')}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={loading || previewing}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            {t('buttons.cancel')}
          </Button>
          <Button onClick={handleAdd} disabled={!url.trim() || loading || previewing}>
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {t('forms.feed-dialog.adding')}
              </>
            ) : (
              t('forms.feed-dialog.add-feed')
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
