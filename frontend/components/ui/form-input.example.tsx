/**
 * FormInput Component Examples
 *
 * This file demonstrates various use cases of the FormInput component
 * following the design system requirements (Req 11.1-11.8)
 */

import React from 'react';
import { FormInput } from './form-input';

export function FormInputExamples() {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [emailError, setEmailError] = React.useState('');

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    // Simple email validation
    if (e.target.value && !e.target.value.includes('@')) {
      setEmailError('Please enter a valid email address');
    } else {
      setEmailError('');
    }
  };

  return (
    <div className="space-y-8 p-8 max-w-2xl">
      <h1 className="text-2xl font-bold">FormInput Component Examples</h1>

      {/* Example 1: Basic Input with Label */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Basic Input with Label</h2>
        <FormInput id="basic-input" label="Full Name" placeholder="Enter your full name" />
      </section>

      {/* Example 2: Input with Helper Text */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Input with Helper Text</h2>
        <FormInput
          id="username-input"
          label="Username"
          placeholder="Choose a username"
          helperText="Username must be 3-20 characters long"
        />
      </section>

      {/* Example 3: Input with Error State */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Input with Error State</h2>
        <FormInput
          id="email-input"
          label="Email Address"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={handleEmailChange}
          error={emailError}
        />
      </section>

      {/* Example 4: Disabled Input */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Disabled Input</h2>
        <FormInput
          id="disabled-input"
          label="Account Status"
          value="Active"
          disabled
          helperText="This field cannot be edited"
        />
      </section>

      {/* Example 5: Password Input */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Password Input</h2>
        <FormInput
          id="password-input"
          label="Password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          helperText="Must be at least 8 characters"
        />
      </section>

      {/* Example 6: Number Input */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Number Input</h2>
        <FormInput
          id="age-input"
          label="Age"
          type="number"
          placeholder="Enter your age"
          min={18}
          max={120}
        />
      </section>

      {/* Example 7: Required Input */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Required Input</h2>
        <FormInput
          id="required-input"
          label="Company Name"
          placeholder="Enter company name"
          required
          helperText="This field is required"
        />
      </section>

      {/* Example 8: Input with Custom Styling */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Input with Custom Styling</h2>
        <FormInput
          id="custom-input"
          label="Custom Styled Input"
          placeholder="Custom styling example"
          className="border-2 border-primary"
          containerClassName="max-w-md"
        />
      </section>

      {/* Example 9: Mobile Responsive Demo */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Mobile Responsive</h2>
        <p className="text-sm text-muted-foreground">
          Resize your browser to see responsive behavior:
          <br />
          - Full-width on mobile (&lt; 768px)
          <br />
          - Auto-width on desktop (&gt;= 768px)
          <br />
          - 48px min height on mobile
          <br />- 40px min height on desktop
        </p>
        <FormInput
          id="responsive-input"
          label="Responsive Input"
          placeholder="Try resizing the window"
        />
      </section>

      {/* Example 10: Form Example */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Complete Form Example</h2>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            alert('Form submitted!');
          }}
        >
          <FormInput id="form-name" label="Full Name" placeholder="John Doe" required />
          <FormInput
            id="form-email"
            label="Email"
            type="email"
            placeholder="john@example.com"
            required
            helperText="We'll never share your email"
          />
          <FormInput
            id="form-phone"
            label="Phone Number"
            type="tel"
            placeholder="+1 (555) 000-0000"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
          >
            Submit Form
          </button>
        </form>
      </section>
    </div>
  );
}

export default FormInputExamples;
