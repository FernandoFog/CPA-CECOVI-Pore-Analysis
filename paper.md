---
title: "CPA-CECOVI-Pore-Analysis: An open-source XCT workflow for pore characterization in pervious concrete"
tags:
  - Python
  - X-ray computed tomography
  - pervious concrete
  - porous materials
  - image analysis
  - pore connectivity
authors:
  - name: Fernando Fogliatti
    orcid: 0009-0002-1738-1447
    affiliation: "1"
  - name: María Fernanda Carrasco
    orcid: 0000-0002-5349-0969
    affiliation: "1"
affiliations:
  - index: 1
    name: Centro de Investigación y Desarrollo para la Construcción y la Vivienda, Argentina
date: 18 April 2026
bibliography: paper.bib
---

# Summary

Pervious concrete contains an interconnected void structure that allows water to pass through the material. This pore system controls drainage, infiltration, and susceptibility to clogging, and it also affects mechanical performance [@tennis2004; @rao2021]. X-ray computed tomography (XCT) can image that internal structure in three dimensions, but turning XCT slices into reproducible pore descriptors often requires commercial software, undocumented manual decisions, or custom scripts that are difficult to reuse.

CPA-CECOVI-Pore-Analysis is an open-source Python workflow for analyzing pore structure in pervious concrete from ordered XCT image stacks. The software combines image preprocessing, pore segmentation, slice-to-slice connectivity reconstruction, two-dimensional quantitative metrics, and three-dimensional export in a single package. It supports region-of-interest cropping, circular masking for cylindrical specimens, manual or Otsu-based thresholding, connected-component labeling, graph-based reconstruction of pore connectivity, classification of externally connected versus isolated internal pores, and export of CSV tables and STL geometries.

The package is designed for researchers and laboratories that need a transparent and reusable workflow for XCT-based pore characterization without depending on proprietary platforms. Although it was developed for pervious concrete, the same workflow can be adapted to other porous materials when ordered image stacks and geometric calibration are available.

# Statement of need

The hydraulic behavior of pervious concrete is governed by its internal pore network. Parameters such as connected porosity, pore size distribution, and connectivity influence permeability, clogging resistance, and the balance between drainage capacity and structural integrity [@tennis2004; @rao2021]. For that reason, pore-network characterization is central to research on mixture design, durability, and transport phenomena in permeable cementitious materials.

XCT has become an important tool for quantitative materials characterization, provided that segmentation choices, calibration, and uncertainty sources are handled transparently [@maire2014; @rodriguez2020]. In pervious concrete and related porous materials, previous studies have used XCT to investigate pore geometry and seepage-relevant structure [@zhang2018]. However, many practical workflows still depend on combinations of general-purpose image-analysis tools, closed commercial environments, or lab-specific scripts that are hard to audit and reproduce.

CPA-CECOVI-Pore-Analysis was developed to address that gap. Its target users are researchers and laboratories that need an accessible workflow connecting XCT slices to quantitative pore descriptors and three-dimensional pore reconstructions. The software is intended to reduce the amount of manual glue code required to move from raw tomographic data to metrics that can be compared across specimens and studies.

# State of the field

Open-source and commercial tools already exist for analyzing tomographic images. For example, PoreSpy provides a broad set of methods for quantitative analysis of porous-media images obtained from tomography and related sources [@Gostick2019]. Commercial platforms such as Avizo and Dragonfly provide powerful environments for 3D visualization, segmentation, quantification, and reporting from CT and microscopy data, but they are general platforms rather than specimen-oriented open workflows for a specific research use case [@avizo; @dragonfly].

CPA-CECOVI-Pore-Analysis is not intended to replace broad porous-media ecosystems or full commercial imaging suites. Its contribution is narrower and more application-specific: it packages a complete open workflow for XCT analysis of cylindrical pervious-concrete specimens, with explicit support for specimen masking, pore labeling across image stacks, overlap-based connectivity reconstruction, classification of externally connected and isolated pores, per-slice CSV exports, and STL generation from reconstructed internal pore bodies. In that sense, the software addresses a “build versus contribute” niche where the research need is not just image analysis in general, but a reproducible end-to-end workflow tailored to the pore characterization questions commonly encountered in pervious concrete studies.

# Software design

The software follows a modular backend-frontend design. The backend separates major tasks into analysis stages, including segmentation, overlap detection between consecutive slices, graph construction, pore classification, and export. The graphical user interface exposes these capabilities to non-programmer users while preserving a reusable computational core. This architecture was chosen so that the same scientific logic can support both interactive use in laboratories and future scripted extensions.

A central design decision is to reconstruct three-dimensional connectivity from explicit overlap relationships between labeled pores on adjacent slices. Instead of treating each slice independently, the workflow propagates connectivity through the full image stack and uses seed pores touching specimen boundaries or appearing at the first or last slice to classify pore systems as externally connected or isolated internal components. This choice matters for the intended research application because hydraulic relevance in pervious concrete depends not only on local pore area, but also on whether the void structure forms connected pathways through the specimen [@tennis2004; @zhang2018].

A second design choice is to preserve transparency in segmentation and export. Users can define the region of interest, apply a circular mask consistent with cylindrical specimens, smooth grayscale images when appropriate, and choose between manual and Otsu-based thresholding [@otsu1979]. The workflow then reports interpretable outputs such as per-image porosity, pore area, contour length, pore-wall area proxies, approximate pore-body volumes, and STL meshes. This balances usability and auditability: the interface lowers the barrier to use, while the staged pipeline keeps the computational steps explicit.

# Research impact statement

CPA-CECOVI-Pore-Analysis makes a previously fragmented analysis process available as a public, reusable software package for pore characterization from XCT image stacks. At the time of writing, the project is an early public release rather than a mature community standard, so its strongest evidence of near-term significance is not citation count or widespread downstream adoption. Instead, its impact lies in converting a domain-specific workflow into an openly inspectable and distributable research tool that can be used, evaluated, and extended by other laboratories working on pervious concrete and related porous materials.

The repository is publicly available, distributed under an open-source license, and includes installation instructions and a tagged release. These features lower the barrier for reuse and make the workflow easier to reproduce in academic settings. The immediate research value is that the software enables consistent extraction of pore metrics and 3D geometries from XCT data, which supports comparison among specimens, mixture designs, and future experimental campaigns. The same design also makes the package a practical base for later extensions, such as alternative segmentation strategies, additional morphological descriptors, or tighter coupling with simulation-oriented porous-media tools.

# AI usage disclosure

Generative AI tool (Chat GPT 5.4) were used to assist with language editing and structural revision of the manuscript text. All software descriptions, methodological claims, and references were reviewed and verified by the authors against the repository contents and the cited literature. No AI-generated content was accepted without human review and correction.

# Acknowledgements

This work was supported by the Secretaría de Ciencia, Tecnología y Posgrado of Universidad Tecnológica Nacional through research project ECTCFE0008795TC.