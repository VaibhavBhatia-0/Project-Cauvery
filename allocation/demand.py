"""30-day Karnataka (Cauvery basin) water demand scenarios, in TMC.

Every number here is an editable assumption, not an official estimate.
The agricultural figure is a historical Tribunal benchmark scaled to one month.
"""
from dataclasses import dataclass

LITRES_PER_TMC = 28_316_846_592  # 1 TMC = 1e9 cubic feet


@dataclass(frozen=True)
class UrbanScenario:
    population: float     # people served
    lpcd: float           # litres per person per day delivered
    loss_fraction: float  # distribution losses (0-1)
    non_cauvery_tmc: float = 0.0  # supply from other sources, if known


BENGALURU = {
    'low':    UrbanScenario(13_000_000, 135, 0.15),
    'medium': UrbanScenario(14_500_000, 150, 0.20),
    'high':   UrbanScenario(16_000_000, 165, 0.25),
}

OTHER_DOMESTIC_TMC = 0.300   # other Karnataka towns in the basin (assumed)
ENVIRONMENTAL_TMC = 0.250    # minimum river flow kept for ecology (assumed)

# Cauvery Water Disputes Tribunal (2007), Vol. V: 18.85 lakh acres,
# 250.62 TMC/year for Karnataka. The October share of 10% is an assumption.
AGRI_ANNUAL_TMC = 250.62
AGRI_MONTH_FRACTION = 0.10


def urban_demand_tmc(s: UrbanScenario, days: int = 30) -> float:
    delivered = s.population * s.lpcd * days
    withdrawal = delivered / (1 - s.loss_fraction)
    return max(0.0, withdrawal / LITRES_PER_TMC - s.non_cauvery_tmc)


def monthly_demand(level: str = 'medium', days: int = 30) -> dict:
    """Sector demands in priority order: Bengaluru, domestic, environment, agriculture."""
    return {
        'bengaluru': urban_demand_tmc(BENGALURU[level], days),
        'domestic': OTHER_DOMESTIC_TMC,
        'environment': ENVIRONMENTAL_TMC,
        'agriculture': AGRI_ANNUAL_TMC * AGRI_MONTH_FRACTION,
    }


if __name__ == '__main__':
    for level in BENGALURU:
        d = monthly_demand(level)
        print(level, {k: round(v, 4) for k, v in d.items()}, 'total', round(sum(d.values()), 4))
