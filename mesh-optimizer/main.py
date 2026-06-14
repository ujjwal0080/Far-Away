import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

app = FastAPI(title="Dynamic Dark Store Mesh Optimizer Engine")

# --- DATA MODELS ---
class Node(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    current_stock: int
    predicted_demand_rate: float # Used for Bernoulli/Poisson prediction

class FleetDriver(BaseModel):
    id: int
    max_capacity: int
    start_node_id: int

class OptimizationRequest(BaseModel):
    nodes: List[Node]
    drivers: List[FleetDriver]
    time_windows: List[List[int]] # [Start_Mins, End_Mins] for each node

# --- CORE CS LAYER: GRAPH DISTANCE MATRIX COMPUTER ---
def compute_euclidean_distance_matrix(nodes: List[Node]):
    """
    Generates a distance matrix from geographical coordinates.
    In production, swap this Strategy pattern out for an OSRM/Google Maps API.
    """
    num_nodes = len(nodes)
    matrix = np.zeros((num_nodes, num_nodes), dtype=int)
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i == j:
                matrix[i][j] = 0
            else:
                # Scale coordinate distance to simulate travel time in minutes
                dist = np.sqrt((nodes[i].latitude - nodes[j].latitude)**2 + 
                               (nodes[i].longitude - nodes[j].longitude)**2)
                matrix[i][j] = int(dist * 100) # travel cost/time proxy
    return matrix.tolist()

# --- STATISTICS LAYER: BERNOULLI SUPPLY DISRUPTION RISK ---
def predict_stockout_risk(predicted_demand_rate: float, current_stock: int) -> bool:
    """
    Uses a Bernoulli trial simulation to determine if a dark store node 
    is at immediate risk of a stockout within the next 15-minute window.
    """
    # Probability of a critical batch order spike occurring based on statistical rate
    prob_spike = 1.0 - np.exp(-predicted_demand_rate)
    # Simulate a trial
    trial = np.random.binomial(1, prob_spike)
    if trial == 1 and current_stock < 5:
        return True # Critical intervention required
    return False

# --- ALGORITHMIC ROUTING LAYER (OR-TOOLS VRP-TW) ---
def create_routing_solution(data_matrix, time_windows, drivers, num_nodes):
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(num_nodes, len(drivers), 0)
    routing = pywrapcp.RoutingModel(manager)

    # 1. Create and register a transit callback (Travel Time/Cost)
    def transit_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(transit_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 2. Add Time Windows Constraint
    time_dimension_name = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30,   # allow waiting time at nodes
        180,  # maximum total travel time per vehicle loop (3 hours)
        False, # Don't force start cumul to zero
        time_dimension_name)
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)

    # Add time window constraints for each location except the central depot.
    for location_idx, time_window in enumerate(time_windows):
        if location_idx == 0:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    # 3. Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)
    
    if not solution:
        return None

    # Parse route results
    routes = {}
    for vehicle_id in range(len(drivers)):
        index = routing.Start(vehicle_id)
        route_plan = []
        while not routing.IsEnd(index):
            node_idx = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            route_plan.append({
                "node_id": node_idx,
                "arrival_time_min": solution.Min(time_var)
            })
            index = solution.Value(routing.NextVar(index))
        routes[f"driver_{vehicle_id}"] = route_plan

    return routes

# --- API ENDPOINTS ---
@app.post("/api/v1/optimize-mesh")
async def optimize_mesh(payload: OptimizationRequest):
    if not payload.nodes or not payload.drivers:
        raise HTTPException(status_code=400, detail="Missing required layout nodes or driver data fleets.")

    # Step 1: Compute Graph Adjacency / Distance Matrix
    distance_matrix = compute_euclidean_distance_matrix(payload.nodes)
    
    # Step 2: Check for Critical Node Stockout Alerts via Bernoulli Layer
    alerts = []
    for node in payload.nodes:
        if predict_stockout_risk(node.predicted_demand_rate, node.current_stock):
            alerts.append({
                "node_id": node.id,
                "status": "CRITICAL_STOCKOUT_RISK",
                "message": f"High probability demand spike predicted at {node.name}. Rebalancing required."
            })

    # Step 3: Solve the Vehicle Routing Problem Matrix
    optimized_routes = create_routing_solution(
        distance_matrix, 
        payload.time_windows, 
        payload.drivers, 
        len(payload.nodes)
    )

    if not optimized_routes:
        raise HTTPException(status_code=500, detail="Could not compute an optimal routing mesh matching those constraint windows.")

    return {
        "status": "SUCCESS",
        "stockout_alerts": alerts,
        "optimized_routing_mesh": optimized_routes
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)