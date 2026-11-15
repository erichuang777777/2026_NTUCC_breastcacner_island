export class IslandWorld {
 constructor(data){this.data=data;this.cells=new Set(data.walkable);this.step=data.step;this.width=data.width;this.height=data.height;this.origin=data.origin;
  const start=[...this.cells].sort((a,b)=>this.distance(this.point(a),data.spawn)-this.distance(this.point(b),data.spawn))[0],connected=new Set([start]),queue=[start];
  for(let i=0;i<queue.length;i++){const k=queue[i],x=k%this.width,z=Math.floor(k/this.width);for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]){const nx=x+dx,nz=z+dz,n=nz*this.width+nx;if(nx>=0&&nx<this.width&&nz>=0&&nz<this.height&&this.cells.has(n)&&!connected.has(n)){connected.add(n);queue.push(n);}}}
  this.cells=connected;this.spawnCells=[...connected].sort((a,b)=>this.distance(this.point(a),data.spawn)-this.distance(this.point(b),data.spawn));
 }
 distance(a,b){return Math.hypot(a[0]-b[0],a[1]-b[1]);}
 point(k){return [this.origin[0]+(k%this.width+.5)*this.step,this.origin[1]+(Math.floor(k/this.width)+.5)*this.step];}
 allowed(x,z){const ix=Math.floor((x-this.origin[0])/this.step),iz=Math.floor((z-this.origin[1])/this.step);return ix>=0&&ix<this.width&&iz>=0&&iz<this.height&&this.cells.has(iz*this.width+ix);}
 spawn(others){for(const k of this.spawnCells){const p=this.point(k);if(others.every(o=>this.distance(p,o)>=.9))return p;}throw Error('島上暫時沒有空位。');}
 move(x,z,dx,dz,dt,others){const length=Math.hypot(dx,dz);if(length>1){dx/=length;dz/=length;}const distance=2*Math.max(0,Math.min(.25,dt)),steps=Math.max(1,Math.ceil(distance/.06)),free=(nx,nz)=>this.allowed(nx,nz)&&others.every(o=>this.distance([nx,nz],o)>=.58);
  for(let i=0;i<steps;i++){const sx=dx*distance/steps,sz=dz*distance/steps;if(free(x+sx,z+sz)){x+=sx;z+=sz;}else if(free(x+sx,z))x+=sx;else if(free(x,z+sz))z+=sz;}return [x,z];
 }
}
export const position=r=>({x:r.x,z:r.z,heading:r.heading,sequence:r.sequence,updatedAt:r.updated_at,dx:r.input_dx,dz:r.input_dz});
