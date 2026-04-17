/**
 * Switch Component Examples
 *
 * This file demonstrates how to use the enhanced Switch component
 * with WCAG AA accessibility compliance.
 */

import React, { useState } from 'react';
import { Switch } from './switch';
import { Label } from './label';

export function SwitchExamples() {
  const [notifications, setNotifications] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  return (
    <div className="space-y-8 p-8">
      <section>
        <h2 className="text-2xl font-bold mb-4">Basic Switch</h2>
        <div className="flex items-center space-x-2">
          <Switch id="airplane-mode" />
          <Label htmlFor="airplane-mode">Airplane Mode</Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Controlled Switch</h2>
        <div className="flex items-center space-x-2">
          <Switch id="notifications" checked={notifications} onCheckedChange={setNotifications} />
          <Label htmlFor="notifications">
            Enable notifications (currently {notifications ? 'on' : 'off'})
          </Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Dark Mode Toggle</h2>
        <div className="flex items-center space-x-2">
          <Switch id="dark-mode" checked={darkMode} onCheckedChange={setDarkMode} />
          <Label htmlFor="dark-mode">Dark mode {darkMode ? 'enabled' : 'disabled'}</Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Disabled State</h2>
        <div className="flex items-center space-x-2">
          <Switch id="disabled-off" disabled />
          <Label htmlFor="disabled-off">Disabled (off)</Label>
        </div>
        <div className="flex items-center space-x-2 mt-2">
          <Switch id="disabled-on" disabled checked />
          <Label htmlFor="disabled-on">Disabled (on)</Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">With Description</h2>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Switch id="marketing" />
            <Label htmlFor="marketing">Marketing emails</Label>
          </div>
          <p className="text-sm text-muted-foreground ml-6">
            Receive emails about new products, features, and more
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Settings Panel Example</h2>
        <div className="space-y-4 border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="auto-save">Auto-save</Label>
              <p className="text-sm text-muted-foreground">Automatically save your work</p>
            </div>
            <Switch id="auto-save" defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="sound">Sound effects</Label>
              <p className="text-sm text-muted-foreground">Play sounds for actions</p>
            </div>
            <Switch id="sound" />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Accessibility Features</h2>
        <ul className="list-disc list-inside space-y-2 text-sm">
          <li>44x44px minimum touch target (Req 2.1)</li>
          <li>Visible 2px focus ring with primary color (Req 15.3)</li>
          <li>Keyboard navigation with Space/Enter keys (Req 15.2)</li>
          <li>Smooth 200ms animation when toggling (Req 21.1)</li>
          <li>Clear visual distinction between on/off states</li>
          <li>Disabled state with 50% opacity</li>
          <li>Proper ARIA attributes (role="switch", aria-checked)</li>
        </ul>
      </section>
    </div>
  );
}
