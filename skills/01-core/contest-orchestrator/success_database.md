---
name: success-database
description: 数学建模竞赛成功经验库。与 failure-database 配对，problem-parser 输出题型时同时检索：命中失败→规避，命中成功→复用方法。
---

# 成功经验库（Success Database）

> 用法：problem-parser 输出 `problem_type` 后，同时查 failure_database（规避）+ 本库（复用）。
> 复盘新比赛 → 成功的解法/策略按此 schema 追加。

---

## SD-001 确定性构造突破搜索瓶颈

```yaml
success_id: SD-001
problem_type: 组合优化 + 几何布图
method: 确定性底置打包（skyline）+ 序列搜索
why_success: 搜索空间小（放置顺序+旋转）；确定性判定可行（装得下即实锤）；绕开树扰动瓶颈
result: n300 死区率从 10.24% 压到 8.73%（545²）
score: 本框架搜索上界，已低于常规裕量 15%
reuse: 推荐（同类紧轮廓布图/装箱问题）
```

## SD-002 消融实验证明方法贡献

```yaml
success_id: SD-002
problem_type: 任意（论文论证）
method: 消融实验（去掉我的改进 → 变差）
why_success: 直接回答"怎么证明你的方法有效"；对比组（B*-Tree 10.24% vs 本文 8.73%）有说服力
result: 论文方法有效性论证充分
reuse: 强制内置（每篇论文必做 ≥1 个消融）
```

## SD-003 穷举 + 整数下界证明

```yaml
success_id: SD-003
problem_type: 小规模组合（异形/枚举类）
method: 全枚举 + 整数面积下界证明最优
why_success: 规模小（4!×4⁴）时穷举最优比启发式更有说服力；下界证明杜绝"是不是最优"质疑
result: Q4 精确最优 6×4=24
reuse: 小规模问题优先考虑精确方法
```

---

## SD-004 多方法交叉验证（FFT/寻峰/余弦/Hilbert）

```yaml
success_id: SD-004
problem_type: 信号处理/反演（光学厚度、频谱类）
method: 四种算法交叉验证（FFT + 条纹寻峰 + 余弦拟合 + 希尔伯特相位）
why_success: 单一方法可能选错峰/撞局部极值，多方法互证排除系统偏差
result: 4 方法结果差 <2%，结果可靠
reuse: 强烈推荐（任何从频谱反演参数的问题）
```

## SD-005 双条件交叉一致性验证

```yaml
success_id: SD-005
problem_type: 任意（实验/测量）
method: 两个独立条件（如入射角 10°/15°）结果互相印证
why_success: 若模型正确，不同条件下应得一致参数；不一致=模型有问题
result: 相对差 1.3%，验证可靠
reuse: 强制内置（实验设计时设计交叉验证条件）
```

---

## SD-6

```yaml
problem_type: 组合优化
method: skyline确定性打包
why_success: 确定性判定可行
reuse: 推荐
success_id: SD-6
```

---

## SD-7

```yaml
success_id: SD-7
problem_type: 华数杯B·布图
method: 两阶段级联：问题二用问题一解出的可行树作 init_root
why_success: 把'固定轮廓不可行'这个搜索器瓶颈，转化成'在可行域内优化目标'；可行树保证起点满足面积约束，SA 只需在可行域内找更好布局，绕开了随机树全局收缩不回去的死结
result: 三组数据全部在 γ=15% 固定轮廓内可行，HPWL=249,135/480,437/687,932
reuse: q2_solve.solve_q2(init_root=Q1解出的root)；实测随机树起步可行率≈0%而 Q1 树起步三组全可行
```

---

## SD-8

```yaml
success_id: SD-8
problem_type: 华数杯B·布图
method: Metropolis 预热：主循环前先只压线长+强越界惩罚，温度2×T0
why_success: 多目标(HPWL/面积/长宽比/越界)同时优化前期互相干扰；预热阶段单目标+高温，先把线长起点做优，等价于'先找好种子再平衡'，符合模拟退火'先粗后细'的直觉
result: n200 HPWL 从约 550k 降到 507k，降约7.8%，超越参考值
reuse: q2_solve.solve_q2(preheat=True)；n_pre=max(12%·n_iter,2000), T_pre=2×T0, PRE_K=100
```

---

## SD-9

```yaml
success_id: SD-9
problem_type: 华数杯B·布图
method: 问题三换搜索空间：天际线底置打包 + 序列/朝向SA + 压紧
why_success: 紧轮廓下'微调坐标'有惩罚墙、无拓扑变化；换成'按放置顺序+旋转'底置摆放，可行性由构造保证，搜索空间变成排列——这是把'搜索布局'变成'搜索顺序'，跳出了 SA 能力瓶颈
result: n300 γ* 从 0.1322 降到 0.0873（降34%）；n200 从 0.1244 降到 0.0969
reuse: q3_skyline_compress.skyline_pack(order,W) + run_sa(ds,W,n_iter,seed) + compact_layout；W 从 545 起
```

---

## SD-10

```yaml
success_id: SD-10
problem_type: 华数杯B·布图
method: 增量 HPWL 累加器：只重算坐标变化模块牵涉的线网
why_success: 扰动只改少数模块坐标，全量重算是浪费；维护 模块→线网 索引后只算变化网，把常数因子压下来
result: 每次迭代从全量扫所有线网改为只重算受影响网，迭代效率大幅提升，支撑 120万+ 迭代数
reuse: HPWLAccumulator：net_index 预建索引；recompute_changed 只重算 affected 网
```

---

## SD-11

```yaml
success_id: SD-11
problem_type: 华数杯B·布图
method: 独立验证脚本 verify_layout.py 复核定稿布局
why_success: 把'论文结果'和'求解器运行'解耦：定稿 CSV 用独立实现复算，证明论文数字有据可查，降低'结果不符'判罚风险
result: 9个布局全部通过无重叠/轮廓/面积守恒独立校验；HPWL 复算与论文逐位一致
reuse: python verify_layout.py n300 03_数据/布局定稿/n300_q3final_layout.csv
```

---

## SD-12

```yaml
success_id: SD-12
problem_type: 华数杯B·布图
method: 支撑材料按规范整理：AI声明+清理+结果复现说明+文件清单
why_success: AI章程强制程序前声明；清理探索脚本/缓存避免'与论文不符'；结果复现说明讲清'论文=定稿CSV、求解器为算法实现'，堵住评委重跑对不上号的漏洞
result: 65文件干净交付包，32个py全部带AI声明，附支撑材料文件清单(附录C)
reuse: 所有 .py 头加 AI 声明注释；清理 __pycache__/探索脚本/存档；README 加结果复现说明
```

---

## SD-13（公开经验库·公开）

```yaml
success_id: SD-13
problem_type: 优化
method: 单目标最优化模型+蒙特卡洛模拟
why_success: 解空间维度庞大，蒙特卡洛可在合理时间内搜索近似最优解；单目标优化直接对应问题要求的最大化单位面积功率
result: 最大化定日镜场单位镜面面积年平均输出热功率
limitations: 蒙特卡洛结果为近似最优而非全局最优；未考虑镜面尺寸连续变化的制造约束；计算阴影遮挡时栅格化带来离散误差
source: 定日镜场优化设计模型——CUMCM 2023 A题国一论文(凌国明,中山大学)|https://blog.csdn.net/weixin_62127011/article/details/149843974|2023
confidence: 高
```

---

## SD-14（公开经验库·公开）

