import numpy as np
from scipy.stats import norm
from utils.options import (
    calcular_delta_call_put,
    calcular_payoff_call,
    calcular_payoff_put,
)

def test_calcular_delta_call_put():
    S = 100
    K = 100
    T = 1
    r = 0.05
    sigma = 0.2

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    expected_call = norm.cdf(d1)
    expected_put = expected_call - 1
    assert np.isclose(calcular_delta_call_put(S, K, T, r, sigma, "CALL"), expected_call)
    assert np.isclose(calcular_delta_call_put(S, K, T, r, sigma, "PUT"), expected_put)

def test_calcular_payoff_call():
    S = np.array([90, 100, 110])
    result = calcular_payoff_call(S, 100, premium=5)
    np.testing.assert_array_equal(result, np.array([-5, -5, 5]))

def test_calcular_payoff_put():
    S = np.array([90, 100, 110])
    result = calcular_payoff_put(S, 100, premium=5)
    np.testing.assert_array_equal(result, np.array([5, -5, -5]))
