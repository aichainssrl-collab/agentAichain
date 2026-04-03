# AgentAichain API Reference

Base URL: `https://your-domain.com/api/v1`

Authentication: `X-API-Key: <your-api-key>` header required for all endpoints except `/auth/*`.

---

## Authentication

### Register Tenant

**POST** `/auth/register-tenant`

Create a new tenant with admin user.

**Request JSON:**
```json
{
  "name": "Acme Corp",
  "slug": "acme-corp",
  "admin_email": "admin@acme.com",
  "admin_password": "secure_password_123"
}
```

**Response:**
```json
{
  "message": "Tenant created successfully",
  "tenant_id": 1,
  "admin_id": 2
}
```

### Get Access Token

**POST** `/auth/token`

Standard OAuth2 password flow.

**Form Data:**
- `username`: user email
- `password`: user password

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

Use token in `Authorization: Bearer <token>` header for JWT-authenticated requests.

---

## Agents

### List Agents

**GET** `/agents/`

List all agents for the current tenant.

**Headers:** `X-API-Key` or `Authorization`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Support Bot",
    "role": "assistant",
    "model": "gpt-4",
    "is_active": true,
    "created_at": "2026-04-03T12:00:00Z"
  }
]
```

### Create Agent

**POST** `/agents/`

Create a new agent.

**Request JSON:**
```json
{
  "name": "Support Bot",
  "role": "assistant",
  "model": "gpt-4",
  "description": "Helps customers with questions",
  "instructions": "Be polite and concise.",
  "tools": ["search_kb", "create_ticket"],
  "config": {
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Support Bot",
  "role": "assistant",
  "model": "gpt-4",
  "tenant_id": 1
}
```

### Get Agent

**GET** `/agents/{agent_id}`

Get agent details.

**Response:**
```json
{
  "id": 1,
  "name": "Support Bot",
  "description": "Helps customers...",
  "role": "assistant",
  "model": "gpt-4",
  "config": { "temperature": 0.7 },
  "tools": ["search_kb", "create_ticket"],
  "instructions": "Be polite...",
  "is_active": true,
  "created_at": "2026-04-03T12:00:00Z"
}
```

### Delete Agent

**DELETE** `/agents/{agent_id}`

Permanently delete an agent.

**Response:** `204 No Content`

---

## Teams

### List Teams

**GET** `/teams/`

List all teams for current tenant.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Research Squad",
    "mode": "coordinate",
    "agent_count": 3,
    "created_at": "2026-04-03T12:00:00Z"
  }
]
```

### Create Team

**POST** `/teams/`

Create a new team, optionally adding agents.

**Request JSON:**
```json
{
  "name": "Research Squad",
  "mode": "coordinate",
  "max_iterations": 10,
  "config": {
    "sharing_strategy": "round_robin"
  },
  "agent_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Research Squad",
  "mode": "coordinate",
  "tenant_id": 1,
  "agent_count": 3
}
```

### Get Team

**GET** `/teams/{team_id}`

Get team details with agents.

**Response:**
```json
{
  "id": 1,
  "name": "Research Squad",
  "description": null,
  "mode": "coordinate",
  "max_iterations": 10,
  "config": {},
  "agents": [
    { "id": 1, "name": "Researcher", "role": "researcher" },
    { "id": 2, "name": "Writer", "role": "writer" }
  ],
  "created_at": "2026-04-03T12:00:00Z"
}
```

### Add Agent to Team

**POST** `/teams/{team_id}/agents/{agent_id}`

Add an existing agent to a team.

**Response:** `200 OK`

### Remove Agent from Team

**DELETE** `/teams/{team_id}/agents/{agent_id}`

Remove an agent from a team.

**Response:** `200 OK`

---

## Runs

### Create Agent Run (Async)

**POST** `/runs/agent/{agent_id}`

Create an asynchronous run for an agent.

**Request JSON:**
```json
{
  "task": "Summarize this document",
  "input": {
    "document": "Lorem ipsum...",
    "max_length": 100
  }
}
```

**Response:**
```json
{
  "run_id": 123,
  "status": "pending",
  "celery_task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "agent_id": 1
}
```

### Create Team Run (Async)

**POST** `/runs/team/{team_id}`

Create an asynchronous run for a team.

**Request JSON:**
```json
{
  "task": "Research Q2 trends",
  "input": {
    "topic": "AI agent platforms"
  }
}
```

**Response:**
```json
{
  "run_id": 124,
  "status": "pending",
  "celery_task_id": "f0e9d8c7-b6a5-4321-zyxw-cba987654321",
  "team_id": 1,
  "agent_count": 3
}
```

### Get Run

**GET** `/runs/{run_id}`

Get run status and result.

**Response:**
```json
{
  "id": 123,
  "task": "Summarize this document",
  "input": { "document": "..." },
  "output": { "summary": "..." },
  "error": null,
  "status": "completed",
  "tokens_used": 450,
  "cost": 0.0045,
  "duration_ms": 2340,
  "metadata": {},
  "agent_id": 1,
  "team_id": null,
  "created_at": "2026-04-03T12:00:00Z",
  "celery_task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Status values:** `pending`, `running`, `completed`, `failed`, `cancelled`

### List Runs

**GET** `/runs/?limit=50&offset=0&status=completed&agent_id=1`

List runs for current tenant with optional filters.

**Query Parameters:**
- `limit` (default 50, max 100)
- `offset` (default 0)
- `status` (optional filter)
- `agent_id` (optional filter)
- `team_id` (optional filter)

**Response:**
```json
[
  {
    "id": 123,
    "task": "Summarize this document",
    "status": "completed",
    "agent_id": 1,
    "team_id": null,
    "tokens_used": 450,
    "cost": 0.0045,
    "created_at": "2026-04-03T12:00:00Z"
  }
]
```

---

## API Keys

### Create API Key

**POST** `/api-keys/`

Create a new API key for the authenticated user.

**Request JSON:**
```json
{
  "name": "Production Backend",
  "expires_in_days": 90
}
```

**Response (raw key shown only once):**
```json
{
  "id": 1,
  "name": "Production Backend",
  "key": "ak_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "expires_at": "2026-07-02T12:00:00Z",
  "created_at": "2026-04-03T12:00:00Z"
}
```

**⚠️ SECURITY:** Store the returned key securely; it is never shown again.

### List API Keys

**GET** `/api-keys/`

List API keys for current user.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Production Backend",
    "is_active": true,
    "expires_at": "2026-07-02T12:00:00Z",
    "last_used_at": "2026-04-03T13:00:00Z",
    "usage_count": 142,
    "created_at": "2026-04-03T12:00:00Z"
  }
]
```

### Revoke API Key

**DELETE** `/api-keys/{api_key_id}`

Revoke an API key (sets `is_active=false`).

**Response:** `200 OK`

---

## Error Responses

All endpoints return standard HTTP status codes.

**400 Bad Request:**
```json
{
  "detail": "Invalid input",
  "error_type": "validation_error"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid API Key",
  "error_type": "authentication_error"
}
```

**403 Forbidden:**
```json
{
  "detail": "Agent not in tenant",
  "error_type": "authorization_error"
}
```

**404 Not Found:**
```json
{
  "detail": "Agent not found",
  "error_type": "not_found_error"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error",
  "error_type": "server_error"
}
```

---

## Rate Limits

Currently none enforced (development). Production will implement:

- 1000 requests/minute per API key
- 60 create-agent calls/hour per tenant
- 100 concurrent runs per tenant

---

## Pagination

List endpoints support `limit` and `offset` query parameters.

Default `limit` is 50, max 100.

---

*OpenAPI (Swagger) docs available at: `/docs` (interactive)*