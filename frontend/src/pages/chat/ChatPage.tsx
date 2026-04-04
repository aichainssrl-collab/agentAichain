import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, Button, Textarea } from '@/components/ui';
import { useAgents, useTeams, useCreateAgentRun, useCreateTeamRun, useRun } from '@/lib/hooks/useApi';
import { Send, Loader2, User, Bot, AlertCircle, ArrowLeft, MessageSquare } from 'lucide-react';
import type { Agent, Team } from '@/types';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  runId?: number;
}

type ChatMode = 'agent' | 'team';

const ChatPage: React.FC = () => {
  const { mode, id } = useParams<{ mode: string; id: string }>();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [activeRunId, setActiveRunId] = useState<number | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<number | ''>('');
  const [selectedTeamId, setSelectedTeamId] = useState<number | ''>(id ? parseInt(id) : '');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: agentsData } = useAgents();
  const { data: teamsData } = useTeams();
  const createAgentRun = useCreateAgentRun();
  const createTeamRun = useCreateTeamRun();
  const { data: runData, refetch: checkRunStatus } = useRun(activeRunId || 0);

  const agents = agentsData?.data || [];
  const teams = teamsData?.data || [];

  // Current selection
  const currentMode: ChatMode = mode === 'team' ? 'team' : 'agent';
  const selectedAgent = agents.find(a => a.id === selectedAgentId);
  const selectedTeam = teams.find(t => t.id === selectedTeamId);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeRunId]);

  // Reset chat when selection changes
  useEffect(() => {
    if (currentMode === 'agent' && selectedAgent) {
      setMessages([
        { id: 'system-1', role: 'system', content: `Chat started with agent ${selectedAgent.name} (${selectedAgent.model}).` }
      ]);
    } else if (currentMode === 'team' && selectedTeam) {
      setMessages([
        { id: 'system-1', role: 'system', content: `Chat started with team ${selectedTeam.name} (${selectedTeam.agent_count} agents).` }
      ]);
    } else {
      setMessages([]);
    }
    setActiveRunId(null);
    setInput('');
  }, [currentMode, selectedAgentId, selectedTeamId]);

  // Polling
  useEffect(() => {
    let interval: any;
    if (activeRunId) {
      interval = window.setInterval(() => {
        checkRunStatus();
      }, 2000);
    }
    return () => {
      if (interval) window.clearInterval(interval);
    };
  }, [activeRunId, checkRunStatus]);

  // Handle run status changes
  useEffect(() => {
    if (activeRunId && runData) {
      const terminalStatuses = ['completed', 'failed', 'cancelled'];
      if (terminalStatuses.includes(runData.status)) {
        setActiveRunId(null);

        if (runData.status === 'completed') {
          const output = runData.output as any;
          const content = typeof output === 'string'
            ? output
            : output?.result || output?.response || JSON.stringify(output, null, 2) || 'No output provided.';

          setMessages(prev => [
            ...prev,
            { id: `msg-${Date.now()}`, role: 'assistant', content, runId: runData.id }
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            { id: `err-${Date.now()}`, role: 'system', content: `Error: Run failed (${runData.error || 'Unknown error'})` }
          ]);
        }
      }
    }
  }, [runData, activeRunId]);

  const handleSend = async () => {
    if (!input.trim()) return;

    if (currentMode === 'agent' && !selectedAgentId) {
      alert('Please select an agent');
      return;
    }
    if (currentMode === 'team' && !selectedTeamId) {
      alert('Please select a team');
      return;
    }

    if (activeRunId) return; // Already running

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');

    try {
      if (currentMode === 'agent') {
        const response = await createAgentRun.mutateAsync({
          agentId: selectedAgentId as number,
          data: { task: userMsg.content, input: { chat_history: messages.filter(m => m.role !== 'system') } }
        });
        setActiveRunId(response.run_id);
      } else {
        const response = await createTeamRun.mutateAsync({
          teamId: selectedTeamId as number,
          data: { task: userMsg.content, input: { chat_history: messages.filter(m => m.role !== 'system') } }
        });
        setActiveRunId(response.run_id);
      }
    } catch (error: any) {
      setMessages(prev => [
        ...prev,
        {
          id: `sys-err-${Date.now()}`,
          role: 'system',
          content: `Failed to send message: ${error.response?.data?.detail || error.message || 'Network error'}`
        }
      ]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Determine what to show in header
  const getHeaderTitle = () => {
    if (currentMode === 'agent' && selectedAgent) return `Chat with Agent: ${selectedAgent.name}`;
    if (currentMode === 'team' && selectedTeam) return `Chat with Team: ${selectedTeam.name}`;
    return 'Chat';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/agents')}
          className="flex items-center text-sm text-gray-500 hover:text-primary-600 mb-2"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Agents
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{getHeaderTitle()}</h1>
            <div className="mt-2 flex items-center space-x-4">
              <select
                value={currentMode === 'agent' ? selectedAgentId : selectedTeamId}
                onChange={(e) => {
                  const val = e.target.value ? parseInt(e.target.value) : '';
                  if (currentMode === 'agent') setSelectedAgentId(val);
                  else setSelectedTeamId(val);
                }}
                className="w-64 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">{currentMode === 'agent' ? 'Select an agent...' : 'Select a team...'}</option>
                {currentMode === 'agent'
                  ? agents.map(agent => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.model})
                      </option>
                    ))
                  : teams.map(team => (
                      <option key={team.id} value={team.id}>
                        {team.name} ({team.agent_count} agents)
                      </option>
                    ))
                }
              </select>
              {currentMode === 'agent' && selectedAgent && (
                <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${selectedAgent.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                  {selectedAgent.is_active ? 'Active' : 'Inactive'}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col min-h-0">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 border-b border-gray-200">
          {messages.length === 0 && !activeRunId && (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
              <p>Select an agent or team and start chatting</p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : msg.role === 'system' ? 'justify-center' : 'justify-start'}`}
            >
              {msg.role === 'system' ? (
                <div className="bg-gray-200 text-gray-600 text-xs px-3 py-1 rounded-full flex items-center">
                  {msg.content.startsWith('Error') && <AlertCircle className="w-3 h-3 mr-1" />}
                  {msg.content}
                </div>
              ) : (
                <div className={`flex max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.role === 'user' ? 'bg-primary-600 ml-2' : 'bg-green-600 mr-2'
                  }`}>
                    {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
                  </div>
                  <div className={`px-4 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white rounded-tr-none'
                      : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none shadow-sm'
                  }`}>
                    <div className="whitespace-pre-wrap break-words text-sm">{msg.content}</div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {activeRunId && (
            <div className="flex justify-start">
              <div className="flex max-w-[80%] flex-row">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 mr-2 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="px-4 py-3 bg-white border border-gray-200 text-gray-800 rounded-lg rounded-tl-none shadow-sm flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
                  <span className="text-sm text-gray-500">Agent is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex items-end space-x-2">
            <div className="flex-1 relative">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message... (Shift+Enter for new line)"
                className="w-full resize-none min-h-[60px]"
                disabled={activeRunId !== null}
              />
            </div>
            <Button
              onClick={handleSend}
              disabled={!input.trim() || activeRunId !== null || (currentMode === 'agent' && !selectedAgentId) || (currentMode === 'team' && !selectedTeamId)}
              className="h-[60px] px-6"
            >
              {activeRunId ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </Button>
          </div>
          {(currentMode === 'agent' && !selectedAgentId) || (currentMode === 'team' && !selectedTeamId) ? (
            <p className="text-xs text-gray-500 mt-2">Select an agent/team to enable chat</p>
          ) : null}
        </div>
      </Card>
    </div>
  );
};

export default ChatPage;
