import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CrisisBanner } from '@/components/CrisisBanner';

beforeEach(() => {
  window.sessionStorage.clear();
});

describe('CrisisBanner', () => {
  it('renders crisis hotline numbers', () => {
    render(<CrisisBanner />);
    expect(screen.getByText(/988/)).toBeDefined();
    expect(screen.getByText(/116 123/)).toBeDefined();
  });

  it('has dismissible button', () => {
    render(<CrisisBanner />);
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    expect(dismissButton).toBeDefined();
  });

  it('dismisses when button is clicked', () => {
    render(<CrisisBanner />);
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('remembers dismissal across renders', () => {
    const { unmount } = render(<CrisisBanner />);
    fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));
    unmount();

    render(<CrisisBanner />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('has role="alert" for accessibility', () => {
    render(<CrisisBanner />);
    expect(screen.getByRole('alert')).toBeDefined();
  });
});
