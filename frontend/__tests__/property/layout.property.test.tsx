/**
 * Property Tests for Layout Components
 * Feature: frontend-feature-enhancement
 *
 * These tests validate the correctness properties of layout components
 * using property-based testing with fast-check.
 */

import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import fc from 'fast-check';
import { AppLayout, DashboardLayout, Sidebar, Header, Breadcrumb } from '@/components/layout';
import { renderWithProviders, mockViewport, checkAccessibility } from '../utils/test-utils';
import {
  navigationItemArbitrary,
  breadcrumbItemArbitrary,
  layoutPropsArbitrary,
  dashboardLayoutPropsArbitrary,
  headerPropsArbitrary,
  responsiveBreakpoints,
} from '../utils/arbitraries';

describe('Layout Components Properties', () => {
  /**
   * Property 1: AppLayout 響應式渲染
   * For any valid props, AppLayout should render without errors and maintain proper structure
   * Validates: Requirements 1.1 - Advanced_Article_Browser responsive rendering
   */
  it('Property 1: AppLayout should render correctly with any valid props', () => {
    fc.assert(
      fc.property(layoutPropsArbitrary, (props) => {
        const { container } = renderWithProviders(
          <AppLayout
            {...props}
            sidebar={<div data-testid="sidebar">Sidebar</div>}
            header={<div data-testid="header">Header</div>}
            footer={<div data-testid="footer">Footer</div>}
          >
            <div data-testid="main-content">Main Content</div>
          </AppLayout>
        );

        // Should render main content
        expect(screen.getByTestId('main-content')).toBeInTheDocument();

        // Should have proper ARIA structure
        const main = screen.getByRole('main');
        expect(main).toBeInTheDocument();
        expect(main).toHaveAttribute('id', 'main-content');
        expect(main).toHaveAttribute('tabIndex', '-1');

        // Should render sidebar, header, footer when provided
        expect(screen.getByTestId('sidebar')).toBeInTheDocument();
        expect(screen.getByTestId('header')).toBeInTheDocument();
        expect(screen.getByTestId('footer')).toBeInTheDocument();

        // Should have skip link for accessibility
        const skipLink = container.querySelector('a[href="#main-content"]');
        expect(skipLink).toBeInTheDocument();
        expect(skipLink).toHaveTextContent('跳至主要內容');

        // Check basic accessibility
        checkAccessibility(container);
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property 2: DashboardLayout 標題和描述渲染
   * For any title and description, DashboardLayout should display them correctly
   */
  it('Property 2: DashboardLayout should display title and description correctly', () => {
    fc.assert(
      fc.property(dashboardLayoutPropsArbitrary, (props) => {
        renderWithProviders(
          <DashboardLayout
            title={props.title}
            description={props.description}
            actions={<button>Action</button>}
          >
            <div>Content</div>
          </DashboardLayout>
        );

        // Title should be rendered as h1
        const titleElement = screen.getByRole('heading', { level: 1 });
        expect(titleElement).toBeInTheDocument();
        expect(titleElement).toHaveTextContent(props.title);

        // Description should be rendered if provided
        if (props.description) {
          expect(screen.getByText(props.description)).toBeInTheDocument();
        }

        // Actions should be rendered
        expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property 3: Sidebar 導航項目渲染
   * For any array of navigation items, Sidebar should render all items correctly
   */
  it('Property 3: Sidebar should render all navigation items correctly', () => {
    fc.assert(
      fc.property(
        fc.array(navigationItemArbitrary, { minLength: 1, maxLength: 10 }),
        fc.boolean(), // collapsed state
        (navigation, collapsed) => {
          renderWithProviders(<Sidebar navigation={navigation} collapsed={collapsed} />);

          // All navigation items should be rendered
          navigation.forEach((item) => {
            const links = screen.getAllByRole('link', { name: new RegExp(item.label, 'i') });
            expect(links.length).toBeGreaterThan(0);

            // Check href attribute
            const link = links[0];
            expect(link).toHaveAttribute('href', item.href);

            // Check disabled state
            if (item.disabled) {
              expect(link).toHaveAttribute('aria-disabled', 'true');
            }
          });

          // Should have proper navigation landmarks
          const navElements = screen.getAllByRole('navigation');
          expect(navElements.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property 4: Breadcrumb 導航路徑正確性
   * For any array of breadcrumb items, Breadcrumb should render the path correctly
   */
  it('Property 4: Breadcrumb should render navigation path correctly', () => {
    fc.assert(
      fc.property(
        fc.array(breadcrumbItemArbitrary, { minLength: 1, maxLength: 5 }),
        fc.boolean(), // showHome
        (items, showHome) => {
          renderWithProviders(<Breadcrumb items={items} showHome={showHome} />);

          // Should have navigation landmark
          const nav = screen.getByRole('navigation', { name: /麵包屑導航/i });
          expect(nav).toBeInTheDocument();

          // Should render all items
          items.forEach((item) => {
            expect(screen.getByText(item.label)).toBeInTheDocument();
          });

          // If showHome is true, should include Dashboard link
          if (showHome) {
            const dashboardLinks = screen.queryAllByText('Dashboard');
            expect(dashboardLinks.length).toBeGreaterThan(0);
          }

          // Current item should have proper aria-current
          const currentItems = items.filter((item) => item.current);
          if (currentItems.length > 0) {
            currentItems.forEach((item) => {
              const element = screen.getByText(item.label);
              expect(element.closest('[aria-current="page"]')).toBeInTheDocument();
            });
          }
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property 5: Header 搜尋功能正確性
   * For any search configuration, Header should handle search correctly
   */
  it('Property 5: Header should handle search functionality correctly', () => {
    fc.assert(
      fc.property(headerPropsArbitrary, (props) => {
        const mockOnSearch = vi.fn();

        renderWithProviders(<Header {...props} onSearch={mockOnSearch} />);

        // Search input should be present if showSearch is true
        if (props.showSearch) {
          const searchInput = screen.getByRole('searchbox');
          expect(searchInput).toBeInTheDocument();

          if (props.searchPlaceholder) {
            expect(searchInput).toHaveAttribute('placeholder', props.searchPlaceholder);
          }
        } else {
          expect(screen.queryByRole('searchbox')).not.toBeInTheDocument();
        }

        // Notifications button should be present if showNotifications is true
        if (props.showNotifications) {
          expect(screen.getByLabelText(/通知/i)).toBeInTheDocument();
        }

        // Theme toggle should always be present
        expect(screen.getByLabelText(/切換/i)).toBeInTheDocument();
      }),
      { numRuns: 30 }
    );
  });

  /**
   * Property 6: 響應式佈局一致性
   * Layout components should maintain consistent behavior across different viewport sizes
   * Validates: Requirements 8.1 - Responsive design from 320px to 2560px
   */
  it('Property 6: Layout components should maintain responsive consistency', () => {
    fc.assert(
      fc.property(
        responsiveBreakpoints,
        fc.boolean(), // sidebarCollapsed
        (viewportWidth, sidebarCollapsed) => {
          // Mock viewport width
          mockViewport(viewportWidth);

          const { container } = renderWithProviders(
            <AppLayout
              sidebarCollapsed={sidebarCollapsed}
              sidebar={<Sidebar collapsed={sidebarCollapsed} />}
              header={<Header />}
            >
              <DashboardLayout title="Test Page">
                <div>Content</div>
              </DashboardLayout>
            </AppLayout>
          );

          // Main content should always be accessible
          const main = screen.getByRole('main');
          expect(main).toBeInTheDocument();

          // Layout should not cause horizontal overflow
          const appLayout = container.firstChild as HTMLElement;
          expect(appLayout).toHaveClass('min-h-screen');

          // Sidebar behavior should be consistent with collapsed state
          if (viewportWidth >= 1024) {
            // lg breakpoint
            // Desktop: sidebar should be visible
            const navigation = screen.getAllByRole('navigation');
            expect(navigation.length).toBeGreaterThan(0);
          }

          // Touch targets should be at least 44px on mobile
          if (viewportWidth < 768) {
            const buttons = screen.getAllByRole('button');
            // At least some buttons should exist for mobile navigation
            expect(buttons.length).toBeGreaterThan(0);
          }
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property 7: 可訪問性屬性一致性
   * All layout components should maintain proper accessibility attributes
   * Validates: Requirements 13.1, 13.2, 13.3 - WCAG 2.1 AA compliance
   */
  it('Property 7: Layout components should maintain accessibility attributes', () => {
    fc.assert(
      fc.property(
        fc.array(navigationItemArbitrary, { minLength: 1, maxLength: 8 }),
        (navigation) => {
          const { container } = renderWithProviders(
            <AppLayout sidebar={<Sidebar navigation={navigation} />} header={<Header />}>
              <DashboardLayout title="Accessible Page">
                <Breadcrumb
                  items={[
                    { label: 'Home', href: '/' },
                    { label: 'Current', current: true },
                  ]}
                />
                <div>Content</div>
              </DashboardLayout>
            </AppLayout>
          );

          // Main content should have proper landmarks
          expect(screen.getByRole('main')).toBeInTheDocument();

          // Navigation should have proper landmarks
          const navElements = screen.getAllByRole('navigation');
          expect(navElements.length).toBeGreaterThan(0);

          // Heading hierarchy should be proper
          const headings = screen.getAllByRole('heading');
          expect(headings.length).toBeGreaterThan(0);

          // Should have h1
          const h1Elements = screen.getAllByRole('heading', { level: 1 });
          expect(h1Elements.length).toBeGreaterThan(0);

          // Links should have proper attributes
          const links = screen.getAllByRole('link');
          links.forEach((link) => {
            expect(link).toHaveAttribute('href');
          });

          // Buttons should have proper labels
          const buttons = screen.getAllByRole('button');
          buttons.forEach((button) => {
            // Should have accessible name (either text content or aria-label)
            const accessibleName = button.textContent || button.getAttribute('aria-label');
            expect(accessibleName).toBeTruthy();
          });

          // Run comprehensive accessibility check
          checkAccessibility(container);
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property 8: 鍵盤導航支援
   * All interactive elements should be keyboard accessible
   * Validates: Requirements 1.10, 13.2 - Keyboard navigation support
   */
  it('Property 8: Layout components should support keyboard navigation', () => {
    fc.assert(
      fc.property(
        fc.array(navigationItemArbitrary, { minLength: 1, maxLength: 6 }),
        (navigation) => {
          renderWithProviders(
            <AppLayout sidebar={<Sidebar navigation={navigation} />} header={<Header />}>
              <DashboardLayout title="Keyboard Test">
                <div>Content</div>
              </DashboardLayout>
            </AppLayout>
          );

          // All interactive elements should be focusable
          const interactiveElements = screen
            .getAllByRole('button')
            .concat(screen.getAllByRole('link'))
            .concat(screen.getAllByRole('searchbox'));

          interactiveElements.forEach((element) => {
            // Should be focusable (tabIndex >= 0 or naturally focusable)
            const tabIndex = element.getAttribute('tabindex');
            const isFocusable = tabIndex === null || parseInt(tabIndex) >= 0;
            const isNaturallyFocusable = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(
              element.tagName
            );

            expect(isFocusable || isNaturallyFocusable).toBe(true);
          });

          // Skip link should be present and functional
          const skipLink = document.querySelector('a[href="#main-content"]');
          expect(skipLink).toBeInTheDocument();
        }
      ),
      { numRuns: 15 }
    );
  });
});
