import numpy as np
from scipy.stats import poisson, bernoulli

class DemandPredictor:
    def __init__(self, critical_threshold: float = 0.85):
        """
        Initialize the Demand Predictor.
        :param critical_threshold: The probability threshold (0 to 1) to flag a stockout risk.
        """
        self.critical_threshold = critical_threshold

    def calculate_stockout_probability(self, lambda_rate: float, current_stock: int) -> float:
        """
        Calculate the probability that demand exceeds current stock in a given time window.
        Uses the Poisson distribution.
        
        :param lambda_rate: Expected average demand in the time window.
        :param current_stock: Current inventory level.
        :return: Probability (0 to 1) of a stockout.
        """
        # Probability of getting EXACTLY k orders is poisson.pmf(k, lambda_rate)
        # Probability of getting <= current_stock orders is poisson.cdf(current_stock, lambda_rate)
        # Probability of stockout (demand > current_stock) is 1 - CDF
        prob_no_stockout = poisson.cdf(current_stock, lambda_rate)
        prob_stockout = 1.0 - prob_no_stockout
        return prob_stockout

    def is_immediate_risk(self, risk_probability: float) -> bool:
        """
        Evaluate an immediate binary risk using a Bernoulli trial.
        
        :param risk_probability: The underlying probability of the risk occurring.
        :return: True if the trial results in the risk event happening, False otherwise.
        """
        # Bernoulli trial gives 1 with probability 'risk_probability', 0 otherwise
        trial_result = bernoulli.rvs(risk_probability)
        return bool(trial_result == 1)

    def evaluate_node(self, node_id: str, lambda_rate: float, current_stock: int) -> dict:
        """
        Evaluates a node to determine its status and returns the mathematical probabilities.
        """
        prob_stockout = self.calculate_stockout_probability(lambda_rate, current_stock)
        
        status = "HEALTHY"
        if prob_stockout >= self.critical_threshold:
            status = "SINK"
        elif current_stock > lambda_rate * 3 and prob_stockout < 0.1:
            status = "SOURCE"
            
        return {
            "status": status,
            "stockout_prob": prob_stockout
        }

# Example usage
if __name__ == "__main__":
    predictor = DemandPredictor(critical_threshold=0.85)
    
    # Store A: High demand during match, low stock
    store_a_lambda = 25.0  # 25 orders expected
    store_a_stock = 20     # only 20 units left
    
    prob_a = predictor.calculate_stockout_probability(store_a_lambda, store_a_stock)
    status_a = predictor.evaluate_node("Store_A", store_a_lambda, store_a_stock)
    print(f"Store A - Stockout Prob: {prob_a:.2f}, Status: {status_a}")
    
    # Store B: Idle store, high stock
    store_b_lambda = 5.0
    store_b_stock = 40
    
    prob_b = predictor.calculate_stockout_probability(store_b_lambda, store_b_stock)
    status_b = predictor.evaluate_node("Store_B", store_b_lambda, store_b_stock)
    print(f"Store B - Stockout Prob: {prob_b:.2f}, Status: {status_b}")
