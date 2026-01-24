# SVIPro 完整使用指南

**SVI Research Protocol & Optimization** - 街景视图影像研究采样协议与优化框架

版本：v0.2.0
作者：Jiale Guo & Mingfeng Tang
机构：米兰理工大学
日期：2025-01-23

---

## 目录

1. [快速开始](#1-快速开始)
2. [安装说明](#2-安装说明)
3. [Python API 使用](#3-python-api-使用)
4. [命令行界面 (CLI)](#4-命令行界面-cli)
5. [Jupyter Notebook 教程](#5-jupyter-notebook-教程)
6. [常见问题](#6-常见问题)
7. [最佳实践](#7-最佳实践)
8. [进阶功能](#8-进阶功能)

---

## 1. 快速开始

### 1.1 安装

```bash
# 克隆仓库
git clone https://github.com/GuojialeGeographer/GProcessing2025.git
cd GProcessing2025

# 安装包
pip install -e .

# 验证安装
svipro --help
```

### 1.2 第一个采样示例

```python
from svipro import GridSampling, SamplingConfig
from shapely.geometry import box

# 定义研究区域（米兰市中心）
aoi = box(9.15, 45.42, 9.25, 45.52)

# 创建配置
config = SamplingConfig(spacing=100, seed=42)

# 生成网格采样点
strategy = GridSampling(config)
points = strategy.generate(aoi)

# 导出结果
strategy.to_geojson("milan_samples.geojson")

print(f"生成了 {len(points)} 个采样点")
```

---

## 2. 安装说明

### 2.1 系统要求

- Python 3.9 或更高版本
- 操作系统：Windows, macOS, Linux

### 2.2 依赖安装

SVIPro 自动安装以下核心依赖：

```
geopandas>=0.14.0    # 地理空间数据处理
shapely>=2.0.0       # 几何运算
osmnx>=2.0.0         # OpenStreetMap 路网数据
networkx>=3.1        # 图算法
matplotlib>=3.7.0    # 可视化
seaborn>=0.12.0      # 统计图表
folium>=0.14.0       # 交互式地图
pyyaml>=6.0.0        # 配置文件
click>=8.1.0         # CLI 框架
```

### 2.3 可选依赖

```bash
# Jupyter Notebook 支持（教程）
pip install jupyter notebook

# 高级可视化
pip install plotly

# 性能优化
pip install tqdm
```

---

## 3. Python API 使用

### 3.1 基础采样

#### 网格采样 (Grid Sampling)

```python
from svipro import GridSampling, SamplingConfig
from shapely.geometry import box

# 创建研究区域
aoi = box(9.15, 45.42, 9.25, 45.52)  # 米兰

# 配置采样参数
config = SamplingConfig(
    spacing=100.0,    # 100米间距
    crs="EPSG:4326",  # WGS84坐标系
    seed=42           # 随机种子（保证可复现性）
)

# 创建采样策略
strategy = GridSampling(config)

# 生成采样点
points = strategy.generate(aoi)

# 查看结果
print(f"采样点数量: {len(points)}")
print(points.head())
```

#### 路网采样 (Road Network Sampling)

```python
from svipro import RoadNetworkSampling, SamplingConfig

# 配置
config = SamplingConfig(spacing=100, seed=42)

# 创建路网采样策略
strategy = RoadNetworkSampling(
    config,
    network_type='drive',  # 可行驶道路
    # road_types={'primary', 'secondary'}  # 可选：过滤道路类型
)

# 生成采样点（需要网络连接下载OSM数据）
points = strategy.generate(aoi)
```

### 3.2 质量评估

```python
# 计算覆盖指标
metrics = strategy.calculate_coverage_metrics()

print(f"采样点数量: {metrics['n_points']}")
print(f"覆盖面积: {metrics['area_km2']:.2f} km²")
print(f"采样密度: {metrics['density_pts_per_km2']:.2f} pts/km²")

# 路网特定指标
if hasattr(strategy, 'calculate_road_network_metrics'):
    road_metrics = strategy.calculate_road_network_metrics()
    print(f"道路总长: {road_metrics['total_road_length_km']:.2f} km")
```

### 3.3 数据导出

```python
# 导出为 GeoJSON（带元数据）
strategy.to_geojson("samples.geojson", include_metadata=True)

# 导出配置
config_dict = config.to_dict()

# 从字典加载配置
config2 = SamplingConfig.from_dict(config_dict)
```

### 3.4 错误处理

```python
from svipro import (
    SVIProError,
    ConfigurationError,
    BoundaryError,
    suggest_fix
)

try:
    config = SamplingConfig(spacing=-100)  # 无效间距
except ConfigurationError as e:
    print(f"错误: {e}")
    print(f"详情: {e.details}")

    # 获取修复建议
    suggestion = suggest_fix(e)
    if suggestion:
        print(f"建议: {suggestion}")
```

---

## 4. 命令行界面 (CLI)

### 4.1 基础命令

```bash
# 查看帮助
svipro --help

# 查看子命令帮助
svipro sample --help
svipro sample grid --help
```

### 4.2 网格采样

```bash
# 基础用法
svipro sample grid \
  --spacing 100 \
  --aoi boundary.geojson \
  --output points.geojson

# 高级用法
svipro sample grid \
  --spacing 50 \
  --crs EPSG:3857 \
  --seed 123 \
  --aoi milano.geojson \
  --output milano_points.geojson \
  --metadata
```

### 4.3 路网采样

```bash
# 基础路网采样
svipro sample road-network \
  --spacing 100 \
  --aoi boundary.geojson \
  --output points.geojson

# 指定网络类型
svipro sample road-network \
  --spacing 100 \
  --network-type drive \
  --aoi boundary.geojson \
  --output points.geojson

# 过滤道路类型
svipro sample road-network \
  --spacing 50 \
  --network-type drive \
  --road-types primary \
  --road-types secondary \
  --aoi boundary.geojson \
  --output points.geojson
```

### 4.4 质量评估

```bash
# 计算质量指标
svipro quality metrics --points samples.geojson

# 输出示例：
# ✓ 采样点数量:     127
# ✓ 覆盖面积:       2.4500 km²
# ✓ 采样密度:       51.84 pts/km²
```

### 4.5 可视化

```bash
# 生成交互式地图
svipro visualize points-map \
  --points samples.geojson \
  --output map.html

# 生成统计图表
svipro visualize statistics \
  --points samples.geojson \
  --output stats.png

# 策略对比
svipro visualize compare \
  --grid-spacing 50 \
  --road-spacing 100 \
  --aoi boundary.geojson \
  --output comparison.png
```

### 4.6 协议生成

```bash
# 生成采样协议文件
svipro protocol create \
  --points samples.geojson \
  --output protocol.yaml
```

---

## 5. Jupyter Notebook 教程

### 5.1 启动 Jupyter

```bash
# 导航到 examples 目录
cd examples/

# 启动 Jupyter
jupyter notebook

# 或使用 JupyterLab
jupyter lab
```

### 5.2 入门教程

打开 `intro_to_svipro.ipynb` 学习：
- 基础概念
- 网格采样
- 路网采样
- 质量指标
- 可视化
- 最佳实践

**预计时间**：30-45分钟

### 5.3 高级教程

打开 `advanced_sampling_comparison.ipynb` 学习：
- 策略对比
- 间距优化
- 错误处理
- 性能优化
- 可复现性工作流

**预计时间**：45-60分钟

### 5.4 Notebook 示例

```python
# 在 Notebook 中使用
import matplotlib.pyplot as plt
from svipro import GridSampling, SamplingConfig
from shapely.geometry import box

# 创建配置
config = SamplingConfig(spacing=100, seed=42)
strategy = GridSampling(config)

# 生成采样点
aoi = box(9.15, 45.42, 9.25, 45.52)
points = strategy.generate(aoi)

# 可视化
fig, ax = plt.subplots(figsize=(10, 10))
points.plot(ax=ax, markersize=10, alpha=0.6)
ax.set_title('网格采样结果')
plt.show()
```

---

## 6. 常见问题

### 6.1 安装问题

**Q: pip install 失败，提示缺少 geopandas**

A: geopandas 依赖很多库，建议使用 conda：
```bash
conda install -c conda-forge geopandas
pip install -e .
```

**Q: ImportError: No module named 'svipro'**

A: 确保在项目根目录安装：
```bash
cd /path/to/GProcessing2025
pip install -e .
```

### 6.2 采样问题

**Q: 网格采样没有生成点**

A: 检查以下几点：
1. 边界是否太小
2. 间距是否太大
3. 使用更小的 spacing 值

```python
# 调试
print(f"边界面积: {boundary.area}")
print(f"间距: {config.spacing}")
print(f"面积比率: {boundary.area / (config.spacing ** 2):.3f}")
```

**Q: 路网采样失败，提示网络错误**

A:
1. 检查网络连接
2. 尝试更小的边界区域
3. 使用不同的 network_type
4. 检查 OSM 服务器状态

```python
# 调试
from svipro import handle_small_boundary, check_spacing_bounds

# 验证间距
check_spacing_bounds(spacing)

# 处理小边界
processed, modified = handle_small_boundary(boundary, spacing)
```

### 6.3 可视化问题

**Q: 地图不显示**

A:
1. 检查 CRS 是否正确
2. 确保有采样点生成
3. 尝试不同的可视化方法

```python
# 检查数据
print(f"采样点数量: {len(points)}")
print(f"CRS: {points.crs}")
print(f"范围: {points.total_bounds}")
```

### 6.4 性能问题

**Q: 大数据集采样很慢**

A:
1. 使用更大的间距
2. 分块处理
3. 使用性能工具

```python
from svipro import estimate_processing_time, warn_large_output

# 估计时间
time_est = estimate_processing_time(n_points=10000, strategy='grid')
print(f"预计耗时: {time_est:.1f} 秒")

# 大数据集警告
warn_large_output(n_points=50000)
```

---

## 7. 最佳实践

### 7.1 选择合适的采样策略

| 场景 | 推荐策略 | 原因 |
|------|----------|------|
| 城市绿地评估 | 网格采样 | 均匀覆盖，易于比较 |
| 街景可访问性 | 路网采样 | 符合实际情况 |
| 交通研究 | 路网采样 | 沿道路分布 |
| 总体覆盖评估 | 网格采样 | 空间代表性 |

### 7.2 设置合适的采样间距

| 区域类型 | 推荐间距 | 说明 |
|----------|----------|------|
| 城市密集区 | 50-100m | 高密度采样 |
| 城郊 | 100-200m | 中等密度 |
| 农村地区 | 200-500m | 低密度采样 |

### 7.3 确保可复现性

```python
# 始终设置随机种子
config = SamplingConfig(
    spacing=100,
    seed=42  # 固定种子保证可复现性
)

# 记录配置参数
config_dict = config.to_dict()
print(config_dict)
```

### 7.4 验证输入数据

```python
from svipro import validate_crs_compatibility, fix_invalid_geometry

# 验证 CRS 兼容性
compatible, warning = validate_crs_compatibility('EPSG:4326', 'EPSG:3857')
if not compatible:
    print(f"警告: {warning}")

# 修复无效几何
if not boundary.is_valid:
    boundary = fix_invalid_geometry(boundary)
```

### 7.5 导出完整元数据

```python
# 导出时包含元数据
strategy.to_geojson("output.geojson", include_metadata=True)

# 生成协议文件
import yaml
protocol_data = {
    'config': config.to_dict(),
    'metrics': strategy.calculate_coverage_metrics(),
    'timestamp': datetime.now().isoformat()
}

with open('protocol.yaml', 'w') as f:
    yaml.dump(protocol_data, f)
```

---

## 8. 进阶功能

### 8.1 自定义采样策略

```python
from svipro.sampling.base import SamplingStrategy, SamplingConfig
import geopandas as gpd
from shapely.geometry import Polygon

class CustomSampling(SamplingStrategy):
    """自定义采样策略"""

    def __init__(self, config: SamplingConfig):
        super().__init__(config)
        self.strategy_name = "custom_sampling"

    def generate(self, boundary: Polygon) -> gpd.GeoDataFrame:
        """实现自定义采样逻辑"""
        # 你的采样算法
        pass
```

### 8.2 批量处理

```python
# 处理多个区域
areas = {
    'milan': box(9.15, 45.42, 9.25, 45.52),
    'rome': box(12.4, 41.8, 12.6, 42.0),
}

results = {}
for name, aoi in areas.items():
    strategy = GridSampling(SamplingConfig(spacing=100, seed=42))
    points = strategy.generate(aoi)
    results[name] = points
```

### 8.3 性能优化

```python
from svipro.performance import DiskCache, ProgressTracker

# 使用缓存
cache = DiskCache(cache_dir="cache")

# 使用进度条
tracker = ProgressTracker(desc="生成采样点")

for i in range(len(areas)):
    # 你的采样代码
    tracker.update(1)
```

### 8.4 与其他工具集成

#### 与 QGIS 集成

```python
# 导出为 Shapefile
points.to_file("samples.shp", driver="ESRI Shapefile")

# 或 GeoJSON
points.to_file("samples.geojson", driver="GeoJSON")
```

#### 与 Pandas 集成

```python
import pandas as pd

# 转换为 DataFrame
df = pd.DataFrame({
    'longitude': points.geometry.x,
    'latitude': points.geometry.y,
    'sample_id': points['sample_id'],
    'spacing': points['spacing_m']
})

# 导出为 CSV
df.to_csv("samples.csv", index=False)
```

---

## 9. 故障排除

### 9.1 调试模式

```bash
# 启用详细输出
svipro sample grid --spacing 100 --aoi boundary.geojson --output points.geojson --verbose
```

### 9.2 日志记录

```python
import logging

# 启用日志
logging.basicConfig(level=logging.DEBUG)

# 使用 SVIPro
from svipro import GridSampling, SamplingConfig
strategy = GridSampling(SamplingConfig(spacing=100))
```

### 9.3 获取帮助

- **文档**: `docs/` 目录
- **教程**: `examples/` 目录
- **GitHub Issues**: https://github.com/GuojialeGeographer/GProcessing2025/issues
- **Email**: jiale.guo@mail.polimi.it, mingfeng.tang@mail.polimi.it

---

## 10. 引用

如果你在研究中使用 SVIPro，请引用：

```bibtex
@software{svipro2025,
  title = {SVIPro: Street View Imagery Research Protocol \& Optimization},
  author = {Guo, Jiale and Tang, Mingfeng},
  year = {2025},
  url = {https://github.com/GuojialeGeographer/GProcessing2025},
  institution = {Politecnico di Milano}
}
```

---

**祝您使用愉快！**

如有问题或建议，欢迎通过以上联系方式与我们取得联系。
