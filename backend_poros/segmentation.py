from __future__ import annotations

import os
from typing import Dict, List, Tuple

import cv2
import numpy as np
from skimage import measure
from skimage.filters import threshold_otsu

from .models import MaskConfig, ThresholdConfig, PoreAreaRecord, SegmentationResult


def _build_circular_mask(shape: Tuple[int, int], mask_cfg: MaskConfig) -> np.ndarray:
    """
    Construye una máscara circular booleana dentro de un recorte de tamaño `shape` (h, w).
    Replica la lógica geométrica de tu script original.
    """
    h, w = shape
    if not mask_cfg.use_circular_mask:
        return np.ones((h, w), dtype=bool)

    dy, dx = mask_cfg.circle_center_offset
    cy = h // 2 + dy
    cx = w // 2 + dx
    radio = min(h, w) // 2 - mask_cfg.circle_margin

    Y, X = np.ogrid[:h, :w]
    dist2 = (X - cx) ** 2 + (Y - cy) ** 2
    mask = dist2 <= radio ** 2
    return mask


def _segment_gray(
    gray: np.ndarray,
    thr_cfg: ThresholdConfig,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    A partir de una imagen en escala de grises, calcula:
      - poros: máscara booleana (True = poro)
      - labels: matriz de etiquetas (int32, 0=fondo, 1..N = poro)
      - num_poros: cantidad de poros detectados
    """
    gray = gray.astype(np.uint8)
    valores = np.unique(gray)

    if thr_cfg.manual_threshold is None and not thr_cfg.use_otsu and len(valores) <= 2:
        poros = (gray == 0)
    else:
        if thr_cfg.manual_threshold is not None:
            thr = thr_cfg.manual_threshold
        elif thr_cfg.use_otsu:
            thr = threshold_otsu(gray)
        else:
            thr = threshold_otsu(gray)

        poros = gray < thr

    labels, num_poros = measure.label(poros, connectivity=2, return_num=True)
    labels = labels.astype(np.int32)
    return poros, labels, num_poros

def imread_unicode(path: str):
    with open(path, "rb") as f:
        data = np.frombuffer(f.read(), np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)

def procesar_imagenes(
    image_paths: List[str],
    mask_cfg: MaskConfig,
    thr_cfg: ThresholdConfig,
) -> SegmentationResult:
    """
    Procesa una lista de paths a imágenes de tomografía.
    Devuelve:
      - labels_by_image: dict[nombre_imagen] -> matriz de etiquetas (int32, 0=fondo).
        Las etiquetas son GLOBALMENTE únicas entre cortes (offset acumulado).
      - pore_areas: lista de PoreAreaRecord (imagen, id_poro_global, área_en_pixeles).
    """
    labels_by_image: Dict[str, np.ndarray] = {}
    pore_areas: List[PoreAreaRecord] = []

    offset_poros = 0  # para que los IDs de poro no se repitan entre imágenes

    for path in image_paths:
        nombre = os.path.basename(path)

        imagen_color = imread_unicode(path)
        if imagen_color is None:
            print(f"[procesar_imagenes] ⚠ No se pudo leer: {path}")
            continue

        # Recorte
        y_min, y_max, x_min, x_max = mask_cfg.crop
        imagen_crop = imagen_color[y_min:y_max, x_min:x_max].copy()

        # Máscara circular
        h, w, _ = imagen_crop.shape
        mask_circ = _build_circular_mask((h, w), mask_cfg)

        # A escala de grises + filtrado suave
        gris = cv2.cvtColor(imagen_crop, cv2.COLOR_BGR2GRAY)
        if getattr(thr_cfg, "apply_smoothing", False):
            # Mediana
            gris = cv2.medianBlur(gris, 3)
            # Gaussian Blur
            gris = cv2.GaussianBlur(gris, (3, 3), 0)

        # Forzamos fuera del círculo a valor alto (fondo "blanco")
        gris_masked = gris.copy()
        gris_masked[~mask_circ] = 255

        # Segmentación
        poros, etiquetas_locales, num_poros = _segment_gray(gris_masked, thr_cfg)

        # Forzamos fuera del círculo a fondo
        poros[~mask_circ] = False
        etiquetas_locales[~mask_circ] = 0

        # Aplicar offset global: etiquetas >0 se desplazan
        etiquetas_globales = etiquetas_locales.copy()
        etiquetas_globales[etiquetas_globales > 0] += offset_poros

        # Actualizar offset
        offset_poros += num_poros

        labels_by_image[nombre] = etiquetas_globales

        # Cálculo de áreas
        props = measure.regionprops(etiquetas_globales)
        for region in props:
            pore_id = int(region.label)
            area = int(region.area)
            pore_areas.append(PoreAreaRecord(image_name=nombre, pore_id=pore_id, area_px=area))

    return SegmentationResult(labels_by_image=labels_by_image, pore_areas=pore_areas)
