import React, { useState } from 'react';
import { useAgents, useCreateAgent, useUpdateAgent, useDeleteAgent, useModels } from '@/lib/hooks/useApi';
import { Card, CardHeader, CardTitle, CardContent, Button, Modal, Input, Select } from '@/components/ui';
import { LoadingSpinner } from '@/components/common';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import type { Agent, CreateAgentRequest, UpdateAgentRequest } from '@/types';

const AgentsPage: React.FC = () => {
  const { data, isLoading } = useAgents();
  const { data: models } = useModels();
  const createAgentMutation = useCreateAgent();
  const updateAgentMutation = useUpdateAgent();
  const deleteAgentMutation = useDeleteAgent();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [formData, setFormData] = useState<CreateAgentRequest>({
    name: '',
    role: 'assistant',
    model: 'gpt-4',
  });

  const agents = data?.data || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingAgent) {
        await updateAgentMutation.mutateAsync({
          id: editingAgent.id,
          data: formData as UpdateAgentRequest
        });
      } else {
        await createAgentMutation.mutateAsync(formData);
      }
      closeModal();
    } catch (err) {
      console.error('Failed to save agent:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        await deleteAgentMutation.mutateAsync(id);
      } catch (err) {
        console.error('Failed to delete agent:', err);
      }
    }
  };

  const openEditModal = (agent: Agent) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      role: agent.role,
      model: agent.model,
      description: agent.description,
      instructions: agent.instructions,
      tools: agent.tools,
      config: agent.config,
    });
    setIsCreateModalOpen(true);
  };

  const closeModal = () => {
    setIsCreateModalOpen(false);
    setEditingAgent(null);
    setFormData({ name: '', role: 'assistant', model: 'gpt-4' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
          <p className="text-gray-600 mt-1">
            Create and manage AI agents
          </p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Agent
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : agents.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No agents created yet.</p>
            <Button onClick={() => setIsCreateModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create your first agent
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <Card key={agent.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                    <p className="text-sm text-gray-600">{agent.role}</p>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditModal(agent)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(agent.id)}
                      isLoading={deleteAgentMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">Model:</span>{' '}
                    <span className="font-medium">{agent.model}</span>
                  </div>
                  {agent.description && (
                    <div>
                      <span className="text-gray-500">Description:</span>{' '}
                      <span className="text-gray-700">{agent.description}</span>
                    </div>
                  )}
                  {agent.tools && agent.tools.length > 0 && (
                    <div>
                      <span className="text-gray-500">Tools:</span>{' '}
                      <div className="flex flex-wrap gap-1 mt-1">
                        {agent.tools.map((tool) => (
                          <span
                            key={tool}
                            className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <div>
                    <span className="text-gray-500">Status:</span>{' '}
                    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                      agent.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {agent.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={closeModal}
        title={editingAgent ? 'Edit Agent' : 'Create New Agent'}
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role *
                </label>
                <input
                  type="text"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model *
              </label>
              <select
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              >
                {models && models.length > 0 ? (
                  models.map((model) => (
                    <option key={model.id} value={model.name}>
                      {model.name} ({model.provider}){!model.is_active ? ' ⚠️ INACTIVE' : ''}
                    </option>
                  ))
                ) : (
                  <option value="">No models available</option>
                )}
              </select>
              {models && models.every(m => !m.is_active) && (
                <p className="mt-1 text-sm text-amber-600">
                  ⚠️ All models are inactive. Please activate a model in Settings before creating agents.
                </p>
              )}
              {models && models.some(m => !m.is_active) && (
                <p className="mt-1 text-xs text-gray-500">
                  ⚠️ Inactive models are shown but cannot be used. Activate models in Settings.
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                rows={2}
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Instructions
              </label>
              <textarea
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                rows={3}
                value={formData.instructions || ''}
                onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tools (comma-separated)
              </label>
              <input
                type="text"
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="search_kb, create_ticket, calculator"
                value={formData.tools?.join(', ') || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    tools: e.target.value.split(',').map((t) => t.trim()).filter(Boolean),
                  })
                }
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Configuration (JSON)
              </label>
              <textarea
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
                rows={3}
                placeholder='{"temperature": 0.7, "max_tokens": 1000}'
                value={formData.config ? JSON.stringify(formData.config, null, 2) : ''}
                onChange={(e) => {
                  try {
                    const config = e.target.value ? JSON.parse(e.target.value) : undefined;
                    setFormData({ ...formData, config });
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <Button type="button" variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={createAgentMutation.isPending || updateAgentMutation.isPending}
            >
              {editingAgent ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AgentsPage;
