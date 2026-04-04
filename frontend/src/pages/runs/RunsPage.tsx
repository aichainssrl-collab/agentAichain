import React, { useState } from 'react';
import { useRuns, useRun } from '@/lib/hooks/useApi';
import { useAgents } from '@/lib/hooks/useApi';
import { useTeams } from '@/lib/hooks/useApi';
import { Card, CardHeader, CardTitle, CardContent, Button, Modal, Input, Select, Textarea } from '@/components/ui';
import { LoadingSpinner, StatusBadge } from '@/components/common';
import { Play, Eye } from 'lucide-react';
import type { Run, RunStatus, CreateAgentRunRequest, CreateTeamRunRequest, Agent, Team } from '@/types';

const RunsPage: React.FC = () => {
  const { data: runsData, isLoading: runsLoading, refetch } = useRuns(50);
  const { data: agentsData } = useAgents();
  const { data: teamsData } = useTeams();
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);

  const [filterStatus, setFilterStatus] = useState<RunStatus | ''>('');
  const [isExecuteModalOpen, setIsExecuteModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [executeType, setExecuteType] = useState<'agent' | 'team'>('agent');
  const [selectedId, setSelectedId] = useState<number>(0);
  const [runInput, setRunInput] = useState<Record<string, any>>({ task: '' });

  const runs = runsData?.data || [];
  const agents = agentsData?.data || [];
  const teams = teamsData?.data || [];

  const filteredRuns = filterStatus
    ? runs.filter((run) => run.status === filterStatus)
    : runs;

  const handleOpenExecute = (type: 'agent' | 'team', id: number) => {
    setExecuteType(type);
    setSelectedId(id);
    setRunInput({ task: '' });
    setIsExecuteModalOpen(true);
  };

  const handleCloseExecute = () => {
    setIsExecuteModalOpen(false);
    setRunInput({ task: '' });
  };

  const handleExecute = async () => {
    try {
      if (executeType === 'agent') {
        const data: CreateAgentRunRequest = { task: runInput.task, input: runInput };
        alert('Execute agent run - would call apiClient.createAgentRun');
      } else {
        const data: CreateTeamRunRequest = { task: runInput.task, input: runInput };
        alert('Execute team run - would call apiClient.createTeamRun');
      }
      handleCloseExecute();
      refetch();
    } catch (err) {
      console.error('Failed to execute run:', err);
    }
  };

  const handleViewDetails = (runId: number) => {
    setSelectedRun(runs.find(r => r.id === runId) || null);
    setIsDetailModalOpen(true);
  };

  const closeDetailModal = () => {
    setIsDetailModalOpen(false);
    setSelectedRun(null);
  };

  if (runsLoading) {
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
          <h1 className="text-2xl font-bold text-gray-900">Runs</h1>
          <p className="text-gray-600 mt-1">
            Monitor agent and team executions
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as RunStatus | '')}
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <Button onClick={() => refetch()}>
            Refresh
          </Button>
        </div>
      </div>

      {filteredRuns.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No runs found.</p>
            <p className="text-sm text-gray-400">
              Execute an agent or team to see run results here.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Task
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tokens
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRuns.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    #{run.id}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                    {run.task}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {run.agent_id ? `Agent ${run.agent_id}` : run.team_id ? `Team ${run.team_id}` : 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {run.tokens_used || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {run.cost ? `$${run.cost.toFixed(4)}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {new Date(run.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewDetails(run.id)}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Execute Agent/Team Modal */}
      <Modal
        isOpen={isExecuteModalOpen}
        onClose={handleCloseExecute}
        title={`Execute ${executeType === 'agent' ? 'Agent' : 'Team'}`}
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select {executeType === 'agent' ? 'Agent' : 'Team'}
            </label>
            <select
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              value={selectedId}
              onChange={(e) => setSelectedId(Number(e.target.value))}
            >
              <option value="">Select...</option>
              {executeType === 'agent'
                ? agents
                    .filter(a => a.is_active)
                    .map((agent) => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.role})
                      </option>
                    ))
                : teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name} ({team.mode})
                    </option>
                  ))}
            </select>
          </div>

          <Textarea
            label="Task Description"
            placeholder="What should the agent do?"
            value={runInput.task}
            onChange={(e) => setRunInput({ ...runInput, task: e.target.value })}
            required
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Additional Input (JSON)
            </label>
            <textarea
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
              rows={4}
              placeholder='{"key": "value"}'
              value={runInput.input ? JSON.stringify(runInput.input, null, 2) : ''}
              onChange={(e) => {
                try {
                  const input = e.target.value ? JSON.parse(e.target.value) : {};
                  setRunInput({ ...runInput, input });
                } catch {
                  // Invalid JSON, ignore
                }
              }}
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <Button variant="secondary" onClick={handleCloseExecute}>
            Cancel
          </Button>
          <Button onClick={handleExecute} isLoading={false}>
            <Play className="h-4 w-4 mr-2" />
            Execute
          </Button>
        </div>
      </Modal>

      {/* Run Details Modal */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={closeDetailModal}
        title={`Run Details - #${selectedRun?.id}`}
        size="lg"
      >
        {false ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : selectedRun ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <StatusBadge status={selectedRun.status} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
                <p className="text-sm text-gray-900">
                  {new Date(selectedRun.created_at).toLocaleString()}
                </p>
              </div>
              {selectedRun.completed_at && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Completed</label>
                  <p className="text-sm text-gray-900">
                    {new Date(selectedRun.completed_at).toLocaleString()}
                  </p>
                </div>
              )}
              {selectedRun.duration_ms && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration</label>
                  <p className="text-sm text-gray-900">{selectedRun.duration_ms} ms</p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Task</label>
              <p className="text-sm text-gray-900">{selectedRun.task}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Input</label>
              <pre className="bg-gray-50 p-3 rounded-md text-sm text-gray-900 overflow-x-auto">
                {JSON.stringify(selectedRun.input, null, 2)}
              </pre>
            </div>

            {selectedRun.output && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Output</label>
                <pre className="bg-gray-50 p-3 rounded-md text-sm text-gray-900 overflow-x-auto">
                  {JSON.stringify(selectedRun.output, null, 2)}
                </pre>
              </div>
            )}

            {selectedRun.error && (
              <div>
                <label className="block text-sm font-medium text-red-700 mb-1">Error</label>
                <pre className="bg-red-50 p-3 rounded-md text-sm text-red-900 overflow-x-auto">
                  {selectedRun.error}
                </pre>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tokens Used</label>
                <p className="text-sm text-gray-900">{selectedRun.tokens_used || '-'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cost</label>
                <p className="text-sm text-gray-900">
                  {selectedRun.cost ? `$${selectedRun.cost.toFixed(4)}` : '-'}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">Run not found.</p>
        )}
      </Modal>
    </div>
  );
};

export default RunsPage;
