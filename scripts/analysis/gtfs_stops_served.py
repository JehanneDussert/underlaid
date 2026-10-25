"""Run on 24 October 2026 (check before the emergency curve).
Usage: python scripts/analysis/gtfs_stops_served.py <IDFM-gtfs.zip> <folder with the extracted calendar, routes and trips files>
Stops served per line (metro, RER/train, tram, Noctilien), 6 vs 13 October
2026, from stop_times (read in chunks from the zip): a partly closed line
(works, bus replacement) keeps trips but serves fewer stops."""
import sys, zipfile
import pandas as pd
Z, D = sys.argv[1], sys.argv[2]
cal = pd.read_csv(f"{D}/calendar.txt", dtype=str)
cd = pd.read_csv(f"{D}/calendar_dates.txt", dtype=str)
routes = pd.read_csv(f"{D}/routes.txt", dtype=str)
trips = pd.read_csv(f"{D}/trips.txt", dtype=str, usecols=["route_id", "service_id", "trip_id"])
noct = routes.route_short_name.fillna("").str.match(r"^N\d") & (routes.route_type == "3")
routes["mode"] = routes.route_type.map({"0": "tram", "1": "metro", "2": "rail"}).where(~noct, "noctilien")
keep = routes[routes["mode"].isin(["tram", "metro", "rail", "noctilien"])]
DAYCOL = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
def active(date):
    col = DAYCOL[pd.Timestamp(date).weekday()]
    s = set(cal[(cal[col] == "1") & (cal.start_date <= date) & (cal.end_date >= date)].service_id)
    ex = cd[cd.date == date]
    return (s | set(ex[ex.exception_type == "1"].service_id)) - set(ex[ex.exception_type == "2"].service_id)
dates = ["20261006", "20261013", "20261015"]
t = trips[trips.route_id.isin(keep.route_id)]
by_date = {d: t[t.service_id.isin(active(d))][["trip_id", "route_id"]] for d in dates}
wanted = set(t.trip_id)
parts = []
with zipfile.ZipFile(Z) as z, z.open("stop_times.txt") as f:
    for ch in pd.read_csv(f, dtype=str, usecols=["trip_id", "stop_id"], chunksize=2_000_000):
        parts.append(ch[ch.trip_id.isin(wanted)])
st = pd.concat(parts)
res = {}
for d, tt in by_date.items():
    m = st.merge(tt, on="trip_id")
    res[d] = m.groupby("route_id").stop_id.nunique()
r = pd.DataFrame(res).fillna(0).astype(int).join(keep.set_index("route_id")[["mode", "route_short_name", "route_long_name"]])
print("stops served, by mode:", r.groupby("mode")[dates].sum().to_string(), sep="\n")
d = r[r["20261013"] < r["20261006"]]
print(f"\nlines serving fewer stops on 13 Oct than on 6 Oct: {len(d)}")
print(d.to_string())
d2 = r[r["20261013"] < r["20261015"]]
print(f"\nlines serving fewer stops on 13 Oct than on 15 Oct: {len(d2)}")
print(d2.to_string())
