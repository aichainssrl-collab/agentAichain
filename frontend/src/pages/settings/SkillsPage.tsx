import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent, Button, Modal, Input } from '@/components/ui';
import { LoadingSpinner } from '@/components/common';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import type { Skill } from '@/types';

const SkillsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '', category: '', is_active: true });

  const { data: skillsData, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: async () => {
      const response = await apiClient.request<any[]>('/settings/skills', { method: 'GET' });
      return { data: response, total: response.length };
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiClient.request<any>('/settings/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      setIsModalOpen(false);
      setFormData({ name: '', description: '', category: '', is_active: true });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<typeof formData> }) =>
      apiClient.request<any>(`/settings/skills/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
      setIsModalOpen(false);
      setEditingSkill(null);
      setFormData({ name: '', description: '', category: '', is_active: true });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiClient.request(`/settings/skills/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });

  const skills = skillsData?.data || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingSkill) {
      updateMutation.mutate({ id: editingSkill.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const openEdit = (skill: Skill) => {
    setEditingSkill(skill);
    setFormData({
      name: skill.name,
      description: skill.description || '',
      category: skill.category || '',
      is_active: skill.is_active,
    });
    setIsModalOpen(true);
  };

  const openCreate = () => {
    setEditingSkill(null);
    setFormData({ name: '', description: '', category: '', is_active: true });
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
          <h1 className="text-2xl font-bold text-gray-900">Skills</h1>
          <p className="text-gray-600 mt-1">Manage available skills for agents</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          New Skill
        </Button>
      </div>

      {skills.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No skills defined yet.</p>
            <Button onClick={openCreate}>Create your first skill</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {skills.map((skill: any) => (
                <tr key={skill.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{skill.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{skill.category || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">{skill.description || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${skill.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {skill.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm flex space-x-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(skill)}>
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button variant="danger" size="sm" onClick={() => deleteMutation.mutate(skill.id)}>
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
        onClose={() => { setIsModalOpen(false); setEditingSkill(null); }}
        title={editingSkill ? 'Edit Skill' : 'Create New Skill'}
        size="md"
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Name *"
              placeholder="e.g., search_kb, calculator, translate"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            <Input
              label="Category"
              placeholder="e.g., search, calculation, document"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
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
            <Button type="button" variant="secondary" onClick={() => { setIsModalOpen(false); setEditingSkill(null); }}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending || updateMutation.isPending}>
              {editingSkill ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default SkillsPage;