```yaml
success_id: SD-14
problem_type: 决策/博弈
method: 动态规划+蒙特卡洛模拟+纳什均衡博弈
why_success: 问题具有多阶段决策特性，动态规划适合逆向推导；天气不确定时用蒙特卡洛模拟；多玩家时用博弈论
result: 在穿越沙漠游戏中，使玩家到达终点时剩余资金最大化
limitations: 动态规划状态空间随地图复杂度指数增长；蒙特卡洛结果受随机种子影响；纳什均衡假设玩家完全理性
source: 穿越沙漠游戏最佳策略模型的研究与构建——CUMCM 2020 B题国一论文|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## SD-15（公开经验库·公开）

```yaml
success_id: SD-15
problem_type: 预测+优化
method: BP神经网络+多目标规划
why_success: BP神经网络可拟合复杂的非线性映射关系；多目标规划可同时优化过滤效率和过滤阻力两个相互冲突的指标
result: 建立工艺参数与结构变量、产品性能之间的关系，实现过滤效率高且过滤阻力小的优化设计
limitations: BP神经网络存在收敛速度慢、易陷入局部极小的问题；训练样本量较小(仅8组)可能导致过拟合；多目标规划转化为单目标时权重选择具有主观性
source: 插层熔喷非织造材料性能的分析与研究——2022华数杯C题获奖论文|https://blog.csdn.net/qq_63438888/article/details/126426589|2022
confidence: 高
```

---

## SD-16（公开经验库·公开）

```yaml
success_id: SD-16
problem_type: 预测+决策
method: LSTM时间序列预测+MLP多目标线性规划
why_success: LSTM适合捕捉金融时间序列的长期依赖关系；MLP可在预测基础上进行多目标投资组合优化
result: 基于黄金和比特币历史价格，建立预测模型并制定每日投资策略，使投资组合收益最大化且控制风险
limitations: LSTM对极端行情预测能力不足；未考虑市场微观结构(买卖价差、滑点)；假设历史模式在未来延续，存在模型失效风险
source: All That Glitters Is Not Gold: Trading Strategies——MCM 2022 C题O奖论文(北京理工大学)|https://xgb.bit.edu.cn/xgdt/rdxw/b7fad809dbfa46da8a3306a273e300fa.htm|2022
confidence: 高
```

---

## SD-17（公开经验库·公开）

```yaml
success_id: SD-17
problem_type: 优化
method: 理想抛物面模型+多目标规划
why_success: 依据正交变换和几何光学法则，将三维问题简化为二维，建立理想抛物面后通过多目标规划优化促动器调节量
result: 在约束条件下确定理想抛物面，通过调节促动器伸缩量使工作抛物面尽量贴近理想抛物面，获得最佳电磁波接收效果
limitations: 将三维问题简化为二维可能损失部分精度；假设面板为刚性，实际存在微小变形；未考虑风载等动态环境因素
source: FAST主动反射面的形状调节——CUMCM 2021 A题国一论文(武汉大学肖宇曦/李逍迪/刘禹希团队)|https://m.cyol.com/gb/articles/2021-11/25/content_dw3zxI05e.html|2021
confidence: 高
```

---

## SD-18（公开经验库·公开）

```yaml
success_id: SD-18
problem_type: 组合优化与不确定性决策
method: 混合整数线性规划(MILP) + 鲁棒优化/情景优化
why_success: 种植策略涉及离散决策（是否种植、轮作逻辑）与连续变量（种植面积），需用MILP精确建模；问题2/3引入价格、销量、产量不确定性，需用鲁棒优化或情景分析保证方案稳健性
result: 在7年规划期内最大化乡村种植总收益，同时满足土地、轮作、重茬及市场销售约束
limitations: 作物间替代性与互补性量化主观性强；长期预测（7年）不确定性累积大；线性假设可能忽略规模效应与非线性市场反应；求解规模随情景数指数增长
source: 2024年高教社杯全国大学生数学建模竞赛C题：农作物的种植策略|https://cloud.tencent.com/developer/article/2486153|2024
confidence: 高
```

---

## SD-19（公开经验库·公开）

```yaml
success_id: SD-19
problem_type: 物理机理建模与参数优化
method: 两自由度耦合振动模型 + 频域解析法 + 四阶Runge-Kutta时域积分 + 网格搜索优化
why_success: 波浪能装置涉及浮体水动力学与PTO能量提取的强耦合；两自由度模型(浮子垂荡+振子相对运动)能准确刻画能量传递；频域法可快速求得稳态解析解，时域法可处理非线性阻尼；网格搜索保证全局最优
result: 建立波浪能装置（浮子-振子-PTO系统）的运动模型，优化PTO阻尼参数使平均输出功率最大
limitations: 小振幅线性化假设限制了大波浪条件下的适用性；忽略垂荡-纵摇水动力耦合（问题3/4虽引入纵摇但仍假设系数独立）；仅考虑单频规则波，未考虑不规则波谱；PTO模型简化，未考虑液压传动等非线性环节
source: 2022年高教社杯全国大学生数学建模竞赛A题：波浪能最大输出功率设计|https://blog.csdn.net/weixin_47315122/article/details/163511311|2022
confidence: 高
```

---

## SD-20（公开经验库·公开）

```yaml
success_id: SD-20
problem_type: 供应商评价与两阶段供应链优化
method: 熵权-TOPSIS综合评价 + 线性/整数规划 + 双目标贪心优化
why_success: 问题1需多指标综合评价供应商，熵权-TOPSIS客观赋权且可处理多维度；问题2-4为大规模组合优化，线性/整数规划可精确求解，贪心算法在复杂约束下可快速获得可行解
result: 评估402家原材料供应商重要性，制定未来24周最经济的订购方案与损耗最少的转运方案
limitations: 历史数据仅5年，对供应商长期可靠性预测有限；假设供货量与订货量偏差模式稳定，未考虑突发中断；贪心算法可能非全局最优；未完整考虑多周期库存动态与资金占用成本
source: 2021年高教社杯全国大学生数学建模竞赛C题：生产企业原材料的订购与运输|https://blog.csdn.net/peiye500238/article/details/150857323|2021
confidence: 高
```

---

## SD-21（公开经验库·公开）

```yaml
success_id: SD-21
problem_type: 几何定位与编队控制
method: 圆周角定理几何定位 + 最小二乘拟合 + 迭代位置修正算法
why_success: 纯方位测量仅提供角度信息，传统三角测量需距离辅助；圆周角定理可利用圆上三点角度关系反推位置，几何意义明确且计算稳定；迭代修正可逐步收敛到理想编队
result: 在纯方位无源定位条件下，通过接收信号无人机的方位角信息，实现编队中无人机的精确定位与动态调整
limitations: 仅适用于二维平面，未考虑高度偏差；假设测量无噪声，实际中方位角误差会累积；迭代收敛性依赖初始偏差大小，大偏差可能发散；未考虑动态编队中的实时性要求
source: 2022年高教社杯全国大学生数学建模竞赛B题：无人机遂行编队飞行中的纯方位无源定位|https://blog.csdn.net/weixin_43970743/article/details/161582620|2022
confidence: 高
```

---

## SD-22（公开经验库·公开）

```yaml
success_id: SD-22
problem_type: 成分分析与分类鉴别
method: 对应分析 + 多元线性回归 + Kmeans++聚类 + 随机森林/判别分析 + 皮尔逊相关系数
why_success: 问题1需分析分类变量（风化/类型/纹饰/颜色）关联性，对应分析适合处理列联表；风化前后成分预测需回归模型；问题2亚类划分需无监督聚类；问题3未知样品鉴别需监督分类（随机森林/判别分析）；问题4关联分析需相关系数
result: 分析古代玻璃制品化学成分，建立风化关联模型、分类规律模型与未知样品鉴别模型
limitations: 样本量有限（约49件文物，部分有多采样点），聚类与分类模型泛化能力受限；成分数据存在缺失值与截断（未检测），需合理填充或处理；风化机制复杂，线性回归可能无法完全刻画非线性风化过程；颜色类别样本极不均衡，分类准确率低
source: 2022年高教社杯全国大学生数学建模竞赛C题：古代玻璃制品的成分分析与鉴别|https://developer.aliyun.com/article/1578548|2022
confidence: 高
```

---

## SD-23（公开经验库·公开）

```yaml
success_id: SD-23
problem_type: 运动轨迹建模与碰撞检测优化
method: 等距螺线运动学模型 + 刚体碰撞检测 + S形曲线几何优化 + 二分法速度搜索
why_success: 等距螺线（阿基米德螺线）天然描述盘龙形态；刚体碰撞检测可精确判定板凳间干涉；S形双圆弧满足曲率连续且几何约束明确；二分法可高效搜索满足速度约束的最大龙头速度
result: 模拟板凳龙沿等距螺线盘入盘出的运动过程，确定碰撞终止时刻、最小螺距、最优调头曲线及最大安全行进速度
limitations: 二维假设忽略真实三维空间中的板凳倾斜与扭转；碰撞检测仅考虑相邻板凳，未全面考虑非相邻节段可能碰撞；S形双圆弧约束较强，可能存在更优的广义过渡曲线；数值积分步长影响精度，需足够小以保证稳定性
source: 2024年高教社杯全国大学生数学建模竞赛A题：'板凳龙'闹元宵|https://blog.csdn.net/weixin_43292788/article/details/145744176|2024
confidence: 高
```

---

## SD-24（公开经验库·公开）

```yaml
success_id: SD-24
problem_type: 光学效率优化与太阳能集热
method: 蒙特卡洛光线追踪(MCRT) + 空间向量阴影遮挡判定 + 三分查找/遗传算法优化
why_success: 定日镜场光学效率涉及复杂的几何光学问题，阴影遮挡与截断效率难以用解析式表达；蒙特卡洛光线追踪通过随机采样大量光线可精确计算各效率分量；结合优化算法可搜索最优镜场布局参数
result: 建立定日镜场光学效率与输出热功率模型，优化定日镜尺寸、数量与布局使单位面积镜面输出热功率最大
limitations: 蒙特卡洛计算量大，大规模镜场需GPU加速或降采样；太阳辐射模型简化，未考虑云层、大气散射动态变化；定日镜跟踪理想化，忽略机械误差与动态响应滞后；集热器表面温度分布对效率的影响未建模
source: 2023年高教社杯全国大学生数学建模竞赛A题：定日镜场的优化设计|https://pdf.hanspub.org/csa_1544012.pdf|2023
confidence: 高
```

---

## SD-25（公开经验库·公开）

```yaml
success_id: SD-25
problem_type: 质量检测与多阶段生产决策优化
method: 假设检验（二项检验/正态近似）+ 决策树/动态规划 + 贝叶斯更新
why_success: 问题1为经典统计假设检验问题，可用二项检验或正态近似求解最小样本量；问题2-3为离散决策问题，决策树可清晰刻画各阶段决策路径与期望收益；问题4引入抽样不确定性，贝叶斯更新可修正后验次品率
result: 为企业设计零配件抽样检测方案，并在已知次品率情况下对生产各阶段（零配件检测、成品检测、不合格品处理、用户退回处理）作出最优决策
limitations: 假设检验中样本量公式基于大样本近似，小样本时精确度下降；决策树随工序和零配件数量增加呈指数膨胀；未考虑供应商信誉度等先验信息（问题1未用贝叶斯）；实际生产中次品率可能时变，模型为静态
source: 2024年高教社杯全国大学生数学建模竞赛B题：生产过程中的决策问题|https://blog.csdn.net/weixin_43970743/article/details/151194019|2024
confidence: 高
```

---

## SD-26（公开经验库·公开）

```yaml
success_id: SD-26
problem_type: 军事概率建模与命中优化
method: 二维/三维正态概率积分模型 + 截尾正态分布 + 数值积分 + 网格搜索优化
why_success: 命中概率本质为潜艇中心位置落在深弹有效毁伤区域内的概率积分；水平定位误差服从正态分布，深度误差服从截尾正态分布，可通过多重积分精确计算；多深弹布局优化可用网格搜索或遗传算法
result: 建立反潜航空深弹命中潜艇的概率模型，优化投弹落点、定深引信引爆深度及多深弹布局以最大化命中概率
limitations: 潜艇简化为长方体，未考虑指挥台围壳等复杂外形；忽略深弹入水角度与速度对毁伤范围的影响；未考虑多深弹同时命中时的毁伤叠加效应；数值积分在高维时计算量大
source: 2024年高教社杯全国大学生数学建模竞赛D题：反潜航空深弹命中概率问题|https://cjournal.hep.com.cn/2095-3070/CN/10.19943/j.2095-3070.jmmia.2025.02.07|2024
confidence: 高
```

---

## SD-27（公开经验库·公开）

```yaml
success_id: SD-27
problem_type: 气候风险评估与跨学科决策
method: 信息扩散理论(IDT) + 灰色预测模型(GM) + AHP-TOPSIS + 模糊综合评价 + 成本效益分析
why_success: 极端天气保险问题数据稀缺（历史极端事件样本少），信息扩散理论可解决小样本不确定性；灰色预测适合中长期趋势；AHP-TOPSIS整合多维度选址因素；模糊综合评价处理文化遗产的主观价值判断
result: 构建极端天气背景下的保险决策、开发商选址与文化遗产保护的综合评估框架，为气候风险治理提供量化支持
limitations: 信息扩散理论中扩散函数选择主观性强；灰色预测对数据波动性敏感，长期预测精度下降；AHP权重依赖专家判断，不同专家结果差异大；文化遗产货币化估值存在伦理争议
source: 2024年MCM/ICM美赛O奖论文：极端天气保险决策模型(ICM-E题)|https://mcmicm.org.cn/news/1070.html|2024
confidence: 高
```

---

## SD-28（公开经验库·公开）

```yaml
success_id: SD-28
problem_type: 几何建模与路径优化
method: 空间几何解析模型 + 分区优化策略 + 贪心/搜索算法
why_success: 多波束覆盖宽度由换能器开角、水深和海底坡度通过简单三角几何关系确定，解析法精确且高效；复杂地形下分区策略可降低问题维度，配合贪心搜索快速获得近似最优测线布局
result: 建立多波束测深系统的覆盖宽度与重叠率模型，设计满足覆盖率与重叠率约束的最短测线方案
limitations: 平面坡面假设在真实复杂海底地形下误差大；未考虑声线弯曲与多次反射；等间距平行测线约束可能非全局最优；问题4中基于稀疏单波束数据插值存在不确定性
source: 2023年高教社杯全国大学生数学建模竞赛B题：多波束测线问题|https://www.ppmy.cn/news/1095872.html|2023
confidence: 高
```

---

## SD-29（公开经验库·公开）

```yaml
success_id: SD-29
problem_type: 实验设计与工艺优化
method: 多元线性回归 + 响应面法(RSM) + 粒子群优化(PSO) + 神经网络
why_success: 问题1-2需要建立反应性能与多因素（温度、催化剂参数）的定量关系，回归与响应面法可显式表达并识别主效应；问题3-4为优化与实验设计问题，粒子群可高效搜索离散-连续混合空间，神经网络可捕捉非线性交互效应
result: 研究乙醇催化偶合制备C4烯烃的工艺条件，建立转化率、选择性与催化剂组合及温度的关系模型，优化使C4烯烃收率最大化
limitations: 实验数据量有限，高阶响应面可能过拟合；催化剂组合为离散变量，连续优化算法需编码处理；未考虑催化剂失活的动态机理，仅做经验拟合；神经网络黑箱特性导致优化结果可解释性差
source: 2021年高教社杯全国大学生数学建模竞赛B题：乙醇偶合制备C4烯烃|https://blog.csdn.net/weixin_43970743/article/details/161521614|2021
confidence: 高
```

---

## SD-30（公开经验库·公开）

```yaml
success_id: SD-30
problem_type: 信用风险评估与信贷策略优化
method: Soft Voting集成学习 + XGBoost多分类 + 多目标规划 + 系统聚类
why_success: 信用风险评估需高准确率与鲁棒性，Soft Voting集成多种基分类器可降低方差；信誉评级为多分类问题，XGBoost处理表格数据表现优异；信贷策略涉及收益-风险权衡，天然适合多目标规划；系统聚类可识别疫情下不同企业的风险暴露差异
result: 基于企业交易票据数据量化中小微企业信贷风险，制定收益最大、风险最小的信贷策略
limitations: 集成模型对违约样本少的情况可能过拟合；多目标规划需将多目标转化为单目标（加权或约束法），权重主观；系统聚类类别数K需预设；未考虑企业间关联交易导致的信用风险传染
source: 2020年高教社杯全国大学生数学建模竞赛C题：中小微企业的信贷决策|https://blog.csdn.net/2401_82505179/article/details/142721401|2020
confidence: 高
```

---

## SD-31（公开经验库·公开）

```yaml
success_id: SD-31
problem_type: 需求预测与动态定价优化
method: 关联分析(Apriori/相关系数) + 时间序列/回归预测 + 成本加成定价模型 + 整数规划/启发式优化
why_success: 问题1需发现品类/单品间销售关联，关联分析适合；问题2-3需在预测需求基础上做定价与补货决策，成本加成定价符合商超实际，整数规划可处理离散补货量与单品数量约束
result: 分析蔬菜销售规律，建立成本加成定价模型，制定品类/单品级的自动补货与定价策略以最大化商超收益
limitations: 历史销售数据可能受促销、节假日干扰，未完全清洗；损耗率假设近期代表未来，实际可能波动；未考虑竞争对手定价与顾客价格弹性；整数规划在单品级（SKU多）时求解规模大
source: 2023年高教社杯全国大学生数学建模竞赛C题：蔬菜类商品的自动定价与补货决策|https://bbs.pinggu.org/a-4081715.html|2023
confidence: 高
```

---

## SD-32（公开经验库·公开）

```yaml
success_id: SD-32
problem_type: 在线优化与实时调度
method: 多目标规划 + 序贯算法(Sequential Algorithm)
why_success: 连铸切割涉及多个相互冲突的目标（满足用户长度、最小化损耗、保证质量），多目标规划可系统化处理；序贯算法适合在线实时优化，按优先级逐步满足约束，计算速度快，适合工业现场
result: 在连铸生产过程中，针对铸坯切割环节建立在线优化模型，在满足用户目标要求与正常工艺约束下，最小化切割损耗并处理异常工况
limitations: 序贯算法可能陷入局部最优，非全局最优；异常工况下的动态调整依赖异常检测的实时性；未完整考虑温度对切割质量的影响；多目标转化为单目标时优先级设定主观
source: 2021年高教社杯全国大学生数学建模竞赛D题：连铸切割的在线优化|https://blog.csdn.net/gitblog_06632/article/details/143334963|2021
confidence: 高
```

---

## SD-33（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
success_id: SD-33
problem_type: 预测
method: LSTM长短期记忆神经网络
why_success: 车流量具备周期性，LSTM擅长捕获时序周期性特征
result: 预测工作日各个时段城市道路车流量
limitations: 极；端；暴；雨；、；交；通；事；故；会；造；成；预；测；偏；差
source: 2024高教社杯国赛E题交通流量管控优秀论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2024sxjmstjp/241127/1980970.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## SD-34（公开经验库·公开）

```yaml
success_id: SD-34
problem_type: 预测
method: PCA-多元线性回归预测模型
why_success: 需要筛选冗余宏观指标，主成分分析可以降维去相关
result: 基于宏观指标预测光伏行业板块指数走向
limitations: 难；以；预；判；突；发；行；业；政；策；带；来；的；行；情；震；荡
source: 光伏建筑一体化板块指数分析优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2021
confidence: 高
```

---

## SD-35（公开经验库·公开）

```yaml
success_id: SD-35
problem_type: 优化决策
method: 非线性网格搜索优化模型
why_success: 停车场空间离散分区，网格搜索适配空间约束
result: 最大化停车位数量同时保障车辆进出通道宽度余量
limitations: 计；算；耗；时；随；网；格；精；度；提；升；急；剧；上；涨
source: 2026电工杯A题停车场规划优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2026
confidence: 高
```

---

## SD-36（公开经验库·公开）

```yaml
success_id: SD-36
problem_type: 优化决策
method: 0-1整数规划机组组合模型
why_success: 启停状态属于二元变量，整数规划适合求解该类约束
result: 24小时周期内控制发电机组最低运行成本
limitations: 机；组；数；量；上；涨；后；求；解；速；度；变；慢
source: 2025亚太杯D题电力系统机组组合论文|https://mbd.pub/o/bread/mbd-YZWZlplrZA==|2025
confidence: 高
```

---

## SD-37（公开经验库·公开）

```yaml
success_id: SD-37
problem_type: 评价分类
method: 模糊综合评价模型
why_success: 岗位适配属于模糊定性指标，模糊评价适配模糊属性
result: 评判求职者和各个兼职岗位之间匹配等级
limitations: 权；重；设；置；主；观；成；分；较；强
source: 2020 HiMCM暑期岗位推荐O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2020
confidence: 中
```

---

## SD-38（公开经验库·公开）

```yaml
success_id: SD-38
problem_type: 物理建模
method: 一维有限差分热传导模型
why_success: 离散差分便于迭代求解分层温度分布
result: 求解单根纤维热导率和整块织物导热关系
limitations: 简；化；掉；空；气；对；流；会；带；来；微；小；计；算；误；差
source: 第四届华数杯A题织物导热优秀论文|https://blog.csdn.net/m0_52343631/article/details/140867886|2023
confidence: 高
```

---

## SD-39（公开经验库·公开）

```yaml
success_id: SD-39
problem_type: 图模型
method: 无向连通图-遗传算法优化模型
why_success: 将终端-AP视作网络图，图结构适合描述连通关系
result: 规划AP点位，最大化网络整体吞吐量
limitations: 用；户；点；位；数；量；上；涨；之；后；运；算；速；度；下；降
source: 2024研究生华为杯B题WLAN组网优秀论文|https://github.com/1931239281/MathModel/blob/master/README.md|2024
confidence: 中
```

---

## SD-40（公开经验库·公开）

```yaml
success_id: SD-40
problem_type: 预测
method: 龙格-库塔RK4微分方程数值求解模型
why_success: 压强随时间由常微分方程管控，RK4求解精度更高
result: 计算阀门开闭全过程油管内部压力变化曲线
limitations: 忽；略；油；料；温；度；变；化；带；来；的；参；数；改；变
source: 2019国赛高压油管压力控制一等奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2019
confidence: 高
```

---

## SD-41（公开经验库·公开）

```yaml
success_id: SD-41
problem_type: 评价分类
method: PCA主成分分析+情感得分评价模型
why_success: 文本情绪属于核心指标，PCA整合其余数值指标
result: 依托用户评论数据对电商商品口碑等级划分
limitations: 存；在；刷；单；虚；假；评；论；干；扰；评；价；结；果
source: 2020 MCM-ICM网购平台O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2020
confidence: 中
```

---

## SD-42（公开经验库·公开）

```yaml
success_id: SD-42
problem_type: 预测
method: Prophet时间序列分解模型
why_success: 可以手动设置节假日影响因子，适配节假日垃圾波动
result: 预估未来一月城区每日垃圾产生总量
limitations: 突发大型集会活动会造成短期预测偏差
source: 2022高教社杯国赛C题城市生活垃圾处置优秀论文|https://www.cumcm.edu.cn/works/excellent/2022/|2022
confidence: 高
```

---

## SD-43（公开经验库·公开）

```yaml
success_id: SD-43
problem_type: 预测
method: 随机森林回归预测模型
why_success: 能够处理水质指标的非线性关联，可以输出特征重要度
result: 依据河道监测参数预测各个监测点位溶解氧浓度
limitations: 样；本；量；过；少；时；容；易；出；现；过；拟；合
source: 2025电工杯B题河道水质预警一等奖论文|https://blog.csdn.net/mathmodelshare/article/details/153692147|2025
confidence: 高
```

---

## SD-44（公开经验库·公开）

```yaml
success_id: SD-44
problem_type: 优化决策
method: 带时间窗的VRPTW遗传算法模型
why_success: 属于典型带时间窗车辆路径问题，遗传算法适合全局寻优
result: 规划配送车路线，压缩配送耗时、燃油成本以及生鲜损耗
limitations: 客户点位超过80之后求解耗时较长
source: 2024亚太杯C题生鲜冷链配送优化论文|https://mbd.pub/o/bread/Z5ebm52tZw==|2024
confidence: 高
```

---

## SD-45（公开经验库·公开）

```yaml
success_id: SD-45
problem_type: 优化决策
method: 0-1整数规划模型
why_success: 座位占用只有占用、空闲两种状态，适配零一变量
result: 合理分配自习座位，最大化座位利用率，降低冲突概率
limitations: 学；生；临；时；爽；约；会；降；低；实；际；资；源；利；用；率
source: 第五届华数杯B题自习室调度优秀论文|https://blog.csdn.net/weixin_46189918/article/details/142268904|2024
confidence: 高
```

---

## SD-46（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
success_id: SD-46
problem_type: 评价分类
method: 熵权-TOPSIS综合评价模型
why_success: 熵权依靠原始数据确权，规避人为主观权重偏差
result: 对各个行政村的振兴建设水平划分评价等级
limitations: 无；法；衡；量；难；以；量；化；的；乡；土；文；化；软；实；力
source: 2023高教社杯国赛E题乡村振兴评估一等奖论文|https://www.cumcm.edu.cn/works/excellent/2023/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## SD-47（公开经验库·公开）

```yaml
success_id: SD-47
problem_type: 物理建模
method: 牛顿动力学常微分方程模型
why_success: 需要获取全程运动过程，微分方程适合描述动态过程
result: 求解粗糙斜面上滑块速度、位移随时间的变化规律
limitations: 不；考；虑；摩；擦；系；数；随；速；度；发；生；细；微；改；变
source: 2021 MCM物理方向O奖论文|https://github.com/liuyouyuan/mcm-icm-2021|2021
confidence: 中
```

---

## SD-48（公开经验库·公开）

```yaml
success_id: SD-48
problem_type: 图模型
method: Dijkstra单源最短路算法
why_success: 起点固定，Dijkstra算法求解单起点最短路径效率很高
result: 搭建地铁-公交换乘网络，寻求耗时最短的出行路径
limitations: 无；法；同；时；兼；顾；车；费；、；换；乘；次；数；多；目；标；需；求
source: 2025研究生数学建模F题公共交通线路优化论文|https://github.com/MathematicalModelingClub/HuaweiCup2025|2025
confidence: 中
```

---

## SD-49（公开经验库·公开）

```yaml
success_id: SD-49
problem_type: 预测
method: BP-LSTM混合神经网络模型
why_success: LSTM捕捉循环时序老化特征，BP神经网络处理静态内阻参数
result: 依据充放电监测数据预估电池剩余循环使用寿命
limitations: 电；池；遭；遇；过；充；之；后；原；有；预；测；模；型；失；效
source: 2020 ICM电池寿命方向O奖论文|https://github.com/akashsara/mcm-icm2020|2020
confidence: 中
```

---

## SD-50（公开经验库·公开）

```yaml
success_id: SD-50
problem_type: 优化决策
method: 多目标线性规划模型
why_success: 成本、送达时间两项目标，适合构建多目标规划
result: 灾害之后调配应急物资，使得整体运输成本最低、送达时长最短
limitations: 没；有；考；虑；道；路；突；发；堵；塞；带；来；的；风；险
source: 2022亚太杯D题救灾物资调度优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2022
confidence: 高
```

---

## SD-51（公开经验库·公开）

```yaml
success_id: SD-51
problem_type: 评价分类
method: 层次分析法AHP-模糊综合评价模型
why_success: 各项准则的重要程度可以由教师学生打分对比，适配AHP确权
result: 依据学业成绩、志愿时长、竞赛、文体得分对学生进行分级
limitations: 指；标；权；重；会；受；到；评；审；人；员；主；观；偏；好；干；扰
source: 2026电工杯C题学生综合素质测评一等奖论文|https://blog.csdn.net/codeforfun666/article/details/154713205|2026
confidence: 高
```

---

## SD-52（公开经验库·公开）

```yaml
success_id: SD-52
problem_type: 优化调度
method: 多目标0-1整数规划与Floyd最短路算法
why_success: 精确求解路网最短路径和离散分配问题，能保证全局最优调度并兼顾多目标权衡
result: 设置交巡警服务平台并优化警力调度以最小化出警时间
limitations: 计算复杂度随节点数呈指数增长；难以处理动态实时调度与突发事件的耦合
source: 2011年全国大学生数学建模竞赛B题|全国大学生数学建模竞赛官网|2011
confidence: 高
```

---

## SD-53（公开经验库·公开）

```yaml
success_id: SD-53
problem_type: 预测
method: LSTM长短期记忆神经网络
why_success: 能够有效捕捉时间序列数据中的长期依赖关系，适合处理具有强非线性特征的气象-发电量映射
result: 基于气象数据预测光伏发电量并评估预测精度
limitations: 需要大量历史数据训练；模型可解释性较差，属于黑盒模型
source: 2018年电工杯数学建模竞赛A题|全国大学生数学建模竞赛官网|2018
confidence: 高
```

---

## SD-54（公开经验库·公开）

```yaml
success_id: SD-54
problem_type: 模拟与优化
method: 反应扩散偏微分方程与Eden生长模型
why_success: 反应扩散方程能描述宏观浓度场变化，Eden模型能模拟微观菌丝网络的不规则拓扑生长，两者结合实现多尺度建模
result: 分析菌丝网络在不同分解物表面上的生长扩散行为并优化其覆盖策略
limitations: 参数标定困难；对边界条件与网格尺度敏感
source: 2021年美国大学生数学建模竞赛A题|COMAP官网|2021
confidence: 高
```

---

## SD-55（公开经验库·公开）

```yaml
success_id: SD-55
problem_type: 优化设计
method: 一维非稳态热传导偏微分方程与非线性规划
why_success: 偏微分方程能精确描述热量在多层介质中的动态传导过程，结合非线性规划可实现尺寸寻优
result: 设计高温作业专用服装的厚度组合，在保证皮肤不被烫伤的前提下最小化服装重量
limitations: 一维假设忽略了横向热扩散；数值求解的网格密度对精度影响大
source: 2018年全国大学生数学建模竞赛A题|全国大学生数学建模竞赛官网|2018
confidence: 高
```

---

## SD-56（公开经验库·公开）

```yaml
success_id: SD-56
problem_type: 动态博弈与优化
method: 0-1整数规划与动态分层封堵模型
why_success: 0-1规划解决警力最优指派，动态分层封堵能根据罪犯逃逸时间逐步缩小包围圈
result: 设计对犯罪嫌疑人的最佳围堵方案，最小化抓捕时间并确保封锁
limitations: 假设罪犯绝对理性且信息对称；未考虑多罪犯协同
source: 2011年全国大学生数学建模竞赛B题参考答案|全国大学生数学建模竞赛官网|2011
confidence: 高
```

---

## SD-57（公开经验库·公开）

```yaml
success_id: SD-57
problem_type: 优化
method: 一维非稳态热传导方程与多目标优化算法
why_success: 能够基于传热机理准确反映不同温区温度和速度对焊接点温度的动态影响
result: 确定回流焊炉各温区设定温度及过炉速度，使电路板焊接温度曲线满足工艺要求
limitations: 忽略了电路板内部的热传导滞后效应；难以处理复杂几何形状
source: 2020年全国大学生数学建模竞赛A题|全国大学生数学建模竞赛官网|2020
confidence: 高
```

---

## SD-58（公开经验库·公开）

```yaml
success_id: SD-58
problem_type: 评价与优化
method: 聚类定价模型与带时间窗的车辆路径问题(VRPTW)
why_success: 聚类可将相近任务打包提升吸引力，VRPTW能精确求解多约束路径规划
result: 制定拍照任务的新定价方案并规划会员执行路线以最大化任务完成率
limitations: 模型复杂度高；难以快速求解超大规模问题
source: 2017年全国大学生数学建模竞赛B题|全国大学生数学建模竞赛官网|2017
confidence: 高
```

---

## SD-59（公开经验库·公开）

```yaml
success_id: SD-59
problem_type: 预测
method: 系统动力学模型与时间序列预测
why_success: 系统动力学能清晰刻画温度-浮游生物-猎物-海鸟的食物链因果反馈机制
result: 预测海洋温度上升对苏格兰海鸟种群数量的长期影响
limitations: 需大量参数假设；敏感性较高
source: 2020年美国大学生数学建模竞赛A题|COMAP官网|2020
confidence: 高
```

---

## SD-60（公开经验库·公开）

```yaml
success_id: SD-60
problem_type: 预测与评价
method: 最大熵模型与转移矩阵分析
why_success: 最大熵模型能利用仅存在点数据预测物种潜在分布，适合生态分布建模且所需样本量较少
result: 评估火灾对肯尼亚马赛马拉保护区野生动物种群分布的影响
limitations: 未考虑物种间竞争和人类活动干扰；对多共线性变量敏感
source: 2023年美国大学生数学建模竞赛B题|COMAP官网|2023
confidence: 高
```

---

## SD-61（公开经验库·公开）

```yaml
success_id: SD-61
problem_type: 排队论与决策
method: M/M/c排队论模型与期望收益决策模型
why_success: 排队论可解析计算等待时间期望，结合收益决策模型能量化比较两种选择的期望利润
result: 研究机场出租车司机载客决策（排队等待或空车返回）以最大化收益
limitations: 假设乘客到达率恒定，未考虑航班到达的不均匀性高峰；未考虑司机个体风险偏好
source: 2019年全国大学生数学建模竞赛C题|全国大学生数学建模竞赛官网|2019
confidence: 高
```

---

## SD-62（公开经验库·公开）

```yaml
success_id: SD-62
problem_type: 优化决策
method: 混合整数线性规划模型
why_success: ['问题含0-1互斥约束，混合整数线性规划可通过精确求解器得到全局最优解']
result: 在满足园区负荷需求的前提下，最大化风光储联合运营的经济性与可靠性
limitations: 对大规模园区联合场景，求解速度随变量数增加而下降
source: 2024电工杯A题园区微电网风光储协调优化配置优秀论文|https://blog.csdn.net/2201_75535220/article/details/139207728|2024
confidence: 高
```

---

## SD-63（公开经验库·公开）

```yaml
success_id: SD-63
problem_type: 预测
method: LSTM长短期记忆神经网络
why_success: ['风速序列具有强时序相关性，LSTM擅长捕捉长时序依赖关系']
result: 基于历史气象与机组运行数据，预测未来24小时风电机组输出功率
limitations: 极端天气下预测误差增大
source: 2019电工杯A题风电机组输出功率预测优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2019
confidence: 高
```

---

## SD-64（公开经验库·公开）

```yaml
success_id: SD-64
problem_type: 优化决策
method: 正向运动学+轨迹优化模型
why_success: ['正向运动学便于建立能耗与关节运动的直接关联，轨迹优化可直接引入能耗目标']
result: 在保证运动轨迹平稳的前提下，最小化人形机器人关节能耗
limitations: 未考虑关节摩擦与结构变形的影响
source: 2025亚太杯人形机器人运动建模与能耗优化优秀论文|https://www.iesdouyin.com/share/video/7575096913709687203|2025
confidence: 中
```

---

## SD-65（公开经验库·公开）

```yaml
success_id: SD-65
problem_type: 评价分类
method: 随机森林分类模型
why_success: ['随机森林可处理非线性关联，且能输出特征重要性']
result: 基于母亲身心指标与婴儿行为特征，对婴儿睡眠质量进行优、良、中、差四分类评价
limitations: 对小样本类别分类精度较低
source: 2023华数杯C题婴儿睡眠质量评价优秀论文|https://jishuzhan.net/article/1702235986626351106|2023
confidence: 高
```

---

## SD-66（公开经验库·公开）

```yaml
success_id: SD-66
problem_type: 优化决策
method: 多项式拟合+模拟退火优化模型
why_success: ['多项式拟合可更准确描述K/S值与浓度的非线性关系，模拟退火可避免陷入局部最优']
result: 在满足目标色差要求的前提下，最小化着色剂成本
limitations: 未考虑着色剂之间的相互作用
source: 2023华数杯B题不透明制品最优配色方案设计优秀论文|http://www.guyue12306.com/archives/14/|2023
confidence: 高
```

---

## SD-67（公开经验库·公开）

```yaml
success_id: SD-67
problem_type: 预测
method: 有限差分热传导模型
why_success: ['有限差分法便于离散化求解周期性结构的热传导问题']
result: 基于织物结构参数，预测织物整体热导率
limitations: 未考虑空气对流的影响
source: 2023华数杯A题织物热导率预测优秀论文|https://blog.csdn.net/m0_52343631/article/details/140867886|2023
confidence: 高
```

---

## SD-68（公开经验库·公开）

```yaml
success_id: SD-68
problem_type: 优化决策
method: 多目标线性规划模型
why_success: ['多目标线性规划可同时优化成本与时间两个目标']
result: 在满足受灾点物资需求的前提下，最小化运输成本与配送时间
limitations: 未考虑道路突发堵塞的风险
source: 2022亚太杯D题救灾物资调度优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2022
confidence: 高
```

---

## SD-69（公开经验库·公开）

```yaml
success_id: SD-69
problem_type: 评价分类
method: 熵权-TOPSIS综合评价模型
why_success: ['熵权依靠原始数据确权，规避人为主观权重偏差']
result: 对各个行政村的振兴建设水平划分评价等级
limitations: 无法衡量难以量化的乡土文化软实力
source: 2023国赛E题乡村振兴评估一等奖论文|https://www.cumcm.edu.cn/works/excellent/2023/|2023
confidence: 高
```

---

## SD-70（公开经验库·公开）

```yaml
success_id: SD-70
problem_type: 优化决策
method: 带时间窗的VRPTW遗传算法模型
why_success: ['属于典型带时间窗车辆路径问题，遗传算法适合全局寻优']
result: 规划配送车路线，压缩配送耗时、燃油成本以及生鲜损耗
limitations: 客户点位超过80之后求解耗时较长
source: 2024亚太杯C题生鲜冷链配送优化论文|https://mbd.pub/o/bread/Z5ebm52tZw==|2024
confidence: 高
```

---

## SD-71（公开经验库·公开）

```yaml
success_id: SD-71
problem_type: 预测
method: ['BP-LSTM混合神经网络模型']
why_success: ['LSTM捕捉循环时序老化特征，BP神经网络处理静态内阻参数']
result: 依据充放电监测数据预估电池剩余循环使用寿命
limitations: 电池遭遇过充之后原有预测模型失效
source: 2020 ICM电池寿命方向O奖论文|https://github.com/akashsara/mcm-icm2020|2020
confidence: 中
```

---

## SD-72（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
success_id: SD-72
problem_type: 优化决策
method: 基于蚁群算法与遗传算法优化的蒙特卡洛模拟模型
why_success: ['蚁群算法与遗传算法优化的蒙特卡洛模拟可提高生产决策的效率和准确性']
result: 在保证产品质量的前提下，最小化生产与检测成本，实现利润最大化
limitations: 对大规模生产场景，求解速度随变量数增加而下降
source: 2024高教社杯全国大学生数学建模竞赛B题优秀论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2024qgdxssxjmjslwzs_2024btlw/241104/1977943.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## SD-73（公开经验库·公开）

```yaml
success_id: SD-73
problem_type: 优化决策
method: 基于容量约束的车辆路径优化模型（CVRP）+改进型遗传算法
why_success: ['CVRP模型可有效处理容量约束，改进型遗传算法可提升解的全局探索能力与局部最优性']
result: 在满足垃圾分类收集要求的前提下，最小化运输成本与碳排放，提升运输效率
limitations: 对大规模垃圾分类运输场景，求解速度随收集点数量增加而下降
source: 2025电工杯数学建模竞赛B题优秀论文|https://blog.csdn.net/qq_50593822/article/details/148189953|2025
confidence: 高
```

---

## SD-74（公开经验库·公开）

```yaml
success_id: SD-74
problem_type: 评价分类
method: 熵权-TOPSIS综合评价模型
why_success: ['熵权依靠原始数据确权，规避人为主观权重偏差，TOPSIS计算贴近理想解距离']
result: 对各个行政村的振兴建设水平划分评价等级，识别薄弱环节
limitations: 无法衡量难以量化的乡土文化软实力
source: 我国乡村振兴发展水平综合评价研究|http://qks.cqu.edu.cn/cqdxskcn/article/abstract/20230108?st=search|2023
confidence: 高
```

---

## SD-75（公开经验库·公开）

```yaml
success_id: SD-75
problem_type: 优化决策
method: 多目标遗传算法（MOGA）+改进蚁群算法
why_success: ['多目标遗传算法可同时优化多个目标，改进蚁群算法可提升解的全局探索能力']
result: 在满足客户时间窗要求的前提下，最小化配送成本、制冷成本、货损成本与碳排放，提升客户满意度
limitations: 对大规模生鲜冷链配送场景，求解速度随客户数量增加而下降
source: 考虑碳排放和时间窗约束的冷链物流配送路径优化研究|https://www.hanspub.org/downLoad/page_download?filename=orf2024143_1131701725.pdf|2024
confidence: 高
```

---

## SD-76（公开经验库·公开）

```yaml
success_id: SD-76
problem_type: 预测
method: ['Temporal Convolutional Network（TCN）+ 注意力机制']
why_success: ['TCN擅长捕捉局部时序模式，注意力机制可自动加权关键时段特征，适配短时客流的突变性']
result: 基于历史客流数据、天气、节假日等特征，预测未来15分钟各站点进站客流量
limitations: 极端天气或大型活动下预测误差会显著增大
source: 2021高教社杯国赛A题城市轨道交通客流预测优秀论文|https://www.cumcm.edu.cn/works/excellent/2021/|2021
confidence: 高
```

---

## SD-77（公开经验库·公开）

```yaml
success_id: SD-77
problem_type: 优化决策
method: 混合整数规划模型+改进型蚁群算法
why_success: ['混合整数规划可精确描述堆位分配的离散约束，改进蚁群算法可快速求解大规模问题']
result: 在满足集装箱进出港时间窗的前提下，最小化堆场翻箱率与集卡运输距离
limitations: 对超过1000个集装箱的大规模场景，求解耗时显著增加
source: 2020亚太杯B题港口集装箱堆场优化优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2020
confidence: 高
```

---

## SD-78（公开经验库·公开）

```yaml
success_id: SD-78
problem_type: 评价分类
method: ['CRITIC权重法+TOPSIS综合评价模型']
why_success: ['CRITIC法同时考虑指标的变异强度与冲突性，比熵权法更贴合营商环境评价的实际需求']
result: 对全国主要城市的营商环境进行分级评价，识别优势与短板
limitations: 无法衡量难以量化的“政商关系”等软实力指标
source: 2022国赛D题城市营商环境评价一等奖论文|https://www.cumcm.edu.cn/works/excellent/2022/|2022
confidence: 高
```

---

## SD-79（公开经验库·公开）

```yaml
success_id: SD-79
problem_type: 物理建模
method: 基于地形坡度的自适应航线规划模型
why_success: ['自适应航线可根据地形坡度调整飞行高度与航线间距，在保证精度的同时降低能耗']
result: 在保证测绘精度的前提下，最小化无人机飞行时长与能耗
limitations: 对坡度超过60度的陡峭地形，测绘精度会下降
source: 2023美赛MCM无人机测绘O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2023
confidence: 中
```

---

## SD-80（公开经验库·公开）

```yaml
success_id: SD-80
problem_type: 图模型
method: 基于到达时间差（TDOA）的定位算法
why_success: ['TDOA算法不受信号强度衰减影响，定位精度更高']
result: 基于传感器监测数据，定位地下管网的泄漏点位置
limitations: 传感器数量不足时，定位误差会显著增大
source: 2024研究生数模B题地下管网泄漏定位优秀论文|https://github.com/1931239281/MathModel/blob/master/README.md|2024
confidence: 中
```

---

## SD-81（公开经验库·公开）

```yaml
success_id: SD-81
problem_type: 预测
method: ['Prophet+XGBoost混合模型']
why_success: ['Prophet擅长捕捉趋势与周期，XGBoost擅长处理非线性特征，混合模型兼顾两者优势']
result: 基于历史价格、供需数据、天气数据，预测未来7天农产品批发价格
limitations: 突发政策变化时预测误差会增大
source: 2025华数杯D题农产品价格预测优秀论文|https://blog.csdn.net/weixin_46189918/article/details/142268904|2025
confidence: 高
```

---

## SD-82（公开经验库·公开）

```yaml
success_id: SD-82
problem_type: 优化决策
method: 混合整数规划模型+遗传算法
why_success: ['混合整数规划可精确描述排程的离散约束，遗传算法可快速求解大规模问题']
result: 在满足手术时长、医生 availability、手术室资源的前提下，最小化患者等待时间与手术室闲置时间
limitations: 对超过100台手术的大规模场景，求解耗时显著增加
source: 2023电工杯C题医院手术排程优秀论文|https://blog.csdn.net/mathmodelshare/article/details/153692147|2023
confidence: 高
```

---

## SD-83（公开经验库·公开）

```yaml
success_id: SD-83
problem_type: 评价分类
method: ['因子分析+模糊综合评价模型']
why_success: ['因子分析可提取潜在影响因子，模糊综合评价可处理主观满意度等模糊指标']
result: 对高校毕业生的就业质量进行分级评价，识别影响因素
limitations: 无法衡量“职业发展潜力”等长期指标
source: 2022美赛ICM毕业生就业质量O奖论文|https://github.com/akashsara/mcm-icm2022|2022
confidence: 中
```

---

## SD-84（公开经验库·公开）

```yaml
success_id: SD-84
problem_type: 物理建模
method: ['LSTM+逻辑回归混合模型']
why_success: ['LSTM擅长捕捉时序特征，逻辑回归可输出概率值，适合预警场景']
result: 基于锂电池温度、电压、电流数据，预测热失控发生概率
limitations: 外部短路导致的热失控无法预警
source: 2024国赛B题锂电池热失控预警一等奖论文|https://www.cumcm.edu.cn/works/excellent/2024/|2024
confidence: 高
```

---

## SD-85（公开经验库·公开）

```yaml
success_id: SD-85
problem_type: 图模型
method: ['基于图论的多车辆路径优化模型（VRP）+蚁群算法']
why_success: ['VRP模型可有效处理多车辆路径问题，蚁群算法可快速求解大规模问题']
result: 在满足各站点需求的前提下，最小化调度成本与车辆空驶率
limitations: 对超过50个站点的大规模场景，求解耗时显著增加
source: 2025亚太杯C题共享单车调度优化优秀论文|https://mbd.pub/o/bread/Z5ebm52tZw==|2025
confidence: 高
```

---

## SD-86（公开经验库·公开）

```yaml
success_id: SD-86
problem_type: 预测
method: ['XGBoost特征增强预测模型']
why_success: ['光伏发电属于多因子非线性问题，XGBoost能够筛选关键气象特征，抗异常值干扰能力优秀']
result: 依托历史发电数据与气象数值预报，预测光伏电站次日逐时发电功率
limitations: 突发云层快速遮挡时短时预测误差上升
source: 2025电工杯A题光伏电站发电功率日前预测优秀论文|https://blog.csdn.net/maligebilaowang/article/details/148101073|2025
confidence: 高
```

---

## SD-87（公开经验库·公开）

```yaml
success_id: SD-87
problem_type: 优化决策
method: 0‑1整数规划模型
why_success: ['选址问题属于典型离散布尔变量问题，整数规划求解器能够搜寻全局最优解']
result: 在预算、社区人口约束之下选定养老站点位置，确定站点规模，最大化老年居民综合服务满意度
limitations: 社区点位大于80时求解耗时较长
source: 2026电工杯B题嵌入式社区养老服务站的建设与优化问题论文|https://blog.csdn.net/maligebilaowang/article/details/161324818|2026
confidence: 高
```

---

## SD-88（公开经验库·公开）

```yaml
success_id: SD-88
problem_type: 优化决策
method: ['D‑H参数建模+多目标遗传算法']
why_success: ['多目标遗传算法能够同时优化轨迹平滑程度、能耗、避障条件，输出帕累托解集']
result: 规避空间障碍物，平滑机械臂运动轨迹，降低运动能耗与关节角度冲击
limitations: 障碍物数量过多时算法收敛速度变慢
source: 2024年华数杯A‑机器臂关节角路径的优化设计论文|https://blog.csdn.net/maligebilaowang|2024
confidence: 高
```

---

## SD-89（公开经验库·公开）

```yaml
success_id: SD-89
problem_type: 预测
method: ['K‑means聚类+随机森林分类预测模型']
why_success: ['随机森林可以处理地形、水文的非线性关系，K‑means用于划分洪水灾害等级']
result: 基于水文、降雨、地形数据预测流域洪水发生概率和灾害损失等级
limitations: 突发短时特大暴雨场景预测精度下降
source: 2024亚太杯中文赛B题洪水灾害的数据分析与预测论文|https://jishuzhan.net/article/1811720976279277569|2024
confidence: 高
```

---

## SD-90（公开经验库·公开）

```yaml
success_id: SD-90
problem_type: 评价分类
method: ['CRITIC‑TOPSIS综合评价模型']
why_success: ['CRITIC算法同时考量指标变异程度与指标冲突性，适配能耗、损耗、碳排放多维度评价场景']
result: 从用电成本、设备损耗、供电稳定性、碳排放多个指标评价各类算力调度方案优劣
limitations: 难以量化服务器长期老化损耗等隐性指标
source: 2026年华数杯C题算电协同的多目标优化调度优化研究论文|https://www.iesdouyin.com/share/video/7671299682630503730|2026
confidence: 高
```

---

## SD-91（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
success_id: SD-91
problem_type: 优化决策
method: ['遗传算法优化后的蒙特‑卡洛模拟模型']
why_success: ['蒙特卡洛适合随机次品的仿真试验，遗传算法遍历搜寻最低成本的抽样参数']
result: 设定合适抽样检测方案，在保障次品检出置信度前提下压低检测、返工以及次品损失总成本
limitations: 零件次品率产生大幅波动之后原有抽样方案不再最优
source: 2024高教社杯国赛B题生产检测决策优化一等奖论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2024qgdxssxjmjslwzs_2024btlw/241104/1977943.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## SD-92（公开经验库·公开）

```yaml
success_id: SD-92
problem_type: 机理建模
method: ['常微分方程动力学演化模型']
why_success: ['养分循环属于物质守恒的连续变化机理过程，微分方程适合刻画物种之间耦合关系']
result: 建立微分方程组，刻画菌根真菌、树木、土壤养分之间长年动态演变规律
limitations: 无法处理极端气候冲击带来的突变式种群变化
source: 2021年美赛MCM‑ICM A题森林真菌生态建模O奖论文|https://wenku.csdn.net/doc/xqnrkpdv3e|2021
confidence: 中
```

---

## SD-93（公开经验库·公开）

```yaml
success_id: SD-93
problem_type: 优化决策
method: ['混合整数规划+改进蚁群算法']
why_success: ['选址为离散0‑1变量，路径规划属于NP难题，蚁群算法适合大规模路网搜寻最优路线']
result: 选定垃圾中转站点位、规划清运车辆路线，压缩运输开销以及碳排放
limitations: 收集点超过一百五十个时算法运算耗时明显上涨
source: 2025电工杯B题城市垃圾分类运输的路径优化优秀论文|https://blog.csdn.net/maligebilaowang/article/details/148223307|2025
confidence: 高
```

---

## SD-94（公开经验库·公开）

```yaml
success_id: SD-94
problem_type: 预测
method: ['分层嵌套概率回归模型']
why_success: ['分层模型可以区分国家层面、体育项目层面双层影响因素，适配东道主效应、历史衰减权重']
result: 结合往届赛事数据、东道主红利、综合国力，预测下一届奥运会奖牌数目
limitations: 新兴黑马体育强国很难依靠历史数据预测
source: MCM‑ICM奥运会奖牌预测O奖论文解析|https://mcmicm.org.cn/news/1186.html|2026
confidence: 中
```

---

## SD-95（公开经验库·公开）

```yaml
success_id: SD-95
problem_type: 综合评价
method: ['主成分分析‑模糊综合评价模型']
why_success: ['主成分分析用来筛除高度重合指标；模糊综合评价适配居民满意度这类主观指标']
result: 依托城市几十项统计指标，评估各个城市智慧城市建设等级并且定位短板指标
limitations: 城市特色化的软性文化指标难以量化评估
source: 2017年美赛ICM E题智慧城市建设O奖论文|https://blog.csdn.net/qq_41112170/article/details/122108814|2017
confidence: 中
```

---

## SD-96（公开经验库·公开）

```yaml
success_id: SD-96
problem_type: 交通流量预测与信号控制优化
method: KMeans聚类 + PSO粒子群优化 + MDP马尔可夫决策过程 + DQN深度Q学习 + 泊松分布
why_success: 问题1需将一天划分为若干时段，KMeans聚类可自动识别流量模式；问题2信号灯优化涉及离散动作空间与连续状态空间，MDP+DQN适合动态决策；问题3停车位估算需概率模型，泊松分布描述随机到达
result: 分析小镇交通流量时空分布，优化信号灯配时，识别巡游车辆并估算停车位需求，评价临时管控措施效果
limitations: DQN训练需大量仿真数据，竞赛环境下计算资源有限；巡游车辆判定准则（低车速+短时间重复）可能误标正常车辆；泊松分布假设车辆到达独立，实际可能存在聚集性；未考虑行人、非机动车干扰
source: 2024年高教社杯全国大学生数学建模竞赛E题：交通流量管控|https://blog.csdn.net/weixin_43292788/article/details/146361641|2024
confidence: 高
```

---

## SD-97（公开经验库·公开）

```yaml
success_id: SD-97
problem_type: 生产调度与空间优化
method: 排队论模型 + 整数规划 + 蒙特卡洛模拟
why_success: 湖羊养殖涉及多阶段排队（交配→妊娠→哺乳→育肥→休整），排队论可刻画各阶段等待与流转；整数规划可精确求解栏位分配；蒙特卡洛模拟可评估参数不确定性对空间利用率的影响
result: 优化湖羊养殖过程中各阶段羊只的栏位分配与周转，最大化标准羊栏空间利用率并满足生产周期约束
limitations: 假设周期固定，实际中个体差异导致周期波动；未考虑季节性因素对繁殖率的影响；蒙特卡洛模拟次数有限，极端情况覆盖不足；整数规划规模随羊只数量增加而急剧膨胀
source: 2023年高教社杯全国大学生数学建模竞赛D题：圈养湖羊的空间利用率|https://www.ppmy.cn/news/1096239.html|2023
confidence: 高
```

---

## SD-98（公开经验库·公开）

```yaml
success_id: SD-98
problem_type: 信息传输优化与概率建模
method: 信息传输率最大化原则 + 对称性原则 + 概率计算 + 组合优化
why_success: 问题核心是在有限时间K内最大化信息传播效率，信息传输率最大化原则保证每轮传输信息量最大；对称性原则简化方案设计；概率计算确保副站信息被主站成功接收的概率达标
result: 在地面通信瘫痪的救援场景下，设计气象分队主副站间的报文共享传输方案，最小化传输时间并满足成功接收概率要求
limitations: 假设所有站点同时发送，实际中可能存在冲突；未考虑信道噪声导致的误码，仅考虑发送失败；对称性假设限制了非对称优化方案的可能性；仅针对规则拓扑（主-副站结构），未考虑一般网络
source: 2022年高教社杯全国大学生数学建模竞赛D题：气象报文信息卫星通信传输|https://www.lmlphp.com/user/628420/article/item/10928850/|2022
confidence: 高
```

---

## SD-99（公开经验库·公开）

```yaml
success_id: SD-99
problem_type: 光谱鉴别与分类
method: 光谱预处理 + PCA降维 + SVM分类 + PLS-DA + CARS特征选择 + 多分类器集成(Fisher+SVM+RF概率融合) + BP神经网络
why_success: 光谱数据维数高、噪声大，预处理+降维是必要步骤；SVM在小样本高维下表现稳定；PLS-DA适合处理光谱-类别关系；CARS可选择最优波长组合；多分类器集成融合各方法优势提高鲁棒性；BP神经网络捕捉非线性模式
result: 利用近红外与中红外光谱数据鉴别中药材种类及产地，建立高准确率分类模型
limitations: 不同仪器采集的光谱存在差异，模型泛化能力受限；训练样本量有限，深度学习可能过拟合；产地鉴别中同一产地不同批次可能存在差异；光谱预处理参数选择依赖经验
source: 2021年高教社杯全国大学生数学建模竞赛E题：中药材的鉴别|https://blog.csdn.net/weixin_43970743/article/details/161521761|2021
confidence: 高
```

---

## SD-100（公开经验库·公开）

```yaml
success_id: SD-100
problem_type: 热传导机理建模与工艺优化
method: 一维/二维非稳态热传导方程 + 牛顿冷却定律 + 模拟退火/多重搜索优化
why_success: 回焊炉温度控制本质是热传导与对流换热的耦合过程，非稳态热传导方程可准确描述温度随时间/空间变化；工艺优化涉及多参数（速度、各温区温度），模拟退火/多重搜索可在复杂约束下寻找全局最优
result: 建立印刷电路板在回焊炉中的温度变化机理模型，优化传送带速度与温区温度设置，使焊接质量满足工艺要求
limitations: 一维简化忽略了板面横向温度不均匀性；假设热物性参数为常数，实际随温度变化；牛顿冷却定律线性近似在高温差时误差增大；未考虑焊膏相变潜热对温度曲线的影响
source: 2020年高教社杯全国大学生数学建模竞赛A题：炉温曲线|https://wenku.csdn.net/answer/303wy9rvnqqv|2020
confidence: 高
```

---

## SD-101（公开经验库·公开）

```yaml
success_id: SD-101
problem_type: 几何光学与精密工程
method: 理想抛物面几何模型 + 布尔莎七参数坐标转换 + 光反射定律 + 微元法 + 遍历优化
why_success: FAST反射面调节涉及复杂空间几何变换，理想抛物面由光学性质（焦点在馈源舱）确定；天体位置变化时需坐标转换，布尔莎七参数模型适合刚体变换；反射定律计算信号方向；微元法评估接收比；遍历优化保证满足促动器约束
result: 建立FAST望远镜主动反射面的形状调节模型，确定理想抛物面，计算促动器伸缩量，评估馈源舱接收比
limitations: 假设面板为刚性平面，实际存在微小形变；未考虑面板间缝隙对反射的影响；微元法撒点数量影响接收比精度；遍历优化计算量大，仅适用于小范围搜索
source: 2021年高教社杯全国大学生数学建模竞赛A题：FAST主动反射面的形状调节|https://blog.csdn.net/m0_49842530/article/details/146071683|2021
confidence: 高
```

---

## SD-102（公开经验库·公开）

```yaml
success_id: SD-102
problem_type: 图像识别与目标检测
method: 传统图像处理（阈值分割+形态学滤波+imfindcircles） + CNN特征提取 + K-means无监督聚类 + 迁移学习（ResNet/VGG）
why_success: 问题1-2（计数、定位）可用传统图像处理方法快速实现，苹果圆形特征适合imfindcircles；问题3（成熟度）可用无监督K-means对颜色特征聚类分级；问题5（识别）可用CNN迁移学习；竞赛环境下传统方法计算快、可解释性强
result: 建立果实采摘机器人的图像识别模型，实现苹果计数、定位、成熟度判断、质量估计及收获识别
limitations: 传统方法对遮挡、重叠苹果处理效果差；光照变化影响颜色阈值与成熟度判断；图像分辨率低时特征提取困难；CNN需要较多训练数据，竞赛数据集可能不足
source: 2023年APMCM亚太地区大学生数学建模竞赛A题：果实采摘机器人的图像识别|https://blog.csdn.net/2201_75432540/article/details/134599444|2023
confidence: 中
```

---

## SD-103（公开经验库·公开）

```yaml
success_id: SD-103
problem_type: 计算流体力学与热环境优化
method: 计算流体力学(CFD) + 多孔介质模型 + 迭代求解（有限体积法） + 参数扫描优化
why_success: 温室微气候涉及流体流动与热传递的强耦合，CFD可精确模拟三维温度场与风速场；作物对气流的阻碍与蒸腾作用可用多孔介质模型刻画；通过迭代求解得到稳态解后，可用参数扫描优化通风与风扇配置
result: 建立玻璃温室内微气候（温度、风速）的CFD模型，分析作物对微气候的影响，优化通风口位置与风扇配置使作物处于适宜条件
limitations: CFD计算量大，竞赛环境下受算力限制需简化模型；稳态假设忽略昼夜动态变化；多孔介质参数（渗透率、阻力系数）需经验估计；未考虑湿度与CO2浓度对作物的影响
source: 2023年APMCM亚太地区大学生数学建模竞赛B题：玻璃温室中的微气候调控|https://jishuzhan.net/article/1728259980206804994|2023
confidence: 中
```

---

## SD-104（公开经验库·公开）

```yaml
success_id: SD-104
problem_type: 时间序列预测与竞争分析
method: ARIMA时间序列预测 + 多元线性回归 + 竞争机理模型 + 系统动力学 + 情景分析
why_success: 问题1-2为时间序列预测，ARIMA适合处理销量数据的自相关性；问题3需分析市场竞争，竞争机理模型可刻画替代关系；问题4需评估政策影响，多元回归可量化政策变量；系统动力学适合长期多因素交互分析；情景分析处理不确定性
result: 分析我国新能源电动汽车发展趋势，预测未来销量，评估对传统燃油车行业影响及政策风险
limitations: ARIMA假设时间序列平稳或差分后平稳，结构性突变时失效；多元回归中政策变量难以精确量化；竞争模型参数估计依赖假设；长期预测（10年）不确定性大
source: 2023年APMCM亚太地区大学生数学建模竞赛C题：我国新能源电动汽车的发展趋势|https://blog.csdn.net/weixin_45499067/article/details/134551814|2023
confidence: 中
```

---

## SD-105（公开经验库·公开）

```yaml
success_id: SD-105
problem_type: 需求预测与库存优化
method: 三次指数平滑预测 + 参数调整法 + 强化参数法 + 联合调整法 + 库存-服务水平平衡优化
why_success: 小批量物料需求波动大、趋势各异，三次指数平滑可处理水平、趋势、季节多种模式；参数调整法针对不同趋势类型（水平/上升/下降）设置不同平滑参数；强化参数法与联合调整法在预测基础上动态修正生产计划，平衡库存与服务水平
result: 分析多品种小批量物料历史需求，建立周预测模型，制定生产计划平衡库存成本与服务水平
limitations: 三次指数平滑对突变需求响应滞后；参数选择依赖历史数据拟合，可能过拟合；联合调整法中库存与服务水平的权重主观；未考虑物料间的替代性与相关性
source: 2022年高教社杯全国大学生数学建模竞赛E题：小批量物料的生产安排|https://blog.csdn.net/weixin_43292788/article/details/131082064|2022
confidence: 高
```

---

## SD-113（公开经验库·公开）

```yaml
success_id: SD-113
problem_type: 预测
method: 多元非线性回归 + SVR组合预测
why_success: 非线性回归捕捉放电曲线特征, SVR在小样本下泛化好
result: 根据电池放电数据预测不同温度/电流下的剩余放电时间
limitations: 数据量有限影响深度学习模型；温度耦合效应建模不充分；未考虑电池老化
source: 全国大学生数学建模竞赛2016年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## SD-114（公开经验库·公开）

