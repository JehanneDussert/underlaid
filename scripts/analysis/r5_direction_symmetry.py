"""Check: are R5 transit times about the same cell->GP site and GP site->cell?

Justifies routing from sites in scripts/31 (see its docstring). Run in the
access Docker image, from the repo root.
"""
import sys, time; sys.argv += ['--max-memory','24G']
import r5py, datetime as dt, geopandas as gpd, pandas as pd, numpy as np
cells=gpd.read_file('data/processed/access/demand_grid_idf.geojson')[['cell_id','geometry']].rename(columns={'cell_id':'id'})
sites=gpd.read_file('data/processed/access/gp_sites_idf.geojson')[['site_id','geometry']].rename(columns={'site_id':'id'})
rng=np.random.default_rng(1)
# sample of cells across the MGP and ring; sites within 6 km of them
c=cells[cells.geometry.x.between(2.15,2.6)&cells.geometry.y.between(48.75,48.98)].sample(150,random_state=1)
s=sites[sites.geometry.x.between(2.15,2.6)&sites.geometry.y.between(48.75,48.98)].sample(150,random_state=1)
n=r5py.TransportNetwork('data/raw/osm/ile-de-france-latest.osm.pbf',['data/raw/gtfs/IDFM-gtfs.zip'])
kw=dict(departure=dt.datetime(2026,10,13,10),departure_time_window=dt.timedelta(minutes=60),transport_modes=[r5py.TransportMode.TRANSIT,r5py.TransportMode.WALK],max_time=dt.timedelta(minutes=30),speed_walking=4.5)
t0=time.time(); f=pd.DataFrame(r5py.TravelTimeMatrix(n,origins=c,destinations=s,**kw)).dropna(); t1=time.time()
r=pd.DataFrame(r5py.TravelTimeMatrix(n,origins=s,destinations=c,**kw)).dropna(); t2=time.time()
print('forward s', round(t1-t0), 'reverse s', round(t2-t1))
r=r.rename(columns={'from_id':'to_id','to_id':'from_id'})
m=f.merge(r,on=['from_id','to_id'],how='outer',suffixes=('_fwd','_rev'))
both=m.dropna()
d=(both.travel_time_rev-both.travel_time_fwd)
print('pairs fwd', len(f), 'rev', len(r), 'both', len(both))
print('diff (rev - fwd) min: median', d.median(), 'mean abs', round(d.abs().mean(),2), 'p90 abs', d.abs().quantile(.9), 'share |d|<=2', round((d.abs()<=2).mean(),3))
for lo,hi in [(0,10),(10,15),(15,20),(20,25)]:
    sub=both[(both.travel_time_fwd>=lo)&(both.travel_time_fwd<hi)]; dd=(sub.travel_time_rev-sub.travel_time_fwd)
    print(f'  fwd {lo}-{hi}: n {len(sub)} median {dd.median()} mean abs {dd.abs().mean():.2f}')
bands=lambda t: np.select([t<10,t<15,t<20],[0,1,2],3)
print('same DREES band share', round((bands(both.travel_time_fwd)==bands(both.travel_time_rev)).mean(),3))
