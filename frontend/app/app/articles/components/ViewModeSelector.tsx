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
    <div className="flex items-center gap-1 border rounded-md p-1 bg-background animate-in fade-in-50 zoom-in-95 duration-300">
      {modes.map((mode, index) => (
        <Button
          key={mode.value}
          variant="ghost"
          size="sm"
          onClick={() => onChange(mode.value)}
          className={cn(
            'h-8 px-2 transition-all duration-300 hover:scale-[1.02] active:scale-95',
            'animate-in slide-in-from-top-1 duration-300',
            value === mode.value && 'bg-primary text-primary-foreground shadow-sm scale-105'
          )}
          style={{ animationDelay: `${index * 100}ms` }}
          aria-label={`${mode.label} view`}
          aria-pressed={value === mode.value}
        >
          <span
            className={cn(
              'transition-all duration-200',
              value === mode.value ? 'scale-110' : 'hover:scale-[1.05]'
            )}
          >
            {mode.icon}
          </span>
          <span className="sr-only">{mode.label}</span>
        </Button>
      ))}
    </div>
  );
}
