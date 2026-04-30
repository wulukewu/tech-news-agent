'use client';

import { LayoutGrid, List, Rows } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type ViewMode = 'card' | 'list' | 'compact';

interface ViewModeSelectorProps {
  value: ViewMode;
  onChange: (mode: ViewMode) => void;
}

export function ViewModeSelector({ value, onChange }: ViewModeSelectorProps) {
  const modes: { value: ViewMode; icon: React.ReactNode; label: string }[] = [
    { value: 'card', icon: <LayoutGrid className="h-4 w-4" />, label: 'Card' },
    { value: 'list', icon: <List className="h-4 w-4" />, label: 'List' },
    { value: 'compact', icon: <Rows className="h-4 w-4" />, label: 'Compact' },
  ];

  return (
    <div className="flex items-center gap-1 border rounded-md p-1 bg-background">
      {modes.map((mode) => (
        <Button
          key={mode.value}
          variant="ghost"
          size="sm"
          onClick={() => onChange(mode.value)}
          className={cn(
            'h-8 px-2 transition-all duration-200 hover:scale-105',
            value === mode.value && 'bg-primary text-primary-foreground shadow-sm'
          )}
          aria-label={`${mode.label} view`}
          aria-pressed={value === mode.value}
        >
          <span className="transition-transform duration-200 hover:scale-110">{mode.icon}</span>
          <span className="sr-only">{mode.label}</span>
        </Button>
      ))}
    </div>
  );
}
