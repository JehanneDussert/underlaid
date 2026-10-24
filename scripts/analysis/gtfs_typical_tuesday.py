"""Run on 24 October 2026 (check before the emergency curve).
Usage: python scripts/analysis/gtfs_typical_tuesday.py <folder with calendar.txt, calendar_dates.txt, routes.txt, trips.txt, agency.txt>
Is Tuesday 13 October 2026 a typical day in the IDFM GTFS of 1 October 2026?
Trips per line (metro, RER/train, tram, Noctilien) on each Tuesday and
Thursday of the feed; lines whose 13 October count differs from 6 October."""
import sys
import pandas as pd
D = sys.argv[1]
cal = pd.read_csv(f"{D}/calendar.txt", dtype=str)
cd = pd.read_csv(f"{D}/calendar_dates.txt", dtype=str)
routes = pd.read_csv(f"{D}/routes.txt", dtype=str)
trips = pd.read_csv(f"{D}/trips.txt", dtype=str, usecols=["route_id", "service_id", "trip_id"])
ag = pd.read_csv(f"{D}/agency.txt", dtype=str)
routes = routes.merge(ag[["agency_id", "agency_name"]], on="agency_id", how="left")
print("calendar range:", cal.start_date.min(), "-", cal.end_date.max(), "| exception dates:", cd.date.min(), "-", cd.date.max())
noct = routes.route_short_name.fillna("").str.match(r"^N\d") & (routes.route_type == "3")
routes["mode"] = routes.route_type.map({"0": "tram", "1": "metro", "2": "rail", "7": "funicular"}).where(~noct, "noctilien")
keep = routes[routes["mode"].isin(["tram", "metro", "rail", "noctilien"])]
DAYCOL = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
def active(date):
    d = pd.Timestamp(date)
    col = DAYCOL[d.weekday()]
    s = set(cal[(cal[col] == "1") & (cal.start_date <= date) & (cal.end_date >= date)].service_id)
    ex = cd[cd.date == date]
    s |= set(ex[ex.exception_type == "1"].service_id)
    s -= set(ex[ex.exception_type == "2"].service_id)
    return s
dates = ["20261006", "20261013", "20261020", "20261027", "20261008", "20261015"]
t = trips[trips.route_id.isin(keep.route_id)]
counts = {}
for d in dates:
    s = active(d)
    counts[d] = t[t.service_id.isin(s)].groupby("route_id").size()
c = pd.DataFrame(counts).fillna(0).astype(int)
c = c.join(keep.set_index("route_id")[["mode", "route_short_name", "route_long_name", "agency_name"]])
print("\ntrips by mode and date:")
print(c.groupby("mode")[dates].sum().to_string())
print("\nexceptions in calendar_dates on 13 Oct:", (cd.date == "20261013").sum(), "rows; removed services:", ((cd.date == "20261013") & (cd.exception_type == "2")).sum())
diff = c[(c["20261013"] != c["20261006"])].copy()
diff["delta_pct"] = (100 * (diff["20261013"] - diff["20261006"]) / diff["20261006"].replace(0, pd.NA)).round(1)
print(f"\nlines whose 13 Oct count differs from 6 Oct: {len(diff)} of {len(c)}")
print(diff.sort_values("delta_pct")[["mode", "route_short_name", "route_long_name"] + dates + ["delta_pct"]].to_string())
z = c[(c["20261013"] == 0) & (c[["20261006", "20261008", "20261015"]].max(axis=1) > 0)]
print("\nlines with no trip on 13 Oct but trips on other weekdays:", len(z))
print(z[["mode", "route_short_name", "route_long_name"] + dates].to_string())
