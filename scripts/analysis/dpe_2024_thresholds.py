"""Official DPE class thresholds of the order of 25 March 2024 (JORF 20/04/2024, text 15).

Only what the small-dwelling relabelling needs: the E/F and F/G bounds
(CEP in kWh/m2/yr of primary energy, EGES in kgCO2eq/m2/yr), for a
reference surface of 8 to 40 m2 below 800 m altitude (table 1.2.2.1),
linearly interpolated between whole surfaces. Above 40 m2 the 2021
thresholds are unchanged (CEP_e 330, CEP_f 420, EGES_e 70, EGES_f 100).
Below 8 m2 the 8 m2 row is used.
"""
import numpy as np

# S_REF: (CEP_e, EGES_e, CEP_f, EGES_f)
SMALL = {
    8: (622, 90, 739, 122), 9: (574, 87, 685, 118), 10: (533, 84, 640, 115), 11: (503, 82, 607, 113),
    12: (478, 81, 578, 111), 13: (456, 79, 554, 110), 14: (437, 78, 532, 108), 15: (421, 76, 514, 107),
    16: (412, 76, 504, 106), 17: (404, 75, 496, 105), 18: (397, 75, 489, 105), 19: (390, 74, 482, 105),
    20: (385, 74, 476, 104), 21: (380, 74, 471, 104), 22: (375, 73, 466, 103), 23: (371, 73, 462, 103),
    24: (367, 73, 458, 103), 25: (363, 73, 454, 103), 26: (360, 72, 451, 103), 27: (357, 72, 447, 102),
    28: (354, 72, 444, 102), 29: (351, 72, 442, 102), 30: (349, 72, 439, 102), 31: (346, 72, 437, 102),
    32: (344, 71, 434, 101), 33: (342, 71, 432, 101), 34: (340, 71, 430, 101), 35: (338, 71, 428, 101),
    36: (337, 71, 427, 101), 37: (335, 71, 425, 101), 38: (333, 71, 423, 101), 39: (332, 71, 422, 101),
    40: (330, 70, 420, 100),
}
STANDARD = (330, 70, 420, 100)
_S = np.array(sorted(SMALL))
_T = np.array([SMALL[s] for s in _S], dtype=float)


def fg_bounds(surface: np.ndarray) -> np.ndarray:
    """(CEP_e, EGES_e) for each surface: the bound from which a dwelling is F or G."""
    s = np.clip(np.asarray(surface, dtype=float), 8, 40)
    cep_e = np.interp(s, _S, _T[:, 0])
    eges_e = np.interp(s, _S, _T[:, 1])
    big = np.asarray(surface, dtype=float) > 40
    cep_e[big], eges_e[big] = STANDARD[0], STANDARD[1]
    return np.column_stack([cep_e, eges_e])


def is_fg_2024(surface, cep, eges) -> np.ndarray:
    """F or G under the 2024 thresholds (values rounded down, as the order says)."""
    b = fg_bounds(surface)
    return (np.floor(np.asarray(cep, dtype=float)) >= b[:, 0]) | (np.floor(np.asarray(eges, dtype=float)) >= b[:, 1])


def is_fg_2021(cep, eges) -> np.ndarray:
    return (np.floor(np.asarray(cep, dtype=float)) >= STANDARD[0]) | (np.floor(np.asarray(eges, dtype=float)) >= STANDARD[1])
