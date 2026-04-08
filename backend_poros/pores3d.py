from __future__ import annotations

from typing import Dict, Set, Tuple, List

from collections import defaultdict

import numpy as np
import networkx as nx
import trimesh
from trimesh.smoothing import filter_taubin
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes

from .models import (
    MaskConfig,
    GeometryConfig,
    PoreAreaRecord,
    InternalPoreComponent,
)


# --------------------------------------------------------------------
#  Máscaras en 2D
# --------------------------------------------------------------------

def construir_mascara_borde_circular(shape: Tuple[int, int], mask_cfg: MaskConfig) -> np.ndarray:
    """
    Reconstruye una máscara que marca SOLO el borde del cilindro (anillo de 1 píxel aprox),
    usando los mismos parámetros geométricos que en la segmentación.
    """
    h, w = shape
    if not mask_cfg.use_circular_mask:
        # En caso extremo, tomamos el borde del recorte
        borde = np.zeros((h, w), dtype=bool)
        borde[0, :] = borde[-1, :] = True
        borde[:, 0] = borde[:, -1] = True
        return borde

    dy, dx = mask_cfg.circle_center_offset
    cy = h // 2 + dy
    cx = w // 2 + dx
    radio = min(h, w) // 2 - mask_cfg.circle_margin

    Y, X = np.ogrid[:h, :w]
    dist2 = (X - cx) ** 2 + (Y - cy) ** 2

    mascara_exterior = dist2 <= radio ** 2
    if radio > 1:
        mascara_interior = dist2 <= (radio - 1) ** 2
    else:
        mascara_interior = np.zeros_like(mascara_exterior, dtype=bool)

    borde = mascara_exterior & (~mascara_interior)
    return borde


# --------------------------------------------------------------------
#  Detección de poros exteriores / interiores
# --------------------------------------------------------------------

def obtener_todos_los_ids(labels_by_image: Dict[str, np.ndarray]) -> Set[int]:
    """
    Devuelve el conjunto de TODOS los IDs de poros presentes en todas las matrices.
    """
    ids: Set[int] = set()
    for _, matriz in labels_by_image.items():
        matriz = np.array(matriz, dtype=np.int32)
        valores = np.unique(matriz)
        ids.update(v for v in valores if v != 0)
    return ids


def obtener_ids_exteriores(
    labels_by_image: Dict[str, np.ndarray],
    mask_cfg: MaskConfig,
    grafo_ids: nx.Graph,
) -> Tuple[Set[int], Set[int]]:
    """
    Devuelve:
      - semillas_exterior: IDs de poros que tocan base, techo o borde del cilindro.
      - ids_conectados_exterior: todos los poros (por ID) conectados 3D a esas semillas
        (usando el grafo de IDs).
    """
    nombres_imagenes: List[str] = sorted(labels_by_image.keys())

    matriz_0 = np.array(labels_by_image[nombres_imagenes[0]], dtype=np.int32)
    h, w = matriz_0.shape

    mascara_borde = construir_mascara_borde_circular((h, w), mask_cfg)

    # Poros que tocan el borde lateral
    ids_borde: Set[int] = set()
    for nombre in nombres_imagenes:
        matriz = np.array(labels_by_image[nombre], dtype=np.int32)
        valores_borde = np.unique(matriz[mascara_borde])
        ids_borde.update(v for v in valores_borde if v != 0)

    # Poros que tocan base y techo
    matriz_top = np.array(labels_by_image[nombres_imagenes[0]], dtype=np.int32)
    matriz_bottom = np.array(labels_by_image[nombres_imagenes[-1]], dtype=np.int32)

    ids_top = set(np.unique(matriz_top[matriz_top != 0]))
    ids_bottom = set(np.unique(matriz_bottom[matriz_bottom != 0]))

    semillas: Set[int] = ids_borde | ids_top | ids_bottom

    # Expandimos por el grafo
    conectados_exterior: Set[int] = set()
    for s in semillas:
        if s in conectados_exterior:
            continue
        if s not in grafo_ids:
            conectados_exterior.add(s)
            continue

        comp = nx.node_connected_component(grafo_ids, s)
        conectados_exterior.update(comp)

    return semillas, conectados_exterior


# --------------------------------------------------------------------
#  Volumen 3D y STL (para visualización / export)
# --------------------------------------------------------------------

def construir_volumen_3d(
    labels_by_image: Dict[str, np.ndarray],
    pore_ids: Set[int],
) -> Tuple[np.ndarray, List[str]]:
    """
    Construye un volumen 3D booleano donde voxels True corresponden a poros
    cuyos IDs están en `pore_ids`.

    Ejes: (z, y, x)
      - z: índice del corte, según el orden alfabético de los nombres de imagen
      - y, x: coordenadas de píxel en 2D
    """
    nombres_imagenes: List[str] = sorted(labels_by_image.keys())
    matriz_0 = np.array(labels_by_image[nombres_imagenes[0]], dtype=np.int32)
    h, w = matriz_0.shape

    volumen = np.zeros((len(nombres_imagenes), h, w), dtype=bool)

    for z, nombre in enumerate(nombres_imagenes):
        labels = np.array(labels_by_image[nombre], dtype=np.int32)
        mask = np.isin(labels, list(pore_ids))
        volumen[z, :, :] = mask

    return volumen, nombres_imagenes


