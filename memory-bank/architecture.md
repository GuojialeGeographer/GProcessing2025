# SpatialSamplingPro 项目架构（Architecture）

**最后更新**: 2025-01-25

## 目录结构

```
GProcessing2025/
├── src/
│   ├── ssp/                       # 主包 (SpatialSamplingPro)
│   │   ├── __init__.py            # 包入口，导出核心类
│   │   ├── sampling/              # 采样策略模块
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # ⚠️ 核心抽象基类
│   │   │   ├── grid.py            # 网格采样实现
│   │   │   └── road_network.py    # 路网采样实现
│   │   ├── metadata/              # 元数据管理
│   │   │   ├── __init__.py
│   │   │   ├── protocol.py        # 协议记录和导出
│   │   │   ├── quality.py         # 质量指标计算
│   │   │   └── export.py          # GeoJSON/YAML导出
│   │   ├── reproducibility/       # 可复现性框架
│   │   │   └── recorder.py        # 自动方法文档化
│   │   ├── visualization/         # 可视化工具
│   │   │   ├── maps.py            # 交互式地图（folium）
│   │   │   ├── analysis.py        # 覆盖分析
│   │   │   └── comparison.py      # 策略对比
│   │   └── utils/                 # 工具函数
│   │       ├── spatial.py         # 空间辅助函数
│   │       └── validation.py      # 输入验证
│   ├── api/                       # 预留API层
│   └── core/                      # 预留核心逻辑
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   ├── conftest.py                # pytest配置和fixtures
│   ├── helper.py                  # 测试辅助函数
│   ├── data/                      # 测试数据
│   │   ├── aoi_hk_central.geojson # 香港中环区域
│   │   └── sample_points.geojson  # 示例采样点
│   ├── test_sampling.py           # 采样策略测试
│   ├── test_metadata.py           # 元数据管理测试
│   └── test_visualization.py      # 可视化测试
│
├── docs/                          # 文档
│   ├── en/                        # 英文文档
│   └── zh/                        # 中文文档
│
├── memory-bank/                   # ⚠️ AI开发记忆库
│   ├── game-design-document.md   # → 替换为 README.md + plan.md
│   ├── tech-stack.md             # ✅ 技术栈说明
│   ├── implementation-plan.md    # ✅ 实施计划
│   ├── progress.md               # ✅ 开发进度
│   └── architecture.md           # ✅ 本文件
│
├── config/                        # 配置文件
│   └── config.yaml                # Hydra配置
│
├── scripts/                       # 工具脚本
│   └── configure_project.py       # 项目配置脚本
│
├── examples/                      # 示例代码（Jupyter notebooks）
│   └── tutorial.ipynb             # 教程
│
├── pyproject.toml                 # ⚠️ 项目配置和依赖
├── makefile                       # Make自动化
├── README.md                      # 英文说明
├── README.zh.md                   # 中文说明
├── plan.md                        # 英文开发计划
└── plan.zh.md                     # 中文开发计划
```

## 核心模块说明

### 1. sampling/ - 采样策略模块

**职责**: 实现各种空间采样算法

**关键类**:
- `SamplingStrategy` (base.py) - 抽象基类，定义采样接口
- `SamplingConfig` (base.py) - 采样配置数据类
- `GridSampling` (grid.py) - 规则网格采样
- `RoadNetworkSampling` (road_network.py) - 路网采样

**数据流**:
```
输入: AOI (Polygon) + Config
  ↓
采样策略.generate()
  ↓
输出: 采样点 (GeoDataFrame)
```

**依赖关系**:
- 依赖: geopandas, shapely, numpy
- 被依赖: metadata, visualization

---

### 2. metadata/ - 元数据管理模块

**职责**: 记录、管理和导出采样元数据

**关键类**:
- `MetadataManager` (protocol.py) - 协议管理器
- `QualityMetrics` (quality.py) - 质量指标计算
- `Exporter` (export.py) - 数据导出器

**数据流**:
```
采样点 GeoDataFrame
  ↓
MetadataManager.record_protocol()
  ↓
元数据字典 + YAML文件
```

**依赖关系**:
- 依赖: sampling, pyyaml, datetime
- 被依赖: cli, visualization

---

### 3. visualization/ - 可视化模块

**职责**: 创建采样结果的地图和图表

**关键类**:
- `SamplingVisualizer` (maps.py) - 交互式地图
- `CoverageAnalyzer` (analysis.py) - 覆盖分析
- `StrategyComparator` (comparison.py) - 策略对比

**数据流**:
```
采样点 GeoDataFrame
  ↓
SamplingVisualizer.plot_points()
  ↓
交互式地图 (HTML/图像)
```

**依赖关系**:
- 依赖: sampling, metadata, folium, matplotlib
- 被依赖: cli

---

### 4. reproducibility/ - 可复现性框架

**职责**: 确保研究的可复现性

**关键类**:
- `ProtocolRecorder` (recorder.py) - 自动记录研究过程

