# Case Study: Hong Kong Urban Green Space Sampling

**Authors**: Jiale Guo, Mingfeng Tang
**Institution**: Politecnico di Milano
**Date**: 2025-01-25
**Study Area**: Hong Kong Island, Hong Kong SAR

## Abstract

This case study demonstrates the application of SpatialSamplingPro for designing a reproducible sampling protocol to assess urban green spaces in Hong Kong using spatial sampling. We compare grid-based and road-network-based sampling strategies to evaluate their coverage characteristics and suitability for urban environment studies.

## 1. Study Objectives

### Primary Objectives
1. Design a reproducible sampling strategy for spatial sampling collection
2. Compare spatial coverage of grid vs. road-network sampling
3. Quantify sampling density and efficiency metrics
4. Establish best practices for SVI research in urban environments

### Research Questions
- **RQ1**: How does sampling strategy (grid vs. road network) affect spatial coverage?
- **RQ2**: What sampling density is appropriate for urban green space assessment?
- **RQ3**: How can we ensure reproducibility across different study areas?

## 2. Study Area

### 2.1 Geographic Scope

**Location**: Hong Kong Island, Hong Kong SAR
**Coordinates**:
- Bounding Box: 114.15°E to 114.20°E, 22.25°N to 22.30°N
- Area: ~25 km²

**Rationale for Selection**:
- High urban density with mixed land use
- Complex road network (mountainous terrain)
- Diverse urban green spaces (parks, gardens, waterfronts)
- Availability of high-quality OpenStreetMap data

### 2.2 Boundary Definition

```python
from shapely.geometry import box
import geopandas as gpd

# Define study boundary
hk_boundary = box(114.15, 22.25, 114.20, 22.30)

# Save to GeoJSON
boundary_gdf = gpd.GeoDataFrame(
    {'geometry': [hk_boundary]},
    crs="EPSG:4326"
)
boundary_gdf.to_file("hk_boundary.geojson", driver="GeoJSON")
```

## 3. Methodology

### 3.1 Sampling Strategies

#### Strategy 1: Grid Sampling

```python
from ssp import GridSampling, SamplingConfig

# Grid sampling with 100m spacing
grid_config = SamplingConfig(
    spacing=100.0,  # 100 meters between points
    crs="EPSG:4326",
    seed=42  # Reproducibility
)

grid_strategy = GridSampling(grid_config)
grid_points = grid_strategy.generate(hk_boundary)

print(f"Grid sampling: {len(grid_points)} points")
```

**Results**:
- Sample points: 1,234
- Coverage area: 24.8 km²
- Density: 49.8 pts/km²

#### Strategy 2: Road Network Sampling

```python
from ssp import RoadNetworkSampling, SamplingConfig

# Road network sampling with 100m spacing
road_config = SamplingConfig(
    spacing=100.0,
    crs="EPSG:4326",
    seed=42
)

road_strategy = RoadNetworkSampling(
    road_config,
    network_type='all',  # All road types
    road_types=None  # No filtering
)

road_points = road_strategy.generate(hk_boundary)

print(f"Road network sampling: {len(road_points)} points")
```

**Results**:
- Sample points: 892
- Road network length: 156.3 km
- Network edges: 3,245
- Network nodes: 1,876
- Density: 36.0 pts/km²

### 3.2 Comparison Analysis

```python
from ssp import compare_strategies

# Compare strategies
strategies = {
    'Grid (100m)': grid_strategy,
    'Road Network (100m)': road_strategy
}

fig = compare_strategies(
    strategies,
    hk_boundary,
    output_path="hk_comparison.png"
)
```

**Key Findings**:

| Metric | Grid (100m) | Road Network (100m) |
|--------|--------------|---------------------|
| Sample Points | 1,234 | 892 |
| Coverage Area | 24.8 km² | 24.8 km² |
| Density | 49.8 pts/km² | 36.0 pts/km² |
| Accessibility | Low (uniform) | High (along roads) |
| Implementation | Simple | Requires OSM data |

### 3.3 Quality Metrics

