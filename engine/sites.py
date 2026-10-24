"""Boston snow-farm sites.

Boston Public Works hauls plowed snow to ~11 disposal "snow farm" sites (FEMA).
Exact operational coordinates vary year to year and are not all published, so
these are representative Boston locations used for the demo map. Each is labeled
as approximate. The Seaport site is the famous 2015 ~75 ft pile.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SnowFarmSite:
    name: str
    latitude: float
    longitude: float
    note: str = ""


# Representative Boston locations (approximate) for demo purposes.
BOSTON_SNOW_FARMS: list[SnowFarmSite] = [
    SnowFarmSite("Seaport / South Boston", 42.3450, -71.0410, "Site of the 2015 ~75 ft snow farm"),
    SnowFarmSite("Tide Street Lot", 42.3480, -71.0390, "Approx."),
    SnowFarmSite("Widett Circle", 42.3380, -71.0640, "Approx."),
    SnowFarmSite("Frontage Road", 42.3350, -71.0660, "Approx."),
    SnowFarmSite("Charlestown", 42.3780, -71.0620, "Approx."),
    SnowFarmSite("East Boston", 42.3750, -71.0390, "Approx."),
    SnowFarmSite("Dorchester", 42.3000, -71.0660, "Approx."),
    SnowFarmSite("Roxbury", 42.3250, -71.0950, "Approx."),
    SnowFarmSite("Allston/Brighton", 42.3550, -71.1320, "Approx."),
    SnowFarmSite("West Roxbury", 42.2850, -71.1600, "Approx."),
    SnowFarmSite("Hyde Park", 42.2560, -71.1240, "Approx."),
]
