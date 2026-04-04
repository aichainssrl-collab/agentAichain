// Authentication types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterTenantRequest {
  name: string;
  slug: string;
  admin_email: string;
  admin_password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Agent types
export interface Agent {
  id: number;
  name: string;
  role: string;
  model: string;
  description?: string;
  instructions?: string;
  tools?: string[];
  config?: AgentConfig;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AgentConfig {
  temperature?: number;
  max_tokens?: number;
  [key: string]: any;
}

export interface CreateAgentRequest {
  name: string;
  role: string;
  model: string;
  description?: string;
  instructions?: string;
  tools?: string[];
  config?: AgentConfig;
}

export interface UpdateAgentRequest extends Partial<CreateAgentRequest> {
  name?: string;
  role?: string;
  model?: string;
}

// Team types
export interface Team {
  id: number;
  name: string;
  description?: string;
  mode: string;
  max_iterations?: number;
  config?: Record<string, any>;
  agent_count: number;
  agents?: Agent[];
  created_at: string;
  updated_at?: string;
}

export interface CreateTeamRequest {
  name: string;
  description?: string;
  mode: string;
  max_iterations?: number;
  config?: Record<string, any>;
  agent_ids?: number[];
}

export interface UpdateTeamRequest extends Partial<CreateTeamRequest> {
  name?: string;
  description?: string;
  mode?: string;
}

// Run types
export interface Run {
  id: number;
  task: string;
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  status: RunStatus;
  tokens_used?: number;
  cost?: number;
  duration_ms?: number;
  metadata?: Record<string, any>;
  agent_id?: number;
  team_id?: number;
  created_at: string;
  completed_at?: string;
  celery_task_id: string;
}

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface CreateAgentRunRequest {
  task: string;
  input: Record<string, any>;
}

export interface CreateTeamRunRequest {
  task: string;
  input: Record<string, any>;
}

// API Key types
export interface ApiKey {
  id: number;
  name: string;
  key: string; // Only shown on creation
  prefix: string; // Partial key for display
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  usage_count: number;
  created_at: string;
}

// Settings types
export interface Skill {
  id: number;
  name: string;
  description?: string;
  category?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AIModel {
  id: number;
  name: string;
  provider: string;
  base_url?: string;
  api_key?: string;
  max_tokens?: number;
  max_context?: number;
  cost_per_1k_input?: number;
  cost_per_1k_output?: number;
  config?: string;  // JSON string
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CreateApiKeyRequest {
  name: string;
  expires_in_days?: number;
}

// Common types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface ApiError {
  detail: string;
  error_type: string;
}

export interface HealthCheck {
  status: string;
  timestamp: string;
  version?: string;
}
