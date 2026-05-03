import { redirect } from 'next/navigation';

export default function AnalyticsPage(): never {
  redirect('/app/settings/analytics');
}
