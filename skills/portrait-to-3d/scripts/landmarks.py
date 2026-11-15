"""Extract 2D reference landmarks locally with an explicitly supplied task model."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('輸出已存在')
    if not a.image.is_file() or not a.model.is_file():
        p.error('照片或 MediaPipe task model 不存在')
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    image = mp.Image.create_from_file(str(a.image.resolve()))
    options = vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(a.model.resolve())),
        num_faces=2, output_facial_transformation_matrixes=True)
    with vision.FaceLandmarker.create_from_options(options) as detector:
        result = detector.detect(image)
    if len(result.face_landmarks) != 1:
        raise ValueError('需要恰好一張可辨識臉孔；可另存裁切參考，原照保持不變')
    data = {'size': [image.width, image.height],
            'referenceSHA256': hashlib.sha256(a.image.read_bytes()).hexdigest(),
            'points': [[v.x, v.y, v.z] for v in result.face_landmarks[0]],
            'transform': result.facial_transformation_matrixes[0].tolist(),
            'coordinates': 'normalized image x/y; z is NOT metric depth',
            'manualReviewRequired': True}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'points': len(data['points']), 'output': str(a.out)}))


if __name__ == '__main__':
    main()
