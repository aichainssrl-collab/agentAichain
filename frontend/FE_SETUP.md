# AgentAichain Frontend - Setup Summary

## What Was Built

A full-featured React + TypeScript frontend application for the AgentAichain B2B multi-agent orchestration platform.

## Key Features Implemented

### Authentication & Routing
- JWT-based authentication with automatic token management
- Protected routes with redirect to login
- Login page with form validation
- Tenant registration page
- Main layout with sidebar navigation
- Token expiration handling with clear error messages

### Dashboard
- Overview statistics (total agents, teams, runs, active runs)
- Recent runs table with status badges
- Quick navigation to all sections
- System health indicators

### Agents Management
- List all agents in card grid
- Create new agents (name, role, model, description, instructions, tools, config)
- **Edit agents** – pre-filled modal, partial updates, validation
- Delete agents with confirmation
- Agent status (active/inactive) display
- **Dynamic model dropdown** – loads from API, filters active models, shows inactive with warning
- Model validation: prevents saving with inactive/non-existent models

### Teams Management
- List all teams
- Create teams with agent selection
- Add/remove agents from teams
- Team details (mode, max_iterations, agent count, agents list)
- Delete teams
- Optimized queries with eager loading

### Runs Monitoring
- List all runs with filtering by status
- Execute agent runs with custom task and input (JSON)
- Execute team runs with custom task and input (JSON)
- Detailed run view with output and error logs
- Auto-refresh for running/pending runs (polling every 2s)
- Cost and token usage tracking
- Run status badges (pending, running, completed, failed, cancelled)

### API Key Management
- List all API keys with prefix, status, usage
- Create new API keys with optional expiration
- Revoke API keys
- Secure key display with copy functionality
- Only shows full key once on creation

### Settings Management (NEW – Phase 2)
- **Skills Page**: CRUD for agent skills (name, description, category, active status)
- **Models Page**: CRUD for AI model configurations
  - Provider-agnostic: OpenAI, Anthropic, Google, Ollama, OpenRouter, custom
  - Fields: name, provider, base_url, api_key, max_tokens, max_context, cost tracking, config (JSON), is_active
  - Model validation used by agents; inactive models hidden but selectable with warning
  - Cost tracking for billing analytics
  - Flexible configuration for any LLM provider

## Tech Stack

- **React 18** + **TypeScript** (strict mode)
- **Vite** for dev server and bundling with HMR
- **React Router v6** for client-side routing
- **React Query** for server state management (caching, auto-refetch, mutations)
- **Custom API Client** (fetch-based) with interceptors for auth and logging
- **Tailwind CSS** for utility-first styling
- **Lucide React** for icons
- **Vitest** for unit testing (test suite ready)

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # LoadingSpinner, StatusBadge
│   │   ├── layout/          # MainLayout with sidebar navigation
│   │   └── ui/              # Reusable UI components (Button, Card, Input, Modal, Select)
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts    # ApiClient singleton with JWT injection
│   │   └── hooks/
│   │       ├── useAuth.tsx  # Authentication context (login, logout, token storage)
│   │       └── useApi.ts    # React Query hooks for all endpoints (agents, teams, runs, settings, etc.)
│   ├── pages/
│   │   ├── auth/            # LoginPage, RegisterPage
│   │   ├── dashboard/       # DashboardPage with stats
│   │   ├── agents/          # AgentsPage (CRUD + dynamic model selection)
│   │   ├── teams/           # TeamsPage (CRUD + member management)
│   │   ├── runs/            # RunsPage (list, execute agent/team runs)
│   │   ├── api-keys/        # ApiKeysPage (manage machine keys)
│   │   └── settings/        # SkillsPage, ModelsPage (settings CRUD)
│   ├── types/
│   │   └── index.ts         # All TypeScript interfaces matching backend
│   ├── App.tsx              # Root with routing and providers
│   └── main.tsx             # Entry point (React 18 createRoot)
├── public/
│   └── vite.svg             # Favicon
├── index.html
├── package.json
├── vite.config.ts           # Dev server with API proxy to /api/v1/*
├── vitest.config.ts         # Test configuration
├── tailwind.config.js       # Custom theme (colors, fonts)
├── tsconfig.json
├── tsconfig.node.json
├── .env.example             # Environment variables template
├── .eslintrc.cjs            # ESLint configuration
├── FE_SETUP.md              # This file
└── README.md                # Quick frontend guide
```

## API Integration

All backend endpoints are fully integrated:

- **Auth**: `POST /auth/token`, `POST /auth/register-tenant`
- **Agents**: `GET /agents/`, `POST /agents/`, `GET /agents/{id}`, `PUT /agents/{id}`, `DELETE /agents/{id}`
- **Teams**: `GET /teams/`, `POST /teams/`, `GET /teams/{id}`, `POST /teams/{id}/agents/{agentId}`, `DELETE /teams/{id}/agents/{agentId}`, `DELETE /teams/{id}`
- **Runs**: `GET /runs/`, `POST /runs/agent/{agentId}`, `POST /runs/team/{teamId}`, `GET /runs/{runId}`
- **API Keys**: `GET /api-keys/`, `POST /api-keys/`, `DELETE /api-keys/{id}`
- **Settings**:
  - Skills: `GET /settings/skills`, `POST /settings/skills`, `GET /settings/skills/{id}`, `PUT /settings/skills/{id}`, `DELETE /settings/skills/{id}`
  - Models: `GET /settings/models`, `POST /settings/models`, `GET /settings/models/{id}`, `PUT /settings/models/{id}`, `DELETE /settings/models/{id}`
- **Health**: `GET /health`

## How to Run

### Prerequisites

1. Backend API running on `http://localhost:8000` (with CORS enabled)
2. Node.js 18+ installed
3. Database seeded with demo data (optional but recommended)

