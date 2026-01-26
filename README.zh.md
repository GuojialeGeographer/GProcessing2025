# SpatialSamplingPro

**Spatial Sampling Design Framework**: 面向可复现城市研究的空间采样标准化框架

[English](README.md) | [中文](README.zh.md) | [开发计划](plan.zh.md)

---

## 🎯 项目愿景

SpatialSamplingPro 解决了城市研究中的一个关键方法学缺口：**缺乏标准化、透明和可复现的空间研究采样方法学**。

### 核心问题

当前的空间研究存在以下问题：
- ❌ 随意的采样间隔，缺乏科学依据
- ❌ 空间覆盖不完整或数据冗余收集
- ❌ 黑箱式方法学，无法复现
- ❌ 无法跨不同区域进行比较研究

### 我们的解决方案

一个**科学、可复现、有完整文档**的空间采样设计框架，提供：
- ✅ 生成各种应用的标准化采样协议
- ✅ 提供多种基于科学的采样策略
- ✅ 确保完全的方法学透明度
- ✅ 实现可复现性（相同AOI + 相同参数 = 完全相同的结果）
- ✅ 支持多元研究领域：城市绿地、交通、环境研究、人口研究等

---

## 👥 作者

- **Jiale Guo** - [jiale.guo@mail.polimi.it](mailto:jiale.guo@mail.polimi.it)
- **Mingfeng Tang** - [mingfeng.tang@mail.polimi.it](mailto:mingfeng.tang@mail.polimi.it)

米兰理工大学地理信息工程专业研究生

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/GuojialeGeographer/GProcessing2025.git
cd GProcessing2025

# 安装依赖（推荐使用 uv）
uv sync --all-extras

# 或使用 poetry
poetry install
```

### 基础用法

```python
from ssp import GridSampling, MetadataManager
from shapely.geometry import box

# 定义研究区域（AOI）
aoi = box(114.15, 22.27, 114.18, 22.30)  # 香港中环

# 初始化采样策略
strategy = GridSampling(spacing=100, seed=42)

# 生成采样点
points = strategy.generate(aoi)

# 导出含元数据的结果
strategy.to_geojson("sampling_points.geojson")

# 生成协议文档
metadata = MetadataManager()
metadata.record_protocol(strategy)
metadata.save("sampling_protocol.yaml")

# 获取质量指标
metrics = strategy.calculate_coverage_metrics()
print(f"生成了 {metrics['n_points']} 个采样点")
print(f"密度: {metrics['density_pts_per_km2']} 点/平方公里")
```

### 命令行接口

```bash
# 基础网格采样
ssp sample grid --spacing 100 --aoi aoi.geojson --output points.geojson

# 路网采样
ssp sample road --spacing 50 --network drive --aoi hongkong.geojson --output hk_points.geojson

# 生成协议
ssp protocol create points.geojson --output protocol.yaml

