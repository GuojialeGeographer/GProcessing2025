# SVIPro API Reference

Complete API documentation for SVIPro (SVI Research Protocol & Optimization) package.

## Table of Contents

1. [Sampling Module](#sampling-module)
2. [Visualization Module](#visualization-module)
3. [CLI Module](#cli-module)
4. [Data Structures](#data-structures)
5. [Utility Functions](#utility-functions)

---

## Sampling Module

### Base Classes

#### `SamplingConfig`

Configuration dataclass for sampling strategies.

**Attributes**:
- `spacing` (float): Distance between sample points in meters. Must be positive.
- `crs` (str): Coordinate Reference System as EPSG code (e.g., "EPSG:4326").
- `seed` (int): Random seed for reproducibility. Default is 42.
- `boundary` (Optional[Polygon]): Area of interest as shapely Polygon.
- `metadata` (Dict[str, Any]): Additional metadata dictionary.

**Methods**:
- `to_dict() -> Dict[str, Any]`: Convert configuration to dictionary.
- `from_dict(data: Dict[str, Any]) -> SamplingConfig`: Create configuration from dictionary.
- `_validate() -> None`: Validate configuration parameters.

**Example**:
```python
from svipro import SamplingConfig

config = SamplingConfig(
    spacing=100.0,
    crs="EPSG:4326",
    seed=42
)

# Convert to dict
config_dict = config.to_dict()

# Create from dict
config2 = SamplingConfig.from_dict(config_dict)
```

#### `SamplingStrategy`

Abstract base class for all sampling strategies.

**Subclasses**:
- `GridSampling`: Regular grid-based sampling
- `RoadNetworkSampling`: Road network-aware sampling

**Methods**:
- `generate(boundary: Polygon) -> GeoDataFrame`: Generate sample points (abstract).
- `calculate_coverage_metrics() -> Dict[str, Any]`: Calculate coverage metrics.
- `to_geojson(filepath: str, include_metadata: bool = True) -> None`: Export to GeoJSON.
- `_validate_boundary(boundary: Polygon) -> None`: Validate boundary geometry.

**Example**:
```python
from svipro import SamplingStrategy
from shapely.geometry import box

# Don't instantiate directly - use subclasses
strategy = GridSampling(SamplingConfig(spacing=100))
points = strategy.generate(box(0, 0, 1000, 1000))
```

### Concrete Implementations

#### `GridSampling`

Regular grid sampling strategy.

**Parameters**:
- `config` (SamplingConfig): Sampling configuration.

**Attributes**:
- `strategy_name` (str): "grid_sampling"

**Methods**:
- `generate(boundary: Polygon) -> GeoDataFrame`: Generate grid sample points.
  - Returns GeoDataFrame with columns: geometry, sample_id, strategy, timestamp, grid_x, grid_y, spacing_m
- `optimize_spacing_for_target_n(boundary, target_n, min_spacing, max_spacing) -> GeoDataFrame`: Find optimal spacing.

**Example**:
```python
from svipro import GridSampling, SamplingConfig
from shapely.geometry import box

boundary = box(0, 0, 1000, 1000)
strategy = GridSampling(SamplingConfig(spacing=100))
points = strategy.generate(boundary)

# Optimize for target number of points
strategy.optimize_spacing_for_target_n(
    boundary,
    target_n=500,
    min_spacing=20,
    max_spacing=200
)
```

#### `RoadNetworkSampling`

Road network-based sampling strategy.

**Parameters**:
- `config` (SamplingConfig): Sampling configuration.
- `network_type` (str): OSM network type ('all', 'walk', 'drive', 'bike').
- `road_types` (Optional[Set[str]]): Set of OSM highway types to include.

**Attributes**:
- `strategy_name` (str): "road_network_sampling"
- `network_type` (str): OSM network type
- `road_types` (Optional[Set[str]]): Road type filter

**Methods**:
- `generate(boundary: Polygon) -> GeoDataFrame`: Generate road network sample points.
  - Returns GeoDataFrame with columns: geometry, sample_id, strategy, timestamp, edge_id, distance_along_edge, spacing_m, highway, network_type
- `calculate_road_network_metrics() -> Dict[str, Any]`: Calculate road network metrics.

**Example**:
```python
from svipro import RoadNetworkSampling, SamplingConfig
from shapely.geometry import box

boundary = box(114.15, 22.28, 114.16, 22.29)  # Hong Kong
strategy = RoadNetworkSampling(
    SamplingConfig(spacing=100),
    network_type='drive',
    road_types={'primary', 'secondary'}
)
points = strategy.generate(boundary)

# Get road network metrics
metrics = strategy.calculate_road_network_metrics()
print(f"Road length: {metrics['total_road_length_km']:.2f} km")
print(f"Avg degree: {metrics['avg_degree']:.2f}")
```

---

## Visualization Module

### Strategy Comparison

#### `compare_strategies(strategies, boundary, output_path=None, figsize=(16, 10))`

Compare multiple sampling strategies on the same boundary.

**Parameters**:
- `strategies` (Dict[str, SamplingStrategy]): Dictionary mapping names to strategies.
- `boundary` (Polygon): Area of interest.
- `output_path` (Optional[str]): Path to save figure (PNG).
- `figsize` (tuple): Figure size (width, height).

**Returns**:
- `plt.Figure`: Matplotlib figure object.

**Raises**:
- `ValueError`: If strategies empty or boundary invalid.

**Example**:
```python
from svipro import compare_strategies, GridSampling, SamplingConfig
from shapely.geometry import box

strategies = {
    'Grid 50m': GridSampling(SamplingConfig(spacing=50)),
    'Grid 100m': GridSampling(SamplingConfig(spacing=100))
}

fig = compare_strategies(strategies, box(0, 0, 1000, 1000))
```

### Statistics Visualization

#### `plot_coverage_statistics(points_gdf, output_path=None, figsize=(12, 8))`

Plot coverage statistics for sample points.

**Parameters**:
- `points_gdf` (GeoDataFrame): Sample points.
- `output_path` (Optional[str]): Path to save figure.
- `figsize` (tuple): Figure size.

**Returns**:
- `plt.Figure`: Matplotlib figure object.

**Creates**:
- Spatial distribution heatmap
- Nearest neighbor distance histogram
- Quadrant analysis
- Summary statistics table

**Example**:
```python
from svipro import plot_coverage_statistics

fig = plot_coverage_statistics(points, "statistics.png")
```

#### `plot_spatial_distribution(points_gdf, boundary=None, output_path=None, figsize=(10, 10), title='Sample Points Distribution')`

Create clean spatial distribution plot.

**Parameters**:
- `points_gdf` (GeoDataFrame): Sample points.
- `boundary` (Optional[Polygon]): Boundary polygon for context.
- `output_path` (Optional[str]): Path to save figure.
- `figsize` (tuple): Figure size.
- `title` (str): Plot title.

**Returns**:
- `plt.Figure`: Matplotlib figure object.

**Example**:
```python
from svipro import plot_spatial_distribution
from shapely.geometry import box

fig = plot_spatial_distribution(
    points,
    boundary=box(0, 0, 1000, 1000),
    title="Study Area Distribution"
)
```

---

## CLI Module

### Command Groups

#### `svipro sample`

Generate spatial sample points.

**Subcommands**:
- `grid`: Grid-based sampling
- `road-network`: Road network-based sampling

**Common Options**:
- `--spacing FLOAT`: Distance between points (meters)
- `--crs TEXT`: Coordinate Reference System
- `--seed INT`: Random seed
- `--aoi TEXT`: AOI boundary file (GeoJSON)
- `--output TEXT`: Output file path (GeoJSON)
- `--metadata`: Include metadata

**Example**:
```bash
svipro sample grid --spacing 100 --aoi boundary.geojson --output points.geojson
```

#### `svipro quality`

Calculate quality metrics for sample points.

**Subcommands**:
- `metrics`: Calculate and display coverage metrics

**Example**:
```bash
svipro quality metrics --points samples.geojson
```

#### `svipro visualize`

Visualize sample points and coverage.

**Subcommands**:
- `points-map`: Create interactive map
- `statistics`: Generate statistics plots
- `compare`: Compare sampling strategies

**Example**:
```bash
svipro visualize statistics --points samples.geojson --output stats.png
```

---

## Data Structures

### GeoDataFrame Schema

#### Grid Sampling Output

**Columns**:
- `geometry` (Point): Point geometry
- `sample_id` (str): Unique identifier (format: "grid_sampling_XXXX_YYYY")
- `strategy` (str): Strategy name ("grid_sampling")
- `timestamp` (str): Generation timestamp (ISO 8601)
- `grid_x` (int): X-coordinate index in grid
- `grid_y` (int): Y-coordinate index in grid
- `spacing_m` (float): Spacing used in meters

#### Road Network Sampling Output

**Columns**:
- `geometry` (Point): Point geometry
- `sample_id` (str): Unique identifier (format: "road_network_XXXXX")
- `strategy` (str): Strategy name ("road_network_sampling")
- `timestamp` (str): Generation timestamp (ISO 8601)
- `edge_id` (int): OSM edge ID
- `distance_along_edge` (float): Distance from edge start (meters)
- `spacing_m` (float): Spacing used in meters
- `highway` (str): OSM highway type
- `network_type` (str): Network type used

### Metrics Dictionary

#### Coverage Metrics (`calculate_coverage_metrics()`)

```python
{
    'n_points': int,              # Number of sample points
    'area_km2': float,            # Coverage area in square kilometers
    'density_pts_per_km2': float, # Sampling density
    'bounds': tuple,              # (minx, miny, maxx, maxy)
    'crs': str                    # Coordinate reference system
}
```

#### Road Network Metrics (`calculate_road_network_metrics()`)

```python
{
    'n_points': int,                       # Number of sample points
    'n_edges': int,                         # Number of road edges
    'n_nodes': int,                         # Number of intersections
    'total_road_length_km': float,          # Total road length
    'avg_degree': float,                     # Average node degree
    'road_type_distribution': dict,          # Highway type counts
    'network_type': str                      # Network type
}
```

---

## Utility Functions

### Import Helper

```python
# Import all main components
from svipro import (
    SamplingConfig,
    SamplingStrategy,
    GridSampling,
    RoadNetworkSampling,
    compare_strategies,
    plot_coverage_statistics,
    plot_spatial_distribution
)
```

### Version Information

```python
import svipro
print(svipro.__version__)  # '0.1.0'
print(svipro.__author__)    # 'Jiale Guo, Mingfeng Tang'
```

---

## Type Hints

All functions and methods include complete type hints:

```python
from typing import Dict, Any, Optional
from svipro import GridSampling, SamplingConfig
from shapely.geometry import Polygon
import geopandas as gpd

def create_samples(
    boundary: Polygon,
    spacing: float = 100.0
) -> gpd.GeoDataFrame:
    """Create sample points with type hints."""
    config = SamplingConfig(spacing=spacing)
    strategy = GridSampling(config)
    return strategy.generate(boundary)
```

---

## Exceptions

### ValueError

Raised when:
- Spacing is not positive
- Boundary is invalid or has zero area
- No sample points can be generated
- Invalid network type or road types

### TypeError

Raised when:
- Boundary is not a shapely Polygon
- Config is not SamplingConfig instance

### RuntimeError

Raised when:
- OSM network download fails
- OSM servers are inaccessible

---

## Performance Considerations

### Grid Sampling

- **Complexity**: O(n) where n is number of grid cells
- **Memory**: Proportional to number of points
- **Speed**: Fast, no external dependencies

### Road Network Sampling

- **Complexity**: O(V + E) where V is vertices, E is edges
- **Memory**: Depends on road network size
- **Speed**: Slower due to OSM data download
- **Optimization**: Use smaller boundary or filter road types

---

## See Also

- **Getting Started**: `docs/tutorials/getting_started.md`
- **Case Studies**: `docs/case_studies/hong_kong_urban_green_space.md`
- **GitHub**: https://github.com/GuojialeGeographer/GProcessing2025

---

**Version**: 0.1.0
**Last Updated**: 2025-01-22