### Installation & Development

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Login Credentials (after seeding)

- Email: `admin@demo.com`
- Password: `demo123`

### Environment Variables (.env.local)

Create `.env.local` in `frontend/`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Default proxy in `vite.config.ts` handles `/api` → backend automatically.

### Production Build

```bash
npm run build
npm run preview  # Preview the production build locally
```

The `dist/` folder contains static files ready for deployment to:
- Cloud Storage + CDN
- Netlify / Vercel
- Firebase Hosting
- Any static file host

## Design Decisions

1. **Tailwind CSS**: Utility-first approach for rapid UI development without custom CSS files
2. **React Query**: Automatic caching, background refetching, and optimistic updates; essential for run status polling
3. **Custom API Client**: Lightweight fetch wrapper with JWT injection and structured logging (no Axios dependency)
4. **Component Structure**: Separated concerns between pages, reusable UI components, and business logic hooks
5. **TypeScript**: Full type safety across API contracts and UI state; interfaces match backend exactly
6. **JWT Storage**: localStorage for persistence (consider sessionStorage or httpOnly cookies in production)
7. **Proxy Configuration**: Vite dev server proxies `/api/*` to backend for seamless development
8. **Form Handling**: React Hook Form with manual state (not Zod yet) for simplicity

## State Management Strategy

- **Server State**: React Query (`useQuery`, `useMutation`) – cached, auto-refreshing
- **Auth State**: `useAuth` context – persists in localStorage
- **UI State**: Local component state (`useState`) for forms, modals, etc.
- **Global UI**: No Redux needed; React Query covers most needs

## Notable Patterns

- **ProtectedRoute** wrapper for authenticated pages
- **useRun** hook polls every 2s while run is `pending` or `running`
- **Mutation callbacks** invalidate relevant queries to keep cache fresh
- **Dynamic dropdowns** (e.g., agent model selection) load from API at render
- **Model status indicator** – inactive models show warning ⚠️ in dropdown
- **Backend validation** – agents must reference active models (400 error enforced server-side)

## Next Steps / Improvements

- Implement real-time WebSocket for run status (replace polling)
- Add agent chat interface (create run from agent details page)
- Team run execution UI with live output streaming
- Pagination for list endpoints (currently loading all)
- Toast notifications for success/error feedback
- Dark mode support
- Role-based access control (admin vs user)
- File upload for agent instructions/artifacts
- Agent/team templates and cloning
- Run cancellation (needs backend endpoint)
- Cost analytics dashboard with charts
- Internationalization (i18n)
- Comprehensive test suite (unit + integration)
- E2E tests with Playwright
- Optimistic updates for mutations

## Troubleshooting

### "Cannot find module '@/lib/hooks/useApi'"
Ensure `tsconfig.json` has `"baseUrl": "."` and `"paths": { "@/*": ["src/*"] }`.

### 401 Unauthorized
- Check JWT token is set (localStorage `access_token`)
- Token may be expired (default 24h) – re-login
- Verify backend is running on `http://localhost:8000`
- Check CORS headers from backend include `http://localhost:3000`

### Model dropdown empty
- Ensure at least one AI model exists in `/settings/models` (create via backend API)
- Check `is_active` is true for at least one model
- If all models inactive, dropdown shows warning message

### Live reload not working
- Vite dev server must be running (`npm run dev`)
- Check browser console for HMR errors
- Try manual hard refresh (Ctrl+Shift+R)