```yaml
success_id: SD-114
problem_type: 预测
method: 功率曲线拟合 + 神经网络短期预测 + 尾流模型优化布局
why_success: 曲线拟合建立稳态关系, 神经网络处理动态预测, 尾流模型优化机组布局
result: 分析风电场运行数据, 预测风电功率, 优化风电机组运行策略
limitations: 超短期预测精度有限；尾流模型简化较多；未考虑风机故障
source: 全国大学生数学建模竞赛2016年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## SD-115（公开经验库·公开）

```yaml
success_id: SD-115
problem_type: 预测
method: K-means聚类分析区域特征 + 回归建立定价模型 + 多目标规划优化
why_success: 聚类揭示区域定价差异, 回归量化定价影响因素, 多目标规划优化总方案
result: 分析拍照赚钱APP的任务定价规律, 建立定价模型并优化, 设计任务打包方案
limitations: 未考虑会员行为的不确定性；聚类数选择主观；打包方案可能非全局最优
source: 全国大学生数学建模竞赛2017年B题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## SD-116（公开经验库·公开）

```yaml
success_id: SD-116
problem_type: 预测
method: 多项式回归建立浓度-颜色关系 + AHP评价辨识能力
why_success: 多项式回归捕捉非线性, AHP系统评价三种染料的辨识能力
result: 根据颜色读数(RGB)建立物质浓度预测模型, 并对不同物质进行辨识
limitations: 多物质混合时模型不适用；pH/温度影响未充分建模；数据量有限
source: 全国大学生数学建模竞赛2017年C题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## SD-117（公开经验库·公开）

```yaml
success_id: SD-117
problem_type: 预测
method: RFM特征提取 + K-means会员分群 + 决策树预测消费倾向
why_success: RFM提取核心特征, K-means自动分群, 决策树提供可解释预测
result: 根据会员消费数据建立用户画像, 进行分类并预测消费行为
limitations: RFM仅考虑三个维度；K-means需预设簇数；未考虑时间序列特征
source: 全国大学生数学建模竞赛2018年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2018
confidence: 中
```

---

## SD-118（公开经验库·公开）

```yaml
success_id: SD-118
problem_type: 预测
method: 多元线性回归 + 随机森林组合校准
why_success: 线性回归提供基准, 随机森林捕捉非线性且鲁棒
result: 根据国控点真实数据校准自建点数据, 建立校准模型并评估效果
limitations: 站点间距离影响校准精度；极端天气下模型失效；未考虑污染源位置
source: 全国大学生数学建模竞赛2019年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 中
```

---

## SD-119（公开经验库·公开）

```yaml
success_id: SD-119
problem_type: 预测
method: 需求弹性分析 + 最优化定价模型
why_success: 弹性分析量化价格敏感度, 最优化模型求解最优定价
result: 分析薄利多销策略的适用条件, 建立最优定价模型
limitations: 需求函数假设简化；未考虑消费者行为差异；竞争反应未建模
source: 全国大学生数学建模竞赛2019年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 低
```

---

## SD-120（公开经验库·公开）

```yaml
success_id: SD-120
problem_type: 预测
method: XGBoost违约概率预测 + 整数规划信贷分配优化
why_success: XGBoost在信贷风控中表现优异, 整数规划给出最优信贷分配
result: 根据企业数据建立信贷风险评估模型, 给出最优信贷策略
limitations: 数据不平衡问题；未考虑宏观经济因素；模型可解释性不足
source: 全国大学生数学建模竞赛2020年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 中
```

---

## SD-121（公开经验库·公开）

```yaml
success_id: SD-121
problem_type: 预测
method: LSTM用水量预测 + 孤立森林异常检测
why_success: LSTM捕捉时间序列长期依赖, 孤立森林适合异常检测
result: 根据用水数据预测供水需求, 识别异常用水并优化调度
limitations: 需要大量历史数据；管网拓扑未建模；实时性要求高
source: 全国大学生数学建模竞赛2020年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 低
```

---

## SD-122（公开经验库·公开）

```yaml
success_id: SD-122
problem_type: 预测
method: Leslie矩阵模型 + 情景分析
why_success: Leslie矩阵可精确模拟年龄结构推移, 情景分析评估不同政策
result: 建立中国人口增长预测模型, 分析人口结构变化, 评估人口政策影响
limitations: 迁移率数据不完整；政策变化难以量化；长期预测不确定性大
source: 全国大学生数学建模竞赛2007年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2007
confidence: 中
```

---

## SD-123（公开经验库·公开）

```yaml
success_id: SD-123
problem_type: 预测
method: 综合指数评价 + 一维水质模型预测
why_success: 综合指数评价现状, 一维模型模拟污染物传播和降解
result: 评价长江水质状况, 预测未来水质变化趋势, 提出污染防治建议
limitations: 一维假设简化了实际河流；降解系数标定不确定；未考虑面源污染
source: 全国大学生数学建模竞赛2005年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2005
confidence: 中
```

---

## SD-124（公开经验库·公开）

```yaml
success_id: SD-124
problem_type: 预测
method: 混合效应模型分析疗效差异 + 回归预测疗效趋势
why_success: 混合效应模型处理重复测量数据, 回归预测疗效变化
result: 评价不同艾滋病疗法的效果, 预测疗效变化趋势, 提出最优治疗方案建议
limitations: 患者间差异大；未考虑耐药性；样本可能存在选择偏差
source: 全国大学生数学建模竞赛2006年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2006
confidence: 中
```

---

## SD-125（公开经验库·公开）

```yaml
success_id: SD-125
problem_type: 预测
method: 改进SEIR模型 + 最优化疫苗分配
why_success: SEIR考虑潜伏期更适合埃博拉, 最优化分配有限医疗资源
result: 建立埃博拉疫情传播模型, 优化疫苗/药物分发策略, 控制疫情蔓延
limitations: 均匀混合假设过于简化；未考虑人口流动；参数估计依赖早期数据
source: 2015 MCM Problem A: Eradicating Ebola|https://www.jingsailian.com/news/233612.html|2015
confidence: 中
```

---

## SD-143（公开经验库·公开）

```yaml
success_id: SD-143
problem_type: 预测
method: 迁移学习(ResNet50) + 数据增强
why_success: 迁移学习利用预训练模型, 数据增强解决小样本问题
result: 建立基于图像的农作物病害自动识别模型, 提高识别准确率
limitations: 训练数据有限；田间环境复杂；模型部署要求高
source: 2019年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2019
confidence: 低
```

---

## SD-144（公开经验库·公开）

```yaml
success_id: SD-144
problem_type: 预测
method: 物理模型 + SVR组合预测
why_success: 物理模型提供基准, SVR修正非线性误差
result: 建立光伏发电功率预测模型, 提高电网调度效率
limitations: 云量预测不确定；积灰影响未建模；超短期精度有限
source: 2019年电工杯数学建模竞赛A题|https://www.saikr.com/vse/DGB2019|2019
confidence: 低
```

---

## SD-145（公开经验库·公开）

```yaml
success_id: SD-145
problem_type: 预测
method: PCA降维 + LSTM时间序列预测
why_success: PCA降低维度, LSTM捕捉时间序列长期依赖
result: 建立空气质量预测模型, 分析主要影响因素, 提出治理建议
limitations: 源排放数据缺失；极端天气影响；长期预测不确定性大
source: 2019年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2019|2019
confidence: 低
```

---

## SD-158（公开经验库·公开）

```yaml
success_id: SD-158
problem_type: 优化决策
method: 整数规划营地分配 + 调度规则
why_success: 以所有队伍可行行程为目标, 整数规划分配营地并满足容量与行程约束
result: 在河道营地容量与划行速度约束下, 安排多日漂流行程使各队都能获得合规营地
limitations: 容量与速度简化；未考虑天气；多队并发复杂
source: 2012 MCM Problem B: Camping along the Big Long River|https://www.contest.comap.com/undergraduate/contests/|2012
confidence: 中
```

---

## SD-159（公开经验库·公开）

```yaml
success_id: SD-159
problem_type: 优化决策
method: 元胞自动机微观仿真 + 通行效率评价
why_success: 元胞自动机刻画单车换道与跟车行为, 仿真比较不同规则下的吞吐量
result: 评估'非超车靠右'规则对多车道道路通行效率的影响, 给出最优车道管理建议
limitations: 规则为理想化；未考虑驾驶员异质；仿真参数标定难
source: 2014 MCM Problem A: Keep-Right-Except-to-Pass Rule|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## SD-160（公开经验库·公开）

```yaml
success_id: SD-160
problem_type: 优化决策
method: 排队论瓶颈分析 + 合流仿真优化
why_success: 排队论识别收费与合流瓶颈, 仿真优化车辆合流顺序提升吞吐
result: 在收费车道合流瓶颈下, 优化车辆合流与收费策略使通行能力最大
limitations: 驾驶员行为理想化；未考虑突发；参数地区依赖
source: 2017 MCM Problem B: Merge After Toll|https://www.contest.comap.com/undergraduate/contests/|2017
confidence: 中
```

---

## SD-161（公开经验库·公开）

```yaml
success_id: SD-161
problem_type: 优化决策
method: 排队论通道数优化 + 仿真验证
why_success: 排队论确定满足等待阈值的通道数, 仿真在随机到达下验证鲁棒性
result: 在旅客到达与安检资源约束下, 优化安检通道开放数与排班使等待时间最小
limitations: 到达分布假设；未考虑团体旅客；排班切换成本忽略
source: 2017 ICM Problem D: Airport Checkpoint Operations|http://www.madio.net/thread-290074-1-1.html|2017
confidence: 中
```

---

## SD-162（公开经验库·公开）

```yaml
success_id: SD-162
problem_type: 优化决策
method: 最大覆盖选址 + 整数规划容量配置
why_success: 以覆盖需求最大为目标, 最大覆盖模型定位置, 整数规划配容量控成本
result: 在车辆行驶与需求分布下, 优化加油站(充电站)位置与容量使覆盖率与成本最优
limitations: 需求为估算；未考虑排队；路网静态
source: 2018 MCM Problem D: Out of the Gas?|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## SD-163（公开经验库·公开）

```yaml
success_id: SD-163
problem_type: 优化决策
method: 0-1规划组队 + 多目标权衡沟通与技能
why_success: 以技能覆盖与沟通成本为目标, 0-1规划分配成员到团队并满足约束
result: 在成员技能与任务约束下, 优化团队组建与协作策略使项目成功率最高
limitations: 技能刻画简化；未考虑人际因素；任务依赖忽略
source: 2020 MCM Problem D: The Teaming Strategy|https://www.contest.comap.com/undergraduate/contests/|2020
confidence: 中
```

---

## SD-164（公开经验库·公开）

```yaml
success_id: SD-164
problem_type: 优化决策
method: 多目标规划 + AHP三重底线加权
why_success: 以经济/环境/社会三重底线为目标, 多目标规划求解可持续投入最优分配
result: 在可持续投资与收益权衡下, 评估并优化组织的可持续策略使其长期效益最优
limitations: 收益货币化有争议；权重主观；长期不确定性强
source: 2015 ICM Problem D: Is it smarter to be sustainable?|http://www.madio.net/thread-290074-1-1.html|2015
confidence: 中
```

---

## SD-165（公开经验库·公开）

```yaml
success_id: SD-165
problem_type: 优化决策
method: 整数规划预订 + 蒙特卡洛应对不确定性
why_success: 以总费用最小为目标, 整数规划确定房间与会议室配置, 蒙特卡洛评估到会波动
result: 在发回执率不确定与预算约束下, 优化宾馆房间与会议室预订使总费用最小且满足需求
limitations: 回执率估计误差；未考虑临时增减；价格为简化
source: 全国大学生数学建模竞赛2009年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2009
confidence: 中
```

---

## SD-177（公开经验库·公开）

```yaml
success_id: SD-177
problem_type: 评价分类
method: PCA+LASSO筛选 + DEA效率评价投资
why_success: PCA/LASSO降维筛选关键指标, DEA评价投资效率并优选组合
result: 在投资回报与使命约束下, 评价并优选高校/学科投资方案使社会效益最大
limitations: 回报口径不一；长期效果难估；数据缺失
source: 2016 MCM Problem C: The Goodgrant Challenge|https://www.contest.comap.com/undergraduate/contests/|2016
confidence: 中
```

---

## SD-178（公开经验库·公开）

```yaml
success_id: SD-178
problem_type: 评价分类
method: 成本效益分析 + AHP隐私策略评价
why_success: 成本效益量化保护代价与收益, AHP综合多维度评价隐私策略
result: 建立个人隐私成本与收益评价模型, 比较不同隐私保护策略的代价
limitations: 隐私价值主观；风险概率难估；跨文化差异
source: 2018 ICM Problem F: Cost of Privacy|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## SD-179（公开经验库·公开）

```yaml
success_id: SD-179
problem_type: 评价分类
method: 熵值法客观赋权 + 神经网络综合评价
why_success: 熵值法客观赋权避免主观, 神经网络拟合复杂指标与绩效的非线性关系
result: 建立国家卫生系统综合评价指标, 比较不同系统绩效并提改进建议
limitations: 数据年份不一；因果难辨；文化背景差异
source: 2008 ICM Problem: Health Care System|http://www.madio.net/thread-290074-1-1.html|2008
confidence: 中
```

---

## SD-180（公开经验库·公开）

```yaml
success_id: SD-180
problem_type: 评价分类
method: 灰色预测需求 + AHP多方案评价
why_success: 灰色预测未来能源需求, AHP综合技术/经济/环境评价配置方案
result: 建立能源供给配置评价模型, 分析不同方案对发展与能耗的影响并优选
limitations: 数据有限；替代弹性难估；政策影响忽略
source: 2009 MCM Problem B: Energy and Phones|https://www.contest.comap.com/undergraduate/contests/|2009
confidence: 中
```

---

## SD-181（公开经验库·公开）

```yaml
success_id: SD-181
problem_type: 评价分类
method: AHP+生命周期评价(LCA)综合评估
why_success: LCA量化全周期环境影响, AHP综合经济/电网/环境多维评价推广策略
result: 建立电动汽车推广评价模型, 比较其对环境/经济/电网的影响并给政策建议
limitations: 电池回收难建模；电网耦合复杂；政策变量多
source: 2011 ICM Problem: Electric Vehicles|http://www.madio.net/thread-290074-1-1.html|2011
confidence: 中
```

---

## SD-182（公开经验库·公开）

```yaml
success_id: SD-182
problem_type: 评价分类
method: 网络关联 + PCA+AHP健康综合评价
why_success: 网络刻画系统耦合, PCA降维, AHP赋权综合评估地球健康状态
result: 建立地球健康评价指标网络, 量化各系统健康状态并识别关键风险环节
limitations: 关联权重主观；数据时空不一；阈值难统一
source: 2013 MCM Problem C: Earth Health Network Model|https://www.contest.comap.com/undergraduate/contests/|2013
confidence: 中
```

---

## SD-183（公开经验库·公开）

```yaml
success_id: SD-183
problem_type: 评价分类
method: AHP+模糊评价供需 + 聚类优化调度
why_success: AHP/模糊评价区域供需失衡, 聚类识别热点并优化车辆调度
result: 评价出租车供需匹配状况, 优化'互联网+'下的资源配置与补贴策略
limitations: 数据时空颗粒粗；行为响应难建模；未考虑监管
source: 全国大学生数学建模竞赛2015年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2015
confidence: 中
```

---

## SD-184（公开经验库·公开）

```yaml
success_id: SD-184
problem_type: 评价分类
method: 熵权法+模糊综合评价拥堵等级
why_success: 熵权法客观赋权, 模糊综合评价处理拥堵指标的模糊边界并分级
result: 建立城市交通拥堵综合评价指标, 对路网/区域拥堵程度分级并提缓解建议
limitations: 数据覆盖有限；权重地区依赖；未考虑突发拥堵
source: 2018年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2018
confidence: 低
```

---

## SD-185（公开经验库·公开）

```yaml
success_id: SD-185
problem_type: 评价分类
method: AHP+模糊综合评价智慧物流水平
why_success: AHP确定智慧化维度权重, 模糊综合评价处理不确定性并排序方案
result: 建立智慧物流系统综合评价指标, 评估不同物流方案智能化水平并优选
limitations: 智慧化界定模糊；数据样本少；权重主观
source: 2018年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2018|2018
confidence: 低
```

---

## SD-206（公开经验库·公开）

```yaml
success_id: SD-206
problem_type: 物理建模
method: 分层多保真模型：问题一采用周期切割后的闭合三角网格、轴对齐包围盒粗筛、轴线距离粗筛、三角网格距离细筛和深度优先搜索；问题二、三采用快速轴线随机几何渗流模型、扫描线筛选、线段最短距离、并查集和蒙特卡洛概率估计；问题三使用加权逻辑斯蒂回归定位90%临界值，并以Wilson置信下限直接验证；问题四沿90%导通边界进行整数二分搜索，利用单调性缓存减少重复仿真，再用高斯过程期望改进算法搜索最低成本组合
why_success: 确定性小样本问题需要准确描述圆柱端面、侧面和边界裁剪，因此采用三维实体模型；概率与优化问题需要成千上万次随机试验，完整网格计算量过大，因此采用经过高精度模型思想约束的快速轴线模型。导电性本质上是接触网络的连通问题，图搜索和并查集与物理机制一致。导通概率随体积分数呈S形变化，逻辑斯蒂模型适合定位临界区域，但为避免平滑拟合产生虚假可行解，最终使用Wilson下限直接验证。问题四中增加介质通常不会破坏已有通路，可利用单调性、缓存和二分法减少仿真次数，再用贝叶斯优化避免遍历全部组合
result: 判断随机填充导电介质的微构体是否形成左右贯通通路，估计不同填充量下的导通概率，确定导通概率不低于90%的最低填充量，并优化圆柱介质A与球形介质B的组合成本
limitations: 快速轴线模型不能完全复现平端圆柱实体在端部和边界处的几何细节；蒙特卡洛概率仍受样本量和随机种子影响；公共随机数会使不同填充水平的估计相关，因此逻辑斯蒂模型置信区间只能视为近似诊断；逻辑斯蒂模型预设单调S形关系，局部失拟会影响连续临界值的位置；高斯过程优化结果依赖初始样本覆盖、核长度尺度和候选边界点质量；Wilson下限约束较保守，可能使最终填充量高于平滑模型给出的理论交点
source: 2026年第七届“华数杯”大学生数学建模竞赛 A题《微构体中填充导电介质的仿真优化》 | 本地赛题PDF与配套代码复盘 | 2026
confidence: 高
```

---

## SD-207（公开经验库·公开）

```yaml
success_id: SD-207
problem_type: 水文分析与时间序列预测
method: 多元线性回归 + SVR支持向量回归 + ARDL时间序列回归 + STL季节分解 + LSTM神经网络 + 河床冲淤模型
why_success: 问题1需建立含沙量与多因素的回归关系，从线性到非线性逐步深入；问题2需分解水沙通量的突变性、季节性和周期性，STL分解适合；问题3需长期预测，LSTM可捕捉非线性时序特征；问题4需评估调水调沙效果，河床冲淤模型可量化泥沙沉积与冲刷
result: 分析黄河水沙通量变化规律，预测未来趋势，优化监测采样方案，评估调水调沙效果
limitations: LSTM需要较长序列训练，数据量有限时可能过拟合；ARDL模型对滞后阶数选择敏感；河床冲淤模型参数需经验估计；未考虑极端气候事件对水沙通量的冲击
source: 2023年高教社杯全国大学生数学建模竞赛E题：黄河水沙监测数据分析|https://blog.csdn.net/weixin_43970743/article/details/161108783|2023
confidence: 高
```

---

## SD-208（公开经验库·公开）

