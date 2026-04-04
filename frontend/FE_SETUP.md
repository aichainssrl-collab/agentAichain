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

### Dashboard
- Overview statistics (total agents, teams, runs, active runs)
- Recent runs table with status badges
- Quick navigation to all sections

### Agents Management
- List all agents in card grid
- Create new agents (name, role, model, description, instructions, tools, config)
- Edit agents (UI ready, API endpoint pending)
- Delete agents with confirmation
- Agent status (active/inactive) display

### Teams Management
- List all teams
- Create teams with agent selection
- Add/remove agents from teams
- Team details (mode, max_iterations, agent count)
- Delete teams

### Runs Monitoring
- List all runs with filtering by status
- Execute agent runs with custom task and input (JSON)
- Execute team runs with custom task and input (JSON)
- Detailed run view with output and error logs
- Auto-refresh for running/pending runs
- Cost and token usage tracking

### API Key Management
- List all API keys with prefix, status, usage
- Create new API keys with optional expiration
- Revoke API keys
- Secure key display with copy functionality
- Only shows full key once on creation

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
