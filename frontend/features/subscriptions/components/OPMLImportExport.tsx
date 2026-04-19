/**
 * OPMLImportExport Component
 *
 * Provides UI for importing and exporting feed subscriptions in OPML format
 *
 * Validates: Requirements 4.9
 * - THE Feed_Management_Dashboard SHALL support importing/exporting OPML files for feed management
 */

import { useState, useRef } from 'react';
import { Download, Upload, Loader2, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useI18n } from '@/contexts/I18nContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/lib/toast';
import {
  exportToOPML,
  parseOPML,
  downloadOPML,
  readOPMLFile,
  validateOPML,
  type OPMLOutline,
} from '../utils/opml';
import type { Feed } from '@/types/feed';

export interface OPMLImportExportProps {
  feeds: Feed[];
  onImport: (feeds: OPMLOutline[]) => Promise<void>;
  className?: string;
}

export function OPMLImportExport({ feeds, onImport, className = '' }: OPMLImportExportProps) {
  const { t } = useI18n();
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const [parsedFeeds, setParsedFeeds] = useState<OPMLOutline[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = () => {
    try {
      const subscribedFeeds = feeds.filter((f) => f.is_subscribed);

      if (subscribedFeeds.length === 0) {
        toast.info(t('errors.opml-no-feeds'));
        return;
      }

      const opmlContent = exportToOPML(subscribedFeeds);
      const filename = `tech-news-subscriptions-${new Date().toISOString().split('T')[0]}.opml`;
      downloadOPML(opmlContent, filename);

      toast.success(t('success.opml-exported', { count: subscribedFeeds.length }));
    } catch (error) {
      console.error('Export error:', error);
      toast.error(t('errors.opml-export-failed'));
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setImporting(true);

      // Read file content
      const content = await readOPMLFile(file);

      // Validate OPML
      const validation = validateOPML(content);
      if (!validation.valid) {
        toast.error(t('errors.opml-invalid', { error: validation.error || 'Unknown error' }));
        return;
      }

      // Parse OPML
      const parsed = parseOPML(content);

      if (parsed.length === 0) {
        toast.error(t('errors.opml-no-feeds'));
        return;
      }

      setParsedFeeds(parsed);
      setImportDialogOpen(true);
      toast.success(t('success.opml-parsed', { count: parsed.length }));
    } catch (error) {
      console.error('Import error:', error);
      toast.error(t('errors.opml-read-failed'));
    } finally {
      setImporting(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleImportConfirm = async () => {
    try {
      setImporting(true);
      await onImport(parsedFeeds);
      toast.success(t('success.opml-imported', { count: parsedFeeds.length }));
      setImportDialogOpen(false);
      setParsedFeeds([]);
    } catch (error) {
      console.error('Import confirm error:', error);
      toast.error(t('errors.opml-import-failed'));
    } finally {
      setImporting(false);
    }
  };

  const handleImportCancel = () => {
    setImportDialogOpen(false);
    setParsedFeeds([]);
  };

  return (
    <>
      <div className={`flex gap-2 ${className}`}>
        <Button variant="outline" onClick={handleExport} className="gap-2">
          <Download className="w-4 h-4" />
          {t('buttons.export-opml')}
        </Button>

        <Button
          variant="outline"
          onClick={() => fileInputRef.current?.click()}
          disabled={importing}
          className="gap-2"
        >
          {importing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('buttons.importing')}
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              {t('buttons.import-opml')}
            </>
          )}
        </Button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".opml,.xml"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>{t('dialogs.opml-import.title')}</DialogTitle>
            <DialogDescription>
              {t('dialogs.opml-import.description', { count: parsedFeeds.length })}
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto py-4">
            <div className="space-y-3">
              {parsedFeeds.map((feed, index) => (
                <Card key={index} className="border-muted">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base truncate">{feed.text}</CardTitle>
                        {feed.category && (
                          <Badge variant="secondary" className="mt-1">
                            {feed.category}
                          </Badge>
                        )}
                      </div>
                      <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <CardDescription className="text-xs break-all">{feed.xmlUrl}</CardDescription>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleImportCancel} disabled={importing}>
              {t('buttons.cancel')}
            </Button>
            <Button onClick={handleImportConfirm} disabled={importing}>
              {importing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t('buttons.importing')}
                </>
              ) : (
                t('dialogs.opml-import.confirm-button', { count: parsedFeeds.length })
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
