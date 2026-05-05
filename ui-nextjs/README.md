# ResolveAI - Next.js Premium UI

A modern, premium customer support interface built with Next.js 14, Framer Motion, and Tailwind CSS.

## Features

- **Premium Design System**: Clean Zinc/Emerald palette with refined typography
- **Bento Grid Layout**: Asymmetric dashboard with smooth animations
- **Framer Motion**: Premium micro-interactions and transitions
- **Real-time Chat**: Interactive chat interface with typing indicators
- **Responsive**: Mobile-first design with proper breakpoints

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (FastAPI)

### Installation

```bash
cd ui-nextjs
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
ui-nextjs/
├── app/
│   ├── layout.tsx          # Root layout with fonts
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Design system CSS
├── components/
│   ├── ui/                 # Reusable UI components
│   │   ├── BentoCard.tsx
│   │   ├── MetricCard.tsx
│   │   └── QuickActionButton.tsx
│   ├── dashboard/          # Dashboard components
│   │   ├── MetricsDashboard.tsx
│   │   ├── QuickActions.tsx
│   │   └── DemoOrders.tsx
│   └── chat/
│       └── ChatInterface.tsx
└── lib/
    └── api.ts              # FastAPI client
```

## Design System

### Colors
- Base: Zinc palette (#fafafa to #09090b)
- Accent: Emerald (#10b981)
- Error: Red (#ef4444)
- Warning: Amber (#f59e0b)

### Typography
- Font: Inter (sans), JetBrains Mono (code)
- Tracking: Tighter on headings
- Sizes: Defined in Tailwind config

### Animations
- fadeInUp: Initial load animations
- slideInLeft: Escalation cards
- pulse: Status indicators
- blink: Hero badge dot
- shimmer: Skeleton loading
- typingBounce: Chat typing indicator

## Environment Variables

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Backend Integration

The UI connects to the FastAPI backend at `/api` endpoints:
- GET `/metrics` - Fetch dashboard metrics
- POST `/chat` - Send chat message
- GET `/escalations` - Fetch escalation list

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS 3.x
- **Animations**: Framer Motion 11.x
- **Icons**: Phosphor Icons
- **Fonts**: Inter, JetBrains Mono

## Deployment

Deploy to Vercel:

```bash
npm install -g vercel
vercel
```

Or use Docker:
```bash
docker build -t resolveai-ui .
docker run -p 3000:3000 resolveai-ui
```

## License

MIT