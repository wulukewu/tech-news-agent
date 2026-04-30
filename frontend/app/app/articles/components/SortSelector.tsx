'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useI18n } from '@/contexts/I18nContext';

export type SortOption = 'latest' | 'popular' | 'tinkering';

interface SortSelectorProps {
  value: SortOption;
  onChange: (sort: SortOption) => void;
}

export function SortSelector({ value, onChange }: SortSelectorProps) {
  const { t } = useI18n();

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[140px] h-8 text-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-md focus:scale-105">
        <SelectValue placeholder="Sort by" />
      </SelectTrigger>
      <SelectContent className="animate-in slide-in-from-top-2 fade-in-0 duration-200">
        <SelectItem
          value="latest"
          className="transition-all duration-300 hover:scale-[1.02] hover:bg-accent/80 cursor-pointer"
        >
          {t('sort.latest')}
        </SelectItem>
        <SelectItem
          value="popular"
          className="transition-all duration-300 hover:scale-[1.02] hover:bg-accent/80 cursor-pointer"
        >
          {t('sort.popular')}
        </SelectItem>
        <SelectItem
          value="tinkering"
          className="transition-all duration-300 hover:scale-[1.02] hover:bg-accent/80 cursor-pointer"
        >
          {t('sort.tinkering')}
        </SelectItem>
      </SelectContent>
    </Select>
  );
}
