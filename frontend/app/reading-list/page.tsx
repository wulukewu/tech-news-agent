'use client';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { EmptyState } from '@/components/EmptyState';
import { BookMarked } from 'lucide-react';

export default function ReadingListPage() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-6">Reading List</h1>
        <EmptyState
          title="Reading list coming soon"
          description="This feature will be implemented in a future update. You'll be able to save and manage your favorite articles here."
          icon={<BookMarked className="h-12 w-12" />}
        />
      </div>
    </ProtectedRoute>
  );
}
