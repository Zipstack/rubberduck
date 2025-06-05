# Rubberduck Frontend

A modern React frontend for the Rubberduck LLM caching proxy server.

## Features

- **Authentication**: Login/register with email/password + social login support
- **Dashboard**: Live system stats and metrics with real-time updates
- **Proxy Management**: Complete CRUD operations for LLM proxy instances
- **Logs**: Real-time log streaming with filtering and export capabilities
- **Settings**: Global system configuration
- **Responsive Design**: Beautiful, Stripe-like UI with Tailwind CSS

## Tech Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v3 + Tailwind UI components
- **Routing**: React Router v7
- **Icons**: Heroicons
- **Testing**: Vitest + React Testing Library

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) to view the app.

### Testing

```bash
# Run tests in watch mode
npm run test

# Run tests once
npm run test:run

# Run tests with UI
npm run test:ui
```

### Building

```bash
npm run build
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main app layout with sidebar
│   └── ProxyCard.tsx   # Individual proxy card component
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication state management
├── pages/              # Main application pages
│   ├── Dashboard.tsx   # System overview and metrics
│   ├── Proxies.tsx     # Proxy management interface
│   ├── Logs.tsx        # Log viewing and filtering
│   ├── Settings.tsx    # Global configuration
│   ├── Login.tsx       # Authentication forms
│   └── Register.tsx    
├── types/              # TypeScript type definitions
│   └── index.ts        # All application types
├── test/               # Test files
└── utils/              # Utility functions
```

## Key Components

### Dashboard
- Real-time metrics cards (proxies, cache hit rate, error rate, RPM, cost)
- Active proxy status overview
- Recent activity feed
- Live data updates every 30 seconds

### Proxy Management
- Create, start, stop, configure, and delete proxies
- Proxy status indicators and port management
- Failure simulation configuration
- Search and filtering capabilities

### Logs
- Real-time log streaming
- Advanced filtering (status, proxy, cache hit/miss)
- Export functionality (CSV/JSON)
- Request metadata display

### Settings
- Authentication method configuration
- Global IP filtering (allow/block lists)
- System-wide settings
- Security configuration

## Authentication

The frontend supports multiple authentication methods:

- Email/password login
- Google OAuth (configurable)
- GitHub OAuth (configurable)
- Registration with email verification

## Design System

The UI follows a Stripe-inspired design with:

- Clean, modern interface
- Consistent spacing and typography
- Intuitive navigation
- Responsive layout for all screen sizes
- Accessible form controls and interactions

## API Integration

The frontend is designed to integrate with the Rubberduck FastAPI backend:

- RESTful API calls for all operations
- JWT token authentication
- Real-time updates via polling (WebSocket support planned)
- Error handling and loading states

## Contributing

1. Follow the existing code style and patterns
2. Write tests for new components
3. Use TypeScript strictly (no `any` types)
4. Follow React best practices and hooks patterns
5. Ensure responsive design on all screen sizes