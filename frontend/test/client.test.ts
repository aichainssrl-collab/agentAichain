import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../src/lib/api/client';

// Mock the global fetch
globalThis.fetch = vi.fn();

describe('ApiClient', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.clearToken();
  });

  it('getAgents should append query params correctly', async () => {
    const mockResponse = [{ id: 1, name: 'Test Agent' }];
    (globalThis.fetch as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    });

    const result = await apiClient.getAgents(10, 5);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/agents/?limit=10&offset=5',
      expect.objectContaining({
        method: 'GET',
      })
    );

    expect(result).toEqual({
      data: mockResponse,
      total: 1,
      limit: 10,
      offset: 5,
      has_more: false,
    });
  });

  it('getAgents should handle undefined params', async () => {
    const mockResponse = [{ id: 1, name: 'Test Agent' }];
    (globalThis.fetch as any).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    });

    const result = await apiClient.getAgents();

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/agents/',
      expect.objectContaining({
        method: 'GET',
      })
    );

    expect(result.limit).toBe(50);
    expect(result.offset).toBe(0);
  });
});
