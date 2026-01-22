# SVIPro Getting Started Guide

A comprehensive tutorial for using SVIPro (SVI Research Protocol & Optimization) - A standardized framework for reproducible Street View Imagery sampling design.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [CLI Reference](#cli-reference)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Requirements

- Python 3.10 or higher
- pip or uv package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/GuojialeGeographer/GProcessing2025.git
cd GProcessing2025

# Install in development mode
pip install -e .
```

### Install Dependencies

```bash
# Core dependencies
pip install geopandas shapely numpy pandas scipy
pip install networkx osmnx pyyaml click
pip install matplotlib seaborn folium pyproj
```

### Verify Installation

```bash
# Check version
python -c "import svipro; print(svipro.__version__)"

# Test CLI
svipro --help
```

---

## Quick Start

### Example 1: Grid Sampling (5 minutes)

Generate a regular grid of sample points:

```python
from svipro import GridSampling, SamplingConfig
from shapely.geometry import box
import geopandas as gpd

# Define study area (1km x 1km in Hong Kong)
boundary = box(114.15, 22.28, 114.16, 22.29)

# Create sampling configuration
config = SamplingConfig(
    spacing=100.0,  # 100 meters between points
    crs="EPSG:4326",
    seed=42  # For reproducibility
)

# Generate sample points
strategy = GridSampling(config)
points = strategy.generate(boundary)

# Export to GeoJSON
strategy.to_geojson("hk_grid_samples.geojson")

print(f"Generated {len(points)} sample points")
```

### Example 2: Using CLI (2 minutes)

```bash
# Generate grid sampling points
svipro sample grid \
  --spacing 100 \
  --aoi hong_kong.geojson \
  --output hk_samples.geojson

# Calculate quality metrics
svipro quality metrics --points hk_samples.geojson

# Create visualization
svipro visualize points-map \
  --points hk_samples.geojson \
  --output hk_map.html
```

---

## Basic Usage

### 1. Grid Sampling

Grid sampling provides uniform spatial coverage:

```python
from svipro import GridSampling, SamplingConfig
from shapely.geometry import box

# Define boundary
boundary = box(114.15, 22.28, 114.16, 22.29)

# Create strategy
strategy = GridSampling(
    SamplingConfig(
        spacing=100.0,  # 100m spacing
        seed=42
    )
)

# Generate points
points = strategy.generate(boundary)

# Calculate metrics
metrics = strategy.calculate_coverage_metrics()
print(f"Points: {metrics['n_points']}")
print(f"Density: {metrics['density_pts_per_km2']:.2f} pts/km²")
print(f"Area: {metrics['area_km2']:.4f} km²")
```

**When to use Grid Sampling**:
- Baseline studies
- Comparative analysis
- Uniform coverage requirements
- Simplicity and transparency

### 2. Road Network Sampling

Road network sampling places points along actual roads:

```python
from svipro import RoadNetworkSampling, SamplingConfig
from shapely.geometry import box

# Define boundary
boundary = box(114.15, 22.28, 114.16, 22.29)

# Create strategy for driveable roads only
strategy = RoadNetworkSampling(
    SamplingConfig(spacing=100.0, seed=42),
    network_type='drive',  # Only drivable roads
    road_types={'primary', 'secondary', 'residential'}
)

# Generate points (requires internet for OSM data)
points = strategy.generate(boundary)

# Calculate road network metrics
metrics = strategy.calculate_road_network_metrics()
print(f"Road length: {metrics['total_road_length_km']:.2f} km")
print(f"Edges: {metrics['n_edges']}, Nodes: {metrics['n_nodes']}")
print(f"Avg degree: {metrics['avg_degree']:.2f}")
```

**When to use Road Network Sampling**:
- Street view imagery collection
- Urban environment studies
- Accessibility-based sampling
- Real-world placement constraints

### 3. Export and Visualization

```python
# Export with metadata
strategy.to_geojson(
    "output.geojson",
    include_metadata=True
)

# Create visualizations
from svipro import plot_coverage_statistics, plot_spatial_distribution

# Statistics plots
fig = plot_coverage_statistics(
    points,
    output_path="statistics.png"
)

# Spatial distribution
fig = plot_spatial_distribution(
    points,
    boundary=boundary,
    output_path="distribution.png"
)
```

---

## Advanced Features

### 1. Strategy Comparison

Compare multiple sampling strategies:

```python
from svipro import compare_strategies, GridSampling, SamplingConfig

boundary = box(114.15, 22.28, 114.16, 22.29)

strategies = {
    'Grid 50m': GridSampling(SamplingConfig(spacing=50)),
    'Grid 100m': GridSampling(SamplingConfig(spacing=100)),
    'Grid 200m': GridSampling(SamplingConfig(spacing=200))
}

fig = compare_strategies(
    strategies,
    boundary,
    output_path="comparison.png"
)
```

### 2. Custom Configuration

```python
from svipro import SamplingConfig

# Custom configuration
config = SamplingConfig(
    spacing=75.5,  # Non-standard spacing
    crs="EPSG:3857",  # Projected CRS for accurate meter distances
    seed=123,  # Custom seed
    metadata={
        'project': 'Urban Green Space Study',
        'researcher': 'J. Doe',
        'date': '2025-01-22'
    }
)
```

### 3. Road Type Filtering

```python
from svipro import RoadNetworkSampling, SamplingConfig

# Filter by specific road types
strategy = RoadNetworkSampling(
    SamplingConfig(spacing=100),
    network_type='drive',
    road_types={
        'primary',      # Major roads
        'secondary'     # Secondary roads
        # Exclude: residential, service, etc.
    }
)
```

---

## CLI Reference

### Sample Commands

```bash
# Grid sampling
svipro sample grid [OPTIONS]

# Road network sampling
svipro sample road-network [OPTIONS]
```

**Common Options**:
- `--spacing FLOAT`: Distance between points (meters)
- `--crs TEXT`: Coordinate Reference System (default: EPSG:4326)
- `--seed INT`: Random seed for reproducibility (default: 42)
- `--aoi TEXT`: AOI boundary file (GeoJSON, required)
- `--output TEXT`: Output file path (GeoJSON, required)
- `--metadata`: Include metadata in output

### Quality Commands

```bash
# Calculate metrics
svipro quality metrics --points samples.geojson

# Generate protocol
svipro protocol create --points samples.geojson --output protocol.yaml
```

### Visualization Commands

```bash
# Interactive map
svipro visualize points-map --points samples.geojson --output map.html

# Statistics plots
svipro visualize statistics --points samples.geojson --output stats.png

# Strategy comparison
svipro visualize compare --aoi boundary.geojson --output comparison.png
```

---

## Best Practices

### 1. Coordinate Reference System (CRS)

**For accurate meter-based spacing**:
```python
# Use projected CRS (EPSG:3857 - Web Mercator)
config = SamplingConfig(spacing=100, crs="EPSG:3857")
```

**For geographic coordinates**:
```python
# Use geographic CRS (EPSG:4326 - WGS84)
config = SamplingConfig(spacing=100, crs="EPSG:4326")
```

### 2. Reproducibility

**Always set a seed**:
```python
config = SamplingConfig(spacing=100, seed=42)

# Same config = same results (except timestamps)
strategy1 = GridSampling(config)
points1 = strategy1.generate(boundary)

strategy2 = GridSampling(config)
points2 = strategy2.generate(boundary)
```

### 3. Boundary Preparation

**Ensure valid boundary**:
```python
from shapely.geometry import box, Polygon
import geopandas as gpd

# Option 1: Use box() for rectangular areas
boundary = box(minx, miny, maxx, maxy)

# Option 2: Load from GeoJSON
gdf = gpd.read_file("boundary.geojson")
boundary = gdf.geometry.iloc[0]

# Validate
if not boundary.is_valid:
    boundary = boundary.convex_hull

if boundary.area == 0:
    raise ValueError("Boundary has zero area")
```

### 4. Performance Optimization

**For large areas**:
```python
# Use larger spacing to reduce point count
config = SamplingConfig(spacing=200)  # Instead of 100

# Filter road types to reduce network size
strategy = RoadNetworkSampling(
    config,
    network_type='drive',  # Instead of 'all'
    road_types={'primary', 'secondary'}
)
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'svipro'"

**Solution**:
```bash
# Reinstall in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/GProcessing2025/src"
```

### Issue: "Failed to download road network from OpenStreetMap"

**Solutions**:
1. Check internet connection
2. Try smaller boundary
3. Use different network type:
   ```python
   strategy = RoadNetworkSampling(config, network_type='drive')
   ```
4. Check if OSM servers are accessible: https://www.openstreetmap.org

### Issue: "No sample points generated"

**Possible causes**:
1. **Spacing too large**: Reduce spacing value
2. **Boundary too small**: Increase boundary size
3. **No road network**: Use `network_type='all'` or don't filter road types
4. **CRS mismatch**: Ensure boundary and sampling use same CRS

### Issue: "ImportError: cannot import name 'osmnx'"

**Solution**:
```bash
pip install osmnx>=2.0.0
```

### Issue: CLI command not found

**Solution**:
```bash
# Reinstall package
pip install -e .

# Check installation
which svipro

# Or use Python module syntax
python -m svipro.cli --help
```

---

## Next Steps

1. **Advanced Tutorials**: See `advanced_usage.md`
2. **Case Studies**: See `case_studies/`
3. **API Reference**: See `api_reference.md`
4. **Examples**: Check `examples/` directory

## Getting Help

- **GitHub Issues**: https://github.com/GuojialeGeographer/GProcessing2025/issues
- **Email**: jiale.guo@mail.polimi.it, mingfeng.tang@mail.polimi.it
- **Documentation**: See full documentation in `docs/`

---

**Authors**: Jiale Guo, Mingfeng Tang (Politecnico di Milano)
**Version**: 0.1.0
**Last Updated**: 2025-01-22
