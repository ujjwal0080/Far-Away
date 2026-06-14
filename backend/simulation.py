import asyncio
import random
from predictive_layer import DemandPredictor
from router import VRPRouter
from main import broadcast_state

# Zepto Mock Dark Stores in Bangalore
STORES = {
    "Store_Indiranagar": {"coords": [12.9784, 77.6408], "stock": 45, "lambda": 12},
    "Store_Koramangala": {"coords": [12.9279, 77.6271], "stock": 5, "lambda": 25}, # High risk
    "Store_HSR_Layout": {"coords": [12.9081, 77.6476], "stock": 60, "lambda": 10},
    "Store_Whitefield": {"coords": [12.9698, 77.7499], "stock": 100, "lambda": 5},  # Source
    "Store_BTM_Layout": {"coords": [12.9166, 77.6101], "stock": 15, "lambda": 18},
    "Store_Jayanagar": {"coords": [12.9299, 77.5826], "stock": 80, "lambda": 8},   # Source
    "Store_Malleshwaram": {"coords": [13.0031, 77.5643], "stock": 12, "lambda": 15},
    "Store_Marathahalli": {"coords": [12.9569, 77.7011], "stock": 25, "lambda": 20},
    "Store_Hebbal": {"coords": [13.0354, 77.5988], "stock": 50, "lambda": 10},
    "Store_Bellandur": {"coords": [12.9304, 77.6784], "stock": 8, "lambda": 22},   # High risk
    "Store_Electronic_City": {"coords": [12.8399, 77.6770], "stock": 120, "lambda": 4}, # Huge Source
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

async def run_simulation_loop():
    print("Starting simulation loop...")
    while True:
        # 1. Predict and Evaluate Nodes
        nodes_status = {}
        sinks = []
        sources = []
        
        for store_id, data in STORES.items():
            # Randomize lambda slightly for simulation
            current_lambda = data["lambda"] * random.uniform(0.8, 1.5)
            status = predictor.evaluate_node(store_id, current_lambda, data["stock"])
            nodes_status[store_id] = {
                "status": status,
                "stock": data["stock"],
                "coords": data["coords"]
            }
            if status == "SINK":
                sinks.append(store_id)
            elif status == "SOURCE":
                sources.append(store_id)
        
        # 2. Run Router if there are sinks and sources
        routes = []
        if sinks and sources:
            # Build OR-Tools data model
            locations = [d["coords"] for d in DRIVERS]
            demands = [0 for _ in DRIVERS]
            time_windows = [(0, 1000) for _ in DRIVERS]
            
            # Add sources
            for s in sources:
                locations.append(STORES[s]["coords"])
                demands.append(20) # Pickup 20 units
                time_windows.append((0, 50))
            
            # Add sinks
            for s in sinks:
                locations.append(STORES[s]["coords"])
                demands.append(-20) # Drop 20 units
                time_windows.append((0, 30)) # tighter time window
                
            vehicle_starts = list(range(len(DRIVERS)))
            
            try:
                model_data = router.create_data_model(locations, demands, time_windows, vehicle_starts)
                raw_routes = router.solve(model_data)
                if raw_routes:
                    routes = raw_routes
            except Exception as e:
                print(f"Routing failed: {e}")

        # 3. Broadcast State
        state = {
            "stores": nodes_status,
            "drivers": DRIVERS,
            "routes": routes
        }
        await broadcast_state(state)
        print(f"Broadcasted state: {len(sinks)} Sinks, {len(sources)} Sources")
        
        await asyncio.sleep(3) # Faster tick

if __name__ == "__main__":
    asyncio.run(run_simulation_loop())
