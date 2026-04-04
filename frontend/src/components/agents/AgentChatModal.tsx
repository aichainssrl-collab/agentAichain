import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Textarea } from '@/components/ui';
import { useCreateAgentRun, useRun } from '@/lib/hooks/useApi';
import { Agent } from '@/types';
import { Send, Loader2, User, Bot, AlertCircle } from 'lucide-react';

interface AgentChatModalProps {
  agent: Agent | null;
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  runId?: number;
}

export const AgentChatModal: React.FC<AgentChatModalProps> = ({ agent, isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [activeRunId, setActiveRunId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const createRun = useCreateAgentRun();
  const { data: runData, refetch: checkRunStatus } = useRun(activeRunId || 0);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeRunId]);

  // Reset chat when agent changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setMessages([
        {
          id: 'system-1',
          role: 'system',
          content: `Chat started with ${agent?.name} (${agent?.model}).`
        }
      ]);
      setActiveRunId(null);
      setInput('');
    }
  }, [agent, isOpen]);

  // Poll for run status
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
      if (runData.status === 'completed' || runData.status === 'failed' || runData.status === 'cancelled') {
        setActiveRunId(null); // Stop polling

        if (runData.status === 'completed') {
          setMessages(prev => [
            ...prev,
            {
              id: `msg-${Date.now()}`,
              role: 'assistant',
              content: typeof runData.output === 'string' 
                ? runData.output 
                : runData.output?.result || runData.output?.response || JSON.stringify(runData.output, null, 2) || 'No output provided.',
              runId: runData.id
            }
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            {
              id: `err-${Date.now()}`,
              role: 'system',
              content: `Error: Run failed (${runData.error || 'Unknown error'})`
            }
          ]);
        }
      }
    }
  }, [runData, activeRunId]);

  const handleSend = async () => {
    if (!input.trim() || !agent || activeRunId) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');

    try {
      const response = await createRun.mutateAsync({
        agentId: agent.id,
        data: { task: userMsg.content, input: { chat_history: messages.filter(m => m.role !== 'system') } }
      });
      setActiveRunId(response.run_id);
    } catch (error: any) {
      setMessages(prev => [
        ...prev,
        {
          id: `sys-err-${Date.now()}`,
          role: 'system',
          content: `Failed to send message: ${error.message || 'Network error'}`
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

  if (!agent) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Chat: ${agent.name}`}
      size="xl"
    >
      <div className="flex flex-col h-[60vh]">
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 rounded-lg border border-gray-200">
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
        </div>

        <div className="mt-4 flex items-end space-x-2">
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
            disabled={!input.trim() || activeRunId !== null}
            className="h-[60px] px-6"
          >
            {activeRunId ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
