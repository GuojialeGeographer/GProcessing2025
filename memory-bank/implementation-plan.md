# SVIPro 实施计划（Implementation Plan）

**原则**: 小步快跑，每步必测

---

## 第一阶段：MVP（最小可行产品）

### 步骤 1.1：完善基础采样架构
**目标**: 创建可扩展的采样策略基类

**任务**:
- [ ] 完善 `src/svipro/sampling/base.py`
  - 添加完整的类型提示
  - 实现所有抽象方法
  - 添加详细的docstring
  - 实现配置验证

**验证**:
- 编写单元测试 `tests/test_sampling_base.py`
- 测试能否创建SamplingStrategy的子类
- 测试配置对象（SamplingConfig）的序列化

**不包含代码**: "在base.py中创建一个抽象基类SamplingStrategy，包含generate()方法，接受Polygon参数，返回GeoDataFrame。同时创建SamplingConfig数据类，包含spacing、crs、seed等字段。"

---

### 步骤 1.2：实现网格采样
**目标**: 实现规则网格采样算法

**任务**:
- [ ] 完善 `src/svipro/sampling/grid.py`
  - 实现2D网格生成算法
  - 处理边界内点过滤
  - 添加坐标系转换支持
  - 实现可复现性（seed-based）

**验证**:
- 编写单元测试 `tests/test_grid_sampling.py`
- 测试给定边界和spacing，生成的点数正确
- 测试相同seed产生相同结果
- 测试不同spacing产生不同结果
- 测试边界过滤正确性

**不包含代码**: "在grid.py中实现GridSampling类，继承自SamplingStrategy。generate()方法应：1)获取边界bbox；2)按spacing创建x和y坐标数组；3)生成所有网格点；4)过滤出边界内的点；5)返回带元数据的GeoDataFrame。使用numpy进行网格生成，确保使用seed参数控制随机性。"

---

### 步骤 1.3：实现GeoJSON导出
**目标**: 导出采样点为标准GeoJSON格式

**任务**:
- [ ] 在base.py中实现`to_geojson()`方法
  - 使用geopandas的to_file()方法
  - 添加元数据到FeatureCollection
  - 验证输出格式

**验证**:
- 测试生成的GeoJSON可用QGIS/GeoPandas打开
- 测试元数据正确保存
- 测试坐标系正确（CRS）

**不包含代码**: "在SamplingStrategy类中添加to_geojson(filepath)方法，使用geopandas的to_file()方法导出GeoJSON。确保在properties中包含strategy、spacing、timestamp等元数据字段。"

---

### 步骤 1.4：创建命令行接口（基础版）
**目标**: 提供简单的CLI进行网格采样

**任务**:
- [ ] 创建 `src/svipro/cli.py`
  - 使用click创建命令组
  - 实现`svipro sample grid`命令
  - 添加--spacing, --aoi, --output参数

**验证**:
- 测试CLI能正确调用采样函数
- 测试参数验证
- 测试文件输出

**不包含代码**: "使用click创建CLI模块。定义sample命令组，包含grid子命令。grid命令接受三个参数：--spacing（浮点数）、--aoi（GeoJSON文件路径）、--output（输出路径）。读取AOI文件，创建GridSampling实例，调用generate()，导出到output。"

---

## 第二阶段：核心功能

### 步骤 2.1：实现路网采样
**目标**: 基于OSM路网进行采样

**任务**:
- [ ] 创建 `src/svipro/sampling/road_network.py`
  - 使用osmnx获取路网数据
  - 沿道路边进行采样
  - 处理不同网络类型（drive, walk, bike）
  - 实现距离约束

**验证**:
- 测试能从OSM获取路网
- 测试采样点在道路上
- 测试不同network_type的结果
- 测试在无网络区域的错误处理

