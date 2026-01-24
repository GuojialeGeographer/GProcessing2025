# SVIPro Examples and Tutorials

This directory contains Jupyter notebook tutorials demonstrating various features and capabilities of SVIPro.

## Available Notebooks

### 1. Introduction to SVIPro (`intro_to_svipro.ipynb`)

**Level:** Beginner
**Time:** 30-45 minutes

Learn the fundamentals of SVIPro:
- Installation and setup
- Basic concepts and terminology
- Grid sampling strategy
- Road network sampling strategy
- Quality metrics calculation
- Data export and visualization
- Best practices

**Prerequisites:**
- Basic Python knowledge
- Understanding of geographic concepts (latitude/longitude)

### 2. Advanced Sampling Comparison (`advanced_sampling_comparison.ipynb`)

**Level:** Advanced
**Time:** 45-60 minutes

Dive deeper into SVIPro capabilities:
- Comparing multiple sampling strategies
- Optimizing spacing for target sample size
- Error handling and edge cases
- Performance considerations
- Integration with external tools
- Reproducibility workflows

**Prerequisites:**
- Completion of Introduction tutorial
- Experience with pandas and geopandas
- Understanding of statistical sampling concepts

## How to Use These Notebooks

### Option 1: Jupyter Notebook

```bash
# Install Jupyter
pip install jupyter

# Navigate to examples directory
cd examples/

# Start Jupyter
jupyter notebook

# Open and run any notebook
```

### Option 2: JupyterLab

```bash
# Install JupyterLab
pip install jupyterlab

# Navigate to examples directory
cd examples/

# Start JupyterLab
jupyter lab
```

### Option 3: Google Colab

You can upload these notebooks to Google Colab to run them in the cloud:

1. Go to https://colab.research.google.com/
2. Click "File" → "Upload Notebook"
3. Upload the desired notebook
4. Run the cells

**Note:** Some features (like road network sampling) may have limitations in Colab due to network restrictions.

## Installation

Before running the notebooks, make sure you have SVIPro installed:

```bash
# Install from local directory
cd ..
pip install -e .

# Or install from PyPI (if published)
pip install svipro
```

Install additional dependencies for the notebooks:

```bash
pip install jupyter matplotlib seaborn pandas numpy geopandas shapely
```

## Notebook-Specific Requirements

### Internet Connection

- **Road network sampling** requires internet connection to download data from OpenStreetMap
- Some visualizations may require internet for map tiles

### Data Files

The notebooks will create sample output files:
- `grid_samples_milan.geojson`
- `road_samples_milan.geojson`
- `study_area.geojson`
- `samples.geojson`
- `samples.csv`
- `milan_reproducible_samples.geojson`

You can delete these after running the notebooks.

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'svipro'`

**Solution:** Make sure you've installed SVIPro:
```bash
cd /path/to/GProcessing2025
pip install -e .
```

**Issue:** OSM download fails

**Solution:** Check your internet connection and try:
- Using a smaller boundary area
- Different network_type ('walk' vs 'drive')
- Running the cell again (OSM servers may be busy)

**Issue:** Visualizations don't display

**Solution:** Ensure you have matplotlib and seaborn installed:
```bash
pip install matplotlib seaborn
```

## Learning Path

We recommend following this sequence:

1. **Start here:** `intro_to_svipro.ipynb`
   - Learn the basics
   - Understand core concepts
   - Run your first sampling

2. **Next step:** `advanced_sampling_comparison.ipynb`
   - Explore advanced features
   - Learn optimization techniques
   - Build reproducible workflows

3. **Apply to your research:**
   - Use your own study area
   - Adapt examples to your needs
   - Integrate into your workflow

## Additional Resources

- **API Documentation:** `../docs/api_reference.md`
- **Getting Started Guide:** `../docs/tutorials/getting_started.md`
- **Case Studies:** `../docs/case_studies/`
- **GitHub Repository:** https://github.com/GuojialeGeographer/GProcessing2025

## Feedback and Contributions

Found a bug? Have a suggestion? Please:
- Open an issue on GitHub
- Submit a pull request
- Contact the authors

## Citation

If you use SVIPro in your research, please cite:

```bibtex
@software{svipro2025,
  title = {SVIPro: Street View Imagery Research Protocol & Optimization},
  author = {Guo, Jiale and Tang, Mingfeng},
  year = {2025},
  url = {https://github.com/GuojialeGeographer/GProcessing2025},
  institution = {Politecnico di Milano}
}
```

---

**Happy Sampling! 🎉**
