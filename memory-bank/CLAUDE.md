# SVIPro - AI开发规则配置

**项目**: SVIPro - Street View Imagery Research Protocol & Optimization
**开发者**: Jiale Guo & Mingfeng Tang
**课程**: Geospatial Processing, Politecnico di Milano

---

## 🚨 最高优先级规则（Always Apply）

以下规则**必须始终应用**，在任何代码生成前强制阅读：

### 1. 必读文件（代码前必读）

```python
# 重要提示：
# 写任何代码前必须完整阅读 memory-bank/architecture.md（包含完整数据库结构）
# 写任何代码前必须完整阅读 memory-bank/tech-stack.md
# 写任何代码前必须完整阅读 memory-bank/implementation-plan.md
# 写任何代码前必须完整阅读 memory-bank/progress.md（了解当前进度）
# 每完成一个重大功能或里程碑后，必须更新 memory-bank/architecture.md
# 每完成一个步骤后，必须更新 memory-bank/progress.md
```

### 2. 模块化原则（强制）

```python
# 禁止：
# - 创建单体巨文件（monolith）超过500行
# - 在一个文件中实现多个不相关功能
# - 硬编码配置参数

# 必须：
# - 每个模块只负责一个清晰的功能
# - 使用类和函数进行合理的抽象
# - 遵循单一职责原则（SRP）
# - 优先组合而非继承
```

### 3. 代码质量标准

```python
# 必须包含：
# - 类型提示（Type Hints）用于所有函数参数和返回值
# - Docstrings（Google风格）用于所有公共类和方法
# - 输入验证（validation）用于所有公共API
# - 错误处理（try-except）用于外部依赖调用
# - 单元测试（pytest）用于所有核心功能

# 示例：
from typing import Optional
import geopandas as gpd
from shapely.geometry import Polygon

def generate_samples(
    boundary: Polygon,
    spacing: float = 100.0,
    seed: Optional[int] = None
) -> gpd.GeoDataFrame:
    """
    Generate grid sampling points within the given boundary.

    Args:
        boundary: Area of interest as shapely Polygon
        spacing: Distance between sample points in meters
        seed: Random seed for reproducibility

    Returns:
        GeoDataFrame with sampling points and metadata

    Raises:
        ValueError: If boundary is invalid or spacing <= 0
    """
    if not isinstance(boundary, Polygon):
        raise ValueError("boundary must be a shapely Polygon")
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    # Implementation...
```

### 4. 测试驱动开发（TDD）

```python
# 开发流程：
# 1. 先写测试（test_*.py）
# 2. 运行测试（失败）
# 3. 编写代码（使测试通过）
# 4. 重构代码
# 5. 重复

# 命名规范：
# - 测试文件：test_<module>.py
# - 测试函数：test_<function>_<scenario>
# - 测试类：Test<ClassName>

# 示例：
def test_grid_sampling_with_valid_boundary():
    """Test grid sampling generates correct number of points."""
    boundary = box(0, 0, 1000, 1000)
    strategy = GridSampling(spacing=100, seed=42)
    points = strategy.generate(boundary)
    assert len(points) == 121  # 11x11 grid
```

---

## 📋 技术栈最佳实践

### 地理空间处理

```python
# 推荐：
# - 使用GeoDataFrame处理空间数据
# - 使用shapely进行几何运算
# - 使用pyproj进行坐标系转换
# - 缓存OSM下载的数据

# 避免：
# - 手动实现几何算法（使用shapely）
# - 在循环中重复创建对象
# - 不必要的坐标系转换

# 性能优化：
# - 使用numpy向量化操作
# - 使用geopandas的空间索引
# - 对大数据集使用分块处理
```

### 配置管理

```python
# 使用dataclass而非dict：
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class SamplingConfig:
    """Configuration for sampling strategy."""
    spacing: float = 100.0
    crs: str = "EPSG:4326"
    seed: int = 42
    boundary: Optional[Polygon] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'spacing': self.spacing,
            'crs': self.crs,
            'seed': self.seed,
        }
```

### 错误处理

```python
# 外部API调用（如OSM）：
import time
from typing import Optional

def fetch_osm_data(place_name: str, max_retries: int = 3) -> Optional[dict]:
    """Fetch OSM data with retry logic."""
    for attempt in range(max_retries):
        try:
            # Implementation...
            return data
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
    return None
```

---

## 🗂️ 项目架构规则

### 目录结构

```
src/svipro/
├── sampling/          # 采样策略（每个文件一个策略）
├── metadata/          # 元数据管理
├── visualization/     # 可视化工具
└── utils/            # 工具函数（按功能分组）
```

### 模块导入

```python
# 推荐：
from svipro import GridSampling, MetadataManager
from svipro.sampling import SamplingStrategy

# 避免：
from svipro.sampling.base import SamplingStrategy  # 太长
from svipro.sampling.base import *  # 不明确
```

### 依赖方向

```python
# 依赖层次：
# visualization → metadata → sampling
# utils → （可被所有模块使用）

# 禁止循环依赖：
# sampling 不能依赖 visualization
# metadata 不能依赖 visualization
```

---

## 📝 文档规范

### Docstring格式（Google Style）

```python
def calculate_metrics(points: gpd.GeoDataFrame) -> dict:
    """
    Calculate coverage quality metrics for sampling points.

    This function computes various metrics to assess the quality
    of spatial sampling, including point density, coverage area,
    and average spacing.

    Args:
        points: GeoDataFrame containing sampling point geometries

    Returns:
        Dictionary containing:
            - n_points: Total number of sampling points
            - area_km2: Coverage area in square kilometers
            - density_pts_per_km2: Points per square kilometer
            - avg_spacing_m: Average distance between points

    Raises:
        ValueError: If points GeoDataFrame is empty

    Example:
        >>> points = strategy.generate(boundary)
        >>> metrics = calculate_metrics(points)
        >>> print(f"Density: {metrics['density_pts_per_km2']}")
    """
    pass
```

