"""
Sampling Strategy Comparison and Visualization Module

Provides tools for comparing different sampling strategies and visualizing
coverage statistics, spatial distribution, and quality metrics.
"""

from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point
import warnings

from svipro.sampling.base import SamplingStrategy

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10


def compare_strategies(
    strategies: Dict[str, SamplingStrategy],
    boundary: Polygon,
    output_path: Optional[str] = None,
    figsize: tuple = (16, 10)
) -> plt.Figure:
    """
    Compare multiple sampling strategies on the same boundary.

    Creates a multi-panel figure showing:
    1. Spatial distribution comparison
    2. Coverage metrics comparison
    3. Point density analysis

    Args:
        strategies: Dictionary mapping strategy names to SamplingStrategy instances.
                    Keys will be used as labels in the plot.
        boundary: Area of interest as shapely Polygon.
        output_path: Optional path to save the figure (PNG format).
        figsize: Figure size (width, height) in inches.

    Returns:
        matplotlib Figure object for further customization if needed.

    Raises:
        ValueError: If strategies dictionary is empty or boundary is invalid.
        TypeError: If boundary is not a shapely Polygon.

    Example:
        >>> from shapely.geometry import box
        >>> from svipro import GridSampling, RoadNetworkSampling, SamplingConfig
        >>>
        >>> boundary = box(0, 0, 1000, 1000)
        >>> strategies = {
        ...     'Grid (100m)': GridSampling(SamplingConfig(spacing=100)),
        ...     'Grid (200m)': GridSampling(SamplingConfig(spacing=200)),
        ...     'Road Network': RoadNetworkSampling(SamplingConfig(spacing=100))
        ... }
        >>>
        >>> fig = compare_strategies(strategies, boundary, 'comparison.png')
        >>> plt.show()
    """
    if not strategies:
        raise ValueError("strategies dictionary cannot be empty")

    if not isinstance(boundary, Polygon):
        raise TypeError(f"boundary must be shapely Polygon, got {type(boundary)}")

    # Generate samples for each strategy
    results = {}
    for name, strategy in strategies.items():
        try:
            points = strategy.generate(boundary)
            metrics = strategy.calculate_coverage_metrics()
            results[name] = {
                'points': points,
                'metrics': metrics
            }
        except Exception as e:
            warnings.warn(f"Failed to generate samples for {name}: {e}")
            continue

    if not results:
        raise ValueError("No strategies generated valid samples")

    # Create figure with subplots
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # 1. Spatial distribution comparison (top row, spanning both columns)
    ax_map = fig.add_subplot(gs[0, :])
    _plot_spatial_comparison(ax_map, results, boundary)

    # 2. Metrics comparison bar chart (bottom left)
    ax_metrics = fig.add_subplot(gs[1, 0])
    _plot_metrics_comparison(ax_metrics, results)

    # 3. Density distribution (bottom right)
    ax_density = fig.add_subplot(gs[1, 1])
    _plot_density_distribution(ax_density, results)

    # Add overall title
    fig.suptitle(
        'Sampling Strategy Comparison',
        fontsize=16,
        fontweight='bold',
        y=0.98
    )

    # Save if path provided
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close(fig)
    else:
        plt.tight_layout()

    return fig


def _plot_spatial_comparison(
    ax: plt.Axes,
    results: Dict[str, Dict[str, Any]],
    boundary: Polygon
) -> None:
    """
    Plot spatial distribution of sample points for all strategies.

    Args:
        ax: Matplotlib axes object.
        results: Dictionary containing points and metrics for each strategy.
        boundary: Boundary polygon for context.
    """
    # Plot boundary
    if boundary.geom_type == 'Polygon':
        x, y = boundary.exterior.xy
        ax.plot(x, y, 'k-', linewidth=2, label='Boundary', alpha=0.5)

    # Colors for different strategies
    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))

    # Plot points for each strategy
    for idx, (name, data) in enumerate(results.items()):
        points = data['points']
        color = colors[idx]

        # Extract coordinates
        coords = np.array([[pt.x, pt.y] for pt in points.geometry])

        # Plot points
        ax.scatter(
            coords[:, 0],
            coords[:, 1],
            c=[color],
            label=f"{name} (n={len(points)})",
            alpha=0.6,
            s=20,
            edgecolors='black',
            linewidths=0.5
        )

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Spatial Distribution Comparison')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal', adjustable='box')


