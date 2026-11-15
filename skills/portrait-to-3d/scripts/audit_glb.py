"""Validate uncompressed GLB data; deliberately does not score appearance."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


def audit(path):
    raw = path.read_bytes()
    if len(raw) < 20 or struct.unpack_from('<III', raw) != (0x46546C67, 2, len(raw)):
        raise ValueError('不是完整 GLB 2.0')
    chunks, offset = [], 12
    while offset < len(raw):
        if offset+8 > len(raw):
            raise ValueError('chunk 標頭截斷')
        length, kind = struct.unpack_from('<II', raw, offset)
        if length % 4 or offset+8+length > len(raw):
            raise ValueError('chunk 範圍或對齊錯誤')
        chunks.append((kind, raw[offset+8:offset+8+length]))
        offset += 8+length
    if len(chunks) != 2 or chunks[0][0] != 0x4E4F534A or chunks[1][0] != 0x004E4942:
        raise ValueError('需為單一 JSON 與 BIN chunk 的 GLB')
    doc, binary = json.loads(chunks[0][1]), chunks[1][1]
    if doc.get('asset', {}).get('version') != '2.0':
        raise ValueError('gltf asset.version 必須為 2.0')
    buffers = doc.get('buffers', [])
    if len(buffers) != 1 or 'uri' in buffers[0] or not 0 <= len(binary)-buffers[0]['byteLength'] <= 3:
        raise ValueError('不支援外部 buffer，或 BIN 長度不符')
    if any(x in doc.get('extensionsUsed', []) for x in ['KHR_draco_mesh_compression', 'EXT_meshopt_compression']):
        raise ValueError('壓縮 GLB 需先解碼；此工具不會跳過壓縮資料並標成功')
    for view in doc.get('bufferViews', []):
        off, count = view.get('byteOffset', 0), view['byteLength']
        if view.get('buffer', 0) != 0 or off < 0 or count < 0 or off+count > buffers[0]['byteLength']:
            raise ValueError('bufferView 範圍錯誤')
    formats = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
    counts = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
    cache = {}

    def values(index):
        if not isinstance(index, int) or not 0 <= index < len(doc.get('accessors', [])):
            raise ValueError('accessor 索引錯誤')
        if index in cache:
            return cache[index]
        a = doc['accessors'][index]
        if 'sparse' in a or 'bufferView' not in a:
            raise ValueError('不支援 sparse 或沒有 bufferView 的 accessor')
        if a['type'] not in counts or a['componentType'] not in formats:
            raise ValueError('不支援此 accessor 格式')
        if not 0 <= a['bufferView'] < len(doc.get('bufferViews', [])):
            raise ValueError('accessor bufferView 索引錯誤')
        v = doc['bufferViews'][a['bufferView']]
        fmt = '<'+formats[a['componentType']]*counts[a['type']]
        size = struct.calcsize(fmt)
        stride, off = v.get('byteStride', size), a.get('byteOffset', 0)
        end = off+(a['count']-1)*stride+size
        if a['count'] <= 0 or off < 0 or stride < size or end > v['byteLength']:
            raise ValueError('accessor 範圍錯誤')
        result = [struct.unpack_from(fmt, binary, v.get('byteOffset', 0)+off+i*stride) for i in range(a['count'])]
        if not all(math.isfinite(x) for row in result for x in row):
            raise ValueError('accessor 含非有限值')
        cache[index] = result
        return result

    for i in range(len(doc.get('accessors', []))):
        values(i)
    meshes = []
    for mesh in doc.get('meshes', []):
        triangles = 0
        for primitive in mesh['primitives']:
            if primitive.get('mode', 4) != 4:
                raise ValueError('僅支援 TRIANGLES primitive')
            attrs = primitive['attributes']
            position = doc['accessors'][attrs['POSITION']]
            if position['type'] != 'VEC3' or position['componentType'] != 5126:
                raise ValueError('POSITION 格式錯誤')
            vertices = values(attrs['POSITION'])
            if any(len(values(i)) != len(vertices) for i in attrs.values()):
                raise ValueError('頂點屬性數量不一致')
            if 'indices' in primitive:
                index_info = doc['accessors'][primitive['indices']]
                if index_info['type'] != 'SCALAR' or index_info['componentType'] not in [5121, 5123, 5125]:
                    raise ValueError('索引格式錯誤')
                indices = [v[0] for v in values(primitive['indices'])]
            else:
                indices = list(range(len(vertices)))
            if len(indices) % 3 or any(i < 0 or i >= len(vertices) for i in indices):
                raise ValueError('三角索引錯誤')
            if 'material' in primitive and not 0 <= primitive['material'] < len(doc.get('materials', [])):
                raise ValueError('材質索引錯誤')
            triangles += len(indices)//3
        meshes.append({'name': mesh.get('name'), 'triangles': triangles})
    if not meshes:
        raise ValueError('沒有 mesh')
    for im in doc.get('images', []):
        if 'bufferView' not in im or not 0 <= im['bufferView'] < len(doc['bufferViews']):
            raise ValueError('影像未內嵌或索引錯誤')
        view = doc['bufferViews'][im['bufferView']]
        start = view.get('byteOffset', 0)
        data = binary[start:start+view['byteLength']]
        mime = im.get('mimeType')
        valid = ((mime == 'image/png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or
                 (mime == 'image/jpeg' and data.startswith(b'\xff\xd8\xff')) or
                 (mime == 'image/webp' and data[:4] == b'RIFF' and data[8:12] == b'WEBP') or
                 (mime == 'image/ktx2' and data.startswith(b'\xabKTX 20\xbb\r\n\x1a\n')))
        if not valid:
            raise ValueError('內嵌影像標頭或 MIME 不符')
    return {'status': 'technical-pass', 'assetSHA256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw), 'meshes': meshes, 'triangles': sum(m['triangles'] for m in meshes),
            'embeddedImages': len(doc.get('images', [])), 'visualReview': 'not-run',
            'limits': ['不檢查相似度、UV 重疊、自交或動畫品質', '影像僅驗證標頭，完整解碼由瀏覽器驗證']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('glb', type=Path)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    if a.report.exists():
        p.error('報告已存在，請使用新的檔名')
    try:
        report = audit(a.glb)
    except (ValueError, KeyError, IndexError, TypeError, OSError, struct.error) as exc:
        report = {'status': 'failed', 'error': str(exc), 'visualReview': 'not-run'}
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'technical-pass' else 1)


if __name__ == '__main__':
    main()