### README和文档

```markdown
# 新功能文档模板

## 功能名称

### 用途
简要说明功能的用途和解决的问题

### 使用方法
\```python
from svipro import FeatureClass

instance = FeatureClass(param1, param2)
result = instance.method()
\```

### 参数说明
- param1: 参数1说明
- param2: 参数2说明

### 返回值
返回值说明

### 注意事项
- 重要提示1
- 重要提示2
```

---

## 🧪 测试规范

### 测试结构

```python
# tests/test_sampling.py
import pytest
from shapely.geometry import box
from svipro import GridSampling

class TestGridSampling:
    """Test suite for GridSampling class."""

    @pytest.fixture
    def sample_boundary(self):
        """Create a sample boundary for testing."""
        return box(0, 0, 1000, 1000)

    @pytest.fixture
    def strategy(self):
        """Create a GridSampling instance."""
        return GridSampling(spacing=100, seed=42)

    def test_generate_creates_correct_points(self, strategy, sample_boundary):
        """Test that generate creates expected number of points."""
        points = strategy.generate(sample_boundary)
        assert len(points) == 121

    def test_generate_with_invalid_spacing_raises_error(self, sample_boundary):
        """Test that invalid spacing raises ValueError."""
        strategy = GridSampling(spacing=-100)
        with pytest.raises(ValueError):
            strategy.generate(sample_boundary)
```

### 测试覆盖率

```bash
# 运行测试并检查覆盖率
pytest --cov=src/svipro --cov-report=html --cov-report=term

# 目标：
# - 整体覆盖率：> 80%
# - 核心模块（sampling/）：> 90%
# - 可视化模块：> 70%
```

---

## 🔄 Git提交规范

### Commit Message格式

```
<type>: <description>

[optional body]

[optional footer]
```

### Type类型

- `feat`: 新功能
- `fix`: Bug修复
- `test`: 测试相关
- `docs`: 文档更新
- `refactor`: 代码重构
- `chore`: 构建/工具
- `perf`: 性能优化

### 示例

```
feat: implement road network sampling strategy

- Add RoadNetworkSampling class in sampling/road_network.py
- Integrate osmnx for street network data
- Support different network types (drive, walk, bike)
- Add unit tests in tests/test_road_network.py

Closes #12
```

---

## ⚡ 性能优化规则

### 大数据处理

```python
# 推荐：分批处理
def process_large_dataset(data: gpd.GeoDataFrame, batch_size: int = 1000):
    """Process large dataset in batches."""
    results = []
    for i in range(0, len(data), batch_size):
        batch = data.iloc[i:i+batch_size]
        result = process_batch(batch)
        results.append(result)
    return pd.concat(results)

# 避免：一次性加载所有数据
```

### 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_osm_graph(place_name: str, network_type: str = "all"):
    """Fetch OSM graph with caching."""
    # Expensive operation, cached results
    pass
```

---

## 🚀 部署与发布

### 版本管理

```python
# svipro/__init__.py
__version__ = "0.1.0"  # 遵循语义化版本
```

### 依赖管理

```toml
# pyproject.toml
[project]
dependencies = [
    "geopandas>=0.14.0,<1.0.0",  # 明确版本范围
    "shapely>=2.0.0,<3.0.0",
]
```

---

## 🎯 特定场景规则

### 添加新的采样策略

1. 在`src/svipro/sampling/`创建新文件
2. 继承`SamplingStrategy`基类
3. 实现`generate()`方法
4. 添加类型提示和docstring
5. 在`tests/`创建对应测试文件
6. 在`__init__.py`中导出新类
7. 更新`architecture.md`
8. 更新`progress.md`

### 修改核心架构

1. 先讨论并更新`architecture.md`
2. 更新相关测试
3. 修改代码
4. 运行所有测试
5. 更新文档

---

## 📊 代码审查检查清单

提交代码前检查：

- [ ] 所有函数有类型提示
- [ ] 所有公共API有docstring
- [ ] 有对应的单元测试
- [ ] 测试覆盖率未下降
- [ ] 代码通过black格式化
- [ ] 代码通过flake8检查
- - 代码通过mypy类型检查
- [ ] 已更新相关文档
- [ ] 已更新architecture.md（如涉及架构变更）
- [ ] 已更新progress.md

---

## 🆘 常见问题

### Q: 如何处理外部依赖失败？

A: 使用重试机制和优雅降级：
```python
try:
    data = fetch_external_data()
except Exception as e:
    logger.warning(f"Failed to fetch data: {e}")
    data = get_cached_data_or_default()
```

### Q: 如何确保可复现性？

A: 总是使用random seed：
```python
import numpy as np

np.random.seed(config.seed)
```

### Q: 如何优化性能？

A:
1. 使用cProfile识别瓶颈
2. 使用numpy向量化
3. 缓存重复计算
4. 使用分批处理大数据

---

## 📚 参考资料

- [Python类型提示](https://docs.python.org/3/library/typing.html)
- [GeoPandas文档](https://geopandas.org/)
- [Pytest文档](https://docs.pytest.org/)
- [Google Python风格指南](https://google.github.io/styleguide/pyguide.html)

---

**最后更新**: 2025-01-21
**维护者**: Jiale Guo & Mingfeng Tang
