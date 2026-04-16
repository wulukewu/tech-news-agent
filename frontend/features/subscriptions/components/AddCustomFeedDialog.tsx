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
      toast.error('請輸入 RSS Feed URL');
      return;
    }

    if (!validateUrl(url)) {
      toast.error('請輸入有效的 URL (必須以 http:// 或 https:// 開頭)');
      return;
    }

    if (!onPreviewFeed) {
      toast.info('預覽功能尚未實作');
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
        toast.success('預覽載入成功');
      } else {
        toast.error('無法載入 Feed 預覽，請檢查 URL 是否正確');
      }
    } catch (error) {
      console.error('Preview error:', error);
      toast.error('預覽失敗，請檢查 URL 是否為有效的 RSS Feed');
    } finally {
      setPreviewing(false);
    }
  };

  const handleAdd = async () => {
    if (!url.trim()) {
      toast.error('請輸入 RSS Feed URL');
      return;
    }

    if (!validateUrl(url)) {
      toast.error('請輸入有效的 URL');
      return;
    }

    try {
      setLoading(true);
      await onAddFeed(url, name || undefined, category || undefined);
      toast.success('自訂 Feed 新增成功');

      // Reset form
      setUrl('');
      setName('');
      setCategory('');
      setPreview(null);
      setOpen(false);
    } catch (error) {
      console.error('Add feed error:', error);
      toast.error('新增 Feed 失敗，請稍後再試');
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
          新增自訂 Feed
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>新增自訂 RSS Feed</DialogTitle>
          <DialogDescription>
            輸入 RSS Feed URL 以新增自訂來源。您可以先預覽 Feed 內容再決定是否新增。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="feed-url">RSS Feed URL *</Label>
            <div className="flex gap-2">
              <Input
                id="feed-url"
                placeholder="https://example.com/feed.xml"
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
                    預覽中
                  </>
                ) : (
                  '預覽'
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
                  {preview.category && <Badge variant="secondary">分類: {preview.category}</Badge>}
                  {preview.articleCount !== undefined && (
                    <Badge variant="outline">文章數: {preview.articleCount}</Badge>
                  )}
                  {preview.lastUpdated && (
                    <Badge variant="outline">最後更新: {preview.lastUpdated}</Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-2">
            <Label htmlFor="feed-name">Feed 名稱 (選填)</Label>
            <Input
              id="feed-name"
              placeholder="自動從 Feed 中取得"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading || previewing}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="feed-category">分類 (選填)</Label>
            <Input
              id="feed-category"
              placeholder="例如: Tech, AI, Web Development"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={loading || previewing}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            取消
          </Button>
          <Button onClick={handleAdd} disabled={!url.trim() || loading || previewing}>
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                新增中...
              </>
            ) : (
              '新增 Feed'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
