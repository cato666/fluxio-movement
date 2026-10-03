"""Existing private image pipeline, shared by all training channels."""
from pathlib import Path
from uuid import uuid4
import os
import cv2
import numpy as np
from .training_errors import TrainingInvalid, TrainingTooLarge, TrainingNotFound

IMAGE_LIMIT = 8 * 1024 * 1024


def image_directory():
    return Path(os.getenv('STORAGE_PATH', '/data/storage')) / 'training-images'


class TrainingMediaStore:
    def directory(self):
        return image_directory()

    def save_image(self, raw: bytes):
        if len(raw) > IMAGE_LIMIT:
            raise TrainingTooLarge('La imagen supera 8 MB')
        if not (raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG\r\n\x1a\n') or (raw.startswith(b'RIFF') and raw[8:12] == b'WEBP')):
            raise TrainingInvalid('Sube una imagen JPEG, PNG o WebP válida')
        try:
            image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        except cv2.error:
            image = None
        if image is None or image.shape[0] * image.shape[1] > 24000000:
            raise TrainingInvalid('Imagen inválida o demasiado grande (máximo 24 megapíxeles)')
        if max(image.shape[:2]) > 2400:
            factor = 2400 / max(image.shape[:2])
            image = cv2.resize(image, (round(image.shape[1] * factor), round(image.shape[0] * factor)))
        ok, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok:
            raise TrainingInvalid('No se pudo procesar la imagen')
        identifier = uuid4()
        directory = self.directory(); directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'{identifier}.jpg'
        path.write_bytes(encoded.tobytes())
        return identifier, path

    def image_path(self, name):
        path = self.directory() / name
        if not path.is_file():
            raise TrainingNotFound('Imagen no disponible')
        return path