def _plot_metrics_comparison(
    ax: plt.Axes,
    results: Dict[str, Dict[str, Any]]
) -> None:
    """
    Plot comparison of coverage metrics across strategies.

    Args:
        ax: Matplotlib axes object.
        results: Dictionary containing metrics for each strategy.
    """
    # Extract metrics
    names = list(results.keys())
    n_points = [results[name]['metrics']['n_points'] for name in names]
    densities = [results[name]['metrics']['density_pts_per_km2'] for name in names]
    areas = [results[name]['metrics']['area_km2'] for name in names]

    # Create bar positions
    x = np.arange(len(names))
    width = 0.25

    # Plot bars
    ax1 = ax
    ax2 = ax.twinx()

    bars1 = ax1.bar(x - width, n_points, width, label='Number of Points', alpha=0.8)
    bars2 = ax2.bar(x, densities, width, label='Density (pts/km²)', alpha=0.8, color='orange')
    bars3 = ax1.bar(x + width, areas, width, label='Area (km²)', alpha=0.8, color='green')

    # Labels and styling
    ax1.set_xlabel('Strategy')
    ax1.set_ylabel('Count / Area')
    ax2.set_ylabel('Density (pts/km²)')
    ax1.set_title('Coverage Metrics Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=45, ha='right')

    # Combine legends
    all_bars = [bars1, bars2, bars3]
    labels = [b.get_label() for b in all_bars]
    ax1.legend(all_bars, labels, loc='upper left', fontsize=8)

    ax1.grid(True, alpha=0.3, axis='y')


def _plot_density_distribution(
    ax: plt.Axes,
    results: Dict[str, Dict[str, Any]]
) -> None:
    """
    Plot density distribution for each strategy.

    Args:
        ax: Matplotlib axes object.
        results: Dictionary containing points for each strategy.
    """
    densities = []
    labels = []

    for name, data in results.items():
        metrics = data['metrics']
        densities.append(metrics['density_pts_per_km2'])
        labels.append(name)

    # Create bar plot
    colors = plt.cm.Set3(np.linspace(0, 1, len(densities)))
    bars = ax.barh(labels, densities, color=colors, alpha=0.8, edgecolor='black')

    # Add value labels on bars
    for bar, density in zip(bars, densities):
        width = bar.get_width()
        ax.text(
            width + max(densities) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f'{density:.1f}',
            ha='left',
            va='center',
            fontsize=9
        )

    ax.set_xlabel('Density (points per km²)')
    ax.set_title('Sampling Density Comparison')
    ax.grid(True, alpha=0.3, axis='x')


def plot_coverage_statistics(
    points_gdf: gpd.GeoDataFrame,
    output_path: Optional[str] = None,
    figsize: tuple = (12, 8)
) -> plt.Figure:
    """
    Plot coverage statistics and spatial distribution of sample points.

    Creates a comprehensive visualization showing:
    1. Spatial distribution heatmap
    2. Distance to nearest neighbor histogram
    3. Quadrant analysis

    Args:
        points_gdf: GeoDataFrame containing sample points.
        output_path: Optional path to save the figure (PNG format).
        figsize: Figure size (width, height) in inches.

    Returns:
        matplotlib Figure object.

    Raises:
        ValueError: If points_gdf is empty or missing geometry column.
        TypeError: If points_gdf is not a GeoDataFrame.

    Example:
        >>> from svipro import plot_coverage_statistics
        >>> fig = plot_coverage_statistics(points, 'coverage_stats.png')
        >>> plt.show()
    """
    if not isinstance(points_gdf, gpd.GeoDataFrame):
        raise TypeError(f"points_gdf must be GeoDataFrame, got {type(points_gdf)}")

    if len(points_gdf) == 0:
        raise ValueError("points_gdf is empty")

    if 'geometry' not in points_gdf.columns:
        raise ValueError("points_gdf must contain 'geometry' column")

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(
        'Coverage Statistics Analysis',
        fontsize=16,
        fontweight='bold'
    )

    # Flatten axes for easier iteration
    axes = axes.flatten()

    # 1. Spatial distribution (top-left)
    _plot_points_spatial_distribution(axes[0], points_gdf)

    # 2. Nearest neighbor distances (top-right)
    _plot_nearest_neighbor_distances(axes[1], points_gdf)

    # 3. Quadrant analysis (bottom-left)
    _plot_quadrant_analysis(axes[2], points_gdf)

    # 4. Summary statistics table (bottom-right)
    _plot_summary_statistics(axes[3], points_gdf)

    plt.tight_layout()

    # Save if path provided
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close(fig)

    return fig


def _plot_points_spatial_distribution(ax: plt.Axes, points_gdf: gpd.GeoDataFrame) -> None:
    """Plot spatial distribution of points."""
    coords = np.array([[pt.x, pt.y] for pt in points_gdf.geometry])

    # Create 2D histogram for density
    if len(coords) > 0:
        h = ax.hist2d(
            coords[:, 0],
            coords[:, 1],
            bins=50,
            cmap='YlOrRd',
            cmin=1
        )
        plt.colorbar(h[3], ax=ax, label='Point Count')
        ax.scatter(coords[:, 0], coords[:, 1], c='blue', s=1, alpha=0.3)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Spatial Distribution Heatmap')
    ax.grid(True, alpha=0.3)


def _plot_nearest_neighbor_distances(ax: plt.Axes, points_gdf: gpd.GeoDataFrame) -> None:
    """Plot histogram of nearest neighbor distances."""
    from scipy.spatial.distance import pdist, squareform

    coords = np.array([[pt.x, pt.y] for pt in points_gdf.geometry])

    if len(coords) > 1:
        # Calculate pairwise distances
        distances = pdist(coords)
        nearest_neighbor_dists = np.min(squareform(distances), axis=1)
        nearest_neighbor_dists = nearest_neighbor_dists[nearest_neighbor_dists > 0]

        if len(nearest_neighbor_dists) > 0:
            ax.hist(
                nearest_neighbor_dists,
                bins=30,
                color='steelblue',
                alpha=0.7,
                edgecolor='black'
            )
            ax.axvline(
                np.mean(nearest_neighbor_dists),
                color='red',
                linestyle='--',
                linewidth=2,
                label=f'Mean: {np.mean(nearest_neighbor_dists):.2f}'
            )
            ax.legend()
            ax.set_xlabel('Distance to Nearest Neighbor')
            ax.set_ylabel('Frequency')
        else:
            ax.text(0.5, 0.5, 'Insufficient points for analysis',
                   ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'Need at least 2 points for analysis',
               ha='center', va='center', transform=ax.transAxes)

    ax.set_title('Nearest Neighbor Distances')
    ax.grid(True, alpha=0.3)


def _plot_quadrant_analysis(ax: plt.Axes, points_gdf: gpd.GeoDataFrame) -> None:
    """Plot quadrant analysis of point distribution."""
    bounds = points_gdf.total_bounds
    minx, miny, maxx, maxy = bounds

    # Calculate midpoints
    midx = (minx + maxx) / 2
    midy = (miny + maxy) / 2

    # Count points in each quadrant
    coords = np.array([[pt.x, pt.y] for pt in points_gdf.geometry])

    quadrants = {
        'NW (upper-left)': np.sum((coords[:, 0] < midx) & (coords[:, 1] > midy)),
        'NE (upper-right)': np.sum((coords[:, 0] >= midx) & (coords[:, 1] > midy)),
        'SW (lower-left)': np.sum((coords[:, 0] < midx) & (coords[:, 1] <= midy)),
        'SE (lower-right)': np.sum((coords[:, 0] >= midx) & (coords[:, 1] <= midy))
    }

    # Create bar plot
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24']
    bars = ax.bar(quadrants.keys(), quadrants.values(), color=colors, alpha=0.8, edgecolor='black')

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height + max(quadrants.values()) * 0.01,
            f'{int(height)}',
            ha='center',
            va='bottom',
            fontsize=10
        )

    ax.set_ylabel('Number of Points')
    ax.set_title('Quadrant Distribution')
    ax.grid(True, alpha=0.3, axis='y')


