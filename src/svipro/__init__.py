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

Authors:
    Jiale Guo (jiale.guo@mail.polimi.it)
    Mingfeng Tang (mingfeng.tang@mail.polimi.it)

Geoinformatics Engineering graduate students at Politecnico di Milano
"""

__version__ = "0.1.0"
__author__ = "Jiale Guo, Mingfeng Tang"

from svipro.sampling import SamplingStrategy, GridSampling, RoadNetworkSampling
from svipro.metadata import MetadataManager, SamplingProtocol
from svipro.reproducibility import ProtocolRecorder
from svipro.visualization import SamplingVisualizer

__all__ = [
    "__version__",
    "__author__",
    # Sampling
    "SamplingStrategy",
    "GridSampling",
    "RoadNetworkSampling",
    # Metadata
    "MetadataManager",
    "SamplingProtocol",
    # Reproducibility
    "ProtocolRecorder",
    # Visualization
    "SamplingVisualizer",
]
