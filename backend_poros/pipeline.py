from __future__ import annotations

from typing import List, Tuple

from .models import (
    MaskConfig,
    ThresholdConfig,
    GeometryConfig,
    AnalysisResult,
    StlExportConfig,
)
from .segmentation import procesar_imagenes
from .overlaps import calcular_superposiciones
from .graph_3d import construir_grafo_ids
from .pores3d import (
    obtener_todos_los_ids,
    obtener_ids_exteriores,
    construir_volumen_3d,
    recortar_volumen_a_bbox,
    volumen_a_stl,
    suavizar_volumen_gaussiano,
    extraer_malla_desde_volumen,
    suavizar_malla_taubin,
    compute_internal_components,
    compute_internal_components_volumes,
)


def run_full_analysis(
    image_paths: List[str],
    mask_cfg: MaskConfig,
    thr_cfg: ThresholdConfig,
    geom_cfg: GeometryConfig,
) -> AnalysisResult:
    """
    Ejecuta TODO el pipeline:
      1) Segmenta poros en cada corte
      2) Calcula superposiciones entre cortes consecutivos
      3) Construye el grafo 3D por ID
      4) Detecta poros conectados al exterior (base, techo, borde)
      5) Determina poros internos (cerrados)
      6) Agrupa poros internos en componentes 3D y calcula volúmenes mm³

    Devuelve AnalysisResult con toda la información necesaria para la GUI.
    """
    # 1) Segmentación 2D
    seg_result = procesar_imagenes(image_paths, mask_cfg, thr_cfg)

    # 2) Superposiciones entre cortes
    overlaps = calcular_superposiciones(seg_result.labels_by_image)

    # 3) Grafo de IDs
    graph_result = construir_grafo_ids(overlaps)

    # 4) Poros exteriores / interiores
    _, ids_conectados_exterior = obtener_ids_exteriores(
        seg_result.labels_by_image,
        mask_cfg,
        graph_result.graph,
    )

    ids_todos = obtener_todos_los_ids(seg_result.labels_by_image)
    external_ids = ids_conectados_exterior
    internal_ids = ids_todos - external_ids

    # 5) Componentes internas (poros 3D cerrados)
    internal_components_sets = compute_internal_components(
        graph_result.graph,
        internal_ids,
    )

    # 6) Calcular volúmenes de poros internos

    internal_components = compute_internal_components_volumes(
        internal_components_sets,
        seg_result.pore_areas,
        geom_cfg,
    )

    total_internal_volume_mm3 = sum(c.volume_mm3 for c in internal_components)

    return AnalysisResult(
        segmentation=seg_result,
        overlaps=overlaps,
        graph=graph_result,
        all_pore_ids=ids_todos,
        external_pore_ids=external_ids,
        internal_pore_ids=internal_ids,
        internal_components=internal_components,
        total_internal_volume_mm3=total_internal_volume_mm3,
    )


def export_pores_stl(
    analysis: AnalysisResult,
    geom_cfg: GeometryConfig,
    ruta_stl: str,
    export_cfg: StlExportConfig,
) -> tuple[int, str]:

    tipo = export_cfg.tipo
    aplicar_gaussiano = export_cfg.aplicar_gaussiano
    aplicar_taubin = export_cfg.aplicar_taubin
    sigma_z = export_cfg.sigma_z
    sigma_xy = export_cfg.sigma_xy
    iteraciones_taubin = export_cfg.iteraciones_taubin

    if tipo == "Internal":
        pore_ids = analysis.internal_pore_ids
        nombre = "poros_internos"
    elif tipo == "External":
        pore_ids = analysis.external_pore_ids
        nombre = "poros_externos"
    elif tipo == "All":
        pore_ids = analysis.all_pore_ids
        nombre = "poros_todos"
    else:
        raise ValueError("tipo debe ser 'Internal', 'External' o 'All'")

    if not pore_ids:
        raise ValueError(f"No hay poros {tipo} para exportar.")

    volumen, _ = construir_volumen_3d(
        analysis.segmentation.labels_by_image,
        pore_ids,
    )

    volumen_recortado = recortar_volumen_a_bbox(volumen)
    if volumen_recortado is None:
        raise ValueError("El volumen está vacío después del recorte.")

    volumen_para_exportar = volumen_recortado

    if aplicar_gaussiano:
        volumen_para_exportar = suavizar_volumen_gaussiano(
            volumen_para_exportar,
            sigma_z=sigma_z,
            sigma_xy=sigma_xy,
        )

    if aplicar_taubin:
        verts, faces = extraer_malla_desde_volumen(
            volumen_para_exportar,
            geom_cfg,
            level=0.5,
        )
        mesh = suavizar_malla_taubin(
            verts,
            faces,
            iteraciones=iteraciones_taubin,
        )
        mesh.export(ruta_stl)
    else:
        volumen_a_stl(
            volumen_para_exportar,
            geom_cfg,
            ruta_stl,
        )

    return len(pore_ids), ruta_stl




