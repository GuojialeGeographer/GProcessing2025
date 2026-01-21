"""
Command Line Interface for SVIPro.

This module provides a command-line interface for the SVIPro package,
enabling users to perform spatial sampling operations directly from the terminal.

Available Commands:
    - svipro sample grid: Grid-based sampling
    - svipro protocol create: Generate sampling protocol
    - svipro quality metrics: Calculate coverage metrics
    - svipro visualize points: Visualize sample points

Example:
    $ svipro sample grid --spacing 100 --aoi boundary.geojson --output points.geojson
"""

import click
import sys
from pathlib import Path
from typing import Optional

import geopandas as gpd
from shapely.geometry import Polygon

from svipro import GridSampling, SamplingConfig
from svipro.sampling.base import SamplingStrategy


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'  # bright pink
    OKBLUE = '\033[94m'  # bright blue
    OKCYAN = '\033[96m'  # bright cyan
    OKGREEN = '\033[92m'  # bright green
    WARNING = '\3[93m'  # bright yellow
    FAIL = '\033[91m'   # bright red
    ENDC = '\033[0m'    # end color
    BOLD = '\033[1m'     # bold
    UNDERLINE = '\033[4m' # underline


def success_msg(message: str) -> None:
    """Print success message in green."""
    click.echo(f"{Colors.OKGREEN}✓{Colors.ENDC} {message}")


def error_msg(message: str) -> None:
    """Print error message in red."""
    click.echo(f"{Colors.FAIL}✗{Colors.ENDC} {message}", err=True)


def info_msg(message: str) -> None:
    """Print info message in blue."""
    click.echo(f"{Colors.OKBLUE}ℹ{Colors.ENDC} {message}")


def warning_msg(message: str) -> None:
    """Print warning message in yellow."""
    click.echo(f"{Colors.WARNING}⚠{Colors.ENDC} {message}")


def validate_aoi_file(ctx, param, value: str) -> str:
    """
    Validate that AOI file exists and is readable.

    Args:
        ctx: Click context
        param: Click parameter
        value: File path from user input

    Returns:
        Validated file path

    Raises:
        click.BadParameter: If file doesn't exist or can't be read
    """
    path = Path(value)

    if not path.exists():
        raise click.BadParameter(
            f"AOI file not found: {value}"
        )

    if not path.is_file():
        raise click.BadParameter(
            f"AOI path must be a file, not directory: {value}"
        )

    # Try to read as GeoJSON to validate format
    try:
        gdf = gpd.read_file(path)
        if 'geometry' not in gdf.columns:
            raise click.BadParameter(
                f"Invalid GeoJSON file (no geometry column): {value}"
            )
    except Exception as e:
        raise click.BadParameter(
            f"Failed to read GeoJSON file '{value}': {e}"
        )

    return value


