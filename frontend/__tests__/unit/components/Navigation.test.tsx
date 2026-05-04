import { renderWithProviders as render } from '@/__tests__/utils/test-utils';
import { fireEvent, screen } from '@testing-library/react';
import { Navigation } from '@/components/Navigation';
import { vi, describe, it, expect, beforeEach } from 'vitest';

const mockUsePathname = vi.fn(() => '/app/articles');
vi.mock('next/navigation', () => ({
  usePathname: () => mockUsePathname(),
  useRouter: vi.fn(() => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() })),
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

vi.mock('next/link', () => {
  const MockLink = ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
  MockLink.displayName = 'MockLink';
  return { default: MockLink };
});

const mockLogout = vi.fn();
vi.mock('@/lib/hooks/useAuth', () => ({
  useAuth: () => ({
    logout: mockLogout,
    isAuthenticated: true,
    loading: false,
    login: vi.fn(),
    checkAuth: vi.fn(),
  }),
}));

describe('Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue('/app/articles');
    document.body.style.overflow = '';
  });

  it('should display navigation links', () => {
    render(<Navigation />);
    expect(screen.getByText('Articles')).toBeInTheDocument();
    expect(screen.getByText('Reading')).toBeInTheDocument();
    expect(screen.getByText('Feeds')).toBeInTheDocument();
  });

  it('should display application name', () => {
    render(<Navigation />);
    expect(screen.getByText('Tech News Agent')).toBeInTheDocument();
  });

  it('should have mobile menu toggle', () => {
    render(<Navigation />);
    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });
    expect(menuButton).toBeInTheDocument();
  });

  it('should toggle mobile drawer when hamburger button is clicked', () => {
    render(<Navigation />);
    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });
    expect(screen.queryByLabelText('Mobile navigation')).not.toBeInTheDocument();
    fireEvent.click(menuButton);
    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();
  });

  it('should close drawer when close button is clicked', () => {
    render(<Navigation />);
    fireEvent.click(screen.getByRole('button', { name: /toggle navigation menu/i }));
    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /close navigation menu/i }));
    expect(screen.queryByLabelText('Mobile navigation')).not.toBeInTheDocument();
  });

  it('should prevent body scrolling when drawer is open', () => {
    render(<Navigation />);
    expect(document.body.style.overflow).toBe('');
    fireEvent.click(screen.getByRole('button', { name: /toggle navigation menu/i }));
    expect(document.body.style.overflow).toBe('hidden');
    fireEvent.click(screen.getByRole('button', { name: /close navigation menu/i }));
    expect(document.body.style.overflow).toBe('');
  });

  it('should display logout button', async () => {
    render(<Navigation />);
    // Logout is in the mobile drawer
    fireEvent.click(screen.getByRole('button', { name: /toggle navigation menu/i }));
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });
});
