'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export type SortOption = 'latest' | 'popular' | 'tinkering';

interface SortSelectorProps {
  value: SortOption;
  onChange: (sort: SortOption) => void;
}

export function SortSelector({ value, onChange }: SortSelectorProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Sort by" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="latest">Latest</SelectItem>
        <SelectItem value="popular">Popular</SelectItem>
        <SelectItem value="tinkering">Tinkering Index</SelectItem>
      </SelectContent>
    </Select>
  );
}
