from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional, Any

import numpy as np


@dataclass
class GeometryConfig:
    """
    Información geométrica de la tomografía.
    """
    pixel_size_mm: float       # tamaño de píxel (mm/píxel) en X e Y
    slice_distance_mm: float   # distancia entre cortes (mm) o espesor de corte


@dataclass
class MaskConfig:
    """
    Parámetros de recorte y máscara de la probeta.
    - crop: (y_min, y_max, x_min, x_max) en píxeles de la imagen original.
    - use_circular_mask: si True, se aplica máscara circular sobre el recorte.
    - circle_center_offset: desplazamiento (dy, dx) del centro del círculo respecto al centro del recorte.
    - circle_margin: margen en píxeles entre el borde de la imagen recortada y el borde del círculo.
    """
    crop: Tuple[int, int, int, int]
    use_circular_mask: bool = True
    circle_center_offset: Tuple[int, int] = (-15, 0)
    circle_margin: int = 15


@dataclass
class ThresholdConfig:
    """
    Parámetros de umbralizado.
    - use_otsu: si True y manual_threshold es None, se usa Otsu.
    - manual_threshold: si no es None, se usa este valor de umbral (0..255).
    """
    use_otsu: bool = True
    manual_threshold: Optional[int] = None
    apply_smoothing: bool = False


@dataclass
class StlExportConfig:
    """
    Parámetros de exportación del STL.
    - tipo: qué conjunto de poros exportar (internos, externos o todos).
    - aplicar_gaussiano: si True, suaviza el volumen 3D antes de extraer la malla.
    - aplicar_taubin: si True, suaviza la malla triangulada final.
    """
    tipo: str = "Internal"
    aplicar_gaussiano: bool = False
    aplicar_taubin: bool = False
    sigma_z: float = 0.6
    sigma_xy: float = 1.0
    iteraciones_taubin: int = 10


@dataclass
class PoreAreaRecord:
    """
    Registro del área de un poro 2D en una imagen específica.
    """
    image_name: str
    pore_id: int
    area_px: int


@dataclass
class SegmentationResult:
    """
    Resultado de la segmentación 2D en todos los cortes.
    """
    labels_by_image: Dict[str, np.ndarray]  
    pore_areas: List[PoreAreaRecord]         


@dataclass
class OverlapResult:
    """
    Superposición de poros entre pares de imágenes consecutivas.
    """
    # (img1, img2) -> {id_poro_img1: {id_poro_img2, ...}}
    overlaps: Dict[Tuple[str, str], Dict[int, Set[int]]]


@dataclass
class GraphResult:
    """
    Grafo de conectividad entre poros.
    """
    graph: Any                  
    image_order: List[str]      


@dataclass
class InternalPoreComponent:
    """
    Representa un poro 3D interno (componente conexa en el grafo de IDs internos).
    - component_id: índice de la componente (1, 2, 3, ...)
    - pore_ids: IDs de poros 2D que forman este poro 3D.
    - n_pores_2d: cuántos poros 2D lo forman.
    - n_slices: en cuántas imágenes aparece.
    - volume_mm3: volumen aproximado del poro 3D en mm³.
    """
    component_id: int
    pore_ids: List[int]
    n_pores_2d: int
    n_slices: int
    volume_mm3: float


@dataclass
class AnalysisResult:
    """
    Resultado global del análisis.
    """
    segmentation: SegmentationResult
    overlaps: OverlapResult
    graph: GraphResult
    all_pore_ids: Set[int]
    external_pore_ids: Set[int]            # poros conectados al exterior
    internal_pore_ids: Set[int]            # poros totalmente internos
    internal_components: List[InternalPoreComponent]
    total_internal_volume_mm3: float

@dataclass
class ImageAnalysisRecord:
    """
    Métricas 2D por imagen (equivalentes al CSV de analisis.py).
    """
    image_name: str
    pixeles_poro: int
    area_mascara_pixeles: int
    porosidad: float
    area_poros_cm2: float
    longitud_contorno_px: float
    longitud_contorno_cm: float
    area_pared_poros_cm2: float
    porosidad_exterior: float
    area_pared_poros_exteriores_cm2: float
