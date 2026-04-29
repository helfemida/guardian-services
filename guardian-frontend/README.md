# Guardian Frontend

Vue 3 dashboard for the **Guardian Intelligent Surveillance System**.

## Tech Stack

| Layer      | Technology                         |
|------------|------------------------------------|
| Framework  | Vue 3 (Composition API)            |
| State      | Pinia + persisted state            |
| Router     | Vue Router 4                       |
| HTTP       | Axios (JWT interceptor + refresh)  |
| Real-time  | Server-Sent Events (SSE)           |
| Charts     | Chart.js + vue-chartjs             |
| Maps       | Leaflet + @vue-leaflet/vue-leaflet |
| Icons      | Lucide Vue Next                    |
| Dates      | date-fns                           |
| Toasts     | vue-toastification                 |
| Build      | Vite 5                             |

## Project Structure

```
src/
├── assets/styles/
│   └── main.css           # Design system (CSS variables, components)
├── components/
│   ├── layout/
│   │   └── AppLayout.vue  # Sidebar, topbar, SSE wiring
│   └── common/
│       ├── StatCard.vue
│       └── ConfidenceBar.vue
├── views/
│   ├── LoginView.vue
│   ├── DashboardView.vue       # KPIs, trend chart, live feed
│   ├── IncidentsView.vue       # Paginated table, filters
│   ├── IncidentDetailView.vue  # Status flow, notes, alert log
│   ├── CamerasView.vue         # Camera grid + CRUD modal
│   ├── CameraDetailView.vue    # Live stream + incidents
│   ├── AlertsView.vue          # Alert log + SSE ticker
│   ├── HistoryView.vue         # Video chunk search + player
│   ├── StatisticsView.vue      # Charts, breakdown, heatmap
│   └── SettingsView.vue        # Users, change password
├── stores/
│   ├── auth.js            # JWT tokens (persisted)
│   ├── incidents.js       # Incidents + live SSE feed
│   └── cameras.js         # Camera list
├── services/
│   ├── api.js             # Axios instance + interceptors
│   ├── endpoints.js       # All API call functions
│   └── sse.js             # ReconnectingEventSource
└── router/index.js        # Routes + auth guards
```

## Quick Start

```bash
npm install
npm run dev         # Vite dev server on :5173
npm run build       # Production build → dist/
npm run preview     # Preview production build
```

### Environment Variables
Create `.env.local`:
```
VITE_API_URL=http://localhost:8080/api
```

For production, the Nginx config proxies `/api/` to the backend automatically.

## Real-time Features

The dashboard uses **Server-Sent Events** for live updates:

- **Incident stream** (`/api/incidents/stream`) — pushes every new CV detection
- **Alert stream** (`/api/alerts/stream`) — pushes every harassment alert dispatch

The `ReconnectingEventSource` service auto-reconnects with exponential backoff.

## Roles & Access Control

| Role                | Access                                            |
|---------------------|---------------------------------------------------|
| `ANALYST`           | View incidents, cameras, statistics, history      |
| `SECURITY_PERSONNEL`| + Create/edit cameras, acknowledge incidents      |
| `ADMIN`             | + User management, settings, delete cameras       |

## Building & Deploying

### Docker
```bash
docker build -t guardian-frontend .
docker run -p 80:80 guardian-frontend
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/guardian-frontend .
gcloud run deploy guardian-frontend \
  --image gcr.io/YOUR_PROJECT/guardian-frontend \
  --region us-central1 \
  --allow-unauthenticated \
  --port 80
```

### Firebase Hosting (alternative)
```bash
npm run build
firebase deploy --only hosting
```

## Design System

Dark industrial theme based on CSS custom properties:

```css
--bg-base:        #0a0c10    /* Page background  */
--bg-surface:     #111318    /* Cards, sidebar    */
--accent:         #f59e0b    /* Primary amber     */
--red:            #ef4444    /* Alerts, critical  */
--green:          #22c55e    /* Online, resolved  */
--font-mono:      'Space Mono'
--font-sans:      'DM Sans'
```
