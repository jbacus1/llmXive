"""
Visualization Service for GIS and Climate Data

Generates visualizations for climate-smart agricultural analysis.
Uses matplotlib for plotting and integrates with geopandas/rasterio for GIS data.

Logging: All operations are logged with appropriate levels for debugging and audit.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import rasterio
from matplotlib.patches import Patch
from rasterio.plot import show as riodisplay

from src.config.constants import LOG_LEVEL, VISUALIZATION_OUTPUT_DIR

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, 'INFO'))

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class VisualizationService:
    """
    Service for generating visualizations from agricultural and climate data.

    Supports:
    - GIS-based risk mapping (choropleth, heatmaps)
    - Time series plots for climate patterns
    - Yield prediction visualizations
    - Recommendation impact charts
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize visualization service.

        Args:
            output_dir: Directory for saving visualizations. Defaults to config.
        """
        self.output_dir = Path(output_dir or VISUALIZATION_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"VisualizationService initialized with output_dir: {self.output_dir}")

    def _generate_filename(self, prefix: str, format: str = 'png') -> str:
        """Generate timestamped filename for visualization."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.{format}"
        logger.debug(f"Generated filename: {filename}")
        return filename

    def create_choropleth_map(
        self,
        gdf: gpd.GeoDataFrame,
        column: str,
        title: str,
        cmap: str = 'YlOrRd',
        output_file: Optional[str] = None
    ) -> str:
        """
        Create a choropleth map from GeoDataFrame.

        Args:
            gdf: GeoDataFrame with geometry and data columns
            column: Column name to visualize
            title: Map title
            cmap: Matplotlib colormap name
            output_file: Optional filename to save to

        Returns:
            Path to saved visualization
        """
        logger.info(f"Creating choropleth map for column '{column}' with {len(gdf)} features")

        try:
            # Validate input
            if not isinstance(gdf, gpd.GeoDataFrame):
                raise TypeError("Input must be a GeoDataFrame")
            if column not in gdf.columns:
                raise ValueError(f"Column '{column}' not found in GeoDataFrame")
            logger.debug("Input validation passed")

            # Create figure
            fig, ax = plt.subplots(figsize=(12, 10))
            logger.debug("Figure created")

            # Plot choropleth
            gdf.plot(
                column=column,
                cmap=cmap,
                linewidth=0.8,
                ax=ax,
                edgecolor='0.8',
                legend=True
            )
            logger.debug(f"Choropleth plot generated with colormap '{cmap}'")

            # Add title and labels
            ax.set_title(title, fontsize=16, pad=20)
            ax.set_axis_off()

            # Determine output path
            if output_file:
                save_path = self.output_dir / output_file
            else:
                save_path = self.output_dir / self._generate_filename('choropleth')

            # Save figure
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Choropleth map saved to: {save_path}")

            return str(save_path)

        except Exception as e:
            logger.error(f"Failed to create choropleth map: {str(e)}", exc_info=True)
            raise

    def create_time_series_plot(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_cols: Union[str, List[str]],
        title: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Create time series plot for climate/yield data.

        Args:
            df: DataFrame with time series data
            x_col: Column name for x-axis (time)
            y_cols: Column name(s) for y-axis
            title: Plot title
            output_file: Optional filename to save to

        Returns:
            Path to saved visualization
        """
        logger.info(f"Creating time series plot with {len(df)} data points")

        try:
            # Validate input
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Input must be a DataFrame")
            if x_col not in df.columns:
                raise ValueError(f"Column '{x_col}' not found in DataFrame")

            y_cols_list = [y_cols] if isinstance(y_cols, str) else y_cols
            for col in y_cols_list:
                if col not in df.columns:
                    raise ValueError(f"Column '{col}' not found in DataFrame")
            logger.debug("Input validation passed")

            # Create figure
            fig, ax = plt.subplots(figsize=(14, 7))
            logger.debug("Figure created")

            # Plot each series
            colors = list(mcolors.CSS4_COLORS.values())[:len(y_cols_list)]
            for i, col in enumerate(y_cols_list):
                ax.plot(
                    df[x_col],
                    df[col],
                    label=col,
                    color=colors[i % len(colors)],
                    linewidth=2
                )
            logger.debug(f"Plotted {len(y_cols_list)} time series")

            # Add title and labels
            ax.set_title(title, fontsize=16)
            ax.set_xlabel(x_col, fontsize=12)
            ax.set_ylabel('Value', fontsize=12)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            # Determine output path
            if output_file:
                save_path = self.output_dir / output_file
            else:
                save_path = self.output_dir / self._generate_filename('timeseries')

            # Save figure
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Time series plot saved to: {save_path}")

            return str(save_path)

        except Exception as e:
            logger.error(f"Failed to create time series plot: {str(e)}", exc_info=True)
            raise

    def create_risk_heatmap(
        self,
        risk_scores: pd.DataFrame,
        x_col: str,
        y_col: str,
        value_col: str,
        title: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Create heatmap visualization for risk scores.

        Args:
            risk_scores: DataFrame with x, y, and value columns
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            value_col: Column name for heatmap values
            title: Plot title
            output_file: Optional filename to save to

        Returns:
            Path to saved visualization
        """
        logger.info(f"Creating risk heatmap with {len(risk_scores)} data points")

        try:
            # Validate input
            required_cols = [x_col, y_col, value_col]
            for col in required_cols:
                if col not in risk_scores.columns:
                    raise ValueError(f"Column '{col}' not found in DataFrame")
            logger.debug("Input validation passed")

            # Create pivot table for heatmap
            pivot = risk_scores.pivot_table(
                index=y_col,
                columns=x_col,
                values=value_col,
                aggfunc='mean'
            )
            logger.debug(f"Pivot table created with shape {pivot.shape}")

            # Create figure
            fig, ax = plt.subplots(figsize=(14, 10))
            logger.debug("Figure created")

            # Plot heatmap
            im = ax.imshow(pivot.values, cmap='RdYlGn_r', aspect='auto')
            logger.debug("Heatmap rendered")

            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(value_col)

            # Add title and labels
            ax.set_title(title, fontsize=16, pad=20)
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_yticks(range(len(pivot.index)))
            ax.set_xticklabels(pivot.columns, rotation=45)
            ax.set_yticklabels(pivot.index)

            # Add value annotations
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    text = ax.text(
                        j, i, f'{pivot.values[i, j]:.2f}',
                        ha='center', va='center',
                        color='black' if pivot.values[i, j] > pivot.values.mean() else 'white'
                    )

            # Determine output path
            if output_file:
                save_path = self.output_dir / output_file
            else:
                save_path = self.output_dir / self._generate_filename('heatmap')

            # Save figure
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Risk heatmap saved to: {save_path}")

            return str(save_path)

        except Exception as e:
            logger.error(f"Failed to create risk heatmap: {str(e)}", exc_info=True)
            raise

    def create_recommendation_bar_chart(
        self,
        recommendations: pd.DataFrame,
        x_col: str,
        score_col: str,
        title: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Create bar chart for recommendation scores.

        Args:
            recommendations: DataFrame with recommendations and scores
            x_col: Column name for recommendation labels
            score_col: Column name for scores
            title: Plot title
            output_file: Optional filename to save to

        Returns:
            Path to saved visualization
        """
        logger.info(f"Creating recommendation bar chart with {len(recommendations)} items")

        try:
            # Validate input
            if x_col not in recommendations.columns:
                raise ValueError(f"Column '{x_col}' not found in DataFrame")
            if score_col not in recommendations.columns:
                raise ValueError(f"Column '{score_col}' not found in DataFrame")
            logger.debug("Input validation passed")

            # Sort by score descending
            sorted_df = recommendations.sort_values(by=score_col, ascending=False)

            # Create figure
            fig, ax = plt.subplots(figsize=(12, 8))
            logger.debug("Figure created")

            # Plot bar chart
            colors = ['green' if score > 0.7 else 'orange' if score > 0.4 else 'red'
                     for score in sorted_df[score_col]]
            ax.bar(
                sorted_df[x_col],
                sorted_df[score_col],
                color=colors,
                edgecolor='black',
                linewidth=0.5
            )
            logger.debug(f"Bar chart rendered with {len(sorted_df)} bars")

            # Rotate x labels if needed
            if len(sorted_df) > 5:
                plt.xticks(rotation=45, ha='right')

            # Add title and labels
            ax.set_title(title, fontsize=16, pad=20)
            ax.set_xlabel('Recommendation', fontsize=12)
            ax.set_ylabel('Adoption Score', fontsize=12)
            ax.set_ylim(0, 1.1)
            ax.axhline(y=0.7, color='green', linestyle='--', alpha=0.5, label='High Priority')
            ax.axhline(y=0.4, color='orange', linestyle='--', alpha=0.5, label='Medium Priority')
            ax.legend()

            # Determine output path
            if output_file:
                save_path = self.output_dir / output_file
            else:
                save_path = self.output_dir / self._generate_filename('recommendations')

            # Save figure
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Recommendation bar chart saved to: {save_path}")

            return str(save_path)

        except Exception as e:
            logger.error(f"Failed to create recommendation bar chart: {str(e)}", exc_info=True)
            raise

    def create_raster_visualization(
        self,
        raster_path: str,
        title: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Create visualization from raster data.

        Args:
            raster_path: Path to raster file (GeoTIFF, etc.)
            title: Plot title
            output_file: Optional filename to save to

        Returns:
            Path to saved visualization
        """
        logger.info(f"Creating raster visualization from: {raster_path}")

        try:
            # Validate input file exists
            if not os.path.exists(raster_path):
                raise FileNotFoundError(f"Raster file not found: {raster_path}")
            logger.debug("Raster file validated")

            # Open raster
            with rasterio.open(raster_path) as src:
                logger.debug(f"Raster opened: {src.count} bands, {src.width}x{src.height}")

                # Create figure
                fig, ax = plt.subplots(figsize=(14, 10))
                logger.debug("Figure created")

                # Display raster
                riodisplay(src, ax=ax)
                logger.debug("Raster displayed")

                # Add title
                ax.set_title(title, fontsize=16, pad=20)

                # Determine output path
                if output_file:
                    save_path = self.output_dir / output_file
                else:
                    base_name = Path(raster_path).stem
                    save_path = self.output_dir / self._generate_filename(f'raster_{base_name}')

                # Save figure
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                plt.close(fig)
                logger.info(f"Raster visualization saved to: {save_path}")

                return str(save_path)

        except Exception as e:
            logger.error(f"Failed to create raster visualization: {str(e)}", exc_info=True)
            raise

    def generate_comparison_chart(
        self,
        df: pd.DataFrame,
        x_col: str,
        before_col: str,
        after_col: str,
        title: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Create before/after comparison chart for intervention analysis.

        Args:
            df: DataFrame with before and after data
            x_col: Column name for x-axis labels
            before_col: Column name for before values
            after_col: Column name for after values
            title: Plot title
            output_file: Optional filename to save to

        Returns:
            Path to saved visualization
        """
        logger.info(f"Creating comparison chart with {len(df)} comparison points")

        try:
            # Validate input
            required_cols = [x_col, before_col, after_col]
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Column '{col}' not found in DataFrame")
            logger.debug("Input validation passed")

            # Create figure
            fig, ax = plt.subplots(figsize=(14, 8))
            logger.debug("Figure created")

            # Create bar width
            x = range(len(df))
            width = 0.35

            # Plot bars
            ax.bar(
                [i - width/2 for i in x],
                df[before_col],
                width,
                label='Before Intervention',
                color='red',
                alpha=0.7
            )
            ax.bar(
                [i + width/2 for i in x],
                df[after_col],
                width,
                label='After Intervention',
                color='green',
                alpha=0.7
            )
            logger.debug("Comparison bars rendered")

            # Add title and labels
            ax.set_title(title, fontsize=16, pad=20)
            ax.set_xlabel(x_col, fontsize=12)
            ax.set_ylabel('Value', fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(df[x_col], rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

            # Determine output path
            if output_file:
                save_path = self.output_dir / output_file
            else:
                save_path = self.output_dir / self._generate_filename('comparison')

            # Save figure
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Comparison chart saved to: {save_path}")

            return str(save_path)

        except Exception as e:
            logger.error(f"Failed to create comparison chart: {str(e)}", exc_info=True)
            raise


def log_visualization_operation(operation: str, status: str, details: str = None):
    """
    Standalone function for logging visualization operations.

    Args:
        operation: Name of the visualization operation
        status: Status of the operation (success, failure, in_progress)
        details: Optional additional details
    """
    msg = f"Visualization Operation: {operation} - Status: {status}"
    if details:
        msg += f" - Details: {details}"

    if status == 'success':
        logger.info(msg)
    elif status == 'failure':
        logger.error(msg)
    else:
        logger.debug(msg)