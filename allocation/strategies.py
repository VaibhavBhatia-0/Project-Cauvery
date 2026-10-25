"""Seven rules for sharing a fixed volume of water between four sectors.

Each strategy takes the water available (TMC) and an ordered dict of sector
demands (highest priority first) and returns {sector: allocation}. The
hedging rule may also hold water back, returned under the key 'reserve'.
All rules satisfy: 0 <= allocation <= demand and sum(allocation) <= supply.
"""

SECTORS = ('bengaluru', 'domestic', 'environment', 'agriculture')

# Relative importance used by the weighted-cuts and optimised rules.
WEIGHTS = {'bengaluru': 4, 'domestic': 3, 'environment': 2, 'agriculture': 1}
# Minimum share of demand guaranteed before agriculture (minimum-guarantee rule).
MINIMA = {'bengaluru': 0.85, 'domestic': 0.80, 'environment': 0.75, 'agriculture': 0.0}
# Share of supply kept back as carry-over storage when there is a shortage.
HEDGE_RESERVE = 0.10


def _fill_in_order(supply, wants, order):
    """Give each sector what it wants, in order, until the water runs out."""
    out = {}
    for k in order:
        out[k] = min(wants[k], supply)
        supply -= out[k]
    return out, supply


def _cut_until(supply, demand, shortfall, hi=1e6, iters=200):
    """Bisection on a cut level so that total demand - total shortfall == supply.

    `shortfall(level)` must grow monotonically with `level`.
    """
    total = sum(demand.values())
    lo = 0.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        if total - sum(shortfall(mid).values()) > supply:
            lo = mid
        else:
            hi = mid
    s = shortfall(hi)
    return {k: demand[k] - s[k] for k in demand}


def essential_priority(supply, demand):
    """Strict ladder: Bengaluru, then domestic, then environment, then farms."""
    return _fill_in_order(supply, demand, demand)[0]


def proportional(supply, demand):
    """Every sector gets the same percentage of what it asked for."""
    share = min(1.0, supply / sum(demand.values()))
    return {k: d * share for k, d in demand.items()}


def minimum_guarantee(supply, demand):
    """Guarantee minimum shares to essential uses, then agriculture, then top-ups."""
    floors = {k: demand[k] * MINIMA[k] for k in demand}
    first, left = _fill_in_order(supply, floors, demand)
    rest = {k: demand[k] - first[k] for k in demand}
    order = ['agriculture'] + [k for k in demand if k != 'agriculture']
    second, _ = _fill_in_order(left, rest, order)
    return {k: first[k] + second[k] for k in demand}


def weighted_cuts(supply, demand):
    """Everyone takes a cut, scaled inversely to sector weight.

    satisfaction_i = 1 - mu / w_i, so agriculture (w=1) is cut four times
    harder than Bengaluru (w=4), but no one is fully protected.
    """
    total = sum(demand.values())
    if supply >= total:
        return dict(demand)
    short = lambda mu: {k: min(d, mu * d / WEIGHTS[k]) for k, d in demand.items()}
    return _cut_until(supply, demand, short)


def equal_cuts(supply, demand):
    """Equal absolute cut for every sector (constrained equal losses).

    Looks fair on paper but wipes out small users first: kept as a cautionary rule.
    """
    total = sum(demand.values())
    if supply >= total:
        return dict(demand)
    short = lambda lam: {k: min(d, lam) for k, d in demand.items()}
    return _cut_until(supply, demand, short)


def optimised(supply, demand):
    """Minimise sum_i w_i * (shortfall_i / demand_i)^2.

    KKT conditions give shortfall_i = min(demand_i, mu * demand_i^2 / w_i):
    big, low-weight users absorb more of the shortage, but nobody is cut to
    zero first as in a strict ladder.
    """
    total = sum(demand.values())
    if supply >= total:
        return dict(demand)
    short = lambda mu: {k: min(d, mu * d * d / WEIGHTS[k]) for k, d in demand.items()}
    return _cut_until(supply, demand, short)


def drought_hedging(supply, demand):
    """In a shortage keep a reserve for next month; share the rest by minimum guarantee."""
    if supply >= sum(demand.values()):
        out = dict(demand)
        out['reserve'] = 0.0
        return out
    reserve = supply * HEDGE_RESERVE
    out = minimum_guarantee(supply - reserve, demand)
    out['reserve'] = reserve
    return out


STRATEGIES = {
    'essential_priority': essential_priority,
    'proportional': proportional,
    'minimum_guarantee': minimum_guarantee,
    'weighted_cuts': weighted_cuts,
    'equal_cuts': equal_cuts,
    'optimised': optimised,
    'drought_hedging': drought_hedging,
}


def check_balance(supply, demand, alloc, tol=1e-6):
    given = sum(alloc[k] for k in demand) + alloc.get('reserve', 0.0)
    assert given <= supply + tol, 'released more water than available'
    for k, d in demand.items():
        assert -tol <= alloc[k] <= d + tol, f'{k} outside [0, demand]'
