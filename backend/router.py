from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math

class VRPRouter:
    def __init__(self, num_vehicles, vehicle_capacities):
        self.num_vehicles = num_vehicles
        self.vehicle_capacities = vehicle_capacities

    def calculate_distance(self, p1, p2):
        # Euclidean distance for synthetic graph. Can be swapped with real API.
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def create_data_model(self, locations, demands, time_windows, vehicle_starts):
        """
        locations: list of (x, y) coords.
        demands: list of integers. +ve for pickup (Source), -ve for dropoff (Sink).
        time_windows: list of (start, end) times.
        vehicle_starts: list of indices in 'locations' where vehicles currently are.
        """
        data = {}
        # Calculate distance matrix
        num_locations = len(locations)
        matrix = [[0] * num_locations for _ in range(num_locations)]
        for i in range(num_locations):
            for j in range(num_locations):
                matrix[i][j] = int(self.calculate_distance(locations[i], locations[j]) * 10) # scale to int

        data['distance_matrix'] = matrix
        data['time_windows'] = time_windows
        data['demands'] = demands
        data['vehicle_capacities'] = self.vehicle_capacities
        data['num_vehicles'] = self.num_vehicles
        data['starts'] = vehicle_starts
        data['ends'] = vehicle_starts # For now, end where they start or use dummy node
        
        return data

    def solve(self, data):
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['starts'],
            data['ends']
        )
        routing = pywrapcp.RoutingModel(manager)

        # Distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Demand callback
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )

        # Time Windows
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_index,
            30,  # allow waiting time
            300,  # maximum time per vehicle
            False,  # Don't force start cumul to zero
            'Time'
        )
        time_dimension = routing.GetDimensionOrDie('Time')
        for location_idx, time_window in enumerate(data['time_windows']):
            if location_idx in data['starts'] or location_idx in data['ends']:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            return self.parse_solution(manager, routing, solution, data)
        return None

    def parse_solution(self, manager, routing, solution, data):
        routes = []
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append(node_index)
                index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
            routes.append(route)
        return routes

if __name__ == "__main__":
    router = VRPRouter(num_vehicles=2, vehicle_capacities=[15, 15])
    locations = [(0,0), (0,10), (10,10), (10,0)] # 0: driver1 start, 1: source, 2: sink, 3: driver2 start
    demands = [0, 10, -10, 0]
    time_windows = [(0, 100), (0, 20), (0, 50), (0, 100)]
    vehicle_starts = [0, 3]
    
    data = router.create_data_model(locations, demands, time_windows, vehicle_starts)
    routes = router.solve(data)
    print("Calculated Routes:", routes)
