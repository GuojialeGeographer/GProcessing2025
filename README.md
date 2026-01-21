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
git clone https://github.com/yourusername/svipro.git
cd svipro

# Install dependencies (using uv - recommended)
uv sync --all-extras

# Or using poetry
poetry install
```

### Basic Usage

```python
from svipro import GridSampling, MetadataManager
from shapely.geometry import box

# Define Area of Interest (AOI)
aoi = box(114.15, 22.27, 114.18, 22.30)  # Hong Kong Central

# Initialize sampling strategy
strategy = GridSampling(spacing=100, seed=42)

# Generate sample points
points = strategy.generate(aoi)

# Export with metadata
strategy.to_geojson("sampling_points.geojson")

# Generate protocol documentation
metadata = MetadataManager()
metadata.record_protocol(strategy)
metadata.save("sampling_protocol.yaml")

# Get quality metrics
metrics = strategy.calculate_coverage_metrics()
print(f"Generated {metrics['n_points']} points")
print(f"Density: {metrics['density_pts_per_km2']} pts/km²")
```

### Command Line Interface

```bash
# Basic grid sampling
svipro sample grid --spacing 100 --aoi aoi.geojson --output points.geojson

# Road network sampling
svipro sample road --spacing 50 --network drive --aoi hongkong.geojson --output hk_points.geojson

# Generate protocol
svipro protocol create points.geojson --output protocol.yaml

# Visualize coverage
svipro visualize points.geojson --output coverage_map.html
```

---

## 📋 Features

### Phase 1: Core Sampling Algorithms (MVP)

- **Grid Sampling** - Regular grid-based, fully reproducible
- **Road Network Sampling** - OSM-based, follows street networks
- **Optimized Coverage** - Greedy algorithm for maximum coverage
- **Stratified Random** - Statistically valid random sampling

### Phase 2: Metadata & Reproducibility

- **Protocol Recorder** - Complete documentation of all parameters
- **Quality Metrics** - Coverage density, spatial distribution analysis
- **Reproducibility Reports** - Auto-generate methods sections
- **FAIR Metadata** - Standardized data descriptions

### Phase 3: Visualization & Evaluation

- **Interactive Maps** - Folium-based visualization
- **Coverage Analysis** - Spatial distribution metrics
- **Strategy Comparison** - Compare multiple sampling methods
- **Bias Detection** - Identify under/over-sampled areas

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

### Current Phase: 📝 Planning

- [x] Literature review and gap analysis
- [x] Reference code evaluation (SHAPClab framework)
- [x] Development plan design
- [ ] Core implementation (Milestone 1)

### Development Roadmap

#### Milestone 1: MVP (Week 1-2)
- [ ] Base sampling architecture
- [ ] Grid sampling implementation
- [ ] Basic GeoJSON export
- [ ] Simple CLI interface

#### Milestone 2: Core Features (Week 3-4)
- [ ] Road network sampling (OSMnx)
- [ ] Metadata management system
- [ ] Quality metrics calculation
- [ ] Protocol generation

#### Milestone 3: Visualization (Week 5-6)
- [ ] Interactive maps (folium)
- [ ] Coverage analysis plots
- [ ] Strategy comparison tool
- [ ] Documentation and examples

#### Milestone 4: Testing & Refinement (Week 7-8)
- [ ] Unit tests for all modules
- [ ] Integration tests
- [ ] Performance optimization
- [ ] Case study validation

---

## 📚 Documentation

- [Development Plan](plan.md) - Detailed technical design and implementation roadmap
- [API Documentation](docs/) - (Coming soon)
- [Examples](examples/) - Jupyter notebooks with tutorials (Coming soon)

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
