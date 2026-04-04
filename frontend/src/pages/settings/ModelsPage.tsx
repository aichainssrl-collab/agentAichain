import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent, Button, Modal, Input, Textarea } from '@/components/ui';
import { LoadingSpinner } from '@/components/common';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import type { AIModel } from '@/types';

const ModelsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<AIModel | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    provider: '',
    base_url: '',
    api_key: '',
    max_tokens: undefined as number | undefined,
    max_context: undefined as number | undefined,
    cost_per_1k_input: undefined as number | undefined,
    cost_per_1k_output: undefined as number | undefined,
    config: '',
    is_active: true,
  });

  const { data: modelsData, isLoading } = useQuery({
    queryKey: ['aimodels'],
    queryFn: async () => {
      const response = await apiClient.request<any[]>('/settings/models', { method: 'GET' });
      return { data: response, total: response.length };
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiClient.request<any>('/settings/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aimodels'] });
      setIsModalOpen(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<typeof formData> }) =>
      apiClient.request<any>(`/settings/models/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aimodels'] });
      setIsModalOpen(false);
      setEditingModel(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiClient.request(`/settings/models/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aimodels'] });
    },
  });

  const models = modelsData?.data || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingModel) {
      updateMutation.mutate({ id: editingModel.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const openEdit = (model: AIModel) => {
    setEditingModel(model);
    setFormData({
      name: model.name,
      provider: model.provider,
      base_url: model.base_url || '',
      api_key: model.api_key || '',
      max_tokens: model.max_tokens,
      max_context: model.max_context,
      cost_per_1k_input: model.cost_per_1k_input,
      cost_per_1k_output: model.cost_per_1k_output,
      config: model.config || '',
      is_active: model.is_active,
    });
    setIsModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      provider: '',
      base_url: '',
      api_key: '',
      max_tokens: undefined,
      max_context: undefined,
      cost_per_1k_input: undefined,
      cost_per_1k_output: undefined,
      config: '',
      is_active: true,
    });
    setEditingModel(null);
  };

  const openCreate = () => {
    resetForm();
    setIsModalOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Models</h1>
          <p className="text-gray-600 mt-1">Configure available AI models including custom providers like Ollama, OpenRouter, etc.</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          New Model
        </Button>
      </div>

      {models.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No models defined yet.</p>
            <Button onClick={openCreate}>Create your first model</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Base URL</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Max Tokens</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {models.map((model: any) => (
                <tr key={model.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{model.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 capitalize">{model.provider}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 truncate max-w-xs">{model.base_url || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{model.max_tokens || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${model.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {model.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm flex space-x-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(model)}>
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button variant="danger" size="sm" onClick={() => deleteMutation.mutate(model.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingModel(null); }}
        title={editingModel ? 'Edit AI Model' : 'Create New AI Model'}
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Name *"
                placeholder="e.g., gpt-4, claude-3-opus, llama2"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
              <Input
                label="Provider *"
                placeholder="e.g., openai, anthropic, ollama, openrouter, custom"
                value={formData.provider}
                onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                required
              />
            </div>

            <Input
              label="Base URL"
              placeholder="e.g., http://localhost:11434 (for Ollama) or https://openrouter.ai/api/v1"
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
            />

            <Input
              label="API Key"
              placeholder="Optional: API key for provider (OpenRouter, custom endpoints)"
              type="password"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Max Tokens"
                type="number"
                placeholder="e.g., 4096"
                value={formData.max_tokens || ''}
                onChange={(e) => setFormData({ ...formData, max_tokens: e.target.value ? Number(e.target.value) : undefined })}
              />
              <Input
                label="Context Window"
                type="number"
                placeholder="e.g., 8192"
                value={formData.max_context || ''}
                onChange={(e) => setFormData({ ...formData, max_context: e.target.value ? Number(e.target.value) : undefined })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Cost per 1K input ($)"
                type="number"
                step="0.0001"
                placeholder="0.001"
                value={formData.cost_per_1k_input || ''}
                onChange={(e) => setFormData({ ...formData, cost_per_1k_input: e.target.value ? Number(e.target.value) : undefined })}
              />
              <Input
                label="Cost per 1K output ($)"
                type="number"
                step="0.0001"
                placeholder="0.002"
                value={formData.cost_per_1k_output || ''}
                onChange={(e) => setFormData({ ...formData, cost_per_1k_output: e.target.value ? Number(e.target.value) : undefined })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Additional Config (JSON)</label>
              <Textarea
                placeholder='{"temperature": 0.7, "top_p": 0.9}'
                value={formData.config}
                onChange={(e) => setFormData({ ...formData, config: e.target.value })}
                rows={3}
              />
              <p className="mt-1 text-xs text-gray-500">Optional JSON configuration for model-specific parameters</p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">Active</label>
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <Button type="button" variant="secondary" onClick={() => { setIsModalOpen(false); setEditingModel(null); }}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending || updateMutation.isPending}>
              {editingModel ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ModelsPage;