def validate_output_path(ctx, param, value: str) -> str:
    """
    Validate output path and create directory if needed.

    Args:
        ctx: Click context
        param: Click parameter
        value: Output file path

    Returns:
        Validated output path

    Raises:
        click.BadParameter: If path is invalid
    """
    path = Path(value)

    # Create parent directory if it doesn't exist
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise click.BadParameter(
            f"Cannot create output directory: {e}"
        )

    return value


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    SVIPro Command Line Interface.

    A standardized framework for reproducible Street View Imagery sampling design.
    """
    pass


@cli.group()
def sample():
    """
    Generate spatial sample points using various strategies.

    This command group provides different sampling methods for
    generating spatial sample points within a given area of interest.
    """
    pass


@sample.command()
@click.option(
    '--spacing',
    type=float,
    default=100.0,
    show_default=True,
    help='Distance between sample points in meters'
)
@click.option(
    '--crs',
    type=str,
    default='EPSG:4326',
    show_default=True,
    help='Coordinate Reference System (EPSG code)'
)
@click.option(
    '--seed',
    type=int,
    default=42,
    show_default=True,
    help='Random seed for reproducibility'
)
@click.option(
    '--aoi',
    type=str,
    required=True,
    callback=validate_aoi_file,
    help='Path to AOI boundary file (GeoJSON format)'
)
@click.option(
    '--output',
    type=str,
    required=True,
    callback=validate_output_path,
    help='Output file path for sample points (GeoJSON format)'
)
@click.option(
    '--metadata',
    is_flag=True,
    default=False,
    show_default=True,
    help='Include metadata in output GeoJSON'
)
def grid(spacing: float, crs: str, seed: int, aoi: str, output: str, metadata: bool):
    """
    Generate grid-based sample points within the given boundary.

    Creates a regular grid of sample points with the specified spacing.
    Points are aligned with the coordinate system axes and only points
    within the boundary are included.

    Example:
        $ svipro sample grid --spacing 100 --aoi boundary.geojson --output points.geojson

    \b
    Advanced usage:
        $ svipro sample grid --spacing 50 --crs EPSG:3857 --aoi hk.geojson --output hk_points.geojson --metadata
    """
    try:
        info_msg(f"Loading AOI from: {aoi}")

        # Read AOI
        aoi_gdf = gpd.read_file(aoi)

        # Extract boundary (assuming first feature or union all)
        if len(aoi_gdf) == 1:
            boundary = aoi_gdf.geometry.iloc[0]
        else:
            # Union all geometries if multiple features
            boundary = aoi_gdf.unary_union_all()

        if not isinstance(boundary, Polygon):
            # If not a polygon, try to get the convex hull
            boundary = boundary.convex_hull

        info_msg(f"Boundary area: {boundary.area:.2f} square degrees")

        # Create configuration
        config = SamplingConfig(
            spacing=spacing,
            crs=crs,
            seed=seed
        )

        # Create strategy and generate points
        info_msg(f"Generating grid sample points with {spacing}m spacing...")
        strategy = GridSampling(config)

        points = strategy.generate(boundary)

        if len(points) == 0:
            warning_msg("No sample points generated. "
                        "Check if boundary is large enough for the spacing.")
            return

        success_msg(f"Generated {len(points)} sample points")

        # Calculate and display metrics
        metrics = strategy.calculate_coverage_metrics()
        info_msg(f"Coverage area: {metrics['area_km2']:.4f} km²")
        info_msg(f"Sampling density: {metrics['density_pts_per_km2']:.2f} pts/km²")

        # Export to GeoJSON
        info_msg(f"Exporting to: {output}")
        strategy.to_geojson(output, include_metadata=metadata)

        success_msg(f"Sample points saved to: {output}")

    except FileNotFoundError as e:
        error_msg(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        error_msg(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        error_msg(f"Unexpected error: {e}")
        sys.exit(1)


@cli.group()
def protocol():
    """
    Generate and manage sampling protocol documentation.

    This command group provides tools for creating, validating, and
    managing sampling protocol files that document the complete sampling
    methodology.
    """
    pass


@protocol.command()
@click.option(
    '--points',
    type=str,
    required=True,
    callback=validate_aoi_file,
    help='Path to sample points GeoJSON file'
)
@click.option(
    '--output',
    type=str,
    default='sampling_protocol.yaml',
    show_default=True,
    help='Output protocol file path (YAML format)'
)
def create(points: str, output: str):
    """
    Generate sampling protocol file from sample points.

    Extracts metadata from sample points and creates a standardized YAML
    protocol file documenting the sampling methodology.

    Example:
        $ svipro protocol create --points samples.geojson --output protocol.yaml
    """
    try:
        info_msg(f"Loading sample points from: {points}")

        # Read sample points
        points_gdf = gpd.read_file(points)

        if len(points_gdf) == 0:
            error_msg("Sample points file is empty")
            sys.exit(1)

        # Extract metadata
        strategy_name = points_gdf['strategy'].iloc[0] if 'strategy' in points_gdf.columns else 'unknown'
        spacing = points_gdf['spacing_m'].iloc[0] if 'spacing_m' in points_gdf.columns else 0
        n_points = len(points_gdf)

        # Calculate metrics
        bounds = points_gdf.total_bounds
        from shapely.geometry import box
        bbox = box(*bounds)
        area_m2 = bbox.area
        area_km2 = area_m2 / 1e6

        # Generate protocol content
        import yaml
        from datetime import datetime

        protocol_data = {
            'sampling_protocol': {
                'version': '0.1.0',
                'timestamp': datetime.now().isoformat(),
                'authors': [
                    'Jiale Guo <jiale.guo@mail.polimi.it>',
                    'Mingfeng Tang <mingfeng.tang@mail.polimi.it>'
                ],
                'aoi': {
                    'source_file': points,
                    'bounds': [float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3])],
                    'crs': str(points_gdf.crs)
                },
                'strategy': {
                    'name': strategy_name,
                    'spacing_m': spacing,
                    'parameters': {
                        'algorithm': 'regular_grid',
                        'alignment': 'bottom_left'
                    }
                },
                'quality_metrics': {
                    'n_points': n_points,
                    'area_km2': round(area_km2, 4),
                    'density_pts_per_km2': round(n_points / area_km2, 2) if area_km2 > 0 else 0
                },
                'reproducibility': {
                    'svipro_version': '0.1.0',
                    'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    'dependencies': {
                        'geopandas': '>=0.14.0',
                        'shapely': '>=2.0.0',
                        'numpy': '>=1.24.0'
                    }
                }
            }
        }

        # Write protocol file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(protocol_data, f, default_flow_style=False, sort_keys=False)

        success_msg(f"Protocol file saved to: {output}")

    except FileNotFoundError as e:
        error_msg(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        error_msg(f"Error generating protocol: {e}")
        sys.exit(1)


@cli.group()
def quality():
    """
    Calculate and display quality metrics for sample points.

    This command group provides tools for assessing the quality and
    characteristics of spatial sampling results.
    """
    pass


@quality.command()
@click.option(
    '--points',
    type=str,
    required=True,
    callback=validate_aoi_file,
    help='Path to sample points GeoJSON file'
)
def metrics(points: str):
    """
    Calculate and display coverage quality metrics.

    Computes various metrics to assess the quality and characteristics
    of the spatial sampling, including point density, coverage area, and
    spatial extent.

    Example:
        $ svipro quality metrics --points samples.geojson
    """
    try:
        info_msg(f"Loading sample points from: {points}")

        # Read sample points
        points_gdf = gpd.read_file(points)

        if len(points_gdf) == 0:
            error_msg("Sample points file is empty")
            sys.exit(1)

        # Calculate metrics using base class directly
        # We can use GridSampling since it has the calculate_coverage_metrics method
        from svipro import GridSampling, SamplingConfig

        spacing = points_gdf['spacing_m'].iloc[0] if 'spacing_m' in points_gdf.columns else 100
        config = SamplingConfig(spacing=spacing, crs=str(points_gdf.crs))
        strategy = GridSampling(config)
        strategy._sample_points = points_gdf
        metrics = strategy.calculate_coverage_metrics()

        # Display metrics
        click.echo(f"\n{Colors.BOLD}Sampling Quality Metrics{Colors.ENDC}")
        click.echo("=" * 50)

        click.echo(f"\n📊 {Colors.OKCYAN}Coverage Metrics:{Colors.ENDC}")
        click.echo(f"  Number of points:     {Colors.BOLD}{metrics['n_points']}{Colors.ENDC}")
        click.echo(f"  Coverage area:       {metrics['area_km2']:.4f} km²")
        click.echo(f"  Sampling density:    {metrics['density_pts_per_km2']:.2f} pts/km²")

        click.echo(f"\n📍 {Colors.OKCYAN}Spatial Extent:{Colors.ENDC}")
        click.echo(f"  Min X: {metrics['bounds'][0]:.4f}")
        click.echo(f"  Min Y: {metrics['bounds'][1]:.4f}")
        click.echo(f"  Max X: {metrics['bounds'][2]:.4f}")
        click.echo(f"  Max Y: {metrics['bounds'][3]:.4f}")

        click.echo(f"\n🌐 {Colors.OKCYAN}Coordinate System:{Colors.ENDC}")
        click.echo(f"  CRS: {metrics['crs']}")

        success_msg("\nMetrics calculated successfully")

    except FileNotFoundError as e:
        error_msg(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        error_msg(f"Error calculating metrics: {e}")
        sys.exit(1)


@cli.group()
def visualize():
    """
    Visualize sample points and coverage.

    This command group provides tools for creating visualizations
    of spatial sampling results, including interactive maps and
    coverage analysis plots.
    """
    pass


@visualize.command()
@click.option(
    '--points',
    type=str,
    required=True,
    callback=validate_aoi_file,
    help='Path to sample points GeoJSON file'
)
@click.option(
    '--output',
    type=str,
    default='coverage_map.html',
    show_default=True,
    help='Output HTML file path for the map'
)
@click.option(
    '--title',
    type=str,
    default='Sampling Coverage Map',
    show_default=True,
    help='Title for the map'
)
def points_map(points: str, output: str, title: str):
    """
    Create an interactive map showing sample points.

    Generates an interactive HTML map using Folium, displaying the
    sample points and their spatial distribution. The map can be opened
    in any web browser.

    Example:
        $ svipro visualize points --points samples.geojson --output map.html
        $ svipro visualize points --points samples.geojson --title "My Study Area" --output my_map.html
    """
    try:
        import folium

        info_msg(f"Loading sample points from: {points}")

        # Read sample points
        points_gdf = gpd.read_file(points)

        if len(points_gdf) == 0:
            error_msg("Sample points file is empty")
            sys.exit(1)

        # Get centroid for map center
        bounds = points_gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        info_msg(f"Creating map with {len(points_gdf)} points...")

        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # Add sample points
        for idx, row in points_gdf.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=5,
                popup=f"Point: {row.get('sample_id', idx)}",
                color='blue',
                fill=True,
                fill_opacity=0.6,
                weight=2
            ).add_to(m)

        # Add bounds outline
        folium.GeoJson(
            data=points_gdf.geometry.__geo_interface__,
            style_function=lambda x: {
                'fillColor': 'green',
                'color': 'green',
                'weight': 2,
                'fillOpacity': 0.1
            }
        ).add_to(m)

        # Add tile layer with labels
        folium.TileLayer('OpenStreetMap', attr='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors').add_to(m)

        # Fit map to bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        # Save map
        output_path = Path(output)
        m.save(str(output_path))

        success_msg(f"Interactive map saved to: {output_path}")
        info_msg(f"Open the file in a web browser to view the map.")

    except FileNotFoundError as e:
        error_msg(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        error_msg(f"Error creating visualization: {e}")
        sys.exit(1)


def main():
    """Entry point for the CLI when run as a script."""
    cli()


if __name__ == '__main__':
    main()