```yaml
success_id: SD-208
problem_type: 博弈决策与路径优化
method: 动态规划 + 统计分析 + 静态博弈 + 蒙特卡洛模拟
why_success: 穿越沙漠涉及多阶段决策（每日行动选择），动态规划可逆向求解最优策略；天气不确定性需统计分析；多玩家竞争需博弈论；复杂场景可用蒙特卡洛模拟评估
result: 在穿越沙漠游戏中，制定最优策略（路线、资源购买、天气应对）使玩家在规定时间内到达终点并保留最多资金
limitations: 动态规划状态空间随天数指数增长；天气概率假设为历史频率，可能不准确；静态博弈未考虑对手动态反应；未考虑玩家风险偏好差异
source: 2020年高教社杯全国大学生数学建模竞赛B题：穿越沙漠|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## SD-209（公开经验库·公开）

```yaml
success_id: SD-209
problem_type: 几何反演与模式识别
method: 几何反演 + 分段拟合 + 曲率分析 + 最小二乘拟合
why_success: 轮廓自动标注本质是几何反演问题：从离散观测点反求分段几何模型；曲率分析可识别直线-圆弧过渡点；最小二乘可精确拟合各段参数；几何约束保证段间连续性
result: 对接触式轮廓仪获取的工件轮廓数据，自动识别并标注各几何段（直线、圆弧）的参数
limitations: 测量噪声影响曲率计算精度；小圆弧与直线难以区分；未考虑更复杂曲线（椭圆、抛物线）；对密集噪声点敏感
source: 2020年高教社杯全国大学生数学建模竞赛D题：接触式轮廓仪的自动标注|https://gitcode.csdn.net/6a20255310ee7a33f2773f47.html|2020
confidence: 高
```

---

## SD-210（公开经验库·公开）

```yaml
success_id: SD-210
problem_type: 流体力学与压力控制优化
method: 质量守恒微分方程 + 流量计算 + 离散时间迭代 + 参数搜索优化
why_success: 高压油管压力控制本质是燃油质量守恒与可压缩性的耦合问题；通过建立质量守恒微分方程可描述压力-密度动态关系；流量公式描述进出边界条件；离散时间迭代适合数值求解；参数搜索可优化凸轮转速等控制参数
result: 建立高压油管内燃油压力动态模型，优化供油策略使压力稳定在目标值（100MPa或特定变化曲线）
limitations: 集总参数假设忽略管内压力梯度；未考虑燃油温度变化对粘度的影响；针阀动态简化，未考虑液压振荡；参数搜索步长影响精度与效率
source: 2019年高教社杯全国大学生数学建模竞赛A题：高压油管的压力控制|https://www.ppmy.cn/news/195212.html|2019
confidence: 高
```

---

## SD-211（公开经验库·公开）

```yaml
success_id: SD-211
problem_type: 传感器校准与数据融合
method: 多元线性回归(MLR) + 含交互项的逐步回归 + 随机森林 + Z-score标准化 + 时间前后划分验证
why_success: 问题需从自建点测量值推断真实浓度，线性回归提供基线可解释性；逐步回归引入气象交互项刻画电化学传感器物理机理；随机森林捕捉非线性与高阶交互，对异常值鲁棒；分层递进结构兼顾可解释性与精度
result: 建立微型传感器与国控点高精度仪器的校准模型，修正传感器漂移与交叉干扰，提高空气质量数据准确性
limitations: 不同污染物需分别建模（一气一模型），工作量大；随机森林黑箱特性导致极端值预测可能偏差；24天数据量有限，长期漂移外推不可靠；未考虑传感器老化导致的非线性漂移
source: 2019年高教社杯全国大学生数学建模竞赛D题：空气质量数据的校准|https://gitcode.csdn.net/6a200938662f9a54cb792c0f.html|2019
confidence: 高
```

---

## SD-212（公开经验库·公开）

```yaml
success_id: SD-212
problem_type: 热传导与多层材料优化
method: 一维非稳态热传导方程 + 有限差分法(FDM) + 界面热阻模型 + 单变量/二维网格搜索优化
why_success: 高温防护服涉及多层材料的热传导与蓄热，一维非稳态热传导方程可准确描述温度随时间与厚度的变化；有限差分法适合规则分层几何；界面热阻模型修正理想接触假设；网格搜索可优化厚度组合
result: 建立高温作业专用服装的热传导模型，确定各层材料厚度与界面热阻，使人体皮肤外侧温度满足安全要求
limitations: 一维假设忽略服装边缘与人体曲率影响；热物性参数假设为常数，实际随温度变化；界面热阻需通过实验数据反演，存在识别误差；未考虑汗液蒸发等生理调节机制
source: 2018年高教社杯全国大学生数学建模竞赛A题：高温作业专用服装设计|https://blog.csdn.net/weixin_43970743/article/details/161520460|2018
confidence: 高
```

---

## SD-213（公开经验库·公开）

```yaml
success_id: SD-213
problem_type: 刚体力学与协同控制优化
method: 牛顿第二定律 + 动量/能量守恒 + 欧拉刚体旋转定理 + 小角度近似 + 模拟退火优化
why_success: 同心鼓运动涉及平动与转动的耦合，牛顿第二定律描述平动，转动定律描述转动，欧拉定理描述三维姿态；小角度近似简化三维转动为两个独立自由度；模拟退火可优化多人协作的发力策略
result: 建立同心鼓颠球运动的力学模型，分析鼓面倾斜机理，给出最优协作策略使连续颠球次数最多且能耗最小
limitations: 小角度近似限制了大倾角情况；忽略绳子振动与弹性；假设所有队员同步周期性发力，实际可能有相位差；未考虑队员反应时间延迟
source: 2019年高教社杯全国大学生数学建模竞赛B题：同心协力策略研究|https://blog.csdn.net/2401_82505179/article/details/142747597|2019
confidence: 高
```

---

## SD-214（公开经验库·公开）

```yaml
success_id: SD-214
problem_type: 排队论与收益优化
method: 排队论模型(M/M/1或M/M/c) + 收益成本分析 + 静态博弈 + 补偿机制设计
why_success: 机场出租车排队是典型的排队系统，排队论可刻画等待时间；收益成本分析比较两种选择（排队vs空返）的期望利润；博弈论分析多司机竞争；补偿机制设计可平衡长短途收益
result: 分析出租车司机在机场的决策行为，建立收益模型优化司机选择策略，设计短途补偿机制平衡收益
limitations: 假设到达服从泊松分布，实际可能有航班聚集；未考虑司机风险偏好差异；静态博弈未考虑动态信息更新；短途补偿机制设计依赖主观参数
source: 2019年高教社杯全国大学生数学建模竞赛C题：机场的出租车问题|https://www.toymoban.com/blog/675072.html|2019
confidence: 高
```

---

## SD-215（公开经验库·公开）

```yaml
success_id: SD-215
problem_type: 零售数据分析与定价策略
method: 数据清洗与聚合 + 利润率反推 + 打折力度指标构建 + 相关性分析 + 线性回归 + 分类对比分析
why_success: 问题1-2为数据计算与指标构建，需清洗聚合；问题3-4为关系分析，回归与相关性分析适合；分类对比可揭示不同商品大类的差异
result: 分析商场销售数据，计算营业额与利润率，量化打折力度，研究薄利多销策略的效果
limitations: 成本价缺失导致利润率计算存在估计误差；未考虑库存成本与资金占用；打折力度指标构建主观性强；时间序列中的节假日效应未完全剔除
source: 2019年高教社杯全国大学生数学建模竞赛E题：薄利多销分析|https://blog.csdn.net/2403_87108415/article/details/149207364|2019
confidence: 高
```

---

## SD-216（公开经验库·公开）

```yaml
success_id: SD-216
problem_type: 客户价值分析与关联挖掘
method: RFMT客户价值模型 + AHP层次分析法 + K-means聚类 + 因子分析 + 线性回归 + FP-Growth关联规则
why_success: RFM是客户价值分析经典框架，T（单次最高消费）增强了对高端商场的刻画；AHP确定指标权重；K-means实现会员分群；因子分析提取激活率潜变量；FP-Growth高效挖掘商品关联规则
result: 构建百货商场会员画像，识别会员价值，划分生命周期状态，计算激活率，策划连带消费促销
limitations: AHP权重主观性强；K-means聚类数K需预设；因子分析对样本量有要求；关联规则最小支持度选择影响结果；未考虑会员社交关系与口碑传播
source: 2018年高教社杯全国大学生数学建模竞赛C题：大型百货商场会员画像描绘|https://damodev.csdn.net/6889c366bb9d8e0ecec3e417.html|2018
confidence: 高
```

---

## SD-217（公开经验库·公开）

```yaml
success_id: SD-217
problem_type: 优化决策
method: 多目标整数规划模型
why_success: 需兼顾覆盖与工作量均衡整数规划能精确求解最优布局
result: 合理设置交巡警服务平台并分配管辖范围使出警时间最短且均衡
limitations: 未考虑交通拥堵实时变化；假设事故发生概率均匀可能不符合实际
source: 2011年全国大学生数学建模B题优秀论文|https://doc.xuehai.net/b835340c48a00378980807b7c.html|2011
confidence: 高
```

---

## SD-218（公开经验库·公开）

```yaml
success_id: SD-218
problem_type: 预测
method: SEIR改进模型
why_success: 需区分潜伏期与发病期SEIR更符合埃博拉特征
result: 预测埃博拉疫情发展并设计干预与资源分配方案
limitations: 未充分模拟国际援助延迟；参数依赖历史报告准确性
source: 2015 MCM Outstanding Papers: Eradicating Ebola|http://www.hanlin.com/archives/85459|2015
confidence: 高
```

---

## SD-219（公开经验库·公开）

```yaml
success_id: SD-219
problem_type: 评价分类
method: 主成分分析(PCA)与聚类分析
why_success: 指标维度高且相关需降维后聚类分级
result: 分析酿酒葡萄与葡萄酒质量关系评价葡萄等级
limitations: 未考虑微观风味物质相互作用；感官评分主观性难消除
source: 2012国赛A题优秀论文|https://doc.xuehai.net/bc46036d3588eff46e760df6d.html|2012
confidence: 高
```

---

## SD-220（公开经验库·公开）

```yaml
success_id: SD-220
problem_type: 评价分类
method: 熵权-模糊综合评价与交通分配模型
why_success: 需多指标评价且可结合路网流量分配
result: 评价小区开放对周边道路通行的影响并优化道路设计
limitations: 未覆盖所有小区形态；仿真未含动态信号控制
source: 2016年全国数学建模竞赛B题一等奖论文|https://www.bodocs.net/doc/4520055488.html|2016
confidence: 高
```

---

## SD-221（公开经验库·公开）

```yaml
success_id: SD-221
problem_type: 优化决策
method: 成本效益优化与网络清除模型
why_success: 需权衡清除收益与成本并优先高风险目标
result: 评估太空碎片清除的商业可行性与优先清除策略
limitations: 未模拟国际政策协调；编目数据存在误差
source: 2016 MCM特等奖Outstanding论文B题下载-Space Junk|https://www.hanlin.com/archives/category/bonus/documents/page/49/|2016
confidence: 高
```

---

## SD-222（公开经验库·公开）

```yaml
success_id: SD-222
problem_type: 优化决策
method: 排队论与启发式寻优
why_success: 需处理随机服务过程并全局寻优
result: 确定电动汽车充电站最优位置与容量
limitations: 未考虑快充对电网冲击的动态过程；假设路径选择单一
source: 2016电工杯数学建模竞赛论文|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2016
confidence: 中
```

---

## SD-223（公开经验库·公开）

```yaml
success_id: SD-223
problem_type: 优化决策
method: 动态规划与状态转移模型
why_success: 离散时间与资源状态适合阶段决策建模
result: 在资源、天气与规则约束下求解穿越沙漠最优策略
limitations: 未考虑真实玩家心理；随机天气仅用概率近似
source: CUMCM2020-Desert-Game 全国一等奖论文源码|https://www.github.com/seanys/CUMCM2020-Desert-Game|2020
confidence: 高
```

---

## SD-224（公开经验库·公开）

```yaml
success_id: SD-224
problem_type: 物理建模
method: 质心跟踪与边缘特征回归模型
why_success: 题目明确先跟踪质心再提取轮廓特征
result: 跟踪二氧化硅颗粒熔融过程并估计熔化速率
limitations: 二维图像对体积估计有近似误差；高温噪声影响边缘提取
source: 亚太地区数学建模优秀论文_2019年第九届APMCM A题|https://blog.csdn.net/weixin_39580749/article/details/110816724|2019
confidence: 中
```

---

## SD-225（公开经验库·公开）

```yaml
success_id: SD-225
problem_type: 优化决策
method: 绿波带模型与启发式算法
why_success: 干线协调需最大化通过带宽
result: 利用车辆轨迹数据优化信号配时减少拥堵
limitations: 假设流量均匀未考虑随机到达；未优化左转专用相位
source: 2017 MCM特等奖Outstanding论文C题下载-Cooperate and Navigate|http://www.hanlin.com/archives/84719|2017
confidence: 高
```

---

## SD-226（公开经验库·公开）

```yaml
success_id: SD-226
problem_type: 优化决策
method: 多原则比较与蒙特卡洛模拟调度模型
why_success: NP特征明显模拟比解析更易获得可行优解
result: 设计智能加工系统中RGV动态调度策略使产量最高
limitations: 未考虑刀具磨损细节；随机故障仅概率建模
source: 智能RGV的动态调度策略|https://publish.cnki.net/journal/portal/stdx/client/paper/5a488777c0246c392ca31fa4b5cda6b9|2018
confidence: 高
```

---

## SD-227（公开经验库·公开）

```yaml
success_id: SD-227
problem_type: 图像重建与参数标定
method: 最小二乘法标定 + 傅立叶变换重建(中心切片定理) + 滤波反投影法(FBP) + 圆形组合模板优化
why_success: CT参数标定需从投影数据反推几何参数，最小二乘可拟合正弦曲线求旋转角度与探测器间距；中心切片定理是解析重建的理论基础；FBP可去除反投影星状伪影；圆形模板可避免椭圆边缘插值误差
result: 对存在安装误差的二维CT系统进行参数标定，并重建未知介质吸收率分布
limitations: 解析重建对噪声敏感，问题3噪声大时需FBP改进；圆形模板假设可能不适用于所有CT系统；180个角度采样有限，存在混叠伪影；滤波器选择影响重建质量
source: 2017年高教社杯全国大学生数学建模竞赛A题：CT系统参数标定及成像|https://blog.csdn.net/weixin_43292788/article/details/142355315|2017
confidence: 高
```

---

## SD-228（公开经验库·公开）

```yaml
success_id: SD-228
problem_type: 定价优化与任务分配
method: 描述统计+箱线图 + 多元线性回归 + 随机森林 + DBSCAN密度聚类 + 任务打包优化
why_success: 问题1需探索性分析定价规律与完成率关系；问题2需建立定价预测模型，多元回归可解释性强，随机森林捕捉非线性；问题3任务打包需聚类，DBSCAN可发现任意形状密集区域；问题4综合优化
result: 分析拍照赚钱APP的任务定价规律，设计新定价方案，优化任务打包策略以提高完成率并降低成本
limitations: 多元回归调整R²仅31.59%，解释力有限；未考虑时间维度（任务时效性）；DBSCAN对参数敏感；会员行为假设简化
source: 2017年高教社杯全国大学生数学建模竞赛B题：'拍照赚钱'的任务定价|https://github.com/Henryers/PhotoPricingModel|2017
confidence: 高
```

---

## SD-229（公开经验库·公开）

```yaml
success_id: SD-229
problem_type: 化学计量学与回归分析
method: 散点图探索 + 多元线性回归 + 主成分回归(PCR) + Michaelis-Menten非线性回归 + 数据质量评价模型
why_success: 不同物质浓度-颜色关系各异：组胺/溴酸钾/工业碱呈线性可用回归；硫酸铝钾呈饱和趋势用Michaelis-Menten；奶中尿素关系复杂需多模型尝试；PCR处理多重共线性；数据质量评价需准确度与精密度综合
result: 建立颜色读数与物质浓度的定量关系，评价数据质量，探讨数据量与维度对模型的影响
limitations: 不同物质需分别建模，工作量大；Michaelis-Menten参数初值敏感；颜色维度选择主观性强；数据量小（每种物质约10组）
source: 2017年高教社杯全国大学生数学建模竞赛C题：颜色与物质浓度辨识|https://blog.csdn.net/weixin_43970743/article/details/161520390|2017
confidence: 高
```

---

## SD-230（公开经验库·公开）

```yaml
success_id: SD-230
problem_type: 路径优化与排班调度
method: 图论最短路径 + 多目标规划 + 分区巡检策略 + 错时排班优化 + 灵敏度分析
why_success: 巡检路线本质是图上的路径规划，图论法可求最短路径；多目标规划同时优化人力与工作量平衡；分区策略将26点划分为若干区域降低复杂度；错时排班可平滑需求峰值
result: 为化工厂26个巡检点设计巡检路线与排班方案，满足周期约束并最小化人力成本，同时考虑休息进餐与错时上班
limitations: 26点规模不大但约束复杂，精确求解困难；休息与进餐时间窗口增加排班复杂度；错时上班可能增加管理成本；未考虑紧急巡检需求
source: 2017年高教社杯全国大学生数学建模竞赛D题：巡检线路的排班|https://blog.csdn.net/weixin_43970743/article/details/161520407|2017
confidence: 高
```

---

## SD-231（公开经验库·公开）

```yaml
success_id: SD-231
problem_type: 多体静力学与多目标优化
method: 悬链线力学模型 + 隔离体受力分析 + 递推倾角关系 + 多目标非线性规划 + 熵权法 + 循环搜索
why_success: 系泊系统涉及浮标-钢管-钢桶-锚链的多体静力平衡，悬链线模型可准确描述锚链形状；隔离体受力分析建立各构件倾角递推关系；多目标规划同时优化吃水深度、游动区域、钢桶倾角；循环搜索适合小范围参数优化
result: 设计系泊系统（锚链型号、长度、重物球质量），使浮标吃水深度、游动区域和钢桶倾角最小
limitations: 刚体假设忽略弹性变形；悬链线模型仅适用于均匀链，实际锚链由多段组成；未考虑动态波浪力（仅静力）；问题3中水深变化范围大，需多次求解
source: 2016年高教社杯全国大学生数学建模竞赛A题：系泊系统的设计|https://blog.csdn.net/weixin_43970743/article/details/161519114|2016
confidence: 高
```

---

## SD-232（公开经验库·公开）

```yaml
success_id: SD-232
problem_type: 交通影响评价与仿真
method: AHP-熵权-TOPSIS综合评价 + 元胞自动机(NaSch模型) + BP神经网络 + 排队论 + 路网图模型
why_success: 问题1需综合评价小区开放影响，AHP-熵权-TOPSIS可整合多维度指标；问题2需模拟车辆微观行为，NaSch元胞自动机可刻画跟驰、换道、拥堵传播；BP神经网络可训练评价指标权重；排队论描述交叉口排队；路网图模型描述拓扑结构
result: 定量评价小区开放对周边道路通行的影响，建立车辆通行模型，向城市规划和交通管理部门提出建议
limitations: 元胞自动机网格尺寸影响仿真精度；BP神经网络需要训练数据，竞赛中数据有限；未考虑动态交通需求变化；小区类型抽象可能过于简化
source: 2016年高教社杯全国大学生数学建模竞赛B题：小区开放对道路通行的影响|https://blog.csdn.net/weixin_43970743/article/details/161520008|2016
confidence: 高
```

---

## SD-233（公开经验库·公开）

```yaml
success_id: SD-233
problem_type: 天文定位与参数反演
method: 太阳高度角公式 + 影长公式 + 启发式遍历搜索 + 粒子群优化(PSO) + 视频帧提取
why_success: 影长由太阳高度角决定，而太阳高度角由纬度、经度（通过时角）、日期（通过赤纬角）共同决定，建立闭合公式后可反演参数；启发式遍历保证全局性；PSO提高搜索效率；视频处理提取影子坐标
result: 根据直杆太阳影子顶点坐标数据，确定直杆所在地点（经纬度）与日期，并扩展到视频数据分析
limitations: 忽略大气折射导致低太阳高度角时误差增大；假设杆严格垂直；视频提取影子坐标受光照、地面纹理影响；遍历步长影响定位精度
source: 2015年高教社杯全国大学生数学建模竞赛A题：太阳影子定位|https://blog.csdn.net/qq_73954832/article/details/140455963|2015
confidence: 高
```

---

## SD-234（公开经验库·公开）

```yaml
success_id: SD-234
problem_type: 供需匹配与动态定价
method: 模糊综合评价 + 多元回归拟合 + 高斯分布模型 + Logit模型 + 等步长搜索 + 动态补贴优化
why_success: 问题1需评价供求匹配，模糊综合评价适合处理定性指标；多元回归可拟合供给/需求函数；问题2需分析补贴对拒单率、拼车率的影响，Logit模型适合二元选择；问题3需优化补贴金额，等步长搜索简单有效
result: 分析出租车市场供需匹配程度，评估现有补贴方案效果，设计新的动态补贴方案缓解打车难
limitations: 模糊综合评价权重主观；Logit模型参数估计需大量数据；动态补贴未考虑实时供需变化；仅分析静态均衡，未考虑动态演化
source: 2015年高教社杯全国大学生数学建模竞赛B题：互联网+时代的出租车资源配置|https://blog.csdn.net/weixin_43292788/article/details/142518644|2015
confidence: 高
```

---

## SD-235（公开经验库·公开）

```yaml
success_id: SD-235
problem_type: 动态调度与路径优化
method: 整数规划 + 启发式调度规则 + 遗传算法/粒子群优化 + 离散事件仿真
why_success: RGV调度是带时间窗和优先级的车辆路径问题，整数规划可精确建模但规模受限；启发式规则（如最近邻、最早截止期）计算快适合实时调度；遗传算法/粒子群可优化复杂目标；离散事件仿真验证策略效果
result: 优化智能RGV（轨道引导车）在CNC加工系统中的动态调度策略，最小化总加工时间或最大化设备利用率
limitations: 整数规划在CNC数量多时是NP-hard；启发式规则可能非最优；遗传算法参数选择依赖经验；未考虑多RGV冲突与协同
source: 2018年高教社杯全国大学生数学建模竞赛B题：智能RGV的动态调度策略|https://blog.csdn.net/gitblog_06777/article/details/148274765|2018
confidence: 中
```

---

## SD-236（公开经验库·公开）

```yaml
success_id: SD-236
problem_type: 体育数据分析与势头量化
method: PCA-TOPSIS综合评价 + 白噪声检验(Ljung-Box/Box-Pierce) + GM(1,1)灰色预测 + 灰色关联分析 + 隐马尔可夫模型(HMM) + 蒙特卡洛模拟
why_success: 问题1需量化势头，PCA-TOPSIS可融合18个指标综合评估；问题2需检验随机性，白噪声检验是标准统计方法；问题3需预测转折点，GM(1,1)适合小样本灾变预测；HMM可刻画比赛状态转移；蒙特卡洛验证模型稳健性
result: 建立网球比赛中'势头'的量化模型，评估势头是否随机，预测比赛转折点，为教练和选手提供策略建议
limitations: 势头定义主观，不同指标权重影响结果；灰色预测仅适用于中短期、小样本；HMM状态数选择依赖经验；未考虑选手心理因素的显式建模
source: 2024年美国大学生数学建模竞赛MCM C题：网球运动中的势头|https://arxiv.org/pdf/2402.12149.pdf|2024
confidence: 高
```

---

## SD-237（公开经验库·公开）

```yaml
success_id: SD-237
problem_type: 优化决策
method: 解析频率模型与多目标优化
why_success: 频率公式明确且面积功耗可解析表达
result: 在速度、面积、功耗约束下优化环形振荡器尺寸与晶圆布局
limitations: 未考虑寄生电容细节；版图连线仅近似
source: 2022华数杯数学建模A题环形振荡器的优化设计|https://www.bianchengbaodian.com/article/0d58bb48fc221cff4020253d3ae6e732.html|2022
confidence: 中
```

---

## SD-238（公开经验库·公开）

```yaml
success_id: SD-238
problem_type: 评价分类
method: 元胞自动机与交通流模型
why_success: 可模拟异质车辆与规则下的宏观流量
result: 评估靠右行驶规则对轻/重交通流量与安全的影响
limitations: 未完全刻画驾驶员异质行为；智能系统假设理想
source: 2014 MCM特等奖Outstanding论文A题下载-The Keep-Right-Except-To-Pass Rule|http://www.hanlin.com/archives/85463|2014
confidence: 高
```

---

## SD-239（公开经验库·公开）

```yaml
success_id: SD-239
problem_type: 预测
method: 交通波理论与排队论模型
why_success: 排队长度可由上下游流量差与波速推导
result: 估算车道被占用对道路实际通行能力与排队长度的影响
limitations: 未完全刻画驾驶人心理；视频检测有误差
source: 2013年国赛一等奖优秀论文A题车道被占用对城市道路通行能力的影响|https://m.renrendoc.com/p-85829993.html|2013
confidence: 高
```

---

## SD-240（公开经验库·公开）

```yaml
success_id: SD-240
problem_type: 评价分类
method: 模糊综合评价与优化规划
why_success: 先评价保障重要性再优化成本与损耗
result: 筛选重要供应商并制定经济原材料订购与转运方案
limitations: 未完全刻画市场价波动；转运分配简化
source: 2021年全国大学生数学建模竞赛题目C:生产企业原材料的订购与运输优秀论文范例|https://max.book118.com/html/2022/0816/5123202041004323.shtm|2021
confidence: 高
```

---

## SD-241（公开经验库·公开）

```yaml
success_id: SD-241
problem_type: 优化决策
method: 反射面形状调节优化模型
why_success: 需将促动器控制量映射到反射面误差
result: 调节FAST主动反射面使其逼近理想抛物面并提高接收比
limitations: 未考虑实时风振；理想面定义有近似
source: 2021年数模国赛题目优秀论文|https://download.csdn.net/download/weixin_67798981/88778695|2021
confidence: 高
```

---

## SD-242（公开经验库·公开）

```yaml
success_id: SD-242
problem_type: 预测
method: 回归模型与遗传算法优化
why_success: 可解释变量边际效应并寻优
result: 分析催化剂组合与温度对乙醇转化率及C4烯烃选择性的影响并优化收率
limitations: 未完全建模反应动力学；外推至新配方需谨慎
source: 开源一份2021年数学建模国赛B题全国二等奖的完整论文|https://juejin.cn/post/7083785524917305380|2021
confidence: 中
```

---

## SD-243（公开经验库·公开）

```yaml
success_id: SD-243
problem_type: 预测
method: 灰色预测与多目标规划
why_success: 小样本趋势预测后做资源配置
result: 制定中国至2025年水资源供需、调蓄、淡化与成本效益战略
limitations: 未细化流域水文随机性；国际河流约束简化
source: 2013 MCM特等奖Outstanding论文B题下载-Water, Water, Everywhere|https://www.hanlin.com/archives/category/bonus/documents/page/48|2013
confidence: 高
```

---

## SD-244（公开经验库·公开）

```yaml
success_id: SD-244
problem_type: 优化决策
method: 混合整数线性规划(MILP)
why_success: 精确求解器可保证物理可行与成本最优
result: 在电气约束下优化微电网日前经济调度
limitations: 未考虑设备启停非线性细节；预测误差需鲁棒处理
source: 全国大学生电工数学建模竞赛|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2018
confidence: 中
```

---

## SD-245（公开经验库·公开）

```yaml
success_id: SD-245
problem_type: 优化决策
method: 阿克曼转向几何与网格寻优
why_success: 进出所需通道宽度可由几何严格推导
result: 在不规则场地上设计停车场使容量大且车辆可自由出入
limitations: 未考虑实时驾驶行为；异型车辆混合简化
source: 全国大学生电工数学建模竞赛|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2019
confidence: 中
```

---

## SD-246（公开经验库·公开）

```yaml
success_id: SD-246
problem_type: 优化决策
method: 动态规划与目标规划
why_success: 多层物料与生产提前期适合阶段决策
result: 制定水下机器人组件与成品的组装生产计划
limitations: 未考虑随机缺件；需求分布外生
source: 2022华数杯|https://blog.csdn.net/weixin_43292788/category_11968618.html|2022
confidence: 中
```

---

## SD-247（公开经验库·公开）

```yaml
success_id: SD-247
problem_type: 数据挖掘与管网优化
method: 描述统计 + 时间序列分析 + 灰色预测模型 + 层级水力平衡 + 成本效益分析 + 漏损定位模型
why_success: 问题1需探索性分析用水规律；问题2需建立水表层级关系模型；问题3需漏损分析；问题4需漏损定位；问题5需维修决策优化；灰色预测适合小样本中长期预测；水力平衡可识别异常节点
result: 基于智能水表数据建立校园供水系统分析模型，识别用水规律、漏损位置并制定最优维修决策
limitations: 水表可能存在测量误差；漏损定位精度受水表密度限制；灰色预测对数据波动性敏感；未考虑季节性用水突变
source: 2020年高教社杯全国大学生数学建模竞赛E题：校园供水系统智能管理|https://blog.csdn.net/weixin_43292788/article/details/144255198|2020
confidence: 高
```

---

## SD-248（公开经验库·公开）

```yaml
success_id: SD-248
problem_type: 组合优化与生产调度
method: 序贯算法 + 多目标规划 + 整数规划(Lingo) + 图论 + 五步确色法 + 分类优化策略
why_success: 汽车装配线约束极其复杂（品牌/配置/动力/驱动/颜色五维度），且约束间可能冲突；序贯算法按优先级（品牌→驱动→动力→颜色→配置）逐层分解多目标问题为单目标问题；整数规划可精确建模；图论描述颜色允许连接关系；五步确色法系统化确定颜色顺序
result: 在满足多属性工艺约束下，优化汽车总装线装配顺序，最小化生产成本（换色/换配置/换动力等切换成本）
limitations: 序贯算法可能非全局最优（优先级主观）；整数规划规模随车辆数增大而爆炸；未考虑动态调整（如临时插单）；颜色规则复杂，完全枚举不可行
source: 2018年高教社杯全国大学生数学建模竞赛D题：汽车总装线的配置问题|https://jishuzhan.net/article/1836921021442035713|2018
confidence: 高
```

---

## SD-249（公开经验库·公开）

```yaml
success_id: SD-249
problem_type: 曲线拟合与参数预测
method: 指数函数拟合 + 反函数多项式拟合 + 分段建模（波动段/稳定段） + 插值法 + MRE评估
why_success: 放电曲线前期波动大、后期平缓，指数函数可刻画衰减趋势但不便求解；反函数多项式将求解放电时间转化为计算函数值；分段建模分别处理波动段与稳定段；插值法连接离散电流数据到连续模型；MRE客观评估拟合精度
result: 建立铅酸电池放电曲线模型，预测不同电流强度下的剩余放电时间，评估模型精度
limitations: 指数模型对初始波动拟合不佳；反函数多项式为近似，存在误差；分段点（拐点）选择主观；插值在电流边界外推不可靠
source: 2016年高教社杯全国大学生数学建模竞赛C题：电池剩余放电时间预测|https://www.ppmy.cn/embedded/119988.html|2016
confidence: 高
```

---

## SD-250（公开经验库·公开）

```yaml
success_id: SD-250
problem_type: 轨道力学与最优控制
method: 开普勒定律 + 机械能守恒 + 牛顿第二定律动力学模型 + 轨迹离散化迭代 + 最优控制 + 高程图平坦度分析 + 灵敏度分析
why_success: 问题1用开普勒定律和机械能守恒确定椭圆轨道参数；问题2用牛顿第二定律建立六阶段动力学模型，以燃料最小为目标；轨迹离散化迭代适合非线性ODE数值求解；高程图分析用于避障段着陆点选择；灵敏度分析评估参数影响
result: 设计嫦娥三号软着陆轨道与六阶段最优控制策略，使燃料消耗最小并满足各阶段状态约束
limitations: 忽略月球引力非球项；假设引力场均匀；未考虑姿态控制发动机燃料消耗；离散化步长影响精度；高程图分辨率有限
source: 2014年高教社杯全国大学生数学建模竞赛A题：嫦娥三号软着陆轨道设计与控制策略|https://blog.csdn.net/weixin_43970743/article/details/161518779|2014
confidence: 高
```

---

## SD-251（公开经验库·公开）

```yaml
success_id: SD-251
problem_type: 几何建模与结构优化
method: 空间解析几何 + 定轴转动模型 + 多目标优化(MOP) + 图像法可行域分析 + 静力学平衡
why_success: 折叠桌动态变化可由杆件定轴转动描述，空间解析几何计算各木条位置与高度；多目标优化同时考虑稳固性（重心最低）、材料最少、加工方便；图像法可直观确定可行域；静力学平衡保证使用安全
result: 建立平板折叠桌动态变化模型，确定最优设计加工参数（平板尺寸、钢筋位置、开槽长度），使产品稳固性好、加工方便、用材最少
limitations: 忽略摩擦力导致实际开槽长度需留余量；刚体假设忽略木条弹性变形；多目标权重主观；图像法精度有限
source: 2014年高教社杯全国大学生数学建模竞赛B题：创意平板折叠桌|https://jishuzhan.net/article/1845398393514364929|2014
confidence: 高
```

---

## SD-252（公开经验库·公开）

```yaml
success_id: SD-252
problem_type: 交通流分析与排队预测
method: 城市交通二流理论 + 非线性比例尺改进算法 + BP神经网络 + 遗传算法优化 + 元胞自动机(NaSch模型)
why_success: 问题3需建立排队长度与多因素关系，二流理论是交通流经典理论；BP神经网络可捕捉非线性；遗传算法优化网络权重；问题4需预测排队长度到达上游路口的时间，元胞自动机适合微观交通仿真，可直观模拟车辆排队演化
result: 分析交通事故导致车道被占用对城市道路通行能力的影响，建立排队长度预测模型
limitations: 二流理论假设理想条件，实际道路复杂；BP神经网络需要足够训练样本；元胞自动机网格尺寸影响精度；未考虑驾驶员行为差异
source: 2013年高教社杯全国大学生数学建模竞赛A题：车道被占用对城市道路通行能力的影响|https://blog.csdn.net/weixin_43292788/article/details/142876944|2013
confidence: 高
```

---

## SD-253（公开经验库·公开）

```yaml
success_id: SD-253
problem_type: 统计分析与品质评价
method: 配对t检验/方差分析 + 主成分分析(PCA) + 聚类分析 + 相关分析 + 回归分析
why_success: 问题1需判断两组品酒员评分差异，t检验/ANOVA是标准统计方法；问题2需对葡萄分级，PCA降维后聚类适合；问题3需分析理化指标与品质关系，相关分析与回归可量化影响
result: 分析两组品酒员对葡萄酒的评价结果，建立分级评价体系，分析酿酒葡萄与葡萄酒理化指标对品质的影响
limitations: 品酒员主观偏好影响评分客观性；样本量小（27/28种），聚类结果可能不稳定；芳香物质数据维度高且与理化指标关系复杂；分级标准主观性强
source: 2012年高教社杯全国大学生数学建模竞赛A题：葡萄酒的评价|https://blog.51cto.com/u_16213621/12369495|2012
confidence: 高
```

---

## SD-254（公开经验库·公开）

```yaml
success_id: SD-254
problem_type: 环境评价与污染溯源
method: 单因子指数 + 内梅罗综合指数 + IDW反距离权重插值 + 克里金插值 + 主成分分析(PCA) + 高斯扩散衰减模型 + 相关分析
why_success: 问题1需评价污染程度，单因子指数和综合指数是环境评价标准方法；空间分布需插值，IDW和克里金适合；问题2需识别污染原因，PCA可提取主要污染因子；问题3需定位污染源，高斯扩散模型可反演污染源位置
result: 分析城市表层土壤重金属空间分布、污染程度、污染原因，并定位污染源位置
limitations: 插值精度受采样点密度限制；高斯扩散模型假设均匀介质，实际土壤异质性强；PCA结果解释主观；污染源数量需预设
source: 2011年高教社杯全国大学生数学建模竞赛A题：城市表层土壤重金属污染分析|https://blog.csdn.net/weixin_43292788/article/details/142920057|2011
confidence: 高
```

---

## SD-255（公开经验库·公开）

```yaml
success_id: SD-255
problem_type: 图像拼接与模式识别
method: 像素差边缘匹配 + 相关系数匹配 + 贪心算法 + 行列分离策略 + 2-opt局部搜索优化 + 行首行尾特征识别
why_success: 问题1为1D拼接，像素差和相关系数可量化边缘匹配度；贪心算法快速构建初始解；问题2为2D拼接，行列分离策略将2D降为1D+1D，降低复杂度；2-opt可优化局部错误；行首行尾特征（如空白、标点）辅助定位边界
result: 建立碎纸片拼接复原模型，对单面/双面打印、横纵切、中文/英文碎纸片进行自动拼接复原
limitations: 贪心算法可能陷入局部最优；碎片边缘噪声影响匹配精度；2-opt对大规模问题改进有限；未考虑碎片旋转和缩放
source: 2013年高教社杯全国大学生数学建模竞赛B题：碎纸片的拼接复原|https://blog.csdn.net/weixin_43970743/article/details/161518701|2013
confidence: 高
```

---

## SD-256（公开经验库·公开）

```yaml
success_id: SD-256
problem_type: 几何体积计算与参数反演
method: 微元法 + 投影法 + 截面法 + 分类讨论（8种情形） + 最小二乘参数识别 + 误差分析
why_success: 储油罐体积计算是经典几何问题，微元法可处理复杂截面；投影法和截面法处理变位后的三维几何；分类讨论覆盖不同油位高度下的不同几何形态（如油面与罐底/顶的关系）；最小二乘从实测数据反演变位参数
result: 建立储油罐变位后罐容表标定模型，识别纵向倾斜角α和横向偏转角β，给出变位后油位高度与储油量的对应关系
limitations: 变位后几何情形分类复杂（问题2有8种）；近似处理（投影法）引入误差；球冠体部分积分复杂；参数识别可能多解
source: 2010年高教社杯全国大学生数学建模竞赛A题：储油罐的变位识别与罐容表标定|https://blog.csdn.net/weixin_43292788/article/details/142970050|2010
confidence: 高
```

---

## SD-257（公开经验库·公开）

```yaml
success_id: SD-257
problem_type: 排队论与调度优化
method: 排队论 + SPTF算法 + 动态延时因子EDD算法 + 余弦分布满意度函数 + 综合评价指数模型 + 轮盘赌随机模拟
why_success: 病床安排本质是带优先级的排队调度问题，SPTF和EDD是经典调度算法；动态延时因子可根据手术日期对白内障病人进行时延调整，避免过早入院占用床位；余弦函数刻画满意度随等待时间的非线性衰减；综合评价指数兼顾病人满意度与医院利益
result: 优化眼科病床安排策略，缩短病人等待队列，提高病床利用率与病人满意度
limitations: 假设病人到达率为常数，实际可能有季节性波动；满意度函数参数主观；未考虑病人个体差异（如病情严重程度）；仿真次数有限，极端情况覆盖不足
source: 2009年高教社杯全国大学生数学建模竞赛B题：眼科病床的合理安排|https://blog.csdn.net/weixin_43292788/article/details/143105580|2009
confidence: 高
```

---

## SD-258（公开经验库·公开）

```yaml
success_id: SD-258
problem_type: 计算机视觉与几何标定
method: 针孔相机模型 + 交比不变性 + 最小二乘椭圆拟合 + 迭代法求公切线 + 最小二乘标定
why_success: 问题1需从变形的圆像中提取圆心，交比不变性在透视投影下保持，可利用切线交点精确定位；问题2需拟合椭圆参数，最小二乘稳健；问题3需标定相机参数，针孔模型+最小二乘是标准方法；问题4需双目标定，迭代法求公切线可确定对应关系
result: 建立数码相机定位模型，从靶标圆的变形像中精确提取圆心像坐标，实现双目相机系统标定
limitations: 针孔模型忽略镜头畸变；迭代法初值选择影响收敛；交比不变性要求四点共线，实际中需精心选择切点；椭圆拟合对噪声敏感
source: 2008年高教社杯全国大学生数学建模竞赛A题：数码相机定位|https://blog.csdn.net/weixin_43970743/article/details/161517516|2008
confidence: 高
```

---

## SD-259（公开经验库·公开）

```yaml
success_id: SD-259
problem_type: 教育经济学与定价模型
method: 波特五力模型 + 拉姆齐定价模型 + 合作博弈模型 + 最小二乘回归 + 层次分析法(AHP)
why_success: 学费问题涉及多方利益（政府、学校、学生、家庭），波特五力分析竞争环境；拉姆齐定价在成本回收与效率间平衡；合作博弈刻画多方博弈均衡；AHP确定指标权重；回归分析量化影响因素
result: 建立高等教育学费标准的定量分析模型，平衡学校培养质量、学生支付能力与政府财政投入
limitations: 数据收集困难，部分指标难以量化；拉姆齐定价假设完全信息，实际信息不对称；博弈模型均衡解可能不唯一；未考虑动态调整机制
source: 2008年高教社杯全国大学生数学建模竞赛B题：高等教育学费标准探讨|https://sx.xxu.edu.cn/info/1035/1357.htm|2008
confidence: 中
```

---

## SD-260（公开经验库·公开）

```yaml
success_id: SD-260
problem_type: 人口预测与动态建模
method: Logistic增长模型 + Leslie矩阵模型 + 分要素计算法 + 多元线性回归 + 时变参数Leslie矩阵 + 分性别分城乡扩展模型
why_success: 问题1需建立人口结构模型，Leslie矩阵是人口预测的标准工具，可按年龄结构递推；Logistic提供总量参考；分要素计算法分别预测出生、死亡、迁移；时变参数Leslie矩阵可反映生育率、死亡率随时间变化；分性别分城乡扩展模型更精细刻画结构变化
result: 建立中国人口增长预测模型，考虑老龄化、性别比、城镇化等新特点，进行中短期与长期预测
limitations: Leslie矩阵假设生育率、死亡率稳定，长期预测误差累积；分城乡数据不完整，部分参数需估计；未考虑政策突变（如全面二孩）；长期预测不确定性大
source: 2007年高教社杯全国大学生数学建模竞赛A题：中国人口增长预测|https://blog.csdn.net/weixin_43970743/article/details/161517385|2007
confidence: 高
```

---

## SD-261（公开经验库·公开）

```yaml
success_id: SD-261
problem_type: 图论最短路径与多目标优化
method: 0-1整数规划 + Dijkstra算法 + BFS广度优先搜索 + 邻接算法 + 分层序列法 + 多目标优化 + 有向赋权图
why_success: 公交查询本质是图上的最短路径问题，Dijkstra适合单源最短路径；BFS适合无权图或分层搜索；0-1整数规划可精确建模多目标（时间/费用/转乘次数）；分层序列法按优先级（转乘次数>时间>费用）逐层优化；有向赋权图将不同目标量化为不同权重
result: 建立公交查询系统的最佳乘车方案模型，支持公汽、地铁混乘，考虑转乘次数、时间、费用等多目标
limitations: 预建直达数据库占用空间大；环行线路抽象为4条路线增加复杂度；未考虑实时交通拥堵；步行换乘问题3扩展复杂
source: 2007年高教社杯全国大学生数学建模竞赛B题：乘公交，看奥运|https://www.docin.com/p-557988980.html|2007
confidence: 高
```

---

## SD-262（公开经验库·公开）

```yaml
success_id: SD-262
problem_type: 资源配置与多目标优化
method: 熵权法 + TOPSIS + 强势系数模型 + Lingo整数规划 + 稳定性约束优化
why_success: 问题1需将总书号分配给各分社，TOPSIS可综合评价分社强势程度；熵权法客观赋权；整数规划精确求解分配方案；稳定性约束避免分配剧烈波动；问题2需将分社书号分配到具体课程，层次化优化降低复杂度
result: 优化出版社书号资源分配，使总利润最大同时支持强势分社和长期发展
limitations: 强势系数构建主观；假设销售额与书号数线性关系可能不成立；未考虑新书号的市场培育期；整数规划规模受限
source: 2006年高教社杯全国大学生数学建模竞赛A题：出版社的资源配置|https://blog.csdn.net/getusushu/article/details/132582371|2006
confidence: 高
```

---

## SD-263（公开经验库·公开）

```yaml
success_id: SD-263
problem_type: 纵向数据分析与疗效评价
method: 多项式回归 + 线性混合效应模型(LME) + 模糊聚类 + BP神经网络 + 多元线性回归 + 成本效益双目标规划 + 面积比较整体最优法
why_success: 问题1需从纵向数据（重复测量）中提取疗效趋势，多项式回归拟合CD4时间曲线，LME处理个体间差异；问题2需比较四种疗法，模糊聚类分类病人，多元回归预测各疗法CD4曲线；问题3引入费用，双目标规划平衡疗效与成本；面积比较法综合评估整体优劣
result: 评价四种艾滋病疗法的疗效，预测继续治疗效果，考虑经济因素给出最优治疗方案
limitations: 纵向数据存在缺失和不规则时间间隔；LME对样本量有要求；模糊聚类类别数需预设；双目标规划中偏好系数主观
source: 2006年高教社杯全国大学生数学建模竞赛B题：艾滋病疗法的评价及疗效的预测|https://blog.csdn.net/weixin_43970743/article/details/161517254|2006
confidence: 高
```

---

## SD-264（公开经验库·公开）

```yaml
success_id: SD-264
problem_type: 环境评价与污染预测
method: 单因子指数法 + 模糊综合评价 + 一维稳态水质模型 + GM(1,1)灰色预测 + 一元线性回归
why_success: 问题1需水质评价，单因子指数和模糊综合评价是标准方法；问题2需污染溯源，一维稳态水质模型（质量守恒+降解）可反推各江段排污量；问题3需长期预测，GM(1,1)适合小样本趋势预测；问题4需污水处理量估算，回归分析建立污水量与水质关系
result: 对长江水质进行定量综合评价，定位主要污染源，预测未来十年水质趋势及污水处理需求
limitations: 一维模型忽略横向和垂向混合；降解系数k需经验估计；灰色预测对数据质量敏感；未考虑极端气候和突发污染事件
source: 2005年高教社杯全国大学生数学建模竞赛A题：长江水质的评价和预测|https://blog.csdn.net/weixin_43970743/article/details/161512894|2005
confidence: 高
```

---

## SD-265（公开经验库·公开）

```yaml
success_id: SD-265
problem_type: 库存决策与资源分配
method: 概率统计 + 0-1整数线性规划 + 满意度最大化模型 + 两阶段随机优化 + 贪心算法
why_success: 问题1为库存决策，需用概率统计估计需求；问题2为分配问题，0-1整数规划可精确建模；问题3需同时考虑采购与分配，两阶段随机优化适合；贪心算法可作为快速近似解
result: 设计DVD在线租赁系统的库存策略与分配方案，保证会员满意度同时最小化DVD采购量
limitations: 假设会员行为稳定，实际可能有季节性；0-1规划规模随会员和DVD数增大；满意度量化主观；未考虑DVD磨损和淘汰
source: 2005年高教社杯全国大学生数学建模竞赛B题：DVD在线租赁|https://blog.csdn.net/weixin_43970743/article/details/161513314|2005
confidence: 高
```

---

## SD-266（公开经验库·公开）

```yaml
success_id: SD-266
problem_type: 商业网点规划与人流预测
method: 统计规律挖掘 + Dijkstra最短路径 + 人流量分布模型 + 整数规划(MS网点优化) + 聚类分析
why_success: 问题1需从问卷数据挖掘出行、餐饮、购物规律；问题2需预测人流量，Dijkstra可模拟最短路径选择；问题3需优化MS网点布局，整数规划可精确求解类型和数量；聚类分析识别消费模式
result: 预测奥运会期间商区人流量，设计MS（Mini Supermarket）临时超市网点类型与数量，使利润最大且满足购物需求
limitations: 问卷调查样本代表性有限；Dijkstra假设所有人选择最短路径，实际可能绕行；未考虑MS间竞争；消费行为假设简化
source: 2004年高教社杯全国大学生数学建模竞赛A题：奥运会临时超市网点设计|https://blog.csdn.net/weixin_43970743/article/details/161508748|2004
confidence: 高
```

---

## SD-267（公开经验库·公开）

```yaml
success_id: SD-267
problem_type: 生物经济建模与多阶段优化
method: 盈亏平衡分析 + 整数规划(Lingo) + 最小二乘拟合 + 0-1变量动态规划 + 多目标优化
why_success: 问题1为盈亏平衡分析，确定最低产仔量；问题2为规模优化，整数规划可精确求解种猪比例与存栏数；问题3引入价格波动，需用0-1变量决策配种与出栏时机，最小二乘拟合价格-饲料关系，多目标优化平衡存栏与利润
result: 建立生猪养殖场经营管理模型，确定盈亏平衡点、最优养殖规模与经营策略，实现利润最大化
limitations: 假设价格不变或按历史趋势外推，实际波动大；未考虑疫病、自然灾害等风险；种猪淘汰率假设为固定值；整数规划规模随时间延长而增大
source: 2014年高教社杯全国大学生数学建模竞赛C题：生猪养殖场的经营管理|https://www.ppmy.cn/embedded/127230.html|2014
confidence: 高
```

---

## SD-268（公开经验库·公开）

```yaml
success_id: SD-268
problem_type: 结构变形监测与预测
method: 最小二乘平面拟合 + 优化模型求中心 + 空间曲线拟合 + 坐标旋转变换 + 灰色预测模型(GM)
why_success: 问题1需从8个观测点确定层中心，最小二乘拟合平面后优化求距离平方和最小点；问题2需量化三种变形，倾斜用三角函数，弯曲用空间曲线曲率，扭曲用坐标变换角度；问题3数据少（仅4次），灰色预测适合小样本趋势预测
result: 根据多次测量数据确定古塔各层中心位置，量化倾斜、弯曲、扭曲变形，预测变形趋势
limitations: 4次测量数据极少，灰色预测精度有限；假设变形仅三种因素，忽略沉降、裂缝等；观测点固定假设可能不成立（测量误差）；中心点定义主观（距离平方和最小）
source: 2013年高教社杯全国大学生数学建模竞赛C题：古塔的变形|https://blog.csdn.net/weixin_43292788/article/details/142879150|2013
confidence: 高
```

---

## SD-269（公开经验库·公开）

```yaml
success_id: SD-269
problem_type: 光伏建筑一体化设计
method: 几何布局优化 + 辐射量计算 + 线性/整数规划 + 多目标优化 + 贪心算法 + 模拟退火
why_success: 问题需同时优化电池类型选择、布局、倾角、逆变器匹配，是多约束组合优化；几何优化处理空间布局；线性/整数规划处理离散选择；多目标优化平衡发电量与成本；贪心/模拟退火适合大规模组合搜索
result: 设计太阳能小屋的光伏电池铺设方案，使年发电量最大且单位发电成本最小
limitations: 辐射模型简化，未考虑周围建筑遮挡；电池温度效应未建模；几何布局为近似处理；多目标权重主观
source: 2012年高教社杯全国大学生数学建模竞赛B题：太阳能小屋的设计|https://blog.csdn.net/weixin_43292788/article/details/142903938|2012
confidence: 中
```

---

## SD-270（公开经验库·公开）

```yaml
success_id: SD-270
problem_type: 设施选址与警力调度优化
method: 0-1整数规划 + 罚函数优化 + 模拟退火 + 多对少指派模型 + 图论最短路径 + 计算机仿真检验
why_success: 管辖分配是0-1指派问题；3分钟约束用罚函数处理；工作量均衡用模拟退火优化；封锁调度是多对少指派；围堵方案需图论最短路径；仿真检验不同车速与目标下的方案稳健性
result: 优化交巡警服务平台设置、管辖范围分配、警力调度与围堵方案，实现3分钟出警与工作量均衡
limitations: 假设路径为直线，实际道路弯曲；发案率假设稳定，实际可能时变；模拟退火参数选择影响结果；围堵模型未考虑实时信息更新
source: 2011年高教社杯全国大学生数学建模竞赛B题：交巡警服务平台的设置与调度|https://www.ppmy.cn/embedded/129890.html|2011
confidence: 高
```

---

## SD-271（公开经验库·公开）

```yaml
success_id: SD-271
problem_type: 时间序列预测与经济影响评估
method: 时间序列分解 + 趋势外推加权拟合 + ARMA(2,1)模型 + 凯恩斯乘数原理 + 回归分析
why_success: 问题1需预测参观人数，时间序列分解可分离长期趋势与随机波动，ARMA(2,1)适合处理有自相关的时间序列；问题2需评估经济影响，凯恩斯乘数原理是宏观经济标准工具，回归分析可拟合投资-增加值关系
result: 定量评估2010年上海世博会对上海市旅游业的影响力，预测参观人数与旅游投资增量
limitations: ARMA模型对突发事件（如恶劣天气）预测差；乘数原理假设边际消费倾向稳定；反事实情景（无世博会）无法真实观测；仅分析旅游业，未考虑其他产业溢出
source: 2010年高教社杯全国大学生数学建模竞赛B题：上海世博会影响力的定量评估|https://blog.csdn.net/weixin_43292788/article/details/142971912|2010
confidence: 高
```

---

## SD-272（公开经验库·公开）

```yaml
success_id: SD-272
problem_type: 机电系统控制与能量补偿
method: 刚体力学 + 能量守恒 + 离散时间迭代控制 + 反馈控制 + Laplace变换设计
why_success: 问题1-2为刚体力学计算转动惯量；问题3基于能量守恒建立电流-可观测量的关系；问题4评价能量误差；问题5设计前一时间段观测值推导本时段电流的迭代控制；问题6引入反馈和Laplace变换改进，证明N足够大时能量误差近似为零
result: 建立制动器试验台驱动电流控制模型，补偿机械惯量不足，使试验台模拟与路试能量一致
limitations: 假设减速度为常数，实际制动过程非线性；忽略观测误差和离散化误差；反馈控制存在时延；Laplace变换设计复杂度高
source: 2009年高教社杯全国大学生数学建模竞赛A题：制动器试验台的控制方法分析|https://blog.csdn.net/weixin_43292788/article/details/142999700|2009
confidence: 高
```

---

## SD-273（公开经验库·公开）

```yaml
success_id: SD-273
problem_type: 产品几何优化与成本分析
method: 微积分极值 + 拉格朗日乘数法 + 多目标优化 + 实际测量验证 + 灵敏度分析
why_success: 问题2为简单圆柱体，可用微积分求解析最优；问题3为圆柱+圆台组合，需多目标优化同时考虑材料、美观、工艺；问题4需考虑焊缝长度等实际约束；拉格朗日乘数法处理等式约束
result: 优化易拉罐形状和尺寸，在容积固定（355ml）下使材料最省，并考虑美观和工艺约束
limitations: 假设壁厚均匀，实际顶盖更厚；未考虑制造工艺（拉伸、冲压）限制；美观标准主观；实际测量误差影响
source: 2006年高教社杯全国大学生数学建模竞赛C题：易拉罐形状和尺寸的最优设计|https://blog.csdn.net/weixin_43970743/article/details/161517298|2006
confidence: 高
```

---

## SD-274（公开经验库·公开）

```yaml
success_id: SD-274
problem_type: 房地产众筹规划与税务优化
method: Excel核算 + 线性规划(Lingo) + 满意度最大化模型 + 投资回报率约束优化
why_success: 问题1为复杂税务核算，Excel适合分步计算；问题2需重新设计套数，线性规划可优化满意度；问题3需保证投资回报率≥25%，需增加约束重新优化；土地增值税核算涉及四级累进，需分步判断
result: 核算众筹筑屋项目成本收益，重新设计规划方案满足参筹者意愿，确保投资回报率达标
limitations: 土地增值税核算复杂，普通/非普通住宅划分影响大；参筹者意愿与实际需求可能有偏差；线性规划假设满意度与套数线性关系；未考虑市场风险和建设周期
source: 2015年高教社杯全国大学生数学建模竞赛D题：众筹筑屋规划方案设计|https://blog.csdn.net/weixin_43292788/article/details/142817037|2015
confidence: 高
```

---

## SD-275（公开经验库·公开）

```yaml
success_id: SD-275
problem_type: 风能资源评估与运维优化
method: 描述统计 + 威布尔分布(极大似然估计) + 二次拟合功率曲线 + 整数规划排班 + 枚举法周期优化
why_success: 问题1需风能资源评估，威布尔分布是风速标准模型，极大似然法精度高；问题2需比较风机，功率曲线拟合可定量评估发电量；问题3为排班优化，整数规划适合离散决策，枚举法确定最小周期
result: 评估风电场风能资源与利用效率，判断新型风机适用性，优化维修人员排班与风机维护计划
limitations: 威布尔分布假设风速独立，实际可能有持续性；功率曲线拟合仅用二次函数，高风速区可能偏差；排班模型未考虑恶劣天气；忽略风机故障随机性
source: 2016年高教社杯全国大学生数学建模竞赛D题：风电场运行状况分析及优化|https://blog.csdn.net/2403_87108415/article/details/149509195|2016
confidence: 高
```

---

## SD-276（公开经验库·公开）

```yaml
success_id: SD-276
problem_type: 气象预报评价与空间插值
method: 反距离加权插值(IDW) + 三重/五重循环算法 + 动态权重调节 + 高程修正 + 误差统计
why_success: 预报网格与观测站点不重合，需插值将观测值转换到网格点；反距离加权简单有效；动态权重解决站点分布不均；高程修正考虑地形影响；五重循环高效计算大规模网格误差
result: 评价两种6小时雨量预报方法的准确性，建立科学的预报评价模型
limitations: IDW插值对站点密度敏感；高程修正因子需经验确定；仅考虑空间误差，未考虑时间序列特征；41天样本量有限
source: 2005年高教社杯全国大学生数学建模竞赛C题：雨量预报方法的评价|https://blog.csdn.net/2301_80194165/article/details/148932086|2005
confidence: 高
```

---

## SD-277（公开经验库·公开）

```yaml
success_id: SD-277
problem_type: 综合评价/数据预测
method: 因子分析提取主因子 + 因子得分排序 + AHP赋权交叉验证
why_success: 论文用SPSS对规范化后的5指标评价矩阵做因子分析，因子1特征值4.054、累积贡献率81.087%（>80%）即可用单因子代表五指标；因子载荷均>0.5（参观人数0.9679、活动场数0.9571、场馆规模0.9022、参展国0.8780、持续时间0.7852），说明该因子能解释影响力。AHP用于经济侧指标赋权（权重向量0.0833/0.3333/0.1667/0.1667/0.25）做独立验证。
result: 选择若干指标定量评估2010年上海世博会的影响力, 并与往届世博会比较
limitations: 仅取单因子（累积81.087%）会损失约19%方差信息；因子得分基于历史四届数据，外推至文化/社会维度需另建模型；AHP判断矩阵依赖专家打分，存在主观性
source: 全国建模比赛一等奖 2010年上海世博会影响力的定量评估|https://max.book118.com/html/2020/0622/5120103111002310.shtm|2010
confidence: 高
```

---

## SD-278（公开经验库·公开）

```yaml
success_id: SD-278
problem_type: 空间分析/环境评价
method: 克里金插值空间可视化 + 因子分析/相关分析识别污染源 + 内梅罗/地累积指数评价 + 对流弥散模型反演源点
why_success: 论文用Surfer克里金画出8种金属等值图；单因子与内梅罗综合指数评价污染程度，得出功能区排序 工业区>交通区>生活区>公园绿地区>山区；对8金属做相关与因子分析，Cr/Ni/Cu在因子1、As/Cd/Pb/Zn在因子2、Hg单独在因子3，识别同源；第三问用对流弥散(二阶偏微分)反演污染源。
result: 分析城市表层土壤8种重金属污染的空间分布, 确定污染源, 并评价污染程度
limitations: 采样密度有限，插值外推精度受限；因子分析对污染源解释有主观性(需结合地质背景)；对流弥散模型忽略复杂地形与化学反应
source: 2011年全国大学生数模竞赛全国一等奖论文(城市表层土壤重金属污染分析)|https://max.book118.com/html/2019/0524/6003215231002032.shtm|2011
confidence: 高
```

---

## SD-279（公开经验库·公开）

```yaml
success_id: SD-279
problem_type: 精算/数据预测
method: Logistic工资预测 + 替代率精算模型 + 资金缺口收支平衡模型 + 5因素灵敏度分析
why_success: 论文用Logistic模型(渐近线254220元、增长率0.1416)预测2011-2035山东省平均工资;按国发26/38号构建替代率精算公式,测算替代率22.96%~57.31%;建缺口模型得典型缺口R=691432元、替代率45.656%;对缴费年限/领取年限/利率/统筹比例/个人账户比例5因素做灵敏度分析。
result: 预测未来工资, 测算养老金替代率与资金缺口, 评价制度改革效果
limitations: 假设工资严格Logistic, 未考虑短期经济波动；灵敏度假设单因素独立变动, 未考虑因素交互；缺口模型简化利息(直接并入首年)
source: 企业退休职工养老金制度的改革方案(大学生数学建模国家一等奖)|https://doc.guandang.net/sa971d8cd3fed93f0a060cd94.html|2011
confidence: 高
```

---

## SD-280（公开经验库·公开）

```yaml
success_id: SD-280
problem_type: 医学统计/数据预测
method: 描述性统计 + 单因素分析筛选 + SPSS逐步(后退法)多元线性回归
why_success: 论文先用SPSS对性别/年龄/职业做描述统计(男:女=1.17:1, 高峰71-80岁, 农民最多), 再对10个气象特征做单因素与相关性分析剔除不显著项, 用后退法多元线性回归建立发病率与气象因素关系; 逐步回归模型 R²=0.918, F=19.66, P=0.000657 通过显著性检验(来源:2012数学建模论文)。
result: 分析脑卒中发病率与环境因素(气温/气压/湿度)的关系, 建立预测模型并提出干预建议
limitations: 日发病率与气象整体线性相关性不大, 仅平均湿度等少数变量显著；未充分建模滞后效应；数据粒度为日均值, 忽略短时波动
source: 脑卒中发病环境因素分析及干预(2012国赛数学建模国家一等奖)|https://doc.xuehai.net/bec44fb1ced23f185c659750f.html|2012
confidence: 高
```

---

## SD-281（公开经验库·公开）

```yaml
success_id: SD-281
problem_type: 交通流/数据预测
method: 横断面实际通行能力动态模型 + 交通波理论排队长度估算 + 差异度模型比较占道影响
why_success: 论文统计上下游通行量换算标准车当量(pcu), 建立横截面实际通行能力动态模型得事故点通行能力16.8 pcu/min、3min后堵塞; 用交通波理论推导完全/不完全堵塞两种排队长度估算公式(与实际关联度0.79/0.68); 用差异度模型得占2/3车道比占1/2车道通行能力影响大6.9%。
result: 根据视频数据计算车道被占用对道路通行能力的影响程度, 并建立通行能力与排队长度预测模型
limitations: 泊松到达假设在高峰不成立；视频数据精度限制参数标定；不同论文对信号灯处理不同(有/无周期)
source: 车道占用对城市道路通行能力影响(2013高教社杯优秀论文选登, 华中科技大学)|https://dxs.moe.gov.cn/zx/a/qkt_sxjm/131112/1249183.shtml|2013
confidence: 高
```

---

## SD-282（公开经验库·公开）

```yaml
success_id: SD-282
problem_type: 空间几何/变形监测
method: 最小二乘确定各层中心 + 空间曲线/坐标变换刻画倾斜·弯曲·扭曲 + 灰色预测趋势
why_success: 论文用最小二乘拟合观测点所在平面、取距各点平方和最小点为层中心(通用方法); 用空间直线最小二乘拟合成中心线, 定义倾斜角=塔尖与底层中心水平距/塔高、弯曲率K=空间曲线曲率、相对扭曲度=坐标旋转角度; 因数据仅4期, 用灰色预测分析三变形量趋势。
result: 根据4期观测数据计算古塔的变形(倾斜/弯曲/扭曲), 建立变形趋势预测模型
limitations: 仅4期观测, 预测样本少；刚性假设可能不满足；未考虑地基沉降因素
source: 古塔的变形(2013高教社杯优秀论文选登, 成都工业学院)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700221.shtml|2013
confidence: 高
```

---

## SD-283（公开经验库·公开）

```yaml
success_id: SD-283
problem_type: 天文几何/反问题
method: 太阳高度角几何模型 + 非线性最小二乘(贪婪算法遍历)反演经纬度/日期
why_success: 论文以杆长、赤纬角、时角、纬度建立影长模型; 问题二用非线性最小二乘对纬度/经度/杆长最优估计, 并用贪婪算法遍历使拟合前后偏移角度相等, 得海南东方市(19.2486°N,108.5571°E); 问题三增日期变量得附件2新疆(39.8951°N,79.7488°E)、附件3湖北十堰(32.8487°N,110.2449°E); 国家一等奖用误差传递得影长相对误差限0.23%。
result: 根据直杆的太阳影子变化数据, 反推影子的拍摄地点和日期
limitations: 多解问题(不同地点/日期可产生相近影子), 需分类筛选；需足够多影子数据点；大气折射未考虑或仅近似修正
source: 基于非线性最小二乘法的太阳影子定位研究(2015国赛A题全国优秀论文)|https://max.book118.com/html/2017/0924/134885798.shtml|2015
confidence: 高
```

---

## SD-284（公开经验库·公开）

```yaml
success_id: SD-284
problem_type: 搜索优化/概率建模
method: 二次距离-伤亡PDF(定位置信) + POC/POD(Koopman) + 邻域POC更新算法
why_success: 论文用二次PDF预测坠机点距最后联系点的距离, 以 POC 量化各单元包含概率, 用 Koopman 方程算 POD, 再以邻域更新算法在'未找到'时把概率重分配给相邻单元, 实现资源受限下的持续高效搜索
result: 建立通用搜索模型, 协助规划失联跨洋飞机在公海的搜救方案(假设无信号)
limitations: IFP 线性假设在真实转弯航线中不成立；依赖 Hartmann 的 200 英里雷达半径经验值；POD 受搜索机载仪器精度影响, 敏感性高；仅撞击水面才解体的假设忽略了空中解体情形
source: Searching for a Lost Plane: A Probabilistic, Neighborhood-Based Model for Locating Transoceanic Flights (2015 MCM B Outstanding, Colorado College, Team 39173)|https://max.book118.com/html/2026/0704/7062043054011130.shtm|2015
confidence: 高
```

---

## SD-285（公开经验库·公开）

```yaml
success_id: SD-285
problem_type: 网络科学/信息传播
method: 多层网络拓扑 + 中心性影响力度量 + 动态传播 + 价值衰减度量
why_success: 赛题要求在网络结构上同时度量'传播演化'与'影响/价值', 需网络结构(承载传播)、影响力指标(量化节点)、动态传播(演化)、价值衰减(信息价值)四部分组合
result: 建立度量指标量化信息在社会信息网络的演化与影响, 衡量信息的价值与传播
limitations: 真实社交网络数据稀疏, 拓扑不完整会影响度量(推断)；影响力与价值的定义本身带主观性, 指标需可解释(推断)
source: Measuring the Evolution and Influence in Society's Information Networks (2016 ICM Problem D)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## SD-286（公开经验库·公开）

