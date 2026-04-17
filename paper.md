---
title: "CPA-CECOVI-Pore-Analysis: An open-source XCT workflow for pore characterization in pervious concrete"
tags:
  - Python
  - X-ray computed tomography
  - pervious concrete
  - pore network
  - image analysis
  - materials characterization
authors:
  - name: Fernando Fogliatti
    orcid: 0009-0002-1738-1447
    affiliation: 1
    corresponding: true
    email: ffogliatti@utn.frsf.edu.ar
  - name: María Fernanda Carrasco
    orcid: 0000-0002-5349-0969
    affiliation: 1
    email: mcarrasco@utn.frsf.edu.ar
affiliations:
  - name: Centro de Investigación y Desarrollo para la Construcción y la Vivienda, Argentina
    index: 1
date: 17 April 2026
bibliography: paper.bib
---

# Summary

Pervious concrete is defined by a connected pore network that controls infiltration, drainage performance, and clogging susceptibility @tennis2004. Its hydraulic and mechanical behaviour is strongly governed by pore structure attributes such as connected porosity, pore size distribution, and tortuosity, which has motivated sustained interest in image-based characterization approaches @rao2021. X-ray computed tomography (XCT) can capture that internal structure in three dimensions, but transforming image stacks into reproducible descriptors commonly requires proprietary software or advanced scripting workflows.

CPA-CECOVI-Pore-Analysis addresses that gap with an open-source Python workflow for pore-network analysis in pervious concrete. The software loads ordered XCT slices, applies region-of-interest and circular-mask definitions, supports manual or Otsu-based thresholding @otsu1979 with optional smoothing, labels pores on each slice, links overlapping pores between consecutive slices, and builds a three-dimensional connectivity model based on graphs. From that model, the tool distinguishes externally connected pores from isolated internal pores, estimates per-slice porosity metrics, and exports three-dimensional geometries in STL together with CSV reports.

The package was designed so that researchers and laboratories with limited access to commercial image-analysis platforms can obtain a transparent, auditable, and reusable workflow for pore characterization from XCT data.

# Statement of need

The internal architecture of pervious concrete controls hydraulic conductivity, available void ratio, and the balance between permeability and mechanical integrity. Because of this, pore-network characterization is central both to mixture design and to research on durability, clogging, and transport phenomena @tennis2004.

Several studies have shown the value of XCT for measuring pore structure and for reconstructing virtual pore networks in permeable concrete and other porous materials @zhang2018. More broadly, XCT has matured from a qualitative inspection technique into a quantitative measurement framework for materials characterization, provided that segmentation, calibration, and uncertainty sources are handled transparently @maire2014; @rodriguezsanchez2020. Related work on pore-network extraction from micro-CT images also highlights the importance of explicit connectivity reconstruction when moving from voxel data to interpretable pore descriptors @dong2009. Yet practical workflows remain difficult to reproduce when they depend on closed software, undocumented manual steps, or custom scripts that are not packaged for reuse.

CPA-CECOVI-Pore-Analysis was developed to provide an accessible workflow that connects laboratory XCT images with quantitative descriptors of pore geometry and connectivity. Beyond pervious concrete, the same workflow can support exploratory studies on other porous materials when image stacks and geometric calibration are available.

# Workflow and implementation

The software is organized as a modular backend--frontend architecture. A dedicated analysis pipeline coordinates segmentation, overlap detection, graph construction, classification of exterior and interior pores, and export operations. The graphical user interface exposes the pipeline to non-programmer users while preserving the same computational core used by the backend modules. This design follows broadly accepted recommendations for reusable and transparent scientific software, particularly the need for documented, auditable, and modular computational workflows @ince2012; @wilson2017.

During segmentation, each slice is cropped to a user-defined region of interest and optionally constrained by a circular mask consistent with cylindrical specimens. Grayscale images can be smoothed before thresholding; the package supports manual thresholds and Otsu-based threshold selection. Connected-component labeling is then applied on each slice, and pore identifiers are offset so that labels remain unique across the full stack.

Three-dimensional connectivity is reconstructed by comparing consecutive slices and registering partial spatial overlap between pores. Seed pores that touch the specimen border or appear on the first or last slice are used to propagate connectivity and classify all pores as externally connected or isolated internal components.

For quantitative analysis, the workflow computes per-image porosity, pore area, contour length, and pore-wall area estimates, and exports these values as CSV files. Internal connected components can also be grouped into three-dimensional pore bodies, assigned approximate volumes from slice area accumulation and calibrated voxel spacing, and exported as STL meshes. Optional Gaussian smoothing of the volume and Taubin smoothing of the extracted mesh are available before export.

# Typical outputs and reuse potential

The intended use case is the analysis of XCT image series obtained from cylindrical pervious concrete specimens. In that setting, the software helps laboratories move from tomographic slices to metrics that are directly interpretable in materials research, such as porosity by slice, pore-wall area proxies, internal pore volumes, and connected versus isolated void structure.

The STL export supports visualization and downstream geometric analysis, while the CSV outputs facilitate statistical post-processing and comparison between mixture designs. Because the workflow is open and modular, it can also serve as a base for future extensions such as more robust segmentation strategies, additional morphological descriptors, or tighter integration with hydraulic simulation workflows and open pore-network modeling environments.

# Availability

The project is publicly available on GitHub at `FernandoFog/CPA-CECOVI-Pore-Analysis`. The codebase includes a modular backend, a graphical desktop interface, CSV export for two-dimensional metrics, and STL export for reconstructed pore volumes.

# Acknowledgements

This work was supported by the Secretaría de Ciencia, Tecnología y Posgrado of Universidad Tecnológica Nacional through research project ECTCFE0008795TC.
