'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { ChatShell } from '@/components/chat/ChatShell';

function ChatPageContent() {
  const searchParams = useSearchParams();
  const articleId = searchParams.get('articleId');
  const initialMessage = articleId ? `Tell me more about article ${articleId}` : undefined;

  return <ChatShell initialId={null} initialMessage={initialMessage} />;
}

export default function ChatNewPage() {
  return (
    <Suspense fallback={<ChatShell initialId={null} />}>
      <ChatPageContent />
    </Suspense>
  );
}
