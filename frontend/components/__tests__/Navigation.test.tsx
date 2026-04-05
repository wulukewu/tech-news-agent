import { render, screen, fireEvent } from '@testing-library/react';
import { Navigation } from '../Navigation';
import { AuthProvider } from '@/contexts/AuthContext';

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
  return ({ children, href, ...props }: any) => {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

const MockAuthProvider = ({ children, user }: any) => {
  return <AuthProvider>{children}</AuthProvider>;
};

describe('Navigation', () => {
  const mockUser = {
    id: 'user-1',
    discordId: 'discord-1',
    username: 'testuser',
    avatar: 'https://cdn.discordapp.com/avatars/test.png',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display navigation links', () => {
    render(
      <MockAuthProvider user={mockUser}>
        <Navigation />
      </MockAuthProvider>,
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Subscriptions')).toBeInTheDocument();
    expect(screen.getByText('Reading List')).toBeInTheDocument();
  });

  it('should highlight active page', () => {
    const { usePathname } = require('next/navigation');
    usePathname.mockReturnValue('/subscriptions');

    render(
      <MockAuthProvider user={mockUser}>
        <Navigation />
      </MockAuthProvider>,
    );

    const subscriptionsLink = screen.getByText('Subscriptions').closest('a');
    expect(subscriptionsLink).toHaveClass('bg-primary');
  });

  it('should display logout button', () => {
    render(
      <MockAuthProvider user={mockUser}>
        <Navigation />
      </MockAuthProvider>,
    );

    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('should display application name', () => {
    render(
      <MockAuthProvider user={mockUser}>
        <Navigation />
      </MockAuthProvider>,
    );

    expect(screen.getByText('Tech News Agent')).toBeInTheDocument();
  });

  it('should have mobile menu toggle on small screens', () => {
    render(
      <MockAuthProvider user={mockUser}>
        <Navigation />
      </MockAuthProvider>,
    );

    // Mobile menu button should exist (hidden on desktop)
    const menuButton = screen.getByRole('button', { name: /menu/i });
    expect(menuButton).toBeInTheDocument();
  });

  it('should toggle mobile menu when clicked', () => {
    render(
      <MockAuthProvider user={mockUser}>
        <Navigation />
      </MockAuthProvider>,
    );

    const menuButton = screen.getByRole('button', { name: /menu/i });

    // Click to open menu
    fireEvent.click(menuButton);

    // Mobile menu should be visible
    const mobileMenu = screen.getAllByText('Dashboard')[1]; // Second instance is in mobile menu
    expect(mobileMenu).toBeInTheDocument();
  });
});
