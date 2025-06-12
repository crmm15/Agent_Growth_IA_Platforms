import numpy as np
from scipy.stats import norm
import math


def payoff_call(S: np.ndarray, K: float, premium: float) -> np.ndarray:
    return np.maximum(S - K, 0) - premium


def payoff_put(S: np.ndarray, K: float, premium: float) -> np.ndarray:
    return np.maximum(K - S, 0) - premium


def calc_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call") -> float:
    """Calcula delta de Black-Scholes para CALL o PUT."""
    if T <= 0 or sigma <= 0:
        return float('nan')
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    return norm.cdf(d1) if option_type.lower() == "call" else norm.cdf(d1) - 1