```yaml
success_id: SD-286
problem_type: 环境预测/资源管理
method: 集总式水量平衡 + 系统动力学存流量 + 干旱指数评估
why_success: 赛题要求评估可用性并预测趋势, 水量平衡给出供需缺口, 系统动力学刻画存流量演化, 干旱指数提供标准化风险度量
result: 评估区域水资源可用性, 预测干旱/缺水趋势, 提出水资源管理策略
limitations: 历史降水序列长度限制外推可靠性(推断)；跨部门用水分配参数具主观性(推断)
source: Are we headed for a thirsty planet? (2016 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## SD-287（公开经验库·公开）

```yaml
success_id: SD-287
problem_type: 水资源优化/系统管理
method: 系统动力学存流量 + 多目标优化(发电/灌溉/生态权衡)
why_success: 赛题要求兼顾多目标管理, 系统动力学刻画水量演化, 多目标优化在约束下给出权衡前沿
result: 为赞比西河水系制定管理方案, 权衡水力发电、灌溉与生态流量等多目标
limitations: 跨流域国家协调参数难量化(推断)；极端干旱/洪水情景依赖外推(推断)
source: Managing the Zambezi River System (2017 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## SD-288（公开经验库·公开）

```yaml
success_id: SD-288
problem_type: 数据分析/预测
method: 时间序列/回归预测 + 系统动力学耦合 + 政策情景分析
why_success: 赛题是数据驱动(提供真实数据集), 需先由数据建模趋势, 再用系统动力学耦合经济/排放, 最后用情景评估政策
result: 基于多国多年能源数据集, 分析能源生产模式、预测趋势并评估政策影响
limitations: 数据覆盖国家/年份不全, 外推受限(推断)；政策参数具主观设定(推断)
source: Energy Production (2018 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## SD-289（公开经验库·公开）

```yaml
success_id: SD-289
problem_type: 生态建模/生物物理
method: 异速生长代谢 + 能量收支 + 领地面积 + 气候修正
why_success: 赛题要求量化质量→能耗→摄入→面积→社区的全链路, 异速生长律把质量(赛题给定10kg→30-40kg)映射到代谢, 再推导摄食与领地
result: 为《权游》中三条虚构巨龙建立生态模型: 量化生态影响、能量消耗、热量摄入、支撑面积与社区规模, 并分析气候(干旱/温带/北极)影响
limitations: 龙为虚构, 代谢参数需类比现生大型动物并显式声明(赛题要求)；气候修正依赖食物可得性假设(推断)
source: Game of Ecology (2019 MCM Problem A) — 赛题官方全文(含真实数字 10kg/30-40kg)|https://blog.csdn.net/xindolia_ring/article/details/86768820|2019
confidence: 中
```

---

## SD-290（公开经验库·公开）

```yaml
success_id: SD-290
problem_type: 数据分析/流行病学
method: 时空传播 + 机器学习风险分层 + 干预因果评估
why_success: 赛题是数据驱动且要求评估干预, 需传播模型刻画扩散、机器学习做风险分层、因果法评估政策
result: 基于多源真实数据集, 建模阿片滥用传播、预测过量死亡并评估干预策略
limitations: 数据口径跨州不一致(推断)；因果识别受观测数据限制(推断)
source: The Opioid Crisis (2019 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## SD-291（公开经验库·公开）

```yaml
success_id: SD-291
problem_type: 生态建模/气候变化
method: 温度适宜性指数 + 栖息地纬度迁移 + 种群动态耦合
why_success: 赛题要求刻画'北迁', 适宜性指数把温度等映射到栖息地, 再驱动纬度中心迁移与种群响应
result: 建模海洋物种栖息地随海水变暖向北迁移, 评估对生态系统与依赖产业的影响
limitations: 多因子交互难完全量化(推断)；食物网级联效应难建模(推断)
source: Moving North (2020 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## SD-292（公开经验库·公开）

```yaml
success_id: SD-292
problem_type: 数据分析/文本挖掘
method: NLP 情感/主题 + 梯度提升评分预测 + 协同过滤推荐
why_success: 赛题要评分预测与推荐, 文本建模提取观点, 监督模型预测评分, 协同过滤给推荐
result: 分析产品评论数据, 建立评分预测与产品推荐策略
limitations: 评分不平衡影响阈值(推断)；文本噪声与讽刺难处理(推断)
source: A Data Analysis of Online Shopping (2020 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## SD-293（公开经验库·公开）

```yaml
success_id: SD-293
problem_type: 环境建模/物质流
method: 物质流 + 系统动力学存流量 + 减塑情景
why_success: 赛题要累积与策略评估, 物质流保证质量守恒, 系统动力学刻画演化, 情景评估政策
result: 建模塑料废弃物在环境中的累积, 预测污染水平并评估减塑/回收策略
limitations: 降解速率数据不确定(推断)；各国回收统计口径不一(推断)
source: The Plastic (2020 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## SD-294（公开经验库·公开）

```yaml
success_id: SD-294
problem_type: 社会预测/气候适应
method: 暴露-脆弱性-适应性 + 重力模型迁移流
why_success: 赛题要评估气候暴露如何转化为迁移, 需暴露度量化与迁移流建模结合
result: 建模气候变化驱动的人口迁移, 评估海平面上升与极端天气对迁移的影响
limitations: 迁移决策受非气候因素干扰(推断)；接收地数据不全(推断)
source: The Place I Called Home (2020 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## SD-295（公开经验库·公开）

```yaml
success_id: SD-295
problem_type: 风险评估/轨道动力学
method: 碰撞级联演化 + 碰撞概率 + 清理成本效益优化
why_success: 赛题要增长/风险/清理三位一体, 级联模型给演化, 概率给风险, 优化给方案
result: 建模太空碎片增长与碰撞风险, 评估商业清理方案的可行性
limitations: 级联阈值敏感(推断)；商业清理技术参数不确定(推断)
source: Space Junk (2016 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## SD-296（公开经验库·公开）

```yaml
success_id: SD-296
problem_type: 文化演化/预测
method: 语言竞争/转移模型 + 系统动力学存量演化
why_success: 赛题要预测多样性变化, 需使用者如何在语言间转移的机制模型
result: 建模语言使用者转移与消亡, 预测未来语言多样性变化
limitations: 转移参数难估计(推断)；政策/冲突等突发因素难建模(推断)
source: How Many Languages? (2018 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## SD-297（公开经验库·公开）

```yaml
success_id: SD-297
problem_type: 环境经济/生态核算
method: 当量法价值化 + 成本-效益分析 + 敏感性
why_success: 赛题要量化环境成本, 当量法把服务转货币, 成本-效益做决策, 敏感性保稳健
result: 量化生态系统服务价值, 评估土地利用/开发项目的环境成本
limitations: 价值系数具区域主观性(推断)；非市场价值难完全货币化(推断)
source: What is the Cost of Environmental Degradation? (2019 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## SD-298（公开经验库·公开）

```yaml
success_id: SD-298
problem_type: 空间分析/预测
method: 重心法 + 缓冲带/距离衰减画像, 多方案加权组合
why_success: 赛题要求≥2 种方案; 重心法直观(赛题历史案例即用此法), 距离衰减画像刻画'熟悉区+避开家附近'的规律, 二者组合更稳
result: 为地方警署开发连环犯罪地理画像方法: 用≥2 种方案生成画像并组合, 预测下一次犯罪地点, 给出可靠性与警告
limitations: 犯罪样本少时画像不稳定(推断)；缓冲带半径需标定(推断)
source: Criminology (2010 MCM Problem B) — COMAP 官方赛题|https://comap.com/membership/member-resources/item/criminology|2010
confidence: 中
```

---

## SD-299（公开经验库·公开）

```yaml
success_id: SD-299
problem_type: 城市评估/可持续发展
method: 多指标评价(熵权+TOPSIS) + 系统动力学情景
why_success: 赛题要评估并提方案, 多指标评价给可持续性排序, 系统动力学给提升路径
result: 建立城市可持续性评价指标体系, 评估城市发展并制定提升方案
limitations: 权重主观(推断)；数据跨城口径不一(推断)
source: Sustainable Cities Needed! (2017 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## SD-300（公开经验库·公开）

```yaml
success_id: SD-300
problem_type: 经济建模/货币
method: Bass 采用扩散 + 系统动力学货币-价格耦合
why_success: 赛题要评估采用与稳定, Bass 刻画采用扩散, 系统动力学耦合货币供应与价格
result: 评估'通用、去中心化、流通货币'的可行性, 建模采用扩散与价值稳定性
limitations: 采用参数难标定(推断)；治理/安全难量化(推断)
source: Universal, Decentralized, Circulating Currency (2019 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## SD-301（公开经验库·公开）

```yaml
success_id: SD-301
problem_type: 优化决策
method: 非线性规划求解汇合点P与车站E + AHP综合拆迁附加费
why_success: 以总费用 z=7.2*L_郊 + (7.2+e)*L_城 为目标, 用LINGO/fminunc求解P与E坐标使费用最小; 拆迁费e由三家估算(21/24/20)经AHP综合为21.4万元/km
result: 在铁路线一侧建造两炼油厂并增建车站, 在城区/郊区分段计价与拆迁附加费约束下, 确定共用管线汇合点与车站位置, 使管线铺设总费用最小
limitations: 未考虑地形起伏与河流阻隔；单价为分段常数简化, 实际随管径变化；实际管网存在分支与压力约束
source: 输油管的布置-2010大学生年数学建模大赛优秀论文|https://max.book118.com/html/2020/0906/7125151136002165.shtm|2010
confidence: 高
```

---

## SD-302（公开经验库·公开）

```yaml
success_id: SD-302
problem_type: 优化决策
method: 倒序贪心分组 + 各规格整数线性规划 + 余料降级再规划
why_success: 直接整体整数规划因规格三变量过多而求解过慢(超30分钟), 改为按规格分组局部最优再降级汇总, 既快又接近全局最优
result: 在成品规格、误差容限与降级规则约束下, 将一批天然肠衣原料搭配装出尽可能多的合格成品捆, 并在30分钟内产出方案
limitations: 局部最优相加未必是严格全局最优；分档离散化略损失精度；未考虑肠衣质量/直径的附加约束
source: 数学建模天然肠衣国家二等奖论文|https://wk.baidu.com/view/28ffbe51c850ad02de80417c?pcf=2|2004
confidence: 高
```

---

## SD-303（公开经验库·公开）

```yaml
success_id: SD-303
problem_type: 优化决策
method: 优化比例系数K筛选电池 + 整数规划铺设 + 倾角枚举求最佳倾角 + 贪心配逆变器
why_success: 以单位面积功率/价格定义K筛选高性价比电池, 再用整数规划在面积约束下最大化发电量, 倾角以0.01°间隔枚举辐射积分极值
result: 在大同地区气象与光伏电池参数下, 优化电池板选型、外表面铺设与房屋朝向倾角, 使发电量最大且投资回收期最短
limitations: 辐射数据为离散值, 积分近似；未计遮挡与季节积雪；房屋造型受施工成本限制
source: 2012年全国大学生数学建模获奖范文(太阳能小屋的设计, 省一等奖)|https://max.book118.com/html/2015/0608/18664649.shtm|2012
confidence: 高
```

---

## SD-304（公开经验库·公开）

```yaml
success_id: SD-304
problem_type: 优化决策
method: 外扩10得危险包络 + 可视图Dijkstra定必经危险点 + 切线圆结构求最短路径
why_success: 最短路径必由直线段与障碍包络的相切圆弧组成, 先Dijkstra找拓扑最短路, 再在包络上取最小半径圆弧得几何最短
result: 在800×800平面、12个障碍物场景下, 机器人由O(0,0)出发, 以直线段+相切圆弧(最小转弯半径10)绕过障碍, 求到目标点的最短路径与最短时间路径
limitations: 外扩10为固定安全裕度, 未随速度调整；最短时间模型假设速度分段常数；未考虑动态障碍
source: 2012全国大学生数学建模机器人避障问题优秀论文模型|https://wk.baidu.com/view/9635073577a20029bd64783e0912a21615797fca|2012
confidence: 高
```

---

## SD-305（公开经验库·公开）

```yaml
success_id: SD-305
problem_type: 数据分析/优化决策
method: 数据清洗+频数统计定位热点站 + 车锁比分级调度 + 多目标调度模型
why_success: 先用频数统计识别高频借还站点, 再用α=车锁比划分一/二/三级调度窗口, 最后以满意度与成本双目标生成调度路线
result: 基于20天借还车数据, 分析站点使用频次与借车卡分布, 对站点聚类分级, 给出公共自行车系统的调度方案与建设评价指标
limitations: 20天数据未覆盖季节波动；未建模天气对骑行量的影响；调度成本参数依赖经验
source: 公共自行车服务系统—大学生数学建模竞赛论文|https://m.book118.com/html/2015/1217/31548128.shtm|2015
confidence: 高
```

---

## SD-306（公开经验库·公开）

```yaml
success_id: SD-306
problem_type: 优化决策
method: 盈亏平衡点定产仔底线 + 饱和规模下整数规划求母猪存栏与选种比 + 价格周期分解定出栏节奏
why_success: 问题一用盈亏平衡点反推每头母猪年产仔≥18头; 问题二在10000头上限下以利润最大求母猪525头、选种比1:30; 问题三按价格曲线分周期调配肉猪/猪苗比例
result: 在猪场最多养10000头的容量与生猪价格周期下, 确定母猪存栏数、小猪选种比例与出栏节奏, 使三年平均年利润最大化
limitations: 价格预测为给定曲线, 未做不确定性分析；未计疫情与饲料价波动；产仔量取均值忽略个体方差
source: 数学建模比赛C题省二等奖论文(生猪养殖场的经营管理)|https://m.renrendoc.com/paper/207871332.html|2014
confidence: 高
```

---

## SD-307（公开经验库·公开）

```yaml
success_id: SD-307
problem_type: 优化决策
method: 逐步推导定最少竖向类型 + 逐步分裂迭代增类型降冗余 + 多目标规划定横向类型
why_success: 先用W≤2Dmin-1与W≥Dmax+4递推得最少5种竖向(19/31/39/50/60mm); 再以逐步分裂迭代增加类型使总宽度冗余大幅下降; 平面冗余=宽×高冗余, 用多目标规划定横向13种
result: 在药盒推送不并排重叠、不侧翻、不水平旋转的约束下, 设计储药槽竖向/横向隔板间距类型最少且总冗余尽可能小的储药柜方案
limitations: 未考虑药盒推送摩擦差异；需求按最大值配置, 平均利用率偏低；侧翻/旋转约束以对角线近似
source: 大学生数学建模(储药柜的设计, 国赛论文)|https://m.renrendoc.com/paper/210440230.html|2016
confidence: 高
```

---

## SD-308（公开经验库·公开）

```yaml
success_id: SD-308
problem_type: 调度优化
method: 0-1变量刻画目标 + 三种调度原则(就近/FIFO/HRRN)仿真求局部最优
why_success: 加工数最多是NP问题无法精确解, 改用多原则仿真: 就近原则构造时间代价函数, FIFO看等待时间, HRRN综合二者, 在8小时内模拟得最大成料数
result: 由8台CNC与1辆RGV组成的智能加工系统中, 给定作业参数, 给出RGV动态调度模型与算法, 使8小时内加工物料数最多、系统作业效率最高
limitations: 仿真为局部最优非全局最优；故障情形需额外随机模拟；参数恒定假设忽略波动
source: 2018年全国大学生数学建模竞赛论文展示(B217): 基于多原则比较和蒙特卡洛模拟的RGV动态调度模型|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018btlw/240206/1699832.shtml|2018
confidence: 高
```

---

## SD-309（公开经验库·公开）

```yaml
success_id: SD-309
problem_type: 排序优化
method: 颜色衔接构有向图 + 遗传算法TSP/广度优先搜索求最小代价路径
why_success: 把'符合颜色衔接要求的车'作顶点连边构成有向图, 装配顺序即图的遍历路径, 用遗传算法求切换代价最小的哈密顿路径, 黑色车先手工定位缩小搜索
result: 在满足品牌、配置、动力、驱动、颜色等装配要求下, 给出一天车辆的总装线装配顺序, 使配置/颜色切换次数最少、生产成本最低
limitations: 未计设备故障与换线时间波动；喷涂线均衡仅作约束；代价权重依赖经验设定
source: 2018年全国大学生数学建模竞赛论文展示(D027): 汽车总装线配置的优化模型研究|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018dtlw/240206/1699827.shtml|2018
confidence: 高
```

---

## SD-310（公开经验库·公开）

```yaml
success_id: SD-310
problem_type: 决策优化/排队论
method: 效用模型比较两方案收益 + 排队论求蓄车池逗留时间 + AHP定到港比例α
why_success: 以相同时间内载客里程更长者为优: 用M/M/1算蓄车池平均逗留1/(µ-λ), 用AHP把季节/时段/星期/天气/社会五因素合成α, 效用函数调节排队意愿
result: 出租车司机送客到机场后, 在'蓄车池排队等待载客'与'空车返回市区'间决策, 并设计上车点与短途优先规则, 使司机收益与乘客效率均衡
limitations: M/M/1假设与实际高峰聚集有偏差；α权重依赖历史数据；未计网约车竞争
source: 2019数学建模竞赛B题优秀论文-基于'互联网+'机场的出租车问题|https://blog.csdn.net/weixin_43796658/article/details/103402800|2019
confidence: 高
```

---

## SD-311（公开经验库·公开）

```yaml
success_id: SD-311
problem_type: 决策优化/资源规划
method: 确定天气用动态规划+多重搜索初始补给; 不确定天气用期望; 多玩家用博弈论
why_success: 天气已知时建状态转移方程与阶段损益, 动态规划求全局最优; 天气未知时引入概率与期望量化; n名玩家用非合作对策求纳什均衡
result: 在沙漠游戏中, 玩家在天气(晴朗/高温/沙暴)与地图(起点、村庄、矿山、终点)约束下, 决策每日行走/停留/挖矿与物资购买, 使规定时间内到达终点且剩余资金最多
limitations: 期望假设天气独立同分布；未计玩家间实时博弈的信息不对称；负重与资金边界依赖题给常数
source: 2020年数学建模B题国二论文: 穿越沙漠的最佳策略|https://max.book118.com/html/2023/0911/6205213114005225.shtm|2020
confidence: 高
```

---

## SD-312（公开经验库·公开）

```yaml
success_id: SD-312
problem_type: 优化决策
method: 最小二乘回归潮流 + 按段价由低到高选容量的经济调度 + 线路超限排序调整
why_success: 先用回归得各线路潮流表达式, 再按'段价低优先'原则在爬坡与段容量约束下填满负荷得最小费用预案, 最后检查线路限值, 对超限线路用排序算法调整消除阻塞
result: 在机组段容量、爬坡速率与线路有功潮流限值约束下, 制定发电出力分配预案使购电费用最小, 并对出现输电阻塞的预案进行调整消除阻塞
limitations: 潮流线性近似有回归误差；未计网损与无功；阻塞调整以安全优先可能抬高费用
source: 电力市场的输电阻塞管理(2004全国大学生数学建模竞赛全国二等奖论文)|https://m.diyifanwen.net/wenku/1417729.html|2004
confidence: 高
```

---

## SD-313（公开经验库·公开）

```yaml
success_id: SD-313
problem_type: 评价分类
method: AHP(目标-准则-指标三层)赋权 + 模糊综合评价
why_success: 赛题指标兼具定量(造价/面积)与定性模糊(舒适/安全)两类, AHP用1-9标度系统量化三层指标重要性得到客观权重, 模糊综合评价用隶属度处理定性指标; 二者结合计算组合权重×优属度矩阵得综合评价值 Q=[0.2630,0.6240,0.4337,0.7432], 方案4最优, 优于单用TOPSIS或等权法
result: 从经济性、舒适性、安全性三方面对附件四种学生宿舍设计方案做综合量化评价与排序, 选出最优方案
limitations: AHP判断矩阵仍依赖专家两两比较打分, 存在主观性; 可用熵权法组合赋权削弱；文献假设各方案防盗系数相同, 可能低估方案间安全差异(属推断简化)
source: 2010数模D题 宿舍方案优化设计(基于AHP的学生宿舍设计方案评价)|https://m.renrendoc.com/paper/231326836.html|2010
confidence: 高
```

---

## SD-314（公开经验库·公开）

```yaml
success_id: SD-314
problem_type: 评价分类
method: 可信度检验 + PCA降维 + 聚类/优势因子矩阵分级 + 逐步回归关联
why_success: 感官评分含主观差异须先检验可信度(官方A335论文用双向显著性检验+置信区间法, 结论: 红葡萄酒采信第一组、白葡萄酒采信第二组); 理化指标高度相关须PCA提取少数主成分消除共线性; 分级用均值聚类+优势因子矩阵加权求和数据驱动定级; 关联用逐步回归/典型相关分离主次
result: 基于理化指标与感官评分评价葡萄酒质量并对酿酒葡萄分级, 探究理化指标与质量的关联
limitations: 感官评分仍含主观成分, 仅经检验未完全消除；样本27有限, 分级与回归的外推性受限；白葡萄因指标区分度低, 等级划分不如红葡萄清晰(官方论文明确指出)
source: 葡萄酒的质量分析与评价(A335, 2012高教社杯全国大学生数学建模竞赛优秀候选论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2012qgdxssxjmjslwzs/121030/1191829.shtml|2012
confidence: 高
```

---

## SD-315（公开经验库·公开）

```yaml
success_id: SD-315
problem_type: 评价分类
method: Excel基线核算 + 整数线性规划(平均满意度最大) + 双目标分层序列法(满意度/ROI≥25%)
why_success: 先用Excel核算原方案摸清成本/收益/容积率/增值税与免税临界点; 再以平均满意度最大建整数规划满足参筹意愿(Lingo求得最大平均满意度0.7069); 最后叠加ROI≥25%双目标用分层序列法逐步优化, 并在增值率20%临界点微调售价增收益
result: 在住户满意度与开发商投资回报率平衡下, 核算并优化众筹筑屋的房型配比规划方案
limitations: 参筹者购买意愿为抽样调查, 样本有限；房价/成本为给定参数估算, 未考虑市场动态变化；整数规划求解规模受房型数(11种)限制
source: 1D11001-D001 众筹筑屋规划方案设计(2015高教社杯全国大学生数学建模竞赛国家一等奖论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2015qgdxssxjmjslwzs/210621/1700975.shtml|2015
confidence: 高
```

---

## SD-316（公开经验库·公开）

```yaml
success_id: SD-316
problem_type: 评价分类
method: AHP评价体系 + 宏观交通流微分方程 + 二维元胞自动机仿真
why_success: 赛题真实数据难获, AHP对数据要求低且能把'人的感受'纳入评价体系得8指标权向量ω=[0.189,0.098,0.166,0.189,0.169,0.084,0.046,0.056](通过一致性检验); 宏观微分方程刻画内/外车流交互, 元胞自动机仿真开放前后实时车流以算前后延时差
result: 建立评价体系并仿真, 定量评估小区开放对周边道路通行能力的影响, 分条件给出开放策略
limitations: 驾驶行为假设同质, 未充分刻画异质驾驶员；未考虑行人/非机动车；仿真参数(到达率等)需标定, 真实数据有限
source: 小区开放对道路通行能力的影响(2016年高教社杯全国大学生数学建模竞赛一等奖, 南京大学)|https://simlab.nju.edu.cn/0f/8d/c30091a462733/page.htm|2016
confidence: 高
```

---

## SD-317（公开经验库·公开）

```yaml
success_id: SD-317
problem_type: 评价分类
method: 四因素指标体系 + AHP/熵权组合赋权 + TOPSIS排序 + 0-1规划优化
why_success: 四因素(时间间隔方差/背靠背/连强手/连客场)覆盖休息均匀与疲劳; AHP+熵权组合赋权兼顾经验与数据客观差异; TOPSIS对30队艰难程度直观排序; 0-1规划在行列平衡约束下优化'赛3场'安排(商业价值提升54.95%)
result: 把2008-2009赛季NBA赛程数字化, 建立指标评价赛程对各队利弊与公平性, 并优化'赛3场'安排
limitations: 疲劳模型简化, 未计入时差/气候/温度等；对手强度用上赛季排名近似, 非实时；飞行距离需由城市坐标推算, 赛题未直接给
source: nba赛程的分析与评价数学建模论文(2008高教社杯D题获奖论文)|https://www.wenkub.com/doc/357211.html|2008
confidence: 高
```

---

## SD-318（公开经验库·公开）

```yaml
success_id: SD-318
problem_type: 评价分类
method: 插值对齐 + 三项误差指标(均值E/方差D/平方和根) + 公众满意度 + 多检验一致性
why_success: 预报在网格、实测在站点, 须先用最邻近点或改进反距离加权(δ=0.3)插值到91站; 用误差均值E、方差D、误差平方和根多指标兼顾精度与稳定性; 再用7级雨量满意度函数贴合公众感受; 最后用方差分析+r/Q相关性检验交叉验证。结果: 最近邻法方法一误差平方和根449.44<方法二474.22且方差更小, 整体满意度Sa1=0.9692>Sa2=0.9689, 两种方法均可接受、方法一略优
result: 建立指标比较两种6小时雨量预报方法的准确性与公众满意度, 选出更优方法
limitations: 实测站点仅91个, 插值存在空间代表误差；两方法同网格, 分辨率差异问题不突出但真实业务常有；未充分区分不同雨量等级误报对公众的差异(原论文编者按指出第二问稍薄)
source: 雨量预报方法的评价模型(伍利兵等, 工程数学学报2005; 2005高教社杯全国大学生数学建模竞赛全国一等奖)|https://blog.sciencenet.cn/upload/blog/file/2008/11/20081112222131814898.pdf|2005
confidence: 高
```

---

## SD-319（公开经验库·公开）

```yaml
success_id: SD-319
problem_type: 评价分类
method: AHP综合权重 + 志愿双向选择 + 0-1整数规划最优分配
why_success: AHP把笔试(按r)与面试及岗位要求融合成综合权重qij; 申报矩阵S(志愿)转为双向选择权重; 以总权重和最大建0-1整数规划在'一人一岗/类容量/未报类xij=0'约束下求最优分配。结果: 12人/7部门/4类的最优分配为人员5→类1(部门1)、1/2/4→类2(部门2,3)、6/9→类3(部门4,5)、11/12→类4(部门6,7)
result: 在岗位要求与应聘者条件双向匹配下, 建立评价与分配模型完成人岗录用
limitations: 笔试面试主观打分偏差；志愿冲突难以全部满足(未报类别不可分配)；权重中r比例系数依赖部门主观重视度
source: 公务员招聘(2004年高教社杯获得者论文: 层次分析法+0-1整数规划)|https://wenku.baidu.com/view/18f658bf68ec0975f46527d3240c844769eaa08e.html|2004
confidence: 高
```

---

## SD-320（公开经验库·公开）

```yaml
success_id: SD-320
problem_type: 评价分类
method: 碰撞动力学(含转动惯量) + 梁振动模态(节点定位) + 多目标甜区评价
why_success: 纯扭矩刚体会误判棒末端为甜区; 须用含转动惯量的碰撞模型解释出球随击球点变化, 再用柔性梁求自然振动模态(一级≈215Hz、二级≈670Hz、三级≈1252Hz)定位节点集中区(距顶端15.7%-20.2%), 甜区=出球速度最高且对手振动力最小的点
result: 建立棒球棒击球动力学与振动模型, 解释并定位最佳击球点(甜区), 比较木/铝与corking的影响
limitations: 球棒模型简化为均匀/分段均匀梁, 真实剖面渐变有误差；未充分建模握持手部阻尼；材料非线性(木纤维/铝屈服)被忽略
source: 2010 MCM Problem A 棒球甜区建模论文(自然振动模态与节点分析)|https://www.doc88.com/p-4334721419338.html|2010
confidence: 高
```

---

## SD-321（公开经验库·公开）

```yaml
success_id: SD-321
problem_type: 评价分类
method: 有效胜率标准化 + 难度/时代校正 + AHP/PCA综合指数排名
why_success: 不同项目赛季长度差倍, 须先把胜场按赛季长度转为有效胜率统一量纲; 再用项目难度(赛季长度/竞争强度)与时代(ERA)校正跨项目不可比; 最后用AHP/PCA或z-score建综合成就指数跨项目排名。注: 具体教练得分数字未在可访问来源中读取, 本案例方法为基于赛题说明的合理推断
result: 建立大学教练综合评价模型, 跨项目(篮/棒/足/冰球等男女)与跨时代比较, 排出历史最佳教练
limitations: 项目难度校正依赖主观设定的校正因子；时代(ERA)校正难以完全量化；权重主观, 须敏感性分析
source: 2011 MCM Problem A: College Coaching Legends (COMAP官方成绩页, 杰出奖含北大/清华)|https://www.contest.comap.com/undergraduate/contests/mcm/contests/2011/results|2011
confidence: 中
```

---

## SD-323（公开经验库·公开）

```yaml
success_id: SD-323
problem_type: 评价分类
method: 模糊综合评价(部门契合) + 多层复杂网络动态(Lyapunov/Pajek) + 多流失率情景 + 敏感性优化
why_success: 模糊综合评价求部门间欧氏距离量化岗位-战略契合; 建技能/信任/影响/友谊多层复杂网络, 用Lyapunov稳定性+Pajek可视化模拟人员流动与职位完整性; 多流失率情景(18%/25%/35%)定预算(18%时两年预算≈34.22σ); 对7个人力资本价值因素敏感性分析显示各层级员工数量影响最大
result: 建立组织人力资本评价与动态模型, 比较人力战略、评估流失风险并给出配置建议
limitations: 技能量化依赖主观打分；战略指标主观；历史流失/招聘数据不完整
source: Strategic Human Resource Management and Corporate Performance (ICM 2015 MCM C 人力资本论文, scirp)|https://scirp.org/journal/paperabs.aspx?paperid=90134|2015
confidence: 高
```

---

## SD-324（公开经验库·公开）

```yaml
success_id: SD-324
problem_type: 物理建模
method: 分段截面积分(机理) + 系统误差修正项 + 最小二乘/等间距穷举反演变位参数 + 三次多项式残差修正
why_success: 积分可精确求得任意液位下的容积, 实测数据含系统误差需加修正项(实测≈0.9663×理论); 最小二乘或等间距穷举由实测数据反演变位参数标定罐容表。西电国家二等奖论文用最小二乘拟合变位参数得 4.078°, 与题设 4.1° 误差仅 0.5%, 两次修正后计算值与实测值误差不超过 0.04%
result: 根据油位探针读数与罐体变位参数, 建立容积-液位模型并标定罐容表; 由实测进出油数据反演实际罐体纵向倾斜与横向偏转角度
limitations: 小角度刚体变位假设(题设实验 4.1°, 大角度需重新分区)；实际罐两端球冠体积表达式复杂, 近似省略一小部分(需蒙特卡洛补算验证)；探针/制造误差未建模, 系统误差以比例修正项近似
source: 储油罐的变位识别与罐容表标定(2010高教社杯全国大学生数学建模竞赛A题一等奖, 重庆大学 王建等)|https://www.docin.com/p-476164223.html|2010
confidence: 高
```

---

## SD-325（公开经验库·公开）

```yaml
success_id: SD-325
problem_type: 物理建模
method: 二体/开普勒建模 + 6阶段分段最优控制(主减速用Pontryagin/遗传算法燃料最优) + K均值聚类避障 + 三次样条轨迹拼接
why_success: 开普勒第二定律可精确求近/远月点速度(1692.46/1612.15m/s); 将全局最优拆为6阶段子问题可解; 主减速段燃料最优使末速精确达57m/s且燃耗约1055.39kg(东南大学); 避障用K均值聚类+栅格化从高程图稳健选安全落点(最优坐标(1275,1000))
result: 设计嫦娥三号月面软着陆轨道与控制策略: 确定着陆准备轨道近/远月点参数, 规划6阶段最优下降轨迹, 使落点安全、燃料最优、触月速度近零
limitations: 采用二体引力, 忽略地球/太阳摄动细节(敏感度分析表明地球引力影响可忽略)；避障基于高程图栅格化, 对未标注微障碍不敏感；主减速段假设推力最大且方向恒定, 与真实脉动调姿有简化
source: 嫦娥三号软着陆轨道设计与控制策略(2014高教社杯全国大学生数学建模竞赛优秀论文选登, 东南大学 吉张鹤轩等)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2014qgdxssxjmjslwzs/211022/1700790.shtml|2014
confidence: 高
```

---

## SD-326（公开经验库·公开）

```yaml
success_id: SD-326
problem_type: 物理建模
method: 空间几何不变量建模(开槽长度) + 桌脚边缘线柱面相交+三次多项式拟合 + 多目标非线性规划
why_success: 开槽长度由平铺与折叠两态钢筋到铰链距离差(几何不变量)精确求得, 单侧序列20.093→0cm; 桌脚端点投影两坐标面拟合、两柱面交线得边缘线; 多目标规划在桌高53cm、19根木条约束下协同优化开槽最短/黄金梯形稳固/用材最少
result: 建立平板折叠桌的动态变化与加工参数模型: 给定平板尺寸求各木条开槽长度与桌脚边缘线, 并优化设计使桌子稳固、加工方便、用材最少
limitations: 忽略木板弹性变形与铰链间隙；未建模动态展开过程的冲击/摩擦；加工误差(锯缝厚度)以取整木条数近似
source: 创意平板折叠桌(2014高教社杯全国大学生数学建模竞赛三等奖论文, 开槽长度序列与几何模型)|https://m.renrendoc.com/p-23651209.html|2014
confidence: 高
```

---

## SD-327（公开经验库·公开）

```yaml
success_id: SD-327
problem_type: 物理建模
method: 球面三角天文模型 + 太阳赤纬解析公式 + 赤道→地平坐标变换求日落/月出时刻
why_success: 赤纬公式 δ=0.3723+23.2567Sinθ+... 给出太阳赤纬随累计天数N的解析变化; 坐标变换将日月光行转为地平高度, 反解时角得地方时; 国一论文据此算出日落Tsun(α,β,γ)与月出Tmoon(α,β,γ), 并判定2016年乌鲁木齐不能发生该情景
result: 把诗句'月上柳梢头,人约黄昏后'量化为天文阈值, 建立日落/月出时刻关于经纬度与日期的模型, 判定2015北京及2016各城市发生该情景的日期与时间
limitations: 基础模型忽略大气折射与视差(改进模型才加修正)；地形遮挡未考虑(假设水平开阔)；月赤纬依赖历表精度
source: 月上柳梢头(2015高教社杯全国大学生数学建模竞赛C题, 含国一优秀论文 PDF)|https://yuque.com/mcm/cumcm/om8nox|2015
confidence: 高
```

---

## SD-328（公开经验库·公开）

```yaml
success_id: SD-328
problem_type: 物理建模
method: 分单元静力+力矩平衡建模 + 悬链线/集中质量法描述锚链 + 以吃水或重物球质量为变量的二分/迭代搜索
why_success: 逐单元受力与力矩平衡可得各部件倾角与位形; 悬链线刻画锚链形态; 以吃水(或重物球质量)为单变量二分搜索逼近水深18m, 使钢桶夹角<5°、锚链夹角<16°。论文1用此法得12m/s吃水0.6715m(游动14.6552m)、36m/s加重物2280kg时钢桶4.4737°、锚链15.9748°
result: 设计近海单点系泊系统(浮标+4节钢管+钢桶+重物球+电焊锚链), 使浮标在各种海况下稳定、吃水合理且不触底/不拉直
limitations: 静力忽略动力/惯性(未校核瞬态冲击)；海床平坦假设；风浪流耦合以合成载荷近似
source: 2016年数学建模竞赛A题优秀论文(系泊系统的设计, 基于力学分析)|https://www.bodocs.net/doc/4920463175.html|2016
confidence: 高
```

---

## SD-329（公开经验库·公开）

```yaml
success_id: SD-329
problem_type: 物理建模
method: 模板法最小二乘标定(旋转中心+探测器间距+扫描方向) + Radon投影建模 + 滤波反投影(FBP)重建
why_success: 已知模板(2椭圆+1圆)提供几何基准, 用Lambert-Beer定律+最小二乘反推旋转中心(9.3040,6.2149)、探测器间距0.2768mm、比例系数1.7725; Radon变换描述投影, FBP从投影稳定重建吸收系数分布(国一论文重建附件3/5未知介质)
result: 标定CT系统旋转中心、探测器单元间距与180个扫描方向, 建立投影反演模型重建未知介质的位置、几何形状与吸收系数
limitations: 投影噪声敏感(需滤波)；角度有限(180方向)致伪影；单色平行束近似, 多色X射线有偏差
source: 基于单目标优化模型和图像重建算法的CT系统研究(2017国赛国家一等奖A题优秀论文)|https://m.renrendoc.com/p-84299505.html|2017
confidence: 高
```

---

## SD-330（公开经验库·公开）

```yaml
success_id: SD-330
problem_type: 物理建模
method: 多层一维瞬态导热PDE + 有限差分(向后差分/追赶法)求解温度场 + 步长枚举优化Ⅱ/Ⅳ层厚度
why_success: 服装传热是一维非稳态傅里叶导热, 多层变系数无闭式解, 须数值离散; 由附件2实测最小二乘反演外表面对流系数h≈8.64202 W/(m²·°C)校准边界; 问题2步长0.01mm枚举Ⅱ层得最优19.20mm, 问题3枚举Ⅱ+Ⅳ得21.9mm+6.4mm, 计算值与实测最大相对误差4.95%
result: 建立高温作业服装多层织物(Ⅰ-Ⅲ织物层+Ⅳ空气层)一维瞬态导热模型, 反向优化Ⅱ层(及问题3的Ⅳ层)厚度, 使假人皮肤外侧温度在工作时段内不超过47°C且超过44°C的时间不超过5分钟
limitations: 一维假设忽略侧向传热；层间接触热阻忽略(界面理想)；物性随温度变化未建模(常数近似)
source: 2018年高教社杯全国大学生数学建模竞赛A题优秀论文(高温作业专用服装设计, 多层织物热传递模型)|https://max.book118.com/html/2024/0523/8137051072006072.shtm|2018
confidence: 高
```

---

## SD-331（公开经验库·公开）

```yaml
success_id: SD-331
problem_type: 物理建模
method: 质量守恒ODE(d(ρV)/dt=进油−喷油) + 状态方程dp/dρ=E/ρ(附件3分段拟合E(p)) + 二分/网格搜索控制变量
why_success: 燃油可压缩, 压力由净流量经状态方程决定; 由附件3分段拟合E(p)得ρ(p)关系(100MPa时ρ=0.850mg/mm³); 问题1搜索单向阀开启时长使周期净流量为零得0.285ms(100MPa)/[0.75,0.76]ms(150MPa), 问题2搜凸轮角速度ω≈2.99°/ms使压力稳100MPa
result: 建立高压油管燃油压力动力学模型, 优化单向阀开启时长/凸轮角速度, 使管内压力稳定在目标值(如100MPa), 并扩展至多喷孔+减压阀情形
limitations: 一维均匀压力假设(忽略轴向波动)；弹性模量分段拟合近似；瞬态非线性以均匀变化近似
source: 2019全国大学生数学建模竞赛(高教社杯)A题题解(高压油管的压力控制)|https://www.cnblogs.com/Mayfly-nymph/p/11753977.html|2019
confidence: 高
```

---

## SD-332（公开经验库·公开）

```yaml
success_id: SD-332
problem_type: 物理建模
method: 同心鼓刚体动力学(平动+两自由度转动, 欧拉小角度分解) + 球-鼓碰撞(恢复系数) + 耗能最小最优拉绳策略 + 现实误差三因子调整
why_success: 小角度转动分解使三维问题降为竖直平动+绕X/Y两独立转动(转动顺序无关); 球-鼓用恢复系数e∈[0.6,0.85]的动量/能量守恒; 理想态以队员耗能最小得稳态周期颠球策略; 现实态据倾斜角(0.1s达0.2124°–0.4123°)从拉力大小、鼓面倾斜、站位三方面调整
result: 建立同心鼓(队员拉绳使鼓面水平、连续颠球)的运动与碰撞模型, 给出理想状态最佳协作策略, 并研究发力误差致鼓面倾斜后的调整策略, 使连续颠球次数最多
limitations: 队员水平牵拉假设(忽略竖向分力)；小角度近似(大倾斜失效)；发力误差以时滞+噪声近似
source: “同心协力”策略研究(2019高教社杯全国大学生数学建模竞赛B题, 同心鼓颠球, 赛题全文)|https://www.icourse163.org/forum/1237117709/topic-1342038971.htm|2019
confidence: 高
```

---

## SD-333（公开经验库·公开）

```yaml
success_id: SD-333
problem_type: 物理建模
method: 一维瞬态导热+牛顿冷却(集总参数)建模 + 由实测最小二乘拟合热扩散参数 + 制程界限约束下模拟退火/爬山优化温区温度与带速
why_success: 焊接区中心温度以集总参数+牛顿冷却刻画板上温度滞后; 用附件实测最小二乘拟合弛豫时间τs=52.10s、炉前m=0.05/炉后m=0.017; 问题2单变量搜索最大带速69–76cm/min, 问题3以217°C以上覆盖面积最小为目标得温区(185,203,238,265)°C+带速95cm/min(优秀论文)
result: 建立回焊炉印制板(焊接区中心)温度场模型, 优化各温区设定温度与传送带过炉速度, 使炉温曲线满足焊接工艺制程窗口(升温/峰值/回流/降温)
limitations: 对流换热以牛顿冷却近似；物性随温度变未建模；三维/板上各点差异忽略(取中心)
source: 国赛优秀论文2020年A题: 基于一维热传导方程的炉温曲线机理模型研究|http://www.madio.net/forum.php?mod=viewthread&tid=490621&extra=page%3D1&ordertype=1|2020
confidence: 高
```

---

## SD-334（公开经验库·公开）

```yaml
success_id: SD-334
problem_type: 图模型/选址优化
method: Floyd最短路 + 多目标0-1整数规划(管辖划分与新增平台) + 0-1指派(封锁调度)
why_success: Floyd算法把92×92邻接矩阵转化为任意两点最短路, 作为所有后续模型的距离基础; 0-1整数规划在'覆盖唯一性+3km时限+工作量均衡'约束下精确求解管辖与新增平台位置; 封锁调度用0-1指派使13个路口被20个平台中13个覆盖且最大到达时间最小(minimax)。
result: 在92个路口节点、20个现有平台的城市路网下, 按'3分钟(约3km)出警'约束划分管辖范围, 并在重大突发事件时调度平台对13个进出城路口快速全面封锁; 对全市六区平台设置做合理性评价。
limitations: 发案率为历史统计, 未考虑时空动态变化；路网静态, 忽略拥堵与单行/限行；平台容量与警力上限被简化为'单平台封一个路口；新增平台方案依赖变异系数等代理指标, 未做全生命周期成本评估
source: Python小白的数学建模课-A1.国赛赛题类型分析(含2011B题)|https://blog.csdn.net/youcans/article/details/117410678|2011
confidence: 中
```

---

## SD-335（公开经验库·公开）

```yaml
success_id: SD-335
problem_type: 图匹配/数字图像处理
method: 左右/上下边界匹配 + 行特征聚类(二层筛选) + 人工干预微调
why_success: 边界灰度差异最小可直接求左右邻接(问题一完全自动); 横纵切(问题二/三)边缘信息变短、随机性增强, 需先用行特征向量聚类到行、再在类内做边界匹配, 二层筛选兼顾行归属与行内顺序, 正确率显著高于纯边界贪心。
result: 利用碎片边缘与行特征灰度信息, 恢复被纵切(问题一)、双面纵切(问题二)、横纵切(问题三)碎纸片的原始排列顺序。
limitations: 双面/横纵切时边缘信息缩短, 纯边界匹配正确率下降(英文仅65.1%)；依赖人工干预合并聚类(11类由人工判定每类19张)；对严重脏污、撕裂、缺失碎片鲁棒性差；OSTU阈值对扫描质量敏感
source: 碎纸片的拼接复原-西南交通大学(2013高教社杯全国大学生数学建模竞赛优秀论文选登)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700228.shtml|2013
confidence: 高
```

---

## SD-336（公开经验库·公开）

```yaml
success_id: SD-336
problem_type: 图模型/路径优化与排班
method: 最短路径(图论) + 分区 + 多目标规划(人数最少且均衡) + 三班轮倒
why_success: 先用Dijkstra把连通图转为最短路/时间, 再以'周期≤35min、覆盖全部点、人数最少、均衡度小'为目标作分区与排班; 0-1规划用于求关键路径, 错时上班模型在问题三进一步省人。
result: 在某化工厂26个巡检点构成的无向连通图上(起点为调度中心XJ0022), 安排巡检人数与路线, 使所有点按周期完成巡检且人力资源最少, 同时各工人工作量(行走+巡检耗时)尽量均衡。
limitations: 行走时间取附件给定值, 未考虑实时拥堵；均衡度仅以行走时间衡量, 未含休息/进餐波动；错时上班模型依赖工人可弹性到岗的假设；部分最优解(不分区4人)在固时上班下无法形成班次循环
source: 2017年国赛高教杯数学建模D题巡检线路的排班解题全过程文档及程序|https://blog.csdn.net/weixin_43292788/article/details/142359829|2017
confidence: 高
```

---

## SD-337（公开经验库·公开）

```yaml
success_id: SD-337
problem_type: 图模型/网络流与仿真
method: 2D Island-Bridge + Dijkstra最短路分配 + Danger Index瓶颈识别 + 3D Cellula Automata(Pathfinder)验证
why_success: 用岛-桥降维把多层建筑变成图, Dijkstra(改: 超Visual Range 21m与危险区边不可达、出口α上限)求各点最优出口与路径; Danger Index识别瓶颈; 3D元胞自动机(Pathfinder)直观仿真并间接验证危险指数合理性。
result: 为巴黎卢浮宫建立适应性应急疏散模型, 探索不同出口方案下游客的最优疏散路径与潜在瓶颈, 同时允许救援人员尽快进入; 模型需适应多种潜在威胁。
limitations: 拥堵判定按'通过人员比例'而非绝对数, 致人员密度对逃生时间近乎无影响(模型弱点)；Dijkstra需逐点计算, 耗时较长；空间离散化(网格)使人员移动呈'跳变', 需加密网格补偿；未充分建模语言/团体等多样性(仅三类速度人群)
source: 2019 ICM Problem D 拆解笔记(Paper #1900007, O奖分析)|http://pzrain.github.io/COMAP/paper/2019D|2019
confidence: 高
```

---

## SD-338（公开经验库·公开）

```yaml
success_id: SD-338
problem_type: 排队论/医疗调度
method: 排队论(M/M/79)刻画系统 + 优先级控制FCFS + 离散事件仿真评价
why_success: 用M/M/79把79张床当并联服务台, 以优先级(外伤>其他, 并按手术日匹配度分级)控制FCFS解决队列过长; 仿真算出Wq/Wh/利用率并对比FCFS。
result: 在79张眼科病床与各类手术日固定约束下, 安排入院与手术排程, 使平均等待入院时间最短、床位利用率最高、平均逗留时间最优。
limitations: 假设到达服从泊松、住院日偏态, 与实际波动有差距；未充分建模并发症与个体异质性；周末不手术方案下利用率显著下降(36.1%)；固定床位比例牺牲灵活性
source: 眼科医院一等奖论文(2009高教社杯B题, M/M/79排队模型)|https://max.book118.com/html/2017/0923/134812897.shtm|2009
confidence: 高
```

---

## SD-339（公开经验库·公开）

```yaml
success_id: SD-339
problem_type: 图模型/交通流仿真
method: M/G/K排队论 + VISSIM仿真 + 几何/图论合并模式优化(以吞吐/事故/成本为指标)
why_success: M/G/K排队给出吞吐量与平均排队长度的理论基线; VISSIM仿真验证不同合并模式在轻/重交通下的表现; 蜂窝或图论最优合流给出形状与合并方案; 三者互补且被多篇O奖采用。
result: 确定收费屏障之后车流从 B 个收费亭出口车道扇入(fan-in)回 L 条行车道的区域形状、尺寸与合并模式, 兼顾事故预防、吞吐量(辆/小时)与建设成本, 并考察轻/重交通、自动驾驶车辆与三类收费亭比例的影响。
limitations: 服务时间假设为正态(均值15s), 实际异质性更大；VISSIM参数标定依赖假设(耐心、限速)；自动驾驶与ETC比例为外生情景, 未内生优化；事故率用PET近似, 未含人为失误细节
source: 美赛2017b题优秀论文总结(5篇O奖: 56731/68303/69427/70174/70545)|https://www.cnblogs.com/clover-blog/p/14322409.html|2017
confidence: 高
```

---

## SD-340（公开经验库·公开）

```yaml
success_id: SD-340
problem_type: 图模型/多旅行商(MTSP)分区
method: 多旅行商回路(MTSP)建模 + Floyd完备图 + 二边逐次修正法近似 + 干枝聚类均衡分组
why_success: 把'走遍所有点回O'转为最佳推销员回路; 因NP完全, 用Floyd构造最短路完备图后二边逐次修正法求近似最优H圈; 先按O点最短路树的6条干枝聚类分组, 再各组求回路并按均衡度微调。
result: 从县政府O出发, 走遍全县所有乡(镇)、村并返回O, 在分组数约束下使总路程最短且各组尽量均衡; 在限时与停留时间约束下确定最少组数与最佳路线。
limitations: 最佳推销员回路为NP完全, 只得近似解；均衡度阈值α需事先给定, 分组含启发式；假设车速与停留时间恒定, 忽略天气/故障；节点53个规模下近似算法可行, 更大规模需元启发式
source: 建模案例:最佳灾情巡视路线(1998 CUMCM B)|https://www.bodocs.net/doc/413476347.html|1998
confidence: 高
```

---

## SD-341（公开经验库·公开）

```yaml
success_id: SD-341
problem_type: 图模型/全覆盖路径规划
method: 网格分区 + 均衡分派(S型路线) + 最小生成树连接, 以'最远队员耗时'为优化目标
why_success: 将矩形按人数等分(面积比=人数比)使各组任务均衡; 组内用S型/蛇形扫描保证全覆盖且无重复; 用MST把分散队员连成通信可达的树状链路, 避免末端失联; 目标锁定决定总耗时的'最远队员时间'而非平均时间
result: 在平地矩形目标区域内, 规划搜索队伍的行进路线, 使全境(无遗漏)搜索的总耗时最短, 并满足48小时时限与通信可达约束
limitations: 结果依赖"同时出发"假设, 实际近点队员需等待远点队员；探测半径与速度为主观给定, 模型对参数敏感；多组协同的分组方案非唯一, 不同论文给出20/20/10或23/20/7等不同分组
source: 地面搜索(2008高教社杯全国大学生数学建模竞赛C题)|https://www.bodocs.net/doc/307175172.html|2008
confidence: 高
```

---

## SD-342（公开经验库·公开）

```yaml
success_id: SD-342
problem_type: 系统科学/网络科学/多目标政策模型
method: 系统动力学 + 网络科学多层建模 + 多目标优化(GDP/幸福感)权衡
why_success: 系统动力学描述人口-劳动力-教育-经济的长周期演进; 网络科学处理可扩展性(小/大群体)与多层(经济/政府/劳动力/司法); 多目标优化显式权衡GDP与幸福感及收入/教育/平等三维
result: 为火星'人口零'(Population Zero)移民设计政策模型, 在100年内(至2100年)建立可持续、GDP与幸福感双高且照顾收入/教育/平等(女性留存)的社会
limitations: 医疗外部给定, 模型不完整；幸福感/平等量化主观, 权重敏感；100年尺度外推不确定性大, 参数多为假设
source: ICM 2017 Problem F: Migration to Mars: Utopian Workforce of the 2100 Urban Society|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/problems|2017
confidence: 高
```

---

## SD-343（公开经验库·公开）

```yaml
success_id: SD-343
problem_type: 多目标规划/运筹调度
method: 多目标规划: 以平均满载率(公司利益)与乘客候车/拥挤抱怨(乘客利益)为目标, 加权合并求满意解
why_success: 问题本质是公司效益与乘客体验冲突, 多目标规划显式权衡; 用最高断面通过量反推各时段发车间隔与配车数, 物理意义清晰
result: 在客流时空分布与车辆约束下, 制定全天(5:00-23:00)发车时刻表, 平衡公交公司效益(满载率/车公里)与乘客利益(候车/拥挤), 求最少车辆数
limitations: 客流随机波动(泊松假设与实际有偏)；路堵/超车未建模；排班切换与司机工时成本忽略；权重系数敏感(不同权重得不同满意解)
source: 公交车调度方案的优化模型(2001年B题)|http://www.bodocs.net/doc/4a17008335.html|2001
confidence: 高
```

---

## SD-344（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
success_id: SD-344
problem_type: 多目标优化/组合优化
method: 谐波回归预测 + NSGA-II 四目标算力调度 + 每区域独立储能 LP + 两阶段六目标协同框架
why_success: 题型同时含预测/优化/规划三类子问题，须分治再统一；多目标必须用 Pareto（NSGA-II）保留权衡面而非加权求和；6 区域×2407h 全局 MILP 不可解，故储能改为每区域独立 LP；直接在 6 维空间进化+每点 480 次 LP 会超时，故用两阶段（先快速搜 4 目标 Pareto，再储能 LP 精细核算 6 目标）。
result: 算电协同多目标协同最优：运行成本、碳排放、跨域传输时延、算力利用率、网络峰值、新能源消纳率、服务质量(QoS)
limitations: 谐波回归对小时级强波动刻画弱（sMAPE 仍约 65.8%）；两阶段为近似，knee 点需二次储能核算；未建模电池循环寿命成本与分段充放效率曲线；假设任务不可抢占、未考虑网络带宽排队
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---


---

## SD-345（公开经验库·公开）

```yaml
success_id: SD-345
problem_type: 评价分类
method: SNA多中心度 + PCA综合影响力指数 + 社区发现
why_success: SNA计算度/介数/接近/特征向量/PageRank多维刻画节点角色; PCA把多中心度与发文/被引融合成统一影响力指数排名; 社区发现识别研究团伙。注: 本案例为基于网络科学通用方法的合理推断, 具体赛题数值结果未在可访问来源读取
result: 基于合著/合作网络数据, 评价研究者与机构的学术影响力并识别关键节点与社区
limitations: 合著不等于实际贡献(通讯/一作权重不同)；被引数据滞后且有自引干扰；数据缺失(机构归属不全)影响拓扑
source: 2014 MCM Problem C: Networks|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## SD-346（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
success_id: SD-346
problem_type: 优化决策
method: 序贯贝叶斯验收抽样(Beta(1,1)先验,95%/90%置信停止) + 期望净成本闭式优化 + 装配网络DAG拓扑递推 + 蒙特卡洛校验 + 贝叶斯风险/后悔值
why_success: 问题1序贯抽样贴合题意且平均样本量更低；问题2闭式期望净成本可直接比较6种策略；问题3抽象为DAG递推覆盖m工序n元件一般情形；问题4以贝叶斯后悔值量化抽样不确定性
result: 在给定检测、装配、拆解、废品与调换成本结构下，确定多阶段生产-质检-拆解-调换的最优策略，使合格品期望净收益最大
limitations: 问题3的蒙特卡洛回收模型做了简化，导致S3闭式与MC偏差达38.2%；装配/拆解成本结构假设为线性，未考虑规模折扣；调换损失的期望近似忽略多次调换的级联影响；问题4样本量n不足的后悔值对先验选择敏感
source: 2024高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2024
confidence: 中
source_quality: 高
memory_type: human_replay
```

---

## SD-347（公开经验库·公开）

source_quality: 高
memory_type: human_replay
```yaml
success_id: SD-347
problem_type: 几何覆盖/测线优化
method: 几何覆盖宽度模型 W=2D·tan(θ/2)/(1−tan²(θ/2)·tan²α_eff) + 有效坡度投影 α_eff=α·|sinβ| + 沿等深线走向(strike)布设 + 按沿线最窄覆盖宽度 W_min 自适应定距 + 栅格化覆盖率/漏测率量化
why_success: 四问本质是条带覆盖几何，统一几何模型覆盖单坡(Q1)、旋转剖面(Q2)、均匀坡度(Q3)、真实地形(Q4)；沿走向使覆盖宽度沿线恒定，按 W_min 定距保证无漏测且总长最短
result: 给定海底地形与换能器参数（开角θ=120°、坡度α=1.5°），设计测线（方向+间距）使全覆盖、漏测最小、总长度最短，并满足相邻条带重叠率10%~20%
limitations: “无漏测”与“重叠率≤20%”存在固有冲突：Q4 为保零漏测，重叠>20% 长度达 218.40 NM；覆盖宽度公式忽略声线弯曲与换能器安装误差，属平面几何近似；Q3 均匀坡度假设未考虑地形起伏，仅适用于题给理想坡；β 定义依赖坡面法向水平投影，真实地形需先估主导坡度方向
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## SD-348（公开经验库·公开）

```yaml
success_id: SD-348
problem_type: 优化决策
method: 逻辑斯蒂/高斯倒U曲线拟合 + 标准化线性回归与随机森林置换重要性 + 随机森林/GPR 响应面 + GPR-UCB 序贯实验设计
why_success: 温度→转化率饱和上升、温度→选择性倒U 为物理先验；小样本下响应面仅作交叉验证，主证据取观测值与解析拟合曲线；GPR-UCB 兼顾开发与探索
result: 选择催化剂组合与温度使 C4 烯烃收率(=乙醇转化率×C4烯烃选择性)最大；并设计 5 次补充实验
limitations: 数据量小(114 行)、温度点稀疏，响应面外推存在不确定度；拟合曲线对峰值的解析外推(400→432°C)超出观测域，需标注不确定度；乙醇浓度效应受装料质量/Co 负载量混杂，其方向性结论受限
source: 2021 高教社杯全国大学生数学建模竞赛 B 题（乙醇偶合制备 C4 烯烃） | 2021
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## SD-349（公开经验库·公开）

```yaml
success_id: SD-349
problem_type: 优化决策
method: 图论最短路(Dijkstra全源) + 运筹优化(0-1指派/集合覆盖/增量选址/时间窗围堵)
why_success: 路网规模中等(582节点/928边)，最短路是底层通用算子，全源矩阵一次算出各子问复用；各子问目标清晰(覆盖/均衡/minimax/围堵)，对应成熟运筹模型，无需启发式黑箱
result: 设置交巡警服务平台并分配管辖范围，使3分钟出警覆盖率最高且各平台工作量均衡；对13条要道全封锁、对全城增建平台、对嫌疑犯实现动态围堵
limitations: 直线距离近似会高估覆盖率，必须用Dijkstra精确最短路；Q1c贪心增量选址非全局最优(双目标Pareto可改进)；新增平台未计入建设成本；围堵模型假设嫌疑犯必走最短路，未考虑其绕路规避
source: cumcm2011B题 | 交巡警服务平台的设置与调度 | 2011
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## SD-350（2021华数杯B PSR验证场）

```yaml
success_id: ?
problem_type: 优化/随机需求
method: 报童期望利润模型 + 临界分位
why_success: 把随机需求下的订货量决策转成可解析的报童模型，临界分位给出闭式解
result: CR≈0.61~0.67；高变异货(HW7/9/10)用经验分布求期望而非正态近似
reuse: 推荐（随机需求/库存/批量决策类）
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## SD-351（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电路
method: ABCD/耦合系数闭式效率公式
why_success: η=1/(1+2/(k²Q₁²)+Q₂/(k²Q₁)+(k²+Q₁⁻²)/(k²Q₁Q₂))，复算Q1首组56.196%(官方56.20%)、Q3最大92.77%完全一致
result: Q1 56.196% 与官方一致（verified: true）
reuse: 推荐（谐振/互感/传输效率类机理题）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-352（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电磁
method: Neumann 双重积分严格算互感 M
why_success: 用 scipy.dblquad 对 M=(μ₀N²/4π)∮∮cosφ/|r₁−r₂| 严格积分，轴向M(h)与附件实测10组误差<3%
result: 无需拟合即可预测任意间距/偏移互感（verified: true）
reuse: 推荐（互感/线圈/电磁场计算类）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-353（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（工程交付）
method: pandoc 转 docx 前把 figure 渲染为 PNG
why_success: Word 无法内嵌 LaTeX 生成的 PDF 图，须用 PyMuPDF 渲染 PNG 再让 pandoc 引用
result: docx 完整保留图表（verified: true）
reuse: 强制内置（docx 路线图表交付）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-354（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（中文出图）
method: matplotlib 注册 simhei.ttf 解决中文图缺字
why_success: 默认 DejaVu Sans 缺 CJK 字形，注册 C:/Windows/Fonts/simhei.ttf 后中文正常
result: 中文图正常渲染（verified: true）
reuse: 强制内置（中文出图环境）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-355（公开经验库·公开）

```yaml
success_id: SD-355
problem_type: 优化决策
method: 多尺度特征工程(短时/日内/周内滞后+滚动均值+周期相位编码) + GBRT/Ridge逐序列选型预测 + 事件驱动贪心(EDF)基础调度 + 熵权TOPSIS碳感知多目标 + 分区域储能连续LP(HiGHS) + 上层边际打分/下层LP双层协同(EMA阻尼影子价格)
why_success: 异构序列逐序列RMSE选型避免单一算法统一假设；熵权TOPSIS客观赋权从Pareto前沿选优；双层拆分(离散+连续)避免组合爆炸；HiGHS快速求解大规模连续LP
result: 多区域数据中心在算力需求预测、任务调度、储能运行与电网交互下的算-储-电协同优化：最小化运行成本/碳排放/网络时延，最大化新能源利用率，满足SLA
limitations: 尖峰/低基数序列预测WAPE偏高(67.7%)；上层启发式可能陷入局部最优；储能LP未显式充放电互斥需工程复核；未纳入广域传输能耗与微观潮流约束
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## SD-356（公开经验库·公开）

```yaml
success_id: SD-356
problem_type: 优化
method: 模拟退火+查找表修正HPWL
why_success: 软约束好处理，能跳出局部最优
result: 最小化总连接线长+密度约束
limitations: 大规模时查找表构建耗时
source: 2024华数杯B|VLSI自动布局|CM2401166
confidence: 高
source_quality: 中
memory_type: paper_extract
```

## SD-322

```yaml
problem_type: 优化
situation: 随机几何,无解析解,频率近似
method: 对依赖随机落点的量（锥形光线、遮挡）用蒙特卡洛/光线追迹：大量随机抽样统计频率近似概率
why_success: 目标量无解析式时，统计估计是唯一可行且可用重复次数控制精度的途径
reuse: 我们采取光线追迹法对光线进行追踪。我们选取了大量光线照射任意一块定日镜C
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-357

```yaml
problem_type: 优化
situation: 高维优化,启发式算法,多尺度遍历
method: 外层参数按量纲大步长遍历定初值，内层用遗传算法寻优，再逐步缩小步长精细搜索
why_success: 粗-细两阶段搜索兼顾全局探索与局部精度，避免一步到位的高计算成本
reuse: 将步长逐步缩小遍历，重复Step1与Step2操作，最终确定满足约束条件下的最大单位镜面面积年平均输出热功率
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-358

```yaml
problem_type: 优化
situation: 镜面逐点的阴影损失与挡光损失判定
method: 镜面离散为S个点，坐标变换到邻镜局部系做直线-平面求交，无效点占比Sl/S即效率
why_success: 把“遮挡”统一化为同一局部系下的直线与矩形求交，判定路径单一、易编程
reuse: 将第i 面定日镜离散化为S 个点后，通过遍历的方法逐一判断每一个点是否为“无效点”，得出“无效点”的数量Sl，通过式(15) 可以得出第i 面定日镜的阴影损失和
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-359

```yaml
problem_type: 优化
situation: Wa、Wb、hi、L0 四维决策变量直接高精度遍历组合爆炸
method: 变步长遍历：大步长粗搜出初步区间，步长缩为十分之一在区间内细搜
why_success: 先全局后局部，兼顾搜索完备性与精度，代价是少量额外迭代
reuse: 对于各定日镜场参数，将搜索步长缩短为原来的十分之一，并在初步范围内以小步长遍历Wa、Wb、hi 和L0。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-360

```yaml
problem_type: 优化
situation: 目标函数无解析式,需确认变量极值结构
method: 对关键决策变量(D、W)做一维扫描画出目标函数曲线，先验证单峰性再选极值算法
why_success: 单峰性验证为三分法提供理论前提，避免盲目套用全局算法
reuse: 固定其他变量进行并改变D 的值，模拟得到不同D 取值下的目标函数值Pd，并证明了Pd 是关于D 的单峰函数。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-361

```yaml
problem_type: 优化
situation: 优化变量维度高、全遍历计算量不可行
method: 蜂窝排列法固定布局结构→旋转角参数化位置→蒙特卡洛抽样10%粗寻优→减小步长细化
why_success: 规则布局降维加随机抽样削减计算量，得到可接受的局部最优
reuse: 5.2.1-5.2.2：蜂窝排列确定尺寸数目位置，随机选取10%的定日镜计算光学效率预测粗解
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-362

```yaml
problem_type: 机理
situation: 需程序化判断光线是否被塔/前镜遮挡、是否被集热器接收
method: 光线参数方程与几何体方程联立求判别式，用0-1变量统计命中率作为效率
why_success: 把几何条件转化为可编程判别，效率化为光线命中比例，便于网格化枚举
reuse: 4.2.2-4.2.3：联立方程判别式判断遮挡与接收，引入0,1变量r_j表示第j根光线是否被接收
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-363

```yaml
problem_type: 优化
situation: 单目标优化模型难以解析求解时
method: Step式贪心循环遍历：以边界确定首条测线位置→定步长向后遍历→按重叠率约束筛选候选→贪心规则（优先10%）择优→越界终
why_success: 算法流程显式可复现，约束可逐条检验，评审能核验每一步操作
reuse: Step 1 以矩形海域的东边界为始边，以覆盖宽度恰好能达到东边界确定出第一条测线的位置（原文问题三）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-364

```yaml
problem_type: 优化
situation: 重叠率下限固定,已知一条测线位置,求全部测线
method: 固定重叠率为最小临界值,用重叠率方程解相邻测线位置,逐条递推至区域边界
why_success: 把全局布局问题化为单步方程递推,无需大规模优化且结果可复现
reuse: 在重叠率η和第一条测线位置确定的情况下,联立覆盖宽度与重叠率方程求出下一条测线位置,以此类推,当测线越过区域边界时停止递推。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-365

```yaml
problem_type: 优化
situation: 曲线地形,多目标,需分区设计
method: 按等高线将海域分区,每区以最宽处全覆盖确定等高距,再沿梯度方向递推测线
why_success: 把复杂地形分解为准均匀坡面,复用前问模型并量化测线总长与漏测率
reuse: 将待测海域依据等高线划分为三个测区,以每条等高线为基准,找出下一条等高线深度与上一条的递推函数关系,利用Matlab画出航线图,并计算出测线总长度与漏测率。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-366

```yaml
problem_type: 优化
situation: 测线最短且全覆盖
method: 贪心定航向再以重叠率为迭代控制指标
why_success: 把双目标拆成方向优化与位置递推两步，降低耦合
reuse: 基于贪心算法的思想，为使测线的长度最短，需要使得��在各处尽可能宽，由此可得到最短测线距离。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-367

```yaml
problem_type: 优化
situation: 复杂曲面航向决策
method: 先证最大覆宽方向为梯度垂直方向，局部最优拼全局
why_success: 几何论证给出方向解析解，避免纯黑盒搜索
reuse: 由于梯度垂直其等高线，那么(��, ��)一定是最近点。在搜索完一路后，我们以梯度作为方向，让粒子跃迁到下一路。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-368

```yaml
problem_type: 优化
situation: 利润最大化优化模型难以精确求解时
method: 用模拟退火求较优解：设定初温、温度衰减系数与每温度迭代上限，按Metropolis准则概率接受新状态跳出局部最优
why_success: 参数显式可复现，概率突跳机制能跳出局部最优并趋于全局最优，适合离散决策空间
reuse: 设定模拟退火算法的初始温度为100℃，温度衰减系数𝛼= 0.95，且在每个温度上迭代最多100 次
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-369

```yaml
problem_type: 预测
situation: 需为多序列分别选择合适的时间序列模型时
method: 借助SPSS专家建模器按序列特征自动匹配模型（简单季节性/温特斯乘性），并列出各品类对应的模型类型
why_success: 自动选型避免手调每个序列，季节趋势序列用季节分解模型，模型选择有据可查
reuse: 本文利用SPSS 软件构建时间序列模型，以专家建模器为基本算法进行预测未来一周的各蔬菜品类日销量。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-370

```yaml
problem_type: 统计
situation: 销量零膨胀且非正态
method: 用同期平均法把三年数据折成一年，绕开零膨胀建模困难
why_success: ZIP建模难度超本科水平且MCMC运算压力大，同期平均保留周期规律
reuse: 为避开零膨胀数据建模的困难，同时降低WinBUGS 运行MCMC 的运算压力，用同期平均法将三年数据进行转化，形成一年的数据
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-371

```yaml
problem_type: 预测
situation: 多品类联动预测未来一周销量
method: 用生鲜可售寿命业务规则直接定VAR阶数为2
why_success: 业务规则比信息准则定阶更直观可信，且与陈列天数一致
reuse: 为此确定滞后期为2 期，表明今天销售的蔬菜最多是今天凌晨3－4 点进的货，也就是在商超陈列2 天，即售卖2 天，从而确定VAR 模型的阶数为2。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-372

```yaml
problem_type: 优化
situation: 决策变量同时含0-1选择变量与连续数量变量且双目标
method: 按变量类型选算法：混合编码NSGA-II而非PSO或传统遗传算法
why_success: 混合变量+多目标下粒子群与标准遗传算法性能较差，NSGA-II非支配排序+拥挤距离保前沿多样性
reuse: 由于本问决策变量中既含有0-1 变量又含有连续变量，粒子群算法和传统遗传算法的性能较差，需要使用混合编码和多目标规划的优化算法。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-373

```yaml
problem_type: 预测
situation: 需剔除季节、趋势、节假日效应以分析价格对需求的影响时
method: 用带外生价格变量的Prophet分解趋势/周期/节假日项，剔除后对价格回归得影响函数
why_success: Prophet可解释性强、能分离各成分且稳健，外生项让价格直接进入预测模型，实现预测与定价分析一体化
reuse: 本文使用带有外生回归项的Prophet 模型刻画决定市场需求的主要因素。
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-374

```yaml
problem_type: 优化
situation: 目标函数内嵌预测模型难以全局优化，且需求函数仅在小价格波动内有效时
method: 用模拟退火在上一日定价附近求局部最优，并逐日滚动把当日最优结果回填为次日预测输入
why_success: 全局最优距离初始方案远无实际意义，小波动范围+低初始温度能快速收敛，滚动耦合保证决策时序
reuse: 距离初始定价方案较远的全局最优解反而并不具备实际意义，模型的目标是寻找位于上一日定价附近的局部最优解
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-375

```yaml
problem_type: 优化
situation: 完整非线性整数规划约束过多, 基本不可解
method: 决策变量少时放弃通用求解器, 对称化降维后遍历
why_success: 有限整数空间上遍历可复现且保证全局最优, 比启发式稳
reuse: 这样决策变量只有两个整数, 决策空间有限, 用遍历的方法得到最优解
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-376

```yaml
problem_type: 优化
situation: 存在随机性(受孕率、孕期时长)时建立期望损失模型
method: 随机性离散成分支后对1维变量枚举, 蒙特卡洛算期望
why_success: 一维决策变量使枚举成为最稳求解路径, 且能画出损失曲线验证单峰性
reuse: 由于决策变量是1维的, 我们用遍历法求解. 我们观察到随着x 的增加损失先递减后递增, 在x=40 时得到最小的日均损失数3.79
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-377

```yaml
problem_type: 预测
situation: 时间序列建模,流程需完整可复现
method: 按“平稳性检验→差分→定阶→拟合→诊断→预测”标准流程组织
why_success: ADF检验、差分、ACF/PACF、AIC/BIC、D-W诊断逐项呈现，评审可逐环节核对
reuse: 对于非平稳时间序列要先进行d阶差分运算，化为平稳时间序列。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-378

```yaml
problem_type: 预测
situation: 周期性序列需外推未来两年数据
method: 依Dirichlet条件用10阶傅里叶级数逼近周期函数，留出一年数据先检验预测误差再外推
why_success: 傅里叶级数对周期序列逼近精度高，留出样本检验误差使预测有量化依据
reuse: 取2018-2020 年（36 个月）的水沙通量数据作拟合，再对2021 年（12 个月）的水沙通量数据进行预测，接着作预测误差估计
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-379

```yaml
problem_type: 统计
situation: 多次测量位置、起终点各不相同,需复原完整轮廓
method: 先旋转校正各次数据,再以各组第一个圆位置为基准做水平平移对齐,按横坐标范围整合拼接成完整轮廓
why_success: 统一的基准点对齐消除位置偏差,取并集拼接即可复原超出单次测量范围的完整轮廓
reuse: 选用每组数据中从左边起第一个圆的位置作为基准，对每组数据进行水平方法的平移矫正。
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-380

```yaml
problem_type: 统计
situation: 多组测量数据合并
method: 变换对齐后10组数据合并为一组再拟合,等效增大样本量
why_success: 单次测量信息有限,合并后拟合更稳、轮廓更完整
reuse: 我们把经过变换后的10条轮廓的散点数据（10组数据）汇总合为一条散点图（一组数据），进行拟合函数，拟合方法同问题1
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-381

```yaml
problem_type: 评价
situation: 两种测量状态参数对比
method: 用柱状图分六类对比两状态参数并逐图解读
why_success: 可视化差异直观,有力支撑'误差可接受'的结论
reuse: 为了比较两种测量状态下工件1各项参数计算值之间的差异，我们将两次表格得到的数据利用柱状图进行对比
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-382

```yaml
problem_type: 统计
situation: 差分序列噪声大, 有重叠与无重叠滑窗二选一
method: 对比两种滑窗识别效果, 选能识别目标线段的方案
why_success: 无重叠滑窗保留竖直斜线段的短暂平直区, 有重叠则几乎识别不出
reuse: 因此下文主要采用无滑窗的去燥方法。
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-383

```yaml
problem_type: 统计
situation: 每组数据需估计倾斜角, 单一直线斜率不可靠
method: 按斜率相等与否给直线分类, 取数量最多目标类斜率作旋转角
why_success: 多数表决抑制噪声, 比单一直线估计稳健
reuse: 把每组中直线数量最多的类作为目标类。将目标类中直线的斜率作为本组数据的旋转角度
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-384

```yaml
problem_type: 统计
situation: 需估计整体倾斜角, 单条直线斜率噪声大
method: 取多条同向直线斜率平均再取反正切, 用平均抑制随机误差
why_success: 多线平均抵消随机误差, 比单一直线估计稳健
reuse: 取多条直线计算夹角取平均值减小误差
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-385

```yaml
problem_type: 统计
situation: 10次测量姿态起点不同, 数据分散需先对齐再融合
method: 以轮廓最高点/最低点等特征点平移对齐, 重合后合并数据统一拟合
why_success: 特征点明确可比, 平移不改变形状, 把多源数据拼成一份完整数据
reuse: 将9个图像的最低点经过上下左右平移到校准点，此时，9组数据基本重合。
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-386

```yaml
problem_type: 优化
situation: 需要在线实时快速给出调整方案
method: 推导切割总损失最小值关于尾坏长度的分段解析函数f(L)，直接查式求值
why_success: 免去每次异常都重解整数规划，提高在线调整效率，且与数值解完全吻合
reuse: 给出了切割总损失最小值函数L关于尾坏长度L的函数解析表达式。进一步，将整线性规划模型所求的切割损失最小值固定
source: 2021国赛D|连铸切割的在线优化模型|D017
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-387

```yaml
problem_type: 优化
situation: 序贯求解,前序最优值,等式约束
method: 序贯求解时将前序目标的最优值作为等式约束加入下一目标
why_success: 保证次优目标在主目标最优前提下优化，不破坏主目标
reuse: 将得到的最优解看做约束条件放入第二个目标（即切割长度为9.5米的根数最多）求解最优。
source: 2021国赛D|连铸切割的在线优化|D026
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-388

```yaml
problem_type: 优化
situation: 长度下限,4.7米,合并切割
method: 小于最小切割长度的段与下段报废段合并固定长度切割
why_success: 满足基本约束避免阻碍生产，固定该段简化后续求解
reuse: 由于第7个时间单元的钢坏长度为4.7米（含一个报废段），不满足切割后的钢坏长度必须在4.8-12.6米之间的基本要求，因此将第7个时间单元的钢坏长度（4.7米）与第8个时间单元的报废段（0.8米）结合切割
source: 2021国赛D|连铸切割的在线优化|D026
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-389

```yaml
problem_type: 动态新增报废段的切割优化
situation: 结晶器异常导致报废段不断出现，需判断每次是否调整方案
method: 把每段钢坯与报废段整体切割得初始方案，再构造合并相邻报废段（方案1）与合并相邻钢坏最小切割损失（方案2）的调整方案，按损失与二次切割次数比较取舍
why_success: 报废段是固定损失，可与相邻段损耗合并，方案对比使调整决策有量化依据
reuse: 当相邻两段钢坏的最小损耗值之和加上两段钢坏之间报废段长度大于等于4.8米，小于等于12.6米时，应将两段钢坏的损耗部分与报废段一同切割，以达到优化切割工序的目的
source: 2021国赛D|连铸切割的在线优化|2021_D_D034
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-390

```yaml
problem_type: 优化
situation: 阻尼系数多变量寻优且范围大
method: 粗搜得到粗略解后用遗传算法精确寻优
why_success: 遗传算法并行搜索、概率选择，可跳出局部最优并快速收敛
reuse: 本文采用增大步长的方法得到粗略结果。为精确结果，本文另外采用遗传算法。
source: 2022国赛A|波浪能装置输出功率优化设计|A001
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-391

```yaml
problem_type: 机理
situation: 垂荡与纵摇强耦合且转轴受力未知
method: 先以数据估算角位移与相对位移为小量,将垂荡与纵摇解耦;纵摇中将浮子振子视为整体,再建以转轴为原点的平动非惯性系
why_success: 解耦把8维耦合系统拆成可分别求解的子系统,整体化回避未知的转轴受力
reuse: 在考虑垂荡运动时，可以忽略由于纵摇运动带来的影响；在考虑纵摇运动时，由于计算得到的浮子和振子的相对垂荡位移很小，因此可以将浮子和振子视为一个整体计算转动
source: 2022国赛A|波浪能装置输出功率最大化模型|A022
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-392

```yaml
problem_type: 机理
situation: 几何形态众多
method: 先分析类别全面性再建模型,3类9形态→6模型
why_success: 全面性分析先行保证不遗漏几何形态
reuse: 在针对以上三类九种形态的位置关系仅考虑分类讨论的类别全面性分析的完整性
source: 2022国赛B|无人机遂行编队飞行中的纯方位无源定位|B030
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-393

```yaml
problem_type: 统计
situation: 结论需要统计背书
method: 10500组仿真样本求平均偏差,给出100%准确率
why_success: 大样本统计结论可信,支撑'仅需一架发射机'
reuse: 仿真模拟的准确率达到100%上表展示的是随机2的10500组数据
source: 2022国赛B|无人机遂行编队飞行中的纯方位无源定位|B030
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-394

```yaml
problem_type: 优化
situation: 调整方案搜索（选择发射信号的无人机）
method: 带阈值启发式搜索：每轮决策前向前搜索若干层，以L2 loss为估价函数选最优叶子
why_success: DFS层数无限无法完成，贪心短视易局部最优，多步前瞻兼顾效率与全局性
reuse: 因此我们采取了带阈值的启发式搜索算法，在每次决策之前对以后若干层搜索，找出局面最优的叶子结点
source: 2022国赛B|基于计算几何与带阈值启发式搜索的无人机无源定位模型|B035
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-395

```yaml
problem_type: 优化
situation: 目标函数,邻域搜索,步长,仿真
method: 以方位角向量与标准值向量范数平方最小为目标，在正方形邻域内按步长搜索
why_success: 局部信息即可迭代调整，便于仿真模拟
reuse: 以无人机9为中心，在边长为a的正方形区域内以步长b调整，使目标函数达到最小值。
source: 2022国赛B|基于局部最优模型的无人机位置调整策略与仿真定位|B086
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-396

```yaml
problem_type: 机理
situation: 贪心策略,引理,锥形编队,三步调整
method: 按三个引理把锥形编队调整分解为三步贪心操作
why_success: 化整为零，逐步收敛到严格队形
reuse: 将无人机分为中心对称的三类，基于引理按贪心策略分三步调整
source: 2022国赛B|基于局部最优模型的无人机位置调整策略与仿真定位|B086
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-397

```yaml
problem_type: 带标签的分类规律挖掘与亚类划分
situation: 已知玻璃类型标签，需找分类规律并为各类划分亚类
method: 决策树（信息增益）找可解释分类规则；R型聚类对14种成分聚类取代表变量，再基于代表变量做Q型聚类划分亚类；扰动法做敏感性
why_success: 特征筛选先行使亚类划分更客观，决策树给出阈值型规则
reuse: 首先对坡璃的14种十要化学成分进行R型聚类分析法：将14种化学成分聚成三类，再取每类具有代表性的成分当做合适的化学成分进行Q型聚类，进而得到业分类结果
source: 2022国赛C|基于成分数据的古代玻璃制品的成分分析与鉴别|2022_C_C155
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-398

```yaml
problem_type: 多指标变量关联分析
situation: 分析两类玻璃化学成分指标间的关联及类别间差异
method: 遍历每项成分依次作母序列、其余成分作子序列建灰色关联分析，加权关联系数得关联度，比较类别间关联度分布差异
why_success: 灰色关联适用于小样本、无规律样本的变量关联度量
reuse: 出于每和坡璃类别都有十四项化学成分，手是遍历每项成分，依次作为母序列，其余十三组成分作为子序列，建立灰色关联分析模型
source: 2022国赛C|基于成分数据的古代玻璃制品的成分分析与鉴别|2022_C_C155
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-399

```yaml
problem_type: 优化
situation: K与N的关系需覆盖所有自然数情形
method: 对参数取模分类逐一讨论并给出对应方案
why_success: 分类讨论覆盖边界情形，结论更严谨无遗漏
reuse: 取5K+1=4m,4m+1,4m+2,4m+3，则可遍历所有自然数。
source: 2022国赛D|气象报文信息卫星通信传输|D999
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-400

```yaml
problem_type: 预测
situation: 需把生产计划转成库存/缺货/服务水平指标
method: 建立库存量、缺货量与服务水平之间的递推关系:库存=上期库存+本期生产-实际需求,不足部分计缺货,服务水平=1-缺货/需求
why_success: 递推关系把所有评价指标统一到一张表,每周围绕同一公式迭代计算,可批量实现
reuse: 进一步假设第100周未的库存量和缺货量均为零，第100周的生产计划数恰好等于第101周的实际需求数，即第101周库存量=0，缺货量-0。
source: 2022国赛E|基于时间序列预测的物料生产安排模型|E014
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-401

```yaml
problem_type: 优化
situation: 随机几何,无解析解,频率近似
method: 对依赖随机落点的量（锥形光线、遮挡）用蒙特卡洛/光线追迹：大量随机抽样统计频率近似概率
why_success: 目标量无解析式时，统计估计是唯一可行且可用重复次数控制精度的途径
reuse: 我们采取光线追迹法对光线进行追踪。我们选取了大量光线照射任意一块定日镜C
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-402

```yaml
problem_type: 优化
situation: 高维优化,启发式算法,多尺度遍历
method: 外层参数按量纲大步长遍历定初值，内层用遗传算法寻优，再逐步缩小步长精细搜索
why_success: 粗-细两阶段搜索兼顾全局探索与局部精度，避免一步到位的高计算成本
reuse: 将步长逐步缩小遍历，重复Step1与Step2操作，最终确定满足约束条件下的最大单位镜面面积年平均输出热功率
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-403

```yaml
problem_type: 优化
situation: 镜面逐点的阴影损失与挡光损失判定
method: 镜面离散为S个点，坐标变换到邻镜局部系做直线-平面求交，无效点占比Sl/S即效率
why_success: 把“遮挡”统一化为同一局部系下的直线与矩形求交，判定路径单一、易编程
reuse: 将第i 面定日镜离散化为S 个点后，通过遍历的方法逐一判断每一个点是否为“无效点”，得出“无效点”的数量Sl，通过式(15) 可以得出第i 面定日镜的阴影损失和挡光损失ηl−i。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-404

```yaml
problem_type: 优化
situation: Wa、Wb、hi、L0 四维决策变量直接高精度遍历组合爆炸
method: 变步长遍历：大步长粗搜出初步区间，步长缩为十分之一在区间内细搜
why_success: 先全局后局部，兼顾搜索完备性与精度，代价是少量额外迭代
reuse: 对于各定日镜场参数，将搜索步长缩短为原来的十分之一，并在初步范围内以小步长遍历Wa、Wb、hi 和L0。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-405

```yaml
problem_type: 优化
situation: 目标函数无解析式,需确认变量极值结构
method: 对关键决策变量(D、W)做一维扫描画出目标函数曲线，先验证单峰性再选极值算法
why_success: 单峰性验证为三分法提供理论前提，避免盲目套用全局算法
reuse: 固定其他变量进行并改变D 的值，模拟得到不同D 取值下的目标函数值Pd，并证明了Pd 是关于D 的单峰函数。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-406

```yaml
problem_type: 优化
situation: 优化变量维度高、全遍历计算量不可行
method: 蜂窝排列法固定布局结构→旋转角参数化位置→蒙特卡洛抽样10%粗寻优→减小步长细化
why_success: 规则布局降维加随机抽样削减计算量，得到可接受的局部最优
reuse: 5.2.1-5.2.2：蜂窝排列确定尺寸数目位置，随机选取10%的定日镜计算光学效率预测粗解
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-407

```yaml
problem_type: 机理
situation: 需程序化判断光线是否被塔/前镜遮挡、是否被集热器接收
method: 光线参数方程与几何体方程联立求判别式，用0-1变量统计命中率作为效率
why_success: 把几何条件转化为可编程判别，效率化为光线命中比例，便于网格化枚举
reuse: 4.2.2-4.2.3：联立方程判别式判断遮挡与接收，引入0,1变量r_j表示第j根光线是否被接收
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-408

```yaml
problem_type: 优化
situation: 单目标优化模型难以解析求解时
method: Step式贪心循环遍历：以边界确定首条测线位置→定步长向后遍历→按重叠率约束筛选候选→贪心规则（优先10%）择优→越界终止
why_success: 算法流程显式可复现，约束可逐条检验，评审能核验每一步操作
reuse: Step 1 以矩形海域的东边界为始边，以覆盖宽度恰好能达到东边界确定出第一条测线的位置（原文问题三）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-409

```yaml
problem_type: 优化
situation: 重叠率下限固定,已知一条测线位置,求全部测线
method: 固定重叠率为最小临界值,用重叠率方程解相邻测线位置,逐条递推至区域边界
why_success: 把全局布局问题化为单步方程递推,无需大规模优化且结果可复现
reuse: 在重叠率η和第一条测线位置确定的情况下,联立覆盖宽度与重叠率方程求出下一条测线位置,以此类推,当测线越过区域边界时停止递推。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-410

```yaml
problem_type: 优化
situation: 曲线地形,多目标,需分区设计
method: 按等高线将海域分区,每区以最宽处全覆盖确定等高距,再沿梯度方向递推测线
why_success: 把复杂地形分解为准均匀坡面,复用前问模型并量化测线总长与漏测率
reuse: 将待测海域依据等高线划分为三个测区,以每条等高线为基准,找出下一条等高线深度与上一条的递推函数关系,利用Matlab画出航线图,并计算出测线总长度与漏测率。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-411

```yaml
problem_type: 优化
situation: 测线最短且全覆盖
method: 贪心定航向再以重叠率为迭代控制指标
why_success: 把双目标拆成方向优化与位置递推两步，降低耦合
reuse: 基于贪心算法的思想，为使测线的长度最短，需要使得��在各处尽可能宽，由此可得到最短测线距离。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-412

```yaml
problem_type: 优化
situation: 复杂曲面航向决策
method: 先证最大覆宽方向为梯度垂直方向，局部最优拼全局
why_success: 几何论证给出方向解析解，避免纯黑盒搜索
reuse: 由于梯度垂直其等高线，那么(��, ��)一定是最近点。在搜索完一路后，我们以梯度作为方向，让粒子跃迁到下一路。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-413

```yaml
problem_type: 优化
situation: 利润最大化优化模型难以精确求解时
method: 用模拟退火求较优解：设定初温、温度衰减系数与每温度迭代上限，按Metropolis准则概率接受新状态跳出局部最优
why_success: 参数显式可复现，概率突跳机制能跳出局部最优并趋于全局最优，适合离散决策空间
reuse: 设定模拟退火算法的初始温度为100℃，温度衰减系数𝛼= 0.95，且在每个温度上迭代最多100 次
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-414

```yaml
problem_type: 预测
situation: 需为多序列分别选择合适的时间序列模型时
method: 借助SPSS专家建模器按序列特征自动匹配模型（简单季节性/温特斯乘性），并列出各品类对应的模型类型
why_success: 自动选型避免手调每个序列，季节趋势序列用季节分解模型，模型选择有据可查
reuse: 本文利用SPSS 软件构建时间序列模型，以专家建模器为基本算法进行预测未来一周的各蔬菜品类日销量。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-415

```yaml
problem_type: 统计
situation: 销量零膨胀且非正态
method: 用同期平均法把三年数据折成一年，绕开零膨胀建模困难
why_success: ZIP建模难度超本科水平且MCMC运算压力大，同期平均保留周期规律
reuse: 为避开零膨胀数据建模的困难，同时降低WinBUGS 运行MCMC 的运算压力，用同期平均法将三年数据进行转化，形成一年的数据
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-416

```yaml
problem_type: 预测
situation: 多品类联动预测未来一周销量
method: 用生鲜可售寿命业务规则直接定VAR阶数为2
why_success: 业务规则比信息准则定阶更直观可信，且与陈列天数一致
reuse: 为此确定滞后期为2 期，表明今天销售的蔬菜最多是今天凌晨3－4 点进的货，也就是在商超陈列2 天，即售卖2 天，从而确定VAR 模型的阶数为2。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-417

```yaml
problem_type: 优化
situation: 决策变量同时含0-1选择变量与连续数量变量且双目标
method: 按变量类型选算法：混合编码NSGA-II而非PSO或传统遗传算法
why_success: 混合变量+多目标下粒子群与标准遗传算法性能较差，NSGA-II非支配排序+拥挤距离保前沿多样性
reuse: 由于本问决策变量中既含有0-1 变量又含有连续变量，粒子群算法和传统遗传算法的性能较差，需要使用混合编码和多目标规划的优化算法。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-418

```yaml
problem_type: 预测
situation: 需剔除季节、趋势、节假日效应以分析价格对需求的影响时
method: 用带外生价格变量的Prophet分解趋势/周期/节假日项，剔除后对价格回归得影响函数
why_success: Prophet可解释性强、能分离各成分且稳健，外生项让价格直接进入预测模型，实现预测与定价分析一体化
reuse: 本文使用带有外生回归项的Prophet 模型刻画决定市场需求的主要因素。
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-419

```yaml
problem_type: 优化
situation: 目标函数内嵌预测模型难以全局优化，且需求函数仅在小价格波动内有效时
method: 用模拟退火在上一日定价附近求局部最优，并逐日滚动把当日最优结果回填为次日预测输入
why_success: 全局最优距离初始方案远无实际意义，小波动范围+低初始温度能快速收敛，滚动耦合保证决策时序
reuse: 距离初始定价方案较远的全局最优解反而并不具备实际意义，模型的目标是寻找位于上一日定价附近的局部最优解
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-420

```yaml
problem_type: 优化
situation: 完整非线性整数规划约束过多, 基本不可解
method: 决策变量少时放弃通用求解器, 对称化降维后遍历
why_success: 有限整数空间上遍历可复现且保证全局最优, 比启发式稳
reuse: 这样决策变量只有两个整数, 决策空间有限, 用遍历的方法得到最优解
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-421

```yaml
problem_type: 优化
situation: 存在随机性(受孕率、孕期时长)时建立期望损失模型
method: 随机性离散成分支后对1维变量枚举, 蒙特卡洛算期望
why_success: 一维决策变量使枚举成为最稳求解路径, 且能画出损失曲线验证单峰性
reuse: 由于决策变量是1维的, 我们用遍历法求解. 我们观察到随着x 的增加损失先递减后递增, 在x=40 时得到最小的日均损失数3.79
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-422

```yaml
problem_type: 预测
situation: 时间序列建模,流程需完整可复现
method: 按“平稳性检验→差分→定阶→拟合→诊断→预测”标准流程组织
why_success: ADF检验、差分、ACF/PACF、AIC/BIC、D-W诊断逐项呈现，评审可逐环节核对
reuse: 对于非平稳时间序列要先进行d阶差分运算，化为平稳时间序列。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-423

```yaml
problem_type: 预测
situation: 周期性序列需外推未来两年数据
method: 依Dirichlet条件用10阶傅里叶级数逼近周期函数，留出一年数据先检验预测误差再外推
why_success: 傅里叶级数对周期序列逼近精度高，留出样本检验误差使预测有量化依据
reuse: 取2018-2020 年（36 个月）的水沙通量数据作拟合，再对2021 年（12 个月）的水沙通量数据进行预测，接着作预测误差估计
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-424

```yaml
problem_type: 机理
situation: 轨迹含螺线与圆弧混合段
method: 把调头路径划分为盘入螺线、两段圆弧、盘出螺线四个区域，再按时间分段处理。
why_success: 各段几何方程不同，分区后每段用各自方程求解并判断区域交界
reuse: 接着将整个调头过程分为盘入盘出螺线及两段圆弧四块区域并对时间段进行划分
source: 2024国赛A|基于几何模型的舞龙队位置和速度分析|A016
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-425

```yaml
problem_type: 机理
situation: 旋转螺旋运动建模
method: 选极坐标系与阿基米德螺旋线方程，理由是极坐标自然描述旋转且弧长公式可解析积分
why_success: 坐标系贴合运动对称性，使位置-弧长-速度推导全程在极坐标内完成
reuse: 因为极坐标中的极径与极角关系常被用于描述物体的旋转运动，所以我们可以在极坐标系中用阿基米德螺旋线方程来描龙头，龙身及龙尾把手的位置
source: 2024国赛A|基于自标优化的板凳龙形态调节|A053
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-426

```yaml
problem_type: 机理
situation: 凸多边形碰撞检测
method: 选分离轴定理：把矩形板凳的碰撞判定化为各投影轴上投影区间的重叠判断，并封装0/1碰撞检测函数
why_success: 几何重叠转区间比较，判定条件清晰且可写成约束参与后续优化
reuse: 基于分离轴定理，将龙头碰撞问题转化为板尧所占矩形区域的重登问题，进而建立出盘入碰撞检测模型。
source: 2024国赛A|基于自标优化的板凳龙形态调节|A053
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-427

```yaml
problem_type: 机理
situation: 连续运动,微元法,微分方程,解析解,误差累积
method: 微元几何推导运动微分方程并求解析解，避免数值积分误差累积
why_success: 解析解调用快且无累积误差，支撑后续二分法等多次重复求解（每步都要调用同一求解器）
reuse: 利用微元法获得微分方程，并求得解析解，避免了数值求解时带来的误差积累，提高求解效率和精度。
source: 2024国赛A|板凳龙表演的行进路径与速度控制|A178
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-428

```yaml
problem_type: 机理
situation: 碰撞检测,近似模型,搜索空间裁剪,误差1%
method: 同心圆近似螺线估计事件时刻，将精确判定限制在小区间变步长搜索
why_success: 近似估计误差在1%以内，把全域遍历降为局部搜索，成本与精度兼得
reuse: 问题二采取同心圆近似螺线估计碰撞时间，极大地减少了后续对时间遍历的搜索空间，减小求解成本：同时估计结果与真实结果较为接近，误差在1%以内。
source: 2024国赛A|板凳龙表演的行进路径与速度控制|A178
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-429

```yaml
problem_type: 优化
situation: 需确认最小螺距搜索没有遗漏更优解
method: 绘制目标函数最小值随决策变量d变化的图像，检验其单调性并与安全阈值线对照
why_success: 单调性说明变步长搜索不会遗漏更小可行螺距，从灵敏度角度验证了算法与结果
reuse: 从图中可以看出，dis（t）在龙头前把手进人调头空间前的最小值随螺距d增大而单调增加，且呈较明显的线性关系。这表明变步长搜索并不会遗漏满足要求的更小螺距，证明了我们算法选择的合理性。
source: 2024国赛A|基于动态搜索的“板凳龙”运动状态及路线研究|A242
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-430

```yaml
problem_type: 优化
situation: 多工序系统状态-决策模型的搭建
method: 按“状态变量定义→决策变量定义→成本函数→收益函数→模型总结→算法求解”分层展开
why_success: 把复杂系统拆成可复用构件，模型逻辑链完整且可迁移到其它多阶段问题
reuse: 为了构建状态-决策模型，首先靠要明确该问题背景下不同阶段的状态变量与决策变量定义。……系统的状态S描述了当前零件，半成品和成品的质量状况及其检测结果。
source: 2024国赛B|生产过程中的决策优化设计|B159
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-431

```yaml
problem_type: 优化
situation: 高维0-1决策向量的优化求解
method: 用模拟退火优化连续松弛的决策向量（允许0~1浮动），收敛后观察端点取值
why_success: 退火可跳出局部最优，连续化便于算法实施，端点性反证离散化假设
reuse: 求解过程依旧采用退火算法（设置初始零件为10000套），优化后的决策变量很可能只取0或1，但为了完成模拟退火的优化过程，允许其值在0～1之间浮动（5.2.8、5.3.6概括）
source: 2024国赛B|基于多阶段模拟仿真的生产决策问题|B195
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-432

```yaml
problem_type: 优化
situation: 抽样方案需给出(n,c)数对
method: 遍历样本量n，要求二项累计概率接近目标置信水平（误差1%容限）筛选判据c
why_success: 穷举加误差容限实现简单可靠，得到的数对可用二项分布表直接验证
reuse: 人为规定误差为1%，由此遍历n值，若存在c0满足对应不等式，则(n,c0)数对即为抽样方案（5.1.6概括）
source: 2024国赛B|基于多阶段模拟仿真的生产决策问题|B195
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-433

```yaml
problem_type: 优化
situation: 0-1编码,蚁群算法,信息素,策略元组
method: 把决策策略编码为0-1元组作为蚂蚁路径，以利润为目标函数，用信息素正反馈与启发式信息引导搜索更优路径
why_success: 将离散决策空间映射为算法可操作的编码结构，同一框架可复用并加强随机模拟的搜索效率
reuse: 我们将每个策略用一个四元组result=[xi.x2,x3,x4]表示，其中：X1：是否检测零件1（0表示不检测，1表示检测）
source: 2024国赛B|基于蚁群算法与遗传算法优化的蒙特卡洛模拟在生产决策优化中的应用研究|B196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-434

```yaml
problem_type: 优化
situation: 遗传算法,精英策略,单点交叉,并行计算
method: 16位二进制染色体编码+单点交叉+位翻转变异+精英保留+并行适应度评估，适应度取个体决策的利润
why_success: 精英策略防止高适应度解在随机遗传操作中丢失，保证收敛性；并行评估加速大种群迭代
reuse: 在遗传算法的实施过程中，为了确保在遗传变异过程中不遗先具有优良特性的个体，我们采纳了精英策略。该策略的实施，确保了在算法送代过程中，表现最为优异的个体能够得到保留，并顺利传递至下一代
source: 2024国赛B|基于蚁群算法与遗传算法优化的蒙特卡洛模拟在生产决策优化中的应用研究|B196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-435

```yaml
problem_type: 优化
situation: 建模前需量化耕地资源分布
method: 对1201亩34地块按平旱地/梯田/山坡地/水浇地及大棚做占比统计
why_success: 把题目背景转化为结构化数据描述,为面积类约束提供常数依据
reuse: 该乡村现有路天耕地总面积为1201亩，分布在34个地块中，涵盖平早地、梯田、山坡地和水浇地四种类型。
source: 2024国赛C|基于差分遗传算法的农作物种植策略优化|C038
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-436

```yaml
problem_type: 优化
situation: 滞销有两种处理方式
method: 按浪费/半价两种情形分别建目标函数并求解
why_success: 忠实反映题目两种情形,结果对比有说服力
reuse: 根据经济学中总利润=总收入-总支出考惠到滞销部分有两种处理方式，则需要将目标函数分情况讨论
source: 2024国赛C|基于优化算法的农作物最优种植模型|C063
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-437

```yaml
problem_type: 评价
situation: 不确定环境下的方案选择
method: 构建益损值矩阵,分别用乐观/期望/悲观准则选方案
why_success: 多准则覆盖不同风险偏好,结论稳健
reuse: 分别采用最大期望准则、乐观准则，悲观准则三种准则对最优方案进行选取
source: 2024国赛C|基于优化算法的农作物最优种植模型|C063
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-438

```yaml
problem_type: 优化
situation: 权衡求解质量与求解速度
method: 求解器与贪心算法双解法并行求解并对比
why_success: 求解器结果更优但慢，贪心快但可能次优，两者对照覆盖不同需求
reuse: 这两种求解方法各有优缺点，求解器求解结果更优，但求解慢，而贪心算法则相反，根据具体需求选择方法
source: 2024国赛C|基于随机优化的农作物种植策略模型|C094
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-439

```yaml
problem_type: 优化
situation: 决策变量,染色体编码,遗传算法
method: 以某年某耕地某季某作物的种植面积为决策变量，染色体个体代表种植方案
why_success: 决策变量与染色体编码一一对应，算法实现清晰
reuse: 将该问题的候选解集用染色体表示，每一个染色体个体能代表种植方案，即每年每季每块耕地所种农作物的面积。
source: 2024国赛C|基于遗传算法的最优种植策略|C234
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-440

```yaml
problem_type: 优化
situation: 模拟数据,方案对比,利润变化
method: 问题三用模拟数据与问题一、二结果对比，分析利润变化原因
why_success: 用跨问对比说明新引入因素对结果的实际影响
reuse: 问题三的年利润相对于问题二减小，这是由于供需关系，者代性导致买方可能选择更低价的农产品
source: 2024国赛C|基于遗传算法的最优种植策略|C234
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-441

```yaml
problem_type: 误差维度扩展的命中概率优化
situation: 深度方向新增单边截尾正态定位误差
method: 利用误差独立性沿用水平最优方案，深度维再按d与实际深度最小值相对位置分5情形，用条件概率对深度密度积分得分段函数，数值粗搜+细搜求最优d
why_success: 逐层扩展误差维度复用前问结构，避免整体重建模
reuse: 根据定深引信引爆深度d与潜庭中心实际深度最小值7的相对位置可建立5种情形：先以情形5为例进行具体说明...依次得出其余4种情形命中概率表达式
source: 2024国赛D|反潜航空深弹命中概率的优化问题|2024_D_D033
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-442

```yaml
problem_type: 统计
situation: 24小时流量需要客观划分时段
method: K-means/DBSCAN/GMM三算法聚类并轮廓系数选优
why_success: 聚类从数据内在结构划分时段，比人工定界客观
reuse: 分别采用K-means聚类，DBSCAN和高斯混合模型（GMM）三种聚类算法对交通量进行时段划分
source: 2024国赛E|交通流量管控|E010
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-443

```yaml
problem_type: 预测
situation: 分时段分相位流量估计
method: 用XGBoost回归估计各相位交通量并报告MSE/R²
why_success: 梯度提升树捕捉非线性关系且带正则防过拟合
reuse: 基于极限梯度提升树算法（XGBoost）对经中路-纬中路交叉口各个相位的交通量进行估计，预测结果误差较小
source: 2024国赛E|交通流量管控|E010
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-444

```yaml
problem_type: 评价
situation: 停车位需求估算
method: 巡游车辆总数除以周转率折算停车位需求
why_success: 周转率把时长转化为车位数，简单可解释
reuse: 总停车位需求：假期期间需要的停车位数量为巡游车辆总数除以停车位的周转率
source: 2024国赛E|交通流量管控|E010
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-445

```yaml
problem_type: 统计
situation: 需估算临时停车位数量
method: 以泊松分布刻画停车需求,λ=平均巡游车辆数×0.2(发改委0.1-0.3泊位系数),取泊松分布95%分位点(PPF)作为需求上界
why_success: 随机需求用分布描述比点估计更稳健,95%分位点直接给出"够用概率95%"的泊位数
reuse: 使用松柏分布最终预计五一期间每日需临时增加约1287个停车位。
source: 2024国赛E|基于多目标优化的交通管理评估分析|E061
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-446

```yaml
problem_type: 优化
situation: 信号灯配时需随车流动态调整
method: 以车流量矩阵为状态、绿灯配时方案为动作、通行效率为奖励构建MDP,用DQN(卷积特征提取+经验回放+目标网络)逼近Q值函数求最优策略
why_success: 强化学习可处理状态-动作空间较大的动态决策,训练后按Q值最大化输出每个时段的配时
reuse: 在训练完成后，策略元（S）可以用于生成红绿灯配时策略，对于每个交叉口和每个时段，信号灯配时gi根据Q值最大化的动作a来确定。
source: 2024国赛E|基于多目标优化的交通管理评估分析|E061
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-447

```yaml
problem_type: 评价
situation: 管控效果评价
method: 选取流量密度/绕行车辆/通行方向三个可量化指标综合评价
why_success: 多指标互补,从三个维度交叉验证管控成效
reuse: 需选择评价指标：车流量、绕行车辆和通行方向，比较管控措施前后这些指标的变化
source: 2024国赛E|基于Python语言的交通流量管控与预测分析|E218
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-448

```yaml
problem_type: 统计
situation: 巡游车辆识别
method: 行驶路径+速度阈值+出现频率多条件组合识别
why_success: 单条件误判率高,多条件交叉筛选更可靠
reuse: 根据车辆的行驶轨迹数据，识别出反复绕行且行驶速度低于某一阅值（例如低于20km/h），则判定为超游车辆
source: 2024国赛E|基于Python语言的交通流量管控与预测分析|E218
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-449

```yaml
problem_type: 优化
situation: 目标函数无解析表达式、无梯度信息
method: 多起点变步长搜索（全局随机采样+变步长坐标搜索），并用粒子群交叉验证
why_success: 函数值需仿真得到，梯度类算法不适用，多起点+自适应步长平衡全局与局部搜索
reuse: 由于本问题的目标函数有效遮蔽时长没有解析表达式，其函数值需要通过模拟仿真才能得到，这导致它的梯度信息难以计算，传统的梯度下降等优化算法不再适用
source: 2025国赛A|多情形下无人机烟幕遮蔽策略的建模与优化研究|A196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-450

```yaml
problem_type: 优化
situation: 问题五45维大规模组合优化
method: 分层优化：整数线性规划任务分配（分支定界）+三个独立子问题分别优化+有效区间取交集
why_success: 维度太高无法直接求解，先定分配再优化参数使问题可解
reuse: 先分配任务再优化参数，求解时，先对任务分配进行了说明，之后把问题分成了三个子问题
source: 2025国赛A|多情形下无人机烟幕遮蔽策略的建模与优化研究|A196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-451

```yaml
problem_type: 机理
situation: 极值点提取,样条插值,相邻波谷,3σ剔除,统计分析
method: 用滑动窗口样条拟合反射率随波数的变化取出极值点，用相邻两波谷波数计算外延层厚度得到多个厚度值，再按3σ法则剔除差距较大的可疑值后进行统计分析
why_success: 样条抑制噪声且给出可求导表达式，多组厚度加统计处理避免单点误差
reuse: 用滑动窗口样条拟合碳化硅的反射率随波数的变化便于取出极值点，对所有取出的波谷按照顺序，用相邻两波谷频数来计算外延层厚度，得到多个外延层厚度，利用3σ原则剔除差距较大可疑值之后对其进行统计分析。
source: 2025国赛B|红外干涉法测量外延层厚度的建模分析|B060
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-452

```yaml
problem_type: 优化
situation: 非线性最小二乘,网格搜索,高斯牛顿法,变量对数化
method: 采用网格搜索设定参数初值后使用高斯-牛顿法精细优化，并将掺杂浓度转换为log10(N)形式进行优化以提高数值稳定性与收敛效率
why_success: 对数变换改善参数尺度，网格搜索多初值避免局部极值
reuse: 为了提高算法的数值稳定性与收敛效率，我们将掺杂浓度参数转换为其对数形式log10(N)进行优化（原文：为了提高算法的效值稳定性与收敏效幸，我们将接杂浓度参转换为其对放形式log信（N）进行优化）
source: 2025国赛B|红外干涉法测量外延层厚度的建模分析|B060
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-453

```yaml
problem_type: 光谱反问题的厚度反演
situation: 由实测反射光谱反演外延层厚度并评估可靠性
method: 等间距重采样+物理区裁剪+AsLS去基线+S-G平滑去噪；滑窗FFT提取主频与SNR自动选带得厚度初值；双角联合加权鲁棒最小二乘（共享d、A、B，含波数刻度与角度校准量）精拟合；多维可靠性检验
why_success: 两步法保证收敛，联合拟合保证厚度物理唯一性，检验矩阵保证可信度
reuse: 我们构造了带有物理先验正则的加权鲁棒最小二乘目标
source: 2025国赛B|碳化硅外延层厚度的双光束和多光束干涉法测量研究|2025_B_B157
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-454

```yaml
problem_type: 统计
situation: 纵向重复测量数据建模
method: 线性混合效应模型（随机截距+随机斜率）处理组内相关
why_success: 固定效应给群体趋势，随机效应吸收个体异质性
reuse: 采用线性混合效应模型框架处理纵向数据的组内相关性，通过随机截距和随机斜率刻画个体异质性
source: 2025国赛C|基于混合效应模型的NIPT时点优化与胎儿异常判定|C023
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-455

```yaml
problem_type: 预测
situation: 需预测随孕周变化的动态达标概率并处理删失样本
method: 引入生存分析框架:事件定义为浓度首达4%,时间离散化取整,右删失样本编码事件状态;MLP编码静态特征,LSTM编码时序,DeepHit生存头输出达标概率曲线,复合损失含似然项与排序项
why_success: Cox依赖比例风险假设,DeepHit无需该假设且能利用删失样本的风险排序信息,提升预测性能
reuse: DeepHit无需依赖比例风险假设，适合处理存在册失数据的时点预测间题
source: 2025国赛C|基于统计建模与元学习的NIPT检测决策优化与异常识别|C132
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-456

```yaml
problem_type: 统计
situation: 女胎数据少且不平衡,需识别单发与复合染色体异常
method: 堆叠集成元学习:LightGBM+Optuna构建T13/T18/T21专项模型与交互影响模型,输出概率作为元特征,与关键原始特征融合后由元模型做7类分类,再以Z值逻辑修正层兜底
why_success: 专项模型各司其职,元模型学习交互,逻辑修正层保障复合异常召回,三层设计兼顾精度与鲁棒性
reuse: 采用基于LightGBM和Optuna的堆叠集成模型框架以充分利用数据
source: 2025国赛C|基于统计建模与元学习的NIPT检测决策优化与异常识别|C132
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-457

```yaml
problem_type: 机理
situation: 复杂漫延过程
method: 按封闭/断流两个维度拆成三种子模型再综合成统一模型
why_success: 有限子情形覆盖完整,综合后处理任意巷道结构
reuse: 本问建立三种特殊突水水流在巷道的流动浸延模型。分别为没有封闭，没有断流模型：封闭，没有断流模型：没有封闭：断流模型。将三种特殊的模型综合在一起形成平面突水水流漫延模型
source: 2025国赛D|矿井突水水流漫延模型与逃生方案问题|D037
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-458

```yaml
problem_type: 图论
situation: 动态网络最短路
method: 时间离散化把动态网络问题转化为静态问题复用Dijkstra
why_success: 经典算法直接可用,实现简单结论可靠
reuse: 把每个时间步看成一个集合，在集合内网络状态不变，便将动态网络问题转化为静态问题，从而达到Dijkstra算法实现。
source: 2025国赛D|矿井突水水流漫延模型与逃生方案问题|D037
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## SD-459

```yaml
problem_type: 预测
situation: 小样本回归预测成绩
method: 多元线性回归与随机森林双模型对比，最终选线性回归
why_success: 随机森林小样本下不稳定、外推误差大，线性回归误差仅0.002米
reuse: 随后对两种模型进行误差分析，得到多元线性回归预测结果最优，为1.077米
source: 2025国赛E|基于姿态识别的AI辅助智能体测研究|E030
confidence: 中
source_quality: 中
memory_type: paper_extract
```


---

## SD-460（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电路
method: ABCD/耦合系数闭式效率公式
why_success: η=1/(1+2/(k²Q₁²)+Q₂/(k²Q₁)+(k²+Q₁⁻²)/(k²Q₁Q₂))，复算Q1首组56.196%(官方56.20%)、Q3最大92.77%完全一致
result: Q1 56.196% 与官方一致（verified: true）
reuse: 推荐（谐振/互感/传输效率类机理题）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-461（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电磁
method: Neumann 双重积分严格算互感 M
why_success: 用 scipy.dblquad 对 M=(μ₀N²/4π)∮∮cosφ/|r₁−r₂| 严格积分，轴向M(h)与附件实测10组误差<3%
result: 无需拟合即可预测任意间距/偏移互感（verified: true）
reuse: 推荐（互感/线圈/电磁场计算类）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-462（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（工程交付）
method: pandoc 转 docx 前把 figure 渲染为 PNG
why_success: Word 无法内嵌 LaTeX 生成的 PDF 图，须用 PyMuPDF 渲染 PNG 再让 pandoc 引用
result: docx 完整保留图表（verified: true）
reuse: 强制内置（docx 路线图表交付）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-463（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（中文出图）
method: matplotlib 注册 simhei.ttf 解决中文图缺字
why_success: 默认 DejaVu Sans 缺 CJK 字形，注册 C:/Windows/Fonts/simhei.ttf 后中文正常
result: 中文图正常渲染（verified: true）
reuse: 强制内置（中文出图环境）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-464（2021华数杯B PSR验证场）

```yaml
success_id: ?
problem_type: 优化/随机需求
method: 报童期望利润模型 + 临界分位
why_success: 把随机需求下的订货量决策转成可解析的报童模型，临界分位给出闭式解
result: CR≈0.61~0.67；高变异货(HW7/9/10)用经验分布求期望而非正态近似
reuse: 推荐（随机需求/库存/批量决策类）
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## SD-465（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电路
method: ABCD/耦合系数闭式效率公式
why_success: η=1/(1+2/(k²Q₁²)+Q₂/(k²Q₁)+(k²+Q₁⁻²)/(k²Q₁Q₂))，复算Q1首组56.196%(官方56.20%)、Q3最大92.77%完全一致
result: Q1 56.196% 与官方一致（verified: true）
reuse: 推荐（谐振/互感/传输效率类机理题）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-466（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电磁
method: Neumann 双重积分严格算互感 M
why_success: 用 scipy.dblquad 对 M=(μ₀N²/4π)∮∮cosφ/|r₁−r₂| 严格积分，轴向M(h)与附件实测10组误差<3%
result: 无需拟合即可预测任意间距/偏移互感（verified: true）
reuse: 推荐（互感/线圈/电磁场计算类）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-467（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（工程交付）
method: pandoc 转 docx 前把 figure 渲染为 PNG
why_success: Word 无法内嵌 LaTeX 生成的 PDF 图，须用 PyMuPDF 渲染 PNG 再让 pandoc 引用
result: docx 完整保留图表（verified: true）
reuse: 强制内置（docx 路线图表交付）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-468（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（中文出图）
method: matplotlib 注册 simhei.ttf 解决中文图缺字
why_success: 默认 DejaVu Sans 缺 CJK 字形，注册 C:/Windows/Fonts/simhei.ttf 后中文正常
result: 中文图正常渲染（verified: true）
reuse: 强制内置（中文出图环境）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-469（2021华数杯B PSR验证场）

```yaml
success_id: ?
problem_type: 优化/随机需求
method: 报童期望利润模型 + 临界分位
why_success: 把随机需求下的订货量决策转成可解析的报童模型，临界分位给出闭式解
result: CR≈0.61~0.67；高变异货(HW7/9/10)用经验分布求期望而非正态近似
reuse: 推荐（随机需求/库存/批量决策类）
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## SD-470（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电路
method: ABCD/耦合系数闭式效率公式
why_success: η=1/(1+2/(k²Q₁²)+Q₂/(k²Q₁)+(k²+Q₁⁻²)/(k²Q₁Q₂))，复算Q1首组56.196%(官方56.20%)、Q3最大92.77%完全一致
result: Q1 56.196% 与官方一致（verified: true）
reuse: 推荐（谐振/互感/传输效率类机理题）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-471（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电磁
method: Neumann 双重积分严格算互感 M
why_success: 用 scipy.dblquad 对 M=(μ₀N²/4π)∮∮cosφ/|r₁−r₂| 严格积分，轴向M(h)与附件实测10组误差<3%
result: 无需拟合即可预测任意间距/偏移互感（verified: true）
reuse: 推荐（互感/线圈/电磁场计算类）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-472（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（工程交付）
method: pandoc 转 docx 前把 figure 渲染为 PNG
why_success: Word 无法内嵌 LaTeX 生成的 PDF 图，须用 PyMuPDF 渲染 PNG 再让 pandoc 引用
result: docx 完整保留图表（verified: true）
reuse: 强制内置（docx 路线图表交付）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-473（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（中文出图）
method: matplotlib 注册 simhei.ttf 解决中文图缺字
why_success: 默认 DejaVu Sans 缺 CJK 字形，注册 C:/Windows/Fonts/simhei.ttf 后中文正常
result: 中文图正常渲染（verified: true）
reuse: 强制内置（中文出图环境）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-474（2021华数杯B PSR验证场）

```yaml
success_id: ?
problem_type: 优化/随机需求
method: 报童期望利润模型 + 临界分位
why_success: 把随机需求下的订货量决策转成可解析的报童模型，临界分位给出闭式解
result: CR≈0.61~0.67；高变异货(HW7/9/10)用经验分布求期望而非正态近似
reuse: 推荐（随机需求/库存/批量决策类）
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```

---

## SD-475（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电路
method: ABCD/耦合系数闭式效率公式
why_success: η=1/(1+2/(k²Q₁²)+Q₂/(k²Q₁)+(k²+Q₁⁻²)/(k²Q₁Q₂))，复算Q1首组56.196%(官方56.20%)、Q3最大92.77%完全一致
result: Q1 56.196% 与官方一致（verified: true）
reuse: 推荐（谐振/互感/传输效率类机理题）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-476（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 机理/电磁
method: Neumann 双重积分严格算互感 M
why_success: 用 scipy.dblquad 对 M=(μ₀N²/4π)∮∮cosφ/|r₁−r₂| 严格积分，轴向M(h)与附件实测10组误差<3%
result: 无需拟合即可预测任意间距/偏移互感（verified: true）
reuse: 推荐（互感/线圈/电磁场计算类）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-477（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（工程交付）
method: pandoc 转 docx 前把 figure 渲染为 PNG
why_success: Word 无法内嵌 LaTeX 生成的 PDF 图，须用 PyMuPDF 渲染 PNG 再让 pandoc 引用
result: docx 完整保留图表（verified: true）
reuse: 强制内置（docx 路线图表交付）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-478（2021华数杯A PSR第二场）

```yaml
success_id: ?
problem_type: 任意（中文出图）
method: matplotlib 注册 simhei.ttf 解决中文图缺字
why_success: 默认 DejaVu Sans 缺 CJK 字形，注册 C:/Windows/Fonts/simhei.ttf 后中文正常
result: 中文图正常渲染（verified: true）
reuse: 强制内置（中文出图环境）
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
verified: True
```

---

## SD-479（2021华数杯B PSR验证场）

```yaml
success_id: ?
problem_type: 优化/随机需求
method: 报童期望利润模型 + 临界分位
why_success: 把随机需求下的订货量决策转成可解析的报童模型，临界分位给出闭式解
result: CR≈0.61~0.67；高变异货(HW7/9/10)用经验分布求期望而非正态近似
reuse: 推荐（随机需求/库存/批量决策类）
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
```
