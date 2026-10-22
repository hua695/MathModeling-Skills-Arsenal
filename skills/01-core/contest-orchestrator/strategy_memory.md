---
name: strategy-memory
description: 数学建模竞赛策略选择经验库。存"何时该保守/何时该创新/何时先跑baseline"，供 strategy-selector 检索。
---

# 策略记忆库（Strategy Memory）

> 用法：strategy-selector 输入（题型/数据规模/剩余时间/历史经验）→ 检索本库定策略（保守/创新/风险等级）。
> 复盘新比赛 → 策略选择经验按此 schema 追加。

---

## ST-001 数据少 → 保守，别上复杂模型

```yaml
scenario: 数据量不足（如训练集 < 1000）
strategy: 不要上深度学习/Transformer
reason: 小样本泛化风险高，复杂模型过拟合
recommend: 统计模型 + 解释性分析（回归/灰色关联/AHP）
signal: 训练样本量低于模型复杂度需求
```

## ST-002 架构卡阈值 → 换互补架构，别调参硬撑

```yaml
scenario: 多种子+多参数后结果停在固定阈值
strategy: 判定架构到极限 → 换互补架构（随机搜索 ↔ 确定性构造）
reason: 参数微调只在同一搜索空间打转，突破不了几何/结构下界
recommend: 文献先行找备选架构，小规模并行验证再全量
signal: 结果随调参不随迭代变化；文献显示别的表示方法能更紧
```

## ST-003 时间紧 → 保主问，保论文，砍次要

```yaml
scenario: 剩余时间不足（如 < 24h）
strategy: 冻结模型 → 进论文模式；主问解保证、次要问可略
reason: 摘要/论文规范/结果准确是拿分大头，多解一个次要问收益低
recommend: adaptive-scheduler 重排；baseline 保底不创新
signal: 预测总耗时 > 剩余时间 × 1.5
```

## ST-004 先跑 baseline 再谈创新

```yaml
scenario: 任意题开始建模
strategy: 永远 baseline-first（最简模型+sanity check）
reason: 证明"这题能解、数据能喂、目标能算"，再谈改进；防止 50h 调复杂模型
recommend: baseline ≥ 目标 80% 就停，否则才进 model-search
signal: 开始建模阶段
```

## ST-005 可解释性优先

```yaml
scenario: 评委重视逻辑的题（国赛大多数）
strategy: 优先可解释模型（数学规划/统计/经典方法），ML 黑盒慎用
reason: 评委看重"为什么用这个方法"，解释性强加分，黑盒扣印象分
recommend: model-selector 评分时"数学解释性 30%"压住黑盒
signal: 有明确优化/评价/决策结构，非纯模式识别
```

---

## ST-006 物理建模先验单位与材料参数

```yaml
scenario: 物理机理建模（光学/热/力学）
strategy: 动笔前先定单位制 + 查证材料参数
reason: 单位换算（μm×cm⁻¹ 差 1e-4）和折射率参数错误会造成系统性 30% 偏差
recommend: 单位换算先写在注释；材料参数查文献（SiC n≈2.55, Si n≈3.42）
signal: 涉及长度×波数/频率的公式
avoid: 直接套公式；凭感觉设物理常数
```

## ST-007 反演/频谱问题多方法互证

```yaml
scenario: 从频谱/信号反演物理参数（厚度/频率/成分）
strategy: ≥3 种独立算法交叉验证 + 两个条件互证
reason: 单方法选错峰/基线偏差会产生假结果，互证才可靠
recommend: FFT + 寻峰 + 拟合 + 相位法；不同实验条件验证
signal: 反演类问题
avoid: 单方法出结论
```

## ST-008 物理数据先选频段避开吸收带

```yaml
scenario: 光学/光谱数据处理
strategy: 分析前先识别并避开材料吸收带（如 SiC reststrahlen 800-1000 cm⁻¹）
reason: 吸收带内 n 为复数，折射率模型失效，污染拟合
recommend: 画全谱看结构，选透明区段（1500-4000）
signal: 光谱在特定波段骤变/强吸收
avoid: 全谱无脑拟合
```

---

## ST-9

```yaml
scenario: 紧轮廓
strategy: 确定性构造判可行性
reason: 随机可行率≈0
recommend: skyline+SA
strategy_id: ST-9
```

---

## ST-10

```yaml
strategy_id: ST-10
scenario: 问题带硬约束（固定轮廓、固定面积、尺寸限制）且随机初始化可行率极低时
strategy: 两阶段级联：先解无约束可行解，再在可行域内优化目标
reason: 把'找可行'和'优化目标'解耦，可行率从≈0%提升到100%，且目标优化更专注
recommend: 先跑无约束/松约束版本拿到可行解（问题一），把该解作为带约束问题（问题二/三）的 init_root；在可行域内只优化目标函数，不再为'可行'挣扎
risk: 可行解可能不是全局最优起点；可行域内局部最优仍可能较差。缓解：多 seed 取多个可行起点择优
example: Q2 用 Q1 解出的 B*-Tree 作 init_root
```

---

## ST-11

```yaml
strategy_id: ST-11
scenario: 当前搜索器在某约束下卡死（找不到可行解），增加迭代/调权重都无效时
strategy: 换搜索空间而非硬调参数：把'搜索布局'变成'搜索顺序
reason: 绕开能力瓶颈，n300 γ* 从 0.1322 降到 0.0873（降34%）
recommend: 识别真正的瓶颈是'搜索器能力'而非'目标函数'；换一种表示使可行性由构造保证（如天际线底置打包按顺序放置天然不重叠不越界），把搜索空间从'布局坐标'换成'放置顺序+旋转
risk: 新搜索空间可能牺牲目标最优性；需用压缩/精修后处理补足。缓解：加压紧和坐标级精修
example: Q3 天际线底置打包 + 序列/朝向SA + compact_layout
```

---

## ST-12

```yaml
strategy_id: ST-12
scenario: 随机搜索算法交付时，且论文报告最优值
strategy: 多 seed 取最优 + 复现口径明确（以结果文件种子为准）
reason: 论文数字有据可查，评委复现口径清晰，降低'结果不符'判罚风险
recommend: 跑多个随机种子取最优；把'产生该最优的 seed'记录到结果文件；种子记录明确写'以结果文件为准'；配独立验证脚本证明定稿布局与论文一致
risk: 多 seed 增加墙钟；不同机器随机性一致（Python random 固定 seed 可复现）
example: SEEDS=3(42/43/44) 择优 + 结果文件记最优 seed
```

---

## ST-13

```yaml
strategy_id: ST-13
scenario: 所有使用 AI 辅助的竞赛，交付支撑材料时
strategy: 支撑材料合规三件套：AI声明 + 清理 + 结果复现说明
reason: 满足 AI 章程第13/17条，避免'与论文不符'取消评奖资格
recommend: ①所有 .py 头加'本程序及代码是在AI工具辅助下完成的+工具名/版本/公司/日期'；②只打包最终交付代码+定稿数据+图+运行记录，删 __pycache__/探索脚本/存档/附录；③README 加'论文结果以定稿CSV为准，求解器为算法实现，多种子取最优
risk: 过度清理可能漏掉支撑论文的必要文件；需按规范清单核对
example: 65文件干净交付包 + 附录C文件清单
```

---

## ST-14

```yaml
strategy_id: ST-14
scenario: 代码含下标字符(S₀)、✓ 等非 GBK 字符，且会在 Windows 中文控制台运行
strategy: Windows 环境统一 stdout UTF-8 重定向
reason: 避免 UnicodeEncodeError 崩溃，评委能直接运行
recommend: 脚本头部加 sys.stdout.reconfigure(encoding='utf-8') 或 TextIOWrapper 重定向；交付前在 Windows 实测跑一遍
risk: 无
example: q4_solve.py 等 print 含 S₀/✓ 的脚本
```


















































---

## ST-15（公开经验库·公开）

```yaml
strategy_id: ST-15
scenario: 定日镜尺寸及安装高度必须统一
strategy: 固定布局后单独优化尺寸参数，用三分查找降维
reason: 减少决策变量，降低解空间维度
recommend: 适用于约束较强的子问题
source: 定日镜场优化设计模型——CUMCM 2023 A题国一论文(凌国明,中山大学)|https://blog.csdn.net/weixin_62127011/article/details/149843974|2023
confidence: 高
```

---

## ST-16（公开经验库·公开）

```yaml
strategy_id: ST-16
scenario: 各定日镜尺寸及安装高度可变
strategy: 在统一尺寸最优解基础上，用蒙特卡洛微调各排高度
reason: 在已获得的较优解邻域内进一步搜索
recommend: 适用于解空间极大但需快速求解的场景
source: 定日镜场优化设计模型——CUMCM 2023 A题国一论文(凌国明,中山大学)|https://blog.csdn.net/weixin_62127011/article/details/149843974|2023
confidence: 高
```

---

## ST-17（公开经验库·公开）

```yaml
strategy_id: ST-17
scenario: 需要精确验证光学效率
strategy: 使用SOLTRACE或HFLCAL进行射线追踪验证
reason: 蒙特卡洛结果需要第三方工具交叉验证
recommend: 工业级光热电站设计必备步骤
source: 定日镜场优化设计模型——CUMCM 2023 A题国一论文(凌国明,中山大学)|https://blog.csdn.net/weixin_62127011/article/details/149843974|2023
confidence: 高
```

---

## ST-18（公开经验库·公开）

```yaml
strategy_id: ST-18
scenario: 天气完全已知且单玩家
strategy: 动态规划逆向推导，优先确定关键区域物资分配
reason: 确定性多阶段决策问题，动态规划可保证最优性
recommend: 适用于问题一、问题三(5)
source: 穿越沙漠游戏最佳策略模型的研究与构建——CUMCM 2020 B题国一论文|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## ST-19（公开经验库·公开）

```yaml
strategy_id: ST-19
scenario: 天气未知且单玩家
strategy: 基于历史天气估算概率，用蒙特卡洛模拟期望收益
reason: 随机环境下需用期望值代替确定值
recommend: 适用于问题二、问题四
source: 穿越沙漠游戏最佳策略模型的研究与构建——CUMCM 2020 B题国一论文|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## ST-20（公开经验库·公开）

