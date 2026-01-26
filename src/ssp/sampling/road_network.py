"""
Road Network Sampling Strategy Module

Implements road network-based sampling for spatial point generation.
This strategy places sample points along road networks, which is particularly
useful for street view imagery studies and urban environment analysis.

Road network sampling provides:
- Realistic placement along actual roadways
- Better coverage of accessible areas
- OSM-based road type filtering
- Reproducible sampling with distance constraints

Features:
- OSMnx integration for road network retrieval
- Configurable road type filtering
- Distance-based sampling along edges
- NetworkX graph processing
"""

from datetime import datetime
from typing import Optional, List, Set, Tuple
import numpy as np
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, Polygon
import osmnx as ox
import warnings
from tqdm import tqdm

from ssp.sampling.base import SamplingStrategy, SamplingConfig


class RoadNetworkSampling(SamplingStrategy):
    """
    Road network sampling strategy.

    Creates sample points along road networks retrieved from OpenStreetMap.
    This is particularly useful for street view imagery sampling where access
    to roads is required for image capture.

    Points are distributed along road edges with approximately equal spacing.
    The sampling respects road network topology and can filter by road type.

    Attributes:
        strategy_name: Identifier for this sampling strategy
        config: SamplingConfig with spacing and other parameters
        network_type: Type of OSM network ('walk', 'drive', 'bike', 'all')
        road_types: Set of OSM highway types to include

    Example:
        >>> from shapely.geometry import box
        >>> boundary = box(116.3, 39.9, 116.4, 40.0)  # Beijing area
        >>> config = SamplingConfig(spacing=100, seed=42)
        >>> strategy = RoadNetworkSampling(
        ...     config,
        ...     network_type='drive',
        ...     road_types={'primary', 'secondary'}
        ... )
        >>> points = strategy.generate(boundary)
        >>> print(f"Generated {len(points)} sample points along roads")
    """

    # OSM highway types classification
    HIGHWAY_TYPES = {
        'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
        'unclassified', 'residential', 'service', 'motorway_link',
        'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link',
        'living_street', 'pedestrian', 'track', 'road', 'path',
        'cycleway', 'footway', 'steps', 'bridleway'
    }

    NETWORK_TYPES = {'all', 'walk', 'drive', 'bike'}

    def __init__(
        self,
        config: Optional[SamplingConfig] = None,
        network_type: str = 'all',
        road_types: Optional[Set[str]] = None
    ):
        """
        Initialize road network sampling strategy.

        Args:
            config: SamplingConfig instance. If None, uses defaults.
            network_type: OSM network type ('all', 'walk', 'drive', 'bike').
                         Default is 'all' for complete road network.
            road_types: Set of OSM highway types to include (e.g., {'primary', 'secondary'}).
                       If None, includes all road types in the network.

        Raises:
            TypeError: If config is not None and not a SamplingConfig.
            ValueError: If network_type is not valid.
            ValueError: If road_types contains invalid highway types.

        Example:
            >>> config = SamplingConfig(spacing=50)
            >>> strategy = RoadNetworkSampling(
            ...     config,
            ...     network_type='drive',
            ...     road_types={'primary', 'secondary', 'residential'}
            ... )
        """
        if config is None:
            config = SamplingConfig()

        super().__init__(config)
        self.strategy_name = "road_network_sampling"

        # Validate network_type
        if network_type not in self.NETWORK_TYPES:
            raise ValueError(
                f"network_type must be one of {self.NETWORK_TYPES} "
                f"(got '{network_type}')"
            )
        self.network_type = network_type

        # Validate and store road_types
        if road_types is not None:
            invalid_types = road_types - self.HIGHWAY_TYPES
            if invalid_types:
                raise ValueError(
                    f"Invalid road types: {invalid_types}. "
                    f"Valid types are: {sorted(self.HIGHWAY_TYPES)}"
                )
        self.road_types = road_types

        # Store road network graph
        self._road_graph: Optional[nx.MultiDiGraph] = None

    def generate(self, boundary: Polygon) -> gpd.GeoDataFrame:
        """
        Generate road network sample points within boundary.

        Retrieves the road network from OpenStreetMap within the boundary
        polygon and places sample points along road edges at approximately
        the specified spacing distance.

        The sampling process:
        1. Download road network from OSM using OSMnx
        2. Filter by network type and road types if specified
        3. Calculate total length of road network
        4. Determine number of points based on spacing
        5. Place points along edges with uniform spacing

        Args:
            boundary: Area of interest as shapely Polygon. Must be a valid,
                      non-empty polygon with non-zero area. For best results,
                      use projected CRS (e.g., EPSG:3857) for accurate spacing.

        Returns:
            GeoDataFrame with road network sample points containing:
                - geometry: Point geometries (shapely.Point)
                - sample_id: Unique identifier (str, format: "road_network_XXXX")
                - strategy: Strategy name ("road_network_sampling")
                - timestamp: Generation timestamp (ISO 8601 string)
                - edge_id: OSM edge ID (int)
                - distance_along_edge: Distance from edge start in meters (float)
                - spacing_m: Spacing used in meters (float)
                - highway: OSM highway type (str, e.g., "primary", "residential")
                - network_type: Network type used (str)

        Raises:
            ValueError: If boundary is invalid, empty, or has zero area.
            TypeError: If boundary is not a shapely Polygon.
            RuntimeError: If OSM network download fails or returns empty network.
            ValueError: If no road edges match the criteria within boundary.

        Note:
            - Requires internet connection for OSM data download
            - OSMnx caches downloaded networks for faster subsequent access
            - For large boundaries, download may take time
            - Actual spacing may vary slightly due to road network topology

        Example:
            >>> strategy = RoadNetworkSampling(
            ...     SamplingConfig(spacing=100),
            ...     network_type='drive'
            ... )
            >>> points = strategy.generate(boundary)
            >>> assert len(points) > 0
            >>> assert 'highway' in points.columns
            >>> assert 'edge_id' in points.columns
        """
        # Validate boundary
        self._validate_boundary(boundary)

        # Store boundary and timestamp
        self.config.boundary = boundary
        self._generation_timestamp = datetime.now()

        # Set random seed for reproducibility
        np.random.seed(self.config.seed)

        # Provide spacing guidance for geographic CRS
        import sys
        if self.config.crs == "EPSG:4326" or self.config.crs.startswith("EPSG:4"):
            # Geographic coordinate system - spacing is in degrees
            spacing_meters = self.config.spacing * 111000  # Approximate at equator
            if spacing_meters > 200:
                print(f"\n⚠️  Warning: spacing={self.config.spacing} degrees ≈ {spacing_meters:.0f}m")
                print(f"    This may generate too many points. Consider:")
                print(f"    - spacing=0.0001 for ~11m (dense)")
                print(f"    - spacing=0.0005 for ~55m (moderate)")
                print(f"    - spacing=0.0010 for ~110m (sparse)")
                sys.stdout.flush()

        # Estimate area and provide time estimate
        minx, miny, maxx, maxy = boundary.bounds
        width_deg = maxx - minx
        height_deg = maxy - miny

        # Rough time estimate based on area
        area_deg2 = width_deg * height_deg
        if area_deg2 > 0.01:  # Large area (> 10km x 10km roughly)
            print(f"\nℹ️  Downloading road network for area: {area_deg2:.4f} sq deg")
            print(f"   This may take 1-3 minutes depending on:")
            print(f"   - Network connection speed")
            print(f"   - OSM server response time")
            print(f"   - Road density in the area")
            print(f"\n   Starting download...\n")
            sys.stdout.flush()

        # Get boundary bounds for OSM query

        # Try to get place name from boundary for better caching
        # (fallback to bounding box if no place name)
        import time
        start_time = time.time()

        try:
            # Convert boundary to bounding box for OSM query
            boundary_polygon = boundary

            # Download road network from OSM
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._road_graph = ox.graph_from_polygon(
                    boundary_polygon,
                    network_type=self.network_type,
                    simplify=True,
                    retain_all=False
                )

            download_time = time.time() - start_time
            if download_time > 10:  # Only print if download took > 10 seconds
                print(f"✓ Road network downloaded in {download_time:.1f} seconds")
                sys.stdout.flush()

        except Exception as e:
            raise RuntimeError(
                f"Failed to download road network from OpenStreetMap: {e}\n"
                f"Please check:\n"
                f"  - You have an internet connection\n"
                f"  - The boundary covers a valid area with roads\n"
                f"  - OSM servers are accessible (try again later if servers are busy)\n"
                f"  - Boundary size is reasonable (try smaller area if download fails)"
            ) from e

        # Check if graph has edges
        if self._road_graph.number_of_edges() == 0:
            raise ValueError(
                f"No road network found within the boundary for "
                f"network_type='{self.network_type}'. "
                f"Try a different boundary or network_type."
            )

        # Convert to undirected graph for bidirectional sampling
        # Use osmnx.convert.to_undirected() for newer OSMnx versions
        try:
            # Try newer OSMnx API first (v2.0+)
            graph = self._road_graph.to_undirected()
        except AttributeError:
            # Fallback to older API
            try:
                import osmnx.utils_graph
                graph = osmnx.utils_graph.get_undirected(self._road_graph)
            except AttributeError:
                # Last resort: just use the graph as-is
                graph = self._road_graph

        # Filter by road types if specified
        if self.road_types is not None:
            edges_to_keep = []
            for u, v, key, data in graph.edges(keys=True, data=True):
                highway = data.get('highway', '')
                # Handle both string and list highway types
                if isinstance(highway, list):
                    if any(h in self.road_types for h in highway):
                        edges_to_keep.append((u, v, key))
                elif highway in self.road_types:
                    edges_to_keep.append((u, v, key))

            if not edges_to_keep:
                raise ValueError(
                    f"No road edges matching road_types={self.road_types} "
                    f"found within boundary."
                )

            # Create subgraph with only matching edges
            graph = graph.edge_subgraph(edges_to_keep).copy()

        # Get edges as GeoDataFrame
        edges_gdf = ox.graph_to_gdfs(graph, nodes=False)

        # Calculate total road length and number of points needed
        # Use projected CRS for accurate distance calculation
        if 'length' not in edges_gdf.columns:
            # Calculate geometric length if not provided by OSMnx
            edges_gdf['length'] = edges_gdf.geometry.length

        total_length = edges_gdf['length'].sum()
        n_points_target = max(1, int(total_length / self.config.spacing))

        # Generate sample points along edges
        points = []
        points_generated = 0

        # Progress bar for edge processing
        pbar = tqdm(
            total=len(edges_gdf),
            desc="Processing road edges",
            unit="edges",
            disable=None  # Auto-detect if in terminal
        )

        for idx, row in edges_gdf.iterrows():
            # Handle both MultiIndex (u, v, key) and simple index
            if isinstance(idx, tuple) and len(idx) >= 2:
                u, v = idx[0], idx[1]
            else:
                # Fallback: use row data if available
                u = row.get('u', None)
                v = row.get('v', None)
                if u is None or v is None:
                    continue  # Skip if we can't determine edge endpoints

            edge_geom = row.geometry
            edge_length = row['length']
            highway = row.get('highway', 'unknown')

            # Calculate number of points on this edge
            if points_generated == 0:
                # First edge gets one more point to account for remainder
                n_edge_points = max(1, int(edge_length / self.config.spacing) + 1)
            else:
                n_edge_points = max(1, int(edge_length / self.config.spacing))

            # Generate points along the edge
            for i in range(n_edge_points):
                if points_generated >= n_points_target:
                    break

                # Calculate position along edge (0.0 to 1.0)
                if n_edge_points > 1:
                    fraction = i / (n_edge_points - 1)
                else:
                    fraction = 0.5  # Midpoint for single point

                # Interpolate point along edge
                point = edge_geom.interpolate(fraction, normalized=True)

                # Ensure point is within boundary
                if not boundary.contains(point):
                    continue

                # Get edge data
                edge_data = graph.get_edge_data(u, v)
                edge_id = edge_data[0].get('osmid', idx) if edge_data else idx

                points.append({
                    'geometry': point,
                    'sample_id': f"{self.strategy_name}_{points_generated:05d}",
                    'strategy': self.strategy_name,
                    'timestamp': self._generation_timestamp.isoformat(),
                    'edge_id': edge_id,
                    'distance_along_edge': fraction * edge_length,
                    'spacing_m': self.config.spacing,
                    'highway': highway if isinstance(highway, str) else str(highway),
                    'network_type': self.network_type
                })

                points_generated += 1

            # Update progress bar
            pbar.update(1)
            pbar.set_postfix({'points': points_generated})

            if points_generated >= n_points_target:
                break

        # Close progress bar
        pbar.close()

        # Check if any points were generated
        if not points:
            raise ValueError(
                f"No sample points could be generated within boundary. "
                f"This may happen if:\n"
                f"  - Road edges are outside the boundary polygon\n"
                f"  - The boundary area is too small\n"
                f"  - Spacing is too large for the road network"
            )

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(points, crs=self.config.crs)
        self._sample_points = gdf

        # Warn if point count is unusual
        n_points = len(gdf)
        if n_points > 100000:
            print(f"\n⚠️  Warning: Generated {n_points:,} sample points (very high!)")
            print(f"    This may cause:")
            print(f"    - High memory usage")
            print(f"    - Slow visualization/processing")
            print(f"    - Consider increasing spacing value")
        elif n_points < 50:
            print(f"\n⚠️  Warning: Only {n_points} sample points generated (very low)")
            print(f"    Consider decreasing spacing value for better coverage")

        return gdf

    def calculate_road_network_metrics(self) -> dict:
        """
        Calculate road network-specific metrics.

        Provides additional metrics specific to road network sampling,
        including network statistics and road type distribution.

        Returns:
            Dictionary with road network metrics:
                - n_points: Number of sample points
                - n_edges: Number of road edges in network
                - n_nodes: Number of intersections/nodes in network
                - total_road_length_km: Total length of road network in km
                - avg_degree: Average node degree (connectivity)
                - road_type_distribution: Count of points by highway type
                - network_type: Network type used

        Example:
            >>> strategy = RoadNetworkSampling()
            >>> points = strategy.generate(boundary)
            >>> metrics = strategy.calculate_road_network_metrics()
            >>> print(f"Total road length: {metrics['total_road_length_km']:.2f} km")
        """
        if self._sample_points is None or len(self._sample_points) == 0:
            return {
                'n_points': 0,
                'n_edges': 0,
                'n_nodes': 0,
                'total_road_length_km': 0.0,
                'avg_degree': 0.0,
                'road_type_distribution': {},
                'network_type': self.network_type
            }

        # Basic metrics
        metrics = {
            'n_points': len(self._sample_points),
            'n_edges': self._road_graph.number_of_edges() if self._road_graph else 0,
            'n_nodes': self._road_graph.number_of_nodes() if self._road_graph else 0,
            'network_type': self.network_type
        }

        # Calculate total road length from graph
        if self._road_graph is not None:
            edges_gdf = ox.graph_to_gdfs(self._road_graph, nodes=False)
            if 'length' in edges_gdf.columns:
                total_length_m = edges_gdf['length'].sum()
            else:
                total_length_m = edges_gdf.geometry.length.sum()

            metrics['total_road_length_km'] = total_length_m / 1000.0

            # Calculate average node degree
            if self._road_graph.number_of_nodes() > 0:
                degrees = [d for n, d in self._road_graph.degree()]
                metrics['avg_degree'] = np.mean(degrees)
            else:
                metrics['avg_degree'] = 0.0
        else:
            metrics['total_road_length_km'] = 0.0
            metrics['avg_degree'] = 0.0

        # Road type distribution
        if 'highway' in self._sample_points.columns:
            road_type_counts = self._sample_points['highway'].value_counts().to_dict()
            metrics['road_type_distribution'] = road_type_counts
        else:
            metrics['road_type_distribution'] = {}

        return metrics
