"""Offline asset build: run with Shapely installed; no runtime GIS dependency."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import split, unary_union

root=Path(__file__).resolve().parents[2]
raw=json.loads(Path(__file__).with_name('taiwan-mainland-natural-earth.json').read_text())
south,north=min(p[1] for p in raw),max(p[1] for p in raw)
scale=24/(north-south);middle=(min(p[0] for p in raw)+max(p[0] for p in raw))/2
coast=[((lon-middle)*math.cos(math.radians(23.6))*scale,(north-lat)*scale-12) for lon,lat in raw]
mainland=Polygon(coast).simplify(.012,preserve_topology=True)
shores=[]
for i in range(401):
 v=i/400;z=max(-11.99999,min(11.99999,v*24-12))
 cut=mainland.intersection(LineString([(-20,z),(20,z)]))
 shores.append([v,cut.bounds[0],cut.bounds[2]])
seams=[.50,.57,.45,.56,.43,.50]
# Area-balanced bands leave enough space to build on the southern two islands.
levels=[0,.23083,.38457,.52383,.66626,1]
def point(u,v):
 t=max(0,min(400,v*400));i=min(399,int(t));a,b=shores[i],shores[i+1];t-=i
 left=a[1]+(b[1]-a[1])*t;right=a[2]+(b[2]-a[2])*t
 bend=math.sin(math.pi*u)*math.sin(math.pi*v)
 return (left+(right-left)*u+.38*bend*math.sin(v*19),24*v-12+.72*bend*math.sin(u*10+v*17))
def seam(v):
 row=next((i for i in range(5) if v<=levels[i+1]),4);t=(v-levels[row])/(levels[row+1]-levels[row])
 return seams[row]+(seams[row+1]-seams[row])*t+.06*math.sin(t*math.pi*2)
cuts=[LineString([point(-.4+i/100*1.8,levels[row]) for i in range(101)]) for row in range(1,5)]
mid=[point(seam(i/500),i/500) for i in range(501)]
cuts.append(LineString([(mid[0][0],-14)]+mid+[(mid[-1][0],14)]))
regions=[mainland]
for line in cuts:
 regions=[g for p in regions for g in split(p,line).geoms if g.area>.03]
assert len(regions)==10,len(regions)
water=unary_union([c.buffer(.065,cap_style=2) for c in cuts])
result=[]
for row in range(5):
 for col in range(2):
  v=(levels[row]+levels[row+1])/2;u=(1+seam(v))/2 if col else seam(v)/2;center=point(u,v)
  from shapely.geometry import Point
  region=next(p for p in regions if p.contains(Point(center)))
  land=region.difference(water)
  if land.geom_type=='MultiPolygon':land=max(land.geoms,key=lambda g:g.area)
  result.append(dict(id=len(result)+1,row=row,col=col,center=center,points=list(land.exterior.coords)[:-1]))
payload='// Derived from Natural Earth 1:10m, mainland only. See tools/coastline/README.md.\n'
for name,value in [('shores',shores),('divisionLevels',levels),('coastline',list(mainland.exterior.coords)),('modelPieces',result)]:
 payload+='export const '+name+'='+json.dumps(value,separators=(',',':'))+';\n'
(root/'taiwan-coastline.js').write_text(payload)
print('Built',len(result),'islands from',len(mainland.exterior.coords),'coast vertices.')