```yaml
strategy_id: ST-20
scenario: 多玩家竞争且天气已知
strategy: 纳什均衡博弈分析，寻找混合策略
reason: 多玩家决策相互影响，需考虑对手反应
recommend: 适用于问题三(6)，注意合作与竞争的平衡
source: 穿越沙漠游戏最佳策略模型的研究与构建——CUMCM 2020 B题国一论文|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## ST-21（公开经验库·公开）

```yaml
strategy_id: ST-21
scenario: 工艺参数与结构变量关系明确且线性
strategy: 多元线性回归+方差分析
reason: 简单模型可解释性强，适合线性关系
recommend: 数据量小且关系简单时优先使用
source: 插层熔喷非织造材料性能的分析与研究——2022华数杯C题获奖论文|https://blog.csdn.net/qq_63438888/article/details/126426589|2022
confidence: 高
```

---

## ST-22（公开经验库·公开）

```yaml
strategy_id: ST-22
scenario: 工艺参数与结构变量关系复杂非线性
strategy: BP神经网络或支持向量机
reason: 非线性模型拟合能力强
recommend: 数据量足够且关系复杂时选用，注意避免过拟合
source: 插层熔喷非织造材料性能的分析与研究——2022华数杯C题获奖论文|https://blog.csdn.net/qq_63438888/article/details/126426589|2022
confidence: 高
```

---

## ST-23（公开经验库·公开）

```yaml
strategy_id: ST-23
scenario: 需要同时优化多个相互冲突的性能指标
strategy: 多目标规划转化为单目标(加权法或ε-约束法)
reason: 获得Pareto最优解集，便于决策者权衡
recommend: 工业产品设计中常用策略
source: 插层熔喷非织造材料性能的分析与研究——2022华数杯C题获奖论文|https://blog.csdn.net/qq_63438888/article/details/126426589|2022
confidence: 高
```

---

## ST-24（公开经验库·公开）

```yaml
strategy_id: ST-24
scenario: 市场趋势明显且历史模式稳定
strategy: LSTM预测+趋势跟踪策略
reason: 趋势性市场中动量策略有效
recommend: 适用于黄金等具有长期趋势的品种
source: All That Glitters Is Not Gold: Trading Strategies——MCM 2022 C题O奖论文(北京理工大学)|https://xgb.bit.edu.cn/xgdt/rdxw/b7fad809dbfa46da8a3306a273e300fa.htm|2022
confidence: 高
```

---

## ST-25（公开经验库·公开）

```yaml
strategy_id: ST-25
scenario: 市场波动剧烈且不确定性高
strategy: 降低仓位、增加现金比例、设置止损
reason: 风险控制优先于收益最大化
recommend: 适用于比特币等高波动品种
source: All That Glitters Is Not Gold: Trading Strategies——MCM 2022 C题O奖论文(北京理工大学)|https://xgb.bit.edu.cn/xgdt/rdxw/b7fad809dbfa46da8a3306a273e300fa.htm|2022
confidence: 高
```

---

## ST-26（公开经验库·公开）

```yaml
strategy_id: ST-26
scenario: 需要平衡收益与风险
strategy: 多目标优化+风险调整收益指标
reason: 获得风险收益比最优的投资组合
recommend: 适用于长期稳健型投资者
source: All That Glitters Is Not Gold: Trading Strategies——MCM 2022 C题O奖论文(北京理工大学)|https://xgb.bit.edu.cn/xgdt/rdxw/b7fad809dbfa46da8a3306a273e300fa.htm|2022
confidence: 高
```

---

## ST-27（公开经验库·公开）

```yaml
strategy_id: ST-27
scenario: 天体目标位于天顶方向(对称轴与基准球面垂直)
strategy: 利用旋转对称性，将问题简化为二维截面分析
reason: 对称情况下三维问题可解析降维
recommend: 适用于FAST观测天顶附近目标时的快速估算
source: FAST主动反射面的形状调节——CUMCM 2021 A题国一论文(武汉大学肖宇曦/李逍迪/刘禹希团队)|https://m.cyol.com/gb/articles/2021-11/25/content_dw3zxI05e.html|2021
confidence: 高
```

---

## ST-28（公开经验库·公开）

```yaml
strategy_id: ST-28
scenario: 天体目标位于任意方向
strategy: 建立完整的三维理想抛物面模型，再用多目标规划求解
reason: 非对称情况下需完整三维建模
recommend: 适用于一般观测方向的精确调节
source: FAST主动反射面的形状调节——CUMCM 2021 A题国一论文(武汉大学肖宇曦/李逍迪/刘禹希团队)|https://m.cyol.com/gb/articles/2021-11/25/content_dw3zxI05e.html|2021
confidence: 高
```

---

## ST-29（公开经验库·公开）

```yaml
strategy_id: ST-29
scenario: 需要快速估算调节量
strategy: 基于基准球面与理想抛物面的几何关系，推导近似公式
reason: 工程现场需要快速响应
recommend: 适用于实时控制系统的初步调节
source: FAST主动反射面的形状调节——CUMCM 2021 A题国一论文(武汉大学肖宇曦/李逍迪/刘禹希团队)|https://m.cyol.com/gb/articles/2021-11/25/content_dw3zxI05e.html|2021
confidence: 高
```

---

## ST-30（公开经验库·公开）

```yaml
strategy_id: ST-30
scenario: 农业种植长期规划面临多重不确定性（价格、气候、成本）
strategy: 采用情景优化+鲁棒优化的分层方法：先用情景生成刻画不确定性，再用鲁棒目标保证最差情况可接受
reason: 纯期望收益最大化在极端情景下可能亏损严重；农业决策者通常风险厌恶
recommend: 竞赛中可用3-5个代表性情景（乐观/基准/悲观）代替完整随机规划，降低求解难度同时保留稳健性
source: 2024年高教社杯全国大学生数学建模竞赛C题：农作物的种植策略|https://cloud.tencent.com/developer/article/2486153|2024
confidence: 高
```

---

## ST-31（公开经验库·公开）

```yaml
strategy_id: ST-31
scenario: 物理机理模型与数值优化结合
strategy: 先建机理方程明确变量关系，对线性退化情形求解析解标定数值方法，再对非线性情形用数值积分+网格搜索
reason: 解析解可验证数值代码正确性（退化一致性检验），避免数值误差导致优化结果不可信
recommend: 对含参数优化的物理系统，务必设计退化检验（如将α=1代入非线性阻尼验证是否退化为线性结果）
source: 2022年高教社杯全国大学生数学建模竞赛A题：波浪能最大输出功率设计|https://blog.csdn.net/weixin_47315122/article/details/163511311|2022
confidence: 高
```

---

## ST-32（公开经验库·公开）

```yaml
strategy_id: ST-32
scenario: 大规模供应商评价与选择（400+供应商）
strategy: 先通过综合评价筛选关键供应商缩小决策空间，再对精选供应商构建优化模型
reason: 直接对402家供应商做整数规划变量过多，求解困难；分层筛选降低复杂度
recommend: 熵权-TOPSIS快速排序取前50-100家，再以此为基础构建MILP，兼顾效率与精度
source: 2021年高教社杯全国大学生数学建模竞赛C题：生产企业原材料的订购与运输|https://blog.csdn.net/peiye500238/article/details/150857323|2021
confidence: 高
```

---

## ST-33（公开经验库·公开）

```yaml
strategy_id: ST-33
scenario: 纯方位无源定位（仅有角度测量）
strategy: 几何定理优先，数值优化辅助：先用圆周角/三角关系建立解析框架，再用最小二乘处理冗余测量与噪声
reason: 纯方位问题几何约束强，解析方法可保证解的存在性与唯一性；数值优化用于处理超定方程组提高精度
recommend: 对10架以内小规模编队，圆周角定理+迭代修正足够；对大规模集群需考虑图论连通性与分布式算法
source: 2022年高教社杯全国大学生数学建模竞赛B题：无人机遂行编队飞行中的纯方位无源定位|https://blog.csdn.net/weixin_43970743/article/details/161582620|2022
confidence: 高
```

---

## ST-34（公开经验库·公开）

```yaml
strategy_id: ST-34
scenario: 考古文物成分数据：高维、小样本、有缺失、含先验分类
strategy: 分层建模：先验分类→子类内聚类→监督分类验证→相关分析解释
reason: 先验分类（高钾/铅钡）是考古学共识，不应被无监督方法推翻；分层处理尊重领域知识，同时挖掘内部亚结构
recommend: 对类似有先验标签的小样本分类问题，优先用随机森林/判别分析做监督学习，聚类仅用于探索子类结构
source: 2022年高教社杯全国大学生数学建模竞赛C题：古代玻璃制品的成分分析与鉴别|https://developer.aliyun.com/article/1578548|2022
confidence: 高
```

---

## ST-35（公开经验库·公开）

```yaml
strategy_id: ST-35
scenario: 多刚体链式结构在曲线路径上的运动仿真
strategy: 几何约束递推+刚体碰撞检测+分段参数化路径
reason: 链式结构各节位置强耦合，必须从龙头开始逐节递推；碰撞检测需考虑实际几何形状而非仅质点距离
recommend: 对类似盘龙、机械臂、蛇形机器人等问题，优先建立基于弧长约束的几何递推模型，碰撞检测采用分离轴定理或包围盒层次结构
source: 2024年高教社杯全国大学生数学建模竞赛A题：'板凳龙'闹元宵|https://blog.csdn.net/weixin_43292788/article/details/145744176|2024
confidence: 高
```

---

## ST-36（公开经验库·公开）

```yaml
strategy_id: ST-36
scenario: 大规模定日镜场光学效率仿真
strategy: 蒙特卡洛光线追踪+GPU并行加速+分时段聚合
reason: 镜场规模可达数千面，单时刻光线追踪计算量大；GPU可将单面镜计算时间从6200ms降至1ms（提升三个数量级）
recommend: 竞赛场景下若计算资源有限，可采用关键时段采样（如春分、夏至、冬至的代表性时刻）代替全年逐时仿真，降低计算量同时保留主要特征
source: 2023年高教社杯全国大学生数学建模竞赛A题：定日镜场的优化设计|https://pdf.hanspub.org/csa_1544012.pdf|2023
confidence: 高
```

---

## ST-37（公开经验库·公开）

```yaml
strategy_id: ST-37
scenario: 多阶段生产质量决策（检测-装配-拆解-调换）
strategy: 决策树全局优化+贝叶斯风险更新
reason: 各阶段决策相互影响（如零配件不检测会导致成品次品率升高），必须全局优化；抽样不确定性用贝叶斯修正
recommend: 对两零配件-单成品的基础场景用决策树枚举；扩展到多零配件时用动态规划降维；始终用假设检验理论设计抽样方案
source: 2024年高教社杯全国大学生数学建模竞赛B题：生产过程中的决策问题|https://blog.csdn.net/weixin_43970743/article/details/151194019|2024
confidence: 高
```

---

## ST-38（公开经验库·公开）

```yaml
strategy_id: ST-38
scenario: 三维空间中的武器命中概率优化
strategy: 概率积分解析化+数值求解+布局网格搜索
reason: 命中概率可分解为独立坐标方向的积分，解析分解降低维度；数值积分保证精度；网格搜索保证全局最优
recommend: 对单武器先建立解析概率表达式，用数值积分（如MATLAB integral2/integral3）求解；对多武器布局，先用粗网格定位最优区域，再用细网格精确搜索
source: 2024年高教社杯全国大学生数学建模竞赛D题：反潜航空深弹命中概率问题|https://cjournal.hep.com.cn/2095-3070/CN/10.19943/j.2095-3070.jmmia.2025.02.07|2024
confidence: 高
```

---

## ST-39（公开经验库·公开）

```yaml
strategy_id: ST-39
scenario: 气候风险下的跨学科决策（保险+房地产+文化遗产）
strategy: 模块化子模型+统一灵敏度分析框架
reason: 三个子问题领域差异大（金融、工程、人文），统一模型难以兼顾；模块化设计保持各领域专业性，统一灵敏度分析确保整体一致性
recommend: 对复合型赛题，建议将问题分解为独立子模型（如MDI/MSS/MCB），各子模型选用该领域最适合的方法，最后通过灵敏度分析和情景分析整合结论
source: 2024年MCM/ICM美赛O奖论文：极端天气保险决策模型(ICM-E题)|https://mcmicm.org.cn/news/1070.html|2024
confidence: 高
```

---

## ST-40（公开经验库·公开）

```yaml
strategy_id: ST-40
scenario: 海底地形起伏海域的多波束测线设计
strategy: 先分区拟合坡度→再按区设计平行测线→最后全局校验覆盖率
reason: 分区将非线性地形局部线性化，使解析模型适用；全局校验确保子区域间无缝衔接
recommend: 对复杂地形优先采用基于单波束数据的分区坡度拟合，而非全局曲面拟合，降低计算复杂度同时满足工程精度
source: 2023年高教社杯全国大学生数学建模竞赛B题：多波束测线问题|https://www.ppmy.cn/news/1095872.html|2023
confidence: 高
```

---

## ST-41（公开经验库·公开）

```yaml
strategy_id: ST-41
scenario: 化工实验数据量少、变量间交互强、需同时建模与优化
strategy: 分层递进：相关分析→回归基线→响应面/神经网络非线性拟合→智能优化→实验设计验证
reason: 化工实验成本高、数据少，不能盲目上复杂模型；分层策略先用简单模型识别主效应，再逐步引入非线性与优化，最后用实验设计验证
recommend: 对类似催化反应优化问题，建议先用皮尔逊/聚类筛选关键因子，再用响应面法建立显式关系，最后用PSO/GA优化，避免直接用黑箱神经网络做全流程建模
source: 2021年高教社杯全国大学生数学建模竞赛B题：乙醇偶合制备C4烯烃|https://blog.csdn.net/weixin_43970743/article/details/161521614|2021
confidence: 高
```

---

## ST-42（公开经验库·公开）

```yaml
strategy_id: ST-42
scenario: 中小微企业信贷数据稀疏、标签少、需兼顾收益与风险
strategy: 特征工程+集成学习风险量化→多目标规划策略优化→情景分析动态调整
reason: 中小微企业经营波动大、数据质量参差，集成学习提高预测鲁棒性；多目标规划显式平衡银行收益与风险；聚类+情景分析应对突发事件
recommend: 对类似信用风险评估问题，建议先用XGBoost/LightGBM做基线，再用Soft Voting或Stacking提升稳定性；信贷策略务必用多目标规划而非单目标，避免过度追求收益忽视风险
source: 2020年高教社杯全国大学生数学建模竞赛C题：中小微企业的信贷决策|https://blog.csdn.net/2401_82505179/article/details/142721401|2020
confidence: 高
```

---

## ST-43（公开经验库·公开）

```yaml
strategy_id: ST-43
scenario: 生鲜零售的自动补货与定价（高损耗、短保质期、SKU多）
strategy: 分层优化：品类级需求预测与定价→单品级组合选择与补货量→损耗率修正
reason: 品类级聚合降低预测方差，单品级优化满足陈列与替代约束，损耗率修正保证实际可售量
recommend: 对高损耗生鲜商品，建议在补货模型中显式引入损耗率衰减函数，定价时采用动态成本加成而非固定加成率
source: 2023年高教社杯全国大学生数学建模竞赛C题：蔬菜类商品的自动定价与补货决策|https://bbs.pinggu.org/a-4081715.html|2023
confidence: 高
```

---

## ST-44（公开经验库·公开）

```yaml
strategy_id: ST-44
scenario: 工业生产中的在线切割优化（需秒级响应、多目标冲突、异常频繁）
strategy: 多目标规划定框架+序贯算法保实时性+分时段重规划降复杂度
reason: 多目标规划保证目标体系完整；序贯算法将复杂问题分解为优先级队列，快速求解；分时段处理避免全局重算
recommend: 对类似连铸切割、板材下料等在线优化问题，务必先分析时间约束，选择计算复杂度与问题规模匹配的算法，不能盲目追求全局最优而牺牲实时性
source: 2021年高教社杯全国大学生数学建模竞赛D题：连铸切割的在线优化|https://blog.csdn.net/gitblog_06632/article/details/143334963|2021
confidence: 高
```

---

## ST-45（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-45
scenario: 周期性时序数据预测
strategy: 先做时序可视化识别早晚高峰周期
reason: 依据波动幅度挑选适配预测模型
recommend: 平缓序列ARIMA；强周期序列LSTM
source: 2024高教社杯国赛E题交通流量管控优秀论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2024sxjmstjp/241127/1980970.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-46（公开经验库·公开）

```yaml
strategy_id: ST-46
scenario: 多因子金融时序预测
strategy: 先检验多重共线性再搭建预测模型
reason: 共线性会毁掉线性回归可信度
recommend: 高相关指标采用PCA或者因子分析降维
source: 光伏建筑一体化板块指数分析优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2021
confidence: 高
```

---

## ST-47（公开经验库·公开）

```yaml
strategy_id: ST-47
scenario: 场地空间布局优化
strategy: 先几何推导硬性边界，之后增加人为因素惩罚项
reason: 单纯数学最优方案落地可行性较差
recommend: 把实操短板转化成目标函数惩罚条件
source: 2026电工杯A题停车场规划优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2026
confidence: 高
```

---

## ST-48（公开经验库·公开）

```yaml
strategy_id: ST-48
scenario: 设备启停类资源调度
strategy: 使用0-1变量标记设备启停状态
reason: 启停只有开启、关闭两种状态
recommend: PuLP工具构建整数规划模型求解
source: 2025亚太杯D题电力系统机组组合论文|https://mbd.pub/o/bread/mbd-YZWZlplrZA==|2025
confidence: 高
```

---

## ST-49（公开经验库·公开）

```yaml
strategy_id: ST-49
scenario: 多属性主观适配评估
strategy: 区分客观指标、主观指标选用对应评价模型
reason: 两类指标的数据性质不一样
recommend: 客观指标TOPSIS；主观模糊指标模糊综合评价
source: 2020 HiMCM暑期岗位推荐O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2020
confidence: 中
```

---

## ST-50（公开经验库·公开）

```yaml
strategy_id: ST-50
scenario: 多孔复合材料传热计算
strategy: 宏观整体模型搭配最小重复微观单元
reason: 材料周期性结构决定微观结构参数
recommend: 有限差分法处理一维传热问题
source: 第四届华数杯A题织物导热优秀论文|https://blog.csdn.net/m0_52343631/article/details/140867886|2023
confidence: 高
```

---

## ST-51（公开经验库·公开）

```yaml
strategy_id: ST-51
scenario: 节点布设、通信组网类问题
strategy: 转化成连通图之后使用智能优化算法求解
reason: 需要规避节点之间互相干扰
recommend: 遗传算法、蚁群算法求解图布局问题
source: 2024研究生华为杯B题WLAN组网优秀论文|https://github.com/1931239281/MathModel/blob/master/README.md|2024
confidence: 中
```

---

## ST-52（公开经验库·公开）

```yaml
strategy_id: ST-52
scenario: 动力学连续状态预测
strategy: 建立常微分方程，分段区分工况再数值求解
reason: 设备开关状态改变动力学方程
recommend: RK-4四阶龙格库塔进行迭代计算
source: 2019国赛高压油管压力控制一等奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2019
confidence: 高
```

---

## ST-53（公开经验库·公开）

```yaml
strategy_id: ST-53
scenario: 网络商品口碑分级评估
strategy: 文本情感特征作为首要评估指标
reason: 星级评分容易被人为操控
recommend: NLP情感打分搭配客观销售指标综合评判
source: 2020 MCM-ICM网购平台O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2020
confidence: 中
```

---

## ST-54（公开经验库·公开）

```yaml
strategy_id: ST-54
scenario: 带有节假日扰动的短期时序预估
strategy: 拆分长期趋势、周期分量、假日扰动项
reason: 假期是垃圾产量的关键扰动源
recommend: Facebook-Prophet进行建模预测
source: 2022高教社杯国赛C题城市生活垃圾处置优秀论文|https://www.cumcm.edu.cn/works/excellent/2022/|2022
confidence: 高
```

---

## ST-55（公开经验库·公开）

```yaml
strategy_id: ST-55
scenario: 多因子环境参数预测任务
strategy: 先筛选显著影响因子之后再搭建回归模型
reason: 很多监测指标相关性很低
recommend: 随机森林，获取特征权重筛选变量
source: 2025电工杯B题河道水质预警一等奖论文|https://blog.csdn.net/mathmodelshare/article/details/153692147|2025
confidence: 高
```

---

## ST-56（公开经验库·公开）

```yaml
strategy_id: ST-56
scenario: 物流配送路径规划
strategy: 将时间窗口、载重作为硬性惩罚条件写入目标函数
reason: 超时配送会直接造成订单失效
recommend: 遗传算法或者蚁群算法求解VRPTW模型
source: 2024亚太杯C题生鲜冷链配送优化论文|https://mbd.pub/o/bread/Z5ebm52tZw==|2024
confidence: 高
```

---

## ST-57（公开经验库·公开）

```yaml
strategy_id: ST-57
scenario: 公共设施分时资源分配
strategy: 0-1整数规划定义占用状态，增设人性化偏好惩罚项
reason: 现实场景不能单纯追求资源利用率
recommend: PuLP编写整数规划代码求解
source: 第五届华数杯B题自习室调度优秀论文|https://blog.csdn.net/weixin_46189918/article/details/142268904|2024
confidence: 高
```

---

## ST-58（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-58
scenario: 多客观指标地区发展评估
strategy: 熵权法自动计算权重，TOPSIS计算贴近理想解距离
reason: 杜绝人工权重带来的主观偏向
recommend: 熵权TOPSIS作为首要评价模型
source: 2023高教社杯国赛E题乡村振兴评估一等奖论文|https://www.cumcm.edu.cn/works/excellent/2023/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-59（公开经验库·公开）

```yaml
strategy_id: ST-59
scenario: 刚体运动动力学仿真
strategy: 分阶段建立动力学微分方程，RK-4迭代求解
reason: 物体触碰边界之后受力条件会改变
recommend: 四阶龙格-库塔完成时序迭代计算
source: 2021 MCM物理方向O奖论文|https://github.com/liuyouyuan/mcm-icm-2021|2021
confidence: 中
```

---

## ST-60（公开经验库·公开）

```yaml
strategy_id: ST-60
scenario: 路网、交通网络寻路
strategy: 把换乘、等候损耗折算为边权重
reason: 通勤耗时不止路上行驶时间
recommend: 单源最短路选用Dijkstra；多起点选用Floyd
source: 2025研究生数学建模F题公共交通线路优化论文|https://github.com/MathematicalModelingClub/HuaweiCup2025|2025
confidence: 中
```

---

## ST-61（公开经验库·公开）

```yaml
strategy_id: ST-61
scenario: 周期性损耗设备寿命预估
strategy: 区分平稳老化阶段、加速损耗阶段进行时序建模
reason: 元器件老化速率并不是恒定数值
recommend: LSTM处理周期性监测时序数据
source: 2020 ICM电池寿命方向O奖论文|https://github.com/akashsara/mcm-icm2020|2020
confidence: 中
```

---

## ST-62（公开经验库·公开）

```yaml
strategy_id: ST-62
scenario: 灾害应急物资调配任务
strategy: 建立多目标规划平衡运费、配送时长
reason: 应急场景速度和成本都需要考量
recommend: 加权法或者帕累托解集处理多目标优化
source: 2022亚太杯D题救灾物资调度优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2022
confidence: 高
```

---

## ST-63（公开经验库·公开）

```yaml
strategy_id: ST-63
scenario: 人文、学业、实践多维度人员评估
strategy: AHP层次分析法确认指标权重之后开展综合评判
reason: 各项指标重要程度并不相等
recommend: AHP适合层级清晰的打分评价体系
source: 2026电工杯C题学生综合素质测评一等奖论文|https://blog.csdn.net/codeforfun666/article/details/154713205|2026
confidence: 高
```

---

## ST-64（公开经验库·公开）

```yaml
strategy_id: ST-64
scenario: 含离散约束的能源系统优化
strategy: 将非线性互斥约束通过大M法转化为线性约束
reason: 线性规划可利用成熟求解器保证全局最优
recommend: 使用CPLEX/Gurobi求解混合整数线性规划模型
source: 2024电工杯A题园区微电网风光储协调优化配置优秀论文|https://blog.csdn.net/2201_75535220/article/details/139207728|2024
confidence: 高
```

---

## ST-65（公开经验库·公开）

```yaml
strategy_id: ST-65
scenario: 非平稳时序预测
strategy: 先进行去噪与平稳性检验，再选择适配模型
reason: 不同平稳性的时序数据适配模型差异大
recommend: 非平稳序列优先选用LSTM或Transformer模型
source: 2019电工杯A题风电机组输出功率预测优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2019
confidence: 高
```

---

## ST-66（公开经验库·公开）

```yaml
strategy_id: ST-66
scenario: 多自由度机器人运动优化
strategy: 先建立正向运动学模型，再引入轨迹平滑约束进行优化
reason: 正向模型便于控制运动的连续性与能耗
recommend: 使用遗传算法或粒子群算法求解轨迹优化问题
source: 2025亚太杯人形机器人运动建模与能耗优化优秀论文|https://www.iesdouyin.com/share/video/7575096913709687203|2025
confidence: 中
```

---

## ST-67（公开经验库·公开）

```yaml
strategy_id: ST-67
scenario: 多分类不平衡数据评价
strategy: 先处理类别不平衡，再选用树类或集成学习模型
reason: 类别不平衡会导致模型偏向多数类
recommend: 使用SMOTE过采样+随机森林分类模型
source: 2023华数杯C题婴儿睡眠质量评价优秀论文|https://jishuzhan.net/article/1702235986626351106|2023
confidence: 高
```

---

## ST-68（公开经验库·公开）

```yaml
strategy_id: ST-68
scenario: 含非线性关系的配方优化
strategy: 先进行高精度非线性拟合，再选用智能优化算法求解
reason: 非线性拟合可提高模型精度，智能算法可保证全局最优
recommend: 使用多项式拟合+模拟退火算法求解
source: 2023华数杯B题不透明制品最优配色方案设计优秀论文|http://www.guyue12306.com/archives/14/|2023
confidence: 高
```

---

## ST-69（公开经验库·公开）

```yaml
strategy_id: ST-69
scenario: 周期性复合材料热传导预测
strategy: 先建立微观最小单元模型，再使用有限差分法求解
reason: 微观模型可更准确描述周期性结构的热传导过程
recommend: 使用有限差分法求解周期性复合材料的热传导问题
source: 2023华数杯A题织物热导率预测优秀论文|https://blog.csdn.net/m0_52343631/article/details/140867886|2023
confidence: 高
```

---

## ST-70（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-70
scenario: 企业生产过程中的决策优化
strategy: 采用智能算法优化的蒙特卡洛模拟模型
reason: 智能算法可提高模拟的效率和准确性
recommend: 使用蚁群算法与遗传算法优化的蒙特卡洛模拟模型
source: 2024高教社杯全国大学生数学建模竞赛B题优秀论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2024qgdxssxjmjslwzs_2024btlw/241104/1977943.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-71（公开经验库·公开）

```yaml
strategy_id: ST-71
scenario: 城市垃圾分类运输的路径优化与调度
strategy: 采用CVRP模型+改进型遗传算法
reason: CVRP模型可有效处理容量约束，改进型遗传算法可提升解的全局探索能力与局部最优性
recommend: 使用Clarke-Wright Savings启发式构造初始解，结合2-opt局部搜索和改进型遗传算法
source: 2025电工杯数学建模竞赛B题优秀论文|https://blog.csdn.net/qq_50593822/article/details/148189953|2025
confidence: 高
```

---

## ST-72（公开经验库·公开）

```yaml
strategy_id: ST-72
scenario: 绿电直连型电氢氨园区优化运行
strategy: 将非线性互斥约束通过大M法转化为线性约束
reason: 线性规划可利用成熟求解器保证全局最优
recommend: 使用CPLEX/Gurobi求解混合整数线性规划模型
source: 2026电工杯数学建模竞赛A题优秀论文|https://blog.csdn.net/maligebilaowang/article/details/161324818|2026
confidence: 高
```

---

## ST-73（公开经验库·公开）

```yaml
strategy_id: ST-73
scenario: 乡村振兴发展水平综合评价
strategy: 熵权法自动计算权重，TOPSIS计算贴近理想解距离
reason: 杜绝人工权重带来的主观偏向
recommend: 熵权TOPSIS作为首要评价模型
source: 我国乡村振兴发展水平综合评价研究|http://qks.cqu.edu.cn/cqdxskcn/article/abstract/20230108?st=search|2023
confidence: 高
```

---

## ST-74（公开经验库·公开）

```yaml
strategy_id: ST-74
scenario: 生鲜冷链配送路径优化
strategy: 采用多目标遗传算法+改进蚁群算法
reason: 多目标遗传算法可同时优化多个目标，改进蚁群算法可提升解的全局探索能力
recommend: 使用多目标遗传算法+改进蚁群算法求解生鲜冷链配送路径优化问题
source: 考虑碳排放和时间窗约束的冷链物流配送路径优化研究|https://www.hanspub.org/downLoad/page_download?filename=orf2024143_1131701725.pdf|2024
confidence: 高
```

---

## ST-75（公开经验库·公开）

```yaml
strategy_id: ST-75
scenario: 短时突变性时序预测
strategy: 结合时序模型与空间特征，引入注意力机制加权关键时段
reason: 短时数据存在强局部模式与突变，需同时捕捉时序与空间关联
recommend: TCN或Transformer模型，加入空间注意力模块
source: 2021高教社杯国赛A题城市轨道交通客流预测优秀论文|https://www.cumcm.edu.cn/works/excellent/2021/|2021
confidence: 高
```

---

## ST-76（公开经验库·公开）

```yaml
strategy_id: ST-76
scenario: 带后续操作约束的资源分配
strategy: 将后续操作成本转化为目标函数的惩罚项，使用智能算法求解
reason: 单纯当前最优会导致后续操作成本激增
recommend: 混合整数规划+改进蚁群算法
source: 2020亚太杯B题港口集装箱堆场优化优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2020
confidence: 高
```

---

## ST-77（公开经验库·公开）

```yaml
strategy_id: ST-77
scenario: 多指标综合评价
strategy: 先区分指标方向，再选用CRITIC法确权，最后用TOPSIS排序
reason: CRITIC法兼顾数据特征与指标重要性，避免权重偏差
recommend: CRITIC-TOPSIS模型
source: 2022国赛D题城市营商环境评价一等奖论文|https://www.cumcm.edu.cn/works/excellent/2022/|2022
confidence: 高
```

---

## ST-78（公开经验库·公开）

```yaml
strategy_id: ST-78
scenario: 复杂地形的无人机航线规划
strategy: 先分析地形坡度分布，再建立自适应航线间距模型
reason: 地形坡度直接影响测绘精度与能耗，需动态调整
recommend: 自适应航线规划模型
source: 2023美赛MCM无人机测绘O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2023
confidence: 中
```

---

## ST-79（公开经验库·公开）

```yaml
strategy_id: ST-79
scenario: 复杂环境的目标定位
strategy: 选用基于时间差的定位算法，引入环境误差修正项
reason: 时间差比信号强度更稳定，受环境干扰小
recommend: TDOA定位算法
source: 2024研究生数模B题地下管网泄漏定位优秀论文|https://github.com/1931239281/MathModel/blob/master/README.md|2024
confidence: 中
```

---

## ST-80（公开经验库·公开）

```yaml
strategy_id: ST-80
scenario: 周期性波动的价格预测
strategy: 先识别周期特征，再选用Prophet或混合模型
reason: 周期性波动是价格预测的关键特征，灰色预测无法适配
recommend: Prophet+XGBoost混合模型
source: 2025华数杯D题农产品价格预测优秀论文|https://blog.csdn.net/weixin_46189918/article/details/142268904|2025
confidence: 高
```

---

## ST-81（公开经验库·公开）

```yaml
strategy_id: ST-81
scenario: 带优先级约束的资源排程
strategy: 将优先级转化为硬约束，使用混合整数规划+遗传算法求解
reason: 优先级约束是硬约束，必须优先满足
recommend: 混合整数规划+遗传算法
source: 2023电工杯C题医院手术排程优秀论文|https://blog.csdn.net/mathmodelshare/article/details/153692147|2023
confidence: 高
```

---

## ST-82（公开经验库·公开）

```yaml
strategy_id: ST-82
scenario: 含主观模糊指标的评价
strategy: 先提取潜在因子，再用模糊综合评价处理主观指标
reason: 主观指标无法精确量化，需用模糊方法处理
recommend: 因子分析+模糊综合评价模型
source: 2022美赛ICM毕业生就业质量O奖论文|https://github.com/akashsara/mcm-icm2022|2022
confidence: 中
```

---

## ST-83（公开经验库·公开）

```yaml
strategy_id: ST-83
scenario: 时序相关的预警问题
strategy: 先提取时序特征，再用分类模型输出预警概率
reason: 预警依赖时序变化特征，而非当前状态
recommend: LSTM+逻辑回归混合模型
source: 2024国赛B题锂电池热失控预警一等奖论文|https://www.cumcm.edu.cn/works/excellent/2024/|2024
confidence: 高
```

---

## ST-84（公开经验库·公开）

```yaml
strategy_id: ST-84
scenario: 带优先级约束的多车辆调度
strategy: 将站点优先级转化为目标函数的权重，使用VRP+蚁群算法求解
reason: 优先级高的站点需要优先满足，需在目标函数中体现
recommend: VRP+蚁群算法
source: 2025亚太杯C题共享单车调度优化优秀论文|https://mbd.pub/o/bread/Z5ebm52tZw==|2025
confidence: 高
```

---

## ST-85（公开经验库·公开）

```yaml
strategy_id: ST-85
scenario: ['多气象因子的新能源发电预测']
strategy: 集成天气预报特征，选用树集成类机器学习模型
reason: ['光照、温度等多因素非线性地影响发电功率']
recommend: XGBoost或者LightGBM
source: 2025电工杯A题光伏电站发电功率日前预测优秀论文|https://blog.csdn.net/maligebilaowang/article/details/148101073|2025
confidence: 高
```

---

## ST-86（公开经验库·公开）

```yaml
strategy_id: ST-86
scenario: 社区公共基础设施选址规划
strategy: 构建0‑1整数规划，增设空间覆盖约束
reason: ['公共设施需要兼顾全部居民区，不能只优先人口密集区域']
recommend: Lingo、Gurobi求解整数规划模型
source: 2026电工杯B题嵌入式社区养老服务站的建设与优化问题论文|https://blog.csdn.net/maligebilaowang/article/details/161324818|2026
confidence: 高
```

---

## ST-87（公开经验库·公开）

```yaml
strategy_id: ST-87
scenario: 多自由度机器人避障轨迹规划
strategy: 正向运动学建模之后采用多目标遗传算法求解
reason: ['需要同时处理平滑度、能耗、避障多项指标']
recommend: D‑H参数+改进遗传算法
source: 2024年华数杯A‑机器臂关节角路径的优化设计论文|https://blog.csdn.net/maligebilaowang|2024
confidence: 高
```

---

## ST-88（公开经验库·公开）

```yaml
strategy_id: ST-88
scenario: 自然灾害风险等级判别预测
strategy: 先进行相关性筛选，之后使用随机森林开展分类
reason: ['地形降水因子之间大多是非线性关系']
recommend: Kmeans聚类划分风险等级+随机森林
source: 2024亚太杯中文赛B题洪水灾害的数据分析与预测论文|https://jishuzhan.net/article/1811720976279277569|2024
confidence: 高
```

---

## ST-89（公开经验库·公开）

```yaml
strategy_id: ST-89
scenario: 多维度工程调度方案对比评价
strategy: 指标正向化之后使用CRITIC求取权重，TOPSIS排序
reason: ['兼顾指标波动和指标之间冲突，权重分配更加合理']
recommend: CRITIC‑TOPSIS评价框架
source: 2026年华数杯C题算电协同的多目标优化调度优化研究论文|https://www.iesdouyin.com/share/video/7671299682630503730|2026
confidence: 高
```

---

## ST-90（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-90
scenario: 带随机风险的工业抽样检验优化
strategy: 蒙特卡洛模拟仿真次品风险，遗传算法优化抽样参数
reason: ['零件次品属于随机事件，依靠仿真模拟风险损失']
recommend: 遗传算法‑蒙特卡洛耦合模型
source: 2024高教社杯国赛B题生产检测决策优化一等奖论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2024qgdxssxjmjslwzs_2024btlw/241104/1977943.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-91（公开经验库·公开）

```yaml
strategy_id: ST-91
scenario: 生态系统物种耦合演化仿真
strategy: 基于物质守恒构建常微分方程组刻画种群互相作用
reason: ['生态群落演变依靠内在机理，单纯数据拟合泛化能力差']
recommend: ODE常微分方程动力学模型
source: 2021年美赛MCM‑ICM A题森林真菌生态建模O奖论文|https://wenku.csdn.net/doc/xqnrkpdv3e|2021
confidence: 中
```

---

## ST-92（公开经验库·公开）

```yaml
strategy_id: ST-92
scenario: 设施选址‑配送路径联合优化
strategy: 混合整数规划搭建约束框架，改进蚁群算法求解
reason: ['同时包含离散选址变量和连续路径优化，属于NP‑hard组合优化']
recommend: MIP+改进蚁群算法
source: 2025电工杯B题城市垃圾分类运输的路径优化优秀论文|https://blog.csdn.net/maligebilaowang/article/details/148223307|2025
confidence: 高
```

---

## ST-93（公开经验库·公开）

```yaml
strategy_id: ST-93
scenario: 大型赛事奖牌多层因素预测
strategy: 分层概率回归，历史数据设置时间衰减权重
reason: ['近期赛事参考价值更高，东道主效应属于非线性影响因子']
recommend: 多层次嵌套回归预测模型
source: MCM‑ICM奥运会奖牌预测O奖论文解析|https://mcmicm.org.cn/news/1186.html|2026
confidence: 中
```

---

## ST-94（公开经验库·公开）

```yaml
strategy_id: ST-94
scenario: 软硬指标共存的城市发展水平评估
strategy: 主成分分析精简指标，模糊综合评价处理主观数据
reason: ['智慧城市评估同时含有硬性统计数据和民众主观感受指标']
recommend: PCA‑模糊综合评价模型
source: 2017年美赛ICM E题智慧城市建设O奖论文|https://blog.csdn.net/qq_41112170/article/details/122108814|2017
confidence: 中
```

---

## ST-95（公开经验库·公开）

```yaml
strategy_id: ST-95
scenario: 交通信号灯动态优化
strategy: MDP+DQN强化学习动态配时，配合仿真验证（SUMO）
reason: 传统固定配时无法适应动态交通流，强化学习可实时响应；SUMO仿真验证避免直接上路测试的风险
recommend: 竞赛中若缺乏真实仿真环境，可用简化排队模型模拟车流，再训练DQN；务必设计合理的奖励函数（如车速+通行量-等待时间加权）
source: 2024年高教社杯全国大学生数学建模竞赛E题：交通流量管控|https://blog.csdn.net/weixin_43292788/article/details/146361641|2024
confidence: 高
```

---

## ST-96（公开经验库·公开）

```yaml
strategy_id: ST-96
scenario: 畜牧养殖多阶段空间规划（交配-妊娠-哺乳-育肥-休整）
strategy: 动态状态转移模型+整数规划优化初始配置+蒙特卡洛稳健性检验
reason: 养殖周期各阶段空间需求不同且时间耦合，动态模型刻画流转；整数规划优化初始投入；蒙特卡洛检验参数不确定性
recommend: 对类似养殖/制造多阶段排产问题，建议先建立状态转移方程明确各阶段数量动态，再用优化模型求解初始配置，最后用模拟验证
source: 2023年高教社杯全国大学生数学建模竞赛D题：圈养湖羊的空间利用率|https://www.ppmy.cn/news/1096239.html|2023
confidence: 高
```

---

## ST-97（公开经验库·公开）

```yaml
strategy_id: ST-97
scenario: 应急通信中有限时间内的信息全网共享
strategy: 信息传输率最大化+对称性设计+概率冗余保障
reason: 应急场景时间紧迫，需每轮传输信息量最大；对称性简化方案设计并保证公平性；概率冗余确保关键信息可靠到达
recommend: 对类似报文共享问题，先计算信息论下限（总信息量/信道容量），再设计对称并行传输方案逼近下限，最后根据可靠性要求增加冗余
source: 2022年高教社杯全国大学生数学建模竞赛D题：气象报文信息卫星通信传输|https://www.lmlphp.com/user/628420/article/item/10928850/|2022
confidence: 高
```

---

## ST-98（公开经验库·公开）

```yaml
strategy_id: ST-98
scenario: 高维光谱数据的种类/产地鉴别
strategy: 预处理→降维/特征选择→多模型对比→集成融合
reason: 光谱数据噪声大、维度高，预处理是基础；降维避免维度灾难；多模型对比选择最优；集成融合提高稳健性
recommend: 对类似光谱/色谱鉴别问题，建议先用SG平滑+SNV+MSC预处理，再用PCA/PLS降维，然后用SVM/RF做基线分类，最后用投票或概率融合集成，避免直接用原始数据训练深度学习
source: 2021年高教社杯全国大学生数学建模竞赛E题：中药材的鉴别|https://blog.csdn.net/weixin_43970743/article/details/161521761|2021
confidence: 高
```

---

## ST-99（公开经验库·公开）

```yaml
strategy_id: ST-99
scenario: 工业热加工过程的机理建模与参数优化
strategy: 机理方程（热传导/对流）+数值求解（有限差分）+智能优化（模拟退火/遗传算法）
reason: 机理模型保证外推合理性与物理可解释性；数值求解处理复杂边界条件；智能优化搜索全局最优工艺参数
recommend: 对类似炉温曲线、热处理工艺优化问题，建议先建立一维非稳态热传导基线模型，用有限差分验证后，再扩展到二维；优化时先用网格搜索定位大致范围，再用模拟退火精细搜索
source: 2020年高教社杯全国大学生数学建模竞赛A题：炉温曲线|https://wenku.csdn.net/answer/303wy9rvnqqv|2020
confidence: 高
```

---

## ST-100（公开经验库·公开）

```yaml
strategy_id: ST-100
scenario: 大型精密结构的空间几何调节（如望远镜反射面、天线阵面）
strategy: 物理约束确定理想形状→坐标变换适应不同工况→几何优化满足执行器约束→微元法评估性能
reason: 精密结构调节需兼顾物理原理（光学/电磁学）、几何可达性（执行器行程）与性能评估；分步策略保证各环节可验证
recommend: 对类似FAST反射面、相控阵天线等问题，先由物理定律确定理想曲面，再用坐标变换处理不同指向，最后用优化算法在满足执行器约束下逼近理想形状，性能评估采用蒙特卡洛或微元法
source: 2021年高教社杯全国大学生数学建模竞赛A题：FAST主动反射面的形状调节|https://blog.csdn.net/m0_49842530/article/details/146071683|2021
confidence: 高
```

---

## ST-101（公开经验库·公开）

```yaml
strategy_id: ST-101
scenario: 农业图像识别（数据量小、场景相对单一）
strategy: 传统图像处理为主（颜色+形状），深度学习为辅（迁移学习）
reason: 农业竞赛数据集通常不大，传统方法可解释性强、计算快；深度学习用于需要语义理解的环节（如种类识别）
recommend: 对类似果实识别问题，建议先用颜色阈值+形态学滤波做初步分割，再用几何特征（圆度、面积）筛选目标，最后用轻量CNN或K-means做分类/分级，避免盲目使用YOLO/Faster R-CNN
source: 2023年APMCM亚太地区大学生数学建模竞赛A题：果实采摘机器人的图像识别|https://blog.csdn.net/2201_75432540/article/details/134599444|2023
confidence: 中
```

---

## ST-102（公开经验库·公开）

```yaml
strategy_id: ST-102
scenario: 设施农业环境调控（CFD计算量大、需多工况对比）
strategy: 简化CFD理论模型+自主编程实现+参数扫描优化
reason: 完整CFD仿真在竞赛中不可行，但可用简化方程（如二维稳态N-S方程）自主编程求解；参数扫描可系统对比不同配置
recommend: 对类似温室、建筑通风问题，建议先建立二维简化模型（忽略长度方向变化），用有限体积法编程求解，验证后再扩展到三维；优化时采用网格搜索而非遗传算法，降低计算量
source: 2023年APMCM亚太地区大学生数学建模竞赛B题：玻璃温室中的微气候调控|https://jishuzhan.net/article/1728259980206804994|2023
confidence: 中
```

---

## ST-103（公开经验库·公开）

```yaml
strategy_id: ST-103
scenario: 新兴产业长期发展趋势预测（政策驱动、技术变革、市场替代）
strategy: 时间序列基线预测+多因素回归修正+竞争/系统动力学模型刻画交互+情景分析处理不确定性
reason: 单一模型难以兼顾历史趋势、外部因素、市场交互与不确定性；分层策略各取所长
recommend: 对类似新能源、AI等新兴产业预测，建议先用ARIMA/指数平滑做基线，再用回归纳入政策/经济因素，最后用竞争模型或系统动力学刻画市场结构变化，始终以情景分析收尾
source: 2023年APMCM亚太地区大学生数学建模竞赛C题：我国新能源电动汽车的发展趋势|https://blog.csdn.net/weixin_45499067/article/details/134551814|2023
confidence: 中
```

---

## ST-104（公开经验库·公开）

```yaml
strategy_id: ST-104
scenario: 多品种小批量物料的需求预测与库存控制（需求波动大、提前期固定、服务水平约束）
strategy: 分类预测（按趋势分组）+动态参数调整+库存-服务联合优化
reason: 小批量物料需求模式各异，分类处理提高预测精度；动态调整适应需求变化；联合优化平衡成本与服务
recommend: 对类似MTO/ETO生产环境，建议先按ABC分类或趋势聚类将物料分组，再对各组分别建立预测模型（如指数平滑/ARIMA），最后用(s,S)或动态规划做库存决策，始终以满足服务水平为硬约束
source: 2022年高教社杯全国大学生数学建模竞赛E题：小批量物料的生产安排|https://blog.csdn.net/weixin_43292788/article/details/131082064|2022
confidence: 高
```

---

## ST-112（公开经验库·公开）

```yaml
strategy_id: ST-112
scenario: 电池寿命预测；非线性曲线拟合；多因素影响预测
strategy: 特征分析+非线性建模+组合预测
reason: 先理解数据特征, 再选合适非线性模型, 组合预测降低单一模型风险
recommend: 
source: 全国大学生数学建模竞赛2016年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## ST-113（公开经验库·公开）