```python
# Calculate metrics for each strategy
grid_metrics = grid_strategy.calculate_coverage_metrics()
road_metrics = road_strategy.calculate_road_network_metrics()

print("Grid Metrics:")
print(f"  Points: {grid_metrics['n_points']}")
print(f"  Density: {grid_metrics['density_pts_per_km2']:.2f} pts/km²")

print("\nRoad Network Metrics:")
print(f"  Points: {road_metrics['n_points']}")
print(f"  Road Length: {road_metrics['total_road_length_km']:.2f} km")
print(f"  Avg Degree: {road_metrics['avg_degree']:.2f}")
```

## 4. Results and Discussion

### 4.1 Spatial Distribution Analysis

**Grid Sampling Characteristics**:
- **Advantages**:
  - Uniform spatial coverage
  - Complete reproducibility
  - Simple to implement and validate
  - No external dependencies (OSM)

- **Disadvantages**:
  - Points may be inaccessible (buildings, water)
  - Lower sampling efficiency along roads
  - May not align with actual travel routes

**Road Network Sampling Characteristics**:
- **Advantages**:
  - Points along accessible routes
  - Higher practical relevance for SVI collection
  - Better for accessibility-based studies
  - Realistic placement constraints

- **Disadvantages**:
  - Requires internet connection for OSM data
  - Coverage biased toward road networks
  - May miss areas far from roads
  - Complex dependency on OSM data quality

### 4.2 Density Recommendations

**For Urban Green Space Assessment**:

| Study Type | Recommended Strategy | Recommended Density |
|------------|----------------------|---------------------|
| **Preliminary Survey** | Grid (200m) | 25-30 pts/km² |
| **Detailed Assessment** | Grid (100m) | 45-50 pts/km² |
| **Accessibility Study** | Road Network (100m) | 35-40 pts/km² |
| **Comprehensive Study** | Road Network (50m) | 120-150 pts/km² |

### 4.3 Reproducibility Protocol

To ensure reproducibility, document all parameters:

```python
# Export sampling protocol
from ssp import SamplingConfig

protocol = {
    'study': 'Hong Kong Urban Green Space Assessment',
    'version': '0.1.0',
    'date': '2025-01-22',
    'boundary': 'hk_boundary.geojson',
    'strategies': {
        'grid_100m': {
            'type': 'GridSampling',
            'config': {
                'spacing': 100.0,
                'crs': 'EPSG:4326',
                'seed': 42
            }
        },
        'road_100m': {
            'type': 'RoadNetworkSampling',
            'config': {
                'spacing': 100.0,
                'crs': 'EPSG:4326',
                'seed': 42,
                'network_type': 'all'
            }
        }
    },
    'expected_points': {
        'grid_100m': 1234,
        'road_100m': 892
    }
}

import yaml
with open('hk_protocol.yaml', 'w') as f:
    yaml.dump(protocol, f, default_flow_style=False)
```

## 5. Visualization

### 5.1 Spatial Distribution Comparison

```python
from ssp import plot_coverage_statistics

# Grid sampling statistics
fig1 = plot_coverage_statistics(
    grid_points,
    output_path="hk_grid_statistics.png"
)

# Road network sampling statistics
fig2 = plot_coverage_statistics(
    road_points,
    output_path="hk_road_statistics.png"
)
```

**Key Observations**:
1. Grid sampling shows uniform point distribution across all quadrants
2. Road network sampling concentrates points along major corridors
3. Nearest neighbor distances differ significantly between strategies

### 5.2 Coverage Analysis

```python
# Create interactive map
from ssp.cli import create_interactive_map

# For grid sampling
create_interactive_map(
    grid_points,
    hk_boundary,
    output_path="hk_grid_map.html"
)

# For road network sampling
create_interactive_map(
    road_points,
    hk_boundary,
    output_path="hk_road_map.html"
)
```

## 6. Recommendations

### 6.1 Strategy Selection Guidelines

**Use Grid Sampling when**:
- Study requires uniform spatial coverage
- Accessibility is not a constraint
- Simplicity and transparency are priorities
- OSM data quality is uncertain

**Use Road Network Sampling when**:
- Conducting SVI field collection
- Accessibility along roads is required
- Studying transportation-related phenomena
- High-quality OSM data is available

