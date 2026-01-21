# SVIPro Development Plan

**SVI Research Protocol & Optimization**: A Standardized Framework for Reproducible Street View Imagery Sampling Design

---

## 1. Model & Methodology

### 1.1 Core Problem Statement

Current SVI (Street View Imagery) research suffers from **non-standardized, non-transparent, and irreproducible data sampling methodologies**, leading to:

- ❌ Arbitrary sampling intervals (50m? 100m? No scientific basis)
- ❌ Incomplete spatial coverage or redundant data
- ❌ Geographic coordinate discrepancies between planned and actual SVI locations
- ❌ Black-box methodology that cannot be reproduced
- ❌ Inability to compare studies across different regions/scales

### 1.2 Our Solution: Standardized Sampling Framework

Based on the **"Spider-Web Collection Method"** (Wang et al., 2025), we provide a **scientific, reproducible, and documented** sampling design framework that **does NOT crawl SVI data** but instead **generates standardized sampling protocols**.

**Key Innovations**:

1. **Scientific Sampling Strategies** - Multiple algorithms with transparent parameters
2. **Metadata-Driven Protocol** - Complete documentation of all sampling decisions
3. **Reproducibility Guarantee** - Same AOI + same parameters = identical results
4. **Quality Assessment** - Built-in coverage metrics and bias detection
5. **Compliance-First** - Outputs protocols for legal API usage, not mass crawling

---

## 2. Implementation Vision

### Phase 1: Core Sampling Algorithms (MVP)
**Goal**: Provide scientific alternative to arbitrary grid sampling

**Features**:
- ✅ Grid Sampling (baseline, reproducible)
- ✅ Road Network Sampling (OSM-based, follows streets)
- ✅ Optimized Coverage Sampling (greedy algorithm)
- ✅ Stratified Random Sampling (statistical validity)

**Output**: GeoJSON with sampling points + complete metadata YAML

### Phase 2: Metadata & Reproducibility
**Goal**: Ensure complete methodological transparency

**Features**:
- ✅ Protocol Recorder (tracks all parameters, timestamps, versions)
- ✅ Metadata Generator (FAIR-principled data description)
- ✅ Quality Metrics (coverage density, spatial distribution analysis)
- ✅ Reproducibility Report (auto-generate methods section)

**Output**: Standardized protocol files for publication

### Phase 3: Visualization & Evaluation
**Goal**: Help researchers understand and validate their sampling design

**Features**:
- ✅ Interactive Maps (folium-based visualization)
- ✅ Coverage Analysis (spatial distribution metrics)
- ✅ Comparative Tool (compare multiple sampling strategies)
- ✅ Bias Detection (identify under/over-sampled areas)

**Output**: Publication-ready figures and quality reports

### Phase 4: API Cost Optimization (Future)
**Goal**: Make legal API usage affordable for researchers

**Features**:
- ⏳ Cost Estimator (calculate API costs before collection)
- ⏳ Sampling Optimization (minimize points while maximizing coverage)
- ⏳ Duplicate Detection (avoid redundant API calls)
- ⏳ Multi-Source Comparison (GSV vs BSV vs Mapillary)

---

## 3. Technical Stack

### 3.1 Core Dependencies
```yaml
Geospatial Processing:
  - geopandas >= 0.14.0    # Spatial data handling
  - shapely >= 2.0.0       # Geometric operations
  - pyproj >= 3.6.0        # Coordinate transformations
  - osmnx >= 2.0.0         # OpenStreetMap road networks
  - networkx >= 3.1        # Graph algorithms

Data & Math:
  - numpy >= 1.24.0        # Numerical computing
  - pandas >= 2.0.0        # Data manipulation
  - scipy >= 1.10.0        # Spatial algorithms
  - scikit-learn >= 1.3.0  # Clustering and optimization

Visualization:
  - matplotlib >= 3.7.0    # Static plots
  - seaborn >= 0.12.0      # Statistical visualization
  - folium >= 0.14.0       # Interactive maps

Utilities:
  - pyyaml >= 6.0.0        # Configuration files
  - click >= 8.1.0         # CLI interface
```

### 3.2 Architecture

```
svipro/
├── sampling/              # Sampling strategies
│   ├── base.py           # Abstract base class
│   ├── grid.py           # Regular grid sampling
│   ├── road_network.py   # OSM-based road sampling
│   └── optimized.py      # Coverage-optimized sampling
│
├── metadata/              # Metadata management
│   ├── protocol.py       # Protocol recording
│   ├── quality.py        # Quality metrics
│   └── export.py         # GeoJSON/YAML export
│
├── reproducibility/       # Framework for reproducibility
│   └── recorder.py       # Automatic method documentation
│
├── visualization/         # Visualization tools
│   ├── maps.py           # Interactive maps (folium)
│   ├── analysis.py       # Coverage analysis
│   └── comparison.py     # Strategy comparison
│
└── utils/                 # Utilities
    ├── spatial.py        # Spatial helper functions
    └── validation.py     # Input validation
```

### 3.3 Design Principles

1. **Modularity** - Each sampling strategy is independent and swappable
2. **Transparency** - Every parameter is logged and documented
3. **Testability** - Deterministic algorithms (seed-based random)
4. **Extensibility** - Easy to add new sampling strategies
5. **Compliance** - No crawling, only protocol generation

---

## 4. User Interface

### 4.1 Python API

