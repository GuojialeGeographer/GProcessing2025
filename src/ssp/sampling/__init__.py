"""
Sampling Strategy Module

This module provides scientific spatial sampling strategies for geospatial
studies and research. All strategies are designed to be reproducible and documented.

Available Strategies:
    - GridSampling: Regular grid-based sampling
    - RoadNetworkSampling: Road network-aware sampling along OpenStreetMap roads
    - RandomSampling: Stratified random sampling (planned)
    - OptimizedSampling: Coverage-optimized sampling (planned)

Example:
    >>> from ssp import GridSampling, RoadNetworkSampling, SamplingConfig
    >>> from shapely.geometry import box
    >>> # Grid sampling
    >>> strategy = GridSampling(SamplingConfig(spacing=100))
    >>> points = strategy.generate(box(0, 0, 1000, 1000))
    >>> # Road network sampling
    >>> road_strategy = RoadNetworkSampling(SamplingConfig(spacing=50))
    >>> road_points = road_strategy.generate(boundary)
"""

from ssp.sampling.base import SamplingStrategy
from ssp.sampling.grid import GridSampling
from ssp.sampling.road_network import RoadNetworkSampling

__all__ = [
    "SamplingStrategy",
    "GridSampling",
    "RoadNetworkSampling",
]