---

*Last updated: 2026-04-04 – Phase 2 complete (Settings + Agent Edit)*

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** for dev server and bundling
- **React Router v6** for client-side routing
- **React Query** for server state management (caching, auto-refetch)
- **Axios** with interceptors for API communication
- **Tailwind CSS** for utility-first styling
- **React Hook Form** + **Zod** for form validation
- **Lucide React** for icons
- **Vitest** for testing

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # LoadingSpinner, StatusBadge
│   │   ├── layout/          # MainLayout with sidebar
│   │   ├── ui/              # Reusable UI primitives
│   │   ├── agents/          # (ready for agent-specific components)
│   │   ├── teams/           # (ready for team-specific components)
│   │   ├── runs/            # (ready for run-specific components)
│   │   └── api-keys/        # (ready for api-key components)
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts    # Axios instance with auth
│   │   ├── hooks/
│   │   │   ├── useAuth.tsx  # Authentication context
│   │   │   └── useApi.ts    # React Query hooks for all endpoints
│   │   ├── schemas/         # (ready for Zod schemas)
│   │   └── utils/           # (ready for utilities)
│   ├── pages/
│   │   ├── auth/            # Login, Register
│   │   ├── dashboard/       # Dashboard
│   │   ├── agents/          # Agents CRUD
│   │   ├── teams/           # Teams management
│   │   ├── runs/            # Runs monitoring & execution
│   │   └── api-keys/        # API key management
│   ├── types/
│   │   └── index.ts         # All TypeScript interfaces
│   ├── App.tsx              # Routing & providers
│   └── main.tsx             # Entry point
├── public/
│   └── vite.svg             # Favicon
├── index.html
├── package.json
├── vite.config.ts           # Dev server with proxy
├── vitest.config.ts         # Test configuration
├── tailwind.config.js       # Custom Tailwind theme
├── tsconfig.json
└── README.md                # Frontend-specific documentation
```

## API Integration

All API endpoints from the FastAPI backend are integrated:

- `POST /auth/token` - Login
- `POST /auth/register-tenant` - Register tenant
- `GET /agents/` - List agents
- `POST /agents/` - Create agent
- `GET /teams/` - List teams
- `POST /teams/` - Create team
- `POST /teams/{teamId}/agents/{agentId}` - Add agent to team
- `DELETE /teams/{teamId}/agents/{agentId}` - Remove agent
- `GET /runs/` - List runs (with filters)
- `POST /runs/agent/{agentId}` - Execute agent
- `POST /runs/team/{teamId}` - Execute team
- `GET /runs/{runId}` - Get run details
- `GET /api-keys/` - List API keys
- `POST /api-keys/` - Create API key
- `DELETE /api-keys/{id}` - Revoke API key
- `GET /health` - Health check

## How to Run

### Prerequisites

1. Backend API running on `http://localhost:8000`
2. Node.js 18+ installed

### Installation & Development

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Login Credentials

After seeding the database:
- Email: `admin@demo.com`
- Password: `demo123`

### Production Build

```bash
npm run build
npm run preview  # Preview the production build
```

The `dist/` folder contains static files ready for deployment.

## Design Decisions

1. **Tailwind CSS**: Utility-first approach for rapid UI development without custom CSS files
2. **React Query**: Automatic caching and background refetching, especially useful for run status polling
3. **Form Validation**: React Hook Form + Zod provides type-safe, performant forms
4. **Axios Interceptors**: Automatic JWT injection and 401 handling
5. **Component Structure**: Separated concerns between pages, reusable components, and business logic
6. **TypeScript**: Full type safety across API contracts and UI state
7. **Bearer Token Auth**: JWT stored in localStorage (consider secure storage for production)

## Next Steps / Improvements

- Implement agent/team update functionality (edit modal includes form)
- Add pagination for list endpoints
- Implement real-time updates via WebSocket for run status
- Add more sophisticated error handling and toast notifications
- Create reusable data tables component
- Add dark mode support
- Implement role-based access control (admin vs user)
- Add file upload support for agent instructions
- Create agent/team templates
- Add run cancellation functionality
- Implement cost analytics dashboard
- Add internationalization (i18n)
- Unit and integration tests

## Notes

- The proxy in `vite.config.ts` rewrites `/api/*` to `/api/v1/*` for cleaner URLs
- React Query auto-refreshes runs with `pending` or `running` status every 2 seconds
- API key creation shows the full key only once - stored in state and cleared on modal close
- All forms have client-side validation via Zod schemas
- Authentication state is persisted in localStorage
