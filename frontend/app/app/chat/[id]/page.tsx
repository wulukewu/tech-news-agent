'use client';

import { useParams } from 'next/navigation';
import { ChatShell } from '@/components/chat/ChatShell';

export default function ChatConversationPage() {
  const params = useParams();
  const id: string | null =
    typeof params?.id === 'string' ? params.id : Array.isArray(params?.id) ? params.id[0] : null;

  return <ChatShell initialId={id} />;
}
