'use client';

import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { ChatShell } from '@/components/chat/ChatShell';

export default function ConversationPage() {
  const params = useParams();
  const id: string | null =
    typeof params?.id === 'string' ? params.id : Array.isArray(params?.id) ? params.id[0] : null;

  return (
    <ProtectedRoute>
      <ChatShell initialId={id} />
    </ProtectedRoute>
  );
}
