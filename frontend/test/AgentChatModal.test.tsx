import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentChatModal } from '../src/components/agents/AgentChatModal';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock scrollIntoView for jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn();

// Mock dependencies
vi.mock('@/lib/hooks/useApi', () => ({
  useCreateAgentRun: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ run_id: 123, status: 'pending' })
  }),
  useRun: () => ({
    data: { id: 123, status: 'completed', output: 'Hello from agent' },
    refetch: vi.fn()
  })
}));

const queryClient = new QueryClient();

describe('AgentChatModal', () => {
  it('renders chat modal when open', () => {
    const agent = { id: 1, name: 'Test Agent', role: 'assistant', model: 'gpt-4', is_active: true };
    
    render(
      <QueryClientProvider client={queryClient}>
        <AgentChatModal agent={agent as any} isOpen={true} onClose={() => {}} />
      </QueryClientProvider>
    );
    
    expect(screen.getByText('Chat: Test Agent')).toBeTruthy();
    expect(screen.getByText(/Chat started with Test Agent/i)).toBeTruthy();
  });

  it('sends message when typing and clicking send', async () => {
    const agent = { id: 1, name: 'Test Agent', role: 'assistant', model: 'gpt-4', is_active: true };
    
    render(
      <QueryClientProvider client={queryClient}>
        <AgentChatModal agent={agent as any} isOpen={true} onClose={() => {}} />
      </QueryClientProvider>
    );
    
    const input = screen.getByPlaceholderText(/Type your message/i);
    fireEvent.change(input, { target: { value: 'Hello agent' } });
    
    // The button might be disabled if input is empty, but we typed something.
    // However, finding the button could be tricky if there are multiple. 
    // Let's find it by role and ensure it's the right one.
    const sendButton = screen.getAllByRole('button')[1]; // second button, first is close
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Hello agent')).toBeTruthy();
    });
  });
});
