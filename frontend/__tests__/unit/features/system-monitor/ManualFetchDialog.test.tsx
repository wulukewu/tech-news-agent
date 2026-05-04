import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ManualFetchDialog } from '@/features/system-monitor/components/ManualFetchDialog';

describe('ManualFetchDialog', () => {
  const mockOnOpenChange = vi.fn();
  const mockOnConfirm = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render dialog when open is true', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );
    expect(screen.getByText('Confirm Manual Fetch')).toBeInTheDocument();
  });

  it('should not render dialog when open is false', () => {
    render(
      <ManualFetchDialog open={false} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );
    expect(screen.queryByText('Confirm Manual Fetch')).not.toBeInTheDocument();
  });

  it('should display dialog description', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );
    expect(screen.getByText(/This operation will immediately trigger/)).toBeInTheDocument();
  });

  it('should display notice items', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );
    expect(screen.getByText('Important Notes:')).toBeInTheDocument();
  });

  it('should render cancel and confirm buttons', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm Fetch' })).toBeInTheDocument();
  });

  it('should call onOpenChange with false when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('should call onConfirm when confirm button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );
    await user.click(screen.getByRole('button', { name: 'Confirm Fetch' }));
    expect(mockOnConfirm).toHaveBeenCalledTimes(1);
  });

  it('should show loading text when isLoading is true', () => {
    render(
      <ManualFetchDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        isLoading={true}
      />
    );
    expect(screen.getByText('Fetching...')).toBeInTheDocument();
  });

  it('should disable buttons when isLoading is true', () => {
    render(
      <ManualFetchDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        isLoading={true}
      />
    );
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Fetching...' })).toBeDisabled();
  });
});
