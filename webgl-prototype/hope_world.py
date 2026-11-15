"""Authoritative, request-driven movement shared by phone controllers and displays."""
import json
import math
import time
from pathlib import Path

class IslandWorld:
    def __init__(self, path):
        self.data=json.loads(Path(path).read_text());self.cells=set(self.data['walkable'])
        self.step=self.data['step'];self.width=self.data['width'];self.height=self.data['height'];self.origin=self.data['origin']
        # Keep only cells connected to the hospital arrival area.
        start=min(self.cells,key=lambda k:self.distance(self.point(k),self.data['spawn']))
        connected={start};queue=[start]
        for k in queue:
            x,z=k%self.width,k//self.width
            for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,nz=x+dx,z+dz;n=nz*self.width+nx
                if 0<=nx<self.width and 0<=nz<self.height and n in self.cells and n not in connected:connected.add(n);queue.append(n)
        self.cells=connected
        self.spawn_cells=sorted(self.cells,key=lambda k:self.distance(self.point(k),self.data['spawn']))
    @staticmethod
    def distance(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
    def point(self,k):return [self.origin[0]+(k%self.width+.5)*self.step,self.origin[1]+(k//self.width+.5)*self.step]
    def allowed(self,x,z):
        ix=math.floor((x-self.origin[0])/self.step);iz=math.floor((z-self.origin[1])/self.step)
        return 0<=ix<self.width and 0<=iz<self.height and iz*self.width+ix in self.cells
    def spawn(self,others):
        for k in self.spawn_cells:
            p=self.point(k)
            if all(self.distance(p,o)>=.9 for o in others):return p
        raise ValueError('島上暫時沒有空位，請稍後再試。')
    def move(self,x,z,dx,dz,dt,others):
        length=math.hypot(dx,dz)
        if length>1:dx/=length;dz/=length
        dt=max(0,min(.25,dt));distance=2*dt
        steps=max(1,math.ceil(distance/.06))
        def free(nx,nz):return self.allowed(nx,nz) and all(self.distance((nx,nz),o)>=.58 for o in others)
        for _ in range(steps):
            sx,sz=dx*distance/steps,dz*distance/steps
            if free(x+sx,z+sz):x+=sx;z+=sz
            elif free(x+sx,z):x+=sx
            elif free(x,z+sz):z+=sz
        return x,z


def initialize_world(db):
    db.execute('''CREATE TABLE IF NOT EXISTS player_positions(profile_id TEXT PRIMARY KEY REFERENCES resident_profiles(id),x REAL NOT NULL,z REAL NOT NULL,heading REAL NOT NULL DEFAULT 0,sequence INTEGER NOT NULL DEFAULT 0,updated_at REAL NOT NULL)''')

    columns={r[1] for r in db.execute('PRAGMA table_info(player_positions)')}
    for name in ('input_dx','input_dz'):
        if name not in columns:db.execute(f'ALTER TABLE player_positions ADD COLUMN {name} REAL NOT NULL DEFAULT 0')


def active_positions(db):
    from hope_content import today
    return db.execute("SELECT w.* FROM player_positions w JOIN participants p ON p.profile_id=w.profile_id JOIN events e ON e.id=p.event_id WHERE e.date=? AND e.status='open' AND w.updated_at>?",(today(),time.time()-90)).fetchall()


def position_dict(row):
    return dict(x=row['x'],z=row['z'],heading=row['heading'],sequence=row['sequence'],updatedAt=row['updated_at'],dx=row['input_dx'],dz=row['input_dz'])
