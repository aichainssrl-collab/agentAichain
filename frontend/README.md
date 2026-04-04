# AgentAichain Frontend

React + TypeScript frontend for the AgentAichain B2B multi-agent orchestration platform.

## Features

- Agent management (CRUD)
- Team management with agent assignments
- Run monitoring and execution
- API key management
- JWT authentication
- Responsive design with Tailwind CSS
- React Query for data fetching

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development
- **React Router v6** for routing
- **React Query** for server state management
- **Axios** for API communication
- **Tailwind CSS** for styling
- **React Hook Form** with Zod validation
- **Lucide React** for icons

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server (with proxy to backend at localhost:8000)
npm run dev
```

The frontend will be available at http://localhost:3000

### Build

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

## API Configuration

The frontend proxies API requests to the backend:

- Development: `/api/*` → `http://localhost:8000/api/v1/*`
- Production: Update `vite.config.ts` to point to your backend URL

## Project Structure

```
src/
├── components/
│   ├── common/       # Reusable components (LoadingSpinner, StatusBadge)
│   ├── layout/       # Layout components (MainLayout)
│   ├── ui/           # UI primitives (Button, Card, Modal, Input)
│   ├── agents/       # Agent-specific components
│   ├── teams/        # Team-specific components
│   ├── runs/         # Run-specific components
│   └── api-keys/     # API key components
├── lib/
│   ├── api/          # API client
│   ├── hooks/        # Custom React Query hooks
│   ├── schemas/      # Zod validation schemas
│   └── utils/        # Utility functions
├── pages/
│   ├── auth/         # Login & Register pages
│   ├── dashboard/    # Dashboard page
│   ├── agents/       # Agents management page
│   ├── teams/        # Teams page
│   ├── runs/         # Runs monitoring page
│   └── api-keys/     # API keys page
├── types/            # TypeScript type definitions
├── App.tsx           # Main app component with routing
├── main.tsx          # Entry point
└── index.css         # Global styles with Tailwind
```

## Authentication

- JWT tokens stored in localStorage
- Automatic token injection in API requests
- Protected routes redirect to login if not authenticated
- Auto-redirect to dashboard if already logged in

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=/api
```

## Development Notes

- Uses React Query for data fetching and caching
- All API calls are type-safe using TypeScript
- Form validation with React Hook Form + Zod
- Responsive design with Tailwind CSS
- Proxy configured for local development

## Container Deployment

The frontend can be built and served with any static file server:

```bash
# Build
npm run build

# The dist/ folder contains production-ready files
# Deploy to Netlify, Vercel, S3, or any static hosting
```
