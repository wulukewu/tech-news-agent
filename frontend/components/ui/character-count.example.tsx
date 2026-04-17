/**
 * CharacterCount Component Examples
 *
 * This file demonstrates various use cases for the CharacterCount component
 * Requirements Coverage: 11.4
 */

import React, { useState } from 'react';
import { CharacterCount } from './character-count';
import { FormInput } from './form-input';
import { Label } from './label';

export function CharacterCountExamples() {
  const [message, setMessage] = useState('');
  const [bio, setBio] = useState('');
  const [title, setTitle] = useState('');

  return (
    <div className="space-y-8 p-8">
      <h1 className="text-2xl font-bold">CharacterCount Component Examples</h1>

      {/* Example 1: Standalone CharacterCount */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">1. Standalone CharacterCount</h2>
        <div className="space-y-2">
          <Label htmlFor="standalone-input">Message</Label>
          <input
            id="standalone-input"
            type="text"
            maxLength={100}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            placeholder="Type your message..."
          />
          <CharacterCount current={message.length} max={100} />
        </div>
      </section>

      {/* Example 2: CharacterCount without label */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">2. CharacterCount without "characters" label</h2>
        <div className="space-y-2">
          <Label htmlFor="no-label-input">Bio</Label>
          <textarea
            id="no-label-input"
            maxLength={500}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            placeholder="Tell us about yourself..."
            rows={4}
          />
          <CharacterCount current={bio.length} max={500} showLabel={false} />
        </div>
      </section>

      {/* Example 3: Integrated with FormInput */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">3. Integrated with FormInput</h2>
        <FormInput
          id="integrated-input"
          label="Article Title"
          maxLength={100}
          showCharacterCount
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter article title..."
          helperText="Keep it concise and descriptive"
        />
      </section>

      {/* Example 4: Different States */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">4. Different Color States</h2>
        <div className="space-y-4">
          <div>
            <p className="mb-2 text-sm font-medium">Default (below 80%)</p>
            <CharacterCount current={50} max={100} />
          </div>
          <div>
            <p className="mb-2 text-sm font-medium">Warning (80-99%)</p>
            <CharacterCount current={85} max={100} />
          </div>
          <div>
            <p className="mb-2 text-sm font-medium">Error (at or over limit)</p>
            <CharacterCount current={100} max={100} />
          </div>
          <div>
            <p className="mb-2 text-sm font-medium">Over limit</p>
            <CharacterCount current={105} max={100} />
          </div>
        </div>
      </section>

      {/* Example 5: Custom Warning Threshold */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">5. Custom Warning Threshold (90%)</h2>
        <div className="space-y-2">
          <CharacterCount current={85} max={100} warningThreshold={0.9} />
          <p className="text-sm text-muted-foreground">
            85/100 is still in default state with 90% threshold
          </p>
        </div>
        <div className="space-y-2">
          <CharacterCount current={90} max={100} warningThreshold={0.9} />
          <p className="text-sm text-muted-foreground">
            90/100 triggers warning with 90% threshold
          </p>
        </div>
      </section>

      {/* Example 6: Small Limits */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">6. Small Character Limits</h2>
        <FormInput
          id="small-limit-input"
          label="Short Code"
          maxLength={10}
          showCharacterCount
          placeholder="Max 10 chars"
        />
      </section>

      {/* Example 7: With Error State */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">7. With Error Message</h2>
        <FormInput
          id="error-input"
          label="Username"
          maxLength={20}
          showCharacterCount
          error="Username is already taken"
          defaultValue="existinguser"
        />
      </section>

      {/* Example 8: Disabled State */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">8. Disabled State</h2>
        <FormInput
          id="disabled-input"
          label="Read-only Field"
          maxLength={50}
          showCharacterCount
          disabled
          defaultValue="This field is disabled"
        />
      </section>

      {/* Example 9: Real-world Use Case - Comment Form */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">9. Real-world Example: Comment Form</h2>
        <div className="rounded-lg border p-4">
          <FormInput
            id="comment-input"
            label="Add a comment"
            maxLength={280}
            showCharacterCount
            placeholder="Share your thoughts..."
            helperText="Be respectful and constructive"
          />
          <div className="mt-4 flex justify-end gap-2">
            <button className="rounded-md border px-4 py-2 text-sm">Cancel</button>
            <button className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">
              Post Comment
            </button>
          </div>
        </div>
      </section>

      {/* Example 10: Multiple Inputs */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">10. Form with Multiple Character Limits</h2>
        <div className="space-y-4 rounded-lg border p-4">
          <FormInput
            id="form-title"
            label="Title"
            maxLength={100}
            showCharacterCount
            placeholder="Enter title..."
          />
          <FormInput
            id="form-subtitle"
            label="Subtitle"
            maxLength={150}
            showCharacterCount
            placeholder="Enter subtitle..."
          />
          <div className="space-y-2">
            <Label htmlFor="form-description">Description</Label>
            <textarea
              id="form-description"
              maxLength={500}
              className="w-full rounded-md border border-input bg-background px-3 py-2"
              placeholder="Enter description..."
              rows={4}
            />
            <CharacterCount current={0} max={500} />
          </div>
        </div>
      </section>
    </div>
  );
}

export default CharacterCountExamples;