def _plot_summary_statistics(ax: plt.Axes, points_gdf: gpd.GeoDataFrame) -> None:
    """Plot summary statistics table."""
    # Calculate statistics
    coords = np.array([[pt.x, pt.y] for pt in points_gdf.geometry])
    bounds = points_gdf.total_bounds

    stats = {
        'Statistic': [
            'Total Points',
            'Bounds (Min X)',
            'Bounds (Min Y)',
            'Bounds (Max X)',
            'Bounds (Max Y)',
            'X Range',
            'Y Range'
        ],
        'Value': [
            f"{len(points_gdf):,}",
            f"{bounds[0]:.4f}",
            f"{bounds[1]:.4f}",
            f"{bounds[2]:.4f}",
            f"{bounds[3]:.4f}",
            f"{bounds[2] - bounds[0]:.4f}",
            f"{bounds[3] - bounds[1]:.4f}"
        ]
    }

    # Add CRS if available
    if points_gdf.crs is not None:
        stats['Statistic'].append('CRS')
        stats['Value'].append(str(points_gdf.crs))

    # Create table
    table = ax.table(
        cellText=list(zip(stats['Statistic'], stats['Value'])),
        cellLoc='left',
        loc='center',
        colLabels=['Statistic', 'Value']
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style table
    for i in range(len(stats['Statistic']) + 1):
        for j in range(2):
            cell = table[(i, j)]
            if i == 0:  # Header
                cell.set_facecolor('#4472C4')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')

    ax.axis('off')
    ax.set_title('Summary Statistics', pad=20)


def plot_spatial_distribution(
    points_gdf: gpd.GeoDataFrame,
    boundary: Optional[Polygon] = None,
    output_path: Optional[str] = None,
    figsize: tuple = (10, 10),
    title: str = 'Sample Points Distribution'
) -> plt.Figure:
    """
    Create a clean spatial distribution plot.

    Args:
        points_gdf: GeoDataFrame containing sample points.
        boundary: Optional boundary polygon to display.
        output_path: Optional path to save the figure.
        figsize: Figure size (width, height) in inches.
        title: Plot title.

    Returns:
        matplotlib Figure object.

    Example:
        >>> from svipro import plot_spatial_distribution
        >>> fig = plot_spatial_distribution(points, boundary, 'distribution.png')
        >>> plt.show()
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot boundary if provided
    if boundary is not None and isinstance(boundary, Polygon):
        x, y = boundary.exterior.xy
        ax.plot(x, y, 'k-', linewidth=2, label='Boundary', alpha=0.7)
        ax.fill(x, y, color='gray', alpha=0.1)

    # Plot points
    coords = np.array([[pt.x, pt.y] for pt in points_gdf.geometry])

    # Create scatter plot with density coloring
    if len(coords) > 1:
        # Calculate point density using 2D histogram
        from scipy.stats import gaussian_kde

        try:
            # Try to calculate density
            kde = gaussian_kde(coords.T)
            density = kde(coords.T)

            # Normalize density for coloring
            density_normalized = (density - density.min()) / (density.max() - density.min() + 1e-10)

            scatter = ax.scatter(
                coords[:, 0],
                coords[:, 1],
                c=density_normalized,
                cmap='viridis',
                s=30,
                alpha=0.7,
                edgecolors='black',
                linewidths=0.5
            )

            plt.colorbar(scatter, ax=ax, label='Relative Density')
        except Exception:
            # Fallback to simple scatter if KDE fails
            ax.scatter(
                coords[:, 0],
                coords[:, 1],
                c='steelblue',
                s=30,
                alpha=0.7,
                edgecolors='black',
                linewidths=0.5
            )
    else:
        ax.scatter(
            coords[:, 0],
            coords[:, 1],
            c='steelblue',
            s=30,
            alpha=0.7,
            edgecolors='black',
            linewidths=0.5
        )

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal', adjustable='box')

    # Add point count annotation
    ax.annotate(
        f'Total Points: {len(points_gdf):,}',
        xy=(0.02, 0.98),
        xycoords='axes fraction',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
        fontsize=10,
        verticalalignment='top'
    )

    plt.tight_layout()

    # Save if path provided
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close(fig)

    return fig
