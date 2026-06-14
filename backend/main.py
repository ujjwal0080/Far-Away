from fastapi import FastAPI, WebSocket
import asyncio
import json
import random
import numpy as np
from predictive_layer import DemandPredictor
from router import VRPRouter
from agentic_layer import AgentSupervisor

app = FastAPI(title="Dark Store Optimizer API")
connected_clients = set()

def create_products(snack_stock, snack_l, milk_stock, milk_l, bev_stock, bev_l):
    return {
        "Match Day Snacks": {"stock": snack_stock, "lambda": snack_l},
        "Daily Essentials": {"stock": milk_stock, "lambda": milk_l},
        "Cold Beverages": {"stock": bev_stock, "lambda": bev_l}
    }

STORES = {
    "Store_Indiranagar": {"coords": [12.9784, 77.6408], "products": create_products(45, 12, 100, 5, 80, 8)},
    "Store_Koramangala": {"coords": [12.9279, 77.6271], "products": create_products(5, 25, 60, 4, 30, 15)},
    "Store_HSR_Layout": {"coords": [12.9081, 77.6476], "products": create_products(60, 10, 80, 6, 40, 10)},
    "Store_Whitefield": {"coords": [12.9698, 77.7499], "products": create_products(100, 5, 120, 2, 90, 4)},
    "Store_BTM_Layout": {"coords": [12.9166, 77.6101], "products": create_products(15, 18, 50, 5, 25, 12)},
    "Store_Jayanagar": {"coords": [12.9299, 77.5826], "products": create_products(80, 8, 90, 4, 100, 6)},
    "Store_Malleshwaram": {"coords": [13.0031, 77.5643], "products": create_products(12, 15, 70, 4, 60, 7)},
    "Store_Marathahalli": {"coords": [12.9569, 77.7011], "products": create_products(25, 20, 45, 8, 20, 18)},
    "Store_Hebbal": {"coords": [13.0354, 77.5988], "products": create_products(50, 10, 110, 3, 70, 5)},
    "Store_Bellandur": {"coords": [12.9304, 77.6784], "products": create_products(8, 22, 30, 10, 15, 20)},
    "Store_Electronic_City": {"coords": [12.8399, 77.6770], "products": create_products(120, 4, 150, 2, 140, 3)}
}

DRIVERS = [
    {"id": "D1", "coords": [12.9500, 77.6300], "capacity": 20, "inventory": 0},
    {"id": "D2", "coords": [12.9800, 77.7000], "capacity": 20, "inventory": 0},
    {"id": "D3", "coords": [12.9100, 77.6000], "capacity": 20, "inventory": 0},
    {"id": "D4", "coords": [13.0100, 77.5800], "capacity": 20, "inventory": 0},
    {"id": "D5", "coords": [12.8500, 77.6700], "capacity": 20, "inventory": 0},
]

predictor = DemandPredictor(critical_threshold=0.80)
router = VRPRouter(num_vehicles=len(DRIVERS), vehicle_capacities=[d["capacity"] for d in DRIVERS])
ai_supervisor = AgentSupervisor()

async def broadcast_state(state: dict):
    if not connected_clients: return
    msg = json.dumps(state)
    for c in connected_clients:
        try: await c.send_text(msg)
        except Exception: pass

async def run_simulation_loop():
    print("Starting simulation loop...")
    while True:
        nodes_status = {}
        sinks_per_prod = {p: [] for p in ["Match Day Snacks", "Daily Essentials", "Cold Beverages"]}
        sources_per_prod = {p: [] for p in ["Match Day Snacks", "Daily Essentials", "Cold Beverages"]}
        ghosts_per_prod = {p: [] for p in ["Match Day Snacks", "Daily Essentials", "Cold Beverages"]}

        for store_id, data in STORES.items():
            store_status = "HEALTHY"
            max_prob = 0.0
            
            for prod_name, prod_data in data["products"].items():
                tick_lambda = prod_data["lambda"] / 30.0 
                orders_this_tick = np.random.poisson(tick_lambda)
                if orders_this_tick > 0:
                    prod_data["stock"] = max(0, prod_data["stock"] - orders_this_tick)
                    
                eval_res = predictor.evaluate_node(store_id, prod_data["lambda"], prod_data["stock"])
                prob = eval_res["stockout_prob"]
                max_prob = max(max_prob, prob)
                
                if prob >= 0.80:
                    store_status = "SINK"
                    sinks_per_prod[prod_name].append(store_id)
                elif prob >= 0.50 and prob < 0.80:
                    ghosts_per_prod[prod_name].append(store_id)
                elif eval_res["status"] == "SOURCE" and store_status != "SINK":
                    sources_per_prod[prod_name].append(store_id)

            nodes_status[store_id] = {
                "status": store_status,
                "products": data["products"],
                "coords": data["coords"],
                "stockout_prob": max_prob
            }

        routes = []
        ghost_routes = []
        
        # Calculate routes for whichever product has sinks
        for prod in ["Match Day Snacks", "Daily Essentials", "Cold Beverages"]:
            sinks = sinks_per_prod[prod]
            sources = sources_per_prod[prod]
            ghosts = ghosts_per_prod[prod]
            
            # Active Routes
            if sinks and sources:
                locs = [d["coords"] for d in DRIVERS]
                dems = [0 for _ in DRIVERS]
                tws = [(0, 1000) for _ in DRIVERS]
                
                for s in sources[:3]: # limit to avoid over-routing
                    locs.append(STORES[s]["coords"])
                    dems.append(20) 
                    tws.append((0, 50))
                for s in sinks[:3]:
                    locs.append(STORES[s]["coords"])
                    dems.append(-20) 
                    tws.append((0, 30)) 
                    
                v_starts = list(range(len(DRIVERS)))
                try:
                    model = router.create_data_model(locs, dems, tws, v_starts)
                    raw_routes = router.solve(model)
                    if raw_routes:
                        for route in raw_routes:
                            if len(route) > 2: 
                                routes.append([locs[n] for n in route])
                                # Simulate stock transfer
                                try:
                                    src_idx = route[1] - len(DRIVERS)
                                    snk_idx = route[2] - len(DRIVERS)
                                    src_store = sources[src_idx]
                                    snk_store = sinks[snk_idx]
                                    STORES[src_store]["products"][prod]["stock"] = max(0, STORES[src_store]["products"][prod]["stock"] - 15)
                                    STORES[snk_store]["products"][prod]["stock"] += 15
                                except Exception: pass
                except Exception: pass
                
            # Ghost Routes (Anticipatory)
            if ghosts and sources:
                for g in ghosts[:2]:
                    ghost_routes.append([DRIVERS[random.randint(0, len(DRIVERS)-1)]["coords"], STORES[g]["coords"]])

        ai_insights = ai_supervisor.analyze_routing(sinks_per_prod, routes, ghost_routes, STORES)

        state = {
            "stores": nodes_status,
            "drivers": DRIVERS,
            "routes": routes,
            "ghost_routes": ghost_routes,
            "insights": ai_insights
        }
        await broadcast_state(state)
        await asyncio.sleep(8)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_simulation_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    await websocket.send_text(json.dumps({
        "stores": {k: {"status": "HEALTHY", "products": v["products"], "coords": v["coords"], "stockout_prob": 0.0} for k,v in STORES.items()},
        "drivers": DRIVERS, "routes": [], "ghost_routes": [], "insights": ["AI: Initializing..."]
    }))
    try:
        while True: await websocket.receive_text()
    except Exception: pass
    finally: connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