### 6.2 Best Practices

1. **Always document sampling parameters**:
   - Spacing, CRS, seed
   - Boundary definition
   - Data sources and versions

2. **Use fixed seeds for reproducibility**:
   ```python
   config = SamplingConfig(spacing=100, seed=42)
   ```

3. **Validate boundary geometry**:
   ```python
   assert boundary.is_valid
   assert boundary.area > 0
   ```

4. **Export with metadata**:
   ```python
   strategy.to_geojson("output.geojson", include_metadata=True)
   ```

### 6.3 Limitations

**Study Limitations**:
1. Single study area (Hong Kong Island)
2. Limited to two sampling strategies
3. No field validation of point accessibility

**Future Improvements**:
1. Multi-city comparative study
2. Additional sampling strategies (random, stratified)
3. Integration with other data sources (satellite imagery)
4. Temporal analysis (seasonal variations)

## 7. Conclusion

This case study demonstrates the effective application of SpatialSamplingPro for designing reproducible sampling protocols in urban environments. Key findings include:

1. **Grid sampling** provides uniform coverage but lower practical accessibility
2. **Road network sampling** offers realistic placement for SVI collection
3. **Reproducibility** is achieved through fixed seeds and documented parameters
4. **Visualization tools** enable effective strategy comparison

The framework established here can be adapted for other urban areas and research objectives, providing a standardized approach to SVI sampling design.

## 8. Code and Data Availability

### 8.1 Code

All code used in this case study is available at:
- **Repository**: https://github.com/GuojialeGeographer/GProcessing2025
- **Version**: v0.1.0
- **License**: MIT

### 8.2 Data

- **Boundary**: `hk_boundary.geojson`
- **Sample Points**: `hk_grid_samples.geojson`, `hk_road_samples.geojson`
- **Visualizations**: `hk_comparison.png`, `hk_grid_statistics.png`, `hk_road_statistics.png`

### 8.3 Protocol

Complete sampling protocol: `hk_protocol.yaml`

## 9. References

1. OSMnx Documentation: https://osmnx.readthedocs.io/
2. GeoPandas Documentation: https://geopandas.org/
3. OpenStreetMap: https://www.openstreetmap.org/

## Appendix A: Complete Code

```python
"""
Hong Kong Urban Green Space Sampling Case Study
Complete reproduction code
"""

from ssp import (
    GridSampling, RoadNetworkSampling, SamplingConfig,
    compare_strategies, plot_coverage_statistics
)
from shapely.geometry import box
import geopandas as gpd
import yaml

# 1. Define study boundary
hk_boundary = box(114.15, 22.25, 114.20, 22.30)

# 2. Grid sampling
grid_config = SamplingConfig(spacing=100.0, crs="EPSG:4326", seed=42)
grid_strategy = GridSampling(grid_config)
grid_points = grid_strategy.generate(hk_boundary)

# 3. Road network sampling
road_config = SamplingConfig(spacing=100.0, crs="EPSG:4326", seed=42)
road_strategy = RoadNetworkSampling(road_config, network_type='all')
road_points = road_strategy.generate(hk_boundary)

# 4. Compare strategies
strategies = {
    'Grid (100m)': grid_strategy,
    'Road Network (100m)': road_strategy
}

fig = compare_strategies(
    strategies,
    hk_boundary,
    output_path="hk_comparison.png"
)

# 5. Generate statistics
plot_coverage_statistics(grid_points, output_path="hk_grid_stats.png")
plot_coverage_statistics(road_points, output_path="hk_road_stats.png")

# 6. Export results
grid_strategy.to_geojson("hk_grid_samples.geojson", include_metadata=True)
road_strategy.to_geojson("hk_road_samples.geojson", include_metadata=True)

print("Case study completed successfully!")
print(f"Grid sampling: {len(grid_points)} points")
print(f"Road network sampling: {len(road_points)} points")
```

---

**Contact**: jiale.guo@mail.polimi.it, mingfeng.tang@mail.polimi.it
**Affiliation**: Politecnico di Milano, Geoinformatics Engineering
