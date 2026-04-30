'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import LandingPage from '../page';

export default function AppPage() {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (pathname === '/app') {
      router.replace('/app/articles');
    }
  }, [router, pathname]);

  // When Next.js incorrectly renders this as the root page in Docker,
  // show the landing page instead
  if (pathname === '/' || pathname === null) {
    return <LandingPage />;
  }

  return null;
}
