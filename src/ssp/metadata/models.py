"""
Metadata Models Module

Defines data models for sampling metadata to ensure complete traceability
and reproducibility of SVI sampling protocols.

This module provides structured metadata classes that capture all aspects
of the sampling process including configuration, execution, and results.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import sys
import platform


class SamplingStrategyType(Enum):
    """Enumeration of supported sampling strategy types."""
    GRID = "grid_sampling"
    ROAD_NETWORK = "road_network_sampling"
    OPTIMIZED_COVERAGE = "optimized_coverage"
    STRATIFIED_RANDOM = "stratified_random"


@dataclass
class BoundaryMetadata:
    """
    Metadata for the area of interest (AOI) boundary.

    Attributes:
        geometry_wkt: Boundary geometry in Well-Known Text format.
        crs: Coordinate Reference System (EPSG code).
        area_km2: Boundary area in square kilometers.
        bounds: Bounding box [minx, miny, maxx, maxy].
        source: Source of boundary data (e.g., "user_provided", "osm").
        description: Human-readable description of the boundary.
    """
    geometry_wkt: str
    crs: str
    area_km2: float
    bounds: tuple
    source: str = "user_provided"
    description: Optional[str] = None


@dataclass
class SamplingParametersMetadata:
    """
    Metadata for sampling parameters.

    Attributes:
        spacing: Distance between sample points in meters.
        seed: Random seed for reproducibility.
        crs: Coordinate Reference System.
        strategy_type: Type of sampling strategy used.
        additional_params: Dictionary of strategy-specific parameters.
    """
    spacing: float
    seed: int
    crs: str
    strategy_type: str
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetadata:
    """
    Metadata for sampling execution environment.

    Attributes:
        timestamp: ISO 8601 timestamp of execution.
        python_version: Python version used.
        ssp_version: SpatialSamplingPro package version.
        os_info: Operating system information.
        hostname: Machine hostname (if available).
        user: Username (if available).
        runtime_seconds: Execution time in seconds.
    """
    timestamp: str
    python_version: str
    ssp_version: str
    os_info: str
    hostname: Optional[str] = None
    user: Optional[str] = None
    runtime_seconds: Optional[float] = None


@dataclass
class DataSourceMetadata:
    """
    Metadata for external data sources used.

    Attributes:
        source_type: Type of data source (e.g., "osm", "user_provided").
        source_url: URL or identifier of the data source.
        access_timestamp: Timestamp when data was accessed.
        version: Version or date of the data source.
        quality_notes: Notes about data quality or limitations.
    """
    source_type: str
    source_url: Optional[str] = None
    access_timestamp: Optional[str] = None
    version: Optional[str] = None
    quality_notes: Optional[str] = None


@dataclass
class ResultsMetadata:
    """
    Metadata for sampling results.

    Attributes:
        n_points: Total number of sample points generated.
        density_pts_per_km2: Sampling density.
        coverage_metrics: Dictionary of coverage metrics.
        strategy_metrics: Dictionary of strategy-specific metrics.
    """
    n_points: int
    density_pts_per_km2: float
    coverage_metrics: Dict[str, Any] = field(default_factory=dict)
    strategy_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SamplingMetadata:
    """
    Complete metadata for a sampling protocol.

    This is the main metadata container that aggregates all other
    metadata types into a single, comprehensive record.

    Attributes:
        protocol_id: Unique identifier for this sampling protocol.
        protocol_name: Human-readable name for the protocol.
        description: Detailed description of the sampling protocol.
        version: Version of the protocol.
        created_at: Creation timestamp.
        boundary: Boundary metadata.
        parameters: Sampling parameters metadata.
        execution: Execution environment metadata.
        data_sources: List of external data sources used.
        results: Results metadata.
        custom_fields: Additional custom metadata fields.
        tags: List of tags for categorization.
        author: Protocol author/researcher.
        institution: Institution or organization.
        contact: Contact email.

    Example:
        >>> metadata = SamplingMetadata(
        ...     protocol_id="hk_urban_green_001",
        ...     protocol_name="Hong Kong Urban Green Space Assessment",
        ...     description="Sampling protocol for urban green space study",
        ...     boundary=boundary_meta,
        ...     parameters=params_meta,
        ...     execution=exec_meta
        ... )
    """
    protocol_id: str
    protocol_name: str
    description: str
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    boundary: Optional[BoundaryMetadata] = None
    parameters: Optional[SamplingParametersMetadata] = None
    execution: Optional[ExecutionMetadata] = None
    data_sources: List[DataSourceMetadata] = field(default_factory=list)
    results: Optional[ResultsMetadata] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    institution: Optional[str] = None
    contact: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metadata to dictionary for serialization.

        Returns:
            Dictionary representation of all metadata fields.
        """
        data = asdict(self)

        # Convert dataclass objects to dicts
        if self.boundary:
            data['boundary'] = asdict(self.boundary)
        if self.parameters:
            data['parameters'] = asdict(self.parameters)
        if self.execution:
            data['execution'] = asdict(self.execution)
        if self.results:
            data['results'] = asdict(self.results)

        # Convert data sources
        data['data_sources'] = [asdict(ds) for ds in self.data_sources]

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SamplingMetadata':
        """
        Create metadata from dictionary.

        Args:
            data: Dictionary containing metadata fields.

        Returns:
            SamplingMetadata instance.

        Raises:
            ValueError: If required fields are missing.
        """
        required_fields = ['protocol_id', 'protocol_name', 'description']
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Create data objects from nested dicts
        kwargs = {}

        if 'boundary' in data and data['boundary']:
            kwargs['boundary'] = BoundaryMetadata(**data['boundary'])

        if 'parameters' in data and data['parameters']:
            kwargs['parameters'] = SamplingParametersMetadata(**data['parameters'])

        if 'execution' in data and data['execution']:
            kwargs['execution'] = ExecutionMetadata(**data['execution'])

        if 'results' in data and data['results']:
            kwargs['results'] = ResultsMetadata(**data['results'])

        if 'data_sources' in data and data['data_sources']:
            kwargs['data_sources'] = [
                DataSourceMetadata(**ds) for ds in data['data_sources']
            ]

        # Copy other fields
        for key in ['protocol_id', 'protocol_name', 'description', 'version',
                    'created_at', 'custom_fields', 'tags', 'author',
                    'institution', 'contact']:
            if key in data:
                kwargs[key] = data[key]

        return cls(**kwargs)

    @classmethod
    def create_from_strategy(
        cls,
        strategy: Any,
        boundary: Any,
        protocol_name: str,
        description: str,
        author: Optional[str] = None,
        institution: Optional[str] = None,
        contact: Optional[str] = None
    ) -> 'SamplingMetadata':
        """
        Create metadata from a sampling strategy instance.

        This is a convenience method to automatically create metadata
        from an existing sampling strategy execution.

        Args:
            strategy: SamplingStrategy instance (GridSampling, RoadNetworkSampling, etc.)
            boundary: Shapely Polygon boundary used for sampling
            protocol_name: Name for the protocol
            description: Description of the protocol
            author: Optional author name
            institution: Optional institution name
            contact: Optional contact email

        Returns:
            SamplingMetadata instance populated with strategy information.
        """
        from shapely.geometry import box
        import ssp

        # Get strategy info
        try:
            import ssp
            ssp_version = ssp.__version__
        except (ImportError, AttributeError):
            ssp_version = "0.1.0"

        # Create boundary metadata
        boundary_meta = BoundaryMetadata(
            geometry_wkt=boundary.wkt,
            crs=strategy.config.crs,
            area_km2=round(boundary.area / 1e6, 4),
            bounds=tuple(boundary.bounds),
            source="user_provided",
            description=description
        )

        # Create parameters metadata
        additional_params = {}
        if hasattr(strategy, 'network_type'):
            additional_params['network_type'] = strategy.network_type
        if hasattr(strategy, 'road_types') and strategy.road_types:
            additional_params['road_types'] = list(strategy.road_types)

        params_meta = SamplingParametersMetadata(
            spacing=strategy.config.spacing,
            seed=strategy.config.seed,
            crs=strategy.config.crs,
            strategy_type=strategy.strategy_name,
            additional_params=additional_params
        )

        # Create execution metadata
        timestamp = strategy._generation_timestamp
        if timestamp:
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = datetime.now().isoformat()

        exec_meta = ExecutionMetadata(
            timestamp=timestamp_str,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            ssp_version=ssp_version,
            os_info=f"{platform.system()} {platform.release()}",
            hostname=platform.node(),
            runtime_seconds=None  # Would need to be measured externally
        )

        # Create data source metadata if road network
        data_sources = []
        if hasattr(strategy, 'network_type'):
            ds_meta = DataSourceMetadata(
                source_type="osm",
                source_url="https://www.openstreetmap.org/",
                access_timestamp=timestamp_str,
                version=None,  # OSM doesn't version in this way
                quality_notes="Quality depends on OSM data completeness"
            )
            data_sources.append(ds_meta)

        # Create results metadata if points have been generated
        results_meta = None
        if strategy._sample_points is not None:
            try:
                coverage = strategy.calculate_coverage_metrics()
                strategy_metrics = {}

                # Add strategy-specific metrics
                if hasattr(strategy, 'calculate_road_network_metrics'):
                    strategy_metrics = strategy.calculate_road_network_metrics()

                results_meta = ResultsMetadata(
                    n_points=len(strategy._sample_points),
                    density_pts_per_km2=coverage.get('density_pts_per_km2', 0),
                    coverage_metrics=coverage,
                    strategy_metrics=strategy_metrics
                )
            except Exception:
                # If metrics calculation fails, create minimal results
                results_meta = ResultsMetadata(
                    n_points=len(strategy._sample_points),
                    density_pts_per_km2=0,
                    coverage_metrics={},
                    strategy_metrics={}
                )

        # Generate protocol ID from name and timestamp
        protocol_id = f"{protocol_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return cls(
            protocol_id=protocol_id,
            protocol_name=protocol_name,
            description=description,
            version="1.0.0",
            created_at=timestamp_str,
            boundary=boundary_meta,
            parameters=params_meta,
            execution=exec_meta,
            data_sources=data_sources,
            results=results_meta,
            author=author,
            institution=institution,
            contact=contact
        )

    def __repr__(self) -> str:
        """Return string representation of metadata."""
        return (
            f"SamplingMetadata(id='{self.protocol_id}', "
            f"name='{self.protocol_name}', version='{self.version}')"
        )
