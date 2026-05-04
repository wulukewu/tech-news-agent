'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { ChatShell } from '@/components/chat/ChatShell';

function ChatPageContent() {
  const searchParams = useSearchParams();
  const articleTitle = searchParams.get('articleTitle');
  const articleId = searchParams.get('articleId');

  let initialMessage: string | undefined;
  if (articleTitle) {
    initialMessage = `幫我深入分析這篇文章：${articleTitle}`;
  } else if (articleId) {
    initialMessage = `Tell me more about article ${articleId}`;
  }

  return <ChatShell initialId={null} initialMessage={initialMessage} />;
}

export default function ChatNewPage() {
  return (
    <Suspense fallback={<ChatShell initialId={null} />}>
      <ChatPageContent />
    </Suspense>
  );
}
