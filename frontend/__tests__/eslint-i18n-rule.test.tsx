/**
 * Test file to verify ESLint i18n rules detect hardcoded text
 *
 * This file contains intentional violations that should be caught by ESLint.
 * Run: npm run lint to verify the rules are working.
 */

import React from 'react';

// ❌ VIOLATION: Hardcoded Chinese text in JSX
export function BadExample1() {
  return <div>這是硬編碼的中文</div>;
}

// ❌ VIOLATION: Hardcoded Chinese text in placeholder
export function BadExample2() {
  return <input placeholder="請輸入您的名字" />;
}

// ❌ VIOLATION: Hardcoded Chinese text in title
export function BadExample3() {
  return <button title="點擊這裡">Click</button>;
}

// ❌ VIOLATION: Hardcoded Chinese text in aria-label
export function BadExample4() {
  return <button aria-label="關閉對話框">X</button>;
}

// ❌ VIOLATION: Hardcoded Chinese text in alt
export function BadExample5() {
  return <img src="/image.jpg" alt="美麗的風景" />;
}

// ✅ CORRECT: Using translation keys (this should NOT trigger the rule)
export function GoodExample() {
  // Mock useI18n for demonstration
  const t = (key: string) => key;

  return (
    <div>
      <div>{t('common.welcome')}</div>
      <input placeholder={t('forms.placeholders.enter-name')} />
      <button title={t('buttons.click-here')}>Click</button>
      <button aria-label={t('buttons.close-dialog')}>X</button>
      <img src="/image.jpg" alt={t('images.beautiful-landscape')} />
    </div>
  );
}

// ✅ CORRECT: Technical terms and code should be allowed
export function TechnicalExample() {
  return (
    <div>
      <code>const API_URL = 'https://api.example.com';</code>
      <pre>npm install react</pre>
      <span>HTTP 404 Not Found</span>
    </div>
  );
}
