import random
from datetime import datetime

class AgentSupervisor:
    def __init__(self):
        self.log_history = []

    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_history.insert(0, f"[{timestamp}] {message}")
        if len(self.log_history) > 50:
            self.log_history.pop()

    def analyze_routing(self, sinks_per_prod, routes, ghost_routes, stores):
        insights_generated = 0
        
        # 1. Product-Level Alerts
        for prod, sinks in sinks_per_prod.items():
            for s in sinks:
                stock = stores[s]['products'][prod]['stock']
                self.add_log(f"ALERT: {s.replace('Store_', '')} '{prod}' critically low ({stock} units).")
                insights_generated += 1

        # 2. Predictive Ghost Routes
        if ghost_routes:
            self.add_log(f"ANTICIPATION: Calculated {len(ghost_routes)} ghost routes for nodes nearing critical stock.")
            insights_generated += 1

        # 3. Active Dispatch
        if routes:
            self.add_log(f"DISPATCH: Solidified inter-loping routes. {len(routes)} agents dispatched for immediate rebalancing.")
            insights_generated += 1
            
        if insights_generated == 0:
            self.add_log("NETWORK STABLE: All product categories across nodes are within safe probability margins.")
            
        return self.log_history