**不包含代码**: "创建RoadNetworkSampling类，使用osmnx的graph_from_place()或graph_from_bbox()获取路网。将边（edges）转换为GeoDataFrame，按spacing进行插值采样。支持network_type参数选择道路类型（drive/walk/bike）。处理OSM API超时和错误。"

---

### 步骤 2.2：实现元数据管理
**目标**: 记录和导出采样协议

**任务**:
- [ ] 创建 `src/svipro/metadata/protocol.py`
  - 实现MetadataManager类
  - 记录采样参数和版本信息
  - 导出YAML格式的协议文件

**验证**:
- 测试元数据完整记录
- 测试YAML导出格式正确
- 测试包含时间戳和版本信息

**不包含代码**: "创建MetadataManager类，包含record_protocol()方法，读取SamplingStrategy的配置并记录到字典。save()方法将协议导出为YAML文件，包含：version、timestamp、authors、AOI、strategy、quality_metrics等字段。"

---

### 步骤 2.3：实现质量指标计算
**目标**: 评估采样质量

**任务**:
- [ ] 在base.py中实现`calculate_coverage_metrics()`
  - 计算采样点数量
  - 计算覆盖面积
  - 计算采样密度
  - 计算平均间距

**验证**:
- 测试指标计算正确性
- 测试不同采样策略的指标差异
- 测试边界情况（空点集、单点）

**不包含代码**: "在SamplingStrategy类中添加calculate_coverage_metrics()方法，返回包含n_points、area_km2、density_pts_per_km2等字段的字典。使用shapely计算面积，使用GeoDataFrame的total_bounds计算覆盖范围。"

---

### 步骤 2.4：完善CLI（添加元数据和质量命令）
**目标**: 扩展CLI功能

**任务**:
- [ ] 在cli.py中添加新命令
  - `svipro protocol create` - 生成协议文件
  - `svipro protocol validate` - 验证协议
  - `svipro quality metrics` - 计算质量指标

**验证**:
- 测试所有CLI命令
- 测试参数验证
- 测试错误提示友好

**不包含代码**: "在CLI中添加protocol和quality命令组。protocol create接受采样点文件和配置文件，输出协议YAML。quality metrics接受采样点文件，打印质量指标。使用click的验证和错误处理机制。"

---

## 第三阶段：可视化

### 步骤 3.1：实现交互式地图
**目标**: 使用folium可视化采样点

**任务**:
- [ ] 创建 `src/svipro/visualization/maps.py`
  - 实现SamplingVisualizer类
  - 创建folium地图
  - 添加采样点标记
  - 添加AOI边界
  - 导出HTML文件

**验证**:
- 测试地图可在浏览器打开
- 测试点标记正确
- 测试边界显示正确
- 测试不同采样点的颜色区分

**不包含代码**: "创建SamplingVisualizer类，包含plot_points()方法。使用folium.Map创建地图，中心点为AOI的centroid。使用folium.GeoJson添加采样点和边界。支持不同策略使用不同颜色。保存为HTML文件。"

---

### 步骤 3.2：实现策略对比工具
**目标**: 可视化对比不同采样策略

**任务**:
- [ ] 创建 `src/svipro/visualization/comparison.py`
  - 实现compare_strategies()函数
  - 创建多子图地图
  - 添加图例和统计信息
  - 保存为图像或HTML

**验证**:
- 测试能同时显示多个策略
- 测试图例清晰
- 测试统计信息准确

**不包含代码**: "创建compare_strategies()函数，接受策略列表和AOI。为每个策略生成采样点，创建包含多个子图的folium地图或matplotlib图。添加颜色图例、点数、密度等统计信息。"

---

### 步骤 3.3：实现CLI可视化命令
**目标**: 添加CLI可视化接口

**任务**:
- [ ] 在cli.py中添加visualize命令
  - `svipro visualize points` - 生成交互式地图
  - `svipro visualize compare` - 对比策略

**验证**:
- 测试CLI生成可视化
- 测试输出文件可用

