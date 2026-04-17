# CPA-CECOVI-Pore-Analysis

An open-source Python workflow for pore characterization in pervious concrete using X-ray computed tomography (XCT).

## 🔬 Overview

CPA-CECOVI-Pore-Analysis is a modular software tool designed to analyze pore structures from XCT image stacks. It provides a reproducible and transparent workflow for segmenting pores, reconstructing 3D connectivity, and extracting quantitative metrics.

The software is particularly suited for pervious concrete analysis but can be extended to other porous materials.



## ⚙️ Features

- Image preprocessing (ROI cropping and circular masking)
- Thresholding (manual or Otsu)
- Optional smoothing (median + Gaussian)
- 2D pore labeling per slice
- 3D pore connectivity reconstruction using graphs
- Classification of:
  - Connected (external) pores
  - Internal (isolated) pores
- Export:
  - CSV (per-image metrics)
  - STL (3D pore geometry)

## 🧠 How it works (high level)

The pipeline follows these steps:

1. **Segmentation**
   - Each XCT slice is processed and pores are identified
   - Implemented in: `segmentation.py` 

2. **Overlap detection**
   - Pores are linked across consecutive slices
   - Implemented in: `overlaps.py` 

3. **3D graph construction**
   - Connectivity is represented as a graph
   - Implemented in: `graph_3d.py` 

4. **Pore classification**
   - External vs internal pores are identified
   - Implemented in: `pores3d.py` 

5. **Analysis**
   - Per-image metrics and volumetric properties
   - Implemented in: `analysis_2d.py` 

6. **Pipeline execution**
   - Full workflow orchestration
   - Implemented in: `pipeline.py` 

## 📦 Installation

```bash
git clone https://github.com/FernandoFog/CPA-CECOVI-Pore-Analysis
cd CPA-CECOVI-Pore-Analysis
pip install -r requirements.txt
