import { render, screen, fireEvent } from '@/__tests__/utils/test-utils';
import { Navigation } from '@/components/Navigation';
import * as AuthHooks from '@/lib/hooks/useAuth';
import * as UserContext from '@/contexts/UserContext';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/dashboard'),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  })),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

// Mock Link component
jest.mock('next/link', () => {
  const MockLink = ({ children, href, ...props }: any) => {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
  MockLink.displayName = 'MockLink';
  return MockLink;
});

// Mock useAuth hook
jest.mock('@/lib/hooks/useAuth');

// Mock useUser hook
jest.mock('@/contexts/UserContext');

describe('Navigation', () => {
  const mockUser = {
    id: 'user-1',
    discordId: 'discord-1',
    username: 'testuser',
    avatar: 'https://cdn.discordapp.com/avatars/test.png',
  };

  const mockLogout = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (AuthHooks.useAuth as jest.Mock).mockReturnValue({
      logout: mockLogout,
      isAuthenticated: true,
      loading: false,
    });
    (UserContext.useUser as jest.Mock).mockReturnValue({
      user: mockUser,
      loading: false,
      refreshUser: jest.fn(),
    });
  });

  it('should display navigation links', () => {
    render(<Navigation />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Subscriptions')).toBeInTheDocument();
    expect(screen.getByText('Reading List')).toBeInTheDocument();
  });

  it('should highlight active page', () => {
    const { usePathname } = require('next/navigation');
    usePathname.mockReturnValue('/subscriptions');

    render(<Navigation />);

    const subscriptionsLink = screen.getByText('Subscriptions').closest('a');
    expect(subscriptionsLink).toHaveClass('bg-primary');
  });

  it('should display logout button', () => {
    render(<Navigation />);

    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('should display application name', () => {
    render(<Navigation />);

    expect(screen.getByText('Tech News Agent')).toBeInTheDocument();
  });

  it('should have mobile menu toggle on small screens', () => {
    render(<Navigation />);

    // Mobile menu button should exist (hidden on desktop)
    const menuButton = screen.getByRole('button', { name: /menu/i });
    expect(menuButton).toBeInTheDocument();
  });

  it('should toggle mobile menu when clicked', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /menu/i });

    // Click to open menu
    fireEvent.click(menuButton);

    // Mobile menu should be visible
    const mobileMenu = screen.getAllByText('Dashboard')[1]; // Second instance is in mobile menu
    expect(mobileMenu).toBeInTheDocument();
  });
});