**不包含代码**: "添加visualize命令组，包含points和compare子命令。points命令接受GeoJSON文件，输出HTML地图。compare命令接受策略列表和AOI，输出对比图。"

---

## 第四阶段：测试与完善

### 步骤 4.1：编写完整单元测试
**目标**: 达到80%+测试覆盖率

**任务**:
- [ ] 为所有模块编写测试
- [ ] 使用pytest-cov检查覆盖率
- [ ] 添加边界情况测试
- [ ] 添加错误处理测试

**验证**:
- 运行`pytest --cov`查看覆盖率报告
- 确保所有核心函数有测试

**不包含代码**: "为每个模块创建test_*.py文件。使用pytest的fixture创建测试数据。使用mock模拟外部API（如OSM）。测试正常流程和异常情况。使用pytest-cov生成覆盖率报告，目标80%以上。"

---

### 步骤 4.2：性能优化
**目标**: 确保处理大规模数据时性能可接受

**任务**:
- [ ] 使用cProfile识别性能瓶颈
- [ ] 优化热点代码
- [ ] 添加进度条（tqdm）
- [ ] 实现分批处理

**验证**:
- 测试处理10万个点的性能
- 测试内存占用

**不包含代码**: "使用python -m cProfile分析代码性能。对采样生成循环进行优化，使用numpy向量化操作。对OSM下载添加缓存。对长时间操作添加tqdm进度条。对大数据集实现分批处理。"

---

### 步骤 4.3：文档完善
**目标**: 提供完整的用户文档

**任务**:
- [ ] 编写API文档（使用mkdocstrings）
- [ ] 创建Jupyter notebook教程
- [ ] 添加使用示例
- [ ] 添加常见问题解答

**验证**:
- 运行`mkdocs build`生成文档
- 测试所有示例可运行

**不包含代码**: "在docs/目录添加tutorial.md和examples.md。使用Jupyter创建示例notebook，展示：1)基础用法；2)不同采样策略；3)可视化；4)自定义策略。使用mkdocstrings自动生成API文档。"

---

### 步骤 4.4：案例研究
**目标**: 使用真实数据验证项目

**任务**:
- [ ] 选择真实城市区域（如香港中环）
- [ ] 生成采样点
- [ ] 生成协议和可视化
- [ ] 撰写案例分析文档

**验证**:
- 测试完整流程可运行
- 测试结果可复现

**不包含代码**: "选择香港中环作为案例区域，使用box()创建AOI。依次运行GridSampling和RoadNetworkSampling，生成GeoJSON和协议文件。创建可视化地图对比两种策略。撰写case-study.md记录过程和结果。"

---

## 通用规则

### 测试优先
- 每个功能必须先写测试
- 测试驱动开发（TDD）
- 测试文件命名：`test_<module>.py`

### 小步提交
- 每完成一个步骤就commit
- Commit message格式：`<type>: <description>`
- Types: feat, fix, test, docs, refactor

### 代码审查
- 每个里程碑进行代码审查
- 使用black格式化代码
- 使用flake8检查代码质量
- 使用mypy进行类型检查

### 文档同步
- 代码更新时同步更新文档
- 每个函数必须有docstring
- 复杂逻辑需要注释

---

## 里程碑检查点

### MVP完成标志
- [ ] 可以通过CLI生成网格采样点
- [ ] 采样点可导出为GeoJSON
- [ ] 有基础的单元测试

### 核心功能完成标志
- [ ] 支持路网采样
- [ ] 可以生成协议文件
- [ ] CLI功能完整
- [ ] 测试覆盖率>70%

### 可视化完成标志
- [ ] 可生成交互式地图
- [ ] 可对比不同策略
- [ ] 有完整的使用文档

### 项目完成标志
- [ ] 测试覆盖率>80%
- [ ] 有完整的案例研究
- [ ] 文档齐全
- [ ] 代码质量达标
