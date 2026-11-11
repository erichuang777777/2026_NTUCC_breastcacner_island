import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(root, 'export/env-pathology-island-001.glb');
const chunks = [];
const bufferViews = [];
const accessors = [];
const meshes = [];
const nodes = [];
const materials = [
  material('rock', '#8F857D'), material('grass-lower', '#B9C5A6'),
  material('grass', '#9AA58F'), material('path', '#E8C9BD'), material('gate', '#556B60'),
];

function material(name, hex) {
  const value = Number.parseInt(hex.slice(1), 16);
  return { name, pbrMetallicRoughness: {
    baseColorFactor: [((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255, 1],
    metallicFactor: 0, roughnessFactor: 0.88,
  } };
}

function byteLength() { return chunks.reduce((sum, chunk) => sum + chunk.length, 0); }
function addChunk(array, type) {
  const padding = (4 - (byteLength() % 4)) % 4;
  if (padding) chunks.push(Buffer.alloc(padding));
  const byteOffset = byteLength();
  const buffer = Buffer.from(array.buffer, array.byteOffset, array.byteLength);
  chunks.push(buffer);
  const view = bufferViews.push({ buffer: 0, byteOffset, byteLength: buffer.length, target: 34962 }) - 1;
  const values = [[], [], []];
  for (let i = 0; i < array.length; i += 3) for (let axis = 0; axis < 3; axis += 1) values[axis].push(array[i + axis]);
  return accessors.push({ bufferView: view, componentType: 5126, count: array.length / 3, type,
    min: values.map((axis) => Math.min(...axis)), max: values.map((axis) => Math.max(...axis)) }) - 1;
}

function addMesh(name, geometry, materialIndex, translation) {
  const position = addChunk(new Float32Array(geometry.positions), 'VEC3');
  const normal = addChunk(new Float32Array(geometry.normals), 'VEC3');
  const mesh = meshes.push({ name, primitives: [{ attributes: { POSITION: position, NORMAL: normal }, material: materialIndex }] }) - 1;
  nodes.push({ name, mesh, translation });
}

function triangle(store, a, b, c, normal) {
  store.positions.push(...a, ...b, ...c);
  store.normals.push(...normal, ...normal, ...normal);
}

function frustum(radiusTop, radiusBottom, height, sides = 6) {
  const store = { positions: [], normals: [] };
  const topY = height / 2;
  const bottomY = -height / 2;
  for (let i = 0; i < sides; i += 1) {
    const a = (i / sides) * Math.PI * 2 + Math.PI / 6;
    const b = ((i + 1) / sides) * Math.PI * 2 + Math.PI / 6;
    const topA = [Math.cos(a) * radiusTop, topY, Math.sin(a) * radiusTop];
    const topB = [Math.cos(b) * radiusTop, topY, Math.sin(b) * radiusTop];
    const bottomA = [Math.cos(a) * radiusBottom, bottomY, Math.sin(a) * radiusBottom];
    const bottomB = [Math.cos(b) * radiusBottom, bottomY, Math.sin(b) * radiusBottom];
    triangle(store, [0, topY, 0], topB, topA, [0, 1, 0]);
    triangle(store, [0, bottomY, 0], bottomA, bottomB, [0, -1, 0]);
    const mid = (a + b) / 2;
    const normal = [Math.cos(mid), 0.18, Math.sin(mid)];
    const length = Math.hypot(...normal);
    const normalized = normal.map((value) => value / length);
    triangle(store, topA, topB, bottomB, normalized);
    triangle(store, topA, bottomB, bottomA, normalized);
  }
  return store;
}

function box(width, height, depth) {
  const x = width / 2, y = height / 2, z = depth / 2;
  const store = { positions: [], normals: [] };
  const faces = [
    [[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z],[0,0,1]], [[x,-y,-z],[-x,-y,-z],[-x,y,-z],[x,y,-z],[0,0,-1]],
    [[x,-y,z],[x,-y,-z],[x,y,-z],[x,y,z],[1,0,0]], [[-x,-y,-z],[-x,-y,z],[-x,y,z],[-x,y,-z],[-1,0,0]],
    [[-x,y,z],[x,y,z],[x,y,-z],[-x,y,-z],[0,1,0]], [[-x,-y,-z],[x,-y,-z],[x,-y,z],[-x,-y,z],[0,-1,0]],
  ];
  for (const [a, b, c, d, normal] of faces) { triangle(store, a, b, c, normal); triangle(store, a, c, d, normal); }
  return store;
}

addMesh('island-rock-base', frustum(12.1, 13.1, 2.55), 0, [0, -1.03, 0]);
addMesh('island-shore-rim', frustum(12.35, 12.45, 0.52), 1, [0, 0.47, 0]);
addMesh('island-grass-top', frustum(11.72, 12.04, 0.34), 2, [0, 0.88, 0]);
addMesh('north-care-path', box(2.4, 0.18, 3.0), 3, [0, 1.13, 11.15]);
addMesh('north-gate-left', box(0.22, 2.25, 0.22), 4, [-1.12, 2.15, 11.65]);
addMesh('north-gate-right', box(0.22, 2.25, 0.22), 4, [1.12, 2.15, 11.65]);
addMesh('north-gate-header', box(2.46, 0.22, 0.22), 4, [0, 3.2, 11.65]);

const binary = Buffer.concat(chunks);
const gltf = { asset: { version: '2.0', generator: 'Hope Island deterministic low-poly generator' }, scene: 0,
  scenes: [{ name: 'ENV-PATHOLOGY-ISLAND-001', nodes: nodes.map((_, index) => index) }],
  nodes, meshes, materials, accessors, bufferViews, buffers: [{ byteLength: binary.length }] };
const jsonSource = JSON.stringify(gltf);
const json = Buffer.from(jsonSource + ' '.repeat((4 - (Buffer.byteLength(jsonSource) % 4)) % 4));
const bin = Buffer.concat([binary, Buffer.alloc((4 - (binary.length % 4)) % 4)]);
const header = Buffer.alloc(12); header.writeUInt32LE(0x46546c67, 0); header.writeUInt32LE(2, 4); header.writeUInt32LE(12 + 8 + json.length + 8 + bin.length, 8);
const jsonHeader = Buffer.alloc(8); jsonHeader.writeUInt32LE(json.length, 0); jsonHeader.writeUInt32LE(0x4e4f534a, 4);
const binHeader = Buffer.alloc(8); binHeader.writeUInt32LE(bin.length, 0); binHeader.writeUInt32LE(0x004e4942, 4);
await mkdir(dirname(output), { recursive: true });
await writeFile(output, Buffer.concat([header, jsonHeader, json, binHeader, bin]));
console.log(output);
