"""
SVIPro: SVI Research Protocol & Optimization

A standardized framework for reproducible Street View Imagery sampling design.
This package provides scientific sampling strategies, metadata management, and
reproducibility tools for urban studies using street view data.

Core Modules:
    - sampling: Scientific spatial sampling strategies
    - metadata: Standardized metadata generation and management
    - reproducibility: Framework for reproducible research protocols
    - visualization: Tools for sampling evaluation and visualization
    - cli: Command-line interface

Authors:
    Jiale Guo (jiale.guo@mail.polimi.it)
    Mingfeng Tang (mingfeng.tang@mail.polimi.it)

Geoinformatics Engineering graduate students at Politecnico di Milano
"""

__version__ = "0.1.0"
__author__ = "Jiale Guo, Mingfeng Tang"

from svipro.sampling.base import SamplingConfig
from svipro.sampling import SamplingStrategy, GridSampling, RoadNetworkSampling
from svipro.visualization import compare_strategies, plot_coverage_statistics, plot_spatial_distribution

__all__ = [
    "__version__",
    "__author__",
    # Sampling
    "SamplingConfig",
    "SamplingStrategy",
    "GridSampling",
    "RoadNetworkSampling",
    # Visualization
    "compare_strategies",
    "plot_coverage_statistics",
    "plot_spatial_distribution",
]
