<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React 19" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/OR--Tools-VRP-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="OR-Tools" />
  <img src="https://img.shields.io/badge/WebSocket-Realtime-8b5cf6?style=for-the-badge&logo=socketdotio&logoColor=white" alt="WebSocket" />
  <img src="https://img.shields.io/badge/Leaflet-Maps-199900?style=for-the-badge&logo=leaflet&logoColor=white" alt="Leaflet" />
</p>

# 🔮 FarAway — Dark Store Mesh Optimizer

> **Real-time supply chain intelligence for hyperlocal delivery networks.**  
> An interactive simulation platform that predicts stockouts using Poisson statistics, rebalances inventory across a mesh of dark stores via Vehicle Routing Problem (VRP) optimization, and visualizes the entire network as a living, breathing Voronoi tessellation on a map of Bangalore.

---

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [How It Works](#how-it-works)
  - [Predictive Layer (Poisson Model)](#predictive-layer-poisson-model)
  - [Routing Layer (OR-Tools VRP)](#routing-layer-or-tools-vrp)
  - [Agentic Supervision Layer](#agentic-supervision-layer)
  - [Interactive Scenarios](#interactive-scenarios)
- [Dashboard Guide](#dashboard-guide)
- [Mesh Optimizer API (Standalone)](#mesh-optimizer-api-standalone)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

FarAway simulates a network of **11 dark stores** spread across Bangalore, each carrying three product categories (**Match Day Snacks**, **Daily Essentials**, **Cold Beverages**). Orders arrive stochastically following a Poisson process. The system continuously:

1. **Predicts** which stores are about to stockout (within 15- and 30-minute horizons)
2. **Classifies** each store as a **Source** (surplus), **Sink** (critical), or **Anticipatory Risk** (ghost pre-crisis)
3. **Solves** a Capacitated Vehicle Routing Problem with Time Windows (CVRP-TW) to dispatch 5 fleet drivers for inter-store rebalancing
4. **Broadcasts** the entire network state to the dashboard over WebSocket at 4-second ticks

The frontend renders all of this on a dark-themed Leaflet map with **Voronoi tessellation** that colors zones by risk, animated routing polylines, and a per-node probability inspector powered by live Poisson PMF charts.

---

## Key Features

| Feature | Description |
|---|---|
| **📊 Poisson Stockout Prediction** | Dual-horizon model (15-min & 30-min) using `scipy.stats.poisson` CDF to calculate real-time stockout probabilities |
| **🗺️ Voronoi Service Zones** | Turf.js generates Voronoi polygons around each store, color-coded by risk level (green → amber → red) |
| **🚛 VRP-TW Routing** | Google OR-Tools solves a multi-vehicle capacitated routing problem with time windows to find optimal rebalancing paths |
| **👻 Ghost Routes** | Anticipatory pre-dispatch routes to stores predicted to enter crisis within 30 minutes (dashed amber lines) |
| **🏏 Scenario Injection** | Toggle real-world scenarios — **Cricket Match** (3.5× snack demand), **Monsoon** (1.8× all demand), **Festival** (2.5× essentials) |
| **🔥 Manual Demand Spikes** | Click any store to inject a 4× hyper-spike and watch the system react in real time |
| **🧠 Cognitive Engine Feed** | An agentic supervisor layer generates natural-language operational insights and alerts |
| **📈 Live PMF Inspector** | Click any store node to view its Poisson probability mass function chart, current stock, and λ arrival rate |
| **⚡ WebSocket Real-Time Sync** | Bidirectional WebSocket between backend simulation and React dashboard for instant state updates |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Leaflet Map │  │ Voronoi Mesh │  │ Recharts Inspector │  │
│  │ + Markers   │  │ (Turf.js)    │  │ (Poisson PMF)      │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬───────────┘  │
│         └────────────────┼───────────────────┘              │
│                          │  WebSocket (ws://localhost:8000)  │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│  ┌──────────────────┐  ┌─┴────────────────┐  ┌───────────┐  │
│  │ Predictive Layer │  │ Simulation Loop  │  │ Agentic   │  │
│  │ (Poisson CDF)    │──│ (4s tick cycle)  │──│ Supervisor│  │
│  └──────────────────┘  └──────────────────┘  └───────────┘  │
│  ┌──────────────────┐                                        │
│  │ VRP Router       │  ← Google OR-Tools CVRP-TW Solver      │
│  │ (ortools)        │                                        │
│  └──────────────────┘                                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              MESH OPTIMIZER (Standalone API)                  │
│  Euclidean distance matrix + Bernoulli stockout risk +        │
│  OR-Tools VRP-TW solver exposed as REST endpoint              │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | UI framework with hooks and functional components |
| **Vite 8** | Lightning-fast dev server and build tooling |
| **Leaflet + react-leaflet** | Interactive map rendering with dark CARTO tiles |
| **Turf.js** | Geospatial analysis — Voronoi tessellation of service zones |
| **Recharts** | Data visualization — Poisson PMF area charts |
| **Lucide React** | Icon system for the dashboard UI |

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | Async Python web framework with WebSocket support |
| **Google OR-Tools** | Industrial-grade VRP solver (CVRP-TW) |
| **NumPy** | Poisson random variate generation for order simulation |
| **SciPy** | `scipy.stats.poisson` CDF for stockout probability |
| **Uvicorn** | ASGI server for production-grade async serving |

---

## Project Structure

```
FarAway/
├── backend/
│   ├── main.py               # FastAPI app, WebSocket endpoint, simulation loop
│   ├── predictive_layer.py   # Poisson CDF-based dual-horizon stockout predictor
│   ├── router.py             # OR-Tools VRP-TW solver wrapper (VRPRouter class)
│   ├── agentic_layer.py      # AI supervisor — generates operational insights
│   ├── simulation.py         # Standalone simulation runner (dev/testing)
│   └── requirements.txt      # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main dashboard — map, sidebar, inspector panel
│   │   ├── main.jsx          # React entry point
│   │   ├── index.css         # Design system — dark theme, glassmorphism, animations
│   │   └── App.css           # Vite scaffold styles (unused)
│   ├── public/
│   │   ├── favicon.svg       # App icon
│   │   └── icons.svg         # Icon sprites
│   ├── index.html            # HTML shell
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Vite configuration
│
├── mesh-optimizer/
│   └── main.py               # Standalone REST API for mesh optimization requests
│
├── .gitignore
└── README.md                 # ← You are here
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Git**

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the backend server
python main.py
```

The backend will start on **`http://localhost:8000`** and begin the simulation loop immediately. The WebSocket endpoint is available at **`ws://localhost:8000/ws`**.

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start the development server
npm run dev
```

The frontend will start on **`http://localhost:5173`** (default Vite port). Open this URL in your browser to view the dashboard.

> **Note:** The frontend connects to the backend via WebSocket at `ws://localhost:8000/ws`. Make sure the backend is running first.

---

## How It Works

### Predictive Layer (Poisson Model)

The [`DemandPredictor`](backend/predictive_layer.py) class models order arrivals as a **Poisson process**. For each store and product category:

```
P(stockout) = 1 - CDF_Poisson(current_stock, λ_scaled)
```

Where `λ_scaled = hourly_lambda × (lookahead_minutes / 60)`

Two prediction horizons are evaluated every tick:
- **15-minute window** → If P(stockout) ≥ 0.80, the store is classified as a **SINK** (emergency)
- **30-minute window** → If P(stockout) ≥ 0.50, the store enters **ANTICIPATORY_RISK** (ghost pre-crisis)
- **Source condition** → Stock > (λ × 0.5) and 30-min risk < 0.10

### Routing Layer (OR-Tools VRP)

The [`VRPRouter`](backend/router.py) wraps Google's OR-Tools to solve a **Capacitated Vehicle Routing Problem with Time Windows (CVRP-TW)**:

- **5 delivery drivers** with 20-unit capacity each
- **Sources** contribute positive demand (pickup), **Sinks** contribute negative demand (dropoff)
- **Time windows** enforce urgency — sinks have tighter windows (0–30 min) vs sources (0–50 min)
- Uses `PATH_CHEAPEST_ARC` first solution strategy for fast convergence

When a solution is found, **15 units** are transferred from source to sink, and routes are broadcast as coordinate arrays for polyline rendering.

### Agentic Supervision Layer

The [`AgentSupervisor`](backend/agentic_layer.py) acts as a cognitive monitor:

- Generates **product-level stockout alerts** with store name and remaining units
- Reports **anticipatory ghost route** deployments
- Logs **active dispatch events** when VRP routes are executing
- Falls back to **"NETWORK NOMINAL"** when all nodes are healthy
- Maintains a rolling 50-entry log with timestamps

### Interactive Scenarios

Users can inject real-world disruptions via the dashboard sidebar:

| Scenario | Effect | Multiplier |
|---|---|---|
| 🏏 **Cricket Match** | Snack demand surges near stadium zones | 3.5× on Match Day Snacks |
| 🌧️ **Monsoon** | City-wide delivery slowdown, all orders spike | 1.8× on all categories |
| 🎉 **Festival** | Essentials demand spikes for celebrations | 2.5× on Daily Essentials |
| 🔥 **Manual Spike** | Per-store 4× hyper-spike on all products | 4.0× on selected store |

---

## Dashboard Guide

The dashboard is split into three main areas:

### Left Sidebar — Control Panel
- **Scenario Presets** — Toggle macro-level disruption scenarios (Cricket, Monsoon)
- **Demand Spike Grid** — Click individual stores to inject/remove a 4× demand spike
- **Cognitive Engine Feed** — Live AI-generated insights and alerts with timestamps
- **Reset Button** — Restore all stores to baseline stock levels and clear all modifiers

### Center — Live Map
- **Store Markers** — Green (healthy), red pulsing (sink/critical), purple (source/surplus)
- **Voronoi Zones** — Color-coded service area polygons that shift from green → amber → red based on risk
- **Active Routes** — Purple dashed lines showing VRP-solved rebalancing paths
- **Ghost Routes** — Amber dashed lines showing anticipatory pre-dispatch paths
- **Driver Markers** — White dots with purple borders representing fleet agents

### Right Panel — Node Inspector (click any store)
- **Product Tabs** — Switch between Match Day Snacks, Daily Essentials, Cold Beverages
- **Stock & Lambda** — Current inventory count and Poisson arrival rate
- **Poisson PMF Chart** — Live probability distribution curve with gradient fill
- **Risk Percentage** — Real-time stockout probability for the selected product

---

## Mesh Optimizer API (Standalone)

The [`mesh-optimizer/`](mesh-optimizer/) directory contains an independent FastAPI service that exposes the optimization engine as a REST API.

### Endpoint

```
POST /api/v1/optimize-mesh
```

### Request Body

```json
{
  "nodes": [
    {
      "id": 0,
      "name": "Warehouse Central",
      "latitude": 12.9716,
      "longitude": 77.5946,
      "current_stock": 100,
      "predicted_demand_rate": 0.3
    }
  ],
  "drivers": [
    {
      "id": 0,
      "max_capacity": 20,
      "start_node_id": 0
    }
  ],
  "time_windows": [[0, 60], [0, 30]]
}
```

### Response

```json
{
  "status": "SUCCESS",
  "stockout_alerts": [
    {
      "node_id": 3,
      "status": "CRITICAL_STOCKOUT_RISK",
      "message": "High probability demand spike predicted at Store HSR. Rebalancing required."
    }
  ],
  "optimized_routing_mesh": {
    "driver_0": [
      { "node_id": 0, "arrival_time_min": 0 },
      { "node_id": 3, "arrival_time_min": 12 }
    ]
  }
}
```

### Run Standalone

```bash
cd mesh-optimizer
pip install fastapi uvicorn ortools numpy pydantic
python main.py
# API available at http://localhost:8000/docs (Swagger UI)
```

---

## Configuration

### Backend Parameters

| Parameter | Location | Default | Description |
|---|---|---|---|
| `critical_threshold` | `main.py` | `0.80` | Poisson probability threshold to trigger SINK classification |
| `lookahead_minutes` | `predictive_layer.py` | `15.0` / `30.0` | Dual-horizon prediction windows |
| `vehicle_capacities` | `main.py` | `20` per driver | Maximum units each driver can carry |
| `tick_interval` | `main.py` | `4 seconds` | Simulation broadcast frequency |
| Scenario multipliers | `main.py` | `3.5×` / `1.8×` / `2.5×` | Demand scaling factors per scenario |

### Store Network

The simulation models **11 dark stores** across Bangalore neighborhoods:

| Store | Coordinates | Notes |
|---|---|---|
| Indiranagar | 12.978, 77.641 | Moderate traffic |
| Koramangala | 12.928, 77.627 | High beverage demand |
| HSR Layout | 12.908, 77.648 | Balanced profile |
| Whitefield | 12.970, 77.750 | High surplus (source) |
| BTM Layout | 12.917, 77.610 | High demand, low stock |
| Jayanagar | 12.930, 77.583 | Moderate surplus |
| Malleshwaram | 13.003, 77.564 | Moderate demand |
| Marathahalli | 12.957, 77.701 | Very high beverage demand |
| Hebbal | 13.035, 77.599 | High essentials stock |
| Bellandur | 12.930, 77.678 | High risk zone |
| Electronic City | 12.840, 77.677 | Major source node |

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'feat: add your feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with 🧠 predictive intelligence and 🗺️ spatial algorithms
</p>