#### Basic Usage

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

#### Advanced Usage: Compare Strategies

```python
from svipro import GridSampling, RoadNetworkSampling
from svipro.visualization import compare_strategies

# Define strategies
strategies = [
    GridSampling(spacing=100, seed=42),
    RoadNetworkSampling(spacing=100, network_type='drive', seed=42),
]

# Compare coverage
fig = compare_strategies(strategies, aoi)
fig.savefig("strategy_comparison.png")
```

### 4.2 Command Line Interface (CLI)

```bash
# Basic sampling
svipro sample grid --spacing 100 --aoi aoi.geojson --output points.geojson

# Road network sampling
svipro sample road --spacing 50 --network drive --aoi hongkong.geojson --output hk_points.geojson

# Generate protocol
svipro protocol create points.geojson --config sampling_config.yaml --output protocol.yaml

# Visualize coverage
svipro visualize points.geojson --output coverage_map.html

# Compare strategies
svipro compare --strategies grid,road --spacing 50,100 --aoi aoi.geojson
```

### 4.3 Output Files

#### Sampling Points (GeoJSON)
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [114.157, 22.284]},
      "properties": {
        "sample_id": "grid_0001_0042",
        "strategy": "grid_sampling",
        "spacing_m": 100,
        "timestamp": "2025-01-21T10:30:00Z"
      }
    }
  ]
}
```

#### Protocol File (YAML)
```yaml
sampling_protocol:
  version: "0.1.0"
  timestamp: "2025-01-21T10:30:00Z"
  authors:
    - Jiale Guo <jiale.guo@mail.polimi.it>
    - Mingfeng Tang <mingfeng.tang@mail.polimi.it>

  aoi:
    description: "Hong Kong Central District"
    bounds: [114.15, 22.27, 114.18, 22.30]
    crs: "EPSG:4326"

  strategy:
    name: "grid_sampling"
    spacing: 100
    seed: 42
    parameters:
      algorithm: "regular_grid"
      alignment: "bottom_left"

  quality_metrics:
    n_points: 127
    area_km2: 2.45
    density_pts_per_km2: 51.8

  reproducibility:
    svipro_version: "0.1.0"
    python_version: "3.11.0"
    dependencies:
      geopandas: "0.14.1"
      osmnx: "2.0.0"
```

---

## 5. Development Roadmap

### Milestone 1: MVP (Week 1-2)
- [x] Project setup and configuration
- [ ] Base sampling architecture
- [ ] Grid sampling implementation
- [ ] Basic GeoJSON export
- [ ] Simple CLI interface

### Milestone 2: Core Features (Week 3-4)
- [ ] Road network sampling (OSMnx integration)
- [ ] Metadata management system
- [ ] Quality metrics calculation
- [ ] Protocol generation

### Milestone 3: Visualization (Week 5-6)
- [ ] Interactive maps (folium)
- [ ] Coverage analysis plots
- [ ] Strategy comparison tool
- [ ] Documentation and examples

### Milestone 4: Testing & Refinement (Week 7-8)
- [ ] Unit tests for all modules
- [ ] Integration tests
- [ ] Performance optimization
- [ ] Case study validation

---

## 6. Research Contribution

### 6.1 Methodological Paper Opportunities

1. **"Standardizing Street View Imagery Sampling: A Reproducible Framework for Urban Studies"**
   - Systematic review of current sampling practices
   - Proposal of standardized protocols
   - Comparison of sampling strategies

2. **"Assessing Spatial Sampling Bias in Street View-Based Urban Research"**
   - Quantitative analysis of sampling bias
   - Impact on research outcomes
   - Recommendations for best practices

### 6.2 Software Paper

**"SVIPro: An Open-Source Python Package for Reproducible Street View Imagery Sampling Design"**
- Journal: *SoftwareX* or *Journal of Open Source Software*
- Focus: Software architecture, algorithms, and case studies

---

## 7. Compliance & Ethics

### 7.1 No Crawling Policy
- ❌ We do NOT mass-download street view images
- ❌ We do NOT bypass API rate limits
- ❌ We do NOT violate terms of service

### 7.2 What We Provide
- ✅ Sampling design protocols (coordinates only)
- ✅ Metadata documentation standards
- ✅ Quality assessment tools
- ✅ Cost optimization for legal API usage

### 7.3 Legal API Usage
Users of our package should:
1. Use official APIs (Google Maps Platform, Baidu Maps API)
2. Respect rate limits and terms of service
3. Attribute data sources appropriately
4. Follow institutional and national regulations

---

## 8. References

**Wang et al. (2025)** - Cross-platform complementarity: Assessing the data quality and availability of Google Street View and Baidu Street View. *Transactions in Urban Data, Science, and Technology*. DOI: 10.1177/27541231241311474

**Key Innovations from Reference**:
- Spider-web collection method (adapted as metadata protocol)
- Metadata-driven approach (we standardize this)
- Quality assessment framework (we extend this)

**Our Improvements**:
- ✅ Better code structure and modularity
- ✅ Reproducibility guarantees (seed-based)
- ✅ Comprehensive documentation
- ✅ Multiple sampling strategies
- ✅ No actual crawling (compliance-first)
- ✅ Quality metrics and bias detection
- ✅ User-friendly interface (Python + CLI)

---

**Status**: 📝 Planning Phase - Ready for Review

**Next Step**: User approval → Begin Milestone 1 implementation
