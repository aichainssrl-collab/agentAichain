import React from 'react';
import { Link } from 'react-router-dom';
import { useAgents } from '@/lib/hooks/useApi';
import { useTeams } from '@/lib/hooks/useApi';
import { useRuns } from '@/lib/hooks/useApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import { LoadingSpinner } from '@/components/common';
import { Bot, Users, Play, Activity } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: teamsData, isLoading: teamsLoading } = useTeams();
  const { data: runsData, isLoading: runsLoading } = useRuns(10);

  const agents = agentsData?.data || [];
  const teams = teamsData?.data || [];
  const runs = runsData?.data || [];

  const recentRuns = runs.slice(0, 5);

  const stats = [
    {
      name: 'Total Agents',
      value: agents.length,
      icon: Bot,
      color: 'bg-blue-500',
      link: '/agents',
    },
    {
      name: 'Total Teams',
      value: teams.length,
      icon: Users,
      color: 'bg-green-500',
      link: '/teams',
    },
    {
      name: 'Total Runs',
      value: runs.length,
      icon: Play,
      color: 'bg-purple-500',
      link: '/runs',
    },
    {
      name: 'Active Runs',
      value: runs.filter((r) => r.status === 'running' || r.status === 'pending').length,
      icon: Activity,
      color: 'bg-yellow-500',
      link: '/runs?status=running',
    },
  ];

  if (agentsLoading || teamsLoading || runsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Overview of your AI agent platform
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Link
            key={stat.name}
            to={stat.link}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Recent runs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
        </CardHeader>
        <CardContent>
          {recentRuns.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No runs yet. Create an agent and execute it to see results.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Task
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Agent/Team
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
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentRuns.map((run) => (
                    <tr key={run.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-xs truncate">
                        {run.task}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {run.agent_id || run.team_id || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          run.status === 'completed' ? 'bg-green-100 text-green-800' :
                          run.status === 'failed' ? 'bg-red-100 text-red-800' :
                          run.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          run.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {run.tokens_used || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {run.cost ? `$${run.cost.toFixed(4)}` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {recentRuns.length > 0 && (
            <div className="mt-4 text-center">
              <Link
                to="/runs"
                className="text-primary-600 hover:text-primary-700 text-sm font-medium"
              >
                View all runs →
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardPage;
