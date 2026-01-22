# SVIPro

**SVI Research Protocol & Optimization**: A Standardized Framework for Reproducible Street View Imagery Sampling Design

[English](README.md) | [中文](README.zh.md) | [Development Plan](plan.md)

---

## 🎯 Project Vision

SVIPro addresses a critical methodological gap in urban studies: **the lack of standardized, transparent, and reproducible sampling methodologies for Street View Imagery (SVI) research**.

### The Problem

Current SVI research suffers from:
- ❌ Arbitrary sampling intervals with no scientific basis
- ❌ Incomplete spatial coverage or redundant data collection
- ❌ Black-box methodologies that cannot be reproduced
- ❌ Inability to compare studies across different regions

### Our Solution

A **scientific, reproducible, and documented** sampling design framework that:
- ✅ Generates standardized sampling protocols (not mass crawling)
- ✅ Provides multiple scientifically-grounded sampling strategies
- ✅ Ensures complete methodological transparency
- ✅ Enables reproducibility (same AOI + same parameters = identical results)
- ✅ Complies with legal and ethical standards (no unauthorized crawling)

---

## 👥 Authors

- **Jiale Guo** - [jiale.guo@mail.polimi.it](mailto:jiale.guo@mail.polimi.it)
- **Mingfeng Tang** - [mingfeng.tang@mail.polimi.it](mailto:mingfeng.tang@mail.polimi.it)

Geoinformatics Engineering graduate students at Politecnico di Milano

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/GuojialeGeographer/GProcessing2025.git
cd GProcessing2025

# Install in development mode
pip install -e .

# Verify installation
svipro --help
```

### Python API Usage

```python
from svipro import GridSampling, SamplingConfig
from shapely.geometry import box

# Define Area of Interest (AOI)
aoi = box(114.15, 22.27, 114.18, 22.30)  # Hong Kong Central

# Initialize sampling strategy
strategy = GridSampling(SamplingConfig(spacing=100, seed=42))

# Generate sample points
points = strategy.generate(aoi)

# Export with metadata
strategy.to_geojson("sampling_points.geojson")

# Calculate quality metrics
metrics = strategy.calculate_coverage_metrics()
print(f"Generated {metrics['n_points']} points")
print(f"Density: {metrics['density_pts_per_km2']:.2f} pts/km²")
```

### Command Line Interface

```bash
# Grid sampling
svipro sample grid --spacing 100 --aoi aoi.geojson --output points.geojson

# Road network sampling
svipro sample road-network --spacing 100 --network-type drive --aoi hk.geojson --output hk_points.geojson

# Quality metrics
svipro quality metrics --points samples.geojson

# Generate protocol
svipro protocol create --points samples.geojson --output protocol.yaml

# Interactive map
svipro visualize points-map --points samples.geojson --output map.html

# Statistics plots
svipro visualize statistics --points samples.geojson --output stats.png