```yaml
strategy_id: ST-113
scenario: 风电功率预测；风电场布局优化；可再生能源运行分析
strategy: 稳态拟合+动态预测+尾流优化的分层策略
reason: 分层建模从稳态到动态到系统级, 逐步提升预测和优化精度
recommend: 
source: 全国大学生数学建模竞赛2016年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## ST-114（公开经验库·公开）

```yaml
strategy_id: ST-114
scenario: 空间定价策略；任务分配优化；多目标决策
strategy: 聚类分区+回归建模+多目标优化的三步法
reason: 先分区再建模提高针对性, 多目标优化平衡成本和完成率
recommend: 
source: 全国大学生数学建模竞赛2017年B题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## ST-115（公开经验库·公开）

```yaml
strategy_id: ST-115
scenario: 光谱/颜色分析建模；物质浓度预测；多指标辨识评价
strategy: 非线性回归建模+AHP系统评价
reason: 非线性回归准确建模, AHP提供系统化评价框架
recommend: 
source: 全国大学生数学建模竞赛2017年C题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## ST-116（公开经验库·公开）

```yaml
strategy_id: ST-116
scenario: 用户画像与分群；消费行为预测；精准营销策略
strategy: 特征工程+聚类分群+分类预测+关联分析的全流程
reason: 多方法组合覆盖画像刻画的全流程, 各方法互补
recommend: 
source: 全国大学生数学建模竞赛2018年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2018
confidence: 中
```

---

## ST-117（公开经验库·公开）

```yaml
strategy_id: ST-117
scenario: 传感器数据校准；空气质量监测；多源数据融合
strategy: 线性基准+非线性增强的组合校准策略
reason: 线性模型提供可解释基准, 非线性模型提升精度, 组合更鲁棒
recommend: 
source: 全国大学生数学建模竞赛2019年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 中
```

---

## ST-118（公开经验库·公开）

```yaml
strategy_id: ST-118
scenario: 定价策略优化；需求弹性分析；利润最大化
strategy: 弹性分析+最优化+敏感性分析
reason: 弹性分析提供理论基础, 最优化求解最优策略, 敏感性分析评估鲁棒性
recommend: 
source: 全国大学生数学建模竞赛2019年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 低
```

---

## ST-119（公开经验库·公开）

```yaml
strategy_id: ST-119
scenario: 信贷风险评估；金融决策优化；企业信用分类
strategy: 机器学习风控预测+整数规划决策优化
reason: 机器学习准确预测风险, 整数规划给出最优决策, 两者形成预测-决策闭环
recommend: 
source: 全国大学生数学建模竞赛2020年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 中
```

---

## ST-120（公开经验库·公开）

```yaml
strategy_id: ST-120
scenario: 时间序列预测；异常检测；智能水务管理
strategy: 深度学习预测+异常检测+调度优化
reason: LSTM适应复杂周期模式, 孤立森林无需标注即可检测异常
recommend: 
source: 全国大学生数学建模竞赛2020年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 低
```

---

## ST-121（公开经验库·公开）

```yaml
strategy_id: ST-121
scenario: 人口预测；年龄结构分析；政策效果评估
strategy: 矩阵模型+参数校准+情景分析
reason: 矩阵模型精确模拟年龄推移, 情景分析提供政策参考
recommend: 
source: 全国大学生数学建模竞赛2007年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2007
confidence: 中
```

---

## ST-122（公开经验库·公开）

```yaml
strategy_id: ST-122
scenario: 河流水质评价与预测；污染物传播建模；环境管理决策
strategy: 现状评价+传播建模+趋势预测+对策建议
reason: 从评价到建模到预测形成完整分析链, 为管理决策提供科学依据
recommend: 
source: 全国大学生数学建模竞赛2005年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2005
confidence: 中
```

---

## ST-123（公开经验库·公开）

```yaml
strategy_id: ST-123
scenario: 临床疗效评价；重复测量数据分析；治疗方案优化
strategy: 混合效应模型+回归预测+综合评价
reason: 混合效应模型正确处理重复测量, 回归预测提供趋势, 评价给出决策建议
recommend: 
source: 全国大学生数学建模竞赛2006年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2006
confidence: 中
```

---

## ST-124（公开经验库·公开）

```yaml
strategy_id: ST-124
scenario: 传染病传播预测；疫苗/医疗资源分配；公共卫生应急
strategy: 机理传播模型+资源优化分配+敏感性分析
reason: 机理模型描述传播动态, 优化模型分配资源, 敏感性分析评估鲁棒性
recommend: 
source: 2015 MCM Problem A: Eradicating Ebola|https://www.jingsailian.com/news/233612.html|2015
confidence: 中
```

---

## ST-142（公开经验库·公开）

```yaml
strategy_id: ST-142
scenario: 农作物病害识别；图像分类；小样本学习
strategy: 迁移学习+数据增强+模型微调
reason: 迁移学习解决小样本, 数据增强平衡类别, 微调适应任务
recommend: 
source: 2019年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2019
confidence: 低
```

---

## ST-143（公开经验库·公开）

```yaml
strategy_id: ST-143
scenario: 光伏功率预测；新能源发电调度；物理-数据融合建模
strategy: 物理模型+数据驱动修正的组合预测
reason: 物理模型提供机理基础, 数据驱动修正实际偏差, 组合更准确
recommend: 
source: 2019年电工杯数学建模竞赛A题|https://www.saikr.com/vse/DGB2019|2019
confidence: 低
```

---

## ST-144（公开经验库·公开）

```yaml
strategy_id: ST-144
scenario: 空气质量预测；多因素影响分析；环境污染治理
strategy: PCA降维+LSTM预测+因素分析
reason: PCA处理高维, LSTM捕捉时序, 因素分析提供治理依据
recommend: 
source: 2019年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2019|2019
confidence: 低
```

---

## ST-157（公开经验库·公开）

```yaml
strategy_id: ST-157
scenario: 户外行程调度；营地容量分配；多队资源管理
strategy: 营地容量建模+整数规划分配+仿真验证
reason: 容量约束保证可行, 整数规划消除冲突, 仿真验证整体行程
recommend: 
source: 2012 MCM Problem B: Camping along the Big Long River|https://www.contest.comap.com/undergraduate/contests/|2012
confidence: 中
```

---

## ST-158（公开经验库·公开）

```yaml
strategy_id: ST-158
scenario: 多车道交通仿真；车道规则评估；通行效率优化
strategy: 元胞自动机微观仿真+规则对比+效率评价
reason: 微观仿真捕捉换道细节, 规则对比量化收益, 评价支撑管理建议
recommend: 
source: 2014 MCM Problem A: Keep-Right-Except-to-Pass Rule|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## ST-159（公开经验库·公开）

```yaml
strategy_id: ST-159
scenario: 收费站合流优化；瓶颈通行能力提升；收费车道配置
strategy: 瓶颈定位+排队建模+合流仿真优化
reason: 先定位真瓶颈再优化, 仿真刻画合流微观行为, 提升整体吞吐
recommend: 
source: 2017 MCM Problem B: Merge After Toll|https://www.contest.comap.com/undergraduate/contests/|2017
confidence: 中
```

---

## ST-160（公开经验库·公开）

```yaml
strategy_id: ST-160
scenario: 安检/服务台配置；排队资源优化；运营排班
strategy: 排队论定通道+整数规划排班+仿真验证
reason: 排队论给理论通道数, 排班优化控成本, 仿真保证随机下可行
recommend: 
source: 2017 ICM Problem D: Airport Checkpoint Operations|http://www.madio.net/thread-290074-1-1.html|2017
confidence: 中
```

---

## ST-161（公开经验库·公开）

```yaml
strategy_id: ST-161
scenario: 加油/充电站选址；应急设施覆盖；服务网络优化
strategy: 需求驱动最大覆盖选址+容量整数规划
reason: 覆盖模型贴合需求, 整数规划控成本与容量, 提升投资效率
recommend: 
source: 2018 MCM Problem D: Out of the Gas?|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## ST-162（公开经验库·公开）

```yaml
strategy_id: ST-162
scenario: 项目团队组建；技能-任务匹配；组织效能优化
strategy: 0-1组队+技能覆盖约束+沟通多目标权衡
reason: 0-1规划精确组队, 覆盖约束保可行, 多目标平衡技能与沟通成本
recommend: 
source: 2020 MCM Problem D: The Teaming Strategy|https://www.contest.comap.com/undergraduate/contests/|2020
confidence: 中
```

---

## ST-163（公开经验库·公开）

```yaml
strategy_id: ST-163
scenario: 可持续投资决策；三重底线评价；长期战略优化
strategy: 三重底线建模+AHP赋权+多目标优化
reason: 三重底线全面刻画价值, AHP客观赋权, 多目标给出平衡的最优投入
recommend: 
source: 2015 ICM Problem D: Is it smarter to be sustainable?|http://www.madio.net/thread-290074-1-1.html|2015
confidence: 中
```

---

## ST-164（公开经验库·公开）

```yaml
strategy_id: ST-164
scenario: 会务资源预订；不确定需求下采购；整数规划配置
strategy: 整数规划配置+蒙特卡洛应对需求不确定性
reason: 整数规划精确配置资源, 蒙特卡洛在随机需求下检验与优化方案
recommend: 
source: 全国大学生数学建模竞赛2009年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2009
confidence: 中
```

---

## ST-176（公开经验库·公开）

```yaml
strategy_id: ST-176
scenario: 教育/公益投资评价；投资组合优选；效率评价(DEA)
strategy: 降维筛选+DEA效率评价+组合优选
reason: 降维提升指标质量, DEA客观评效率, 组合优化兼顾使命与回报
recommend: 
source: 2016 MCM Problem C: The Goodgrant Challenge|https://www.contest.comap.com/undergraduate/contests/|2016
confidence: 中
```

---

## ST-177（公开经验库·公开）

```yaml
strategy_id: ST-177
scenario: 隐私策略评价；效用-风险权衡；合规成本分析
strategy: 成本效益+AHP多维隐私评价
reason: 成本效益给量化基准, AHP融合多维诉求, 支撑隐私策略取舍
recommend: 
source: 2018 ICM Problem F: Cost of Privacy|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## ST-178（公开经验库·公开）

```yaml
strategy_id: ST-178
scenario: 卫生系统绩效评价；跨国指标比较；客观赋权评价
strategy: 熵值法客观赋权+神经网络非线性综合评价
reason: 客观赋权保证公正, 神经网络捕捉复杂关系, 适合多国系统比较
recommend: 
source: 2008 ICM Problem: Health Care System|http://www.madio.net/thread-290074-1-1.html|2008
confidence: 中
```

---

## ST-179（公开经验库·公开）

```yaml
strategy_id: ST-179
scenario: 能源配置评价；多方案优选；灰色预测辅助决策
strategy: 需求预测+AHP多维度方案评价
reason: 预测明确问题规模, AHP系统权衡技术经济环境多目标
recommend: 
source: 2009 MCM Problem B: Energy and Phones|https://www.contest.comap.com/undergraduate/contests/|2009
confidence: 中
```

---

## ST-180（公开经验库·公开）

```yaml
strategy_id: ST-180
scenario: 电动汽车推广评价；生命周期评价；政策情景分析
strategy: LCA全周期环境核算+AHP多维政策评价
reason: LCA避免局部视角, AHP统筹经济电网环境, 支撑推广决策
recommend: 
source: 2011 ICM Problem: Electric Vehicles|http://www.madio.net/thread-290074-1-1.html|2011
confidence: 中
```

---

## ST-181（公开经验库·公开）

```yaml
strategy_id: ST-181
scenario: 地球/生态健康评价；系统关联分析；关键风险识别
strategy: 网络关联建模+PCA降维+AHP综合评价
reason: 网络揭示耦合, PCA去冗余, AHP量化健康, 适合复杂巨系统评价
recommend: 
source: 2013 MCM Problem C: Earth Health Network Model|https://www.contest.comap.com/undergraduate/contests/|2013
confidence: 中
```

---

## ST-182（公开经验库·公开）

```yaml
strategy_id: ST-182
scenario: 出租车/网约车调度；供需匹配评价；动态补贴优化
strategy: 供需评价+热点聚类+定向调度补贴
reason: 评价定位失衡, 聚类聚焦热点, 定向调度提升匹配效率
recommend: 
source: 全国大学生数学建模竞赛2015年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2015
confidence: 中
```

---

## ST-183（公开经验库·公开）

```yaml
strategy_id: ST-183
scenario: 城市拥堵评价；路网健康分级；交通治理优先级
strategy: 熵权客观赋权+模糊综合评价拥堵分级
reason: 客观赋权保证公正, 模糊评价贴合拥堵的渐变特征, 适合分级管理
recommend: 
source: 2018年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2018
confidence: 低
```

---

## ST-184（公开经验库·公开）

```yaml
strategy_id: ST-184
scenario: 智慧物流评估；物流方案优选；多指标综合评价
strategy: AHP赋权+模糊综合评价智慧化水平
reason: AHP系统赋权, 模糊评价处理不确定性, 适合新兴概念的评价
recommend: 
source: 2018年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2018|2018
confidence: 低
```

---

## ST-205（自研·多来源择优）

```yaml
strategy_id: ST-205
scenario: 多来源公开经验采集（Kimi/豆包/GLM/WorkBuddy/千问并发产出）
strategy: 来源注册表优先级 + 内容指纹去重 + 幂等合并 + 质量门（占位/模糊来源过滤）
reason: 多来源并发产出必然跨源重复与占位，需确定性择优（rank排序+指纹去重+幂等）而非人工逐条判断
recommend: 新来源先在 SOURCES 登记 rank/tag/占位过滤；source 必须真实 URL；同题跨源保留高优先级版本；采集指令硬性要求单行JSON+真实URL+禁编造赛题
```

---

## ST-206（公开经验库·公开）

```yaml
strategy_id: ST-206
scenario: 确定性样本少但几何精度要求高
strategy: 使用周期切割的闭合三维实体模型，并设置包围盒、轴线距离和三角网格距离三级筛选
reason: 前两级快速排除不可能接触的对象，只有少量候选进入高成本细筛
recommend: 把粗筛设计成只会多保留候选而不会漏掉真实接触，并给出网格离散误差补偿
source: 2026年第七届“华数杯”大学生数学建模竞赛 A题《微构体中填充导电介质的仿真优化》 | 本地赛题PDF与配套代码复盘 | 2026
confidence: 高
```

---

## ST-207（公开经验库·公开）

```yaml
strategy_id: ST-207
scenario: 需要在多个参数水平上重复估计连通概率
strategy: 使用公共随机数、快速接触模型、并查集和并行蒙特卡洛
reason: 公共随机数使不同水平的比较更平稳，并查集能够在加入接触边时快速维护连通分量
recommend: 固定随机种子以保证可复现，同时用独立种子集完成最终验证，避免只报告单次随机结果
source: 2026年第七届“华数杯”大学生数学建模竞赛 A题《微构体中填充导电介质的仿真优化》 | 本地赛题PDF与配套代码复盘 | 2026
confidence: 高
```

---

## ST-208（公开经验库·公开）

```yaml
strategy_id: ST-208
scenario: 目标是满足概率约束的最小设计值
strategy: 先用逻辑斯蒂模型或代理模型定位临界区域，再在候选点上使用Wilson下限进行直接验证
reason: 模型拟合适合搜索，置信下限适合证明可行性，两者分工可以兼顾效率和严谨性
recommend: 论文中分别报告拟合交点和直接验证值，不要把两者混为同一个结论
source: 2026年第七届“华数杯”大学生数学建模竞赛 A题《微构体中填充导电介质的仿真优化》 | 本地赛题PDF与配套代码复盘 | 2026
confidence: 高
```

---

## ST-209（公开经验库·公开）

```yaml
strategy_id: ST-209
scenario: 离散设计变量具有单调性且单次仿真昂贵
strategy: 采用倍增找区间、整数二分定位边界，并缓存已知成功与失败状态，外层再用贝叶斯优化选择搜索位置
reason: 单调性能够推断部分未计算状态，代理模型能够把试验集中在低成本且不确定的位置
recommend: 在正式优化前验证单调性是否成立，并对最终低成本候选使用更大样本独立复核
source: 2026年第七届“华数杯”大学生数学建模竞赛 A题《微构体中填充导电介质的仿真优化》 | 本地赛题PDF与配套代码复盘 | 2026
confidence: 高
```

---

## ST-210（公开经验库·公开）

```yaml
strategy_id: ST-210
scenario: 水文时间序列分析（多因素、多时间尺度、有干预事件）
strategy: 分层递进：线性基线→非线性改进→动态滞后→深度学习预测→机理模型评估
reason: 水文数据兼具统计规律与物理机理，分层策略可从数据驱动逐步过渡到机理验证，提高结果可信度
recommend: 对类似河流水沙、水质监测问题，建议先用回归识别主效应，再用STL分解时序结构，长期预测用LSTM/ARIMA，效果评估用物理机理模型（如冲淤模型）
source: 2023年高教社杯全国大学生数学建模竞赛E题：黄河水沙监测数据分析|https://blog.csdn.net/weixin_43970743/article/details/161108783|2023
confidence: 高
```

---

## ST-211（公开经验库·公开）

