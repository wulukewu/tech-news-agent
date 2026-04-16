import { Metadata } from 'next';
import { DashboardLayoutClient } from './layout-client';

export const metadata: Metadata = {
  title: {
    template: '%s | Tech News Agent',
    default: 'Dashboard | Tech News Agent',
  },
  description: '技術資訊管理控制台',
};

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayoutWrapper({ children }: DashboardLayoutProps) {
  return <DashboardLayoutClient>{children}</DashboardLayoutClient>;
}
