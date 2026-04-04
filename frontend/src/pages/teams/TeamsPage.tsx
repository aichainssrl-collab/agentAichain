import React, { useState } from 'react';
import { useTeams, useCreateTeam, useDeleteTeam, useAddAgentToTeam, useRemoveAgentFromTeam } from '@/lib/hooks/useApi';
import { useAgents } from '@/lib/hooks/useApi';
import { Card, CardHeader, CardTitle, CardContent, Button, Modal, Input, Select } from '@/components/ui';
import { LoadingSpinner } from '@/components/common';
import { Plus, Edit2, Trash2, UserPlus, UserMinus } from 'lucide-react';
import type { Team, CreateTeamRequest, Agent } from '@/types';

const TeamsPage: React.FC = () => {
  const { data: teamsData, isLoading: teamsLoading } = useTeams();
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const createTeamMutation = useCreateTeam();
  const deleteTeamMutation = useDeleteTeam();
  const addAgentToTeamMutation = useAddAgentToTeam();
  const removeAgentFromTeamMutation = useRemoveAgentFromTeam();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [selectedTeamForAgents, setSelectedTeamForAgents] = useState<Team | null>(null);
  const [formData, setFormData] = useState<CreateTeamRequest>({
    name: '',
    mode: 'coordinate',
    max_iterations: 10,
  });

  const teams = teamsData?.data || [];
  const allAgents = agentsData?.data || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTeam) {
        alert('Update not implemented yet');
      } else {
        await createTeamMutation.mutateAsync(formData);
        setIsModalOpen(false);
        setFormData({ name: '', mode: 'coordinate', max_iterations: 10 });
      }
    } catch (err) {
      console.error('Failed to save team:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this team?')) {
      try {
        await deleteTeamMutation.mutateAsync(id);
      } catch (err) {
        console.error('Failed to delete team:', err);
      }
    }
  };

  const handleAddAgent = async (teamId: number, agentId: number) => {
    try {
      await addAgentToTeamMutation.mutateAsync({ teamId, agentId });
      setSelectedTeamForAgents(null);
    } catch (err) {
      console.error('Failed to add agent:', err);
    }
  };

  const handleRemoveAgent = async (teamId: number, agentId: number) => {
    try {
      await removeAgentFromTeamMutation.mutateAsync({ teamId, agentId });
    } catch (err) {
      console.error('Failed to remove agent:', err);
    }
  };

  const openTeamAgents = (team: Team) => {
    setSelectedTeamForAgents(team);
  };

  const closeTeamAgents = () => {
    setSelectedTeamForAgents(null);
  };

  const availableAgents = (team: Team) => {
    if (!team.agents) return allAgents;
    const teamAgentIds = new Set(team.agents.map((a) => a.id));
    return allAgents.filter((a) => !teamAgentIds.has(a.id));
  };

  if (teamsLoading || agentsLoading) {
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
          <h1 className="text-2xl font-bold text-gray-900">Teams</h1>
          <p className="text-gray-600 mt-1">
            Group agents into collaborative teams
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Team
        </Button>
      </div>

      {teams.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No teams created yet.</p>
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create your first team
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <Card key={team.id}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
                    <p className="text-sm text-gray-600">{team.mode}</p>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openTeamAgents(team)}
                      title="Manage Agents"
                    >
                      <UserPlus className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(team.id)}
                      isLoading={deleteTeamMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">Description:</span>{' '}
                    <span className="text-gray-700">{team.description || 'None'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Max Iterations:</span>{' '}
                    <span className="font-medium">{team.max_iterations || 'Default'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Agents:</span>{' '}
                    <span className="font-medium">{team.agent_count}</span>
                  </div>

                  {team.agents && team.agents.length > 0 && (
                    <div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {team.agents.map((agent) => (
                          <div
                            key={agent.id}
                            className="flex items-center space-x-1 px-2 py-1 bg-primary-50 text-primary-700 text-xs rounded-full"
                          >
                            <span>{agent.name}</span>
                            <button
                              onClick={() => handleRemoveAgent(team.id, agent.id)}
                              className="ml-1 hover:text-red-600"
                              title="Remove agent"
                            >
                              <UserMinus className="h-3 w-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Team Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Team"
        size="md"
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Team Name"
              placeholder="Research Squad"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />

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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mode
                </label>
                <select
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  value={formData.mode}
                  onChange={(e) => setFormData({ ...formData, mode: e.target.value })}
                >
                  <option value="coordinate">Coordinate</option>
                  <option value="collaborate">Collaborate</option>
                  <option value="sequential">Sequential</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Iterations
                </label>
                <input
                  type="number"
                  min="1"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  value={formData.max_iterations || 10}
                  onChange={(e) => setFormData({ ...formData, max_iterations: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Add Agents
              </label>
              <div className="space-y-2 max-h-40 overflow-y-auto border border-gray-300 rounded-lg p-2">
                {allAgents.map((agent) => (
                  <label key={agent.id} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      checked={formData.agent_ids?.includes(agent.id) || false}
                      onChange={(e) => {
                        const current = formData.agent_ids || [];
                        if (e.target.checked) {
                          setFormData({ ...formData, agent_ids: [...current, agent.id] });
                        } else {
                          setFormData({ ...formData, agent_ids: current.filter((id) => id !== agent.id) });
                        }
                      }}
                    />
                    <span className="text-sm text-gray-700">{agent.name} ({agent.role})</span>
                  </label>
                ))}
                {allAgents.length === 0 && (
                  <p className="text-sm text-gray-500">No agents available. Create agents first.</p>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createTeamMutation.isPending}>
              Create Team
            </Button>
          </div>
        </form>
      </Modal>

      {/* Team Agents Modal */}
      <Modal
        isOpen={!!selectedTeamForAgents}
        onClose={closeTeamAgents}
        title={`Manage Agents - ${selectedTeamForAgents?.name}`}
        size="md"
      >
        {selectedTeamForAgents && (
          <div className="space-y-4">
            <div className="max-h-60 overflow-y-auto">
              <h4 className="font-medium text-sm text-gray-700 mb-2">Team Agents</h4>
              {selectedTeamForAgents.agents && selectedTeamForAgents.agents.length > 0 ? (
                <div className="space-y-2">
                  {selectedTeamForAgents.agents.map((agent) => (
                    <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{agent.name}</p>
                        <p className="text-sm text-gray-600">{agent.role}</p>
                      </div>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleRemoveAgent(selectedTeamForAgents.id, agent.id)}
                        isLoading={removeAgentFromTeamMutation.isPending}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 py-4">No agents in this team.</p>
              )}

              <h4 className="font-medium text-sm text-gray-700 mt-6 mb-2">Available Agents</h4>
              <div className="space-y-2">
                {availableAgents(selectedTeamForAgents).length > 0 ? (
                  availableAgents(selectedTeamForAgents).map((agent) => (
                    <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{agent.name}</p>
                        <p className="text-sm text-gray-600">{agent.role}</p>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleAddAgent(selectedTeamForAgents.id, agent.id)}
                        isLoading={addAgentToTeamMutation.isPending}
                      >
                        Add
                      </Button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500 py-4">All agents are already in this team.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TeamsPage;