def recortar_volumen_a_bbox(volumen: np.ndarray) -> np.ndarray | None:
    """
    Recorta el volumen a la bounding box mínima que contiene todos los voxels True.
    Si el volumen está vacío, devuelve None.
    """
    coords = np.argwhere(volumen)
    if coords.size == 0:
        return None

    z_min, y_min, x_min = coords.min(axis=0)
    z_max, y_max, x_max = coords.max(axis=0) + 1

    return volumen[z_min:z_max, y_min:y_max, x_min:x_max]


def suavizar_volumen_gaussiano(
    volumen: np.ndarray,
    sigma_z: float = 0.6,
    sigma_xy: float = 1.0,
) -> np.ndarray:
    """
    Aplica suavizado gaussiano 3D a un volumen booleano o numérico.
    Devuelve un volumen float suavizado.
    """
    volumen_float = volumen.astype(np.float32)
    return gaussian_filter(
        volumen_float,
        sigma=(sigma_z, sigma_xy, sigma_xy)
    )


def extraer_malla_desde_volumen(
    volumen: np.ndarray,
    geom_cfg: GeometryConfig,
    level: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extrae vertices y caras desde un volumen usando marching_cubes.
    """
    verts, faces, normals, values = marching_cubes(
        volumen,
        level=level,
        spacing=(
            geom_cfg.slice_distance_mm,
            geom_cfg.pixel_size_mm,
            geom_cfg.pixel_size_mm,
        )
    )
    return verts, faces


def suavizar_malla_taubin(
    verts: np.ndarray,
    faces: np.ndarray,
    iteraciones: int = 10,
    lamb: float = 0.5,
    nu: float = -0.53,
) -> trimesh.Trimesh:
    """
    Aplica suavizado Taubin a una malla triangulada.
    """
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    filter_taubin(mesh, lamb=lamb, nu=nu, iterations=iteraciones)
    return mesh

def volumen_a_stl(
    volumen: np.ndarray,
    geom_cfg: GeometryConfig,
    ruta_stl: str,
) -> None:
    """
    Convierte un volumen a STL sin aplicar suavizados.
    Si el volumen es booleano/uint8, marching_cubes trabaja directo.
    Si el volumen ya viene suavizado en float, también funciona.
    """

   
    if not np.any(volumen):
        raise ValueError("El volumen está vacío; no se puede generar STL.")

    verts, faces = extraer_malla_desde_volumen(volumen, geom_cfg, level=0.5)

    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    mesh.export(ruta_stl)

# --------------------------------------------------------------------
#  Componentes internas y volúmenes (versión "área × distancia")
# --------------------------------------------------------------------

def compute_internal_components(
    graph_ids: nx.Graph,
    internal_ids: Set[int],
) -> List[Set[int]]:
    """
    Devuelve una lista de componentes conexas internas (poros 3D cerrados).
    Cada componente es un conjunto de IDs de poros 2D (ints).
    """
    subgraph = graph_ids.subgraph(internal_ids)
    components = [set(comp) for comp in nx.connected_components(subgraph)]
    return components


def compute_internal_components_volumes(
    components: List[Set[int]],
    pore_areas: List[PoreAreaRecord],
    geom_cfg: GeometryConfig,
) -> List[InternalPoreComponent]:
    """
    A partir de:
      - components: lista de componentes de IDs internos (poros 3D),
      - pore_areas: lista global de áreas 2D,
      - geom_cfg: tamaño de píxel y distancia entre cortes,
    calcula el volumen de cada componente interna.
    """
    # Mapeo ID -> lista de registros de área
    areas_by_pore: Dict[int, List[PoreAreaRecord]] = defaultdict(list)
    for rec in pore_areas:
        areas_by_pore[rec.pore_id].append(rec)

    internal_components: List[InternalPoreComponent] = []

    # factor de conversión de área píxel^2 -> mm^2
    area_factor = geom_cfg.pixel_size_mm ** 2
    dz = geom_cfg.slice_distance_mm

    for idx, comp_ids in enumerate(sorted(components, key=lambda s: min(s)), start=1):
        # Reunimos todas las áreas de todos los poros 2D de esta componente
        registros: List[PoreAreaRecord] = []
        for pid in comp_ids:
            registros.extend(areas_by_pore.get(pid, []))

        if not registros:
            # No hay info de área para esos IDs
            continue

        # Slices en los que aparece
        slices_names = {r.image_name for r in registros}
        n_slices = len(slices_names)

        # Suma de áreas en píxeles^2
        suma_area_px2 = sum(r.area_px for r in registros)

        # Área en mm^2
        suma_area_mm2 = suma_area_px2 * area_factor

        # Volumen en mm^3 (aprox): sum A(z) * dz  -> aquí usamos suma total * dz
        volume_mm3 = suma_area_mm2 * dz

        internal_components.append(
            InternalPoreComponent(
                component_id=idx,
                pore_ids=sorted(comp_ids),
                n_pores_2d=len(comp_ids),
                n_slices=n_slices,
                volume_mm3=volume_mm3,
            )
        )

    return internal_components
