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
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Sort by" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="latest">{t('sort.latest')}</SelectItem>
        <SelectItem value="popular">{t('sort.popular')}</SelectItem>
        <SelectItem value="tinkering">{t('sort.tinkering')}</SelectItem>
      </SelectContent>
    </Select>
  );
}
