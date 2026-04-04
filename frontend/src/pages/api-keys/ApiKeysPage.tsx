import React, { useState } from 'react';
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '@/lib/hooks/useApi';
import { Card, CardHeader, CardTitle, CardContent, Button, Modal, Input } from '@/components/ui';
import { LoadingSpinner } from '@/components/common';
import { Plus, Copy, Trash2, Check } from 'lucide-react';
import type { ApiKey, CreateApiKeyRequest } from '@/types';

const ApiKeysPage: React.FC = () => {
  const { data: apiKeysData, isLoading, refetch } = useApiKeys();
  const createApiKeyMutation = useCreateApiKey();
  const revokeApiKeyMutation = useRevokeApiKey();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [showNewKey, setShowNewKey] = useState(false);
  const [newKey, setNewKey] = useState<ApiKey | null>(null);
  const [copied, setCopied] = useState(false);
  const [formData, setFormData] = useState<CreateApiKeyRequest>({
    name: '',
    expires_in_days: 90,
  });

  const apiKeys = apiKeysData?.data || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const createdKey = await createApiKeyMutation.mutateAsync(formData);
      setNewKey(createdKey);
      setShowNewKey(true);
      setFormData({ name: '', expires_in_days: 90 });
      setIsCreateModalOpen(false);
    } catch (err) {
      console.error('Failed to create API key:', err);
    }
  };

  const handleRevoke = async (id: number) => {
    if (window.confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      try {
        await revokeApiKeyMutation.mutateAsync(id);
      } catch (err) {
        console.error('Failed to revoke API key:', err);
      }
    }
  };

  const handleCopyKey = async (key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const closeNewKeyModal = () => {
    setShowNewKey(false);
    setNewKey(null);
    refetch();
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
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
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="text-gray-600 mt-1">
            Manage API keys for programmatic access
          </p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New API Key
        </Button>
      </div>

      {apiKeys.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No API keys created yet.</p>
            <Button onClick={() => setIsCreateModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create your first API key
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Key Prefix
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expires
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Used
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {apiKeys.map((apiKey) => (
                <tr key={apiKey.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {apiKey.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                    {apiKey.prefix}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        apiKey.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {apiKey.is_active ? 'Active' : 'Revoked'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(apiKey.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(apiKey.expires_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {apiKey.usage_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(apiKey.last_used_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {apiKey.is_active && (
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleRevoke(apiKey.id)}
                        isLoading={revokeApiKeyMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Revoke
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create API Key Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New API Key"
        size="md"
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Name"
              placeholder="Production Backend"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expires In (days)
              </label>
              <input
                type="number"
                min="1"
                max="365"
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                value={formData.expires_in_days}
                onChange={(e) =>
                  setFormData({ ...formData, expires_in_days: parseInt(e.target.value) || undefined })
                }
              />
              <p className="mt-1 text-xs text-gray-500">
                Leave empty for no expiration. Max 365 days.
              </p>
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createApiKeyMutation.isPending}>
              Create Key
            </Button>
          </div>
        </form>
      </Modal>

      {/* Show New Key Modal */}
      <Modal
        isOpen={showNewKey}
        onClose={closeNewKeyModal}
        title="API Key Created"
        size="md"
      >
        {newKey && (
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-medium text-yellow-800 mb-2">
                ⚠️ Important: Save your API key
              </h4>
              <p className="text-sm text-yellow-700 mb-3">
                This is the only time you'll see the full key. Save it securely and don't share it.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  readOnly
                  className="flex-1 block w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm"
                  value={newKey.key}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopyKey(newKey.key)}
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Prefix: {newKey.prefix}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Expires:</span>{' '}
                <span className="font-medium">{formatDate(newKey.expires_at)}</span>
              </div>
              <div>
                <span className="text-gray-600">Created:</span>{' '}
                <span className="font-medium">{formatDate(newKey.created_at)}</span>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <Button onClick={closeNewKeyModal}>Done</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ApiKeysPage;
