import numpy as np
import math
from scipy.stats import norm

def calcular_delta_call_put(S, K, T, r, sigma, tipo="CALL"):
    try:
        d1 = (math.log(S/K) + (r+0.5*sigma**2)*T)/(sigma*math.sqrt(T))
        return norm.cdf(d1) if tipo.upper()=="CALL" else norm.cdf(d1)-1
    except:
        return None


def calcular_payoff_call(S, K, premium):
    return np.maximum(S-K,0) - premium


def calcular_payoff_put(S, K, premium):
    return np.maximum(K-S,0) - premium