# 可视化覆盖
ssp visualize points.geojson --output coverage_map.html
```

---

## 📋 功能特性

### ✅ 已实现功能（v0.1.0）

#### 采样策略
- **网格采样** - 基于规则网格，完全可复现
  - 均匀空间覆盖
  - 可配置间距和对齐方式
  - 基于种子的可复现性

- **路网采样** - 基于OSM，沿道路网络布点
  - OSMnx集成自动下载道路网络
  - 可配置网络类型（全部、步行、驾驶、自行车）
  - 道路类型过滤（19种OSM道路类型）

#### 质量评估
- **覆盖指标** - 点密度、面积、空间范围
- **路网指标** - 边数、节点数、总长度、连通性
- **质量可视化** - 交互式统计图表

#### 元数据与文档
- **协议生成** - 基于YAML的采样协议文件
- **元数据导出** - 带完整参数文档的GeoJSON
- **时间戳跟踪** - ISO 8601时间戳确保可复现性

#### 可视化工具
- **交互式地图** - 基于Folium的网络地图
- **统计图表** - Matplotlib/Seaborn统计可视化
- **策略对比** - 多策略对比图表
- **覆盖分析** - 空间分布热图、最近邻分析

#### 命令行接口
- **完整CLI** - 所有功能可通过命令行访问
- **彩色输出** - 用户友好的终端消息
- **错误处理** - 全面的验证和错误消息

### 🚧 计划功能（未来版本）

- 优化覆盖 - 贪心算法实现最大覆盖
- 分层随机 - 统计学有效的随机采样
- 高级空间策略 - 六边形采样、自适应密度采样
- 基于人口的采样 - 人口感知的采样设计

---

## 🔬 研究背景

本项目受城市研究中空间采样方法学的启发并进行了改进，包括：

> **Wang et al. (2025)** - Cross-platform complementarity: Assessing the data quality and availability of Google Street View and Baidu Street View. *Transactions in Urban Data, Science, and Technology*. DOI: 10.1177/27541231241311474

### 参考文献的核心贡献

1. **系统化采集方法** - 标准化的元数据发现
2. **元数据驱动方法** - 专注于文档化和可复现性
3. **质量评估框架** - 多维度评估

### 我们的创新

1. ✅ **更好的代码架构** - 模块化、可扩展设计
2. ✅ **可复现性保证** - 基于种子的确定性算法
3. ✅ **更广的应用范围** - 不仅限于街景，支持多种空间研究
4. ✅ **多种策略** - 网格、路网等更多采样方法
5. ✅ **用户友好接口** - Python API 和 CLI
6. ✅ **质量指标** - 内置覆盖和偏差分析

---

## 🛠️ 技术栈

**地理空间处理**：
- geopandas, shapely, pyproj, osmnx, networkx

**数据与数学**：
- numpy, pandas, scipy, scikit-learn

**可视化**：
- matplotlib, seaborn, folium

**工具库**：
- pyyaml, click

完整依赖列表见 [pyproject.toml](pyproject.toml)。

---

## 📊 项目状态

### 当前阶段：📝 规划中

- [x] 文献综述和缺口分析
- [x] 参考代码评估（SHAPClab框架）
- [x] 开发计划设计
- [ ] 核心实现（里程碑1）

### 开发路线图

#### 里程碑1：MVP（第1-2周）
- [ ] 基础采样架构
- [ ] 网格采样实现
- [ ] 基础GeoJSON导出
- [ ] 简单CLI接口

#### 里程碑2：核心功能（第3-4周）
- [ ] 路网采样（OSMnx）
- [ ] 元数据管理系统
- [ ] 质量指标计算
- [ ] 协议生成

#### 里程碑3：可视化（第5-6周）
- [ ] 交互式地图（folium）
- [ ] 覆盖分析图表
- [ ] 策略对比工具
- [ ] 文档和示例

#### 里程碑4：测试与完善（第7-8周）
- [ ] 所有模块的单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 案例研究验证

---

## 📚 文档

- [开发计划](plan.zh.md) - 详细的技术设计和实施路线图
- [API文档](docs/zh/) - （即将推出）
- [示例](examples/) - Jupyter notebook教程（即将推出）

---

## 🤝 贡献

欢迎贡献！请随时提交Pull Request。

---

## 📄 许可证

MIT许可证。参见 [LICENSE](LICENSE)。

---

## 🙏 致谢

- 参考实现：[SHAPClab_Quality-and-Availability-of-GSV-BSV](./SHAPClab_Quality-and-Availability-of-GSV-BSV/)
- 作为米兰理工大学**地理空间处理**课程项目开发
- 灵感来源于Wang et al. (2025)识别的方法学缺口

---

## 🔮 未来路线图

### 第四阶段：高级采样方法（未来）
- 高级空间采样算法
- 多目标优化
- 自适应采样策略

### 研究贡献
本项目旨在实现：
1. **方法学论文** - 关于空间采样标准化
2. **软件论文** - 发表于 *SoftwareX* 或 *JOSS*
3. **可复现的城市研究** - 使用标准化协议
4. **跨领域应用** - 环境科学、交通、城市规划、人口学等领域

---

**状态**：📝 规划中 - [查看开发计划](plan.zh.md) 了解详情