# Strategy comparison
svipro visualize compare --aoi boundary.geojson --output comparison.png
```

---

## 📋 Features

### ✅ Implemented Features (v0.1.0)

#### Sampling Strategies
- **Grid Sampling** - Regular grid-based, fully reproducible
  - Uniform spatial coverage
  - Configurable spacing and alignment
  - Seed-based reproducibility

- **Road Network Sampling** - OSM-based, follows street networks
  - OSMnx integration for automatic road network download
  - Configurable network types (all, walk, drive, bike)
  - Road type filtering (19 OSM highway types)

#### Quality Assessment
- **Coverage Metrics** - Point density, area, spatial extent
- **Road Network Metrics** - Edge count, node count, total length, connectivity
- **Quality Visualization** - Interactive statistics plots

#### Metadata & Documentation
- **Protocol Generation** - YAML-based sampling protocol files
- **Metadata Export** - GeoJSON with complete parameter documentation
- **Timestamp Tracking** - ISO 8601 timestamps for reproducibility

#### Visualization Tools
- **Interactive Maps** - Folium-based web maps
- **Statistics Plots** - Matplotlib/Seaborn statistical visualizations
- **Strategy Comparison** - Multi-strategy comparison plots
- **Coverage Analysis** - Spatial distribution heatmaps, nearest neighbor analysis

#### Command-Line Interface
- **Complete CLI** - All functionality accessible via command line
- **Colored Output** - User-friendly terminal messages
- **Error Handling** - Comprehensive validation and error messages

### 🚧 Planned Features (Future Releases)

- Optimized Coverage - Greedy algorithm for maximum coverage
- Stratified Random - Statistically valid random sampling
- API Cost Estimation - Cost estimation for legal API usage
- Multi-source Comparison - Compare across different SVI providers

---

## 🔬 Research Background

This project is inspired by and improves upon:

> **Wang et al. (2025)** - Cross-platform complementarity: Assessing the data quality and availability of Google Street View and Baidu Street View. *Transactions in Urban Data, Science, and Technology*. DOI: 10.1177/27541231241311474

### Key Contributions from Reference

1. **Spider-Web Collection Method** - Systematic metadata discovery
2. **Metadata-Driven Approach** - Focus on documentation
3. **Quality Assessment Framework** - Multi-dimensional evaluation

### Our Innovations

1. ✅ **Better Code Architecture** - Modular, extensible design
2. ✅ **Reproducibility Guarantees** - Seed-based deterministic algorithms
3. ✅ **Compliance-First** - No crawling, only protocol generation
4. ✅ **Multiple Strategies** - Not just spider-web, but grid, road-based, etc.
5. ✅ **User-Friendly Interface** - Both Python API and CLI
6. ✅ **Quality Metrics** - Built-in coverage and bias analysis

---

## 🛠️ Technical Stack

**Geospatial Processing**:
- geopandas, shapely, pyproj, osmnx, networkx

**Data & Math**:
- numpy, pandas, scipy, scikit-learn

**Visualization**:
- matplotlib, seaborn, folium

**Utilities**:
- pyyaml, click

See [pyproject.toml](pyproject.toml) for complete dependency list.

---

## 📊 Project Status

### Current Version: v0.1.0 (January 2025)

**Development Progress**: Core features completed

### ✅ Completed Milestones

#### Milestone 1: MVP ✅
- [x] Base sampling architecture
- [x] Grid sampling implementation (32 unit tests)
- [x] Road network sampling (21 unit tests)
- [x] GeoJSON export with metadata
- [x] Complete CLI interface

#### Milestone 2: Core Features ✅
- [x] Road network sampling with OSMnx
- [x] Quality metrics calculation
- [x] Protocol generation
- [x] Enhanced CLI with all commands

#### Milestone 3: Visualization ✅
- [x] Interactive maps (Folium)
- [x] Statistics plots (Matplotlib/Seaborn)
- [x] Strategy comparison visualization
- [x] Documentation and tutorials

#### Milestone 4: Testing & Documentation ✅
- [x] 80 unit tests (all passing)
- [x] Getting started tutorial
- [x] API reference documentation
- [x] Case study (Hong Kong urban green space)
- [x] Complete README and user guides

### 📈 Test Coverage

- **Total Tests**: 80 unit tests
- **Sampling Module**: 53 tests
  - Base architecture: 27 tests
  - Grid sampling: 32 tests
  - Road network sampling: 21 tests
- **Pass Rate**: 100%
- **Coverage**: Core functionality fully tested

### 📚 Documentation

- **Tutorials**: `docs/tutorials/getting_started.md`
- **API Reference**: `docs/api_reference.md`
- **Case Studies**: `docs/case_studies/hong_kong_urban_green_space.md`
- **README**: Comprehensive project documentation
- **Progress Tracking**: `memory-bank/progress.md`

---

## 📚 Documentation

### User Documentation

- **[Getting Started Guide](docs/tutorials/getting_started.md)** - Comprehensive tutorial for new users
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[Case Study: Hong Kong](docs/case_studies/hong_kong_urban_green_space.md)** - Real-world application example

### Developer Documentation

- **[Development Plan](plan.md)** - Technical design and implementation roadmap
- **[Memory Bank](memory-bank/)** - Development progress tracking
- **[Architecture](memory-bank/architecture.md)** - System architecture documentation
- **[Tech Stack](memory-bank/tech-stack.md)** - Technology choices and rationale

### Documentation Links

| Document | Description | Audience |
|----------|-------------|----------|
| Getting Started | Step-by-step tutorial | New users |
| API Reference | Complete API docs | Developers |
| Case Studies | Real-world examples | Researchers |
| Development Plan | Technical design | Contributors |

### Examples and Tutorials

```bash
# Quick start examples
cd examples/

# Grid sampling example
python grid_sampling_example.py

# Road network sampling example
python road_network_example.py

# Visualization example
python visualization_example.py
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License. See [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- Reference implementation: [SHAPClab_Quality-and-Availability-of-GSV-BSV](./SHAPClab_Quality-and-Availability-of-GSV-BSV/)
- Developed as part of the **Geospatial Processing** course at Politecnico di Milano
- Inspired by the methodological gaps identified in Wang et al. (2025)

---

## 🔮 Future Roadmap

### Phase 4: API Cost Optimization (Future)
- Cost estimator for legal API usage
- Sampling optimization algorithms
- Multi-source comparison tools

### Research Contributions
This project aims to enable:
1. **Methodological papers** on sampling standardization
2. **Software papers** in *SoftwareX* or *JOSS*
3. **Reproducible urban studies** using standardized protocols

---

**Status**: 📝 Planning - [See Development Plan](plan.md) for details
