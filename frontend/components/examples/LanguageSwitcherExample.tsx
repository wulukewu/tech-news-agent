/**
 * LanguageSwitcher Example
 *
 * Demonstrates the LanguageSwitcher component with different layouts and contexts.
 * This file serves as both documentation and visual testing for the component.
 *
 * Task 2.1: Create LanguageSwitcher component with accessibility
 * Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 9.1, 9.2, 9.3, 9.4, 9.6
 */

'use client';

import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { useI18n } from '@/contexts/I18nContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

export function LanguageSwitcherExample() {
  const { locale, t } = useI18n();

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Language Switcher Demo</h1>
        <p className="text-muted-foreground">
          Demonstration of the bilingual UI system with language switching
        </p>
      </div>

      {/* Basic Usage */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Basic Usage</h2>

        <Card>
          <CardHeader>
            <CardTitle>Language Switcher Component</CardTitle>
            <CardDescription>
              Click to switch between Traditional Chinese (繁體中文) and English
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <LanguageSwitcher />
          </CardContent>
        </Card>
      </section>

      {/* Current State */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Current State</h2>

        <Card>
          <CardHeader>
            <CardTitle>Active Language</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p>
                <strong>Current Locale:</strong>{' '}
                <code className="px-2 py-1 bg-muted rounded">{locale}</code>
              </p>
              <p>
                <strong>HTML Lang Attribute:</strong>{' '}
                <code className="px-2 py-1 bg-muted rounded">{document.documentElement.lang}</code>
              </p>
              <p>
                <strong>LocalStorage Value:</strong>{' '}
                <code className="px-2 py-1 bg-muted rounded">
                  {localStorage.getItem('language') || 'not set'}
                </code>
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Translation Examples */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Translation Examples</h2>

        <Card>
          <CardHeader>
            <CardTitle>Navigation Labels</CardTitle>
            <CardDescription>These labels change based on the selected language</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Translation Key</p>
                <code className="text-xs">nav.articles</code>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Translated Value</p>
                <p className="font-medium">{t('nav.articles')}</p>
              </div>

              <div>
                <code className="text-xs">nav.reading-list</code>
              </div>
              <div>
                <p className="font-medium">{t('nav.reading-list')}</p>
              </div>

              <div>
                <code className="text-xs">nav.subscriptions</code>
              </div>
              <div>
                <p className="font-medium">{t('nav.subscriptions')}</p>
              </div>

              <div>
                <code className="text-xs">nav.analytics</code>
              </div>
              <div>
                <p className="font-medium">{t('nav.analytics')}</p>
              </div>

              <div>
                <code className="text-xs">nav.settings</code>
              </div>
              <div>
                <p className="font-medium">{t('nav.settings')}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Button Labels</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md">
                {t('buttons.save')}
              </button>
              <button className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md">
                {t('buttons.cancel')}
              </button>
              <button className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md">
                {t('buttons.delete')}
              </button>
              <button className="px-4 py-2 bg-muted text-muted-foreground rounded-md">
                {t('buttons.edit')}
              </button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Messages with Interpolation</CardTitle>
            <CardDescription>Dynamic values can be inserted into translations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p>{t('messages.article-count', { count: 5 })}</p>
              <p>{t('messages.article-count', { count: 42 })}</p>
              <p>{t('messages.loading')}</p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Accessibility Features */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Accessibility Features</h2>

        <Card>
          <CardHeader>
            <CardTitle>WCAG AA Compliance</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 list-disc list-inside">
              <li>
                <strong>Keyboard Navigation:</strong> Use Tab to focus, Enter or Space to activate
              </li>
              <li>
                <strong>ARIA Attributes:</strong> role="group", aria-label, aria-pressed
              </li>
              <li>
                <strong>Focus Indicators:</strong> 2px blue ring on focus (focus:ring-2)
              </li>
              <li>
                <strong>Touch Target Size:</strong> Minimum 44x44px (min-w-[44px] min-h-[44px])
              </li>
              <li>
                <strong>Visual Feedback:</strong> Active language highlighted with background
              </li>
              <li>
                <strong>Smooth Transitions:</strong> 200ms color transitions
              </li>
              <li>
                <strong>Screen Reader Support:</strong> Announces language changes
              </li>
              <li>
                <strong>HTML Lang Attribute:</strong> Updates document.documentElement.lang
              </li>
            </ul>
          </CardContent>
        </Card>
      </section>

      {/* Integration Examples */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Integration Examples</h2>

        <Card>
          <CardHeader>
            <CardTitle>In Navigation Bar</CardTitle>
            <CardDescription>Typical placement in the application navigation</CardDescription>
          </CardHeader>
          <CardContent>
            <nav className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-4">
                <span className="font-bold">Tech News Agent</span>
                <div className="flex gap-2">
                  <a href="#" className="text-sm hover:underline">
                    {t('nav.articles')}
                  </a>
                  <a href="#" className="text-sm hover:underline">
                    {t('nav.reading-list')}
                  </a>
                  <a href="#" className="text-sm hover:underline">
                    {t('nav.subscriptions')}
                  </a>
                </div>
              </div>
              <LanguageSwitcher />
            </nav>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>In Settings Panel</CardTitle>
            <CardDescription>
              Alternative placement in a settings or preferences area
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Language Preference</p>
                  <p className="text-sm text-muted-foreground">
                    Choose your preferred interface language
                  </p>
                </div>
                <LanguageSwitcher />
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