**功能**:
- 记录所有参数和版本信息
- 生成方法学描述
- 验证可复现性

---

### 5. utils/ - 工具模块

**职责**: 提供通用辅助函数

**模块**:
- `spatial.py` - 空间计算辅助函数
- `validation.py` - 输入验证函数

---

## 关键文件说明

### ⚠️ 必读文件（AI开发前必须完整阅读）

1. **pyproject.toml** - 项目依赖和配置
   - 核心依赖：geopandas, osmnx, shapely等
   - 开发依赖：pytest, black, flake8等
   - 项目元数据：名称、版本、作者

2. **src/ssp/sampling/base.py** - 核心架构
   - `SamplingStrategy` 抽象基类
   - `SamplingConfig` 数据类
   - 定义所有采样策略的接口

3. **memory-bank/implementation-plan.md** - 开发路线图
   - 详细的分步实施计划
   - 每步的验证方法

4. **memory-bank/tech-stack.md** - 技术栈说明
   - 为什么选择这些技术
   - 架构原则

5. **plan.md / plan.zh.md** - 项目设计愿景
   - 核心问题定义
   - 实现愿景
   - 用户接口

### 配置文件

- **makefile** - 自动化命令快捷方式
- **tox.ini** - 多Python版本测试配置
- **.gitignore** - Git忽略规则

---

## 数据结构

### 采样点 GeoDataFrame 格式

```python
# 必需列
columns = {
    'geometry': Point,           # 采样点几何
    'sample_id': str,            # 唯一标识
    'strategy': str,             # 采样策略名称
    'spacing_m': float,          # 采样间距（米）
    'timestamp': str,            # 生成时间
}

# 可选列（根据策略）
grid_columns = {
    'grid_x': int,               # 网格X坐标索引
    'grid_y': int,               # 网格Y坐标索引
}

road_columns = {
    'edge_id': str,              # 路网边ID
    'distance_along_edge': float,# 沿边的距离
}
```

### 协议文件 YAML 格式

```yaml
sampling_protocol:
  version: str                   # 协议版本
  timestamp: str                 # ISO 8601时间戳
  authors: list                 # 作者列表

  aoi:
    description: str             # 区域描述
    bounds: list                # [minx, miny, maxx, maxy]
    crs: str                    # 坐标系

  strategy:
    name: str                   # 策略名称
    parameters: dict            # 策略参数
    seed: int                   # 随机种子

  quality_metrics:
    n_points: int               # 采样点数
    area_km2: float             # 覆盖面积
    density_pts_per_km2: float  # 采样密度

  reproducibility:
    ssp_version: str         # SpatialSamplingPro版本
    python_version: str         # Python版本
    dependencies: dict          # 关键依赖版本
```

---

## 扩展点

### 添加新的采样策略

1. 在 `src/ssp/sampling/` 创建新文件
2. 继承 `SamplingStrategy` 基类
3. 实现 `generate()` 方法
4. 在 `__init__.py` 中导出
5. 添加单元测试

### 添加新的可视化

1. 在 `src/ssp/visualization/` 创建新函数
2. 接受 GeoDataFrame 作为输入
3. 返回地图或图表对象
4. 在CLI中添加对应命令

### 添加新的导出格式

1. 在 `src/ssp/metadata/export.py` 添加函数
2. 实现 `to_<format>()` 方法
3. 处理格式特定的元数据
4. 更新单元测试

---

## 性能考虑

### 预期规模
- 采样点数：< 100,000
- AOI面积：< 1000 km²
- 运行时间：< 5分钟

### 优化策略
- 使用numpy向量化操作
- 缓存OSM路网数据
- 分批处理大规模数据
- 使用tqdm显示进度

---

## 测试策略

### 单元测试
- 每个模块都有对应测试文件
- 使用pytest fixtures创建测试数据
- Mock外部API（OSM）

### 集成测试
- 测试完整的采样流程
- 测试CLI命令
- 测试数据导出和导入

### 覆盖率目标
- 最低要求：70%
- 推荐目标：80%
- 核心模块：90%

---

## 依赖关系图

```
┌─────────────┐
│   CLI       │
│  (cli.py)   │
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
┌──────┐  ┌─────────┐
│sampling│ │metadata │
└───┬──┘  └────┬────┘
    │          │
    └───┬──────┘
        ▼
  ┌─────────┐
  │visualization│
  └─────────┘
```

---

## 版本控制策略

### 分支模型
- `main` - 稳定版本
- `develop` - 开发分支
- `feature/*` - 功能分支
- `fix/*` - 修复分支

### Commit规范
```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat` - 新功能
- `fix` - Bug修复
- `test` - 测试
- `docs` - 文档
- `refactor` - 重构
- `chore` - 构建/工具

---

## 更新日志

每次重大变更后更新此文件，记录：
- 新增模块
- 架构调整
- 依赖变化
- 重要设计决策
