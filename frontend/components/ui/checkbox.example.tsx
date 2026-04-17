/**
 * Checkbox Component Examples
 *
 * This file demonstrates how to use the enhanced Checkbox component
 * with WCAG AA accessibility compliance.
 */

import React, { useState } from 'react';
import { Checkbox } from './checkbox';
import { Label } from './label';
import type { CheckedState } from '@radix-ui/react-checkbox';

export function CheckboxExamples() {
  const [checked, setChecked] = useState(false);
  const [indeterminate, setIndeterminate] = useState<CheckedState>('indeterminate');

  const handleCheckedChange = (value: CheckedState) => {
    setChecked(value === true);
  };

  return (
    <div className="space-y-8 p-8">
      <section>
        <h2 className="text-2xl font-bold mb-4">Basic Checkbox</h2>
        <div className="flex items-center space-x-2">
          <Checkbox id="terms" />
          <Label htmlFor="terms">Accept terms and conditions</Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Controlled Checkbox</h2>
        <div className="flex items-center space-x-2">
          <Checkbox id="controlled" checked={checked} onCheckedChange={handleCheckedChange} />
          <Label htmlFor="controlled">
            Controlled checkbox (currently {checked ? 'checked' : 'unchecked'})
          </Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Indeterminate State</h2>
        <div className="flex items-center space-x-2">
          <Checkbox id="indeterminate" checked={indeterminate} onCheckedChange={setIndeterminate} />
          <Label htmlFor="indeterminate">Indeterminate checkbox (select all)</Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Disabled State</h2>
        <div className="flex items-center space-x-2">
          <Checkbox id="disabled" disabled />
          <Label htmlFor="disabled">Disabled checkbox</Label>
        </div>
        <div className="flex items-center space-x-2 mt-2">
          <Checkbox id="disabled-checked" disabled checked />
          <Label htmlFor="disabled-checked">Disabled checked checkbox</Label>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">With Helper Text</h2>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox id="newsletter" />
            <Label htmlFor="newsletter">Subscribe to newsletter</Label>
          </div>
          <p className="text-sm text-muted-foreground ml-6">
            Receive weekly updates about new articles and features
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Accessibility Features</h2>
        <ul className="list-disc list-inside space-y-2 text-sm">
          <li>44x44px minimum touch target (Req 2.1)</li>
          <li>Visible 2px focus ring with primary color (Req 15.3)</li>
          <li>Keyboard navigation with Space key (Req 15.2)</li>
          <li>Smooth 200ms transitions</li>
          <li>Disabled state with 50% opacity</li>
          <li>Support for checked, unchecked, and indeterminate states</li>
        </ul>
      </section>
    </div>
  );
}