```yaml
strategy_id: ST-211
scenario: 资源约束下的多阶段路径决策（游戏/探险/物流）
strategy: 动态规划全局优化+蒙特卡洛模拟不确定性+博弈论处理竞争
reason: 动态规划保证全局最优，蒙特卡洛评估随机因素，博弈论处理多主体交互
recommend: 对类似穿越沙漠、背包+路径组合优化问题，建议先建立状态空间（位置×时间×资源），再用DP逆向求解，最后用模拟验证策略稳健性
source: 2020年高教社杯全国大学生数学建模竞赛B题：穿越沙漠|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## ST-212（公开经验库·公开）

```yaml
strategy_id: ST-212
scenario: 离散测量数据的分段几何反演
strategy: 曲率分析识别段类型→最小二乘拟合参数→连续性约束修正边界
reason: 曲率反映局部几何特征，适合识别段类型；最小二乘精确估计参数；连续性约束保证工程合理性
recommend: 对类似轮廓仪、三坐标测量数据，建议先计算滑动窗口曲率，再用阈值分割，最后用RANSAC或最小二乘拟合各段，避免全局高阶拟合
source: 2020年高教社杯全国大学生数学建模竞赛D题：接触式轮廓仪的自动标注|https://gitcode.csdn.net/6a20255310ee7a33f2773f47.html|2020
confidence: 高
```

---

## ST-213（公开经验库·公开）

```yaml
strategy_id: ST-213
scenario: 高压流体系统的压力控制（燃油喷射、液压伺服）
strategy: 质量守恒+状态方程+流量边界+离散迭代+参数搜索
reason: 高压流体可压缩性显著，必须用质量守恒而非体积守恒；状态方程描述P-ρ关系；流量公式处理边界；离散迭代适合数值求解；搜索优化控制参数
recommend: 对类似高压油管、液压系统问题，务必先建立P-ρ关系（通过弹性模量积分），再用质量守恒方程，时间步长需足够小（0.01ms量级）以保证稳定性
source: 2019年高教社杯全国大学生数学建模竞赛A题：高压油管的压力控制|https://www.ppmy.cn/news/195212.html|2019
confidence: 高
```

---

## ST-214（公开经验库·公开）

```yaml
strategy_id: ST-214
scenario: 物联网传感器校准（时序数据、多因素干扰、小样本）
strategy: EDA差异分析→分层递进建模（线性→交互→非线性）→时间划分验证→滑动窗口稳健性检验
reason: 时序数据特性要求特殊验证方式；分层递进兼顾精度与可解释性；多维度差异分析指导特征工程
recommend: 对类似传感器校准问题，务必先做Bland-Altman一致性分析，再用时间划分验证，最后用滑动窗口检验模型对传感器漂移的适应能力
source: 2019年高教社杯全国大学生数学建模竞赛D题：空气质量数据的校准|https://gitcode.csdn.net/6a200938662f9a54cb792c0f.html|2019
confidence: 高
```

---

## ST-215（公开经验库·公开）

```yaml
strategy_id: ST-215
scenario: 多层防护材料的热设计与厚度优化
strategy: 热传导机理建模+有限差分数值求解+实验数据反演参数+网格搜索优化
reason: 机理模型保证外推合理性；有限差分处理复杂边界；数据反演识别未知参数；网格搜索保证全局最优
recommend: 对类似防护服、隔热层设计问题，建议先建立一维非稳态模型，用实测数据反演界面热阻，再做灵敏度分析确定关键层，最后优化关键层厚度
source: 2018年高教社杯全国大学生数学建模竞赛A题：高温作业专用服装设计|https://blog.csdn.net/weixin_43970743/article/details/161520460|2018
confidence: 高
```

---

## ST-216（公开经验库·公开）

```yaml
strategy_id: ST-216
scenario: 多人协作的刚体控制（同心鼓、无人机编队、机械臂协同）
strategy: 刚体动力学建模+小角度线性化+多目标优化+模拟退火全局搜索
reason: 刚体动力学保证物理正确性；小角度线性化降低求解复杂度；多目标优化平衡多个冲突目标；模拟退火避免陷入局部最优
recommend: 对类似多人协作控制问题，建议先建立完整刚体模型（6自由度），再根据实际情况降维（如小角度近似），最后用优化算法搜索协作策略，务必通过数值仿真验证
source: 2019年高教社杯全国大学生数学建模竞赛B题：同心协力策略研究|https://blog.csdn.net/2401_82505179/article/details/142747597|2019
confidence: 高
```

---

## ST-217（公开经验库·公开）

```yaml
strategy_id: ST-217
scenario: 服务系统中的个体决策与机制设计（排队+收益+博弈）
strategy: 排队论刻画系统性能+收益分析驱动个体决策+博弈论分析均衡+机制设计优化系统效率
reason: 排队论提供系统层面指标（等待时间、吞吐量）；收益分析解释个体行为；博弈论预测均衡状态；机制设计纠正市场失灵
recommend: 对类似机场出租车、医院挂号、网约车调度问题，建议先建立排队模型计算等待时间，再用收益比较分析个体选择，最后用机制设计（如优先权、补贴）优化系统整体效率
source: 2019年高教社杯全国大学生数学建模竞赛C题：机场的出租车问题|https://www.toymoban.com/blog/675072.html|2019
confidence: 高
```

---

## ST-218（公开经验库·公开）

```yaml
strategy_id: ST-218
scenario: 零售销售数据分析（数据缺失、多维度、需因果关系）
strategy: 数据清洗→指标构建→描述探索→回归量化→分类对比
reason: 零售数据质量参差不齐，清洗是基础；指标构建将业务概念转化为可计算变量；回归量化因果关系；分类对比揭示异质性
recommend: 对类似销售分析，建议先处理缺失值（行业均值/回归插补），再构建复合指标，最后用分层回归或分位数回归分析不同子群体的差异
source: 2019年高教社杯全国大学生数学建模竞赛E题：薄利多销分析|https://blog.csdn.net/2403_87108415/article/details/149207364|2019
confidence: 高
```

---

## ST-219（公开经验库·公开）

```yaml
strategy_id: ST-219
scenario: 零售会员精细化管理（价值识别、状态划分、激活策略、连带促销）
strategy: RFMT价值量化→K-means状态聚类→因子分析激活潜力→关联规则促销组合
reason: 会员管理是系统工程，价值识别确定优先级，状态划分指导差异化运营，激活策略挽回沉默客户，关联规则提升客单价
recommend: 对类似会员画像问题，建议用RFMT替代传统RFM（增加T反映消费能力），聚类时用轮廓系数确定K，关联规则用FP-Growth替代Apriori（效率更高），最后用AHP或熵权法确定指标权重
source: 2018年高教社杯全国大学生数学建模竞赛C题：大型百货商场会员画像描绘|https://damodev.csdn.net/6889c366bb9d8e0ecec3e417.html|2018
confidence: 高
```

---

## ST-220（公开经验库·公开）

```yaml
strategy_id: ST-220
scenario: 新增平台数量受限时
strategy: 优先在覆盖盲区或高发案区增设
reason: 提高整体覆盖率与响应速度
recommend: 结合敏感性分析确定最佳新增点
source: 2011年全国大学生数学建模B题优秀论文|https://doc.xuehai.net/b835340c48a00378980807b7c.html|2011
confidence: 高
```

---

## ST-221（公开经验库·公开）

```yaml
strategy_id: ST-221
scenario: 医疗资源突增
strategy: 动态提高隔离床位上限
reason: 打破传播链依赖收治能力
recommend: 建立医疗资源-感染率反馈回路
source: 2015 MCM Outstanding Papers: Eradicating Ebola|http://www.hanlin.com/archives/85459|2015
confidence: 高
```

---

## ST-222（公开经验库·公开）

```yaml
strategy_id: ST-222
scenario: 新增未知样本分级
strategy: 代入已有主成分空间进行判别
reason: 保持评级标准一致
recommend: 定期用新数据更新载荷矩阵
source: 2012国赛A题优秀论文|https://doc.xuehai.net/bc46036d3588eff46e760df6d.html|2012
confidence: 高
```

---

## ST-223（公开经验库·公开）

```yaml
strategy_id: ST-223
scenario: 城市规划部门选择开放试点
strategy: 优先开放环形或网状路网小区
reason: 提升连通性且延误可控
recommend: 配套交叉口渠化与限速管理
source: 2016年全国数学建模竞赛B题一等奖论文|https://www.bodocs.net/doc/4520055488.html|2016
confidence: 高
```

---

## ST-224（公开经验库·公开）

```yaml
strategy_id: ST-224
scenario: 预算有限时
strategy: 先清除高碰撞概率关键轨道带碎片
reason: 降低级联碰撞风险
recommend: 建立风险-成本双指标排序
source: 2016 MCM特等奖Outstanding论文B题下载-Space Junk|https://www.hanlin.com/archives/category/bonus/documents/page/49/|2016
confidence: 高
```

---

## ST-225（公开经验库·公开）

```yaml
strategy_id: ST-225
scenario: 电动车渗透率逐年提高
strategy: 预留扩容裕度并分阶段建设
reason: 避免重复投资
recommend: 采用滚动规划框架
source: 2016电工杯数学建模竞赛论文|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2016
confidence: 中
```

---

## ST-226（公开经验库·公开）

```yaml
strategy_id: ST-226
scenario: 多玩家同图竞争
strategy: 用博弈均衡选择路线与行动
reason: 避免集体拥堵或资源战
recommend: 结合蒙特卡洛评估策略稳健性
source: CUMCM2020-Desert-Game 全国一等奖论文源码|https://www.github.com/seanys/CUMCM2020-Desert-Game|2020
confidence: 高
```

---

## ST-227（公开经验库·公开）

```yaml
strategy_id: ST-227
scenario: 图像噪声较强
strategy: 先做滤波与边缘增强再提取特征
reason: 提高质心稳定性
recommend: 对连续帧做轨迹平滑
source: 亚太地区数学建模优秀论文_2019年第九届APMCM A题|https://blog.csdn.net/weixin_39580749/article/details/110816724|2019
confidence: 中
```

---

## ST-228（公开经验库·公开）

```yaml
strategy_id: ST-228
scenario: 早晚高峰流量不对称
strategy: 采用双向不对称绿波
reason: 匹配主向交通需求
recommend: 基于实时数据滚动优化周期
source: 2017 MCM特等奖Outstanding论文C题下载-Cooperate and Navigate|http://www.hanlin.com/archives/84719|2017
confidence: 高
```

---

## ST-229（公开经验库·公开）

```yaml
strategy_id: ST-229
scenario: 系统常发轻微故障
strategy: 在状态转移中插入空闲等待与重调度
reason: 降低报废传播
recommend: 保留可中断恢复机制
source: 智能RGV的动态调度策略|https://publish.cnki.net/journal/portal/stdx/client/paper/5a488777c0246c392ca31fa4b5cda6b9|2018
confidence: 高
```

---

## ST-230（公开经验库·公开）

```yaml
strategy_id: ST-230
scenario: CT系统参数标定与图像重建（几何误差+噪声+有限角度）
strategy: 最小二乘标定参数→中心切片定理基线重建→FBP处理噪声→新模板优化精度
reason: 分层策略从参数识别到图像重建逐步深入，每步都有理论保证；新模板从源端减少标定误差
recommend: 对类似成像反演问题，建议先用简单模板做最小二乘标定，再用解析重建验证，噪声大时切换至FBP或迭代算法，最后设计更优标定模板提升系统整体精度
source: 2017年高教社杯全国大学生数学建模竞赛A题：CT系统参数标定及成像|https://blog.csdn.net/weixin_43292788/article/details/142355315|2017
confidence: 高
```

---

## ST-231（公开经验库·公开）

```yaml
strategy_id: ST-231
scenario: 互联网平台任务定价与空间分配（众包/跑腿/巡检）
strategy: EDA发现规律→回归模型定价→密度聚类打包→对比验证成本
reason: 平台任务具有空间属性，定价需考虑供需密度；打包可降低边际成本；对比验证保证方案稳健
recommend: 对类似拍照赚钱、外卖配送、众包任务问题，建议先画地理热力图识别供需失衡区域，再用回归模型量化定价因素，最后用DBSCAN等空间聚类做任务组合优化
source: 2017年高教社杯全国大学生数学建模竞赛B题：'拍照赚钱'的任务定价|https://github.com/Henryers/PhotoPricingModel|2017
confidence: 高
```

---

## ST-232（公开经验库·公开）

```yaml
strategy_id: ST-232
scenario: 化学比色法浓度预测（多物质、小样本、高维颜色特征）
strategy: EDA分类→针对性建模（线性/非线性）→数据质量评价→维度/样本量灵敏度分析
reason: 化学显色反应机理各异，必须分类建模；小样本下需评价数据质量；灵敏度分析验证模型稳健性
recommend: 对类似光谱/色谱定量分析问题，建议先画散点图识别关系类型，线性用回归，饱和用Michaelis-Menten或Logistic，再做交叉验证与留一法检验，最后分析样本量与特征维度的影响
source: 2017年高教社杯全国大学生数学建模竞赛C题：颜色与物质浓度辨识|https://blog.csdn.net/weixin_43970743/article/details/161520390|2017
confidence: 高
```

---

## ST-233（公开经验库·公开）

```yaml
strategy_id: ST-233
scenario: 工业巡检路线排班（多周期约束、休息进餐窗口、错时上班）
strategy: 图论最短路径→周期分层分区→多目标人力优化→休息进餐约束嵌入→错时对比分析
reason: 工业巡检有严格的周期与安全约束，分层分区降低复杂度；多目标优化平衡成本与公平；错时分析提供管理决策依据
recommend: 对类似巡检、巡逻、设备维护排班问题，建议先按周期分层（高频/低频），再用图论求各层最短路径，最后用启发式或整数规划做人员分配，务必考虑休息窗口对有效工时的影响
source: 2017年高教社杯全国大学生数学建模竞赛D题：巡检线路的排班|https://blog.csdn.net/weixin_43970743/article/details/161520407|2017
confidence: 高
```

---

## ST-234（公开经验库·公开）

```yaml
strategy_id: ST-234
scenario: 海洋工程多体静力平衡与优化（系泊/锚固/吊装）
strategy: 隔离体受力分析→递推关系建立→几何约束校验→多目标优化→极端工况稳健性分析
reason: 多体系统需逐段传递力与力矩；几何约束（水深、着地）决定模型适用范围；多目标优化平衡多个工程指标；极端工况检验设计可靠性
recommend: 对类似系泊、吊装、塔架等问题，建议先画受力简图明确各构件关系，再建立递推公式，用搜索算法（而非梯度优化）处理强非线性约束，最后做参数灵敏度分析
source: 2016年高教社杯全国大学生数学建模竞赛A题：系泊系统的设计|https://blog.csdn.net/weixin_43970743/article/details/161519114|2016
confidence: 高
```

---

## ST-235（公开经验库·公开）

```yaml
strategy_id: ST-235
scenario: 城市交通政策影响评价（无标准数据、需多尺度建模）
strategy: 综合评价指标体系→微观仿真验证→分类对比→敏感性分析→政策建议
reason: 政策评价需多维度指标；微观仿真验证实际运行效果；分类对比揭示异质性；敏感性分析检验结论稳健性
recommend: 对类似小区开放、限行、拥堵收费等政策评估，建议先建TOPSIS等综合指标做宏观评估，再用元胞自动机或VISSIM做微观仿真，最后通过控制变量法识别关键影响因素
source: 2016年高教社杯全国大学生数学建模竞赛B题：小区开放对道路通行的影响|https://blog.csdn.net/weixin_43970743/article/details/161520008|2016
confidence: 高
```

---

## ST-236（公开经验库·公开）

```yaml
strategy_id: ST-236
scenario: 天文/地理参数反演（影长、星图、GPS信号）
strategy: 正向机理模型建立→全局搜索反演（遍历/PSO）→多解筛选→视频/图像扩展
reason: 天文参数反演问题机理明确但非线性强，正向模型保证物理正确性，全局搜索避免局部最优，多解筛选符合实际问题（若干可能地点）
recommend: 对类似太阳影子定位、星图识别、卫星轨道确定等问题，建议先建立精确的正向模型，再用粒子群或遗传算法做全局反演，最后根据物理约束（如地理位置合理范围）筛选多解
source: 2015年高教社杯全国大学生数学建模竞赛A题：太阳影子定位|https://blog.csdn.net/qq_73954832/article/details/140455963|2015
confidence: 高
```

---

## ST-237（公开经验库·公开）

```yaml
strategy_id: ST-237
scenario: 共享经济平台补贴设计（双边市场、行为响应、多目标权衡）
strategy: 模糊综合评价宏观诊断→多元回归微观量化→离散选择模型刻画行为→优化搜索确定补贴→置信区间控制成本
reason: 双边市场需同时考虑供需双方；行为模型（Logit）刻画非线性响应；优化搜索找到最佳补贴点；置信区间防止过度补贴
recommend: 对类似网约车、共享单车补贴问题，建议先用模糊评价或DEA做效率诊断，再用回归/Logit量化补贴弹性，最后用约束优化或博弈论设计动态补贴机制
source: 2015年高教社杯全国大学生数学建模竞赛B题：互联网+时代的出租车资源配置|https://blog.csdn.net/weixin_43292788/article/details/142518644|2015
confidence: 高
```

---

## ST-238（公开经验库·公开）

```yaml
strategy_id: ST-238
scenario: 自动化制造系统的AGV/RGV实时调度（多机床、异步加工、轨道约束）
strategy: 整数规划建模→启发式规则实时调度→元启发式全局优化→离散事件仿真验证
reason: 整数规划明确问题结构；启发式规则保证实时性；元启发式提升全局效率；仿真验证实际效果
recommend: 对类似AGV调度、机器人路径规划问题，建议先建立简化整数规划模型理解瓶颈，再设计EDD/SPT等启发式规则，最后用GA/PSO优化关键参数，务必用离散事件仿真（如Plant Simulation）验证
source: 2018年高教社杯全国大学生数学建模竞赛B题：智能RGV的动态调度策略|https://blog.csdn.net/gitblog_06777/article/details/148274765|2018
confidence: 中
```

---

## ST-239（公开经验库·公开）

```yaml
strategy_id: ST-239
scenario: 体育竞技中的抽象概念量化（势头/状态/手感）与预测
strategy: 多维度指标体系→综合评价量化→统计检验验证非随机性→灰色预测转折点→关联分析找关键因素→多场景验证泛化性
reason: 抽象概念需分解为可测指标；综合评价量化主观概念；统计检验验证客观规律；灰色预测适合小样本稀有事件；关联分析解释机理；多场景验证模型可靠性
recommend: 对类似势头、士气、状态等体育抽象概念，建议先文献调研确定维度，再用PCA/AHP-TOPSIS综合量化，务必做白噪声/随机性检验，预测转折点时用灰色灾变预测或HMM，最后在其他比赛验证泛化性
source: 2024年美国大学生数学建模竞赛MCM C题：网球运动中的势头|https://arxiv.org/pdf/2402.12149.pdf|2024
confidence: 高
```

---

## ST-240（公开经验库·公开）

```yaml
strategy_id: ST-240
scenario: 频率固定且追求低功耗
strategy: 优先减少反相器数并调栅长
reason: 功耗随频率与电容变化
recommend: 结合解析灵敏度分析
source: 2022华数杯数学建模A题环形振荡器的优化设计|https://www.bianchengbaodian.com/article/0d58bb48fc221cff4020253d3ae6e732.html|2022
confidence: 中
```

---

## ST-241（公开经验库·公开）

```yaml
strategy_id: ST-241
scenario: 左行国家移植规则
strategy: 镜像车道角色并复核视线约束
reason: 驾驶员视野与反应不同
recommend: 做敏感性而非简单替换
source: 2014 MCM特等奖Outstanding论文A题下载-The Keep-Right-Except-To-Pass Rule|http://www.hanlin.com/archives/85463|2014
confidence: 高
```

---

## ST-242（公开经验库·公开）

```yaml
strategy_id: ST-242
scenario: 上游路口距离较近
strategy: 将排队模型与信号周期联动
reason: 红绿灯周期改变到达率
recommend: 做周期敏感性分析
source: 2013年国赛一等奖优秀论文A题车道被占用对城市道路通行能力的影响|https://m.renrendoc.com/p-85829993.html|2013
confidence: 高
```

---

## ST-243（公开经验库·公开）

```yaml
strategy_id: ST-243
scenario: 希望压缩A类采购成本
strategy: 在多目标中设置采购结构与损耗率约束
reason: 避免单目标导致断供
recommend: 输出帕累托方案供决策
source: 2021年全国大学生数学建模竞赛题目C:生产企业原材料的订购与运输优秀论文范例|https://max.book118.com/html/2022/0816/5123202041004323.shtm|2021
confidence: 高
```

---

## ST-244（公开经验库·公开）

```yaml
strategy_id: ST-244
scenario: 多观测方向切换
strategy: 预先分段优化典型指向并插值
reason: 降低在线计算量
recommend: 建立指向-促动器查表
source: 2021年数模国赛题目优秀论文|https://download.csdn.net/download/weixin_67798981/88778695|2021
confidence: 高
```

---

## ST-245（公开经验库·公开）

```yaml
strategy_id: ST-245
scenario: 需要可解释配方规则
strategy: 岭回归与机理边界结合
reason: 说明正负向影响
recommend: 用树模型做重要性交叉验证
source: 开源一份2021年数学建模国赛B题全国二等奖的完整论文|https://juejin.cn/post/7083785524917305380|2021
confidence: 中
```

---

## ST-246（公开经验库·公开）

```yaml
strategy_id: ST-246
scenario: 沿海缺水城市
strategy: 优先耦合淡化与管网
reason: 降低长距离调水依赖
recommend: 做全生命周期成本分析
source: 2013 MCM特等奖Outstanding论文B题下载-Water, Water, Everywhere|https://www.hanlin.com/archives/category/bonus/documents/page/48|2013
confidence: 高
```

---

## ST-247（公开经验库·公开）

```yaml
strategy_id: ST-247
scenario: 电价峰谷差扩大
strategy: 让储能参与套利并校核寿命成本
reason: 提升经济性
recommend: 在目标中加折旧项
source: 全国大学生电工数学建模竞赛|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2018
confidence: 中
```

---

## ST-248（公开经验库·公开）

```yaml
strategy_id: ST-248
scenario: 高密度商圈停车场
strategy: 在容量与通道舒适度间取帕累托
reason: 减少剐蹭与拥堵
recommend: 输出多方案而非单极限值
source: 全国大学生电工数学建模竞赛|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2019
confidence: 中
```

---

## ST-249（公开经验库·公开）

```yaml
strategy_id: ST-249
scenario: 需求不确定增强
strategy: 用历史订单做滚动计划
reason: 降低缺货与库存
recommend: 设置安全库存约束
source: 2022华数杯|https://blog.csdn.net/weixin_43292788/category_11968618.html|2022
confidence: 中
```

---

## ST-250（公开经验库·公开）

```yaml
strategy_id: ST-250
scenario: 智慧水务管网漏损检测与维修决策
strategy: EDA用水模式识别→层级水量平衡→平滑预测漏损量→阈值定位→成本效益维修优化
reason: 水务数据量大且时序性强，EDA识别模式；层级平衡利用管网拓扑约束；平滑预测剔除噪声；阈值法快速定位；成本效益优化维修资源
recommend: 对类似供水、供热、供气管网问题，建议先建立管网拓扑图，再用节点平衡方程识别异常，最后用灰色预测或ARIMA估计漏损趋势，维修决策务必考虑全生命周期成本
source: 2020年高教社杯全国大学生数学建模竞赛E题：校园供水系统智能管理|https://blog.csdn.net/weixin_43292788/article/details/144255198|2020
confidence: 高
```

---

## ST-251（公开经验库·公开）

```yaml
strategy_id: ST-251
scenario: 多属性约束下的生产排程（汽车/电子/纺织）
strategy: 序贯优先级分解→分类特殊处理（高成本属性）→整数规划验证→成本量化评估
reason: 工业排程约束维度多且相互耦合，序贯分解是工程上最实用的策略；特殊属性（如黑车换色）单独优化；整数规划验证保证质量
recommend: 对类似总装线、印刷电路板排产问题，建议先识别最关键/最昂贵约束（如换色、换模），优先优化，再用序贯或启发式处理其余约束，最后用精确方法验证关键指标
source: 2018年高教社杯全国大学生数学建模竞赛D题：汽车总装线的配置问题|https://jishuzhan.net/article/1836921021442035713|2018
confidence: 高
```

---

## ST-252（公开经验库·公开）

```yaml
strategy_id: ST-252
scenario: 电池/电容器衰减曲线建模（前期波动、后期稳定、需反演求解）
strategy: EDA识别曲线形态→分段建模（不同函数）→反函数简化计算→插值扩展到连续参数→MRE评估
reason: 电池放电曲线具有典型的分段特征；反函数避免数值求解；插值实现参数泛化；MRE保证精度可量化
recommend: 对类似电池SOC估计、传感器衰减校准问题，建议先画曲线识别拐点，再分段选择模型（指数/多项式/幂函数），务必建立反函数或查找表以便实时查询，最后用交叉验证或MRE评估
source: 2016年高教社杯全国大学生数学建模竞赛C题：电池剩余放电时间预测|https://www.ppmy.cn/embedded/119988.html|2016
confidence: 高
```

---

## ST-253（公开经验库·公开）

```yaml
strategy_id: ST-253
scenario: 航天器轨道设计与最优控制（多阶段、强约束、燃料最优）
strategy: 经典力学解析轨道参数→离散化数值积分→直接法最优控制→高程图避障→灵敏度/误差分析
reason: 轨道力学部分可用经典理论解析；复杂动力学需数值积分；最优控制用直接法更实用；高程图处理避障约束；灵敏度分析保证工程可靠性
recommend: 对类似软着陆、交会对接、再入飞行问题，建议先用开普勒/二体问题做初始设计，再用数值积分精细仿真，最优控制优先选择直接法（如伪谱法、离散化+SQP），最后务必做蒙特卡洛误差分析
source: 2014年高教社杯全国大学生数学建模竞赛A题：嫦娥三号软着陆轨道设计与控制策略|https://blog.csdn.net/weixin_43970743/article/details/161518779|2014
confidence: 高
```

---

## ST-254（公开经验库·公开）

```yaml
strategy_id: ST-254
scenario: 可折叠结构设计（家具/机械/航天展开机构）
strategy: 几何运动学建模→逐杆参数计算→多目标优化→图像法可行域→静力学验证
reason: 折叠结构核心是几何约束与运动协调；逐杆分析保证各构件不干涉；多目标优化平衡性能与成本；图像法直观展示设计空间
recommend: 对类似折叠桌、太阳能帆板展开、机械臂折叠问题，建议先建立单杆运动模型，再推广到多杆，用几何约束而非复杂动力学，优化时优先选择可可视化的小维度决策空间
source: 2014年高教社杯全国大学生数学建模竞赛B题：创意平板折叠桌|https://jishuzhan.net/article/1845398393514364929|2014
confidence: 高
```

---

## ST-255（公开经验库·公开）

```yaml
strategy_id: ST-255
scenario: 城市道路事故影响评估与排队预测（有信号控制、车道占用）
strategy: 视频数据提取→通行能力折减分析→二流理论/神经网络排队模型→元胞自动机微观仿真→信号影响修正
reason: 事故影响需从实际数据出发；通行能力折减是核心参数；排队模型预测趋势；元胞自动机给出具体时间；信号控制修正提高精度
recommend: 对类似交通事故、施工占道影响评估，建议先用视频或线圈数据提取实际通行能力，再用二流理论或神经网络建立排队长度模型，最后用元胞自动机（如SUMO）做精细仿真，务必纳入信号配时
source: 2013年高教社杯全国大学生数学建模竞赛A题：车道被占用对城市道路通行能力的影响|https://blog.csdn.net/weixin_43292788/article/details/142876944|2013
confidence: 高
```

---

## ST-256（公开经验库·公开）

```yaml
strategy_id: ST-256
scenario: 感官评价与理化指标关联分析（食品/酒类/化妆品）
strategy: 统计检验评价可靠性→PCA降维→聚类分级→相关/回归找关键因素
reason: 感官评价主观性强，需统计检验可靠性；理化指标维度高需降维；聚类实现客观分级；回归量化因果关系
recommend: 对类似葡萄酒、茶叶、咖啡品质评价问题，建议先用方差分析评估评分者一致性，再用PCA+聚类做分级，最后用偏最小二乘(PLS)而非普通回归处理多重共线性
source: 2012年高教社杯全国大学生数学建模竞赛A题：葡萄酒的评价|https://blog.51cto.com/u_16213621/12369495|2012
confidence: 高
```

---

## ST-257（公开经验库·公开）

```yaml
strategy_id: ST-257
scenario: 环境污染评价与溯源（土壤/水体/大气）
strategy: 指数法量化污染→空间插值可视化→相关/PCA识别来源→机理模型反演定位→多源信息验证
reason: 环境问题是典型的数据+机理混合问题，指数法和插值做现状评价，PCA做来源解析，机理模型做定量反演，三者互补
recommend: 对类似重金属、有机物污染溯源问题，建议先用单因子+综合指数做快速筛查，再用克里金插值画污染地图，PCA/因子分析识别来源类型，最后用高斯扩散或对流-弥散模型反演定位，务必结合功能区信息验证
source: 2011年高教社杯全国大学生数学建模竞赛A题：城市表层土壤重金属污染分析|https://blog.csdn.net/weixin_43292788/article/details/142920057|2011
confidence: 高
```

---

## ST-258（公开经验库·公开）

```yaml
strategy_id: ST-258
scenario: 大规模碎片/图像拼接（文档修复、考古、拼图）
strategy: 特征分类降维→1D边缘匹配→贪心初始解→局部搜索优化(2-opt)→人工校验边界
reason: 大规模拼接必须降维；边缘匹配是核心；贪心快速构建初始解；局部搜索修正错误；边界特征辅助定位
recommend: 对类似碎纸、壁画、陶瓷修复问题，建议先按颜色/纹理/边界特征聚类分块，再逐块用贪心+2-opt拼接，最后用全局一致性检查（如文字行连续性）修正错误
source: 2013年高教社杯全国大学生数学建模竞赛B题：碎纸片的拼接复原|https://blog.csdn.net/weixin_43970743/article/details/161518701|2013
confidence: 高
```

---

## ST-259（公开经验库·公开）

```yaml
strategy_id: ST-259
scenario: 复杂几何体的体积/面积计算（储罐/船舱/建筑）
strategy: 几何分解→分类讨论边界条件→微元/截面/投影法积分→参数反演→误差分析→分块精细改进
reason: 复杂几何体边界条件多变，分类讨论是核心；微元法是基础；参数反演连接理论与实测；分块改进提高精度
recommend: 对类似储油罐、船舱容积计算问题，建议先画几何示意图明确所有可能的边界情形，再对每种情形分别建立积分公式，最后用实测数据反演未知参数并做误差分析，不要试图用单一公式覆盖所有情况
source: 2010年高教社杯全国大学生数学建模竞赛A题：储油罐的变位识别与罐容表标定|https://blog.csdn.net/weixin_43292788/article/details/142970050|2010
confidence: 高
```

---

## ST-260（公开经验库·公开）

```yaml
strategy_id: ST-260
scenario: 医疗资源调度（病床/手术室/检查设备）
strategy: 排队论基线→优先级分类→时间窗口时延→满意度-效率综合评价→比例优化
reason: 医疗调度涉及多类患者、多资源约束、时间窗口、满意度等多目标，分层策略逐步优化
recommend: 对类似医院调度问题，建议先按治疗流程识别时间窗口约束，再设计时延或预约机制，最后用仿真验证不同策略下的满意度和资源利用率
source: 2009年高教社杯全国大学生数学建模竞赛B题：眼科病床的合理安排|https://blog.csdn.net/weixin_43292788/article/details/143105580|2009
confidence: 高
```

---

## ST-261（公开经验库·公开）

```yaml
strategy_id: ST-261
scenario: 相机标定与视觉定位（靶标设计、特征提取、参数反演）
strategy: 射影几何不变量提取特征→最小二乘拟合参数→针孔模型标定→多相机坐标变换
reason: 射影几何处理透视变形，最小二乘提高精度，针孔模型是标定基础，坐标变换实现多相机定位
recommend: 对类似相机标定、三维重建问题，建议优先使用已知几何结构的靶标（如圆、棋盘格），利用不变量性质提取特征点，避免直接用几何中心近似
source: 2008年高教社杯全国大学生数学建模竞赛A题：数码相机定位|https://blog.csdn.net/weixin_43970743/article/details/161517516|2008
confidence: 高
```

---

## ST-262（公开经验库·公开）

```yaml
strategy_id: ST-262
scenario: 公共品/准公共品定价（教育/医疗/公共交通）
strategy: 市场结构分析→成本核算→需求侧支付能力评估→拉姆齐/博弈优化→公平性校验
reason: 公共品定价需兼顾效率与公平，不能仅用成本回收；市场结构分析识别竞争态势，支付能力评估保证可及性，博弈模型平衡多方利益
recommend: 对类似学费、医疗费、公交票价等问题，建议先收集供需双方数据，再用AHP或熵权法确定指标权重，最后用拉姆齐定价或合作博弈求解，务必做灵敏度分析检验不同收入群体的承受能力
source: 2008年高教社杯全国大学生数学建模竞赛B题：高等教育学费标准探讨|https://sx.xxu.edu.cn/info/1035/1357.htm|2008
confidence: 中
```

---

## ST-263（公开经验库·公开）

```yaml
strategy_id: ST-263
scenario: 人口/人力资源中长期预测（需考虑结构变化）
strategy: 总量基线→年龄结构Leslie矩阵→时变参数修正→分群体扩展→情景分析
reason: 人口问题核心是结构而非总量；Leslie矩阵刻画年龄结构；时变参数反映趋势；分群体扩展提高精度；情景分析处理不确定性
recommend: 对类似人口、劳动力、教育需求预测问题，建议先用Leslie矩阵做基线，再分别对生育率、死亡率、迁移率做趋势外推，最后分城乡/性别/地区扩展，务必做高/中/低生育情景分析
source: 2007年高教社杯全国大学生数学建模竞赛A题：中国人口增长预测|https://blog.csdn.net/weixin_43970743/article/details/161517385|2007
confidence: 高
```

---

## ST-264（公开经验库·公开）

```yaml
strategy_id: ST-264
scenario: 大规模网络最短路径与多目标优化（公交/地铁/导航）
strategy: 预建索引（直达数据库）→分层序列多目标优化→Dijkstra/BFS求解→网络融合（地铁+公汽）→实时系统架构
reason: 大规模网络需预计算降低在线查询复杂度；多目标需分层避免组合爆炸；单源算法比全源算法更适合实际系统；网络融合需合理的站点抽象
recommend: 对类似路径规划问题，建议先建立分层索引（如直达、一次换乘、多次换乘），再按优先级（转乘次数>时间>费用）逐层优化，最后用Dijkstra或A*算法求解，避免Floyd等全源算法
source: 2007年高教社杯全国大学生数学建模竞赛B题：乘公交，看奥运|https://www.docin.com/p-557988980.html|2007
confidence: 高
```

---

## ST-265（公开经验库·公开）

```yaml
strategy_id: ST-265
scenario: 企业内部资源分配（书号/产能/预算）
strategy: 指标体系构建→综合评价排序→多目标整数规划→稳定性约束→分层细化分配
reason: 资源分配需兼顾效率与公平、短期与长期；指标体系识别关键因素；综合评价排序提供依据；整数规划精确求解；稳定性约束保证可执行性
recommend: 对类似出版社、制造企业资源分配问题，建议先用熵权-TOPSIS或DEA做效率评价，再建立多目标规划模型，引入稳定性或连续性约束，最后用分层优化（先部门后项目）降低复杂度
source: 2006年高教社杯全国大学生数学建模竞赛A题：出版社的资源配置|https://blog.csdn.net/getusushu/article/details/132582371|2006
confidence: 高
```

---

## ST-266（公开经验库·公开）

```yaml
strategy_id: ST-266
scenario: 临床试验纵向数据分析（重复测量、多处理组、多终点）
strategy: EDA+聚类识别亚群→混合效应模型处理纵向结构→多组对比→成本效益双目标优化→个体化推荐
reason: 纵向数据需专门方法处理相关性；聚类识别异质性；混合效应模型是标准工具；双目标优化平衡疗效与成本；最终给出个体化治疗建议
recommend: 对类似临床试验、药物评价问题，建议先用混合效应模型（LME）建立基线，再做亚组分析，最后用成本效益分析或马尔可夫决策模型优化治疗方案，避免将重复测量数据当作独立样本处理
source: 2006年高教社杯全国大学生数学建模竞赛B题：艾滋病疗法的评价及疗效的预测|https://blog.csdn.net/weixin_43970743/article/details/161517254|2006
confidence: 高
```

---

## ST-267（公开经验库·公开）

```yaml
strategy_id: ST-267
scenario: 河流水质评价与污染溯源（多站点、多指标、长期预测）
strategy: 单因子筛查→模糊综合评价→一维水质模型反演污染源→灰色预测趋势→回归量化治理需求
reason: 分层策略从现状评价到机理溯源再到未来预测，逐步深入；单因子定位问题，模糊综合全面评价，机理模型定量溯源，灰色预测把握趋势
recommend: 对类似河流水质、大气污染问题，建议先用单因子和综合指数做快速筛查，再用机理模型（水质/大气扩散模型）反演污染源，最后用灰色预测或系统动力学做长期情景分析
source: 2005年高教社杯全国大学生数学建模竞赛A题：长江水质的评价和预测|https://blog.csdn.net/weixin_43970743/article/details/161512894|2005
confidence: 高
```

---

## ST-268（公开经验库·公开）

```yaml
strategy_id: ST-268
scenario: 在线服务平台资源分配（租赁/订阅/云资源）
strategy: 概率需求预测→整数规划全局分配→两阶段随机优化处理不确定性→灵敏度分析
reason: 在线服务需求波动大，概率预测是基础；整数规划保证全局最优；两阶段优化处理需求不确定性；灵敏度分析检验方案稳健性
recommend: 对类似Netflix/DVD租赁、云计算资源分配问题，建议先用历史数据做需求分布估计，再用整数规划或匹配算法做分配，最后用随机优化或鲁棒优化处理不确定性
source: 2005年高教社杯全国大学生数学建模竞赛B题：DVD在线租赁|https://blog.csdn.net/weixin_43970743/article/details/161513314|2005
confidence: 高
```

---

## ST-269（公开经验库·公开）

```yaml
strategy_id: ST-269
scenario: 大型活动临时商业设施规划（奥运会/世博会/演唱会）
strategy: 问卷数据挖掘行为模式→路径模拟预测人流→整数规划优化网点→均衡性约束→灵敏度分析
reason: 大型活动人流密集且行为可预测，问卷挖掘模式，路径模拟定位热点，整数规划优化配置，均衡性约束避免过度集中
recommend: 对类似活动商业规划问题，建议先用聚类或关联规则挖掘观众行为模式，再用Dijkstra或重力模型预测人流分布，最后用整数规划或启发式算法优化设施布局，务必考虑服务半径和排队容量约束
source: 2004年高教社杯全国大学生数学建模竞赛A题：奥运会临时超市网点设计|https://blog.csdn.net/weixin_43970743/article/details/161508748|2004
confidence: 高
```

---

## ST-270（公开经验库·公开）

```yaml
strategy_id: ST-270
scenario: 农业生物资产经营管理（养殖/种植周期、价格波动、规模约束）
strategy: 盈亏平衡底线分析→静态规模优化→价格趋势拟合→动态0-1规划→多情景稳健性检验
reason: 农业经营需先保证生存，再追求规模，最后优化时机；动态规划处理价格波动，0-1变量处理离散决策
recommend: 对类似养殖、种植经营优化问题，建议先用简单盈亏平衡确定底线，再用整数规划优化规模，最后引入价格预测和0-1变量做动态决策，务必考虑生物资产淘汰周期
source: 2014年高教社杯全国大学生数学建模竞赛C题：生猪养殖场的经营管理|https://www.ppmy.cn/embedded/127230.html|2014
confidence: 高
```

---

## ST-271（公开经验库·公开）

```yaml
strategy_id: ST-271
scenario: 古建筑/结构物变形监测与预测（小样本、多维度变形）
strategy: 几何拟合确定基准→多维度变形量化（倾斜/弯曲/扭曲）→灰色预测趋势→工程措施建议
reason: 古建筑监测数据稀少，几何拟合确定可靠基准是关键；多维度独立量化避免混淆不同变形模式；灰色预测适合小样本；最终需转化为工程语言
recommend: 对类似古塔、桥梁、大坝变形监测，建议先拟合基准面/线确定中心，再分别定义各变形指标，最后用灰色预测或卡尔曼滤波做趋势预测，务必与工程规范（如JGJ8）对照
source: 2013年高教社杯全国大学生数学建模竞赛C题：古塔的变形|https://blog.csdn.net/weixin_43292788/article/details/142879150|2013
confidence: 高
```

---

## ST-272（公开经验库·公开）

```yaml
strategy_id: ST-272
scenario: BIPV光伏建筑一体化设计（多约束、多目标、组合优化）
strategy: 辐射评估→电气匹配选型→几何布局优化→经济性分析→灵敏度检验
reason: BIPV需兼顾建筑约束、电气安全、经济效益；辐射评估确定潜力，电气匹配保证可行性，几何布局优化空间利用
recommend: 对类似光伏铺设问题，建议先用PVsyst或简化模型计算各面辐射量，再建立电池-逆变器匹配的整数规划模型，最后用启发式算法做具体布局，务必检查电气约束（电压范围、电流限制）
source: 2012年高教社杯全国大学生数学建模竞赛B题：太阳能小屋的设计|https://blog.csdn.net/weixin_43292788/article/details/142903938|2012
confidence: 中
```

---

## ST-273（公开经验库·公开）

```yaml
strategy_id: ST-273
scenario: 城市公共安全设施选址与调度（覆盖约束、工作量均衡、动态围堵）
strategy: 路径级覆盖分析→罚函数+0-1规划基础分配→模拟退火均衡优化→分类增设→多指标评价→仿真检验围堵
reason: 公共安全设施选址需精细到路径级覆盖；罚函数处理硬约束；模拟退火优化软目标；分类处理不同问题区域；仿真检验动态方案
recommend: 对类似警局、消防站、急救点选址问题，建议先按路径而非节点做覆盖分析，再用整数规划做基础分配，最后用启发式算法优化均衡性，动态围堵务必用仿真检验
source: 2011年高教社杯全国大学生数学建模竞赛B题：交巡警服务平台的设置与调度|https://www.ppmy.cn/embedded/129890.html|2011
confidence: 高
```

---

## ST-274（公开经验库·公开）

```yaml
strategy_id: ST-274
scenario: 大型活动/政策的经济影响评估（需反事实、多维度、长期与短期）
strategy: 时间序列分解识别趋势→ARMA建立反事实基准→对比得直接效应→乘数/回归量化间接效应→综合评估
reason: 大型活动影响评估需区分自然趋势与事件效应；反事实基准是因果推断的核心；乘数原理捕捉间接效应；综合评估避免片面性
recommend: 对类似奥运会、世博会、自贸区等经济影响评估，建议先用ARIMA/ARMA建立无政策/无事件的反事实预测，再做差值分析直接效应，最后用投入产出或乘数模型分析间接效应，务必做敏感性分析
source: 2010年高教社杯全国大学生数学建模竞赛B题：上海世博会影响力的定量评估|https://blog.csdn.net/weixin_43292788/article/details/142971912|2010
confidence: 高
```

---

## ST-275（公开经验库·公开）

```yaml
strategy_id: ST-275
scenario: 机电系统能量补偿控制（试验台/模拟器/伺服系统）
strategy: 机理建模（能量守恒）→开环理论计算→前馈迭代控制→反馈修正→频域优化设计
reason: 机电系统控制需从物理机理出发，逐步增加控制复杂度；开环提供基准，前馈快速响应，反馈消除稳态误差，频域设计保证稳定性
recommend: 对类似制动试验台、飞行模拟器、机器人伺服控制问题，建议先建立能量/力矩平衡机理模型，再设计前馈控制，最后务必引入反馈闭环，若精度仍不足则考虑频域设计或自适应控制
source: 2009年高教社杯全国大学生数学建模竞赛A题：制动器试验台的控制方法分析|https://blog.csdn.net/weixin_43292788/article/details/142999700|2009
confidence: 高
```

---

## ST-276（公开经验库·公开）

```yaml
strategy_id: ST-276
scenario: 工业产品几何优化（包装/容器/结构件）
strategy: 纯几何解析优化→引入实际约束（厚度/工艺）→多目标权衡→实测验证→灵敏度分析
reason: 工业产品优化不能停留在理论几何最优，必须逐步引入实际约束；多目标权衡反映设计冲突；实测验证保证模型可信度
recommend: 对类似易拉罐、瓶体、箱体设计问题，建议先求纯几何解析解作为基准，再测量实际产品识别约束差异，最后引入厚度、工艺、美观等多目标优化，务必做灵敏度分析检验方案稳健性
source: 2006年高教社杯全国大学生数学建模竞赛C题：易拉罐形状和尺寸的最优设计|https://blog.csdn.net/weixin_43970743/article/details/161517298|2006
confidence: 高
```

---

## ST-277（公开经验库·公开）

```yaml
strategy_id: ST-277
scenario: 房地产项目规划与税务优化（多房型、复杂税制、满意度约束）
strategy: 政策解读→分步税务核算→线性规划优化套数→回报率约束检验→迭代调整
reason: 房地产项目受政策约束强，税务核算是基础；线性规划优化配置；回报率硬约束决定方案可行性；迭代调整逼近最优
recommend: 对类似房地产、基建项目规划问题，建议先深入理解相关政策（税务、容积率、限购等），再建立精确核算模型，最后用优化模型调整方案，务必用灵敏度分析检验关键政策参数的影响
source: 2015年高教社杯全国大学生数学建模竞赛D题：众筹筑屋规划方案设计|https://blog.csdn.net/weixin_43292788/article/details/142817037|2015
confidence: 高
```

---

## ST-278（公开经验库·公开）

```yaml
strategy_id: ST-278
scenario: 风电场资源评估与运维优化（资源评估、设备选型、人员排班）
strategy: 威布尔分布资源评估→功率曲线拟合选型→整数规划排班→人性化调整→经济效益检验
reason: 风电场优化需从资源到设备再到运维全链条；威布尔是风速标准模型；功率曲线定量选型；整数规划处理离散排班；人性化调整保证可执行性
recommend: 对类似风电、光伏电站问题，建议先用威布尔或Weibull混合分布评估资源，再用功率曲线和容量系数做设备选型，最后用整数规划或启发式算法做运维排班，务必考虑季节性（风速/光照的季节差异）
source: 2016年高教社杯全国大学生数学建模竞赛D题：风电场运行状况分析及优化|https://blog.csdn.net/2403_87108415/article/details/149509195|2016
confidence: 高
```

---

## ST-279（公开经验库·公开）

```yaml
strategy_id: ST-279
scenario: 气象预报/环境监测的空间数据评价（网格-站点不匹配、分布不均、地形影响）
strategy: IDW/克里金空间插值→动态权重修正→高程地形修正→多指标误差统计→方法对比
reason: 气象网格预报与站点观测的空间不匹配是核心问题；插值是基础；动态权重和高程修正提高精度；多指标（绝对/相对误差）全面评价
recommend: 对类似雨量、温度、空气质量预报评价问题，建议先用IDW或克里金做空间匹配，再对不均匀分布引入自适应权重，地形复杂区加高程修正，最后用MAE、RMSE、相关系数等多指标综合对比
source: 2005年高教社杯全国大学生数学建模竞赛C题：雨量预报方法的评价|https://blog.csdn.net/2301_80194165/article/details/148932086|2005
confidence: 高
```

---

## ST-280（公开经验库·公开）

```yaml
strategy_id: ST-280
scenario: 多指标综合影响力/竞争力评价(展会、城市、景区、高校等)；小样本(n=4~6)横向对比排序问题
strategy: 无量纲归一化 -> 因子分析提取主因子(累积贡献率>80%即可单因子) -> 因子得分排序 -> AHP赋权交叉验证
reason: 因子分析用数据本身结构降维，避免主观赋权；累积贡献率阈值保证信息保留；AHP交叉验证增强结论可信度。论文实证：因子1累积81.087%、上海因子得分1.3352最高，与AHP验证一致。
recommend: 
source: 全国建模比赛一等奖 2010年上海世博会影响力的定量评估|https://max.book118.com/html/2020/0622/5120103111002310.shtm|2010
confidence: 高
```

---

## ST-281（公开经验库·公开）

```yaml
strategy_id: ST-281
scenario: 土壤/大气/水质污染空间分析；多源污染识别与溯源；区域环境质量评价
strategy: 异常值+正态化预处理 -> 克里金空间插值可视化 -> 单因子/内梅罗指数评价 -> 相关分析+因子分析溯源 -> 对流弥散反演源点
reason: 预处理保证插值无偏; 克里金利用空间自相关比IDW更优; 因子分析将8金属归并为3类同源组(Cr-Ni-Cu/As-Cd-Pb-Zn/Hg), 与功能区污染排序(工业区>交通区>生活区>公园>山区)一致。
recommend: 
source: 2011年全国大学生数模竞赛全国一等奖论文(城市表层土壤重金属污染分析)|https://max.book118.com/html/2019/0524/6003215231002032.shtm|2011
confidence: 高
```

---

## ST-282（公开经验库·公开）

```yaml
strategy_id: ST-282
scenario: 养老金/社保收支预测与缺口测算；替代率敏感性分析；人口老龄化背景下的政策评估
strategy: Logistic工资预测 -> 缴费指数+精算替代率模型 -> 资金缺口/收支平衡模型 -> 多因素灵敏度分析
reason: Logistic避免工资无界增长; 缴费指数使替代率个性化; 缺口+平衡年龄双指标评价可持续; 灵敏度分析锁定关键杠杆(缴费年限、退休年龄)。论文实证: 55岁退休缺口66万元、需领至65.5岁平衡。
recommend: 
source: 企业退休职工养老金制度的改革方案(大学生数学建模国家一等奖)|https://doc.guandang.net/sa971d8cd3fed93f0a060cd94.html|2011
confidence: 高
```

---

## ST-283（公开经验库·公开）

```yaml
strategy_id: ST-283
scenario: 疾病与环境因素关联分析；发病率预测；公共卫生预警与干预
strategy: 数据清洗+描述统计 -> 单因素筛选 -> SPSS逐步(后退法)多元线性回归 -> 文献补充高危因素 -> 预警干预
reason: 先清洗与描述锁定高危人群(男:女=1.17:1,71-80岁,农民), 再用逐步回归量化气象因素方向(最低气压/温差正相关, 平均湿度负相关), R²=0.918, 结论稳健。
recommend: 
source: 脑卒中发病环境因素分析及干预(2012国赛数学建模国家一等奖)|https://doc.xuehai.net/bec44fb1ced23f185c659750f.html|2012
confidence: 高
```

---

## ST-284（公开经验库·公开）

```yaml
strategy_id: ST-284
scenario: 道路通行能力分析；交通事故影响评估；交通拥堵预测与信号控制
strategy: 视频提取+pcu折算 -> 横断面实际通行能力动态模型 -> 差异度比较占道 -> 交通波排队长度估算 -> 信号灯周期预测
reason: pcu折算统一车型; 实际通行能力动态模型给出16.8pcu/min与3min堵塞阈值; 交通波排队公式关联度0.79/0.68; 结合信号灯可预测到达路口时间(5min33s)。
recommend: 
source: 车道占用对城市道路通行能力影响(2013高教社杯优秀论文选登, 华中科技大学)|https://dxs.moe.gov.cn/zx/a/qkt_sxjm/131112/1249183.shtml|2013
confidence: 高
```

---

## ST-285（公开经验库·公开）

```yaml
strategy_id: ST-285
scenario: 古建/高耸结构变形监测；多期观测数据变形分析；小样本趋势预测
strategy: 最小二乘定层中心 -> 空间直线/曲线+坐标变换刻画倾斜·弯曲·扭曲 -> 灰色预测趋势
reason: 最小二乘给出通用层中心; 三独立指标(倾斜角/弯曲率/相对扭曲度)全面刻画变形; 灰色预测适配4期小样本。二等奖实证: 总扭曲距离1996年11.94→2011年3.85。
recommend: 
source: 古塔的变形(2013高教社杯优秀论文选登, 成都工业学院)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700221.shtml|2013
confidence: 高
```

---

## ST-286（公开经验库·公开）

```yaml
strategy_id: ST-286
scenario: 基于影子/日晷的地理定位；单目视频定位；天文几何反问题求解
strategy: 太阳高度角几何模型 -> 非线性最小二乘反演(贪婪/遗传遍历) -> 多解分类筛选 -> 视频影长提取+折射修正
reason: 几何模型物理严谨; 最小二乘+遍历给出候选解集; 分类筛选与偏移角一致性保证解合理。国家一等奖实证影长相对误差限0.23%, 定位海南东方市(19.25°N,108.56°E)。
recommend: 
source: 基于非线性最小二乘法的太阳影子定位研究(2015国赛A题全国优秀论文)|https://max.book118.com/html/2017/0924/134885798.shtml|2015
confidence: 高
```

---

## ST-287（公开经验库·公开）

```yaml
strategy_id: ST-287
scenario: 管道/管廊/廊道网络费用优化；城区与郊区分段计价下的设施选址；含附加费(拆迁/补偿)的路径规划
strategy: 分区域计价建模 + 非线性规划求解汇合点P与车站E + AHP综合异质专家估算
reason: 分区域刻画成本结构后, 总费用可写为决策坐标的连续函数, 非线性规划给出全局最优走向; AHP按资质赋权避免等权平均失真
recommend: 
source: 输油管的布置-2010大学生年数学建模大赛优秀论文|https://max.book118.com/html/2020/0906/7125151136002165.shtm|2010
confidence: 高
```

---

## ST-288（公开经验库·公开）

```yaml
strategy_id: ST-288
scenario: 多规格原料的分装/搭配优化；有误差容限与降级规则的切割下料；带时限的工程排产方案生成
strategy: 倒序贪心分组 + 各规格整数线性规划 + 余料降级再规划
reason: 大规格稀缺原料优先匹配可保护长料, 分组规划把大规模问题降为可30分钟内求解的子问题, 降级规则在误差容限内逼近全局最优(189捆)
recommend: 
source: 数学建模天然肠衣国家二等奖论文|https://wk.baidu.com/view/28ffbe51c850ad02de80417c?pcf=2|2004
confidence: 高
```

---

## ST-289（公开经验库·公开）

```yaml
strategy_id: ST-289
scenario: 建筑光伏一体化(BIPV)电池板布置；受照面优化与最佳倾角设计；多型号器件的性价比选型
strategy: K=功率/价格筛选电池 + 整数规划铺设 + 倾角细步长枚举 + 贪心配逆变器
reason: 用性价比系数把型号海量化繁为简, 整数规划在面积约束下最大化发电, 倾角枚举直接榨取年辐射极值, 三者叠加使发电量从46万提升到99万kWh
recommend: 
source: 2012年全国大学生数学建模获奖范文(太阳能小屋的设计, 省一等奖)|https://max.book118.com/html/2015/0608/18664649.shtm|2012
confidence: 高
```

---

## ST-290（公开经验库·公开）

```yaml
strategy_id: ST-290
scenario: 带最小转弯半径的平面避障路径规划；移动机器人/AGV的线路设计；含安全裕度的几何最短路
strategy: 障碍外扩+可视图Dijkstra定拓扑 + 线圆结构(切线圆弧)求几何最短 + 对半径建目标函数寻优
reason: 外扩把碰撞约束显式化, Dijkstra避免组合爆炸, 线圆结构保证路径可行且几何最短, 半径寻优兼顾最短时间(得R=10.682, T=97.1698)
recommend: 
source: 2012全国大学生数学建模机器人避障问题优秀论文模型|https://wk.baidu.com/view/9635073577a20029bd64783e0912a21615797fca|2012
confidence: 高
```

---

## ST-291（公开经验库·公开）

```yaml
strategy_id: ST-291
scenario: 城市共享出行系统的站点分级与调度；基于使用频次的设施布局评价；供需失衡下的车辆再平衡
strategy: 数据清洗+频次统计定位热点 + 车锁比α分级调度窗口 + 满意度-成本多目标调度
reason: 频次统计把需求显性化, α分级把有限运力精准投向失衡站, 多目标模型兼顾体验与成本, 整体提升周转率并降低行驶距离
recommend: 
source: 公共自行车服务系统—大学生数学建模竞赛论文|https://m.book118.com/html/2015/1217/31548128.shtm|2015
confidence: 高
```

---

## ST-292（公开经验库·公开）

```yaml
strategy_id: ST-292
scenario: 畜禽养殖场的存栏结构与出栏计划；带价格周期的农业生产决策；容量受限下的生产优化
strategy: 盈亏平衡点定繁育底线 + 容量约束下整数规划求存栏/选种比 + 价格周期分解定出栏节奏
reason: 盈亏平衡提供不亏损底线, 容量约束保证方案可行, 周期分解把价格信号转化为出栏节奏, 三者叠加使三年平均年利润达328万元(母猪525头、选种比1:30)
recommend: 
source: 数学建模比赛C题省二等奖论文(生猪养殖场的经营管理)|https://m.renrendoc.com/paper/207871332.html|2014
confidence: 高
```

---

## ST-293（公开经验库·公开）

```yaml
strategy_id: ST-293
scenario: 药盒/零件的分拣槽与货格设计；带几何约束的标准件分类布局；类型数-冗余权衡的设施设计
strategy: 几何约束递推最少类型 + 逐步分裂迭代降冗余 + 平面冗余多目标定横向
reason: W≤2Dmin-1与W≥Dmax+4把安全约束显式化, 递推得最少5种竖向类型, 分裂迭代在类型数与冗余间取得平衡(12种), 平面冗余联合优化横向(13种)
recommend: 
source: 大学生数学建模(储药柜的设计, 国赛论文)|https://m.renrendoc.com/paper/210440230.html|2016
confidence: 高
```

---

## ST-294（公开经验库·公开）

```yaml
strategy_id: ST-294
scenario: 多机台+单AGV/RGV的车间调度；带工序约束的流水作业排程；含故障扰动的离散事件系统
strategy: 0-1变量形式化 + 多原则(就近/FIFO/HRRN)仿真 + 双工序布局遍历择优
reason: 把'加工数最多'形式化为仿真目标, 多原则互验避免偏倚, 双工序遍历256种布局并配比刀具(4:4/3:5/5:3)榨出最优, 单工序达383/360/393件、双工序253/212/241件
recommend: 
source: 2018年全国大学生数学建模竞赛论文展示(B217): 基于多原则比较和蒙特卡洛模拟的RGV动态调度模型|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018btlw/240206/1699832.shtml|2018
confidence: 高
```

---

## ST-295（公开经验库·公开）

```yaml
strategy_id: ST-295
scenario: 多属性产品的装配/喷涂排序；带衔接约束的序列优化；切换代价最小的生产排程
strategy: 强约束车先定位降维 + 颜色衔接构有向图 + 遗传算法TSP求最小切换代价
reason: 先填黑色等强约束车把搜索规模压下来, 再把颜色衔接转成图边, 遗传算法在约束图上求最小代价哈密顿路径, 兼顾可行与低成本
recommend: 
source: 2018年全国大学生数学建模竞赛论文展示(D027): 汽车总装线配置的优化模型研究|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018dtlw/240206/1699827.shtml|2018
confidence: 高
```

---

## ST-296（公开经验库·公开）

```yaml
strategy_id: ST-296
scenario: 机场/枢纽的出租与乘客匹配；带排队与收益权衡的服务调度；短途优先的公平机制设计
strategy: 效用模型比两方案 + 排队论量化等待 + AHP动态α + 短途绿色通道
reason: 效用模型把开放决策转为收益比较, M/M/1量化等待触发'>10分钟返城'阈值, AHP让α随情境自适应, 绿色通道补偿短途司机, 整体兼顾效率与公平
recommend: 
source: 2019数学建模竞赛B题优秀论文-基于'互联网+'机场的出租车问题|https://blog.csdn.net/weixin_43796658/article/details/103402800|2019
confidence: 高
```

---

## ST-297（公开经验库·公开）

```yaml
strategy_id: ST-297
scenario: 带资源约束的探险/生存游戏策略；不确定环境下的物资配置；多智能体路径博弈
strategy: 确定天气动态规划+初始补给多重搜索; 不确定天气用期望; 多玩家用纳什均衡
reason: 状态转移+DP给出天气已知下的全局最优(第1关10430/第2关12730元), 期望处理随机天气, 博弈避免多玩家互损, 三层递进覆盖全题型
recommend: 
source: 2020年数学建模B题国二论文: 穿越沙漠的最佳策略|https://max.book118.com/html/2023/0911/6205213114005225.shtm|2020
confidence: 高
```

---

## ST-298（公开经验库·公开）

```yaml
strategy_id: ST-298
scenario: 电力/能源系统经济调度；带网络安全约束的资源分配；市场清算与阻塞费用结算
strategy: 回归潮流显式化 + 段价优先经济调度 + 线路限值排序调整
reason: 最小二乘把潮流写成出力线性函数, '便宜先发'在爬坡约束下得最小费用预案(982.4MW总费用74416.8元), 再对超限线路(一/五/六)排序调整消除阻塞, 安全经济兼顾
recommend: 
source: 电力市场的输电阻塞管理(2004全国大学生数学建模竞赛全国二等奖论文)|https://m.diyifanwen.net/wenku/1417729.html|2004
confidence: 高
```

---

## ST-299（公开经验库·公开）

```yaml
strategy_id: ST-299
scenario: 建筑/产品方案的多属性综合评价与优选；含定量与定性模糊指标的多方案排序；高校后勤/设施设计类的综合评价问题
strategy: 三层AHP赋权 + 模糊隶属度量化 + 组合权重综合评价
reason: AHP用1-9标度系统量化目标-准则-指标三层重要性, 模糊隶属度把'舒适/安全'等定性指标转[0,1], 组合权重避免只按单准则偏差排序, 综合得分可直接比较方案
recommend: 
source: 2010数模D题 宿舍方案优化设计(基于AHP的学生宿舍设计方案评价)|https://m.renrendoc.com/paper/231326836.html|2010
confidence: 高
```

---

## ST-300（公开经验库·公开）

```yaml
strategy_id: ST-300
scenario: 食品/农产品质量评价(感官+理化混合)；多高度相关指标的分级与降维；理化指标与质量/品质的关联分析
strategy: 可信度检验 + PCA降维 + 聚类/优势因子分级 + 逐步回归关联
reason: 先检验感官评分可信度排除主观偏差, PCA消除共线性, 聚类/优势因子给出数据驱动分级, 逐步回归/典型相关分离直接与间接关联, 全程可解释
recommend: 
source: 葡萄酒的质量分析与评价(A335, 2012高教社杯全国大学生数学建模竞赛优秀候选论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2012qgdxssxjmjslwzs/121030/1191829.shtml|2012
confidence: 高
```

---

## ST-301（公开经验库·公开）

```yaml
strategy_id: ST-301
scenario: 房地产/园区规划方案的评价与配比优化；多方(住户/开发商)利益冲突平衡；带税务阈值与回报率约束的资源分配
strategy: Excel基线核算 + 整数规划(满意度最大) + 双目标分层序列法 + 税务临界微调
reason: 先核算摸清现状与免税临界点, 整数规划给出满足参与意愿的可执行配比, 分层序列法在满意度约束下最大化回报率, 税务微调配比可合法增收益
recommend: 
source: 1D11001-D001 众筹筑屋规划方案设计(2015高教社杯全国大学生数学建模竞赛国家一等奖论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2015qgdxssxjmjslwzs/210621/1700975.shtml|2015
confidence: 高
```

---

## ST-302（公开经验库·公开）

```yaml
strategy_id: ST-302
scenario: 开放小区/路网通行能力评价；交通微循环仿真与政策效应评估；缺数据场景下的多指标评价体系构建
strategy: AHP评价体系 + 元胞自动机/交通流仿真 + 控制变量法分条件权衡
reason: AHP对数据要求低且纳入主观感受, 仿真给出前后延时差定量证据, 控制变量法区分正/负效应成立的条件
recommend: 
source: 小区开放对道路通行能力的影响(2016年高教社杯全国大学生数学建模竞赛一等奖, 南京大学)|https://simlab.nju.edu.cn/0f/8d/c30091a462733/page.htm|2016
confidence: 高
```

---

## ST-303（公开经验库·公开）

```yaml
strategy_id: ST-303
scenario: 体育赛程/排班的公平性评价；多指标利弊综合排序；带平衡约束的场次结构优化
strategy: 四因素指标体系 + 主客观组合赋权 + TOPSIS排序 + 0-1规划优化
reason: 四因素覆盖休息均匀/疲劳/对手/客场, 组合赋权兼顾主客观, TOPSIS直观给出最有利/最不利队, 0-1规划在行列平衡约束下优化场次安排
recommend: 
source: nba赛程的分析与评价数学建模论文(2008高教社杯D题获奖论文)|https://www.wenkub.com/doc/357211.html|2008
confidence: 高
```

---

## ST-304（公开经验库·公开）

```yaml
strategy_id: ST-304
scenario: 预报/模拟方法的精度评价；栅格-站点数据的空间一致性检验；多模型对比与选型
strategy: 插值对齐 + 多误差指标(均值/方差/平方和根) + 公众满意度(分级) + 多检验一致性
reason: 先插值解决空间错位, 多误差指标兼顾精度与稳定性, 分级满意度贴合公众, 多种统计检验交叉验证使结论稳健
recommend: 
source: 雨量预报方法的评价模型(伍利兵等, 工程数学学报2005; 2005高教社杯全国大学生数学建模竞赛全国一等奖)|https://blog.sciencenet.cn/upload/blog/file/2008/11/20081112222131814898.pdf|2005
confidence: 高
```

---

## ST-305（公开经验库·公开）

```yaml
strategy_id: ST-305
scenario: 招聘/人岗匹配与录用分配；多指标人才综合评价；资源-需求的双向最优分配
strategy: AHP综合权重 + 志愿双向选择 + 0-1整数规划最优分配
reason: AHP融合笔试(按r)/面试/岗位要求得客观权重, 志愿矩阵尊重意愿, 0-1规划在类容量与一人一岗约束下最大化总权重, 全局最优
recommend: 
source: 公务员招聘(2004年高教社杯获得者论文: 层次分析法+0-1整数规划)|https://wenku.baidu.com/view/18f658bf68ec0975f46527d3240c844769eaa08e.html|2004
confidence: 高
```

---

## ST-306（公开经验库·公开）

```yaml
strategy_id: ST-306
scenario: 运动器材(球棒/球拍)甜区评价；碰撞动力学 + 结构振动分析；产品参数(材料/质量分布)优化
strategy: 碰撞动力学(含转动) + 梁振动模态(节点) + 多目标(出球速度/手振)甜区评价
reason: 碰撞动力学解释出球随击球点变化, 振动模态定位节点(手感好), 二者交集即真实甜区; 再比较材料参数回答延伸问题
recommend: 
source: 2010 MCM Problem A 棒球甜区建模论文(自然振动模态与节点分析)|https://www.doc88.com/p-4334721419338.html|2010
confidence: 高
```

---

## ST-307（公开经验库·公开）

```yaml
strategy_id: ST-307
scenario: 跨项目/跨时代人物综合排名；体育成就评价；主客观赋权多指标排名
strategy: 按赛季长度标准化有效胜率 + 难度/时代校正 + 综合指数排名 + 敏感性分析
reason: 标准化解决赛季长度不可比, 校正解决项目/时代差异, 综合指数量化'最佳', 敏感性分析保证稳健
recommend: 
source: 2011 MCM Problem A: College Coaching Legends (COMAP官方成绩页, 杰出奖含北大/清华)|https://www.contest.comap.com/undergraduate/contests/mcm/contests/2011/results|2011
confidence: 中
```

---

## ST-309（公开经验库·公开）

```yaml
strategy_id: ST-309
scenario: 组织人力资本评价；人才结构动态优化；员工流失风险管理
strategy: 模糊综合评价(部门契合) + 复杂网络动态(Lyapunov/Pajek) + 多流失率情景 + 敏感性优化
reason: 模糊评价量化契合, 动态网络刻画演化, 情景分析定预算, 敏感性定位最关键因素, 配置有的放矢
recommend: 
source: Strategic Human Resource Management and Corporate Performance (ICM 2015 MCM C 人力资本论文, scirp)|https://scirp.org/journal/paperabs.aspx?paperid=90134|2015
confidence: 高
```

---

## ST-310（公开经验库·公开）

```yaml
strategy_id: ST-310
scenario: 储罐/容器容积标定与罐容表制定；几何反演与未知参数识别(由实测数据反演几何/物理参数)；小角度刚体变位修正；含系统误差的实测数据标定
strategy: 机理积分建模 + 双修正项(系统误差比例修正 + 三次多项式残差修正) + 最小二乘/等间距穷举参数反演
reason: 积分保证任意液位下容积精确; 第一修正项消除系统误差(实测=0.9663×理论), 第二修正项(三次多项式)消除拟合残差, 西电队两次修正后误差<0.04%; 反演从实测数据标定变位参数, 机理与数据结合。该组合可复用于任意规则/近规则罐体的容积标定与变位识别
recommend: 
source: 储油罐的变位识别与罐容表标定(2010高教社杯全国大学生数学建模竞赛A题一等奖, 重庆大学 王建等)|https://www.docin.com/p-476164223.html|2010
confidence: 高
```

---

## ST-311（公开经验库·公开）

```yaml
strategy_id: ST-311
scenario: 航天器/探测器动力下降软着陆轨道设计；含终端约束的燃料最优控制轨迹规划；基于高程图的避障制导律；初始误差传播量化(敏感度/协方差分析)
strategy: 二体/开普勒轨道建模 + 6阶段分段最优控制(主减速段Pontryagin/遗传算法燃料最优) + 高程图K均值聚类避障 + 三次样条轨迹拼接 + 协方差敏感度分析
reason: 分段将复杂全局最优拆为可解子问题; 主减速段燃料最优制导使末速精确达57m/s且燃耗约1055.39kg; 避障用K均值聚类+栅格化从高程图稳健选安全落点(最优坐标(1275,1000)); 敏感度分析(水平位移对推力0.189)量化初始误差保证落点精度。该组合可复用于任意动力下降软着陆任务
recommend: 
source: 嫦娥三号软着陆轨道设计与控制策略(2014高教社杯全国大学生数学建模竞赛优秀论文选登, 东南大学 吉张鹤轩等)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2014qgdxssxjmjslwzs/211022/1700790.shtml|2014
confidence: 高
```

---

## ST-312（公开经验库·公开）

```yaml
strategy_id: ST-312
scenario: 可折叠/可展开结构(家具、机构)设计；参数化几何建模与加工参数提取；多目标结构优化(稳固·用材·加工)；边缘线/轮廓的数学拟合
strategy: 空间几何不变量建模(开槽长度=平铺与折叠两态钢筋-铰链距离差) + 桌脚边缘线柱面相交+三次多项式(Poly33)拟合 + 多目标非线性规划(开槽最短/黄金梯形稳固/用材最少)
reason: 以几何不变量求开槽长度保证桌面平整(单侧序列20.093→0cm); 柱面交线+Poly33拟合给出可制造的边缘线; 多目标规划在桌高53cm、木条19根约束下协同优化稳固与用材。该组合可复用于任意平板折叠/展开结构设计
recommend: 
source: 创意平板折叠桌(2014高教社杯全国大学生数学建模竞赛三等奖论文, 开槽长度序列与几何模型)|https://m.renrendoc.com/p-23651209.html|2014
confidence: 高
```

---

## ST-313（公开经验库·公开）

```yaml
strategy_id: ST-313
scenario: 天文现象时间/方位反演(月出月落、日出日落)；球面三角坐标变换(赤道系↔地平系)；模糊文学/自然概念的数学量化定义；多地点情景可发生性推广
strategy: 模糊概念量化(月高角10°–15°、黄昏后太阳≤-18°) + 太阳赤纬解析公式 + 赤道→地平坐标变换求日落/月出时刻 + 共线约束(农历十五)缩域判定
reason: 先量化诗意阈值使问题可算; 赤纬公式(δ=0.3723+23.2567Sinθ+0.1149Sin2θ-0.1712Sin3θ-0.758Cosθ+0.3656Cos2θ+0.0201Cos3θ)给出季节变化; 坐标变换保证时刻物理正确; 共线约束把全年搜索缩到每月十三~十八六天, 既高效又具物理解释。国一论文据此判定2016年乌鲁木齐不能发生该情景。可复用于任意地点日期的天文事件反演
recommend: 
source: 月上柳梢头(2015高教社杯全国大学生数学建模竞赛C题, 含国一优秀论文 PDF)|https://yuque.com/mcm/cumcm/om8nox|2015
confidence: 高
```

---

## ST-314（公开经验库·公开）

```yaml
strategy_id: ST-314
scenario: 单点系泊/浮标系统设计；浮式结构静力优化与张力控制；锚链选型与张紧设计；海洋结构约束(不触底/不拉直)反向设计
strategy: 分单元静力+力矩平衡建模 + 悬链线/集中质量法描述锚链 + 以吃水或重物球质量为变量二分/迭代搜索 + 以钢桶<5°、锚链末端夹角<16°为硬约束反向设计
reason: 逐单元平衡保证位形物理正确; 悬链线刻画链形; 用吃水或重物质量作单变量搜索, 在18m水深下使钢桶夹角<5°、锚链夹角<16°(加重物2280kg得4.47°/15.97°); 极端工况用控制单一变量先定Ⅴ型锚链再联优长度与重物。可复用于任意单点系泊/浮标设计
recommend: 
source: 2016年数学建模竞赛A题优秀论文(系泊系统的设计, 基于力学分析)|https://www.bodocs.net/doc/4920463175.html|2016
confidence: 高
```

---

## ST-315（公开经验库·公开）

```yaml
strategy_id: ST-315
scenario: CT/MRI等投影成像重建；系统几何参数标定(旋转中心/探测器间距/扫描方向)；积分方程反演；模板法标定(已知基准物体)
strategy: 模板法最小二乘标定(旋转中心+探测器间距+扫描方向) + Radon投影建模 + 滤波反投影(FBP)重建 + 吸收系数非负约束
reason: 已知模板(2椭圆+1圆)提供几何基准, 用Lambert-Beer+最小二乘反推旋转中心(9.3040,6.2149)与探测器间距0.2768mm; Radon变换保证投影正确; FBP抑制噪声伪影稳定重建; 非负约束保证物理可解释。可复用于任意平行束CT系统标定与重建
recommend: 
source: 基于单目标优化模型和图像重建算法的CT系统研究(2017国赛国家一等奖A题优秀论文)|https://m.renrendoc.com/p-84299505.html|2017
confidence: 高
```

---

## ST-316（公开经验库·公开）

```yaml
strategy_id: ST-316
scenario: 防护服/隔热层热设计；多层介质瞬态导热求解；厚度反向优化(安全约束下最薄/最舒适)；边界对流系数由实测反演
strategy: 多层一维瞬态导热PDE(傅里叶+能量守恒) + 向后差分/追赶法数值求解 + 由实测反演对流系数h + 步长枚举Ⅱ/Ⅳ层厚度满足皮肤≤47°C约束
reason: 瞬态PDE刻画真实升温过程避免安全误判; 界面热流连续保证多层耦合正确; 实测反演h≈8.64202校准边界; 枚举搜索在65°C下得Ⅱ层19.20mm、80°C下得Ⅱ层21.9mm+Ⅳ层6.4mm满足约束。可复用于任意多层隔热服/墙体热设计
recommend: 
source: 2018年高教社杯全国大学生数学建模竞赛A题优秀论文(高温作业专用服装设计, 多层织物热传递模型)|https://max.book118.com/html/2024/0523/8137051072006072.shtm|2018
confidence: 高
```

---

## ST-317（公开经验库·公开）

```yaml
strategy_id: ST-317
scenario: 燃油/液压共轨压力稳定控制；ODE流量-压力动力学建模；阀时序/凸轮转速优化；多执行器(多喷孔+减压阀)闭环控制
strategy: 质量守恒ODE(d(ρV)/dt=进−出) + 状态方程dp/dρ=E/ρ(附件3分段拟合E(p)) + 二分/网格搜索阀开启时长或凸轮角速度使周期净流量为零 + 问题3定差策略+减压阀闭环
reason: 可压缩状态方程刻画真实压力动态; 由附件3拟合E(p)保证ρ(p)正确; 搜索使单向阀开启0.285ms(100MPa)或凸轮ω=2.99°/ms压力稳定; 多喷孔用定差+减压阀闭环消除偏差。可复用于高压共轨/液压系统压力稳定控制
recommend: 
source: 2019全国大学生数学建模竞赛(高教社杯)A题题解(高压油管的压力控制)|https://www.cnblogs.com/Mayfly-nymph/p/11753977.html|2019
confidence: 高
```

---

## ST-318（公开经验库·公开）

```yaml
strategy_id: ST-318
scenario: 多智能体协同控制(同心鼓/多旋翼无人机编队)；刚体平动+转动耦合动力学；球-鼓/物体碰撞建模；误差下的反馈调整策略
strategy: 同心鼓刚体动力学(平动牛顿第二定律+绕两轴转动定律, 欧拉小角度分解) + 球-鼓碰撞(恢复系数e∈[0.6,0.85]的动量/能量守恒) + 以耗能最小为目标的最优拉绳策略 + 现实误差下从拉力/倾斜/站位三方面闭环调整
reason: 小角度转动分解使三维问题降为竖直平动+两独立转动, 可解; 恢复系数保证碰撞真实; 理想策略以耗能最小达稳态周期颠球; 现实下据倾斜角(0.1s达0.2124°–0.4123°)调整拉力与站位使球回竖直。可复用于多旋翼/多体协同控制
recommend: 
source: “同心协力”策略研究(2019高教社杯全国大学生数学建模竞赛B题, 同心鼓颠球, 赛题全文)|https://www.icourse163.org/forum/1237117709/topic-1342038971.htm|2019
confidence: 高
```

---

## ST-319（公开经验库·公开）

```yaml
strategy_id: ST-319
scenario: 回流焊/SMT炉温曲线设计；一维瞬态导热仿真；工艺窗口(制程界限)优化；多目标(覆盖面积/对称性)优化
strategy: 一维瞬态导热+牛顿冷却(集总参数)建模 + 由实测最小二乘拟合热扩散参数 + 以217°C以上覆盖面积(及对称性)最小为目标、模拟退火/爬山优化4组温区温度与带速 + 制程界限(升温≤3、峰值217–249、降温≤6)为硬约束
reason: 瞬态导热刻画板上温度滞后; 实测拟合τs=52.10s等参数保证模型可信; 约束下优化使217°C以上面积最小(≈406)且对称(指标21.69), 兼顾焊接质量与产能(带速可达90–95cm/min)。可复用于任意回流焊/热处理炉温工艺设计
recommend: 
source: 国赛优秀论文2020年A题: 基于一维热传导方程的炉温曲线机理模型研究|http://www.madio.net/forum.php?mod=viewthread&tid=490621&extra=page%3D1&ordertype=1|2020
confidence: 高
```

---

## ST-320（公开经验库·公开）

```yaml
strategy_id: ST-320
scenario: 应急设施/服务点选址(消防站、急救点、便利店)；警力/运维人员的管辖范围划分；路网覆盖优化与突发封锁调度
strategy: Floyd最短路预处理 + 多目标0-1整数规划(管辖划分与新增平台) + 0-1指派(minimax)封锁调度
reason: 最短路把图距离量化成响应时间基础; 0-1规划在覆盖唯一性、3km时限、工作量均衡下精确求解; minimax指派保证'全面封锁'由最慢环节决定, 已验证最快封锁8.015min、平均响应约0.97min、新增5平台变异系数降至0.1526。
recommend: 
source: Python小白的数学建模课-A1.国赛赛题类型分析(含2011B题)|https://blog.csdn.net/youcans/article/details/117410678|2011
confidence: 中
```

---

## ST-321（公开经验库·公开）

```yaml
strategy_id: ST-321
scenario: 规则矩形碎纸片/文档的自动拼接复原；扫描件行列对齐与重排；基于边缘相似度的图匹配排序
strategy: 边界灰度匹配(左右/上下)+ 行特征聚类(二层筛选)+ 少量人工干预
reason: 官方优秀论文用此法: 问题一纯边界匹配即可完全自动复原(耗时0.38/0.43s); 问题二横纵切用二层筛选得中文正确率90.4%、英文65.1%; 问题三加两次特征匹配精度更高。方法可解释、可追溯到竞赛组委会登载原文。
recommend: 
source: 碎纸片的拼接复原-西南交通大学(2013高教社杯全国大学生数学建模竞赛优秀论文选登)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700228.shtml|2013
confidence: 高
```

---

## ST-322（公开经验库·公开）

```yaml
strategy_id: ST-322
scenario: 厂区/园区多巡检点路线规划与排班；电力/管道/安防周期性巡逻调度；带周期上限与休息约束的人员排班
strategy: 最短路径(图论) + 周期≤35min分区 + 多目标规划(人数最少且均衡) + 三班/错时轮倒
reason: 可完整访问的解题文档与国一等奖论文验证了该法: 问题一5路线/5人、均衡度0.35(优化至0.15); 问题二6人(首班11人轮换进餐); 问题三错时省1人至4人。方法可解释、数字可追溯到公开文档。
recommend: 
source: 2017年国赛高教杯数学建模D题巡检线路的排班解题全过程文档及程序|https://blog.csdn.net/weixin_43292788/article/details/142359829|2017
confidence: 高
```

---

## ST-323（公开经验库·公开）

```yaml
strategy_id: ST-323
scenario: 大型场馆/地铁/楼宇应急疏散规划；多层建筑出口分配与瓶颈识别；适应多威胁的动态疏散仿真
strategy: 2D Island-Bridge降维 + 改造Dijkstra(α出口上限/危险区/Visual Range) + Danger Index瓶颈识别 + 3D元胞自动机验证
reason: O奖#1900007据此给出五层疏散时间约7,7,17,9,16分钟, 并用3D Pathfinder验证瓶颈在楼梯与出入口; 方法可解释、数字可追溯到公开拆解页与论文。
recommend: 
source: 2019 ICM Problem D 拆解笔记(Paper #1900007, O奖分析)|http://pzrain.github.io/COMAP/paper/2019D|2019
confidence: 高
```

---

## ST-324（公开经验库·公开）

```yaml
strategy_id: ST-324
scenario: 医院科室床位调度与入院排程；带固定服务日约束的排队系统；急诊优先+普通病人FCFS的混合排队
strategy: M/M/79排队刻画 + 优先级控制FCFS(按病种×手术日匹配度) + 离散事件仿真评价
reason: 多源优秀论文验证: FCFS利用率仅58.4%, 优先级+FCFS升至83.0%, 一等奖M/M/79使平均逗留Ws从9.788降到8.217、日均出院5.72升到6.28。数字可追溯到公开论文。
recommend: 
source: 眼科医院一等奖论文(2009高教社杯B题, M/M/79排队模型)|https://max.book118.com/html/2017/0923/134812897.shtm|2009
confidence: 高
```

---

## ST-325（公开经验库·公开）

```yaml
strategy_id: ST-325
scenario: 收费广场/匝道合流区设计；车道减少(汇入)瓶颈优化；兼顾吞吐、安全、成本的交通设施规划
strategy: M/G/K排队论基线 + 几何/图论合并模式设计 + VISSIM仿真验证(轻/重交通) + 三目标(吞吐/事故/成本)权衡
reason: 5篇O奖一致采用'简单模型+仿真验证'; 56731蜂窝方案减面积/降事故/提吞吐, 68303用PCA定位延迟→吞吐、合并点队列→成本、合并点数→事故。数字可追溯到公开O奖总结。
recommend: 
source: 美赛2017b题优秀论文总结(5篇O奖: 56731/68303/69427/70174/70545)|https://www.cnblogs.com/clover-blog/p/14322409.html|2017
confidence: 高
```

---

## ST-326（公开经验库·公开）

```yaml
strategy_id: ST-326
scenario: 灾情/应急巡检巡游路线规划；VRP多车分组路径优化；分区均衡调度(限时均衡)
strategy: Floyd最短路 → 以县中心O为根的最短路树干枝聚类分组 → 组内二边逐次修正法求哈密顿回路 → 组间按均衡度α=(max-min)/max微调
reason: 先按道路树的6条干枝把53节点(17个乡镇+35个村庄+县中心O)归并到同组, 保证每组从O出发可经主干往返; 组内用二边逐次修正法在TSP回路反复去交叉降总长; 最后按均衡度调组使各组总路程接近, 同时满足'天数最短'与'各组天数尽量均衡'两目标。
recommend: 
source: 建模案例:最佳灾情巡视路线(1998 CUMCM B)|https://www.bodocs.net/doc/413476347.html|1998
confidence: 高
```

---

## ST-327（公开经验库·公开）

```yaml
strategy_id: ST-327
scenario: 灾区/失联区域全覆盖搜救路径规划；网格区域多队协同搜索；限时(48h)覆盖任务的人力/分组优化
strategy: 均衡分派(面积比=人数比) + 组内S型全覆盖扫描 + 以最远队员耗时为总耗时 + 多组按通信设备并行
reason: 结构化分区使任务天然均衡、无重复; 蛇形扫描可解析计算耗时; 锁定最远队员耗时避免误判; 按卫星电话分组并行显著缩短总时间。主流结果: 20人最短约48.94h(超48h), 21人加'自由人'补位可47.41h内完成, 50人3组约20.24h。
recommend: 
source: 地面搜索(2008高教社杯全国大学生数学建模竞赛C题)|https://www.bodocs.net/doc/307175172.html|2008
confidence: 高
```

---

## ST-328（公开经验库·公开）

```yaml
strategy_id: ST-328
scenario: 星际/极端环境移民社会系统设计；劳动力-教育-平等政策优化；长周期可持续系统规划(双目标权衡)
strategy: 边界界定(排除医疗) → 系统动力学长周期演进 → 网络科学多层可扩展结构 → 多目标(GDP/幸福感) Pareto 权衡 → 发射窗口节律约束
reason: 先锁边界避免越界; 系统动力学刻画100年人口-经济演化; 网络科学保证小/大群体可扩展与多层动态; 多目标权衡给出可采纳的政策集而非单点。赛题给定 Population Zero=10,000、100年跨度、GDP/幸福双目标与收入/教育/平等三维, 模型须对齐这些锚点。
recommend: 
source: ICM 2017 Problem F: Migration to Mars: Utopian Workforce of the 2100 Urban Society|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/problems|2017
confidence: 高
```

---

## ST-329（公开经验库·公开）

```yaml
strategy_id: ST-329
scenario: 公交/班车全天发车调度；分时运力配置(高峰平峰差异化)；供需匹配多目标优化(企业效益 vs 用户满意度)
strategy: 客流曲线压缩(D(t)/B(t)) → 按客流分5段 → 多目标规划(满载率/候车/拥挤)加权求满意解 → 多组权重求Pareto定最少车数
reason: 把海量站点客流压成两根时间曲线, 发车间隔即曲线面积划分, 可操作; 分段匹配高峰平峰; 多目标显式权衡公司与乘客; Pareto比较保证稳健。典型结果: 上行间隔5/2/4/3/15分、下行10/2/5/3/8分, 52辆/534次/满载率82.094%/抱怨0.91%; 国一等奖解57辆/载客率82.5%/均等2.55分。
recommend: 
source: 公交车调度方案的优化模型(2001年B题)|http://www.bodocs.net/doc/4a17008335.html|2001
confidence: 高
```

---

## ST-330（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-330
scenario: 新能源充裕（基准情景）
strategy: 储能边际价值极低，主杠杆是'新能源优先+外送'
reason: 储能容量 α 缩放几乎不改变成本/消纳率
recommend: 常态下不必过度投资储能，优先外送消纳
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-331（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-331
scenario: 新能源出力降至约 0.6× 及以下
strategy: 必须依赖储能放电+外送削峰，储能从'可有可无'变'不可或缺'
reason: 成本/峰值随新能源出力陡升（η=0.4 时成本 +9e8、峰值 1906MW）
recommend: 设置新能源出力临界预警，触发储能优先调度
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-332（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-332
scenario: 新能源受限下的跨域迁移
strategy: 调度器'调整哪些任务跨域'而非'扩大跨域规模'
reason: 压力场景下迁移结构调整 14.7%，但跨域总占比几乎不变(69.86%→70.05%)
recommend: 压力时重排迁移结构，而非简单扩大迁移比例
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-333（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-333
scenario: 小时级算力负荷预测
strategy: 用可解释谐波回归，残差交由后续优化吸收
reason: 短时波动噪声大，深度模型在该粒度无优势
recommend: 预测模块保持轻量，避免为精度牺牲可解释性
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---


---

## ST-334（公开经验库·公开）

```yaml
strategy_id: ST-334
scenario: 学术/社交网络影响力评价；关键节点(枢纽/核心)识别；社区发现与网络鲁棒性
strategy: SNA多中心度 + PCA综合影响力 + 社区发现 + 鲁棒性检验
reason: 多中心度刻画不同角色, PCA融合成统一指数, 社区发现研究团伙, 鲁棒性检验验证关键节点
recommend: 
source: 2014 MCM Problem C: Networks|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## ST-335（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-335
scenario: 生产/质检/拆解多阶段成本优化；统计决策；装配网络
strategy: 序贯贝叶斯验收 + 期望净成本闭式 + DAG递推 + 蒙特卡洛校验的四段式方法链
reason: 覆盖从抽样检验到网络装配的全链条，且每段都有可解释闭式或数值证据
recommend: 
source: 2024高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2024
confidence: 中
source_quality: 高
memory_type: human_replay
```

---

## ST-336（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
strategy_id: ST-336
scenario: 几何覆盖/条带覆盖/测线或航迹规划类题（多波束测深、侧扫声呐、农业/测绘条带扫描）
strategy: 沿等深线（走向）布设 + 按沿线最窄覆盖宽度自适应定距，保证无漏测且总长最短；用栅格化覆盖率/漏测率量化
reason: 沿走向使覆盖宽度沿线恒定，是条带覆盖最优布设方向；按 W_min 定距把漏测风险压到 0
recommend: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-337（公开经验库·公开）

```yaml
strategy_id: ST-337
scenario: 小样本催化/工艺优化，收率=转化率×选择性
strategy: 曲线拟合先行(逻辑斯蒂+高斯倒U)得物理可解释的温度—响应关系，再用观测+拟合峰值作主证据
reason: 避免响应面平滑低估，峰值位置准确且与观测吻合
recommend: 
source: 2021 高教社杯全国大学生数学建模竞赛 B 题（乙醇偶合制备 C4 烯烃） | 2021
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-338（公开经验库·公开）

```yaml
strategy_id: ST-338
scenario: 多因素效应排序
strategy: 标准化回归效应量 + 随机森林置换重要性双重量化
reason: 兼顾线性效应量与非线性重要性，结论稳健
recommend: 
source: 2021 高教社杯全国大学生数学建模竞赛 B 题（乙醇偶合制备 C4 烯烃） | 2021
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-339（公开经验库·公开）

```yaml
strategy_id: ST-339
scenario: 补充实验设计(仅 5 次)
strategy: GPR 响应面 + UCB 采集函数，目的驱动选取确认峰值/扫描/插值/空缺/低温开发
reason: 兼顾开发与探索，给出量化不确定性，理由可解释
recommend: 
source: 2021 高教社杯全国大学生数学建模竞赛 B 题（乙醇偶合制备 C4 烯烃） | 2021
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-340（公开经验库·公开）

```yaml
strategy_id: ST-340
scenario: 路网上设施选址/管辖分配/围堵
strategy: 先算全源最短路矩阵，再以指派/集合覆盖/时间窗分层求解
reason: 
recommend: 
source: cumcm2011B题 | 交巡警服务平台的设置与调度 | 2011
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-341（公开经验库·公开）

```yaml
strategy_id: ST-341
scenario: 覆盖类硬阈值约束
strategy: 用最近归属+硬阈值，超时节点单列用增量选址消除
reason: 
recommend: 
source: cumcm2011B题 | 交巡警服务平台的设置与调度 | 2011
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-342（公开经验库·公开）

```yaml
strategy_id: ST-342
scenario: 交付格式
strategy: 优先满足用户指定格式(本题Word)，公式图片嵌入
reason: 
recommend: 
source: cumcm2011B题 | 交巡警服务平台的设置与调度 | 2011
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## ST-343（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 多约束运输/装箱题，数据量大
strategy: 数据侧写先判定主导约束（重量 vs 体积），再决定建模方向
reason: 货源总重 6299.5t ≫ 三机总载重 78t(80.8 倍)，重量约束主导
recommend: 主动在问题一暴露"三机运力不足"而非强行装满体积
signal: 总重量与总载重比 > 50 倍
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-344（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 平衡约束（载重平衡）难严格满足
strategy: 利用赛题允许"货物可跨舱分布"，按舱最大载重比例切分实现严格平衡
reason: 严格平衡靠比例切分可解析实现，避免贪心单舱塌陷
recommend: 初版贪心导致单舱塌陷 bug → 改按舱最大载重比例切分
signal: 贪心解出现单舱超载/塌陷
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-345（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 题目要求"可靠性/服务水平"但没给明确度量
strategy: 把可靠性诠释为服务水平约束，给出分位策略（95%/70% 分位）
reason: 把模糊的"可靠性"转成可计算的约束，验证"可靠性↑→利润↓"权衡
recommend: 报童模型里用临界分位 CR≈0.61~0.67；高变异货用经验分布求期望
signal: 可靠性要求无明确量化口径
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-346（外部交付·低温防护服）

```yaml
scenario: 物理传热/热平衡题
strategy: 建模前先固定单位制（统一 W/m2K），附件表头单位逐项核对
reason: 物理题单位制混乱导致公式/常数错误是高频坑
recommend: 先定单位制再列式；附件表头单位逐项核对
source: 华数杯2021A|低温防护服御寒|外部交付(2026-08-14)
confidence: 高
```

---

## ST-347（公开经验库·公开）

```yaml
strategy_id: ST-347
scenario: 异构多序列需求预测
strategy: 按验证集RMSE逐序列自适应选型(Ridge/GBRT)，多候选+验证集择优
reason: 各序列统计特征差异大，统一模型必有偏
recommend: 预测环节先做序列画像(平稳/尖峰)再选型
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## ST-348（公开经验库·公开）

```yaml
strategy_id: ST-348
scenario: 多目标冲突决策
strategy: 先帕累托前沿扫描，再熵权TOPSIS客观赋权选贴近度最高解
reason: 线性加权会丢失权衡面信息，主观赋权不可复现
recommend: 多目标优先'Pareto+TOPSIS'组合，权重用熵权
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## ST-349（公开经验库·公开）

```yaml
strategy_id: ST-349
scenario: 离散+连续混合大规模优化
strategy: 双层协同：上层离散边际打分配置任务，下层连续LP优化能源，EMA阻尼更新影子价格迭代
reason: 单层混合模型组合爆炸，双层拆分保求解效率
recommend: 混合整数难题优先尝试'离散/连续分层+影子价格迭代'
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## ST-350（公开经验库·公开）

```yaml
strategy_id: ST-350
scenario: 储能效益论证
strategy: 终端SOC状态回归校验(期末=初始值)+充放电效率/电价组合灵敏度
reason: 储能收益可被'透支期末电池'造假，SOC校验让净收益可信
recommend: 储能模型必加期末SOC回归与组合参数扰动检验
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## ST-351（公开经验库·公开）

```yaml
strategy_id: ST-351
scenario: 线长估计有理想基准RSMT
strategy: 查找表修正逼近
reason: 分段按接口数修正误差可量化
recommend: 先统计接口数分布再定修正表
source: 2024华数杯B|VLSI自动布局|CM2401166
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## ST-352（公开经验库·公开）

```yaml
strategy_id: ST-352
scenario: 有布局可视化需求
strategy: 原始vs优化并排对比图
reason: 肉眼可见的改善最有说服力
recommend: 同坐标系同图例
source: 2024华数杯B|VLSI自动布局|CM2401166
confidence: 高
source_quality: 中
memory_type: paper_extract
```

## ST-308

```yaml
problem_type: 优化
situation: 灵敏度分析,参数扰动,物理校验
strategy: 对关键参数做扰动并观察目标变化趋势，与物理直觉对照验证模型的准确性与灵敏性
reason: 参数-结果的单调关系是否符合实际，是检验模型合理性最直接的证据
recommend: 当定日镜宽度增加了3米时，单位镜面面积年平均输出功率减少了0.12千瓦每平方米，年平均输出功率增加了30兆瓦
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-353

```yaml
problem_type: 优化
situation: 吸收塔位置自由变量需先压缩搜索域
strategy: 用光学效率云图与太阳方位规律先验锁定选址区间（Y轴负半轴），再进入优化
reason: 把自由度从圆盘内任意点压到一维区间，同时给出可解释的物理依据
recommend: 为了使定日镜反射的太阳光尽可能多的指向集热器中心，本文制定了吸收塔选址策略：吸收塔应建设在正南方向上，且位于定日镜场所在的圆形区域内。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-354

```yaml
problem_type: 优化
situation: 数千面定日镜的坐标与数目需随优化参数变化而确定
strategy: 同心圆分区+各区独立排布规则，给定少量参数唯一生成全部镜面坐标
reason: 把布局变成参数化生成流程，使优化搜索只需搜布局参数而非逐镜坐标
recommend: 分区域同心圆规划策略为：以吸收塔中心为圆心绘制同心圆，将定日镜场划分为多个不同的区域，每个区域内划分为多层，定日镜底座安装在同心圆上。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-355

```yaml
problem_type: 机理
situation: 为加速计算需降低栅格分辨率
strategy: 粗栅格(2*2)与细栅格结果对比，用量化偏差(<2%)证明加速方案可靠
reason: 计算精度与速度的折中给出数值依据，而非拍脑袋设定，审阅者信服
recommend: 为加快运行速度，经检验，可仅将镜面分为2*2 的栅格进行相关指标计算，与上一问题计算结果偏差在2% 以内。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-356

```yaml
problem_type: 机理
situation: 机理模型无实验数据可对照
strategy: 改变指标计算时刻重画散点图，检验峰值移动是否与太阳视运动规律一致
reason: 用物理规律(太阳视运动)作为外部参照系验证模型的真实性与准确性
recommend: 上述结果表明，散点图的峰值移动规律与太阳视运动规律一致。说明模型可以较为真实准确地反映定日镜场镜面反射、阴影遮挡、集热器截断等光学现象。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-357

```yaml
problem_type: 优化
situation: 问题三宣称优化但结果目标不升反降
strategy: 优化前后必须对比目标值：外围镜升高6m后单位面积功率由0.5725降至0.5062，与优化叙事矛盾
reason: 优化必须带来目标改善，否则会被评委判定为模型失效或过度包装
recommend: 6.2：将最外围定日镜安装高度升高为6m；表9：年平均光学效率0.496428083、单位面积功率0.506192417，均低于问题二
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-358

```yaml
problem_type: 优化
situation: 真实海域地形起伏大、整体建模困难时
strategy: 可视化初貌→等深线分区（矩形边平行等深线）→分区域最小二乘拟合坡面→拟合不佳再细分→复用前问模型逐区求解
reason: 把整体难题降解为多个同构子问题，拟合失败的信号（均方误差过大）作为再划分依据，闭环自洽
recommend: 对于矩形III，采用最小二乘目标函数时其均方误差过大，拟合效果不好……选择将区域III划分为新的两个区域III、V（原文问题四）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-359

```yaml
problem_type: 优化
situation: 需要为求解结果提供可信性证据时
strategy: 用模拟退火等独立随机算法重解同一模型，对比测线位置与目标值的绝对、相对误差，再做参数灵敏度分析
reason: 独立算法结果一致并量化误差，构成比自评更有力的验证链
recommend: 仿真结果与求解结果的相对误差和绝对误差很小，这也证明了我们模型的可靠性以及求解结果的精确性（原文问题三验证）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-360

```yaml
problem_type: 通用
situation: 多小问由易到难,模型层层递进
strategy: 问题间层层递进,后问复用前问模型并明确联系与区别
reason: 体现模型可传递性与主线一致性,评审容易跟随并认可完整性
recommend: 本文对于几个问题的模型建立具有可传递性，从问题1 到问题4 是对模型的层层递进，通过增加变量和增加复杂程度来使模型由特殊到一般，使模型更加有层次。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-361

```yaml
problem_type: 预测
situation: 离散单波束数据连续化
strategy: 随机森林拟合深度场，任意点取深度坡度梯度
reason: 连续函数支撑逐点几何计算，精度与效率兼得
recommend: 将已有点的数据作为训练集，建立一个用于辅助计算的机器学习模型，这样，我们给定坐标后，便可以给出精确的数据。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-362

```yaml
problem_type: 优化
situation: 后续问题的优化结构与前一问题同构时
strategy: 识别问题仍为同类优化问题，直接复用前一问题的求解算法（模拟退火）并调整约束
reason: 同构问题复用成熟求解链，省去重复开发且前后逻辑自洽，工作量与出错率双降
recommend: 在问题三的背景下，本题仍然为优化问题中的线性规划问题，所以本题仍选用模拟退火模型求解。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-363

```yaml
problem_type: 统计
situation: Bayesian模型MCMC估计后
strategy: 用轨迹图+核密度+自相关+MC误差四件套做收敛诊断
reason: 证明后验链收敛可靠，是贝叶斯建模的标准检查流程
recommend: MC 链有一定的自相关性，但滞后10 期后，自相关性消退为0。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-364

```yaml
problem_type: 预测
situation: 数据具有明显周期性与趋势性，需要多步预测
strategy: 先用ARIMA/岭回归/灰色预测等统计模型做基线试错，效果差再升级LSTM，形成基线-升级叙事
reason: 展示模型选型过程与数据依据，避免直接上深度学习显得无理由
recommend: 首先采用ARIMA、岭回归、灰色预测模型等统计时间序列模型进行预测，结果发现效果较差。因此本文采用LSTM 长短时记忆网络模型进行预测。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-365

```yaml
problem_type: 优化
situation: 评估优化决策方案的效果
strategy: 将决策方案收益与历史收益区间对比，量化提升幅度
reason: 历史对比让抽象的目标函数值变成可感知的改进，增强结论说服力
recommend: 而采用本文中确定的补货定价方案均大于1740 元，最大可达1810 元，可以对收益额产生一个明显的提升效果。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-366

```yaml
problem_type: 优化
situation: 问题三需在单品层复用问题二的需求-价格关系时
strategy: 承接前问Prophet回归结果建立单品销量-定价线性关系，构造混合整数二次规划并用遗传算法求解
reason: 跨问复用已建立的预测关系，避免重复建模，且问题链条层层递进逻辑自洽
recommend: 结合问题二的Prophet 模型，建立出各单品蔬菜销量与其定价之间的线性关系。基于上述分析，构建出混合整数二次规划，并结合遗传算法，获得相应的最优解
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-367

```yaml
problem_type: 优化
situation: 需要把多阶段占用折算成年化产出与缺口
strategy: 用'羊栏天数'统一单位折算年化产出与缺口
reason: 把数量×时长/容量跨状态累加, 单位可解释, 估算快速
recommend: 1、计算一整个周期(229 天) 每批次的母羊数量x 时需要的总羊栏天数
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-368

```yaml
problem_type: 预测
situation: 多问递进型题目,问与问需衔接
strategy: 后一问显式引用前一问结论作为输入，形成递进故事线
reason: 问题二规律→问题三预测→问题四方案，环环相扣，全文逻辑闭环
recommend: 问题三是根据问题二水沙通量的变化规律研究预测其变化趋势。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-369

```yaml
problem_type: 评价
situation: 结论需体现决策价值,反事实推演
strategy: 用“如果不…会…”反事实推演强化结论意义
reason: 反事实情境突出调水调沙的必要性，把数值结论升华为决策建议
recommend: 如果不进行调水调沙，七月达到的峰值会更高，河道快速变窄变浅，不利于排水排沙。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-370

```yaml
problem_type: 预测
situation: R/S分析的Hurst指数结论需先验证再用于预测
strategy: 检验段结论必须与已知实际情况对照相符，才宣布模型可靠并进入预测段
reason: 用事实校验模型输出，把可靠性论证从口头变成可检查的证据链
recommend: 在模型检验阶段，首先，水通量H=0.3317<0.5，预示水流量未来变化将与过去总体趋势相反，这与实际情况相符。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-371

```yaml
problem_type: 优化
situation: 采样监测需同时满足成本最小与信息覆盖
strategy: 用相邻月通量差分度量单月信息量，月均值作约束，总监测次数作目标，建0-1规划
reason: 信息量度量有明确物理含义，0-1规划保证方案全局最优且可复现
recommend: 以月均信息量为约束条件，以总监测次数最小为目标，建立0-1 规划模型。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-372

```yaml
problem_type: 统计
situation: 四问层层递进,方法高度复用
strategy: 问题一建立识别+去噪+拟合三步基础流水线,后续各问显式复用并标注"使用问题一/问题二的方法"
reason: 用明确的复用引用串起四问,展示方法的扩展性与工程化思路,评委易跟读
recommend: 首先采用问题一方法识别出每组数据不同曲线段的形状。然后基于问题二水平直线的旋转量对各组数据进行校正
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-373

```yaml
problem_type: 统计
situation: 多次测量倾斜角估计
strategy: 选稳定线段作校准线,10次斜率均值作标准角再逐次作差
reason: 均值当标准可消除单次放置偏差,差值即每次倾斜角
recommend: 计算工件2的倾斜程度，我们需要一条校准线（一次方程直线）。在十次工件2的测量中，选取每个轮廓的第3段进行校准，分别计算出其斜率k和倾斜角α
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-374

```yaml
problem_type: 统计
situation: 旋转校正与平移量估计结果需量化验证
strategy: 用误差平方和的平均检验校正参数准确性, 并作图对比
reason: 数值误差加图形对比双重证据, 校验刚体变换参数
recommend: 通过误差平方和的平均检验上面得到的倾斜角度和水平偏移量的准确性
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-375

```yaml
problem_type: 统计
situation: 校正与修正的效果需要量化验证
strategy: 用柱状图逐项对比两状态参数, 并辅以回归显著性检验验证拟合
reason: 图形对比加统计检验双重证据, 支撑'差异可接受'的结论
recommend: 为了比较两种测量状态下工件1各项参数计算值之间的差异，我们将两次表格得到的数据利用柱状图进行对比
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-376

```yaml
problem_type: 优化
situation: 实际切割精度为0.1米
strategy: 按精度将4.8~12.6米离散为79种长度规格，决策变量为各规格计数（整数）
reason: 离散化使切割方案成为整数线性规划，模型可解且符合实际测量精度
recommend: 取定精度为0.1米，将4.8米～12.6米划分为79种长度规格；根据参数与要求、用户目标值范围等条件，建立基于79种长度规格的切割损失最小整线性规划模型
source: 2021国赛D|连铸切割的在线优化模型|D017
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-377

```yaml
problem_type: 优化
situation: 对比分析,初始方案,调整方案
strategy: 用表对比两种方法的初始方案与调整后方案的贴近程度，选择更优方法
reason: 用客观贴近度比较替代主观判断，为方案取舍提供依据
recommend: 对比方法一与方法二求解出的新一段钢坏的初始切割方案，发现方法一所得出的切割方案更贴近调整后的切割方案，因此方法一比方法二更加满足题目要求，更加优化。
source: 2021国赛D|连铸切割的在线优化|D026
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-378

```yaml
problem_type: 参数迁移的切割优化
situation: 用户目标值和目标范围改变（问题三进阶）
strategy: 直接复用问题二算法，仅把程序中的目标值与目标范围参数改掉即可得新最优方案
reason: 算法参数化设计使其可迁移，避免为每个情景重复建模
recommend: 对（1）用户目标值：8.5米目标范围：8.0-9.0米，修改算法中的目标值和目标范围，由问题二所设计数学算法可得下表
source: 2021国赛D|连铸切割的在线优化|2021_D_D034
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-379

```yaml
problem_type: 机理
situation: 模型正确性需要独立验证
strategy: 用受迫振动稳定周期等于激励周期的物理规律做检验
reason: 利用与建模过程独立的物理先验验证，方差小即模型可靠
recommend: 此类物体振动稳定后的振动周期应与波浪激励的周期接近，故据此检验模型的正确性
source: 2022国赛A|波浪能装置输出功率优化设计|A001
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-380

```yaml
problem_type: 机理
situation: 计算过程含近似需评估结果可靠性
strategy: 对关键参数施加±1%扰动观察结果偏差
reason: 扰动分析量化结果对参数误差的敏感性，偏差小即可信
recommend: 对其添加±1%的扰动，并对扰动前后偏差作图进行结果可靠性检验。
source: 2022国赛A|波浪能装置输出功率优化设计|A001
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-381

```yaml
problem_type: 优化
situation: 非线性阻尼无解析解,问题四双参数寻优
strategy: 先以已验证的数值积分法替代解析法,再画全局遍历图定位峰值区,按单调性固定一参数后做局部细化遍历
reason: 全局粗搜+局部细搜的两阶段策略控制计算量,先证明数值法精度再跨问复用,叙事连贯
recommend: 经过研究数据发现PTO对于单调变化，因此取得最大PTO时旋转阻尼系数的值为100000。再对取100000时的局部追历求解。
source: 2022国赛A|波浪能装置输出功率最大化模型|A022
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-382

```yaml
problem_type: 机理
situation: 多目标位置调整
strategy: 三步分层调整:先基准角度→再其余角度→最后长度
reason: 角度与长度解耦,每步闭式可解,层层递进
recommend: 步骤一：利用问题一（1）的定位模型，调整同一圆周上的三架无人机的相对位置接近理想位置关系。步骤二：以步骤一中三架无人机为参照系，利用问题一（1）的定位模型，调节余下无人机的角度坐标，使之接近理想相对位置，输出角度调节量
source: 2022国赛B|无人机遂行编队飞行中的纯方位无源定位|B030
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-383

```yaml
problem_type: 机理
situation: 迭代调整量需判方向
strategy: 调整量正负号赋予方向意义(向心/离心)
reason: 符号携带方向信息,方案可直接执行
recommend: 当4p为正，则向圆心方向调整长度距离，当e为负，则背离圆心方向调整长度距离
source: 2022国赛B|无人机遂行编队飞行中的纯方位无源定位|B030
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-384

```yaml
problem_type: 优化
situation: 估价函数选择
strategy: 以L2 loss（各无人机到预期位置距离平方和）作为估价函数
reason: 平方损失偏向优化离标准位置较远的点，加快收敛速度
recommend: 在确定估价函数时采用了L2loss函数提高精确度。这种方法极大地改进了短视的缺点。
source: 2022国赛B|基于计算几何与带阈值启发式搜索的无人机无源定位模型|B035
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-385

```yaml
problem_type: 优化
situation: 灵敏性分析,正态扰动,全局误差,鲁棒性
strategy: 对精确点施加正态扰动生成多组数据集，做全局误差分析检验鲁棒性
reason: 弥补单组数据无法检验模型的不足
recommend: 对飞行阵列的精确点进行服从正态分布的微小扰动，取十组数据集进行全局误差分析
source: 2022国赛B|基于局部最优模型的无人机位置调整策略与仿真定位|B086
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-386

```yaml
problem_type: 未知样本类别鉴别
situation: 用已建模型鉴别未知玻璃文物类别并分析敏感性
strategy: 直接复用问题二训练好的决策树分类，再用Q型聚类交叉检验；按判别阈值与样本成分差异大小论证敏感性
reason: 模型复用加独立方法交叉验证，可信度更高
recommend: 使用于间题三中训练好的决策树进行分美，并通过Q型聚美法进行交叉检验，分别对风化以及米风化坡璃进行敏感度分析
source: 2022国赛C|基于成分数据的古代玻璃制品的成分分析与鉴别|2022_C_C155
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-387

```yaml
problem_type: 概率统计
situation: 通道存在失败概率需评估方案效果
strategy: 双通道并传提升成功概率后按二项分布计算期望
reason: 概率建模把随机约束转化为可验证的量化指标
recommend: 因此需要两个副站同时向任一主站传输或分别向不同主站各传输两次，此时概率为96%
source: 2022国赛D|气象报文信息卫星通信传输|D999
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-388

```yaml
problem_type: 优化
situation: 服务水平与库存成本此消彼长,需两阶段平衡
strategy: 先用强化参数法保障服务水平,再用联合调整法压缩库存,不达标时以改进版(乘1.1)兜底至85%以上
reason: 两阶段各司其职,先保下限再降库存,最后按规则兜底,形成可复用的调整闭环
recommend: 若经历"强化参数法"和"联合调整法"步骤之后，平均库存量低于30件/周，且平均服务水平低于85%的，令生产计划=预测需求-上周库存+上周缺货×1.1，使得平均库存量小幅增加：但平均服务水平达到85%。
source: 2022国赛E|基于时间序列预测的物料生产安排模型|E014
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-389

```yaml
problem_type: 优化
situation: k延迟情形下β参数取值需说明权衡
strategy: 解释β>1与0≤β≤1两种取值的后果,给出k=2时的建议区间1.3~1.4
reason: 把参数含义翻译成业务后果(库存多还是缺货多),读者能理解参数取舍而非黑箱
recommend: 如果想要提高服务水平，就让B>1，β越大，生产越多，库存越多：反之，如果想要降低库存量，就让0β≤1，β越小，生产越少，库存越少，但缺货量提高，服务水平就越小。
source: 2022国赛E|基于时间序列预测的物料生产安排模型|E014
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-390

```yaml
problem_type: 优化
situation: 灵敏度分析,参数扰动,物理校验
strategy: 对关键参数做扰动并观察目标变化趋势，与物理直觉对照验证模型的准确性与灵敏性
reason: 参数-结果的单调关系是否符合实际，是检验模型合理性最直接的证据
recommend: 当定日镜宽度增加了3米时，单位镜面面积年平均输出功率减少了0.12千瓦每平方米，年平均输出功率增加了30兆瓦
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-391

```yaml
problem_type: 优化
situation: 吸收塔位置自由变量需先压缩搜索域
strategy: 用光学效率云图与太阳方位规律先验锁定选址区间（Y轴负半轴），再进入优化
reason: 把自由度从圆盘内任意点压到一维区间，同时给出可解释的物理依据
recommend: 为了使定日镜反射的太阳光尽可能多的指向集热器中心，本文制定了吸收塔选址策略：吸收塔应建设在正南方向上，且位于定日镜场所在的圆形区域内。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-392

```yaml
problem_type: 优化
situation: 数千面定日镜的坐标与数目需随优化参数变化而确定
strategy: 同心圆分区+各区独立排布规则，给定少量参数唯一生成全部镜面坐标
reason: 把布局变成参数化生成流程，使优化搜索只需搜布局参数而非逐镜坐标
recommend: 分区域同心圆规划策略为：以吸收塔中心为圆心绘制同心圆，将定日镜场划分为多个不同的区域，每个区域内划分为多层，定日镜底座安装在同心圆上。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-393

```yaml
problem_type: 机理
situation: 为加速计算需降低栅格分辨率
strategy: 粗栅格(2*2)与细栅格结果对比，用量化偏差(<2%)证明加速方案可靠
reason: 计算精度与速度的折中给出数值依据，而非拍脑袋设定，审阅者信服
recommend: 为加快运行速度，经检验，可仅将镜面分为2*2 的栅格进行相关指标计算，与上一问题计算结果偏差在2% 以内。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-394

```yaml
problem_type: 机理
situation: 机理模型无实验数据可对照
strategy: 改变指标计算时刻重画散点图，检验峰值移动是否与太阳视运动规律一致
reason: 用物理规律(太阳视运动)作为外部参照系验证模型的真实性与准确性
recommend: 上述结果表明，散点图的峰值移动规律与太阳视运动规律一致。说明模型可以较为真实准确地反映定日镜场镜面反射、阴影遮挡、集热器截断等光学现象。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-395

```yaml
problem_type: 优化
situation: 问题三宣称优化但结果目标不升反降
strategy: 优化前后必须对比目标值：外围镜升高6m后单位面积功率由0.5725降至0.5062，与优化叙事矛盾
reason: 优化必须带来目标改善，否则会被评委判定为模型失效或过度包装
recommend: 6.2：将最外围定日镜安装高度升高为6m；表9：年平均光学效率0.496428083、单位面积功率0.506192417，均低于问题二
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-396

```yaml
problem_type: 优化
situation: 真实海域地形起伏大、整体建模困难时
strategy: 可视化初貌→等深线分区（矩形边平行等深线）→分区域最小二乘拟合坡面→拟合不佳再细分→复用前问模型逐区求解
reason: 把整体难题降解为多个同构子问题，拟合失败的信号（均方误差过大）作为再划分依据，闭环自洽
recommend: 对于矩形III，采用最小二乘目标函数时其均方误差过大，拟合效果不好……选择将区域III划分为新的两个区域III、V（原文问题四）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-397

```yaml
problem_type: 优化
situation: 需要为求解结果提供可信性证据时
strategy: 用模拟退火等独立随机算法重解同一模型，对比测线位置与目标值的绝对、相对误差，再做参数灵敏度分析
reason: 独立算法结果一致并量化误差，构成比自评更有力的验证链
recommend: 仿真结果与求解结果的相对误差和绝对误差很小，这也证明了我们模型的可靠性以及求解结果的精确性（原文问题三验证）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-398

```yaml
problem_type: 通用
situation: 多小问由易到难,模型层层递进
strategy: 问题间层层递进,后问复用前问模型并明确联系与区别
reason: 体现模型可传递性与主线一致性,评审容易跟随并认可完整性
recommend: 本文对于几个问题的模型建立具有可传递性，从问题1 到问题4 是对模型的层层递进，通过增加变量和增加复杂程度来使模型由特殊到一般，使模型更加有层次。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-399

```yaml
problem_type: 预测
situation: 离散单波束数据连续化
strategy: 随机森林拟合深度场，任意点取深度坡度梯度
reason: 连续函数支撑逐点几何计算，精度与效率兼得
recommend: 将已有点的数据作为训练集，建立一个用于辅助计算的机器学习模型，这样，我们给定坐标后，便可以给出精确的数据。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-400

```yaml
problem_type: 优化
situation: 后续问题的优化结构与前一问题同构时
strategy: 识别问题仍为同类优化问题，直接复用前一问题的求解算法（模拟退火）并调整约束
reason: 同构问题复用成熟求解链，省去重复开发且前后逻辑自洽，工作量与出错率双降
recommend: 在问题三的背景下，本题仍然为优化问题中的线性规划问题，所以本题仍选用模拟退火模型求解。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-401

```yaml
problem_type: 统计
situation: Bayesian模型MCMC估计后
strategy: 用轨迹图+核密度+自相关+MC误差四件套做收敛诊断
reason: 证明后验链收敛可靠，是贝叶斯建模的标准检查流程
recommend: MC 链有一定的自相关性，但滞后10 期后，自相关性消退为0。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-402

```yaml
problem_type: 预测
situation: 数据具有明显周期性与趋势性，需要多步预测
strategy: 先用ARIMA/岭回归/灰色预测等统计模型做基线试错，效果差再升级LSTM，形成基线-升级叙事
reason: 展示模型选型过程与数据依据，避免直接上深度学习显得无理由
recommend: 首先采用ARIMA、岭回归、灰色预测模型等统计时间序列模型进行预测，结果发现效果较差。因此本文采用LSTM 长短时记忆网络模型进行预测。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-403

```yaml
problem_type: 优化
situation: 评估优化决策方案的效果
strategy: 将决策方案收益与历史收益区间对比，量化提升幅度
reason: 历史对比让抽象的目标函数值变成可感知的改进，增强结论说服力
recommend: 而采用本文中确定的补货定价方案均大于1740 元，最大可达1810 元，可以对收益额产生一个明显的提升效果。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-404

```yaml
problem_type: 优化
situation: 问题三需在单品层复用问题二的需求-价格关系时
strategy: 承接前问Prophet回归结果建立单品销量-定价线性关系，构造混合整数二次规划并用遗传算法求解
reason: 跨问复用已建立的预测关系，避免重复建模，且问题链条层层递进逻辑自洽
recommend: 结合问题二的Prophet 模型，建立出各单品蔬菜销量与其定价之间的线性关系。基于上述分析，构建出混合整数二次规划，并结合遗传算法，获得相应的最优解
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-405

```yaml
problem_type: 优化
situation: 需要把多阶段占用折算成年化产出与缺口
strategy: 用'羊栏天数'统一单位折算年化产出与缺口
reason: 把数量×时长/容量跨状态累加, 单位可解释, 估算快速
recommend: 1、计算一整个周期(229 天) 每批次的母羊数量x 时需要的总羊栏天数
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-406

```yaml
problem_type: 预测
situation: 多问递进型题目,问与问需衔接
strategy: 后一问显式引用前一问结论作为输入，形成递进故事线
reason: 问题二规律→问题三预测→问题四方案，环环相扣，全文逻辑闭环
recommend: 问题三是根据问题二水沙通量的变化规律研究预测其变化趋势。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-407

```yaml
problem_type: 评价
situation: 结论需体现决策价值,反事实推演
strategy: 用“如果不…会…”反事实推演强化结论意义
reason: 反事实情境突出调水调沙的必要性，把数值结论升华为决策建议
recommend: 如果不进行调水调沙，七月达到的峰值会更高，河道快速变窄变浅，不利于排水排沙。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-408

```yaml
problem_type: 预测
situation: R/S分析的Hurst指数结论需先验证再用于预测
strategy: 检验段结论必须与已知实际情况对照相符，才宣布模型可靠并进入预测段
reason: 用事实校验模型输出，把可靠性论证从口头变成可检查的证据链
recommend: 在模型检验阶段，首先，水通量H=0.3317<0.5，预示水流量未来变化将与过去总体趋势相反，这与实际情况相符。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-409

```yaml
problem_type: 优化
situation: 采样监测需同时满足成本最小与信息覆盖
strategy: 用相邻月通量差分度量单月信息量，月均值作约束，总监测次数作目标，建0-1规划
reason: 信息量度量有明确物理含义，0-1规划保证方案全局最优且可复现
recommend: 以月均信息量为约束条件，以总监测次数最小为目标，建立0-1 规划模型。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-410

```yaml
problem_type: 机理
situation: 驱动端缩放求全链速度上限
strategy: 先证明速度同倍率变化命题，把各把手不超限求龙头速度化为单参数比例缩放。
reason: 用线性齐次性小命题避免重新求解全模型，逻辑严谨且省去重复计算
recommend: 【命题】若某板凳在某位置时一个把手速度变成k倍，则另一个把手的速度也变成k倍。
source: 2024国赛A|基于几何模型的舞龙队位置和速度分析|A016
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-411

```yaml
problem_type: 机理
situation: 整链状态求解
strategy: 同一时刻所有把手由龙头逐节递推，位置链与速度链共用同构递推结构。
reason: 递推只依赖前一节，复杂度随板数线性增长，两链复用同一距离约束
recommend: 因此只需要从第一块板凳开始沿着螺线依次向后逐个递推，就能得到每块板凳的具体位置。
source: 2024国赛A|基于几何模型的舞龙队位置和速度分析|A016
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-412

```yaml
problem_type: 优化
situation: 一维单目标优化且目标不连续
strategy: 变步长遍历法：先大步长粗扫定位极小区间，再小步长精扫，结合极径-螺距图锁定边界值
reason: 碰撞检测函数为0/1跳变，梯度类方法失效；遍历法稳健、易配图解释
recommend: 以大步长4p=1cm进行首次追历，每个p都有对应的恰不发生碰撞的时刻t与极径r
source: 2024国赛A|基于自标优化的板凳龙形态调节|A053
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-413

```yaml
problem_type: 机理
situation: 隐式非线性方程无法解析求解，需逐时刻求根
strategy: 把迭代公式中的隐式方程写成求根形式，用二分法/十分法求零点
reason: 二分法稳定收敛、易实现，适合批量逐时刻逐节求解
recommend: 本文首先通过调整螺距得到两个分别使龙头前把手中心落在调头空间内部和外部的螺距，再通过十分法，精确求解使龙头前把手中心恰好位于边界上的螺距。
source: 2024国赛A|基于几何模型的板凳龙运动路径问题|A163
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-414

```yaml
problem_type: 优化
situation: 单调性,一维参数,可行性判定,二分法,精度控制
strategy: 先分析目标随参数单调性，再把反问题转为二分法加可行性仿真判定
reason: 单调性保证区间收缩正确，每次迭代只需一次仿真判定，精度由区间长度直接控制
recommend: 设定最小螺距的初始搜索区间，设定最小螺距的下界l=0.3m和上界r=0.55m，精度设为6=10-4m……通过二分法求解得最小螺距为0.4000m，误差控制在0.000lm之内。
source: 2024国赛A|板凳龙表演的行进路径与速度控制|A178
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-415

```yaml
problem_type: 机理
situation: 模型给出的速度结果需要独立手段交叉验证
strategy: 用数值微分（小时间间隔位移/时间）重算平均速度，与解析求导结果对比
reason: 两种独立求解路径相互印证，且说明解析法得到的是更精确的瞬时速度
recommend: 我们采用数值微分法，通过选取小时间间隔（如0.01s），计算把手前后位移，再据此计算出平均速度，在时间间隔趋于0的情况下，该平均速度应收敛于我们使用求导算出的速度。
source: 2024国赛A|基于动态搜索的“板凳龙”运动状态及路线研究|A242
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-416

```yaml
problem_type: 机理
situation: 碰撞时刻这类临界值需要直观确认
strategy: 绘制临界时刻整条龙的模拟状态图，确认恰好处于相撞临界且其余位置无碰撞
reason: 可视化在几何直观上印证答案正确，同时反过来验证了“最内圈先碰撞”的假设
recommend: 求解结束后，我们作出了t=412.473838s时板竞龙状态的模拟图像，如图8。不难发现，此时龙头的外侧前顶点Ao恰要与外创板相撞，正处于临界情况，而整条龙其他位置均未有碰撞出现。
source: 2024国赛A|基于动态搜索的“板凳龙”运动状态及路线研究|A242
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-417

```yaml
problem_type: 优化
situation: 16种0-1决策组合的方案表达
strategy: 把决策组合编号化，用“方案编号表”+结果表直接引用编号
reason: 避免每处重复写“检测零配件1、不检测零配件2……”长句，表格紧凑可检索
recommend: 表2 16种决策方案及对应编号表（编号001-016，按是否检测零配件1/2、是否检测成品、是否拆解四维组合）
source: 2024国赛B|生产过程中的决策优化设计|B159
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-418

```yaml
problem_type: 优化
situation: 6种情况×16种方案的利润期望值矩阵
strategy: 结果矩阵表+涂色标注每情况最大值，图下文字解释图例
reason: 最大值一眼可辨，避免读者在大表中自行比对
recommend: 表中标黄部分表示每种情况下单件合格成品利润期望的最大值，其对应的决策编号即为该情况下的最终决策方案。
source: 2024国赛B|生产过程中的决策优化设计|B159
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-419

```yaml
problem_type: 预测
situation: 问题四（贝叶斯）结果与问题二结果对比
strategy: 用黄/绿双色标注决策与上一问一致或不一致，并文字总结差异
reason: 直观展示引入不确定性后决策是否改变，支撑“贝叶斯影响小”的结论
recommend: 表中涂色部分表示每种情况的平均利润最大值·黄色表示平均利润最大值出现的决策与第二问中一致，绿色表示平均利润最大值出现的决策与第二问中不一致
source: 2024国赛B|生产过程中的决策优化设计|B159
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-420

```yaml
problem_type: 统计
situation: 次品率由抽样估计带有不确定性
strategy: Beta先验+二项似然求后验，取0.95置信区间端点回代二三问模型检验决策是否改变
reason: 把抽样误差对决策的影响量化，'决策不变'的稳健性结论直接增强论文可信度
recommend: 将扰动后的0.95概率置信区间的两个端点值作为新的次品率，重新进行问题二、问题三的操作，结果决策不变（5.4.5概括）
source: 2024国赛B|基于多阶段模拟仿真的生产决策问题|B195
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-421

```yaml
problem_type: 优化
situation: 参数不确定性,鲁棒性检验,3σ准则,最恶劣情形
strategy: 用3σ准则把抽样次品率波动范围定为μ±3σ，取最恶劣情形P=μ+3σ重新求最优决策，并与不同信度下决策分布对比
reason: 输入次品率由抽样得到存在不确定性，最恶劣情形检验能暴露决策对参数波动的敏感度，支撑稳健建议
recommend: 为了使得生产利润在不同情况下最优化、稳定化，考惠在实际次品率P最恶劣条件下，即P=μ+3g，不同情况的决策分布。在假设检验95%信度和90%信度下，每种情况的前十个最优决策分布如下图所示
source: 2024国赛B|基于蚁群算法与遗传算法优化的蒙特卡洛模拟在生产决策优化中的应用研究|B196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-422

```yaml
problem_type: 优化
situation: 仅7年小样本数据,需判断变量间相关性方法是否适用
strategy: 先做Shapiro-Wilk正态性检验,拒绝正态后改用Spearman秩相关
reason: 检验先行使方法选择有依据,避免误用要求正态分布与线性关系的Pearson
recommend: S-W检验的结果显示各个变量的显著性P值均小于0.05，水平呈现显著性：拒绝原假设，即各类农作物的种植面积、预期销售量，销售价格、种植成本均不满足正态分布。因此本节选择使用Spearman相关性分析。
source: 2024国赛C|基于差分遗传算法的农作物种植策略优化|C038
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-423

```yaml
problem_type: 统计
situation: 不确定因素描述
strategy: 对随机变化分别用均匀分布和正态分布两种方式刻画
reason: 双分布对比展示模型对分布假设的敏感性
recommend: 对其随机变化分别采用均匀分布和正态分布进行描送，给出了潜在种植风险的定量描述。
source: 2024国赛C|基于优化算法的农作物最优种植模型|C063
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-424

```yaml
problem_type: 优化
situation: 作物互补性
strategy: 定义互补系数对亩产量做修正,体现间作轮作增益
reason: 把农艺互补转成产量修正项,直接改进目标函数
recommend: 当两种作物互补系数达到阔值，则认为该两种作物之间互补性的存在，所以会可以相互提高农作物的亩产量，下面我们对亩产量进行一个修正
source: 2024国赛C|基于优化算法的农作物最优种植模型|C063
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-425

```yaml
problem_type: 优化
situation: 销量、价格、成本随时间波动
strategy: 蒙特卡洛生成100组符合正态分布的随机参数序列，最大化收益期望
reason: 参数不确定下以场景期望度量策略，选抗波动性最强的方案
recommend: 使用蒙特卡落算法生成100组符合正态分布的随机参数序列，使用求解器在随机序列下求出100组种植策略
source: 2024国赛C|基于随机优化的农作物种植策略模型|C094
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-426

```yaml
problem_type: 优化
situation: 进化曲线,收敛判断,极端情况验证
strategy: 以进化曲线趋于平稳判断解收敛，并用极端情况（2023年利润3倍）对比验证方案优越性
reason: 为求解结果提供收敛性与合理性双重证据
recommend: 在这种极端情况下其利润大致为2023年利润的3倍1788万元，而本文方案总利润为：29276719.5元远远大于该值，进一步说明了方案的合理性与优越性。
source: 2024国赛C|基于遗传算法的最优种植策略|C234
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-427

```yaml
problem_type: 多弹阵列协同优化
situation: 9枚深弹同深度阵列投放，至少一枚命中即成功
strategy: 由命中概率随落点距原点增大而减小的单调性证明最优间隔为相切构型a=L+2R、b=W+2R，再沿用问题二表达式对9弹概率求和，数值求最优深度
reason: 利用单调性缩小搜索空间，把多维优化降为一维
recommend: 单枚深弹命中的概率为PA），每枚深弹相互独立，可视PCA）与问题二情况相似，即问题二的大部分关系可以直接在本问中沿用
source: 2024国赛D|反潜航空深弹命中概率的优化问题|2024_D_D033
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-428

```yaml
problem_type: 统计
situation: 判断工作日与非工作日流量是否有差异
strategy: 用方差分析（ANOVA）检验组间差异显著性
reason: 用统计检验代替主观判断，支撑不分工作日建模的决策
recommend: 进一步采用方差分析（ANOVA）分析一周内不同天的交通量是否存在显著差异
source: 2024国赛E|交通流量管控|E010
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-429

```yaml
problem_type: 评价
situation: 管控效果需多指标综合呈现
strategy: 建立车流量变化率、等待时间变化率、车速三个对比模型,给出总量结论(如减少道路车流28%)后逐交叉口举证
reason: 多指标互证+典型案例支撑,评估结论既有总量又有细节,且负面案例亦如实呈现
recommend: 等待时间显示4个交叉口的等待时间大幅缩短，以环东路一纬中路路口为例，管控前后的平均等待时间从7分37秒降至2分43秒，等待时间缩短了64.18%，有效提高了车辆通行效率
source: 2024国赛E|基于多目标优化的交通管理评估分析|E061
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-430

```yaml
problem_type: 评价
situation: 两时期流量对比
strategy: 定义流量密度及变化百分比公式,归一化后对比
reason: 消除天数差异,百分比直观反映管控前后变化
recommend: 流量密度百分比：其中P表示四月的流量密度，P表示五月的流量密度。M可以直观的观测到五月份和四月份的车流量差别。
source: 2024国赛E|基于Python语言的交通流量管控与预测分析|E218
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-431

```yaml
problem_type: 优化
situation: 12维决策空间求解效率低
strategy: 预测拦截点降维：令烟弹中心与导弹位置重合解出自由落体比例与速度，再局部网格搜索微调
reason: 物理先验把搜索空间压到时间t的一维，再用网格微调逼近真最优
recommend: 提出了基于预测拦截点的协同优化算法，将12维决策空间降维处理，显著提升求解效率
source: 2025国赛A|多情形下无人机烟幕遮蔽策略的建模与优化研究|A196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-432

```yaml
problem_type: 统计
situation: 可靠性评估,置信区间,变异系数,逆方差加权
strategy: 用平均值、标准差、不确定度、置信区间和变异系数等统计量评估厚度求解结果的可靠性，并用逆方差加权公式综合两个入射角的结果
reason: 小样本未知方差用t分布构造置信区间，逆方差加权突出高精度样本
recommend: 对厚度组进行了统计分析，计算了平均值、标准差，不确定度、置信区间和变异系数等量。根据表2的计算结果，利用两个入射角下得到的平均厚度和标准偏差，用逆方差公式计算得最终结果。
source: 2025国赛B|红外干涉法测量外延层厚度的建模分析|B060
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-433

```yaml
problem_type: 评价
situation: G值检验,均方误差对比,模型适用性验证
strategy: 通过G值检验和机器学习检验评估多光束效应对实测数据的影响强弱，并用双光束与多光束模型拟合的均方误差对比判断适用模型
reason: G值对应模型间最大相对偏差的定量上界，均方误差直接对比拟合优劣
recommend: 计算得出，收敛后双光束模型的均方误差误差显著大于多光束模型均方误差，可以认为此处适合使用多光束模型进行拟合（表7：双光束模型20.8，多光束模型3.62）。
source: 2025国赛B|红外干涉法测量外延层厚度的建模分析|B060
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-434

```yaml
problem_type: 多光束干涉判定与模型选择
situation: 判断两样品数据是否存在多光束干涉并选择合适模型
strategy: 用相干长度、界面反射率锐度系数F、低吸收、几何分辨四条必要条件判定：硅片条纹呈Airy尖峰且频域含谐波判为显著多光束，用Airy模型；SiC界面反射率仅0.016、高阶项衰减可忽略，沿用两光束模型
reason: 判据先行让模型选择有物理依据，避免过度建模
recommend: 故产生多光束干涉市要满足以下条件：1.相干长度条件：光源相干长度应大于往返光程差...2.反射率条件：界面反射率不能过小...3.低吸收条件...4.儿何与分辨条件
source: 2025国赛B|碳化硅外延层厚度的双光束和多光束干涉法测量研究|2025_B_B157
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-435

```yaml
problem_type: 统计
situation: 模型结构必要性验证
strategy: 似然比检验与显著性检验验证随机项与二次项
reason: 用统计检验支撑模型复杂度决策
recommend: 似然比检验显示，引入随机斜率可显著改善模型拟合（LR=109.44，P≤10⁻¹⁶），加入二次项也带来了显著改进（LR=41.29，P=1.1×10⁻⁹）
source: 2025国赛C|基于混合效应模型的NIPT时点优化与胎儿异常判定|C023
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-436

```yaml
problem_type: 统计
situation: 女胎异常判定与多重比较
strategy: 男胎校准零分布+Z标准化+FDR校正+一致性聚合
reason: 消除批次效应与协变量偏倚，控制假阳性率
recommend: 对残差进行1%winsorize截尾处理后，计算其稳健位置与尺度参数
source: 2025国赛C|基于混合效应模型的NIPT时点优化与胎儿异常判定|C023
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-437

```yaml
problem_type: 优化
situation: BMI分组与时点联合决策需形式化为数学规划
strategy: 以分组数k、分割点集合、各组时点为决策变量,设置有序/时点百分位/最小组规模/分配四类约束,总风险按检测时点分段赋权(早低中中晚高),用GA求解
reason: 把业务要求(准确率、样本量、风险)翻译成约束与目标,风险分级赋权反映临床偏好,优化可复现
recommend: 早期检测（t≤12周）低权重，中期检测（12<1≤27周）中等权重，晚期检测（>27周）高权重。通过最小化风险加权和，实现NIPT策略的风险最优配置。
source: 2025国赛C|基于统计建模与元学习的NIPT检测决策优化与异常识别|C132
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-438

```yaml
problem_type: 机理
situation: 三维立体巷道有落差
strategy: 筛选低于突水位置的端点成平面,BFS找巷道另一端,再平行向上漫延
reason: 把三维问题降维成平面+竖向推进两步,简化求解
recommend: 若筛选出来的端点未在集合内，则通过BFS路径搜索算法寻找与这些端点连接成巷道的另一个端点。接着将模型简化为以形成的平面为基础，从低到高，突水以平行于平面方向向上漫延
source: 2025国赛D|矿井突水水流漫延模型与逃生方案问题|D037
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## ST-439

```yaml
problem_type: 统计
situation: 视频关键点坐标噪声大、有零值
strategy: 线性插补零值异常点，再Savitzky-Golay滤波（窗口7、二阶多项式）平滑
reason: 插补保留趋势，滤波在去抖动同时不扭曲真实轨迹
recommend: 本文采用Savitzky-Golay滤波方法间对数据进行平滑处理。选用二阶多项式拟合，滑动窗口长度设为7顿，对33个关键点坐标进行处理
source: 2025国赛E|基于姿态识别的AI辅助智能体测研究|E030
confidence: 中
source_quality: 中
memory_type: paper_extract
```


---

## ST-440（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 多约束运输/装箱题，数据量大
strategy: 数据侧写先判定主导约束（重量 vs 体积），再决定建模方向
reason: 货源总重 6299.5t ≫ 三机总载重 78t(80.8 倍)，重量约束主导
recommend: 主动在问题一暴露"三机运力不足"而非强行装满体积
signal: 总重量与总载重比 > 50 倍
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-441（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 平衡约束（载重平衡）难严格满足
strategy: 利用赛题允许"货物可跨舱分布"，按舱最大载重比例切分实现严格平衡
reason: 严格平衡靠比例切分可解析实现，避免贪心单舱塌陷
recommend: 初版贪心导致单舱塌陷 bug → 改按舱最大载重比例切分
signal: 贪心解出现单舱超载/塌陷
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-442（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 题目要求"可靠性/服务水平"但没给明确度量
strategy: 把可靠性诠释为服务水平约束，给出分位策略（95%/70% 分位）
reason: 把模糊的"可靠性"转成可计算的约束，验证"可靠性↑→利润↓"权衡
recommend: 报童模型里用临界分位 CR≈0.61~0.67；高变异货用经验分布求期望
signal: 可靠性要求无明确量化口径
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-443（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 多约束运输/装箱题，数据量大
strategy: 数据侧写先判定主导约束（重量 vs 体积），再决定建模方向
reason: 货源总重 6299.5t ≫ 三机总载重 78t(80.8 倍)，重量约束主导
recommend: 主动在问题一暴露"三机运力不足"而非强行装满体积
signal: 总重量与总载重比 > 50 倍
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-444（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 平衡约束（载重平衡）难严格满足
strategy: 利用赛题允许"货物可跨舱分布"，按舱最大载重比例切分实现严格平衡
reason: 严格平衡靠比例切分可解析实现，避免贪心单舱塌陷
recommend: 初版贪心导致单舱塌陷 bug → 改按舱最大载重比例切分
signal: 贪心解出现单舱超载/塌陷
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-445（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 题目要求"可靠性/服务水平"但没给明确度量
strategy: 把可靠性诠释为服务水平约束，给出分位策略（95%/70% 分位）
reason: 把模糊的"可靠性"转成可计算的约束，验证"可靠性↑→利润↓"权衡
recommend: 报童模型里用临界分位 CR≈0.61~0.67；高变异货用经验分布求期望
signal: 可靠性要求无明确量化口径
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-446（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 多约束运输/装箱题，数据量大
strategy: 数据侧写先判定主导约束（重量 vs 体积），再决定建模方向
reason: 货源总重 6299.5t ≫ 三机总载重 78t(80.8 倍)，重量约束主导
recommend: 主动在问题一暴露"三机运力不足"而非强行装满体积
signal: 总重量与总载重比 > 50 倍
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-447（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 平衡约束（载重平衡）难严格满足
strategy: 利用赛题允许"货物可跨舱分布"，按舱最大载重比例切分实现严格平衡
reason: 严格平衡靠比例切分可解析实现，避免贪心单舱塌陷
recommend: 初版贪心导致单舱塌陷 bug → 改按舱最大载重比例切分
signal: 贪心解出现单舱超载/塌陷
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-448（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 题目要求"可靠性/服务水平"但没给明确度量
strategy: 把可靠性诠释为服务水平约束，给出分位策略（95%/70% 分位）
reason: 把模糊的"可靠性"转成可计算的约束，验证"可靠性↑→利润↓"权衡
recommend: 报童模型里用临界分位 CR≈0.61~0.67；高变异货用经验分布求期望
signal: 可靠性要求无明确量化口径
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-449（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 多约束运输/装箱题，数据量大
strategy: 数据侧写先判定主导约束（重量 vs 体积），再决定建模方向
reason: 货源总重 6299.5t ≫ 三机总载重 78t(80.8 倍)，重量约束主导
recommend: 主动在问题一暴露"三机运力不足"而非强行装满体积
signal: 总重量与总载重比 > 50 倍
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-450（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 平衡约束（载重平衡）难严格满足
strategy: 利用赛题允许"货物可跨舱分布"，按舱最大载重比例切分实现严格平衡
reason: 严格平衡靠比例切分可解析实现，避免贪心单舱塌陷
recommend: 初版贪心导致单舱塌陷 bug → 改按舱最大载重比例切分
signal: 贪心解出现单舱超载/塌陷
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## ST-451（2021华数杯B PSR验证场）

```yaml
strategy_id: ?
scenario: 题目要求"可靠性/服务水平"但没给明确度量
strategy: 把可靠性诠释为服务水平约束，给出分位策略（95%/70% 分位）
reason: 把模糊的"可靠性"转成可计算的约束，验证"可靠性↑→利润↓"权衡
recommend: 报童模型里用临界分位 CR≈0.61~0.67；高变异货用经验分布求期望
signal: 可靠性要求无明确量化口径
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```
