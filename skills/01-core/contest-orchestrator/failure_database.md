---
name: failure-database
description: 数学建模竞赛失败经验库。problem-parser 输出题型时自动检索，命中即预警。每场比赛复盘后结构化追加。
---

# 失败经验库（Failure Database）

> 用法：problem-parser 输出 `problem_type` 后，检索本库 `problem_type` 匹配项，命中即预警并套用 `lesson`。
> 复盘新比赛 → 按此 schema 追加条目，形成"越比越强"的 Memory。

---

## FD-001 架构搜索空间到极限（换互补架构）

```yaml
failure_id: FD-001
problem_type: 组合优化 + 几何布图
attempt: B*-Tree + 模拟退火
failure: n300 死区率卡死 555²，多种子+多轮调参无法突破 553/548
cause: 架构搜索空间到极限（树扰动无法改变拓扑，参数微调只在同一空间打转）
signal: 多种子+多参数后结果停在固定阈值不动；文献显示别的表示方法能更紧
lesson: 换互补架构（确定性构造 skyline 突破到 545²）；文献先于架构，换架构预案来自文献
avoid: 在同一架构里耗到第三天；把"调参"当"突破"
```

## FD-002 参数口径不一致（正文/代码/附录）

```yaml
failure_id: FD-002
problem_type: 任意（论文+代码交付）
attempt: 权重 ALPHA=0.95/BETA=0.05（正文） vs 0.8/0.2（代码）
failure: 论文正文/附录/代码三处权重不一致，评审点名为"会评一票否决"硬伤
cause: 参数没集中登记，代码手和论文手各改各的，无对照
signal: 正文公式常量 ↔ 代码变量赋值对不上
lesson: parameter-registry 集中登记；参数溯源检查脚本（提取常量↔赋值比对）；改参数必须同步四处+触发重验证
avoid: 手写参数进论文；改代码不通知论文
```

## FD-003 数据一致性 / 可复现性

```yaml
failure_id: FD-003
problem_type: 任意（附件交付）
attempt: 结果汇总 JSON / 布局 CSV / 收敛图
failure: Q3 汇总 JSON 是旧值（n100 292,848 vs 论文 289,168；n300 0.1276 vs 0.0873）；图6 收敛曲线与表6 对不上；种子记录文档 vs 结果文件 seed 不一致
cause: 结果没从代码单一生成，旧缓存/手写数据混入；图和表各用各的数据源
signal: 论文表格数字回溯不到唯一结果文件；同一变量在摘要/结论/表格值不同
lesson: 结果只从代码生成 + 权威版本哈希；图/表/正文同一 JSON 数据源；交叉校验脚本（同一变量跨位置一致）；复现验证（seed/bbox/HPWL 重算）
avoid: 手写/后补结果文件；用旧缓存出图；种子记录与结果文件脱节
```

## FD-004 附录代码排版（一坨）

```yaml
failure_id: FD-004
problem_type: 论文交付
attempt: 代码直接粘贴进附录
failure: 换行丢失，代码 7772 字挤成单行 + 268 个空行，显示为"一坨"
cause: 粘贴时换行被合并，w:br 全堆末尾
signal: 单个段落文本超 2000 字且无内部换行
lesson: 附录代码按函数/类分段渲染；函数级注释做分节标题；Consolas 等宽；从源码提取而非手贴
avoid: 直接粘贴长代码；不检查换行结构
```

## FD-005 AIGC 检测事后降重

```yaml
failure_id: FD-005
problem_type: 论文写作
attempt: 写完再跑 AIGC 检测
failure: 检测率 40.73%，赛后紧急降重（砍连接词/破模板/口语化）耗时巨大
cause: 写作时用 AI 模板句（因此/表明/而非/主要源于），写完才治理
signal: AIGC 检测率 > 40%；"因此/说明/表明/故"等连接词密度高
lesson: 写作时就人话（长短句交替/口语化）；T-24h AIGC 预检标记高风险段；humanize skill 辅助
avoid: 等检测后大改；公式化过渡词堆砌
```

---

## 复盘：华数杯 2026 B 题（第一笔实战）

- **题型**：VLSI 布图规划（组合优化 + 几何），四问递进
- **突破点**：skyline 确定性底置打包突破 n300 545²（文献先行 → 架构候选池命中）；消融实验（去掉确定性打包→10.24%）证明方法有效
- **教训映射**：FD-001（架构极限）/ FD-002（参数口径）/ FD-003（数据一致性）/ FD-004（附录排版）/ FD-005（AIGC 降重）
- **可复用**：B\*-Tree+SA 是布图可靠基线；互补架构（一个管可行性、一个管线长）是突破关键；穷举+下界证明在小规模更有说服力

---

## FD-006 物理单位换算错误（μm 与 cm⁻¹ 混用）

```yaml
failure_id: FD-006
problem_type: 物理机理建模（光学/干涉/波动）
attempt: 双光束干涉模型相位公式
failure: 结果系统性偏差 30%（真 d=10μm 算出 6.9μm）
cause: d 用 μm、ν 用 cm⁻¹ 时，相位公式漏了 1e-4 单位换算（4π n d cosθ·ν 需 ×1e-4）
signal: 结果整体偏离一个常数因子；两角度结果一致但绝对值不对
lesson: 物理建模先验单位制；长度用 μm、波数用 cm⁻¹ 时相位=4πn d cosθ·ν×1e-4
avoid: 直接套公式不查单位
```

## FD-007 Sellmeier 折射率参数错误

```yaml
failure_id: FD-007
problem_type: 光学/材料建模
attempt: Sellmeier 色散公式 n²=A+Bλ²/(λ²-C²)
failure: A=3.0 导致 n≈1.75（SiC 实际应 ~2.55），厚度结果差 ~30%
cause: 折射率参数没按材料查证，随意设
signal: 合成数据自洽但偏离物理；n 明显低于材料典型值
lesson: 材料折射率必须查证（SiC≈2.55、Si≈3.42）；Sellmeier 系数校准到已知 n
avoid: 凭感觉设折射率参数
```

## FD-008 基线平滑窗口吃掉条纹

```yaml
failure_id: FD-008
problem_type: 信号处理/频谱分析
attempt: 滑动平均（窗宽 501）做基线
failure: 基线窗口（241 cm⁻¹）与条纹周期（200-700 cm⁻¹）同量级，把条纹功率吃掉
cause: 基线窗口没按条纹周期设计
signal: 振荡幅值异常小；FFT 主峰偏移
lesson: 基线用低阶多项式（deg 3）而非长窗平滑；窗口 ≫ 条纹周期
avoid: 用与信号周期相近的窗口做基线
```

## FD-009 多光束 Airy 拟合撞网格边界

```yaml
failure_id: FD-009
problem_type: 多光束/谐振腔拟合
attempt: Airy 公式网格搜索拟合 d
failure: 结果卡在网格上界（10.0），不收敛
cause: Airy 模型参数耦合（R2 与 d），网格搜索局部极小/边界
signal: 最优解落在扫描区间端点
lesson: 非线性多参数拟合用粗-细多尺度 + 初值约束；先 FFT 定 d 数量级再拟合
avoid: 单层网格搜索多参数耦合模型
```

## FD-010 网络受限无法核实外部答案

```yaml
failure_id: FD-010
problem_type: 任意（信息获取）
attempt: 网搜文献/官方答案
failure: 沙箱无外网，只有 WebSearch 可用，WebFetch/下载全失败
cause: 环境网络隔离
lesson: 数值结果必须自洽（多方法互证+双角度一致性），不依赖外部对答案
avoid: 把唯一答案押在外部参考上
```

---

## FD-11

```yaml
problem_type: 组合优化
method: B*-Tree+SA
failure: n300卡555²
cause: 架构到极限
lesson: 换互补架构
signal: 调参结果不动
failure_id: FD-11
```

---

## FD-12

```yaml
problem_type: 数据交付
method: 汇总JSON
failure: 旧值混入
cause: 没单一数据源
lesson: 结果只从代码生成
signal: 表格对不上
failure_id: FD-12
```

---

## FD-13

```yaml
failure_id: FD-13
problem_type: 华数杯B·布图
method: 问题二用随机 B*-Tree 树直接起步做固定轮廓(γ=15%) HPWL 优化
failure: 随机树在固定轮廓下可行率≈0%，SA 怎么迭代都塞不进轮廓，搜索完全卡死
cause: 随机 B*-Tree 膨胀率 1.2~1.5×，远超允许轮廓 L=√(1.15·S0)；SA 局部扰动只能微调，无法把整棵树全局收缩回轮廓——这是'搜索器能力瓶颈'，不是目标函数问题
signal: 初始解 pack 后 W×H 明显超出 L；扰动后轮廓基本不变
lesson: 带硬轮廓约束的问题，不能从随机解起步，必须先有一个可行解再在可行域内优化
avoid: 用两阶段级联：先用问题一（无轮廓约束）解出可行树，作为问题二 init_root
```

---

## FD-14

```yaml
failure_id: FD-14
problem_type: 华数杯B·布图
method: 越界惩罚权重 DELTA 拍脑袋试值
failure: DELTA=20 太弱，布局贴着边界滑出去拉不回来（越界仍被接受）；DELTA=100 太强，随机树在可行域内也被过度惩罚，收敛失败
cause: 惩罚权重影响'接受越界解的代价'，过弱惩罚失效、过强让可行域内搜索也变僵硬，需要折中
signal: DELTA=20 时结果频繁越界；DELTA=100 时可行解也找不到
lesson: 惩罚类参数不能拍脑袋，必须做 2~3 档对照实验取平衡值
avoid: 做 DELTA∈{20,50,100} 小实验，选既能拉回越界又不过度压制的 50；并把实验过程写入运行说明
```

---

## FD-15

```yaml
failure_id: FD-15
problem_type: 华数杯B·布图
method: 问题一目标权重初始设 ALPHA=0.8, BETA=0.2
failure: 代码里权重与论文摘要'面积项和长宽比惩罚项权重 0.95 和 0.05'不一致，若评委对照会判代码与论文不符
cause: 权重是'论文声称值'的一部分，编程手只按直觉设值，没与建模手论文口径对齐
signal: 摘要里写明 0.95/0.05，代码里却是 0.8/0.2——两处口径漂移
lesson: 论文/摘要里写明的模型参数必须与代码逐字一致，这是'代码可复现论文'的硬要求
avoid: 交付前把论文摘要、模型部分的关键数值与代码常量逐一核对；用 grep 抽取 ALPHA/BETA 等常量对比
```

---

## FD-16

```yaml
failure_id: FD-16
problem_type: 华数杯B·布图
method: 支撑材料直接打包全部工作目录
failure: 夹带了 __pycache__、探索脚本(q1_research等)、Q2存档、附录文件，与最终论文结果不符，有被取消评奖资格风险
cause: 工作目录是探索过程产物，直接整包当支撑材料，没做'最终交付'过滤
signal: 压缩包文件数116，明显多于应交付的核心代码+数据+图
lesson: 支撑材料必须'只留能支撑论文结果的必要文件'，探索脚本/缓存/存档都不该进交付包
avoid: 打包前按规范清单过滤：只留核心求解代码+定稿数据+四问汇总+论文图+运行记录；删 __pycache__
```

---

## FD-17

```yaml
failure_id: FD-17
problem_type: 华数杯B·布图
method: 种子记录文件里写'种子42/43/44'，但结果文件实际用 1003/1005
failure: 种子记录与 Q2/Q3 结果文件的最优种子对不上，评委按记录复现会对不上论文数字
cause: 种子记录是后补的、没与实际运行结果文件对齐；多 seed 择优时最优 seed 不等于基础 seed
signal: 结果文件 seed=1003/1005，种子记录却写 42/43/44
lesson: 复现记录必须'以结果文件实际记录为准'，不能拍脑袋写
avoid: 种子记录改成'以 03_数据/结果汇总/*.json 中记录的最优种子为准'，并明确多种子择优口径
```

---

## FD-18

```yaml
failure_id: FD-18
problem_type: 华数杯B·布图
method: 脚本 print 含下标字符 S₀、✓ 等非 GBK 字符
failure: Windows 中文控制台(GBK)直接运行时 UnicodeEncodeError 崩溃（q4_solve.py 等）
cause: print 输出含 GBK 无法编码的 Unicode 字符，Windows 默认 stdout 编码不支持
signal: Python 报 UnicodeEncodeError: 'gbk' codec can't encode character
lesson: Windows 环境代码要兼容 GBK 控制台，尤其含下标/特殊符号时
avoid: 脚本头部加 sys.stdout.reconfigure(encoding='utf-8') 或 TextIOWrapper 重定向；交付前在 Windows 实测跑一遍
```

## WRITER-001 输出格式未确认（生成 Markdown 而非 Word）

```yaml
failure_id: WRITER-001
problem_type: 任意（论文/报告交付）
attempt: writer 默认生成 Markdown
failure: 用户要 Word(.docx+OMML)，给的是 Markdown；公式不是 OMML，Word 无法编辑
cause: writer 没进 Output Contract，未确认输出格式就默认猜
signal: 用户问"怎么是 md 不是 docx"
lesson: 写作前必须确认格式（Word/LaTeX/Markdown/PDF）；国内数模默认 Word+OMML；公式必须真 OMML
avoid: 进 writer 前查 core/output_contract.md
```

---

## FD-19（公开经验库·Kimi）

```yaml
failure_id: FD-19
problem_type: 优化
domain: 新能源/太阳能
method: 直接高维全局优化
failure: 计算量过大，无法在竞赛时间内求解
cause: 决策变量包含所有定日镜位置、尺寸、高度，维度极高
signal: 程序运行超时或内存溢出
lesson: 对高维优化问题应先进行降维或固定部分变量
avoid: 
source: 定日镜场优化设计模型——CUMCM 2023 A题国一论文(凌国明,中山大学)|https://blog.csdn.net/weixin_62127011/article/details/149843974|2023
confidence: 高
```

---

## FD-20（公开经验库·Kimi）

```yaml
failure_id: FD-20
problem_type: 优化
domain: 新能源/太阳能
method: 将入射太阳光视为严格平行光（无锥角）
failure: 截断效率计算偏差较大
cause: 实际太阳光有一定锥角，反射光线为锥形光束
signal: 与SOLTRACE仿真软件对比出现系统误差
lesson: 在精度要求高的光学问题中，应考虑光线锥角效应
avoid: 
source: 定日镜场优化设计模型——CUMCM 2023 A题国一论文(凌国明,中山大学)|https://blog.csdn.net/weixin_62127011/article/details/149843974|2023
confidence: 高
```

---

## FD-21（公开经验库·Kimi）

```yaml
failure_id: FD-21
problem_type: 决策/博弈
domain: 游戏策略/资源管理
method: 正向贪心策略(每天选择当前最优行动)
failure: 在复杂地图中无法得到全局最优解
cause: 贪心策略缺乏全局视野，可能在矿山停留过久导致超时
signal: 与动态规划结果对比，剩余资金明显偏低
lesson: 多阶段决策问题应考虑逆向动态规划或全局优化
avoid: 
source: 穿越沙漠游戏最佳策略模型的研究与构建——CUMCM 2020 B题国一论文|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## FD-22（公开经验库·Kimi）

```yaml
failure_id: FD-22
problem_type: 决策/博弈
domain: 游戏策略/资源管理
method: 忽略沙暴日挖矿的可能性
failure: 遗漏部分可行策略
cause: 沙暴日虽然必须停留，但可以挖矿获得收益
signal: 部分优秀论文提到了沙暴日挖矿策略
lesson: 仔细阅读题目所有规则，不要先入为主排除可能性
avoid: 
source: 穿越沙漠游戏最佳策略模型的研究与构建——CUMCM 2020 B题国一论文|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## FD-23（公开经验库·Kimi）

```yaml
failure_id: FD-23
problem_type: 预测+优化
domain: 材料科学/非织造材料
method: 直接用多元线性回归拟合工艺参数与产品性能
failure: 拟合精度不足，R²较低
cause: 实际关系为非线性，线性模型无法捕捉
signal: 残差分析显示明显非线性趋势
lesson: 建模前应先通过可视化判断关系类型，再选择合适模型
avoid: 
source: 插层熔喷非织造材料性能的分析与研究——2022华数杯C题获奖论文|https://blog.csdn.net/qq_63438888/article/details/126426589|2022
confidence: 高
```

---

## FD-24（公开经验库·Kimi）

```yaml
failure_id: FD-24
problem_type: 预测+优化
domain: 材料科学/非织造材料
method: 仅优化过滤效率忽略过滤阻力
failure: 得到的产品虽然过滤效率高但阻力过大，不实用
cause: 实际产品需同时满足多个性能指标
signal: 与工业实际需求对比发现偏差
lesson: 多指标优化问题应建立多目标规划，避免单一指标极端化
avoid: 
source: 插层熔喷非织造材料性能的分析与研究——2022华数杯C题获奖论文|https://blog.csdn.net/qq_63438888/article/details/126426589|2022
confidence: 高
```

---

## FD-25（公开经验库·Kimi）

```yaml
failure_id: FD-25
problem_type: 预测+决策
domain: 金融/投资组合
method: 仅用历史均值预测未来价格
failure: 无法捕捉价格的趋势性和波动性聚集
cause: 金融时间序列具有自相关性和异方差性
signal: 预测误差大，方向判断准确率低
lesson: 金融预测应使用时序模型(LSTM、ARIMA-GARCH)而非简单统计量
avoid: 
source: All That Glitters Is Not Gold: Trading Strategies——MCM 2022 C题O奖论文(北京理工大学)|https://xgb.bit.edu.cn/xgdt/rdxw/b7fad809dbfa46da8a3306a273e300fa.htm|2022
confidence: 高
```

---

## FD-26（公开经验库·Kimi）

```yaml
failure_id: FD-26
problem_type: 预测+决策
domain: 金融/投资组合
method: 忽略交易成本进行优化
failure: 高频交易策略在实际中收益为负
cause: 黄金2%和比特币1%的交易成本会显著侵蚀利润
signal: 回测结果与模拟交易结果差异巨大
lesson: 任何涉及交易的优化模型必须将交易成本作为硬约束纳入
avoid: 
source: All That Glitters Is Not Gold: Trading Strategies——MCM 2022 C题O奖论文(北京理工大学)|https://xgb.bit.edu.cn/xgdt/rdxw/b7fad809dbfa46da8a3306a273e300fa.htm|2022
confidence: 高
```

---

## FD-27（公开经验库·Kimi）

```yaml
failure_id: FD-27
problem_type: 优化
domain: 射电天文/光学
method: 直接三维曲面优化不简化
failure: 计算复杂度过高，无法在竞赛时间内完成
cause: 500米口径、数千块反射面板的全三维优化维度极高
signal: 程序运行缓慢，收敛困难
lesson: 大型工程问题应寻找合理的简化方法(如对称性降维)
avoid: 
source: FAST主动反射面的形状调节——CUMCM 2021 A题国一论文(武汉大学肖宇曦/李逍迪/刘禹希团队)|https://m.cyol.com/gb/articles/2021-11/25/content_dw3zxI05e.html|2021
confidence: 高
```

---

## FD-28（公开经验库·Kimi）

```yaml
failure_id: FD-28
problem_type: 优化
domain: 射电天文/光学
method: 假设所有促动器可独立任意调节
failure: 得到的调节方案不可行
cause: 实际下拉索长度固定，促动器调节范围受限
signal: 
lesson: 建模时必须考虑实际工程约束，不能仅追求数学最优
avoid: 
source: FAST主动反射面的形状调节——CUMCM 2021 A题国一论文(武汉大学肖宇曦/李逍迪/刘禹希团队)|https://m.cyol.com/gb/articles/2021-11/25/content_dw3zxI05e.html|2021
confidence: 高
```

---

## FD-29（公开经验库·Kimi）

```yaml
failure_id: FD-29
problem_type: 组合优化与不确定性决策
domain: 农业经济/种植规划
method: 初期尝试用简单贪心算法按单季利润排序分配土地
failure: 无法满足跨季轮作与重茬约束，多季方案不可行
cause: 贪心算法缺乏全局视野，轮作约束涉及时间耦合，局部最优导致全局冲突
signal: 后季无法种植任何合法作物，大量土地闲置
lesson: 含时间耦合约束的农业规划必须使用多周期优化模型（MILP），不能逐季独立决策
avoid: 
source: 2024年高教社杯全国大学生数学建模竞赛C题：农作物的种植策略|https://cloud.tencent.com/developer/article/2486153|2024
confidence: 高
```

---

## FD-30（公开经验库·Kimi）

```yaml
failure_id: FD-30
problem_type: 物理机理建模与参数优化
domain: 海洋能源/波浪能转换
method: 初期尝试用单自由度模型（仅浮子垂荡）估算输出功率
failure: 最优功率与两自由度模型结果偏差巨大，且无法解释PTO能量提取机制
cause: 单自由度模型将振子与浮子视为刚性连接，忽略了振子相对运动是PTO做功的核心来源
signal: 计算功率数量级与文献报道的波浪能装置不符，且功率随阻尼系数单调下降无峰值
lesson: 含PTO的波浪能装置必须建立浮子-振子相对运动模型，至少两自由度才能刻画能量提取本质
avoid: 
source: 2022年高教社杯全国大学生数学建模竞赛A题：波浪能最大输出功率设计|https://blog.csdn.net/weixin_47315122/article/details/163511311|2022
confidence: 高
```

---

## FD-31（公开经验库·Kimi）

```yaml
failure_id: FD-31
problem_type: 供应商评价与两阶段供应链优化
domain: 生产物流/供应链管理
method: 初期尝试用简单平均损耗率估计转运成本，未考虑转运商个体差异
failure: 总损耗预测与实际偏差大，部分周次接收量不足导致库存低于安全线
cause: 8家转运商损耗率差异显著（有的长期低损耗，有的波动大），简单平均掩盖了个体风险
signal: 模拟中发现某些周次即使总运力充足，实际接收量仍低于两周库存需求
lesson: 供应链优化中必须基于个体历史表现而非总体统计建模，转运商选择应作为独立决策变量纳入优化模型
avoid: 
source: 2021年高教社杯全国大学生数学建模竞赛C题：生产企业原材料的订购与运输|https://blog.csdn.net/peiye500238/article/details/150857323|2021
confidence: 高
```

---

## FD-32（公开经验库·Kimi）

```yaml
failure_id: FD-32
problem_type: 几何定位与编队控制
domain: 无人机/信号处理
method: 初期尝试用神经网络或强化学习做端到端定位
failure: 模型训练困难，定位精度低且不稳定
cause: 本题数据量极小（仅10架无人机），无大数据支撑深度学习；且问题本质是几何关系，非数据驱动模式识别
signal: 训练损失震荡不收敛，测试定位误差远超几何方法
lesson: 几何定位问题应优先利用几何定理与解析方法，而非盲目套用机器学习；数据量小、机理明确的场景适合传统数学建模
avoid: 
source: 2022年高教社杯全国大学生数学建模竞赛B题：无人机遂行编队飞行中的纯方位无源定位|https://blog.csdn.net/weixin_43970743/article/details/161582620|2022
confidence: 高
```

---

## FD-33（公开经验库·Kimi）

```yaml
failure_id: FD-33
problem_type: 成分分析与分类鉴别
domain: 考古学/化学计量学
method: 初期尝试用单一K-Means对所有样本直接聚类，未区分高钾/铅钡
failure: 聚类结果与已知分类严重不符，铅钡与高钾样本被混为一类
cause: 两类玻璃在成分空间上距离较远，直接全局聚类会忽略已知的类型边界，导致聚类中心落在两类之间
signal: 聚类结果中已知高钾样本与铅钡样本被分配到同一簇
lesson: 有先验类别信息时，应先按已知类别分层，再在子类内部进行聚类或亚类划分；全局无监督聚类可能破坏已有专业知识
avoid: 
source: 2022年高教社杯全国大学生数学建模竞赛C题：古代玻璃制品的成分分析与鉴别|https://developer.aliyun.com/article/1578548|2022
confidence: 高
```

---

## FD-34（公开经验库·Kimi）

```yaml
failure_id: FD-34
problem_type: 运动轨迹建模与碰撞检测优化
domain: 民俗文化/几何动力学
method: 直接用等弧长假设递推龙身位置（认为每节对应相同角度差）
failure: 龙身各把手位置严重偏离螺线，后续节段出现明显抖动
cause: 龙头与龙身长度不同（3.41m vs 2.2m），等弧长假设未考虑长度差异导致角度递推错误
signal: 龙尾轨迹出现非物理振荡，与螺线形状明显不符
lesson: 必须根据每节板凳的实际长度沿螺线反向递推角度，龙头与龙身需采用不同的长度参数分别计算
avoid: 
source: 2024年高教社杯全国大学生数学建模竞赛A题：'板凳龙'闹元宵|https://blog.csdn.net/weixin_43292788/article/details/145744176|2024
confidence: 高
```

---

## FD-35（公开经验库·Kimi）

```yaml
failure_id: FD-35
problem_type: 运动轨迹建模与碰撞检测优化
domain: 民俗文化/几何动力学
method: 忽略板凳宽度方向的几何碰撞，仅检测把手点距离
failure: 未检测到部分板凳侧面碰撞，终止时刻偏晚
cause: 板凳有30cm宽度，非相邻节段可能在把手距离尚安全时，板凳侧面已发生干涉
signal: 可视化中发现板凳矩形区域存在重叠但把手间距仍大于阈值
lesson: 碰撞检测必须考虑板凳的矩形几何形状，可采用线段距离或矩形分离轴定理(SAT)进行精确检测
avoid: 
source: 2024年高教社杯全国大学生数学建模竞赛A题：'板凳龙'闹元宵|https://blog.csdn.net/weixin_43292788/article/details/145744176|2024
confidence: 高
```

---

## FD-36（公开经验库·Kimi）

```yaml
failure_id: FD-36
problem_type: 光学效率优化与太阳能集热
domain: 新能源/光学工程
method: 初期采用解析几何法直接计算阴影遮挡效率
failure: 大规模镜场中相邻定日镜关系复杂，解析公式推导困难且误差大
cause: 阴影遮挡涉及动态变化的太阳位置与密集布置的镜面，解析法难以处理任意布局下的遮挡关系
signal: 计算结果与专业仿真软件SolTrace偏差超过5%
lesson: 复杂几何光学问题应优先采用蒙特卡洛光线追踪等数值方法，解析法仅适用于高度简化的规则布局
avoid: 
source: 2023年高教社杯全国大学生数学建模竞赛A题：定日镜场的优化设计|https://pdf.hanspub.org/csa_1544012.pdf|2023
confidence: 高
```

---

## FD-37（公开经验库·Kimi）

```yaml
failure_id: FD-37
problem_type: 质量检测与多阶段生产决策优化
domain: 工业工程/质量管理
method: 问题1直接用样本比例与标称值简单比较，忽略信度要求
failure: 样本量过小导致两类错误概率过高，企业频繁错误拒收或接收
cause: 未建立严格的假设检验框架，缺乏对第一类/第二类错误概率的控制
signal: 模拟中发现当真实次品率为9%时仍有约15%概率被拒收（超过10%的允许错误率）
lesson: 统计抽样方案必须基于假设检验理论，显式控制信度（显著性水平与检验功效），不能凭经验简单比较
avoid: 
source: 2024年高教社杯全国大学生数学建模竞赛B题：生产过程中的决策问题|https://blog.csdn.net/weixin_43970743/article/details/151194019|2024
confidence: 高
```

---

## FD-38（公开经验库·Kimi）

```yaml
failure_id: FD-38
problem_type: 军事概率建模与命中优化
domain: 国防/概率论
method: 初期将深弹毁伤范围简化为圆形区域，忽略潜艇长方体形状的方向性
failure: 最优投弹点与真实最优解存在系统性偏差
cause: 潜艇长100m、宽20m，长宽比5:1，毁伤区域应随潜艇航向方位角（90°）调整，圆形简化丢失了方向信息
signal: 当潜艇航向改变时，最优投弹点应随之旋转，但圆形模型无法反映此特性
lesson: 毁伤概率建模必须尊重目标真实几何形状，对长方体目标需考虑其长宽方向与毁伤区域的匹配关系
avoid: 
source: 2024年高教社杯全国大学生数学建模竞赛D题：反潜航空深弹命中概率问题|https://cjournal.hep.com.cn/2095-3070/CN/10.19943/j.2095-3070.jmmia.2025.02.07|2024
confidence: 高
```

---

## FD-39（公开经验库·Kimi）

```yaml
failure_id: FD-39
problem_type: 气候风险评估与跨学科决策
domain: 金融保险/可持续发展
method: 初期尝试用传统精算模型（大数定律）估计极端天气风险
failure: 极端天气事件历史数据极少，传统精算方法无法给出可靠概率估计
cause: 大数定律要求大量独立同分布样本，而极端天气为厚尾分布、小概率事件，样本严重不足
signal: 计算得到的百年一遇事件概率与近年实际发生频率严重不符
lesson: 小样本厚尾风险问题必须采用信息扩散理论、极值理论(EVT)或贝叶斯方法，不能直接使用基于大数定律的传统精算模型
avoid: 
source: 2024年MCM/ICM美赛O奖论文：极端天气保险决策模型(ICM-E题)|https://mcmicm.org.cn/news/1070.html|2024
confidence: 高
```

---

## FD-40（公开经验库·Kimi）

```yaml
failure_id: FD-40
problem_type: 几何建模与路径优化
domain: 海洋测绘/几何光学
method: 直接用海区平均水深设计统一测线间距
failure: 浅水区漏测、深水区重叠过多
cause: 未考虑地形坡度导致水深变化，统一间距无法满足全海域覆盖约束
signal: 计算发现部分区域η<0（漏测），部分区域η>30%（冗余）
lesson: 海底地形起伏大的海域必须采用变间距或分区策略，不能简单使用平均水深设计统一间距
avoid: 
source: 2023年高教社杯全国大学生数学建模竞赛B题：多波束测线问题|https://www.ppmy.cn/news/1095872.html|2023
confidence: 高
```

---

## FD-41（公开经验库·Kimi）

```yaml
failure_id: FD-41
problem_type: 实验设计与工艺优化
domain: 化学工程/催化反应
method: 初期直接用原始催化剂组合编码作为单一分类变量进行回归
failure: 模型R²低，无法识别各催化剂组分对反应的独立贡献
cause: 催化剂组合是多个物理化学参数的复合体，单一编码丢失了各组分信息，导致模型无法解释
signal: 不同组合间反应性能差异大但编码数值接近，回归残差呈现明显结构
lesson: 复合工艺变量必须拆解为独立物理意义变量（如金属负载量、流速、温度等）后再建模，不能直接用组合编号作为回归自变量
avoid: 
source: 2021年高教社杯全国大学生数学建模竞赛B题：乙醇偶合制备C4烯烃|https://blog.csdn.net/weixin_43970743/article/details/161521614|2021
confidence: 高
```

---

## FD-42（公开经验库·Kimi）

```yaml
failure_id: FD-42
problem_type: 信用风险评估与信贷策略优化
domain: 金融科技/风险管理
method: 初期仅用企业规模与行业类型做简单评分卡，未深入挖掘交易票据特征
failure: 违约预测AUC仅约0.75，无法满足银行风控精度要求
cause: 交易票据中的进项/销项金额、上下游企业数量、废票比例等动态指标比静态规模更能反映企业真实经营状况
signal: 简单评分卡将大量实际已违约企业误判为优质客户
lesson: 金融风控建模必须重视特征工程，从原始交易数据中提取反映企业经营动态的多维度特征，不能仅依赖静态属性
avoid: 
source: 2020年高教社杯全国大学生数学建模竞赛C题：中小微企业的信贷决策|https://blog.csdn.net/2401_82505179/article/details/142721401|2020
confidence: 高
```

---

## FD-43（公开经验库·Kimi）

```yaml
failure_id: FD-43
problem_type: 需求预测与动态定价优化
domain: 零售管理/供应链优化
method: 初期直接对所有单品独立做预测和优化，未考虑品类约束与单品替代性
failure: 优化结果中某品类单品过多或缺失，导致品类需求无法满足且陈列混乱
cause: 忽略了商超运营中品类平衡与货架空间约束，将单品独立处理导致全局不可行
signal: 某品类选出单品数远超合理范围，而另一品类无单品入选
lesson: 零售补货优化必须考虑品类级约束与单品间替代关系，不能仅做单品独立优化；应先品类后单品的分层策略
avoid: 
source: 2023年高教社杯全国大学生数学建模竞赛C题：蔬菜类商品的自动定价与补货决策|https://bbs.pinggu.org/a-4081715.html|2023
confidence: 高
```

---

## FD-44（公开经验库·Kimi）

```yaml
failure_id: FD-44
problem_type: 在线优化与实时调度
domain: 钢铁冶金/连续铸造
method: 初期尝试用单一全局优化模型同时处理所有工况（正常、尾坯、异常）
failure: 模型求解时间过长，无法满足连铸在线实时性要求（秒级响应）
cause: 全局优化模型变量维度高，且每次异常都需重新求解，计算量过大
signal: 模拟中发现异常发生后数分钟内无法输出新方案，导致生产停滞
lesson: 工业在线优化必须考虑求解实时性，序贯算法或分时段分解策略比全局精确优化更适合有严格时效要求的场景
avoid: 
source: 2021年高教社杯全国大学生数学建模竞赛D题：连铸切割的在线优化|https://blog.csdn.net/gitblog_06632/article/details/143334963|2021
confidence: 高
```

---

## FD-45（公开经验库·豆包）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-45
problem_type: 预测
domain: 交通流量时序预测
method: 灰色预测GM-11
failure: 高峰期预测结果严重偏低
cause: 灰色模型适合平缓数据，车流早晚高峰波动剧烈
signal: 早高峰预测值仅为实测一半
lesson: 周期性波动时序优先选用深度学习时序模型
avoid: 
source: 2024高教社杯国赛E题交通流量管控优秀论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2024sxjmstjp/241127/1980970.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-46（公开经验库·豆包）

```yaml
failure_id: FD-46
problem_type: 预测
domain: 光伏板块指数时序分析
method: 直接多元回归
failure: 回归系数不稳定，每次取样结果浮动大
cause: 解释变量之间高度相关
signal: VIF方差膨胀因子大于10
lesson: 多因子经济预测首先处理多重共线性
avoid: 
source: 光伏建筑一体化板块指数分析优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2021
confidence: 高
```

---

## FD-47（公开经验库·豆包）

```yaml
failure_id: FD-47
problem_type: 优化决策
domain: 停车场车位排布优化
method: 只求解理论最小通道宽度
failure: 排布方案很难供普通司机泊车
cause: 数学最优忽略人为操作容错空间
signal: 优秀论文普遍增设舒适度惩罚项
lesson: 工程类优化问题需要加入现实操作约束
avoid: 
source: 2026电工杯A题停车场规划优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2026
confidence: 高
```

---

## FD-48（公开经验库·豆包）

```yaml
failure_id: FD-48
problem_type: 优化决策
domain: 电力机组经济调度
method: 忽略旋转备用约束
failure: 得到的最优解没有抗风险能力
cause: 模型只适配理想固定负荷
signal: 负荷小幅波动就会出现供电缺口
lesson: 电力调度优化必须设置发电备用量约束
avoid: 
source: 2025亚太杯D题电力系统机组组合论文|https://mbd.pub/o/bread/mbd-YZWZlplrZA==|2025
confidence: 高
```

---

## FD-49（公开经验库·豆包）

```yaml
failure_id: FD-49
problem_type: 评价分类
domain: 暑期兼职岗位适配度评价
method: TOPSIS直接计算距离评分
failure: 部分模糊的软实力指标难以量化
cause: TOPSIS更加适合客观数值指标
signal: 软实力指标打分波动很大
lesson: 含有较多定性指标优先选用模糊综合评判
avoid: 
source: 2020 HiMCM暑期岗位推荐O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2020
confidence: 中
```

---

## FD-50（公开经验库·豆包）

```yaml
failure_id: FD-50
problem_type: 物理建模
domain: 平纹织物热传导建模
method: 只建立宏观传热模型
failure: 无法反推单根纤维导热参数
cause: 宏观模型抹平微观纤维结构信息
signal: 缺少微观结构不能求解纤维参数
lesson: 复合材料参数反推必须搭建微观单元模型
avoid: 
source: 第四届华数杯A题织物导热优秀论文|https://blog.csdn.net/m0_52343631/article/details/140867886|2023
confidence: 高
```

---

## FD-51（公开经验库·豆包）

```yaml
failure_id: FD-51
problem_type: 图模型
domain: WLAN无线网络组网优化
method: 贪婪依次安放AP点位
failure: 后期布点极易发生信道干扰
cause: 贪心算法只顾及当下局部最优
signal: 整体吞吐量低于遗传算法方案
lesson: 无线网络布局属于全局优化，慎用贪心算法
avoid: 
source: 2024研究生华为杯B题WLAN组网优秀论文|https://github.com/1931239281/MathModel/blob/master/README.md|2024
confidence: 中
```

---

## FD-52（公开经验库·豆包）

```yaml
failure_id: FD-52
problem_type: 预测
domain: 高压油管压强数值预测
method: 普通欧拉迭代求解微分方程
failure: 长时间迭代之后压强误差持续累积
cause: 欧拉法截断误差偏大
signal: 迭代步数越多偏差越大
lesson: 工程微分方程优先选择四阶龙格-库塔算法
avoid: 
source: 2019国赛高压油管压力控制一等奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2019
confidence: 高
```

---

## FD-53（公开经验库·豆包）

```yaml
failure_id: FD-53
problem_type: 评价分类
domain: 网购商品综合评分评估
method: 单纯依靠星级评分评价商品
failure: 星级评分存在严重刷单失真
cause: 星级可以人为刷分，文字评论更真实
signal: 高星级商品文本差评数量很多
lesson: 电商口碑评估优先解析评论文本情感特征
avoid: 
source: 2020 MCM-ICM网购平台O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2020
confidence: 中
```

---

## FD-54（公开经验库·豆包）

```yaml
failure_id: FD-54
problem_type: 预测
domain: 城市生活垃圾日产量时序预测
method: 灰色预测GM-11
failure: 周末和假期的峰值全部被平滑处理
cause: 灰色模型只适合单调平缓序列
signal: 每一周周期峰值全部丢失
lesson: 含有周期性、节假日扰动的数据优先选用Prophet
avoid: 
source: 2022高教社杯国赛C题城市生活垃圾处置优秀论文|https://www.cumcm.edu.cn/works/excellent/2022/|2022
confidence: 高
```

---

## FD-55（公开经验库·豆包）

```yaml
failure_id: FD-55
problem_type: 预测
domain: 水质溶解氧含量预测
method: 普通多元线性回归
failure: 拟合精度低下
cause: 水体各项指标之间是非线性关系
signal: 训练集R-square仅有0.43
lesson: 环境监测非线性数据优先使用树类回归算法
avoid: 
source: 2025电工杯B题河道水质预警一等奖论文|https://blog.csdn.net/mathmodelshare/article/details/153692147|2025
confidence: 高
```

---

## FD-56（公开经验库·豆包）

```yaml
failure_id: FD-56
problem_type: 优化决策
domain: 生鲜冷链配送路径优化
method: 最近邻贪心算法规划路线
failure: 后期客户点位出现大面积超时
cause: 贪心只选择近处点位，忽略时间窗口
signal: 超过半数订单错过收货时段
lesson: 带时间窗的VRP问题禁止使用简单贪心策略
avoid: 
source: 2024亚太杯C题生鲜冷链配送优化论文|https://mbd.pub/o/bread/Z5ebm52tZw==|2024
confidence: 高
```

---

## FD-57（公开经验库·豆包）

```yaml
failure_id: FD-57
problem_type: 优化决策
domain: 校园自习室座位分配优化
method: 纯粹贪心顺序分配座位
failure: 结伴学生座位分散
cause: 优先响应预约顺序，没有考虑用户需求
signal: 问卷反馈大量同学需要和朋友寻找邻近空位
lesson: 公共资源分配除利用率之外增设人性化软约束
avoid: 
source: 第五届华数杯B题自习室调度优秀论文|https://blog.csdn.net/weixin_46189918/article/details/142268904|2024
confidence: 高
```

---

## FD-58（公开经验库·豆包）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-58
problem_type: 评价分类
domain: 乡村振兴发展水平综合评价
method: AHP层次分析法确定权重
failure: 评价结果容易受专家主观想法左右
cause: 权重依靠两两对比打分
signal: 更换打分人员之后村庄排名发生巨大变动
lesson: 多客观数据的综合评估优先选用熵权TOPSIS
avoid: 
source: 2023高教社杯国赛E题乡村振兴评估一等奖论文|https://www.cumcm.edu.cn/works/excellent/2023/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-59（公开经验库·豆包）

```yaml
failure_id: FD-59
problem_type: 物理建模
domain: 小球斜面滑动动力学建模
method: 全程使用静态动能定理
failure: 得不到速度-时间变化曲线
cause: 动能定理只能够求解始末状态
signal: 缺失每一刻的动态参数
lesson: 需要全过程动态数据就建立微分方程进行数值迭代
avoid: 
source: 2021 MCM物理方向O奖论文|https://github.com/liuyouyuan/mcm-icm-2021|2021
confidence: 中
```

---

## FD-60（公开经验库·豆包）

```yaml
failure_id: FD-60
problem_type: 图模型
domain: 城市公共交通最优路线规划
method: Floyd算法求解最短路径
failure: 站点数量庞大时运算开销过高
cause: 该算法复杂度为n的三次方
signal: 程序运行卡顿、求解速度很慢
lesson: 单点出发寻路优先选用Dijkstra算法而非Floyd
avoid: 
source: 2025研究生数学建模F题公共交通线路优化论文|https://github.com/MathematicalModelingClub/HuaweiCup2025|2025
confidence: 中
```

---

## FD-61（公开经验库·豆包）

```yaml
failure_id: FD-61
problem_type: 预测
domain: 电动汽车动力电池剩余寿命预测
method: 简单指数衰减回归
failure: 无法拟合电池后期加速老化现象
cause: 电池老化速率是非线性、分阶段变化
signal: 寿命后期预测数值严重偏大
lesson: 周期老化类时序数据优先使用循环神经网络类模型
avoid: 
source: 2020 ICM电池寿命方向O奖论文|https://github.com/akashsara/mcm-icm2020|2020
confidence: 中
```

---

## FD-62（公开经验库·豆包）

```yaml
failure_id: FD-62
problem_type: 优化决策
domain: 应急物资多仓库调运优化
method: 优先就近仓库输送物资贪心策略
failure: 近处仓库物资耗尽之后偏远灾区配送耗时很久
cause: 贪心只顾及单点最优缺少全局考量
signal: 部分偏远受灾点物资送达很晚
lesson: 多物资源应急调度需要全局规划，禁止就近贪心分配
avoid: 
source: 2022亚太杯D题救灾物资调度优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2022
confidence: 高
```

---

## FD-63（公开经验库·豆包）

```yaml
failure_id: FD-63
problem_type: 评价分类
domain: 学生综测综合素质等级评定
method: 简单累加各项加分
failure: 忽视学业成绩的首要地位
cause: 直接相加等同所有指标权重一致
signal: 部分成绩较差但是活动繁多的学生排名靠前
lesson: 学生综合测评必须设置差异化权重，学业权重最高
avoid: 
source: 2026电工杯C题学生综合素质测评一等奖论文|https://blog.csdn.net/codeforfun666/article/details/154713205|2026
confidence: 高
```

---

## FD-64（公开经验库·GLM）

```yaml
failure_id: FD-64
problem_type: 优化调度
domain: 公安/城市管理
method: 直接使用欧氏距离分配
failure: 分配结果导致部分区域由于道路绕行实际出警超时
cause: 忽略了城市路网的真实拓扑结构与单行道限制
signal: 模拟出警路径时发现大量节点不满足3分钟到达约束
lesson: 路径规划与调度类问题必须基于真实路网图论结构，不可用空间直线距离替代
avoid: 
source: 2011年全国大学生数学建模竞赛B题|全国大学生数学建模竞赛官网|2011
confidence: 高
```

---

## FD-65（公开经验库·GLM）

```yaml
failure_id: FD-65
problem_type: 预测
domain: 新能源
method: 多元线性回归
failure: 预测曲线在多云天气波动剧烈时段严重失真
cause: 气象因素与发电量之间存在强烈的非线性关系，且未考虑时序特征
signal: 残差分析显示误差随辐照度波动呈喇叭口状
lesson: 对于具有时序依赖和非线性特征的实际系统，不应仅使用静态线性模型
avoid: 
source: 2018年电工杯数学建模竞赛A题|全国大学生数学建模竞赛官网|2018
confidence: 高
```

---

## FD-66（公开经验库·GLM）

```yaml
failure_id: FD-66
problem_type: 模拟与优化
domain: 生物学/生态学
method: 纯Logistic增长模型
failure: 只能反映单点总质量的增长，无法体现真菌在三维空间蔓延的拓扑形态
cause: 忽略了空间分布与资源浓度梯度的相互作用
signal: 绘图结果显示一条S型曲线，缺乏空间维度的预测能力
lesson: 涉及空间形态演变与资源消耗耦合的问题必须引入空间维度的偏微分方程或网格模型
avoid: 
source: 2021年美国大学生数学建模竞赛A题|COMAP官网|2021
confidence: 高
```

---

## FD-67（公开经验库·GLM）

```yaml
failure_id: FD-67
problem_type: 优化设计
domain: 材料科学与工程热物理
method: 集中参数热容模型（零维模型）
failure: 预测的皮肤温度上升过快且无法反映各层间的温度延迟
cause: 将整个系统视为均质温度节点，忽略了材料内部的热阻和热扩散时间常数
signal: 优化结果给出的厚度远超实际需求以保证安全
lesson: 存在明显热阻梯度的多层介质动态传热问题，必须使用分布参数的偏微分方程
avoid: 
source: 2018年全国大学生数学建模竞赛A题|全国大学生数学建模竞赛官网|2018
confidence: 高
```

---

## FD-68（公开经验库·GLM）

```yaml
failure_id: FD-68
problem_type: 动态博弈与优化
domain: 公安/应急调度
method: 全市所有路口大范围无差别封锁
failure: 警力资源严重不足且耗时极长
cause: 忽视了罪犯移动能力的时间窗口限制
signal: 封锁所需时间远超罪犯逃逸时间
lesson: 围堵问题必须基于时间约束动态圈定搜索范围
avoid: 
source: 2011年全国大学生数学建模竞赛B题参考答案|全国大学生数学建模竞赛官网|2011
confidence: 高
```

---

## FD-69（公开经验库·GLM）

```yaml
failure_id: FD-69
problem_type: 优化
domain: 电子制造/工业工程
method: 多元线性回归
failure: 无法准确预测边界温区突变时的温度滞后
cause: 温度变化具有非线性迟滞特性，线性模型无法捕捉
signal: 预测曲线斜率与实测严重偏离
lesson: 有明确物理过程的系统应优先建立机理模型
avoid: 
source: 2020年全国大学生数学建模竞赛A题|全国大学生数学建模竞赛官网|2020
confidence: 高
```

---

## FD-70（公开经验库·GLM）

```yaml
failure_id: FD-70
problem_type: 评价与优化
domain: 众包物流/商业定价
method: 固定定价与贪心就近分配
failure: 偏远任务无人问津，整体完成率低
cause: 未考虑任务密度对接单意愿的影响
signal: 完成率不足50%
lesson: 定价需反映任务的空间异质性和执行难度
avoid: 
source: 2017年全国大学生数学建模竞赛B题|全国大学生数学建模竞赛官网|2017
confidence: 高
```

---

## FD-71（公开经验库·GLM）

```yaml
failure_id: FD-71
problem_type: 预测
domain: 海洋生态/环境科学
method: 直接用温度预测海鸟数量的线性回归
failure: 预测结果异常且不符合生态学规律
cause: 忽略了生态链中的时滞效应和非线性阈值
signal: 拟合度极低或出现负数种群
lesson: 生态学问题应重视因果机理和级联效应建模
avoid: 
source: 2020年美国大学生数学建模竞赛A题|COMAP官网|2020
confidence: 高
```

---

## FD-72（公开经验库·GLM）

```yaml
failure_id: FD-72
problem_type: 预测与评价
domain: 生态保护与遥感
method: 简单缓冲区分析
failure: 无法量化环境因素对动物选择的具体贡献
cause: 仅考虑了距离火灾中心的绝对距离，忽略了食物来源等关键因素
signal: 预测分布与实际观测偏离度大
lesson: 物种分布预测应结合多维生态因子构建统计学习模型
avoid: 
source: 2023年美国大学生数学建模竞赛B题|COMAP官网|2023
confidence: 高
```

---

## FD-73（公开经验库·GLM）

```yaml
failure_id: FD-73
problem_type: 排队论与决策
domain: 交通运输/运筹学
method: 静态平均计算
failure: 决策结果过于粗糙，高峰低谷期策略无差异
cause: 用平均到达率代替动态到达率，忽略了排队系统的随机性
signal: 计算的等待时间与实际观测差异显著
lesson: 具有随机到达和服务特征的系统必须使用随机过程模型进行解析
avoid: 
source: 2019年全国大学生数学建模竞赛C题|全国大学生数学建模竞赛官网|2019
confidence: 高
```

---

## FD-74（公开经验库·豆包）

```yaml
failure_id: FD-74
problem_type: 优化决策
domain: 园区微电网风光储协调优化配置
method: 非线性规划直接求解
failure: 求解器陷入局部最优，结果不可靠
cause: 问题存在离散约束，非线性规划无法保证全局最优
signal: 多次求解结果差异超过10%
lesson: 含离散互斥约束的优化问题应优先转化为混合整数线性规划
avoid: 
source: 2024电工杯A题园区微电网风光储协调优化配置优秀论文|https://blog.csdn.net/2201_75535220/article/details/139207728|2024
confidence: 高
```

---

## FD-75（公开经验库·豆包）

```yaml
failure_id: FD-75
problem_type: 预测
domain: 风电机组输出功率预测
method: ARIMA模型
failure: 对非平稳风速序列预测精度低
cause: ARIMA假设序列平稳，而风速序列非平稳
signal: 测试集R²仅为0.58
lesson: 非平稳时序预测应优先选用深度学习模型
avoid: 
source: 2019电工杯A题风电机组输出功率预测优秀论文|https://blog.csdn.net/qq_40379132/article/details/161259137|2019
confidence: 高
```

---

## FD-76（公开经验库·豆包）

```yaml
failure_id: FD-76
problem_type: 优化决策
domain: 人形机器人运动建模与能耗优化
method: 逆运动学直接求解
failure: 运动轨迹不连续，能耗波动大
cause: 逆运动学未考虑运动的连续性与平滑性
signal: 关节角速度突变超过30%
lesson: 人形机器人运动优化应优先保证轨迹连续性与平滑性
avoid: 
source: 2025亚太杯人形机器人运动建模与能耗优化优秀论文|https://www.iesdouyin.com/share/video/7575096913709687203|2025
confidence: 中
```

---

## FD-77（公开经验库·豆包）

```yaml
failure_id: FD-77
problem_type: 评价分类
domain: 婴儿睡眠质量综合评价
method: 逻辑回归模型
failure: 对非线性关联拟合效果差
cause: 逻辑回归假设变量与分类结果存在线性关联
signal: 测试集准确率仅为62.3%
lesson: 含非线性关联的分类问题应优先选用树类模型
avoid: 
source: 2023华数杯C题婴儿睡眠质量评价优秀论文|https://jishuzhan.net/article/1702235986626351106|2023
confidence: 高
```

---

## FD-78（公开经验库·豆包）

```yaml
failure_id: FD-78
problem_type: 优化决策
domain: 不透明制品最优配色方案设计
method: 线性拟合+线性规划
failure: 总色差超过目标值20%
cause: 线性拟合无法准确描述非线性关系
signal: 拟合残差超过10%
lesson: 含非线性关系的优化问题应优先选用非线性拟合+智能优化算法
avoid: 
source: 2023华数杯B题不透明制品最优配色方案设计优秀论文|http://www.guyue12306.com/archives/14/|2023
confidence: 高
```

---

## FD-79（公开经验库·豆包）

```yaml
failure_id: FD-79
problem_type: 预测
domain: 织物热导率预测
method: 解析法热传导方程
failure: 对复杂周期性结构求解精度低
cause: 解析法仅适用于简单几何结构
signal: 预测误差超过15%
lesson: 复杂周期性结构的热传导问题应优先选用有限差分法
avoid: 
source: 2023华数杯A题织物热导率预测优秀论文|https://blog.csdn.net/m0_52343631/article/details/140867886|2023
confidence: 高
```

---

## FD-80（公开经验库·豆包）

```yaml
failure_id: FD-80
problem_type: 优化决策
domain: 应急物资多仓库调运优化
method: 贪心调配方案
failure: 部分偏远受灾点物资送达时间过长
cause: 贪心只顾及单点最优，缺少全局考量
signal: 部分受灾点配送时间超过24小时
lesson: 多物资源应急调度需要全局规划，禁止就近贪心分配
avoid: 
source: 2022亚太杯D题救灾物资调度优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2022
confidence: 高
```

---

## FD-81（公开经验库·豆包）

```yaml
failure_id: FD-81
problem_type: 评价分类
domain: 乡村振兴发展水平综合评价
method: AHP层次分析法
failure: 评价结果容易受专家主观想法左右
cause: 权重依靠两两对比打分
signal: 更换打分人员之后村庄排名发生巨大变动
lesson: 多客观数据的综合评估优先选用熵权TOPSIS
avoid: 
source: 2023国赛E题乡村振兴评估一等奖论文|https://www.cumcm.edu.cn/works/excellent/2023/|2023
confidence: 高
```

---

## FD-82（公开经验库·豆包）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-82
problem_type: 优化决策
domain: 企业生产过程中的决策优化
method: 传统蒙特卡洛模拟模型
failure: 生产决策效率低，容易陷入局部最优
cause: 传统蒙特卡洛模拟缺乏优化算法的引导
signal: 多次模拟结果差异超过15%
lesson: 生产决策优化应优先选用智能算法优化的蒙特卡洛模拟模型
avoid: 
source: 2024高教社杯全国大学生数学建模竞赛B题优秀论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2024qgdxssxjmjslwzs_2024btlw/241104/1977943.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-83（公开经验库·豆包）

```yaml
failure_id: FD-83
problem_type: 优化决策
domain: 城市垃圾分类运输的路径优化与调度
method: 贪心算法
failure: 容易陷入局部最优，运输成本与碳排放较高
cause: 贪心算法只顾及当下局部最优，缺少全局考量
signal: 运输成本比改进型遗传算法方案高25%
lesson: 城市垃圾分类运输的路径优化与调度应优先选用改进型遗传算法
avoid: 
source: 2025电工杯数学建模竞赛B题优秀论文|https://blog.csdn.net/qq_50593822/article/details/148189953|2025
confidence: 高
```

---

## FD-84（公开经验库·豆包）

```yaml
failure_id: FD-84
problem_type: 优化决策
domain: 生鲜冷链配送路径优化
method: 传统遗传算法
failure: 容易陷入局部最优，配送成本与货损成本较高
cause: 传统遗传算法缺乏全局探索能力
signal: 配送成本比多目标遗传算法方案高12%
lesson: 生鲜冷链配送路径优化应优先选用多目标遗传算法+改进蚁群算法
avoid: 
source: 考虑碳排放和时间窗约束的冷链物流配送路径优化研究|https://www.hanspub.org/downLoad/page_download?filename=orf2024143_1131701725.pdf|2024
confidence: 高
```

---

## FD-85（公开经验库·豆包）

```yaml
failure_id: FD-85
problem_type: 预测
domain: 城市轨道交通客流短时预测
method: ARIMA模型
failure: 无法捕捉客流的非线性突变特征
cause: ARIMA假设序列平稳，而早高峰客流存在明显突变
signal: 早高峰预测误差超过20%
lesson: 短时突变性时序预测应优先选用深度学习模型
avoid: 
source: 2021高教社杯国赛A题城市轨道交通客流预测优秀论文|https://www.cumcm.edu.cn/works/excellent/2021/|2021
confidence: 高
```

---

## FD-86（公开经验库·豆包）

```yaml
failure_id: FD-86
problem_type: 优化决策
domain: 港口集装箱堆场堆位分配优化
method: 贪心分配算法
failure: 后期堆位冲突严重，翻箱率过高
cause: 贪心仅考虑当前最优，忽略后续提箱需求
signal: 翻箱率超过30%
lesson: 带后续操作约束的资源分配问题禁止使用贪心策略
avoid: 
source: 2020亚太杯B题港口集装箱堆场优化优秀论文|https://mbd.pub/o/bread/ZJOWZ56tZw==|2020
confidence: 高
```

---

## FD-87（公开经验库·豆包）

```yaml
failure_id: FD-87
problem_type: 评价分类
domain: 城市营商环境综合评价
method: 熵权-TOPSIS模型
failure: 权重过度偏向变异大的指标，忽略重要性
cause: 熵权法仅基于数据变异确权，不考虑指标实际重要性
signal: 部分重要但变异小的指标权重被低估
lesson: 多指标综合评价应优先选用同时考虑变异与重要性的权重法
avoid: 
source: 2022国赛D题城市营商环境评价一等奖论文|https://www.cumcm.edu.cn/works/excellent/2022/|2022
confidence: 高
```

---

## FD-88（公开经验库·豆包）

```yaml
failure_id: FD-88
problem_type: 优化决策
domain: 无人机山地地形测绘航线规划
method: 固定平行航线规划
failure: 平坦地形能耗过高，陡峭地形精度不足
cause: 未考虑地形坡度对测绘的影响
signal: 平坦地形飞行时长增加20%，陡峭地形重叠率不足50%
lesson: 地形相关的航线规划必须引入地形特征的自适应调整
avoid: 
source: 2023美赛MCM无人机测绘O奖论文|https://github.com/ZPZhou-lab/MathematicalModeling/blob/main/README.md|2023
confidence: 中
```

---

## FD-89（公开经验库·豆包）

```yaml
failure_id: FD-89
problem_type: 图模型
domain: 城市地下管网泄漏定位
method: RSSI定位算法
failure: 定位误差超过5米
cause: 地下环境复杂，信号强度衰减不稳定
signal: 多次测量的信号强度差异超过30%
lesson: 地下环境的定位问题应优先选用TDOA算法
avoid: 
source: 2024研究生数模B题地下管网泄漏定位优秀论文|https://github.com/1931239281/MathModel/blob/master/README.md|2024
confidence: 中
```

---

## FD-90（公开经验库·豆包）

```yaml
failure_id: FD-90
problem_type: 预测
domain: 农产品价格短期预测
method: 灰色预测模型
failure: 无法捕捉价格的周期性波动
cause: 灰色预测仅适合单调序列，农产品价格存在明显周期
signal: 价格周期峰值预测误差超过15%
lesson: 周期性波动的价格预测应优先选用Prophet模型
avoid: 
source: 2025华数杯D题农产品价格预测优秀论文|https://blog.csdn.net/weixin_46189918/article/details/142268904|2025
confidence: 高
```

---

## FD-91（公开经验库·豆包）

```yaml
failure_id: FD-91
problem_type: 优化决策
domain: 医院手术排程优化
method: 贪心排程算法
failure: 急诊手术等待时间过长
cause: 贪心仅考虑当前手术室闲置，忽略急诊优先级
signal: 急诊手术平均等待时间超过2小时
lesson: 带优先级约束的排程问题禁止使用贪心策略
avoid: 
source: 2023电工杯C题医院手术排程优秀论文|https://blog.csdn.net/mathmodelshare/article/details/153692147|2023
confidence: 高
```

---

## FD-92（公开经验库·豆包）

```yaml
failure_id: FD-92
problem_type: 评价分类
domain: 高校毕业生就业质量评价
method: TOPSIS模型
failure: 主观满意度指标的评价结果偏差较大
cause: TOPSIS适合客观指标，无法处理模糊主观指标
signal: 就业满意度的评价结果与实际调研偏差超过20%
lesson: 含主观模糊指标的评价应优先选用模糊综合评价
avoid: 
source: 2022美赛ICM毕业生就业质量O奖论文|https://github.com/akashsara/mcm-icm2022|2022
confidence: 中
```

---

## FD-93（公开经验库·豆包）

```yaml
failure_id: FD-93
problem_type: 物理建模
domain: 锂电池热失控预警模型
method: 随机森林模型
failure: 预警提前时间不足30秒
cause: 随机森林无法捕捉时序特征，仅能基于当前数据判断
signal: 热失控发生前30秒才发出预警
lesson: 时序相关的预警问题应优先选用深度学习模型
avoid: 
source: 2024国赛B题锂电池热失控预警一等奖论文|https://www.cumcm.edu.cn/works/excellent/2024/|2024
confidence: 高
```

---

## FD-94（公开经验库·豆包）

```yaml
failure_id: FD-94
problem_type: 图模型
domain: 城市共享单车调度优化
method: 贪心调度算法
failure: 核心商圈站点供需失衡严重
cause: 贪心仅考虑当前距离，忽略站点优先级
signal: 核心商圈站点的车辆缺口超过30%
lesson: 带优先级约束的调度问题禁止使用贪心策略
avoid: 
source: 2025亚太杯C题共享单车调度优化优秀论文|https://mbd.pub/o/bread/Z5ebm52tZw==|2025
confidence: 高
```

---

## FD-95（公开经验库·豆包）

```yaml
failure_id: FD-95
problem_type: 预测
domain: 光伏电站日前发电功率预测
method: 灰色GM‑(1,1)
failure: 整日发电功率预测偏差巨大
cause: 光伏发电拥有明显昼夜周期性，灰色模型适配单调变化序列
signal: 晴天正午时段预测数值偏差超过35%
lesson: 具备周期性波动特征的能源时序，禁止使用灰色预测模型
avoid: 
source: 2025电工杯A题光伏电站发电功率日前预测优秀论文|https://blog.csdn.net/maligebilaowang/article/details/148101073|2025
confidence: 高
```

---

## FD-96（公开经验库·豆包）

```yaml
failure_id: FD-96
problem_type: 优化决策
domain: 嵌入式社区养老服务站选址和规模优化
method: 贪心就近选址算法
failure: 部分社区站点扎堆，偏远居民区缺少养老站点
cause: 贪心只优先处理人口稠密点位，忽略整片区域均衡覆盖
signal: 偏远社区老人平均通勤距离超出三千米
lesson: 公共服务设施选址优化应当建立整数规划，设置覆盖约束，不能依靠贪心策略
avoid: 
source: 2026电工杯B题嵌入式社区养老服务站的建设与优化问题论文|https://blog.csdn.net/maligebilaowang/article/details/161324818|2026
confidence: 高
```

---

## FD-97（公开经验库·豆包）

```yaml
failure_id: FD-97
problem_type: 优化决策
domain: 六自由度机械臂关节角路径优化
method: 三次多项式插值规划
failure: 碰到障碍物，运动轨迹发生碰撞
cause: 插值只保证轨迹平滑，没有加入障碍物规避的目标函数
signal: ['仿真检测出现杆件和障碍物相交']
lesson: 存在障碍物的机械臂轨迹规划需要使用智能优化算法，把避障写入目标约束
avoid: 
source: 2024年华数杯A‑机器臂关节角路径的优化设计论文|https://blog.csdn.net/maligebilaowang|2024
confidence: 高
```

---

## FD-98（公开经验库·豆包）

```yaml
failure_id: FD-98
problem_type: 预测
domain: 洪水灾害风险等级以及灾害损失预测
method: Logistic回归模型
failure: 复杂地形流域预测结果偏差大
cause: 逻辑回归只适配特征‑标签之间的线性关联
signal: ['山地流域样本准确率仅有57%']
lesson: ['水文灾害多因子非线性预测优先选用树类集成模型']
avoid: 
source: 2024亚太杯中文赛B题洪水灾害的数据分析与预测论文|https://jishuzhan.net/article/1811720976279277569|2024
confidence: 高
```

---

## FD-99（公开经验库·豆包）

```yaml
failure_id: FD-99
problem_type: 评价分类
domain: 数据中心算电协同调度方案综合评价
method: ['熵权‑TOPSIS']
failure: 权重过度偏向波动较大的碳排放指标
cause: ['熵权法只根据数据波动大小分配权重，忽视指标实际业务重要程度']
signal: ['调度方案评价结果脱离机房运营常识']
lesson: ['工程多指标评估优先选择CRITIC权重法，规避熵权法的权重偏移问题']
avoid: 
source: 2026年华数杯C题算电协同的多目标优化调度优化研究论文|https://www.iesdouyin.com/share/video/7671299682630503730|2026
confidence: 高
```

---

## FD-100（公开经验库·豆包）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-100
problem_type: 优化决策
domain: 工厂生产抽样检测成本优化
method: 基础版蒙特卡洛模拟
failure: 多次仿真之后最优抽样参数波动很大
cause: ['普通蒙特卡洛依靠随机采样搜索，缺少寻优机制']
signal: ['多次运行得出抽样样本数量差距超过四十']
lesson: ['含有随机变量的成本优化问题，需要搭配智能算法优化蒙特卡洛仿真参数']
avoid: 
source: 2024高教社杯国赛B题生产检测决策优化一等奖论文|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2024qgdxssxjmjslwzs_2024btlw/241104/1977943.shtml|2024
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-101（公开经验库·豆包）

```yaml
failure_id: FD-101
problem_type: 机理建模
domain: 森林菌根真菌‑植被养分循环动态建模
method: ['多元线性回归模型']
failure: 只能够拟合现有观测数值，不能推演多年之后生态演化
cause: ['回归属于数据拟合模型，缺少生态机理']
signal: ['十年之后种群预测数值严重偏离常识区间']
lesson: ['探究物质循环、种群博弈的机理问题优先采用微分方程动力学模型']
avoid: 
source: 2021年美赛MCM‑ICM A题森林真菌生态建模O奖论文|https://wenku.csdn.net/doc/xqnrkpdv3e|2021
confidence: 中
```

---

## FD-102（公开经验库·豆包）

```yaml
failure_id: FD-102
problem_type: 优化决策
domain: 城市垃圾分类运输车路径‑中转站选址联合优化
method: ['最近邻贪心算法']
failure: 中转站布局失衡，远距离点位运输成本高昂
cause: 贪心每次挑选最近中转站，缺少全局统筹规划
signal: ['偏远点位单程运输距离超出八公里']
lesson: ['选址‑路径联合优化问题属于复杂组合优化，禁止简易贪心算法求解']
avoid: 
source: 2025电工杯B题城市垃圾分类运输的路径优化优秀论文|https://blog.csdn.net/maligebilaowang/article/details/148223307|2025
confidence: 高
```

---

## FD-103（公开经验库·豆包）

```yaml
failure_id: FD-103
problem_type: 预测
domain: 奥运会各个参赛国家奖牌数量预测
method: ['基础多元线性回归']
failure: 东道主国家奖牌数量预测值偏低
cause: ['普通线性模型很难拟合东道主带来的非线性增益']
signal: ['主办国奖牌预测偏差超过22%']
lesson: ['含有特殊事件红利的多层次预测，优先选用分层嵌套模型']
avoid: 
source: MCM‑ICM奥运会奖牌预测O奖论文解析|https://mcmicm.org.cn/news/1186.html|2026
confidence: 中
```

---

## FD-104（公开经验库·豆包）

```yaml
failure_id: FD-104
problem_type: 综合评价
domain: 智慧城市多维度建设水平评估
method: ['单一TOPSIS评价模型']
failure: 居民满意度指标评价结果失真
cause: ['TOPSIS只适合硬性客观数值，不适用于模糊主观问卷数据']
signal: ['民生满意度得分和市民调研结果出入较大']
lesson: ['客观指标叠加主观问卷的综合评估，搭配主成分分析‑模糊综合评价']
avoid: 
source: 2017年美赛ICM E题智慧城市建设O奖论文|https://blog.csdn.net/qq_41112170/article/details/122108814|2017
confidence: 中
```

---

## FD-105（公开经验库·Kimi）

```yaml
failure_id: FD-105
problem_type: 交通流量预测与信号控制优化
domain: 智能交通/城市规划
method: 初期尝试用固定时段划分（如每2小时一段）做流量分析
failure: 时段边界处流量突变，聚类结果与实际情况不符
cause: 固定时段未考虑实际流量变化规律，导致高峰时段被割裂或平峰被合并
signal: 聚类中心代表性与实际交通状况偏差大
lesson: 时段划分应基于数据驱动（聚类）而非主观设定，KMeans等无监督方法更适合发现自然流量模式
avoid: 
source: 2024年高教社杯全国大学生数学建模竞赛E题：交通流量管控|https://blog.csdn.net/weixin_43292788/article/details/146361641|2024
confidence: 高
```

---

## FD-106（公开经验库·Kimi）

```yaml
failure_id: FD-106
problem_type: 生产调度与空间优化
domain: 畜牧养殖/运筹优化
method: 初期直接用总羊只数除以单栏容量估算所需栏位数
failure: 估算结果远小于实际峰值需求，导致哺乳期和育肥期严重缺栏
cause: 未考虑各阶段不能混养且周期重叠导致的需求峰值，简单平均忽略了时间维度上的叠加效应
signal: 计算显示某几周所需栏位数超过现有112个的50%以上
lesson: 多阶段生产系统必须建立动态库存/栏位模型，考虑各阶段的时间耦合与峰值叠加，不能简单用总量平均
avoid: 
source: 2023年高教社杯全国大学生数学建模竞赛D题：圈养湖羊的空间利用率|https://www.ppmy.cn/news/1096239.html|2023
confidence: 高
```

---

## FD-107（公开经验库·Kimi）

```yaml
failure_id: FD-107
problem_type: 信息传输优化与概率建模
domain: 应急通信/卫星通信
method: 初期尝试用简单广播方式（主站轮流广播自身信息）
failure: 传输时间K远大于理论最小值，效率极低
cause: 未利用消息拼接（1.5条/次）和对称性并行传输，导致每轮传输信息量不足
signal: 计算得K值与N呈线性关系而非对数/次线性关系，与信息论下限差距大
lesson: 信息传播优化必须充分利用信道容量（每条消息最大字符数）和并行传输能力，通过消息拼接与对称设计逼近信息论下限
avoid: 
source: 2022年高教社杯全国大学生数学建模竞赛D题：气象报文信息卫星通信传输|https://www.lmlphp.com/user/628420/article/item/10928850/|2022
confidence: 高
```

---

## FD-108（公开经验库·Kimi）

```yaml
failure_id: FD-108
problem_type: 光谱鉴别与分类
domain: 中药学/化学计量学
method: 初期直接用原始全波段光谱训练BP神经网络
failure: 训练集准确率高但测试集准确率显著下降，泛化能力差
cause: 光谱维数高达数千点，样本量相对不足，神经网络严重过拟合；且未做预处理，噪声干扰大
signal: 训练准确率>95%，测试准确率<70%
lesson: 高维光谱数据必须先进行预处理与降维/特征选择，不能直接将原始数据输入复杂模型；样本量不足时优先使用SVM等泛化能力强的模型
avoid: 
source: 2021年高教社杯全国大学生数学建模竞赛E题：中药材的鉴别|https://blog.csdn.net/weixin_43970743/article/details/161521761|2021
confidence: 高
```

---

## FD-109（公开经验库·Kimi）

```yaml
failure_id: FD-109
problem_type: 热传导机理建模与工艺优化
domain: 电子制造/热工学
method: 初期用集总参数法（将整个PCB视为温度均匀的整体）建模
failure: 计算温度曲线与实测严重不符，峰值温度偏差超过20°C
cause: PCB板有一定厚度，内部存在温度梯度，集总参数法仅适用于Bi数很小的情况，而回焊炉中对流较强，Bi数较大
signal: 计算得到的升温速率远快于实际，且峰值温度偏高
lesson: 当物体内部热阻与表面热阻相当时（Bi>0.1），必须采用分布式热传导模型（一维/二维/三维），不能简单使用集总参数法
avoid: 
source: 2020年高教社杯全国大学生数学建模竞赛A题：炉温曲线|https://wenku.csdn.net/answer/303wy9rvnqqv|2020
confidence: 高
```

---

## FD-110（公开经验库·Kimi）

```yaml
failure_id: FD-110
problem_type: 几何光学与精密工程
domain: 射电天文/精密机械
method: 初期直接用最小二乘法拟合抛物面，未考虑光学焦点约束
failure: 拟合抛物面焦点偏离馈源舱位置，导致接收比极低
cause: 最小二乘仅最小化节点到曲面距离，不保证光学性质（焦点位置），而射电望远镜的核心要求是焦点准确
signal: 计算接收比接近基准球面水平，无显著提升
lesson: 工程问题建模必须尊重核心物理约束（此处为光学聚焦），不能仅用纯数学拟合替代物理机理；理想抛物面必须由焦点位置确定，再检验节点可达性
avoid: 
source: 2021年高教社杯全国大学生数学建模竞赛A题：FAST主动反射面的形状调节|https://blog.csdn.net/m0_49842530/article/details/146071683|2021
confidence: 高
```

---

## FD-111（公开经验库·Kimi）

```yaml
failure_id: FD-111
problem_type: 图像识别与目标检测
domain: 农业机器人/计算机视觉
method: 初期直接用YOLO进行端到端训练
failure: 训练数据量不足，模型无法收敛，检测精度极低
cause: 竞赛提供的图像数据集数量有限，YOLO等复杂目标检测模型参数量大，小样本下严重过拟合
signal: 训练损失震荡不下降，测试集mAP接近0
lesson: 数据量不足时，优先使用传统图像处理方法（阈值分割、圆检测）或轻量CNN+迁移学习，避免直接训练复杂目标检测模型；传统方法在特定场景（如颜色鲜明的苹果）下可能更稳健
avoid: 
source: 2023年APMCM亚太地区大学生数学建模竞赛A题：果实采摘机器人的图像识别|https://blog.csdn.net/2201_75432540/article/details/134599444|2023
confidence: 中
```

---

## FD-112（公开经验库·Kimi）

```yaml
failure_id: FD-112
problem_type: 计算流体力学与热环境优化
domain: 设施农业/环境工程
method: 初期尝试用ANSYS Fluent进行完整三维CFD仿真
failure: 软件授权问题与计算时间过长，无法在竞赛时间内完成
cause: 完整CFD仿真需要专业软件与大量计算资源，竞赛环境下不具备条件
signal: 单次仿真耗时超过数小时，无法在规定时间内完成多工况对比
lesson: 竞赛环境下应优先选择可自主编程实现的简化模型（如Python有限体积法），或采用集总参数模型；CFD思想可用但需大幅简化网格与物理模型
avoid: 
source: 2023年APMCM亚太地区大学生数学建模竞赛B题：玻璃温室中的微气候调控|https://jishuzhan.net/article/1728259980206804994|2023
confidence: 中
```

---

## FD-113（公开经验库·Kimi）

```yaml
failure_id: FD-113
problem_type: 时间序列预测与竞争分析
domain: 产业经济/能源政策
method: 初期仅用简单线性回归拟合销量与时间的关系
failure: 预测结果在几年后出现负销量或 unrealistic 的超高增长
cause: 新能源汽车销量呈S型增长（初期慢、中期快、后期饱和），线性模型无法刻画这种非线性特征
signal: 预测曲线单调上升或下降，无饱和迹象，与产业生命周期理论矛盾
lesson: 产业发展预测必须考虑生命周期规律，优先使用Logistic模型、系统动力学或带饱和项的回归，避免简单线性外推
avoid: 
source: 2023年APMCM亚太地区大学生数学建模竞赛C题：我国新能源电动汽车的发展趋势|https://blog.csdn.net/weixin_45499067/article/details/134551814|2023
confidence: 中
```

---

## FD-114（公开经验库·Kimi）

```yaml
failure_id: FD-114
problem_type: 需求预测与库存优化
domain: 制造业/供应链管理
method: 初期对所有物料使用相同的三次指数平滑参数（如统一α=0.3）
failure: 上升型物料频繁缺货，服务水平远低于85%；下降型物料库存积压严重
cause: 不同物料需求趋势差异大，统一参数无法兼顾：上升型需快速响应，下降型需保守预测
signal: 某上升型物料连续多周缺货，服务水平仅约60%；某下降型物料库存持续攀升
lesson: 多品种需求预测必须分类处理（按趋势/波动率分组），对不同类别采用不同模型参数或策略，不能一刀切
avoid: 
source: 2022年高教社杯全国大学生数学建模竞赛E题：小批量物料的生产安排|https://blog.csdn.net/weixin_43292788/article/details/131082064|2022
confidence: 高
```

---

## FD-129（公开经验库·WorkBuddy）

```yaml
failure_id: FD-129
problem_type: 预测
domain: 能源工程/电池管理
method: 线性回归拟合放电曲线
failure: 放电曲线非线性显著
cause: 放电曲线非线性显著
signal: R^2低
lesson: 需用非线性模型
avoid: 
source: 全国大学生数学建模竞赛2016年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## FD-130（公开经验库·WorkBuddy）

```yaml
failure_id: FD-130
problem_type: 预测
domain: 能源工程/电池管理
method: 忽略温度影响
failure: 温度对放电时间影响大
cause: 温度对放电时间影响大
signal: 不同温度预测偏差大
lesson: 需引入温度变量
avoid: 
source: 全国大学生数学建模竞赛2016年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## FD-131（公开经验库·WorkBuddy）

```yaml
failure_id: FD-131
problem_type: 预测
domain: 能源工程/风电
method: 忽略尾流效应
failure: 下游机组受上游遮挡功率下降
cause: 下游机组受上游遮挡功率下降
signal: 总功率预测偏高
lesson: 需引入尾流模型
avoid: 
source: 全国大学生数学建模竞赛2016年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## FD-132（公开经验库·WorkBuddy）

```yaml
failure_id: FD-132
problem_type: 预测
domain: 能源工程/风电
method: 用物理功率曲线直接预测
failure: 未考虑实际运行偏差
cause: 未考虑实际运行偏差
signal: 预测误差大
lesson: 需数据驱动修正
avoid: 
source: 全国大学生数学建模竞赛2016年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2016
confidence: 中
```

---

## FD-133（公开经验库·WorkBuddy）

```yaml
failure_id: FD-133
problem_type: 预测
domain: 运筹优化/定价策略
method: 全局统一定价模型
failure: 不同区域定价规律不同
cause: 不同区域定价规律不同
signal: 模型拟合差
lesson: 需分区建模
avoid: 
source: 全国大学生数学建模竞赛2017年B题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## FD-134（公开经验库·WorkBuddy）

```yaml
failure_id: FD-134
problem_type: 预测
domain: 运筹优化/定价策略
method: 忽略会员位置因素
failure: 会员就近接单, 位置影响完成率
cause: 会员就近接单, 位置影响完成率
signal: 完成率预测不准
lesson: 需引入距离变量
avoid: 
source: 全国大学生数学建模竞赛2017年B题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## FD-135（公开经验库·WorkBuddy）

```yaml
failure_id: FD-135
problem_type: 预测
domain: 化学计量学/光谱分析
method: 线性回归拟合
failure: 颜色与浓度关系非线性
cause: 颜色与浓度关系非线性
signal: 残差有趋势
lesson: 需用非线性回归
avoid: 
source: 全国大学生数学建模竞赛2017年C题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## FD-136（公开经验库·WorkBuddy）

```yaml
failure_id: FD-136
problem_type: 预测
domain: 化学计量学/光谱分析
method: 忽略交互效应
failure: R/G/B间存在交互影响浓度
cause: R/G/B间存在交互影响浓度
signal: 模型偏差
lesson: 需引入交互项
avoid: 
source: 全国大学生数学建模竞赛2017年C题|https://sxjm.yzu.edu.cn|2017
confidence: 中
```

---

## FD-137（公开经验库·WorkBuddy）

```yaml
failure_id: FD-137
problem_type: 预测
domain: 商业分析/用户画像
method: 仅用消费金额聚类
failure: 维度单一无法全面刻画会员
cause: 维度单一无法全面刻画会员
signal: 分群效果差
lesson: 需多维特征
avoid: 
source: 全国大学生数学建模竞赛2018年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2018
confidence: 中
```

---

## FD-138（公开经验库·WorkBuddy）

```yaml
failure_id: FD-138
problem_type: 预测
domain: 商业分析/用户画像
method: 忽略时间特征
failure: 消费时间模式反映重要行为
cause: 消费时间模式反映重要行为
signal: 预测不准
lesson: 需引入时间特征
avoid: 
source: 全国大学生数学建模竞赛2018年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2018
confidence: 中
```

---

## FD-139（公开经验库·WorkBuddy）

```yaml
failure_id: FD-139
problem_type: 预测
domain: 环境监测/数据校准
method: 仅用线性回归
failure: 污染物浓度与气象因素非线性
cause: 污染物浓度与气象因素非线性
signal: 残差有趋势
lesson: 需用非线性模型
avoid: 
source: 全国大学生数学建模竞赛2019年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 中
```

---

## FD-140（公开经验库·WorkBuddy）

```yaml
failure_id: FD-140
problem_type: 预测
domain: 环境监测/数据校准
method: 忽略气象因素
failure: 温湿度影响监测仪器读数
cause: 温湿度影响监测仪器读数
signal: 校准误差大
lesson: 需引入气象变量
avoid: 
source: 全国大学生数学建模竞赛2019年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 中
```

---

## FD-141（公开经验库·WorkBuddy）

```yaml
failure_id: FD-141
problem_type: 预测
domain: 商业运营/定价策略
method: 假设需求线性下降
failure: 实际需求曲线可能非线性
cause: 实际需求曲线可能非线性
signal: 最优价格偏差
lesson: 需用非线性需求函数
avoid: 
source: 全国大学生数学建模竞赛2019年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 低
```

---

## FD-142（公开经验库·WorkBuddy）

```yaml
failure_id: FD-142
problem_type: 预测
domain: 商业运营/定价策略
method: 忽略竞争反应
failure: 降价可能引发价格战
cause: 降价可能引发价格战
signal: 利润预测偏高
lesson: 需引入博弈模型
avoid: 
source: 全国大学生数学建模竞赛2019年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2019
confidence: 低
```

---

## FD-143（公开经验库·WorkBuddy）

```yaml
failure_id: FD-143
problem_type: 预测
domain: 金融风控/信贷决策
method: 逻辑回归预测违约
failure: 特征与违约非线性关系
cause: 特征与违约非线性关系
signal: AUC偏低
lesson: 需用非线性模型
avoid: 
source: 全国大学生数学建模竞赛2020年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 中
```

---

## FD-144（公开经验库·WorkBuddy）

```yaml
failure_id: FD-144
problem_type: 预测
domain: 金融风控/信贷决策
method: 忽略数据不平衡
failure: 违约样本少导致模型偏向多数类
cause: 违约样本少导致模型偏向多数类
signal: 召回率低
lesson: 需过采样或调整权重
avoid: 
source: 全国大学生数学建模竞赛2020年C题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 中
```

---

## FD-145（公开经验库·WorkBuddy）

```yaml
failure_id: FD-145
problem_type: 预测
domain: 智能水务/时间序列预测
method: ARIMA预测用水量
failure: 用水量有复杂周期性, ARIMA难以捕捉
cause: 用水量有复杂周期性, ARIMA难以捕捉
signal: 预测误差大
lesson: 需用LSTM等深度模型
avoid: 
source: 全国大学生数学建模竞赛2020年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 低
```

---

## FD-146（公开经验库·WorkBuddy）

```yaml
failure_id: FD-146
problem_type: 预测
domain: 智能水务/时间序列预测
method: 固定阈值异常检测
failure: 不同时段正常用水量差异大
cause: 不同时段正常用水量差异大
signal: 误报率高
lesson: 需自适应阈值
avoid: 
source: 全国大学生数学建模竞赛2020年E题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2020
confidence: 低
```

---

## FD-147（公开经验库·WorkBuddy）

```yaml
failure_id: FD-147
problem_type: 预测
domain: 人口学/人口预测
method: 简单指数增长模型
failure: 未考虑年龄结构变化
cause: 未考虑年龄结构变化
signal: 长期预测偏差大
lesson: 需用矩阵模型
avoid: 
source: 全国大学生数学建模竞赛2007年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2007
confidence: 中
```

---

## FD-148（公开经验库·WorkBuddy）

```yaml
failure_id: FD-148
problem_type: 预测
domain: 人口学/人口预测
method: 忽略人口迁移
failure: 城乡迁移对人口分布影响大
cause: 城乡迁移对人口分布影响大
signal: 城镇化率预测不准
lesson: 需引入迁移率
avoid: 
source: 全国大学生数学建模竞赛2007年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2007
confidence: 中
```

---

## FD-149（公开经验库·WorkBuddy）

```yaml
failure_id: FD-149
problem_type: 预测
domain: 环境科学/水质监测
method: 忽略污染物降解
failure: 污染物沿程有自然降解
cause: 污染物沿程有自然降解
signal: 下游浓度预测偏高
lesson: 需引入降解项
avoid: 
source: 全国大学生数学建模竞赛2005年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2005
confidence: 中
```

---

## FD-150（公开经验库·WorkBuddy）

```yaml
failure_id: FD-150
problem_type: 预测
domain: 环境科学/水质监测
method: 仅用单因子评价
failure: 未考虑多指标综合影响
cause: 未考虑多指标综合影响
signal: 评价不全面
lesson: 需用综合指数
avoid: 
source: 全国大学生数学建模竞赛2005年A题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2005
confidence: 中
```

---

## FD-151（公开经验库·WorkBuddy）

```yaml
failure_id: FD-151
problem_type: 预测
domain: 医学统计/疗效评价
method: 简单t检验比较疗效
failure: 未考虑重复测量的自相关
cause: 未考虑重复测量的自相关
signal: p值不可靠
lesson: 需用混合效应模型
avoid: 
source: 全国大学生数学建模竞赛2006年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2006
confidence: 中
```

---

## FD-152（公开经验库·WorkBuddy）

```yaml
failure_id: FD-152
problem_type: 预测
domain: 医学统计/疗效评价
method: 忽略患者个体差异
failure: 不同患者对疗法反应不同
cause: 不同患者对疗法反应不同
signal: 预测精度低
lesson: 需引入随机效应
avoid: 
source: 全国大学生数学建模竞赛2006年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2006
confidence: 中
```

---

## FD-153（公开经验库·WorkBuddy）

```yaml
failure_id: FD-153
problem_type: 预测
domain: 流行病学/公共卫生
method: SIR模型忽略潜伏期
failure: 埃博拉有显著潜伏期
cause: 埃博拉有显著潜伏期
signal: 传播预测不准
lesson: 需用SEIR模型
avoid: 
source: 2015 MCM Problem A: Eradicating Ebola|https://www.jingsailian.com/news/233612.html|2015
confidence: 中
```

---

## FD-154（公开经验库·WorkBuddy）

```yaml
failure_id: FD-154
problem_type: 预测
domain: 流行病学/公共卫生
method: 均匀分配疫苗
failure: 不同地区疫情严重度不同
cause: 不同地区疫情严重度不同
signal: 控制效果差
lesson: 需优化分配
avoid: 
source: 2015 MCM Problem A: Eradicating Ebola|https://www.jingsailian.com/news/233612.html|2015
confidence: 中
```

---

## FD-189（公开经验库·WorkBuddy）

```yaml
failure_id: FD-189
problem_type: 预测
domain: 农业AI/图像识别
method: 从零训练CNN
failure: 数据量不足导致过拟合
cause: 数据量不足导致过拟合
signal: 测试准确率低
lesson: 需用迁移学习
avoid: 
source: 2019年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2019
confidence: 低
```

---

## FD-190（公开经验库·WorkBuddy）

```yaml
failure_id: FD-190
problem_type: 预测
domain: 农业AI/图像识别
method: 忽略数据不平衡
failure: 常见病害样本多, 罕见病害少
cause: 常见病害样本多, 罕见病害少
signal: 少数类识别差
lesson: 需数据增强或加权
avoid: 
source: 2019年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2019
confidence: 低
```

---

## FD-191（公开经验库·WorkBuddy）

```yaml
failure_id: FD-191
problem_type: 预测
domain: 电力系统/新能源
method: 仅用物理模型
failure: 实际功率受多种因素影响, 物理模型理想化
cause: 实际功率受多种因素影响, 物理模型理想化
signal: 预测误差大
lesson: 需数据驱动修正
avoid: 
source: 2019年电工杯数学建模竞赛A题|https://www.saikr.com/vse/DGB2019|2019
confidence: 低
```

---

## FD-192（公开经验库·WorkBuddy）

```yaml
failure_id: FD-192
problem_type: 预测
domain: 电力系统/新能源
method: 忽略云量影响
failure: 云量急剧变化导致功率波动
cause: 云量急剧变化导致功率波动
signal: 短期预测不准
lesson: 需引入云量预测
avoid: 
source: 2019年电工杯数学建模竞赛A题|https://www.saikr.com/vse/DGB2019|2019
confidence: 低
```

---

## FD-193（公开经验库·WorkBuddy）

```yaml
failure_id: FD-193
problem_type: 预测
domain: 环境科学/空气污染
method: 线性回归预测
failure: 空气质量与气象因素非线性
cause: 空气质量与气象因素非线性
signal: R^2低
lesson: 需用非线性模型
avoid: 
source: 2019年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2019|2019
confidence: 低
```

---

## FD-194（公开经验库·WorkBuddy）

```yaml
failure_id: FD-194
problem_type: 预测
domain: 环境科学/空气污染
method: 忽略时间序列特征
failure: 空气质量有日/周/季节周期
cause: 空气质量有日/周/季节周期
signal: 预测不准
lesson: 需用时间序列模型
avoid: 
source: 2019年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2019|2019
confidence: 低
```

---

## FD-219（公开经验库·WorkBuddy）

```yaml
failure_id: FD-219
problem_type: 优化决策
domain: 行程调度/组合优化
method: 固定营地对所有队
failure: 容量被超引起冲突
cause: 容量被超引起冲突
signal: 行程不可行
lesson: 需动态分配
avoid: 
source: 2012 MCM Problem B: Camping along the Big Long River|https://www.contest.comap.com/undergraduate/contests/|2012
confidence: 中
```

---

## FD-220（公开经验库·WorkBuddy）

```yaml
failure_id: FD-220
problem_type: 优化决策
domain: 行程调度/组合优化
method: 忽略划行时间
failure: 当日无法抵达计划营地
cause: 当日无法抵达计划营地
signal: 行程断裂
lesson: 需行程校验
avoid: 
source: 2012 MCM Problem B: Camping along the Big Long River|https://www.contest.comap.com/undergraduate/contests/|2012
confidence: 中
```

---

## FD-221（公开经验库·WorkBuddy）

```yaml
failure_id: FD-221
problem_type: 优化决策
domain: 交通流优化/元胞自动机
method: 仅用宏观流量模型
failure: 无法刻画换道微观行为
cause: 无法刻画换道微观行为
signal: 规则影响失真
lesson: 需微观仿真
avoid: 
source: 2014 MCM Problem A: Keep-Right-Except-to-Pass Rule|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## FD-222（公开经验库·WorkBuddy）

```yaml
failure_id: FD-222
problem_type: 优化决策
domain: 交通流优化/元胞自动机
method: 忽略换道安全
failure: 频繁换道致拥堵
cause: 频繁换道致拥堵
signal: 效率估计偏高
lesson: 需安全约束
avoid: 
source: 2014 MCM Problem A: Keep-Right-Except-to-Pass Rule|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## FD-223（公开经验库·WorkBuddy）

```yaml
failure_id: FD-223
problem_type: 优化决策
domain: 交通优化/合流控制
method: 忽视合流冲突
failure: 瓶颈在合流而非收费
cause: 瓶颈在合流而非收费
signal: 优化方向错
lesson: 需定位真瓶颈
avoid: 
source: 2017 MCM Problem B: Merge After Toll|https://www.contest.comap.com/undergraduate/contests/|2017
confidence: 中
```

---

## FD-224（公开经验库·WorkBuddy）

```yaml
failure_id: FD-224
problem_type: 优化决策
domain: 交通优化/合流控制
method: 固定车道不优化
failure: 配置不匹配需求
cause: 配置不匹配需求
signal: 通行能力低
lesson: 需优化配置
avoid: 
source: 2017 MCM Problem B: Merge After Toll|https://www.contest.comap.com/undergraduate/contests/|2017
confidence: 中
```

---

## FD-225（公开经验库·WorkBuddy）

```yaml
failure_id: FD-225
problem_type: 优化决策
domain: 排队优化/服务调度
method: 固定通道数
failure: 高峰排队长
cause: 高峰排队长
signal: 等待超时
lesson: 需动态开放
avoid: 
source: 2017 ICM Problem D: Airport Checkpoint Operations|http://www.madio.net/thread-290074-1-1.html|2017
confidence: 中
```

---

## FD-226（公开经验库·WorkBuddy）

```yaml
failure_id: FD-226
problem_type: 优化决策
domain: 排队优化/服务调度
method: 忽略预检差异
failure: 服务时间被高估
cause: 服务时间被高估
signal: 通道配置过多
lesson: 需分队列建模
avoid: 
source: 2017 ICM Problem D: Airport Checkpoint Operations|http://www.madio.net/thread-290074-1-1.html|2017
confidence: 中
```

---

## FD-227（公开经验库·WorkBuddy）

```yaml
failure_id: FD-227
problem_type: 优化决策
domain: 设施选址/网络优化
method: 均匀布点
failure: 未匹配需求分布
cause: 未匹配需求分布
signal: 覆盖不足且浪费
lesson: 需需求驱动选址
avoid: 
source: 2018 MCM Problem D: Out of the Gas?|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## FD-228（公开经验库·WorkBuddy）

```yaml
failure_id: FD-228
problem_type: 优化决策
domain: 设施选址/网络优化
method: 忽略容量约束
failure: 站点过载排队
cause: 站点过载排队
signal: 服务失效
lesson: 需容量配置
avoid: 
source: 2018 MCM Problem D: Out of the Gas?|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## FD-229（公开经验库·WorkBuddy）

```yaml
failure_id: FD-229
problem_type: 优化决策
domain: 组织优化/匹配决策
method: 仅按技能最优组队
failure: 团队过大沟通成本飙升
cause: 团队过大沟通成本飙升
signal: 效率下降
lesson: 需多目标权衡
avoid: 
source: 2020 MCM Problem D: The Teaming Strategy|https://www.contest.comap.com/undergraduate/contests/|2020
confidence: 中
```

---

## FD-230（公开经验库·WorkBuddy）

```yaml
failure_id: FD-230
problem_type: 优化决策
domain: 组织优化/匹配决策
method: 忽略技能缺口
failure: 任务需求未被覆盖
cause: 任务需求未被覆盖
signal: 项目失败
lesson: 须约束覆盖
avoid: 
source: 2020 MCM Problem D: The Teaming Strategy|https://www.contest.comap.com/undergraduate/contests/|2020
confidence: 中
```

---

## FD-231（公开经验库·WorkBuddy）

```yaml
failure_id: FD-231
problem_type: 优化决策
domain: 可持续优化/决策分析
method: 单看经济收益
failure: 忽视环境社会价值
cause: 忽视环境社会价值
signal: 策略不可持续
lesson: 需三重底线
avoid: 
source: 2015 ICM Problem D: Is it smarter to be sustainable?|http://www.madio.net/thread-290074-1-1.html|2015
confidence: 中
```

---

## FD-232（公开经验库·WorkBuddy）

```yaml
failure_id: FD-232
problem_type: 优化决策
domain: 可持续优化/决策分析
method: 等权处理维度
failure: 权重不匹配战略
cause: 权重不匹配战略
signal: 方案偏离目标
lesson: 需AHP赋权
avoid: 
source: 2015 ICM Problem D: Is it smarter to be sustainable?|http://www.madio.net/thread-290074-1-1.html|2015
confidence: 中
```

---

## FD-233（公开经验库·WorkBuddy）

```yaml
failure_id: FD-233
problem_type: 优化决策
domain: 会务管理/整数规划
method: 按回执数固定预订
failure: 实际到会波动致房间不足/浪费
cause: 实际到会波动致房间不足/浪费
signal: 费用或体验差
lesson: 需应对不确定
avoid: 
source: 全国大学生数学建模竞赛2009年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2009
confidence: 中
```

---

## FD-234（公开经验库·WorkBuddy）

```yaml
failure_id: FD-234
problem_type: 优化决策
domain: 会务管理/整数规划
method: 忽略预算约束
failure: 预订超支
cause: 预订超支
signal: 方案不可行
lesson: 须加预算
avoid: 
source: 全国大学生数学建模竞赛2009年D题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2009
confidence: 中
```

---

## FD-257（公开经验库·WorkBuddy）

```yaml
failure_id: FD-257
problem_type: 评价分类
domain: 教育投资/组合评价
method: 全指标直接加权
failure: 冗余相关致权重失真
cause: 冗余相关致权重失真
signal: 评价偏颇
lesson: 需降维
avoid: 
source: 2016 MCM Problem C: The Goodgrant Challenge|https://www.contest.comap.com/undergraduate/contests/|2016
confidence: 中
```

---

## FD-258（公开经验库·WorkBuddy）

```yaml
failure_id: FD-258
problem_type: 评价分类
domain: 教育投资/组合评价
method: 仅看声誉排名
failure: 忽视投资效率与使命
cause: 忽视投资效率与使命
signal: 配置低效
lesson: 需DEA评价
avoid: 
source: 2016 MCM Problem C: The Goodgrant Challenge|https://www.contest.comap.com/undergraduate/contests/|2016
confidence: 中
```

---

## FD-259（公开经验库·WorkBuddy）

```yaml
failure_id: FD-259
problem_type: 评价分类
domain: 信息经济/成本评价
method: 仅看保护成本
failure: 忽视泄露损失
cause: 忽视泄露损失
signal: 策略失衡
lesson: 需成本效益
avoid: 
source: 2018 ICM Problem F: Cost of Privacy|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## FD-260（公开经验库·WorkBuddy）

```yaml
failure_id: FD-260
problem_type: 评价分类
domain: 信息经济/成本评价
method: 忽略用户效用
failure: 过度保护降低体验
cause: 过度保护降低体验
signal: 策略不可行
lesson: 需权衡
avoid: 
source: 2018 ICM Problem F: Cost of Privacy|https://www.contest.comap.com/undergraduate/contests/|2018
confidence: 中
```

---

## FD-261（公开经验库·WorkBuddy）

```yaml
failure_id: FD-261
problem_type: 评价分类
domain: 公共卫生/系统评价
method: 主观等权评价
failure: 忽视指标信息量差异
cause: 忽视指标信息量差异
signal: 排名偏颇
lesson: 需客观赋权
avoid: 
source: 2008 ICM Problem: Health Care System|http://www.madio.net/thread-290074-1-1.html|2008
confidence: 中
```

---

## FD-262（公开经验库·WorkBuddy）

```yaml
failure_id: FD-262
problem_type: 评价分类
domain: 公共卫生/系统评价
method: 线性加权处理
failure: 指标与绩效非线性
cause: 指标与绩效非线性
signal: 拟合差
lesson: 需非线性模型
avoid: 
source: 2008 ICM Problem: Health Care System|http://www.madio.net/thread-290074-1-1.html|2008
confidence: 中
```

---

## FD-263（公开经验库·WorkBuddy）

```yaml
failure_id: FD-263
problem_type: 评价分类
domain: 能源评价/配置分析
method: 仅看成本最低
failure: 忽视碳与环境
cause: 忽视碳与环境
signal: 方案不可持续
lesson: 需综合评价
avoid: 
source: 2009 MCM Problem B: Energy and Phones|https://www.contest.comap.com/undergraduate/contests/|2009
confidence: 中
```

---

## FD-264（公开经验库·WorkBuddy）

```yaml
failure_id: FD-264
problem_type: 评价分类
domain: 能源评价/配置分析
method: 忽视需求增长
failure: 供给不足
cause: 供给不足
signal: 方案失效
lesson: 需预测
avoid: 
source: 2009 MCM Problem B: Energy and Phones|https://www.contest.comap.com/undergraduate/contests/|2009
confidence: 中
```

---

## FD-265（公开经验库·WorkBuddy）

```yaml
failure_id: FD-265
problem_type: 评价分类
domain: 交通能源/综合评价
method: 仅看运行零排放
failure: 忽视发电与电池环节
cause: 忽视发电与电池环节
signal: 环境收益高估
lesson: 需LCA
avoid: 
source: 2011 ICM Problem: Electric Vehicles|http://www.madio.net/thread-290074-1-1.html|2011
confidence: 中
```

---

## FD-266（公开经验库·WorkBuddy）

```yaml
failure_id: FD-266
problem_type: 评价分类
domain: 交通能源/综合评价
method: 忽略电网负荷
failure: 充电峰值冲击电网
cause: 充电峰值冲击电网
signal: 评价片面
lesson: 需电网约束
avoid: 
source: 2011 ICM Problem: Electric Vehicles|http://www.madio.net/thread-290074-1-1.html|2011
confidence: 中
```

---

## FD-267（公开经验库·WorkBuddy）

```yaml
failure_id: FD-267
problem_type: 评价分类
domain: 生态评价/网络建模
method: 孤立评价各系统
failure: 忽视系统耦合
cause: 忽视系统耦合
signal: 风险低估
lesson: 需网络建模
avoid: 
source: 2013 MCM Problem C: Earth Health Network Model|https://www.contest.comap.com/undergraduate/contests/|2013
confidence: 中
```

---

## FD-268（公开经验库·WorkBuddy）

```yaml
failure_id: FD-268
problem_type: 评价分类
domain: 生态评价/网络建模
method: 等权处理指标
failure: 重要性差异被掩盖
cause: 重要性差异被掩盖
signal: 评价失真
lesson: 需赋权
avoid: 
source: 2013 MCM Problem C: Earth Health Network Model|https://www.contest.comap.com/undergraduate/contests/|2013
confidence: 中
```

---

## FD-269（公开经验库·WorkBuddy）

```yaml
failure_id: FD-269
problem_type: 评价分类
domain: 交通资源配置/评价优化
method: 均匀补贴全城
failure: 热点区域仍短缺
cause: 热点区域仍短缺
signal: 配置低效
lesson: 需定向调度
avoid: 
source: 全国大学生数学建模竞赛2015年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2015
confidence: 中
```

---

## FD-270（公开经验库·WorkBuddy）

```yaml
failure_id: FD-270
problem_type: 评价分类
domain: 交通资源配置/评价优化
method: 忽视空驶率
failure: 整体供给虚高
cause: 整体供给虚高
signal: 评价失真
lesson: 需供需比
avoid: 
source: 全国大学生数学建模竞赛2015年B题|https://www.cnblogs.com/nagiyuki77/p/17090536.html|2015
confidence: 中
```

---

## FD-271（公开经验库·WorkBuddy）

```yaml
failure_id: FD-271
problem_type: 评价分类
domain: 交通评价/拥堵评估
method: 单一速度指标
failure: 忽略延时与饱和
cause: 忽略延时与饱和
signal: 评价片面
lesson: 需多指标
avoid: 
source: 2018年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2018
confidence: 低
```

---

## FD-272（公开经验库·WorkBuddy）

```yaml
failure_id: FD-272
problem_type: 评价分类
domain: 交通评价/拥堵评估
method: 等权简单相加
failure: 指标信息量差异大
cause: 指标信息量差异大
signal: 等级失真
lesson: 需客观赋权
avoid: 
source: 2018年亚太杯数学建模竞赛A题|https://www.apmcm.org/|2018
confidence: 低
```

---

## FD-273（公开经验库·WorkBuddy）

```yaml
failure_id: FD-273
problem_type: 评价分类
domain: 物流评价/智慧化评估
method: 仅看成本低
failure: 忽视智慧化与时效
cause: 忽视智慧化与时效
signal: 方案落后
lesson: 需综合评价
avoid: 
source: 2018年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2018|2018
confidence: 低
```

---

## FD-274（公开经验库·WorkBuddy）

```yaml
failure_id: FD-274
problem_type: 评价分类
domain: 物流评价/智慧化评估
method: 硬性打分无模糊
failure: 指标边界不清
cause: 指标边界不清
signal: 评价武断
lesson: 需模糊处理
avoid: 
source: 2018年华数杯数学建模竞赛B题|https://www.saikr.com/vse/huashubei2018|2018
confidence: 低
```

---

## FD-315（公开经验库·互换）

```yaml
failure_id: FD-315
problem_type: 物理建模
domain: 复合材料微结构导电渗流与填充成本优化
method: 在问题三和问题四中全面沿用问题一的高密度三角网格实体判定
failure: 单次几何判断包含大量三角形对筛选，乘以多个填充水平和大量蒙特卡洛次数后运行时间难以接受
cause: 高保真模型的计算复杂度与实体块数、候选介质对数和三角网格面数共同增长，不适合直接嵌入大规模随机仿真
signal: 程序耗时主要集中在三角网格构造和三角形距离细筛，增加试验次数后时间近似成比例增长
lesson: 高保真模型应承担校核和机制确认，概率估计与优化阶段应使用保留关键物理机制的低成本模型
avoid: 
source: 2026年第七届“华数杯”大学生数学建模竞赛 A题《微构体中填充导电介质的仿真优化》 | 本地赛题PDF与配套代码复盘 | 2026
confidence: 高
```

---

## FD-316（公开经验库·互换）

```yaml
failure_id: FD-316
problem_type: 物理建模
domain: 复合材料微结构导电渗流与填充成本优化
method: 仅凭逻辑斯蒂曲线的90%交点给出最低填充量
failure: 拟合交点可能落在尚未通过直接概率置信下限检验的位置，连续交点转换成整数介质数量时也可能因向下取整而失去可行性
cause: 回归曲线存在模型误差和抽样误差，交点本身不是对真实导通概率约束的直接证明
signal: 拟合候选点的样本概率或Wilson下限未达到目标，或者留一法、数据来源删除后临界值发生明显移动
lesson: 拟合模型用于缩小搜索区间，最终约束必须由整数化后的候选方案和直接蒙特卡洛置信下限验证
avoid: 
source: 2026年第七届“华数杯”大学生数学建模竞赛 A题《微构体中填充导电介质的仿真优化》 | 本地赛题PDF与配套代码复盘 | 2026
confidence: 高
```

---

## FD-317（公开经验库·Kimi）

```yaml
failure_id: FD-317
problem_type: 水文分析与时间序列预测
domain: 水利工程/环境科学
method: 初期直接用简单线性回归拟合含沙量与时间的关系，忽略水位和水流量
failure: 模型R²极低，残差呈现明显结构
cause: 含沙量受多因素耦合影响，单一时间变量无法解释其变化
signal: 残差时序图呈现周期性波动，与水位变化高度相关
lesson: 水文变量多为多因素耦合结果，建模时必须纳入主要驱动因素（水位、流量），不能仅做单变量时间回归
avoid: 
source: 2023年高教社杯全国大学生数学建模竞赛E题：黄河水沙监测数据分析|https://blog.csdn.net/weixin_43970743/article/details/161108783|2023
confidence: 高
```

---

## FD-318（公开经验库·Kimi）

```yaml
failure_id: FD-318
problem_type: 博弈决策与路径优化
domain: 策略游戏/运筹优化
method: 初期用贪心算法逐日选择当前最优行动
failure: 在复杂地图中频繁陷入资源耗尽或超时失败
cause: 贪心缺乏全局视野，前期过度消耗导致后期无法应对沙暴或长距离移动
signal: 模拟中大量路径在第20-30天因资源不足而失败
lesson: 多阶段资源约束问题必须使用动态规划等全局优化方法，不能逐日贪心决策；状态空间需包含资源存量作为关键维度
avoid: 
source: 2020年高教社杯全国大学生数学建模竞赛B题：穿越沙漠|https://max.book118.com/html/2024/1119/5030301341012000.shtm|2020
confidence: 高
```

---

## FD-319（公开经验库·Kimi）

```yaml
failure_id: FD-319
problem_type: 几何反演与模式识别
domain: 精密测量/计算机视觉
method: 直接用全局多项式拟合整个轮廓
failure: 高阶多项式出现振荡，无法识别各段真实几何形状
cause: 工件轮廓为分段低阶几何（直线+圆弧），全局高阶多项式不适合分段结构
signal: 拟合曲线在圆弧与直线过渡处出现非物理波动
lesson: 分段几何必须用分段方法处理，全局拟合会丢失段间边界信息；应先识别分段类型再分别拟合
avoid: 
source: 2020年高教社杯全国大学生数学建模竞赛D题：接触式轮廓仪的自动标注|https://gitcode.csdn.net/6a20255310ee7a33f2773f47.html|2020
confidence: 高
```

---

## FD-320（公开经验库·Kimi）

```yaml
failure_id: FD-320
problem_type: 流体力学与压力控制优化
domain: 内燃机/液压控制
method: 初期忽略燃油可压缩性，假设密度为常数
failure: 压力计算结果与实际情况严重不符，无法稳定
cause: 高压下燃油密度随压力显著变化（约0.85→0.87g/cm³），不可压缩假设失效
signal: 计算压力在供油时瞬间飙升至数百MPa或跌落到接近0
lesson: 高压液压系统必须考虑流体可压缩性，压力-密度关系是建模核心；不能简单用不可压缩流体力学处理
avoid: 
source: 2019年高教社杯全国大学生数学建模竞赛A题：高压油管的压力控制|https://www.ppmy.cn/news/195212.html|2019
confidence: 高
```

---

## FD-321（公开经验库·Kimi）

```yaml
failure_id: FD-321
problem_type: 传感器校准与数据融合
domain: 环境监测/物联网
method: 初期用随机K折交叉验证评估模型
failure: 模型评估指标过于乐观，实际部署后精度显著下降
cause: 时序数据存在自相关，随机划分使训练集包含未来信息，导致过拟合
signal: 测试集R²高达0.95，但滑动窗口验证R²仅0.75
lesson: 时序数据必须采用时间前后划分或滑动窗口验证，严禁随机打乱；这是时序建模的基本准则
avoid: 
source: 2019年高教社杯全国大学生数学建模竞赛D题：空气质量数据的校准|https://gitcode.csdn.net/6a200938662f9a54cb792c0f.html|2019
confidence: 高
```

---

## FD-322（公开经验库·Kimi）

```yaml
failure_id: FD-322
problem_type: 热传导与多层材料优化
domain: 职业防护/热工学
method: 初期忽略界面热阻，假设各层理想接触
failure: 模型预测温度与实测数据偏差超过5°C，无法通过参数校验
cause: 实际层间存在空气间隙与接触不完全，界面热阻显著影响传热
signal: 即使调整导热系数，模型仍无法同时拟合初始段与稳态段温度曲线
lesson: 多层材料热传导必须考虑界面热阻，理想接触假设在工程实际中通常不成立；未知参数应通过实验数据反演识别而非随意假设
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛A题：高温作业专用服装设计|https://blog.csdn.net/weixin_43970743/article/details/161520460|2018
confidence: 高
```

---

## FD-323（公开经验库·Kimi）

```yaml
failure_id: FD-323
problem_type: 刚体力学与协同控制优化
domain: 体育竞技/团队协作
method: 初期将同心鼓简化为质点，仅考虑竖直方向运动
failure: 无法解释鼓面倾斜现象，非理想工况下模型完全失效
cause: 同心鼓有有限尺寸（直径40cm），不同位置受力不均必然产生力矩导致转动，质点模型丢失转动自由度
signal: 计算显示即使队员发力有微小差异，鼓仍保持竖直运动，与实际情况矛盾
lesson: 具有空间尺寸的刚体运动必须用刚体动力学（平动+转动）建模，不能简化为质点；力矩与转动惯量是分析倾斜的核心
avoid: 
source: 2019年高教社杯全国大学生数学建模竞赛B题：同心协力策略研究|https://blog.csdn.net/2401_82505179/article/details/142747597|2019
confidence: 高
```

---

## FD-324（公开经验库·Kimi）

```yaml
failure_id: FD-324
problem_type: 排队论与收益优化
domain: 交通运输/运营管理
method: 初期仅考虑等待时间忽略收益结构（长短途差异）
failure: 模型建议司机总是排队，无法解释实际中部分司机选择空返的现象
cause: 未考虑短途载客导致收益损失这一关键因素，排队对短途司机可能非最优
signal: 模型预测所有司机都应排队，与实际观察到的空返行为矛盾
lesson: 出租车机场决策的核心是收益而非单纯时间；必须显式建模长短途收益差异，否则模型无法解释实际行为
avoid: 
source: 2019年高教社杯全国大学生数学建模竞赛C题：机场的出租车问题|https://www.toymoban.com/blog/675072.html|2019
confidence: 高
```

---

## FD-325（公开经验库·Kimi）

```yaml
failure_id: FD-325
problem_type: 零售数据分析与定价策略
domain: 商业分析/经济学
method: 初期忽略成本价缺失问题，直接用售价作为成本计算利润率
failure: 利润率计算结果普遍超过100%，明显不合理
cause: 未处理缺失数据，将售价误作成本导致利润虚高
signal: 大量日期利润率超过80%，远超零售业正常水平
lesson: 数据缺失是零售分析的常见问题，必须通过合理假设（行业平均利润率反推）或模型（如EM算法）处理，不能忽略或随意填充
avoid: 
source: 2019年高教社杯全国大学生数学建模竞赛E题：薄利多销分析|https://blog.csdn.net/2403_87108415/article/details/149207364|2019
confidence: 高
```

---

## FD-326（公开经验库·Kimi）

```yaml
failure_id: FD-326
problem_type: 客户价值分析与关联挖掘
domain: 零售管理/数据挖掘
method: 初期直接用消费金额单一指标划分会员价值
failure: 高消费低频会员与低消费高频会员被混为一谈，营销策略失效
cause: 单一指标无法全面反映客户价值，忽略消费频率与最近活跃度
signal: 某会员消费金额高但已一年未消费，仍被划分为高价值客户
lesson: 客户价值分析必须采用多维度综合模型（如RFM/RFMT），单一指标（如消费金额）会严重误判客户状态；维度选择应结合业务场景（高端商场加T指标）
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛C题：大型百货商场会员画像描绘|https://damodev.csdn.net/6889c366bb9d8e0ecec3e417.html|2018
confidence: 高
```

---

## FD-327（公开经验库·混元）

```yaml
failure_id: FD-327
problem_type: 优化决策
domain: 公共安全/警务调度
method: 简单重心法
failure: 部分偏远区域出警超时
cause: 未考虑路网实际拓扑结构
signal: 最大出警时间超出阈值
lesson: 空间聚类需结合路网距离而非欧氏距离
avoid: 
source: 2011年全国大学生数学建模B题优秀论文|https://doc.xuehai.net/b835340c48a00378980807b7c.html|2011
confidence: 高
```

---

## FD-328（公开经验库·混元）

```yaml
failure_id: FD-328
problem_type: 预测
domain: 传染病控制
method: 经典SIR模型
failure: 预测高峰时间偏差较大
cause: 忽略潜伏期长
signal: 拟合优度低
lesson: 对潜伏期长的疾病必须细分仓室
avoid: 
source: 2015 MCM Outstanding Papers: Eradicating Ebola|http://www.hanlin.com/archives/85459|2015
confidence: 高
```

---

## FD-329（公开经验库·混元）

```yaml
failure_id: FD-329
problem_type: 评价分类
domain: 食品科学/统计分析
method: 简单算术平均评分
failure: 无法区分优质与一级葡萄
cause: 未剔除异常评酒员数据
signal: 分级结果与专家判断相悖
lesson: 预处理需剔除不一致评分
avoid: 
source: 2012国赛A题优秀论文|https://doc.xuehai.net/bc46036d3588eff46e760df6d.html|2012
confidence: 高
```

---

## FD-330（公开经验库·混元）

```yaml
failure_id: FD-330
problem_type: 评价分类
domain: 交通规划
method: 仅用平均车速评价
failure: 误判部分小区开放效果
cause: 忽略交叉口延误与绕行
signal: 评价结果与仿真不一致
lesson: 道路通行需多指标综合
avoid: 
source: 2016年全国数学建模竞赛B题一等奖论文|https://www.bodocs.net/doc/4520055488.html|2016
confidence: 高
```

---

## FD-331（公开经验库·混元）

```yaml
failure_id: FD-331
problem_type: 优化决策
domain: 航天垃圾治理
method: 按碎片数量均匀清除
failure: 成本收益比低
cause: 忽略高风险碎片连锁效应
signal: 清除后风险下降有限
lesson: 应优先处理高碰撞概率目标
avoid: 
source: 2016 MCM特等奖Outstanding论文B题下载-Space Junk|https://www.hanlin.com/archives/category/bonus/documents/page/49/|2016
confidence: 高
```

---

## FD-332（公开经验库·混元）

```yaml
failure_id: FD-332
problem_type: 优化决策
domain: 电力系统/交通规划
method: 单纯重心法选址
failure: 部分站点过载
cause: 未考虑路网阻隔与交叉口延误
signal: 排队长度超阈值
lesson: 交通阻抗须纳入选址模型
avoid: 
source: 2016电工杯数学建模竞赛论文|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2016
confidence: 中
```

---

## FD-333（公开经验库·混元）

```yaml
failure_id: FD-333
problem_type: 优化决策
domain: 运筹优化/游戏策略
method: 只考虑直奔终点
failure: 错过挖矿收益或陷入资源缺口
cause: 未权衡村庄矿山补给
signal: 剩余资金非最优
lesson: 应联合路径、补给与挖矿决策
avoid: 
source: CUMCM2020-Desert-Game 全国一等奖论文源码|https://www.github.com/seanys/CUMCM2020-Desert-Game|2020
confidence: 高
```

---

## FD-334（公开经验库·混元）

```yaml
failure_id: FD-334
problem_type: 物理建模
domain: 工业图像分析
method: 仅用像素面积近似质量
failure: 速率估计偏差大
cause: 忽略三维形态变化
signal: 与物理趋势不一致
lesson: 二维图像需结合几何映射
avoid: 
source: 亚太地区数学建模优秀论文_2019年第九届APMCM A题|https://blog.csdn.net/weixin_39580749/article/details/110816724|2019
confidence: 中
```

---

## FD-335（公开经验库·混元）

```yaml
failure_id: FD-335
problem_type: 优化决策
domain: 智能交通
method: 孤立交叉口最优配时
failure: 干线方向排队反而增长
cause: 相邻路口相位未同步
signal: 带宽利用率偏低
lesson: 必须系统性协同而非局部最优
avoid: 
source: 2017 MCM特等奖Outstanding论文C题下载-Cooperate and Navigate|http://www.hanlin.com/archives/84719|2017
confidence: 高
```

---

## FD-336（公开经验库·混元）

```yaml
failure_id: FD-336
problem_type: 优化决策
domain: 智能制造
method: 固定循环顺序不考虑工序分配
failure: 双工序下效率下降
cause: CNC工序布局未优化
signal: 成品数低于候选方案
lesson: 双工序须联合优化设备布局与顺序
avoid: 
source: 智能RGV的动态调度策略|https://publish.cnki.net/journal/portal/stdx/client/paper/5a488777c0246c392ca31fa4b5cda6b9|2018
confidence: 高
```

---

## FD-337（公开经验库·Kimi）

```yaml
failure_id: FD-337
problem_type: 图像重建与参数标定
domain: 医学影像/CT成像
method: 直接用反投影法重建而不加滤波
failure: 重建图像出现严重的星状伪影，吸收率值失真
cause: 反投影将投影数据均匀回抹到所有经过该点的射线上，导致高频成分被过度放大
signal: 重建图像中明显可见从高密度区域发出的放射状亮线
lesson: 解析重建必须使用滤波反投影(FBP)或迭代算法，不能直接用未滤波的反投影；滤波器设计是重建质量的关键
avoid: 
source: 2017年高教社杯全国大学生数学建模竞赛A题：CT系统参数标定及成像|https://blog.csdn.net/weixin_43292788/article/details/142355315|2017
confidence: 高
```

---

## FD-338（公开经验库·Kimi）

```yaml
failure_id: FD-338
problem_type: 定价优化与任务分配
domain: 互联网平台经济/地理信息系统
method: 初期忽略地理位置因素，仅用任务标价与完成率做简单相关分析
failure: 无法解释为什么相同定价在不同区域完成率差异巨大
cause: 未考虑空间维度，任务完成率受周边会员密度与竞争程度影响，非单纯价格因素
signal: 深圳平均定价低导致完成度低，而佛山定价高完成度反而高
lesson: 地理空间因素是平台经济建模的核心变量，必须将会员分布、距离、区域竞争等空间信息纳入模型，不能仅做价格-完成率的二维分析
avoid: 
source: 2017年高教社杯全国大学生数学建模竞赛B题：'拍照赚钱'的任务定价|https://github.com/Henryers/PhotoPricingModel|2017
confidence: 高
```

---

## FD-339（公开经验库·Kimi）

```yaml
failure_id: FD-339
problem_type: 化学计量学与回归分析
domain: 分析化学/颜色科学
method: 初期对所有5种物质统一使用RGB多元线性回归
failure: 硫酸铝钾和奶中尿素拟合效果极差，R²接近0
cause: 不同物质显色机理不同，浓度-颜色关系并非都是线性；硫酸铝钾存在饱和效应，奶中尿素颜色变化微弱
signal: 残差图呈现明显非线性结构，预测值出现负浓度
lesson: 多物质化学计量建模必须分类处理，不能一刀切；应先做EDA（散点图）识别关系类型（线性/饱和/指数），再选择对应模型；强行统一模型会导致部分物质完全失效
avoid: 
source: 2017年高教社杯全国大学生数学建模竞赛C题：颜色与物质浓度辨识|https://blog.csdn.net/weixin_43970743/article/details/161520390|2017
confidence: 高
```

---

## FD-340（公开经验库·Kimi）

```yaml
failure_id: FD-340
problem_type: 路径优化与排班调度
domain: 工业安全/运筹优化
method: 初期将短周期点（35min）与长周期点混为同一条线路
failure: 线路周期严重超标，无法满足短周期点约束
cause: 短周期点需高频巡检，长周期点可低频，混排导致短周期点被延误
signal: 计算得某线路周期达120min，远超35min限制
lesson: 多周期巡检问题必须按周期分层处理，短周期点优先安排独立高频线路，长周期点可合并低频线路；分区策略应基于周期相似性而非单纯地理位置
avoid: 
source: 2017年高教社杯全国大学生数学建模竞赛D题：巡检线路的排班|https://blog.csdn.net/weixin_43970743/article/details/161520407|2017
confidence: 高
```

---

## FD-341（公开经验库·Kimi）

```yaml
failure_id: FD-341
problem_type: 多体静力学与多目标优化
domain: 海洋工程/系泊设计
method: 初期忽略锚链着地现象，假设锚链完全悬空
failure: 风速较低时计算锚链长度不足，锚链张力异常偏大
cause: 实际锚链较长时部分躺在海床上，着地部分不提供竖直支撑力，完全悬空假设导致几何约束错误
signal: 计算得锚点拉力方向与海床夹角为负值（指向海床下方），物理上不可能
lesson: 系泊系统建模必须考虑锚链着地的可能性，当链长超过悬空所需长度时，必须分段处理（着地部分+悬空部分）；几何约束是力学模型的基础，不能忽略
avoid: 
source: 2016年高教社杯全国大学生数学建模竞赛A题：系泊系统的设计|https://blog.csdn.net/weixin_43970743/article/details/161519114|2016
confidence: 高
```

---

## FD-342（公开经验库·Kimi）

```yaml
failure_id: FD-342
problem_type: 交通影响评价与仿真
domain: 城市规划/交通工程
method: 初期仅用宏观交通流模型（如LWR）分析小区开放影响
failure: 无法解释小区开放后局部交叉口拥堵加剧的现象
cause: 宏观模型忽略车辆微观交互（如换道、排队），而小区开放新增的出入口正是微观瓶颈
signal: 宏观模型预测通行能力提升，但实际仿真中部分交叉口饱和度超过0.9
lesson: 交通影响评价需微观-宏观结合：宏观模型评估整体容量变化，微观仿真（元胞自动机/排队论）识别局部瓶颈；仅用一种尺度模型可能遗漏关键问题
avoid: 
source: 2016年高教社杯全国大学生数学建模竞赛B题：小区开放对道路通行的影响|https://blog.csdn.net/weixin_43970743/article/details/161520008|2016
confidence: 高
```

---

## FD-343（公开经验库·Kimi）

```yaml
failure_id: FD-343
problem_type: 天文定位与参数反演
domain: 天文测量/地理信息
method: 初期直接用梯度下降法优化目标函数（理论影长与实际影长误差）
failure: 收敛到局部最优，定位结果偏离中国范围或日期不合理
cause: 目标函数非凸，存在多个局部极小值，梯度下降对初值敏感
signal: 优化结果纬度为负（南半球）或日期为冬季但影子极短（夏季特征）
lesson: 多参数非线性反演问题必须采用全局优化方法（遍历搜索、粒子群、遗传算法），不能依赖梯度下降；遍历搜索虽慢但可靠，PSO可在效率与全局性间平衡
avoid: 
source: 2015年高教社杯全国大学生数学建模竞赛A题：太阳影子定位|https://blog.csdn.net/qq_73954832/article/details/140455963|2015
confidence: 高
```

---

## FD-344（公开经验库·Kimi）

```yaml
failure_id: FD-344
problem_type: 供需匹配与动态定价
domain: 共享经济/交通运营
method: 初期仅按订单量对比补贴前后效果，忽略司机拒单和乘客拼车行为
failure: 高估补贴效果，模型预测补贴后打车难度降为0（完全解决）
cause: 未考虑供给侧的结构性行为变化，司机可能因补贴不足仍拒单，或补贴过度导致空驶增加
signal: 仿真中补贴金额超过一定阈值后匹配率反而下降
lesson: 共享经济供需分析必须同时考虑需求侧（乘客）和供给侧（司机）的行为响应，Logit等离散选择模型可刻画这种非线性响应；单纯线性分析会严重偏差
avoid: 
source: 2015年高教社杯全国大学生数学建模竞赛B题：互联网+时代的出租车资源配置|https://blog.csdn.net/weixin_43292788/article/details/142518644|2015
confidence: 高
```

---

## FD-345（公开经验库·Kimi）

```yaml
failure_id: FD-345
problem_type: 动态调度与路径优化
domain: 智能制造/仓储物流
method: 初期直接用固定顺序（如按CNC编号顺序）调度RGV
failure: 总完工时间远超理论下限，部分CNC长时间等待
cause: 固定顺序未考虑CNC加工时间差异和RGV行程，导致RGV频繁空驶或CNC等待
signal: 仿真中RGV空驶时间占比超过40%
lesson: RGV调度必须采用动态优先级策略（如最早截止期、最短加工时间优先），固定顺序在异步加工系统中效率极低；实时调度需根据系统状态动态调整
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛B题：智能RGV的动态调度策略|https://blog.csdn.net/gitblog_06777/article/details/148274765|2018
confidence: 中
```

---

## FD-346（公开经验库·Kimi）

```yaml
failure_id: FD-346
problem_type: 体育数据分析与势头量化
domain: 竞技体育/数据科学
method: 初期仅用连续得分次数作为势头指标
failure: 无法解释为什么某选手连续得分但势头得分反而下降
cause: 连续得分忽略了对手机会和比赛关键性（如破发点vs普通分），未考虑发球优势、击球质量等深层因素
signal: 某选手连续赢得3个普通发球局，但势头得分低于对手赢得1个破发点
lesson: 体育竞技中的'势头'是多维复合概念，不能简化为单一指标（如连胜次数）；必须建立综合评估体系，涵盖技术、战术、心理多个维度，PCA-TOPSIS等综合评价方法更适合
avoid: 
source: 2024年美国大学生数学建模竞赛MCM C题：网球运动中的势头|https://arxiv.org/pdf/2402.12149.pdf|2024
confidence: 高
```

---

## FD-347（公开经验库·混元）

```yaml
failure_id: FD-347
problem_type: 优化决策
domain: 芯片设计/运筹优化
method: 仅网格遍历所有尺寸
failure: 计算成本高且易漏连续最优
cause: 搜索空间离散过粗
signal: 结果不稳定
lesson: 应先降维再局部精细搜索
avoid: 
source: 2022华数杯数学建模A题环形振荡器的优化设计|https://www.bianchengbaodian.com/article/0d58bb48fc221cff4020253d3ae6e732.html|2022
confidence: 中
```

---

## FD-348（公开经验库·混元）

```yaml
failure_id: FD-348
problem_type: 评价分类
domain: 交通工程
method: 单车道宏观公式直接外推
failure: 重交通下排队与变道效应失真
cause: 忽略车道交互
signal: 预测流量偏差
lesson: 多车道问题需微观或中观仿真
avoid: 
source: 2014 MCM特等奖Outstanding论文A题下载-The Keep-Right-Except-To-Pass Rule|http://www.hanlin.com/archives/85463|2014
confidence: 高
```

---

## FD-349（公开经验库·混元）

```yaml
failure_id: FD-349
problem_type: 预测
domain: 城市交通
method: 假设事故期间通行能力恒定
failure: 低估拥堵演化
cause: 忽略恢复阶段波动
signal: 排队长度偏差
lesson: 通行能力应时间分段建模
avoid: 
source: 2013年国赛一等奖优秀论文A题车道被占用对城市道路通行能力的影响|https://m.renrendoc.com/p-85829993.html|2013
confidence: 高
```

---

## FD-350（公开经验库·混元）

```yaml
failure_id: FD-350
problem_type: 评价分类
domain: 供应链管理
method: 等权重主观打分
failure: 重要供应商排序不稳定
cause: 未结合缺货后果
signal: 前列供应商波动
lesson: 权重应由缺货风险校准
avoid: 
source: 2021年全国大学生数学建模竞赛题目C:生产企业原材料的订购与运输优秀论文范例|https://max.book118.com/html/2022/0816/5123202041004323.shtm|2021
confidence: 高
```

---

## FD-351（公开经验库·混元）

```yaml
failure_id: FD-351
problem_type: 优化决策
domain: 天文工程
method: 均匀调整所有促动器
failure: 局部面板应力与误差增大
cause: 忽略相邻面板协调
signal: 接收比未提升
lesson: 调节需全局协调而非局部补偿
avoid: 
source: 2021年数模国赛题目优秀论文|https://download.csdn.net/download/weixin_67798981/88778695|2021
confidence: 高
```

---

## FD-352（公开经验库·混元）

```yaml
failure_id: FD-352
problem_type: 预测
domain: 化工建模
method: 仅用线性回归
failure: 高温度下选择性拟合差
cause: 非线性过强
signal: R²不足
lesson: 应先做模型比较再定结构
avoid: 
source: 开源一份2021年数学建模国赛B题全国二等奖的完整论文|https://juejin.cn/post/7083785524917305380|2021
confidence: 中
```

---

## FD-353（公开经验库·混元）

```yaml
failure_id: FD-353
problem_type: 预测
domain: 水资源管理
method: 只按缺水总量排名
failure: 忽略水质与输送成本
cause: 指标单一
signal: 方案不可行
lesson: 水资源问题必须多维评价
avoid: 
source: 2013 MCM特等奖Outstanding论文B题下载-Water, Water, Everywhere|https://www.hanlin.com/archives/category/bonus/documents/page/48|2013
confidence: 高
```

---

## FD-354（公开经验库·混元）

```yaml
failure_id: FD-354
problem_type: 优化决策
domain: 电力系统
method: 直接遗传算法求解强约束
failure: 结果波动且偶发不守恒
cause: 随机变异难满足等式
signal: 成本每次不同
lesson: 强等式约束优先精确建模
avoid: 
source: 全国大学生电工数学建模竞赛|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2018
confidence: 中
```

---

## FD-355（公开经验库·混元）

```yaml
failure_id: FD-355
problem_type: 优化决策
domain: 场地规划
method: CAD画几种固定排布
failure: 容量与可达性论证弱
cause: 缺少运动学证明
signal: 评审认可度低
lesson: 开放设计题需量化几何约束
avoid: 
source: 全国大学生电工数学建模竞赛|https://github.com/yc1ggsddu/Math-Model-and-Machine-Learning|2019
confidence: 中
```

---

## FD-356（公开经验库·混元）

```yaml
failure_id: FD-356
problem_type: 优化决策
domain: 制造排程
method: 忽略组件提前一天入库
failure: 装配日物料不足
cause: 只优化最终产品
signal: 计划不可执行
lesson: 多层BOM必须向前展开物料期量
avoid: 
source: 2022华数杯|https://blog.csdn.net/weixin_43292788/category_11968618.html|2022
confidence: 中
```

---

## FD-357（公开经验库·Kimi）

```yaml
failure_id: FD-357
problem_type: 数据挖掘与管网优化
domain: 智慧校园/水务管理
method: 初期直接用单表时序异常检测，忽略水表层级关系
failure: 大量误报，将正常用水波动误判为漏损
cause: 未利用层级平衡约束，单表波动可能由下游用水引起而非漏损
signal: 某宿舍区水表读数突增，实际为该区域新建浴室投入使用
lesson: 管网分析必须利用拓扑层级关系做水量平衡校验，单表异常检测在管网系统中不可靠；层级约束是漏损识别的核心依据
avoid: 
source: 2020年高教社杯全国大学生数学建模竞赛E题：校园供水系统智能管理|https://blog.csdn.net/weixin_43292788/article/details/144255198|2020
confidence: 高
```

---

## FD-358（公开经验库·Kimi）

```yaml
failure_id: FD-358
problem_type: 组合优化与生产调度
domain: 汽车制造/工业工程
method: 初期尝试用单一整数规划同时优化所有五维属性
failure: 模型规模过大，Lingo求解时间超过24小时无法收敛
cause: 460辆车×5种属性×复杂约束，变量数达数千，组合爆炸
signal: Lingo运行数小时后仍无可行解
lesson: 超复杂组合优化问题必须分解或分层处理，序贯算法、分解协调或启发式规则是工业规模问题的唯一可行路径；不能盲目追求全局最优而忽视计算可行性
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛D题：汽车总装线的配置问题|https://jishuzhan.net/article/1836921021442035713|2018
confidence: 高
```

---

## FD-359（公开经验库·Kimi）

```yaml
failure_id: FD-359
problem_type: 曲线拟合与参数预测
domain: 电化学/电池管理
method: 初期直接用高阶多项式拟合整个放电曲线（不分段）
failure: 高阶多项式在波动段出现剧烈振荡，稳定段反而拟合不足
cause: 放电曲线前后特征差异大（前波动后平缓），全局高阶多项式无法兼顾两种形态
signal: 拟合曲线在初始段出现非物理的上下波动，残差分布不均
lesson: 曲线形态发生显著变化时（如拐点前后），必须采用分段建模策略，分别选择适合的函数形式；全局拟合会牺牲局部精度
avoid: 
source: 2016年高教社杯全国大学生数学建模竞赛C题：电池剩余放电时间预测|https://www.ppmy.cn/embedded/119988.html|2016
confidence: 高
```

---

## FD-360（公开经验库·Kimi）

```yaml
failure_id: FD-360
problem_type: 轨道力学与最优控制
domain: 航天工程/深空探测
method: 初期尝试用庞特里亚金极大值原理解析求解最优控制
failure: 协态方程与状态方程强耦合，解析解无法求得
cause: 月球软着陆涉及质量变化（燃料消耗）、推力方向控制、三维运动，极大值原理给出的两点边值问题过于复杂
signal: 协态变量初值无法确定，数值迭代不收敛
lesson: 复杂最优控制问题应优先采用直接法（离散化+数值优化）而非间接法（极大值原理）；直接法将控制问题转化为非线性规划，更易求解且鲁棒性更强
avoid: 
source: 2014年高教社杯全国大学生数学建模竞赛A题：嫦娥三号软着陆轨道设计与控制策略|https://blog.csdn.net/weixin_43970743/article/details/161518779|2014
confidence: 高
```

---

## FD-361（公开经验库·Kimi）

```yaml
failure_id: FD-361
problem_type: 几何建模与结构优化
domain: 家具设计/机械工程
method: 初期将折叠桌运动建模为简单平面四杆机构
failure: 无法描述各木条独立的圆周运动与不同开槽深度
cause: 折叠桌每组木条数量多，各木条运动半径不同，简单四杆机构仅适用于两杆系统
signal: 计算得中间木条运动轨迹与外侧木条冲突，无法平滑折叠
lesson: 多杆联动机构必须用逐杆几何分析，建立每根木条独立的运动学方程；简单机构类比在多自由度系统中失效
avoid: 
source: 2014年高教社杯全国大学生数学建模竞赛B题：创意平板折叠桌|https://jishuzhan.net/article/1845398393514364929|2014
confidence: 高
```

---

## FD-362（公开经验库·Kimi）

```yaml
failure_id: FD-362
problem_type: 交通流分析与排队预测
domain: 交通工程/应急管理
method: 初期仅用宏观排队论M/M/1模型估算排队时间
failure: 估算结果与视频实际严重不符，未考虑信号灯周期性中断
cause: M/M/1假设连续稳定到达与服务，实际城市道路有信号灯控制，车辆到达为间断性 batch arrival
signal: 理论排队时间约5分钟，实际视频显示约8分钟，且排队曲线呈周期性波动
lesson: 城市道路排队分析必须考虑信号控制影响，宏观排队模型仅适用于连续流（如高速公路）；有信号灯的路段需用元胞自动机或考虑信号周期的改进排队模型
avoid: 
source: 2013年高教社杯全国大学生数学建模竞赛A题：车道被占用对城市道路通行能力的影响|https://blog.csdn.net/weixin_43292788/article/details/142876944|2013
confidence: 高
```

---

## FD-363（公开经验库·Kimi）

```yaml
failure_id: FD-363
problem_type: 统计分析与品质评价
domain: 食品科学/感官评价
method: 初期直接对所有理化指标做简单相关分析，未考虑指标间多重共线性
failure: 回归模型系数不稳定，甚至出现与常识相反的符号（如酸度与品质正相关）
cause: 理化指标间高度相关（如糖度与密度），简单回归导致多重共线性
signal: 回归系数标准误极大，VIF值超过10
lesson: 多指标回归分析必须先检验多重共线性，必要时采用PCA降维、岭回归或逐步回归；不能直接将所有指标放入回归模型
avoid: 
source: 2012年高教社杯全国大学生数学建模竞赛A题：葡萄酒的评价|https://blog.51cto.com/u_16213621/12369495|2012
confidence: 高
```

---

## FD-364（公开经验库·Kimi）

```yaml
failure_id: FD-364
problem_type: 环境评价与污染溯源
domain: 环境科学/地质学
method: 初期仅按重金属浓度最高值直接定位污染源
failure: 定位结果与已知工业分布不符，部分高浓度点为历史遗留而非当前污染源
cause: 浓度高值可能受地形、土壤类型等自然因素影响，非单纯人为污染；且污染物可远距离迁移
signal: 某山区采样点浓度极高，但周边无工业活动
lesson: 污染溯源不能仅依赖浓度极值，必须结合污染物传播机理（扩散、对流、吸附）建立反演模型，同时考虑自然背景值和地质条件；机理模型+统计验证是环境溯源的标准方法
avoid: 
source: 2011年高教社杯全国大学生数学建模竞赛A题：城市表层土壤重金属污染分析|https://blog.csdn.net/weixin_43292788/article/details/142920057|2011
confidence: 高
```

---

## FD-365（公开经验库·Kimi）

```yaml
failure_id: FD-365
problem_type: 图像拼接与模式识别
domain: 文档修复/计算机视觉
method: 初期直接用全局遗传算法做2D碎片拼接
failure: 209块碎片的全局排列组合规模巨大，遗传算法数小时无法收敛
cause: 2D碎片拼接是排列组合问题，209!的搜索空间远超任何优化算法的处理能力
signal: 运行数小时后最优个体适应度仍极低，拼接结果完全不可读
lesson: 大规模组合问题必须分解降维，行列分离、分块处理、层次化拼接是处理大规模碎片复原的唯一可行策略；不能盲目使用全局优化算法
avoid: 
source: 2013年高教社杯全国大学生数学建模竞赛B题：碎纸片的拼接复原|https://blog.csdn.net/weixin_43970743/article/details/161518701|2013
confidence: 高
```

---

## FD-366（公开经验库·Kimi）

```yaml
failure_id: FD-366
problem_type: 几何体积计算与参数反演
domain: 计量工程/储运管理
method: 初期尝试用统一的三重积分公式计算变位后储油量，未分类讨论
failure: 积分限确定困难，不同油位高度下积分区域形态变化导致公式失效
cause: 变位后油面与罐体各表面（底、顶、侧壁）的交线随油位变化，几何边界不固定，统一公式无法覆盖所有情况
signal: 某些油位高度下计算结果为负体积或超出物理上限
lesson: 复杂几何体的体积计算必须根据边界变化进行分类讨论，每类建立独立的积分公式；统一公式在边界条件变化时必然失效，分类是工程数学的常用策略
avoid: 
source: 2010年高教社杯全国大学生数学建模竞赛A题：储油罐的变位识别与罐容表标定|https://blog.csdn.net/weixin_43292788/article/details/142970050|2010
confidence: 高
```

---

## FD-367（公开经验库·Kimi）

```yaml
failure_id: FD-367
problem_type: 排队论与调度优化
domain: 医疗服务/运营管理
method: 初期仅按FCFS规则简单模拟，未考虑手术时间窗口约束
failure: 大量白内障病人过早入院，占用床位长达5-7天才手术，导致其他病人排队剧增
cause: FCFS忽略不同病种的最佳入院时间差异，白内障病人若周三入院，需等到下周一才能手术，床位浪费严重
signal: 模拟中白内障病人平均住院天数远超术后观察时间，术前等待占比过大
lesson: 医疗调度必须考虑治疗流程的时间窗口约束（如手术日），不能简单按到达顺序服务；引入时延或预约机制是医疗排队的关键改进
avoid: 
source: 2009年高教社杯全国大学生数学建模竞赛B题：眼科病床的合理安排|https://blog.csdn.net/weixin_43292788/article/details/143105580|2009
confidence: 高
```

---

## FD-368（公开经验库·Kimi）

```yaml
failure_id: FD-368
problem_type: 计算机视觉与几何标定
domain: 摄影测量/计算机视觉
method: 初期直接用椭圆几何中心作为圆心的像坐标
failure: 标定误差大，无法满足高精度定位要求
cause: 透视投影下圆的像为椭圆，但椭圆中心并非圆心的像（存在偏心差），尤其在倾斜拍摄时误差显著
signal: 标定得到的相机参数与真实值偏差超过5%
lesson: 透视投影下不能简单用椭圆中心代替圆心像坐标，必须利用射影几何不变量（如交比）或切线性质精确定位；这是计算机视觉标定的基本原理
avoid: 
source: 2008年高教社杯全国大学生数学建模竞赛A题：数码相机定位|https://blog.csdn.net/weixin_43970743/article/details/161517516|2008
confidence: 高
```

---

## FD-369（公开经验库·Kimi）

```yaml
failure_id: FD-369
problem_type: 教育经济学与定价模型
domain: 公共政策/教育经济
method: 初期仅用简单成本加成法（培养成本×固定比例）计算学费
failure: 计算结果与实际情况严重偏离，部分专业学费过高或过低
cause: 未考虑家庭支付能力差异和专业外部性，成本加成法忽略了需求侧因素
signal: 某热门专业学费按成本加成计算仅为实际学费的30%，而某基础学科学费却超出家庭承受能力
lesson: 教育定价不能仅用成本导向，必须考虑支付能力、社会收益、市场结构等多维因素；拉姆齐定价或博弈模型比简单成本加成更适合公共品定价
avoid: 
source: 2008年高教社杯全国大学生数学建模竞赛B题：高等教育学费标准探讨|https://sx.xxu.edu.cn/info/1035/1357.htm|2008
confidence: 中
```

---

## FD-370（公开经验库·Kimi）

```yaml
failure_id: FD-370
problem_type: 人口预测与动态建模
domain: 人口学/社会统计
method: 初期直接用简单Logistic模型拟合总人口
failure: 无法反映人口结构变化（老龄化、性别比），长期预测严重偏离
cause: Logistic模型仅描述总量S型增长，完全忽略年龄结构、生育模式等内部动态
signal: 预测得老龄化率远低于实际，性别比恒定为正常水平
lesson: 人口预测不能仅用总量模型，必须建立年龄结构模型（如Leslie矩阵）；结构变化（老龄化、性别比）是人口问题的核心，总量模型完全丢失这些信息
avoid: 
source: 2007年高教社杯全国大学生数学建模竞赛A题：中国人口增长预测|https://blog.csdn.net/weixin_43970743/article/details/161517385|2007
confidence: 高
```

---

## FD-371（公开经验库·Kimi）

```yaml
failure_id: FD-371
problem_type: 图论最短路径与多目标优化
domain: 智能交通/公交系统
method: 初期直接用Floyd算法计算全源最短路径
failure: 内存占用过大，无法处理大规模公交网络（数千站点、数百线路）
cause: Floyd算法时间复杂度O(n³)，空间复杂度O(n²)，对大规模图不可行
signal: 程序运行数小时后内存溢出，无法输出结果
lesson: 大规模图最短路径问题必须采用单源算法（Dijkstra、BFS）或分层策略，不能直接用全源算法；预建索引（如直达数据库）是实际系统的标准做法
avoid: 
source: 2007年高教社杯全国大学生数学建模竞赛B题：乘公交，看奥运|https://www.docin.com/p-557988980.html|2007
confidence: 高
```

---

## FD-372（公开经验库·Kimi）

```yaml
failure_id: FD-372
problem_type: 资源配置与多目标优化
domain: 出版业/供应链管理
method: 初期仅按历史销售额比例分配书号
failure: 新兴强势分社得不到足够支持，长期市场份额下滑
cause: 简单比例分配忽略了市场趋势和战略发展，仅反映过去而非未来潜力
signal: 某分社近年满意度持续上升但分配书号反而下降
lesson: 资源配置不能仅按历史业绩平均分配，必须建立综合评价体系（如强势系数）识别潜力分社，多目标优化平衡短期利润与长期发展
avoid: 
source: 2006年高教社杯全国大学生数学建模竞赛A题：出版社的资源配置|https://blog.csdn.net/getusushu/article/details/132582371|2006
confidence: 高
```

---

## FD-373（公开经验库·Kimi）

```yaml
failure_id: FD-373
problem_type: 纵向数据分析与疗效评价
domain: 临床医学/生物统计
method: 初期忽略纵向数据的重复测量特性，将每个时间点的测量视为独立样本做简单回归
failure: 模型拟合效果差，预测误差大，且无法解释个体间差异
cause: 同一病人的多次测量存在相关性，简单回归假设观测独立，导致标准误低估和预测偏差
signal: 残差图呈现明显的个体聚集模式，模型诊断显示异方差性严重
lesson: 纵向数据（重复测量）必须用混合效应模型（LME）或广义估计方程（GEE）处理，显式建模个体随机效应；简单回归在纵向数据分析中会导致严重偏差
avoid: 
source: 2006年高教社杯全国大学生数学建模竞赛B题：艾滋病疗法的评价及疗效的预测|https://blog.csdn.net/weixin_43970743/article/details/161517254|2006
confidence: 高
```

---

## FD-374（公开经验库·Kimi）

```yaml
failure_id: FD-374
problem_type: 环境评价与污染预测
domain: 环境工程/水文水资源
method: 初期仅按各站点污染物浓度高低排序确定污染源
failure: 定位结果与实际情况偏差大，部分高浓度点为上游来水而非本地排放
cause: 未考虑水流稀释和降解作用，下游高浓度可能来自上游传输，非本地排污
signal: 某上游城市下游站点浓度反而低于上游站点，与污染源假设矛盾
lesson: 水污染溯源必须建立水质传输模型（如对流-扩散-降解模型），考虑水流运动和污染物衰减，不能仅凭浓度极值判断；机理模型是环境溯源的核心工具
avoid: 
source: 2005年高教社杯全国大学生数学建模竞赛A题：长江水质的评价和预测|https://blog.csdn.net/weixin_43970743/article/details/161512894|2005
confidence: 高
```

---

## FD-375（公开经验库·Kimi）

```yaml
failure_id: FD-375
problem_type: 库存决策与资源分配
domain: 互联网服务/运营管理
method: 初期用简单贪心算法按会员偏好降序分配DVD
failure: 早期会员获得高偏好DVD，后期会员满意度极低，整体分配不公平
cause: 贪心算法缺乏全局视野，未考虑DVD库存约束在全局上的最优配置
signal: 前100位会员平均满意度接近满分，后100位会员平均满意度不足2分
lesson: 资源分配问题在约束有限时必须用全局优化（整数规划）而非贪心算法；贪心在资源充足时有效，但在稀缺资源分配中会严重损害公平性和整体效率
avoid: 
source: 2005年高教社杯全国大学生数学建模竞赛B题：DVD在线租赁|https://blog.csdn.net/weixin_43970743/article/details/161513314|2005
confidence: 高
```

---

## FD-376（公开经验库·Kimi）

```yaml
failure_id: FD-376
problem_type: 商业网点规划与人流预测
domain: 大型活动/商业运营
method: 初期按各商区面积平均分配MS数量
failure: 部分热门商区MS严重不足导致排队，部分偏远商区MS闲置
cause: 未考虑人流分布的不均匀性，平均分配忽略了路径选择和观众聚集效应
signal: 模拟中某主通道商区排队长度超过20人，而某偏远商区MS利用率不足10%
lesson: 商业网点布局必须基于人流预测而非简单平均分配；人流预测需考虑路径选择（最短路径、吸引力模型）和观众行为（出行、餐饮、购物链），Dijkstra或重力模型是常用工具
avoid: 
source: 2004年高教社杯全国大学生数学建模竞赛A题：奥运会临时超市网点设计|https://blog.csdn.net/weixin_43970743/article/details/161508748|2004
confidence: 高
```

---

## FD-377（公开经验库·Kimi）

```yaml
failure_id: FD-377
problem_type: 生物经济建模与多阶段优化
domain: 畜牧养殖/农业经济
method: 初期忽略种猪淘汰率，假设种猪永久使用
failure: 计算的养殖规模远超实际可持续规模，种猪更新成本被严重低估
cause: 种猪3-5年后失去生育能力需淘汰更新，忽略淘汰率导致长期成本计算错误
signal: 模型预测5年后利润持续上升，但实际养殖中种猪更新成本急剧增加
lesson: 畜牧业等生物资产建模必须考虑资产折旧/淘汰周期，不能假设生物资产永久有效；生命周期成本是农业经济模型的核心
avoid: 
source: 2014年高教社杯全国大学生数学建模竞赛C题：生猪养殖场的经营管理|https://www.ppmy.cn/embedded/127230.html|2014
confidence: 高
```

---

## FD-378（公开经验库·Kimi）

```yaml
failure_id: FD-378
problem_type: 结构变形监测与预测
domain: 古建筑保护/测绘工程
method: 初期直接用8个观测点的坐标平均值作为层中心
failure: 当某方向变形不均匀时，平均值严重偏离真实中心，导致变形指标失真
cause: 古塔变形通常是不对称的（如某侧倾斜更大），简单平均会偏向观测点密集或变形小的一侧
signal: 计算得某层中心位置在4次测量中呈非单调变化，与整体倾斜趋势矛盾
lesson: 多点确定几何中心时，必须考虑各点的空间分布与变形模式，最小二乘拟合平面+优化求中心比简单平均更稳健；古建筑监测中测量点选择和处理方法直接影响变形评估结果
avoid: 
source: 2013年高教社杯全国大学生数学建模竞赛C题：古塔的变形|https://blog.csdn.net/weixin_43292788/article/details/142879150|2013
confidence: 高
```

---

## FD-379（公开经验库·Kimi）

```yaml
failure_id: FD-379
problem_type: 光伏建筑一体化设计
domain: 新能源建筑/几何优化
method: 初期仅按电池功率密度排序选择，忽略逆变器匹配约束
failure: 大量电池无法接入逆变器，方案不可行
cause: 不同电池类型输出电压/电流不同，必须匹配特定逆变器；仅看功率密度会导致类型混杂无法电气连接
signal: 计算得总装机容量很大，但可接入逆变器的容量不足30%
lesson: 光伏系统设计必须同时考虑物理布局与电气匹配，电池-逆变器匹配是硬约束，需在选型阶段就纳入模型；不能先选电池再配逆变器
avoid: 
source: 2012年高教社杯全国大学生数学建模竞赛B题：太阳能小屋的设计|https://blog.csdn.net/weixin_43292788/article/details/142903938|2012
confidence: 中
```

---

## FD-380（公开经验库·Kimi）

```yaml
failure_id: FD-380
problem_type: 设施选址与警力调度优化
domain: 公共安全/运筹优化
method: 初期仅将节点（路口）分配给最近平台，忽略路径分配
failure: 大量路径无法在3分钟内覆盖，出警时间超标
cause: 事故发生在路径上，仅优化节点会导致长路径的中间区域无人管辖
signal: 某条长路径两端节点都在3分钟内，但路径中点超出3分钟范围
lesson: 交通网络优化中，服务覆盖必须考虑边（路径）而不仅是节点（路口）；对长路径需分段处理或增设虚拟节点，不能简单按节点最近分配
avoid: 
source: 2011年高教社杯全国大学生数学建模竞赛B题：交巡警服务平台的设置与调度|https://www.ppmy.cn/embedded/129890.html|2011
confidence: 高
```

---

## FD-381（公开经验库·Kimi）

```yaml
failure_id: FD-381
problem_type: 时间序列预测与经济影响评估
domain: 宏观经济/事件评估
method: 初期仅用参观人数与历史同期简单对比评估影响
failure: 无法区分世博会效应与上海市旅游业自然增长趋势，高估或低估影响
cause: 未建立反事实预测模型（无世博会情景），简单对比混淆了趋势与事件效应
signal: 2005-2009年上海市旅游人数本身呈上升趋势，简单差值将自然增长也归因于世博会
lesson: 事件影响评估必须建立反事实基准（counterfactual），通过预测无事件情景再与实际对比；时间序列模型（如ARMA）是构建反事实的标准工具，不能简单做前后对比
avoid: 
source: 2010年高教社杯全国大学生数学建模竞赛B题：上海世博会影响力的定量评估|https://blog.csdn.net/weixin_43292788/article/details/142971912|2010
confidence: 高
```

---

## FD-382（公开经验库·Kimi）

```yaml
failure_id: FD-382
problem_type: 机电系统控制与能量补偿
domain: 汽车工程/测控技术
method: 初期直接用开环前馈控制，仅按理论电流公式设定
failure: 能量误差高达5.64%，无法满足试验精度要求
cause: 开环控制未考虑实际系统参数漂移、观测噪声和模型误差，理论公式在实际中必然偏差
signal: 不同试验条件下能量误差波动大，无法稳定控制在1%以内
lesson: 精密控制系统必须采用闭环反馈，不能仅依赖开环前馈；反馈可实时修正误差，是工程控制的核心原则；从频域（Laplace变换）设计可从根本上分析系统稳定性与稳态误差
avoid: 
source: 2009年高教社杯全国大学生数学建模竞赛A题：制动器试验台的控制方法分析|https://blog.csdn.net/weixin_43292788/article/details/142999700|2009
confidence: 高
```

---

## FD-383（公开经验库·Kimi）

```yaml
failure_id: FD-383
problem_type: 产品几何优化与成本分析
domain: 工业设计/包装工程
method: 初期仅按表面积最小优化，忽略顶盖、底盖、侧壁厚度差异
failure: 理论最优解与市售易拉罐尺寸严重不符
cause: 实际易拉罐顶盖承受拉环开启力，厚度约为侧壁3倍，简单表面积模型完全忽略此结构差异
signal: 计算得最优直径约6cm，而实际可口可乐罐直径约6.6cm，且高度比例差异更大
lesson: 工程优化必须考虑实际结构约束（如厚度差异、应力集中、制造工艺），不能仅做纯几何优化；测量实际产品并分析差异原因是建模的重要步骤
avoid: 
source: 2006年高教社杯全国大学生数学建模竞赛C题：易拉罐形状和尺寸的最优设计|https://blog.csdn.net/weixin_43970743/article/details/161517298|2006
confidence: 高
```

---

## FD-384（公开经验库·Kimi）

```yaml
failure_id: FD-384
problem_type: 房地产众筹规划与税务优化
domain: 房地产金融/税务筹划
method: 初期忽略普通住宅与非普通住宅的划分对土地增值税的巨大影响
failure: 增值税计算偏差超过50%，导致投资回报率严重失真
cause: 普通住宅增值率≤20%免征土地增值税，非普通住宅按四级累进税率；划分比例直接影响税额数量级
signal: 同一方案按不同划分比例计算，增值税差异达数千万元
lesson: 房地产税务建模必须精确处理政策细节（如普通/非普通住宅划分、四级累进税率），税务政策是房地产模型的核心约束，不能简化或忽略
avoid: 
source: 2015年高教社杯全国大学生数学建模竞赛D题：众筹筑屋规划方案设计|https://blog.csdn.net/weixin_43292788/article/details/142817037|2015
confidence: 高
```

---

## FD-385（公开经验库·Kimi）

```yaml
failure_id: FD-385
problem_type: 风能资源评估与运维优化
domain: 新能源/电力系统
method: 初期仅用年平均风速评估风能资源，忽略风速分布特征
failure: 高估低风速区风机发电量，低估高风速区能量贡献，风机选型错误
cause: 风功率与风速立方成正比，高风速虽频率低但能量贡献大；仅用平均风速丢失分布信息
signal: 按平均风速选型后，实际年发电量仅为预测值的60%
lesson: 风能资源评估必须使用风速分布模型（如威布尔分布），不能仅用平均风速；功率密度（与风速立方相关）是比平均风速更科学的指标
avoid: 
source: 2016年高教社杯全国大学生数学建模竞赛D题：风电场运行状况分析及优化|https://blog.csdn.net/2403_87108415/article/details/149509195|2016
confidence: 高
```

---

## FD-386（公开经验库·Kimi）

```yaml
failure_id: FD-386
problem_type: 气象预报评价与空间插值
domain: 气象科学/空间统计
method: 初期直接用最近邻法将最近观测站值赋给网格点
failure: 在站点稀疏区产生巨大误差，评价结果不稳定
cause: 最近邻法忽略空间连续性，在站点间距大的区域代表性差
signal: 某山区网格点与最近站点距离超过50km，赋值误差超过100%
lesson: 气象空间数据必须采用适当的插值方法（IDW、克里金），不能简单用最近邻；站点分布不均时需引入动态权重或高程修正；空间插值是气象评价的基础步骤，直接影响结论可靠性
avoid: 
source: 2005年高教社杯全国大学生数学建模竞赛C题：雨量预报方法的评价|https://blog.csdn.net/2301_80194165/article/details/148932086|2005
confidence: 高
```

---

## FD-387（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-387
problem_type: 综合评价/数据预测
domain: 社会科学/影响力评估
method: 直接用原始量纲5指标做等权平均排名
failure: 指标量纲不统一，数值大的指标掩盖小量纲指标
cause: 指标量纲不统一，数值大的指标掩盖小量纲指标
signal: 归一化前排名与常识(上海应最高)不符
lesson: 多指标综合评价必须先做量纲归一化(如max/离差标准化)，避免大数值指标主导；不要直接对原始量纲数据等权平均
avoid: 
source: 全国建模比赛一等奖 2010年上海世博会影响力的定量评估|https://max.book118.com/html/2020/0622/5120103111002310.shtm|2010
confidence: 高
```

---

## FD-388（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-388
problem_type: 综合评价/数据预测
domain: 社会科学/影响力评估
method: 仅凭经验给5指标赋权做综合评价
failure: 经验赋权缺乏数据支撑
cause: 经验赋权缺乏数据支撑
signal: 专家给定权重(0.1,0.4,0.15,0.15,0.2)与AHP求得(0.0833,0.3333,0.1667,0.1667,0.25)不一致
lesson: 避免用纯经验赋权做关键评价，至少用AHP/熵权法等数据驱动方法交叉验证；不要只依赖专家拍脑袋定权重
avoid: 
source: 全国建模比赛一等奖 2010年上海世博会影响力的定量评估|https://max.book118.com/html/2020/0622/5120103111002310.shtm|2010
confidence: 高
```

---

## FD-389（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-389
problem_type: 综合评价/数据预测
domain: 社会科学/影响力评估
method: 仅用单因子(累积81.087%)代表全部信息
failure: 为简洁强行取单因子
cause: 为简洁强行取单因子
signal: 因子2、3累积贡献率仍达91.791%/100%
lesson: 单因子降维虽简洁但会损失信息，报告中应注明累积贡献率并说明取舍；不要隐瞒信息损失比例
avoid: 
source: 全国建模比赛一等奖 2010年上海世博会影响力的定量评估|https://max.book118.com/html/2020/0622/5120103111002310.shtm|2010
confidence: 高
```

---

## FD-390（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-390
problem_type: 空间分析/环境评价
domain: 环境科学/空间统计
method: IDW反距离权重插值
failure: IDW仅基于距离权重, 不考虑半变异函数与空间自相关
cause: IDW仅基于距离权重, 不考虑半变异函数与空间自相关
signal: 插值图出现以采样点为圆心的环状伪结构
lesson: 有空间自相关的地理数据应优先用克里金(基于半变异函数); 不要用IDW处理强空间自相关场
avoid: 
source: 2011年全国大学生数模竞赛全国一等奖论文(城市表层土壤重金属污染分析)|https://max.book118.com/html/2019/0524/6003215231002032.shtm|2011
confidence: 高
```

---

## FD-391（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-391
problem_type: 空间分析/环境评价
domain: 环境科学/空间统计
method: 直接用浓度均值评价功能区污染
failure: 均值对极值不敏感
cause: 均值对极值不敏感
signal: 均值法下某功能区评级偏低, 与内梅罗指数结论冲突
lesson: 土壤重金属评价应同时报告单因子指数与内梅罗(或地累积)综合指数, 兼顾极值; 不要用简单均值掩盖极值
avoid: 
source: 2011年全国大学生数模竞赛全国一等奖论文(城市表层土壤重金属污染分析)|https://max.book118.com/html/2019/0524/6003215231002032.shtm|2011
confidence: 高
```

---

## FD-392（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-392
problem_type: 空间分析/环境评价
domain: 环境科学/空间统计
method: 克里金插值前未做正态化
failure: 重金属含量高度右偏(如Hg均值91.94但最大16000), 不满足正态假设
cause: 重金属含量高度右偏(如Hg均值91.94但最大16000), 不满足正态假设
signal: 变异函数出现异常基台
lesson: 克里金前必须用峰度偏度检验+对数转换使数据近似正态; 不要对强右偏数据直接克里金
avoid: 
source: 2011年全国大学生数模竞赛全国一等奖论文(城市表层土壤重金属污染分析)|https://max.book118.com/html/2019/0524/6003215231002032.shtm|2011
confidence: 高
```

---

## FD-393（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-393
problem_type: 精算/数据预测
domain: 经济学/社会保障
method: 简单指数外推未来工资
failure: 忽略经济发展到发达阶段后增长率趋稳
cause: 忽略经济发展到发达阶段后增长率趋稳
signal: 长期预测值发散不现实
lesson: 长期工资/经济预测用Logistic等饱和模型而非指数外推; 不要让预测值无界增长
avoid: 
source: 企业退休职工养老金制度的改革方案(大学生数学建模国家一等奖)|https://doc.guandang.net/sa971d8cd3fed93f0a060cd94.html|2011
confidence: 高
```

---

## FD-394（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-394
problem_type: 精算/数据预测
domain: 经济学/社会保障
method: 忽略缴费指数, 直接用社会平均工资算替代率
failure: 替代率取决于个人指数化工资与社会平均工资之比
cause: 替代率取决于个人指数化工资与社会平均工资之比
signal: 测算替代率与分年龄实际值不符
lesson: 养老金替代率必须引入缴费指数(个人/社会平均工资比); 不要跳过缴费指数直接算
avoid: 
source: 企业退休职工养老金制度的改革方案(大学生数学建模国家一等奖)|https://doc.guandang.net/sa971d8cd3fed93f0a060cd94.html|2011
confidence: 高
```

---

## FD-395（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-395
problem_type: 精算/数据预测
domain: 经济学/社会保障
method: 只看静态资金缺口, 不做收支平衡年龄分析
failure: 缺口是存量, 平衡年龄才是可持续指标
cause: 缺口是存量, 平衡年龄才是可持续指标
signal: 缺口数值大但不知何时平衡
lesson: 养老金可持续性应算收支平衡年龄(缴费总额/年养老金+退休年龄); 不要只报缺口不分析平衡时点
avoid: 
source: 企业退休职工养老金制度的改革方案(大学生数学建模国家一等奖)|https://doc.guandang.net/sa971d8cd3fed93f0a060cd94.html|2011
confidence: 高
```

---

## FD-396（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-396
problem_type: 医学统计/数据预测
domain: 流行病学/环境统计
method: 直接用原始含错数据做回归
failure: 原始病例数据含错误/缺失
cause: 原始病例数据含错误/缺失
signal: 散点图异常离散、系数反常
lesson: 医学/监测数据建模前必须用Excel/MATLAB做错误修复与标准化清洗; 不要跳过数据清洗
avoid: 
source: 脑卒中发病环境因素分析及干预(2012国赛数学建模国家一等奖)|https://doc.xuehai.net/bec44fb1ced23f185c659750f.html|2012
confidence: 高
```

---

## FD-397（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-397
problem_type: 医学统计/数据预测
domain: 流行病学/环境统计
method: 一元线性回归逐因素拟合
failure: 单因素忽略因素间交互
cause: 单因素忽略因素间交互
signal: 单因素拟合R²低
lesson: 多因素疾病环境分析应做多元逐步回归而非单因素一元拟合; 不要只做单因素散点拟合
avoid: 
source: 脑卒中发病环境因素分析及干预(2012国赛数学建模国家一等奖)|https://doc.xuehai.net/bec44fb1ced23f185c659750f.html|2012
confidence: 高
```

---

## FD-398（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-398
problem_type: 医学统计/数据预测
domain: 流行病学/环境统计
method: 忽略因素交互(如湿度受温差/气压影响)
failure: 气象因素高度相关, 存在中介效应
cause: 气象因素高度相关, 存在中介效应
signal: 平均湿度单独回归显著但机制不清
lesson: 多因素环境建模要考虑变量间交互/中介(如湿度受温差、气压影响再作用于发病率); 不要假定各因素相互独立
avoid: 
source: 脑卒中发病环境因素分析及干预(2012国赛数学建模国家一等奖)|https://doc.xuehai.net/bec44fb1ced23f185c659750f.html|2012
confidence: 高
```

---

## FD-399（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-399
problem_type: 交通流/数据预测
domain: 交通工程
method: 简单M/M/1单服务台排队
failure: 事故占用部分车道仍为多服务台系统
cause: 事故占用部分车道仍为多服务台系统
signal: 预测通行能力与实际16.8pcu/min偏差大
lesson: 车道占用问题要按剩余可用车道扩展为多服务台/多车道模型; 不要把多车道当单服务台M/M/1
avoid: 
source: 车道占用对城市道路通行能力影响(2013高教社杯优秀论文选登, 华中科技大学)|https://dxs.moe.gov.cn/zx/a/qkt_sxjm/131112/1249183.shtml|2013
confidence: 高
```

---

## FD-400（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-400
problem_type: 交通流/数据预测
domain: 交通工程
method: 忽略车辆类型折算
failure: 未换算标准车当量(pcu)
cause: 未换算标准车当量(pcu)
signal: 实际通行能力波动大、拟合差
lesson: 交通通行能力必须按车型折算为标准车当量pcu; 不要混用自然车数
avoid: 
source: 车道占用对城市道路通行能力影响(2013高教社杯优秀论文选登, 华中科技大学)|https://dxs.moe.gov.cn/zx/a/qkt_sxjm/131112/1249183.shtml|2013
confidence: 高
```

---

## FD-401（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-401
problem_type: 交通流/数据预测
domain: 交通工程
method: 忽略信号灯周期对排队到达时间的影响
failure: 红绿灯周期改变上游有效到达率
cause: 红绿灯周期改变上游有效到达率
signal: 无周期模型给出的到达时间与视频不符
lesson: 城市路段排队预测必须考虑红绿灯周期(周期性到达); 不要假设车辆均匀连续到达
avoid: 
source: 车道占用对城市道路通行能力影响(2013高教社杯优秀论文选登, 华中科技大学)|https://dxs.moe.gov.cn/zx/a/qkt_sxjm/131112/1249183.shtml|2013
confidence: 高
```

---

## FD-402（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-402
problem_type: 空间几何/变形监测
domain: 测绘工程/结构监测
method: 仅用组合形心公式求层中心
failure: 假设塔层为正多边形
cause: 假设塔层为正多边形
signal: 与实测8点分布不符
lesson: 层中心应最小二乘拟合观测点平面取距各点平方和最小点, 不假设正多边形; 不要对实测层强加正多边形假设
avoid: 
source: 古塔的变形(2013高教社杯优秀论文选登, 成都工业学院)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700221.shtml|2013
confidence: 高
```

---

## FD-403（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-403
problem_type: 空间几何/变形监测
domain: 测绘工程/结构监测
method: 用ARIMA/多期回归预测变形趋势
failure: 样本太少
cause: 样本太少
signal: 预测区间过宽/不收敛
lesson: 小样本(≤4期)变形趋势预测优先用灰色预测GM(1,1)而非ARIMA; 不要对极少期数用参数多的时序模型
avoid: 
source: 古塔的变形(2013高教社杯优秀论文选登, 成都工业学院)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700221.shtml|2013
confidence: 高
```

---

## FD-404（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-404
problem_type: 空间几何/变形监测
domain: 测绘工程/结构监测
method: 忽略扭曲(仅看倾斜/弯曲)
failure: 扭曲变形隐蔽
cause: 扭曲变形隐蔽
signal: 俯视图叠加显示层间旋转
lesson: 古塔变形必须同时刻画倾斜、弯曲、扭曲三要素, 扭曲用坐标旋转变换角度量化; 不要只分析倾斜与弯曲
avoid: 
source: 古塔的变形(2013高教社杯优秀论文选登, 成都工业学院)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700221.shtml|2013
confidence: 高
```

---

## FD-405（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-405
problem_type: 天文几何/反问题
domain: 天体物理/几何建模
method: 假设单一解直接反演经纬度
failure: 影长方程对(地点,日期)非唯一
cause: 影长方程对(地点,日期)非唯一
signal: 优化给出多组候选解
lesson: 太阳影子定位本质是多解反问题, 必须给出候选解集并分类筛选(结合地理合理性与偏移角一致性); 不要只报一个'最优'解
avoid: 
source: 基于非线性最小二乘法的太阳影子定位研究(2015国赛A题全国优秀论文)|https://max.book118.com/html/2017/0924/134885798.shtml|2015
confidence: 高
```

---

## FD-406（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-406
problem_type: 天文几何/反问题
domain: 天体物理/几何建模
method: 忽略时差(北京时间当地方时)
failure: 未将北京时间转为地方时
cause: 未将北京时间转为地方时
signal: 正午时刻与12:00偏离
lesson: 影子定位须将北京时间按经度差转为地方时再算时角; 不要直接用北京时间当地方时
avoid: 
source: 基于非线性最小二乘法的太阳影子定位研究(2015国赛A题全国优秀论文)|https://max.book118.com/html/2017/0924/134885798.shtml|2015
confidence: 高
```

---

## FD-407（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-407
problem_type: 天文几何/反问题
domain: 天体物理/几何建模
method: 忽略大气折射
failure: 折射使太阳视位置偏移
cause: 折射使太阳视位置偏移
signal: 拟合残差有系统偏置
lesson: 高精度影子定位应建立基于大气折射率的修正模型(或至少注明忽略); 不要完全忽略折射影响
avoid: 
source: 基于非线性最小二乘法的太阳影子定位研究(2015国赛A题全国优秀论文)|https://max.book118.com/html/2017/0924/134885798.shtml|2015
confidence: 高
```

---

## FD-408（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-408
problem_type: 搜索优化/概率建模
domain: 海上搜救/贝叶斯搜索理论
method: 假设 IFP(预定航线)为直线、且飞机仅撞击水面才解体
failure: 
cause: 
signal: 模型对航线几何与解体方式高度敏感(论文 Sensitivity Analysis 指出)
lesson: 避免把航线简化为直线或假设单一解体模式; 应以多轨迹/分段航线与空中解体情形做敏感性测试, 并在报告中标注假设边界
avoid: 
source: Searching for a Lost Plane: A Probabilistic, Neighborhood-Based Model for Locating Transoceanic Flights (2015 MCM B Outstanding, Colorado College, Team 39173)|https://max.book118.com/html/2026/0704/7062043054011130.shtm|2015
confidence: 高
```

---

## FD-409（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-409
problem_type: 搜索优化/概率建模
domain: 海上搜救/贝叶斯搜索理论
method: 直接假设 POD(检测概率)为 1
failure: 
cause: 
signal: 搜索价值评估与实际可检测能力脱节
lesson: 不要用 POD=1 偷懒; 必须按具体搜索平台用 Koopman 等方程计算 POD, 否则方案不可执行
avoid: 
source: Searching for a Lost Plane: A Probabilistic, Neighborhood-Based Model for Locating Transoceanic Flights (2015 MCM B Outstanding, Colorado College, Team 39173)|https://max.book118.com/html/2026/0704/7062043054011130.shtm|2015
confidence: 高
```

---

## FD-410（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-410
problem_type: 搜索优化/概率建模
domain: 海上搜救/贝叶斯搜索理论
method: 搜索未命中后保持固定概率、不更新
failure: 
cause: 
signal: 历史 AF447(2009)经验表明静态搜索范围难以收敛
lesson: 避免静态搜索; 必须用'未找到'结果动态重分配概率(邻域 POC 更新), 始终把下一目标指向相邻高概率单元
avoid: 
source: Searching for a Lost Plane: A Probabilistic, Neighborhood-Based Model for Locating Transoceanic Flights (2015 MCM B Outstanding, Colorado College, Team 39173)|https://max.book118.com/html/2026/0704/7062043054011130.shtm|2015
confidence: 高
```

---

## FD-411（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-411
problem_type: 网络科学/信息传播
domain: 社交网络分析/影响力度量
method: 仅用静态网络指标(如单点度数)分析信息
failure: 
cause: 
signal: 模型只能给出单帧快照, 无法回答'信息如何演变
lesson: 避免把信息传播题做成静态图作业; 必须引入时间步与动态扩散过程来刻画演化
avoid: 
source: Measuring the Evolution and Influence in Society's Information Networks (2016 ICM Problem D)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-412（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-412
problem_type: 网络科学/信息传播
domain: 社交网络分析/影响力度量
method: 忽略信息价值随时间衰减
failure: 
cause: 
signal: 老信息传播量高但现实价值低, 度量与直觉冲突
lesson: 不要只用触达量衡量信息价值; 必须引入衰减(指数/对数)刻画信息时效, 价值=传播×衰减
avoid: 
source: Measuring the Evolution and Influence in Society's Information Networks (2016 ICM Problem D)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-413（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-413
problem_type: 网络科学/信息传播
domain: 社交网络分析/影响力度量
method: 影响力指标定义主观且不可解释
failure: 
cause: 
signal: 评委无法复算或比较不同信息
lesson: 避免堆砌不可解释的指标; 每个影响力/价值指标必须有清晰定义与可比性说明
avoid: 
source: Measuring the Evolution and Influence in Society's Information Networks (2016 ICM Problem D)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-414（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-414
problem_type: 环境预测/资源管理
domain: 水资源/干旱风险
method: 只看年降水量判断缺水
failure: 
cause: 
signal: 可用水量与降水走势背离
lesson: 不要只看降水量; 必须做水量平衡(补给-消耗-生态需水), 缺水量=需求-可用补给
avoid: 
source: Are we headed for a thirsty planet? (2016 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-415（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-415
problem_type: 环境预测/资源管理
domain: 水资源/干旱风险
method: 用水需求设为常数
failure: 
cause: 
signal: 预测缺口随时间被实际增长击穿
lesson: 避免把需求当常数; 需求应随人口/收入情景(高/中/低)做敏感性分析
avoid: 
source: Are we headed for a thirsty planet? (2016 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-416（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-416
problem_type: 环境预测/资源管理
domain: 水资源/干旱风险
method: 忽略生态基流约束
failure: 
cause: 
signal: 方案被生态约束否定
lesson: 不要把生态需水当可挤压项; 必须设生态基流/环境阈值硬约束
avoid: 
source: Are we headed for a thirsty planet? (2016 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-417（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-417
problem_type: 水资源优化/系统管理
domain: 水库调度/水电-灌溉-生态权衡
method: 单目标最大化水电发电
failure: 
cause: 
signal: 生态/灌溉目标被严重牺牲
lesson: 不要把发电当唯一目标; 必须同时优化灌溉与生态基流, 用权衡前沿展示取舍
avoid: 
source: Managing the Zambezi River System (2017 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## FD-418（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-418
problem_type: 水资源优化/系统管理
domain: 水库调度/水电-灌溉-生态权衡
method: 忽略大型水库蒸发损失
failure: 
cause: 
signal: 核算可用水量大于实际
lesson: 不要忽略水库面蒸发; 水量平衡必须含蒸发项, 尤其热带大型水库
avoid: 
source: Managing the Zambezi River System (2017 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## FD-419（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-419
problem_type: 水资源优化/系统管理
domain: 水库调度/水电-灌溉-生态权衡
method: 调度规则只在平均来水下设计算
failure: 
cause: 
signal: 平均年表现好但极端年缺水/溃坝风险高
lesson: 避免只在平均情景设计; 必须做干旱/洪水极端年敏感性, 设预警与分级响应
avoid: 
source: Managing the Zambezi River System (2017 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## FD-420（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-420
problem_type: 数据分析/预测
domain: 能源经济/政策分析
method: 忽略数据清洗直接用原始数据建模
failure: 
cause: 
signal: 趋势出现无物理意义的跳变
lesson: 不要跳过数据清洗; 必须统一口径、处理缺失与异常后再建模
avoid: 
source: Energy Production (2018 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## FD-421（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-421
problem_type: 数据分析/预测
domain: 能源经济/政策分析
method: 只用单变量外推能源产量
failure: 
cause: 
signal: 预测值与实际增长脱节
lesson: 避免单变量外推; 能源预测须引入 GDP、人口等驱动变量
avoid: 
source: Energy Production (2018 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## FD-422（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-422
problem_type: 数据分析/预测
domain: 能源经济/政策分析
method: 政策评估只用单一基准情景
failure: 
cause: 
signal: 结论缺乏'若…则…'的洞察
lesson: 避免单一情景; 政策评估必须设多情景(如高/中/低补贴)对比
avoid: 
source: Energy Production (2018 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## FD-423（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-423
problem_type: 生态建模/生物物理
domain: 虚构生物生态位建模
method: 把龙当作普通哺乳动物线性外推代谢
failure: 
cause: 
signal: 推导出的摄入/面积明显偏小, 与体型不符
lesson: 不要对虚构/特殊生物用普通标度直接外推; 必须按赛题要求把假设与功能、体型、食性的物理约束显式关联, 并加行为附加项
avoid: 
source: Game of Ecology (2019 MCM Problem A) — 赛题官方全文(含真实数字 10kg/30-40kg)|https://blog.csdn.net/xindolia_ring/article/details/86768820|2019
confidence: 中
```

---

## FD-424（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-424
problem_type: 生态建模/生物物理
domain: 虚构生物生态位建模
method: 只用单一质量点估算
failure: 
cause: 
signal: 成年龙资源需求被低估
lesson: 不要忽略赛题给定的真实生长数字; 必须建质量-时间曲线再驱动能耗/摄入/面积
avoid: 
source: Game of Ecology (2019 MCM Problem A) — 赛题官方全文(含真实数字 10kg/30-40kg)|https://blog.csdn.net/xindolia_ring/article/details/86768820|2019
confidence: 中
```

---

## FD-425（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-425
problem_type: 生态建模/生物物理
domain: 虚构生物生态位建模
method: 只做龙本身, 不扩展到真实应用
failure: 
cause: 
signal: 报告缺乏现实洞察, 评委扣分
lesson: 不要把'真实应用外推'当可选项; 必须给出模型在现实(如保护区/入侵物种)中的应用讨论
avoid: 
source: Game of Ecology (2019 MCM Problem A) — 赛题官方全文(含真实数字 10kg/30-40kg)|https://blog.csdn.net/xindolia_ring/article/details/86768820|2019
confidence: 中
```

---

## FD-426（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-426
problem_type: 数据分析/流行病学
domain: 公共卫生/药物滥用传播
method: 忽略数据口径差异直接合并
failure: 
cause: 
signal: 出现无现实意义的突变
lesson: 不要跳过数据对齐; 必须统一口径、处理缺失后再建模
avoid: 
source: The Opioid Crisis (2019 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-427（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-427
problem_type: 数据分析/流行病学
domain: 公共卫生/药物滥用传播
method: 把相关当因果评估干预
failure: 
cause: 
signal: 干预效应与同期自然下降混淆
lesson: 避免用简单前后对比评估政策; 须用断点/双重差分等控制趋势与混杂
avoid: 
source: The Opioid Crisis (2019 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-428（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-428
problem_type: 数据分析/流行病学
domain: 公共卫生/药物滥用传播
method: 忽视空间聚集, 只用全国总量
failure: 
cause: 
signal: 资源错配到低危区
lesson: 不要只用聚合总量; 必须做时空扩散与地区风险分层以精准投放资源
avoid: 
source: The Opioid Crisis (2019 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-429（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-429
problem_type: 生态建模/气候变化
domain: 海洋生态/物种分布迁移
method: 只用温度单因子定栖息地
failure: 
cause: 
signal: 预测栖息地与观测偏离
lesson: 不要只用温度; 栖息地适宜度应综合温度/盐度/溶氧/食物等多因子
avoid: 
source: Moving North (2020 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-430（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-430
problem_type: 生态建模/气候变化
domain: 海洋生态/物种分布迁移
method: 只画分布不量化北迁速率
failure: 
cause: 
signal: 结论停留在'会变化'而无定量
lesson: 不要只做静态分布; 必须追踪并报告栖息地纬度中心的迁移速率
avoid: 
source: Moving North (2020 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-431（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-431
problem_type: 生态建模/气候变化
domain: 海洋生态/物种分布迁移
method: 忽略产业/经济影响
failure: 
cause: 
signal: 未给出可执行的适应建议
lesson: 不要把社会/经济影响当可选项; 必须评估渔业/社区影响并提适应策略
avoid: 
source: Moving North (2020 MCM Problem A)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-432（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-432
problem_type: 数据分析/文本挖掘
domain: 电商评论挖掘/推荐
method: 只用评分均值做预测/推荐
failure: 
cause: 
signal: 模型精度低、推荐雷同
lesson: 不要只用评分均值; 必须抽取文本情感/主题作为特征提升区分度
avoid: 
source: A Data Analysis of Online Shopping (2020 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-433（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-433
problem_type: 数据分析/文本挖掘
domain: 电商评论挖掘/推荐
method: 把有用投票当噪声丢弃
failure: 
cause: 
signal: 高质量评论与低质量被同等对待
lesson: 不要用有用投票当噪声; 应以其为质量权重, 优先分析高'有用'评论
avoid: 
source: A Data Analysis of Online Shopping (2020 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-434（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-434
problem_type: 数据分析/文本挖掘
domain: 电商评论挖掘/推荐
method: 忽略评分不平衡直接分类
failure: 
cause: 
signal: 少数类召回低
lesson: 不要忽略评分分布不平衡; 须重采样/加权或改回归, 并报告按类的表现
avoid: 
source: A Data Analysis of Online Shopping (2020 MCM Problem C)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-435（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-435
problem_type: 环境建模/物质流
domain: 塑料污染/循环经济
method: 忽略质量守恒, 只回归产量
failure: 
cause: 
signal: 存量变化无法用输入输出解释
lesson: 不要跳过质量守恒; 必须建 存量=输入-回收-降解 的物质流框架
avoid: 
source: The Plastic (2020 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-436（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-436
problem_type: 环境建模/物质流
domain: 塑料污染/循环经济
method: 假设降解速率恒定且很快
failure: 
cause: 
signal: 预测存量偏低
lesson: 不要假设塑料快速降解; 须采用各品类慢降解时长, 微塑料近似长期留存
avoid: 
source: The Plastic (2020 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-437（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-437
problem_type: 环境建模/物质流
domain: 塑料污染/循环经济
method: 减塑策略不量化
failure: 
cause: 
signal: 结论无'哪招最有效
lesson: 不要只罗列策略; 必须量化各策略对存量的削减并排序
avoid: 
source: The Plastic (2020 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-438（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-438
problem_type: 社会预测/气候适应
domain: 气候移民/人口迁移
method: 把暴露直接等同迁移
failure: 
cause: 
signal: 预测迁移量远超现实
lesson: 不要把气候暴露直接当迁移; 必须用经济/政策适应性调节有效迁移倾向
avoid: 
source: The Place I Called Home (2020 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-439（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-439
problem_type: 社会预测/气候适应
domain: 气候移民/人口迁移
method: 忽略接收地容量约束
failure: 
cause: 
signal: 某接收地迁入远超承载
lesson: 不要忽略接收地容量; 重力模型须加容量硬约束, 溢出流量另寻目的地
avoid: 
source: The Place I Called Home (2020 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-440（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-440
problem_type: 社会预测/气候适应
domain: 气候移民/人口迁移
method: 只用全国总量不做空间分配
failure: 
cause: 
signal: 结论无地理针对性
lesson: 不要只用聚合量; 必须空间显式到地区级, 才能定位高风险迁出区与承压接收地
avoid: 
source: The Place I Called Home (2020 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2020/results/|2020
confidence: 中
```

---

## FD-441（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-441
problem_type: 风险评估/轨道动力学
domain: 航天工程/碎片管理
method: 假设碎片线性增长
failure: 
cause: 
signal: 预测存量远低于级联情形
lesson: 不要假设线性增长; 必须建模碰撞级联正反馈与临界阈值
avoid: 
source: Space Junk (2016 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-442（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-442
problem_type: 风险评估/轨道动力学
domain: 航天工程/碎片管理
method: 只用碎片数量衡量风险
failure: 
cause: 
signal: 高风险小碎片被忽视
lesson: 不要只用数量; 必须按尺寸/轨道算碰撞概率, 关注高危交会
avoid: 
source: Space Junk (2016 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-443（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-443
problem_type: 风险评估/轨道动力学
domain: 航天工程/碎片管理
method: 清理方案'全清'一刀切
failure: 
cause: 
signal: 预算远超可用
lesson: 不要追求全清; 必须按风险/成本效益排序, 优先清理高危害大碎片
avoid: 
source: Space Junk (2016 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2016/results/|2016
confidence: 中
```

---

## FD-444（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-444
problem_type: 文化演化/预测
domain: 语言学/语言灭绝
method: 假设各语言独立指数消亡
failure: 
cause: 
signal: 预测存续语言数偏多
lesson: 不要假设独立消亡; 必须用竞争/转移模型刻画使用者流向主导语
avoid: 
source: How Many Languages? (2018 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## FD-445（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-445
problem_type: 文化演化/预测
domain: 语言学/语言灭绝
method: 只看全球总数不看规模分布
failure: 
cause: 
signal: 多样性损失被平均掩盖
lesson: 不要只看总数; 必须按使用人数分级, 关注小语种濒危
avoid: 
source: How Many Languages? (2018 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## FD-446（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-446
problem_type: 文化演化/预测
domain: 语言学/语言灭绝
method: 保护措施不量化
failure: 
cause: 
signal: 结论无'保护可挽救多少
lesson: 不要只列措施; 必须量化保护(如双语教育)对存续语言数的提升
avoid: 
source: How Many Languages? (2018 MCM Problem B)|https://contest.comap.com/undergraduate/contests/mcm/contests/2018/results/|2018
confidence: 中
```

---

## FD-447（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-447
problem_type: 环境经济/生态核算
domain: 生态系统服务价值评估
method: 只用单一价值系数
failure: 
cause: 
signal: 成本对系数选择极敏感
lesson: 不要只用单一系数; 必须按服务类型(碳汇/水源/生物多样性)分别价值化
avoid: 
source: What is the Cost of Environmental Degradation? (2019 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-448（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-448
problem_type: 环境经济/生态核算
domain: 生态系统服务价值评估
method: 忽略非市场价值
failure: 
cause: 
signal: 成本明显低于学界估算
lesson: 不要把非市场价值当零; 须用替代成本/意愿调查等纳入文化和存在价值
avoid: 
source: What is the Cost of Environmental Degradation? (2019 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-449（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-449
problem_type: 环境经济/生态核算
domain: 生态系统服务价值评估
method: 价值系数不做敏感性
failure: 
cause: 
signal: 结论对系数高度敏感
lesson: 不要给单点环境成本; 必须做系数敏感性, 给成本区间与稳健判断
avoid: 
source: What is the Cost of Environmental Degradation? (2019 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-450（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-450
problem_type: 空间分析/预测
domain: 犯罪地理画像/安保
method: 只用单一方案生成画像
failure: 
cause: 
signal: 报告缺方案对比与组合
lesson: 不要只用一种画像; 赛题明确要求≥2 种方案(如重心法+距离衰减), 并组合其结果
avoid: 
source: Criminology (2010 MCM Problem B) — COMAP 官方赛题|https://comap.com/membership/member-resources/item/criminology|2010
confidence: 中
```

---

## FD-451（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-451
problem_type: 空间分析/预测
domain: 犯罪地理画像/安保
method: 忽略可靠性估计与警告
failure: 
cause: 
signal: 给出单点预测无置信说明
lesson: 不要只给点预测; 必须说明可靠性(随样本增加收敛)并给'样本少/跨区域作案'等警告
avoid: 
source: Criminology (2010 MCM Problem B) — COMAP 官方赛题|https://comap.com/membership/member-resources/item/criminology|2010
confidence: 中
```

---

## FD-452（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-452
problem_type: 空间分析/预测
domain: 犯罪地理画像/安保
method: 假设犯罪点均匀分布无空间规律
failure: 
cause: 
signal: 候选区覆盖过大
lesson: 不要把犯罪点当随机; 必须利用'熟悉区+避开家附近'的距离衰减结构压缩搜索范围
avoid: 
source: Criminology (2010 MCM Problem B) — COMAP 官方赛题|https://comap.com/membership/member-resources/item/criminology|2010
confidence: 中
```

---

## FD-453（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-453
problem_type: 城市评估/可持续发展
domain: 城市规划/可持续性指标
method: 主观等权综合指标
failure: 
cause: 
signal: 排名对权重敏感
lesson: 不要主观等权; 须用熵权/CRITIC 等客观赋权, 并对权重做敏感性
avoid: 
source: Sustainable Cities Needed! (2017 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## FD-454（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-454
problem_type: 城市评估/可持续发展
domain: 城市规划/可持续性指标
method: 忽略指标量纲与方向
failure: 
cause: 
signal: 大数量级指标主导
lesson: 不要混用量纲; 必须正向/负向归一化后再综合
avoid: 
source: Sustainable Cities Needed! (2017 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## FD-455（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-455
problem_type: 城市评估/可持续发展
domain: 城市规划/可持续性指标
method: 只给总分不拆短板
failure: 
cause: 
signal: 结论无'先改什么
lesson: 不要只报综合分; 必须分解到维度定位短板并给优先改善项
avoid: 
source: Sustainable Cities Needed! (2017 ICM Problem E)|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/results/|2017
confidence: 中
```

---

## FD-456（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-456
problem_type: 经济建模/货币
domain: 数字货币/采用与稳定
method: 忽略采用临界质量
failure: 
cause: 
signal: 采用曲线无 S 形拐点
lesson: 不要把采用当线性; 必须用 Bass 等扩散模型刻画临界质量与 S 形增长
avoid: 
source: Universal, Decentralized, Circulating Currency (2019 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-457（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-457
problem_type: 经济建模/货币
domain: 数字货币/采用与稳定
method: 只建模价格忽略货币-采用耦合
failure: 
cause: 
signal: 价格与采用脱节
lesson: 不要孤立看价格; 必须耦合采用、货币供应与价格检验稳定条件
avoid: 
source: Universal, Decentralized, Circulating Currency (2019 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-458（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-458
problem_type: 经济建模/货币
domain: 数字货币/采用与稳定
method: 只谈去中心化优点
failure: 
cause: 
signal: 方案被安全质疑击穿
lesson: 不要只列优点; 必须评估 51% 攻击、私钥丢失等去中心化特有风险并给缓解
avoid: 
source: Universal, Decentralized, Circulating Currency (2019 ICM Problem F)|https://contest.comap.com/undergraduate/contests/mcm/contests/2019/results/|2019
confidence: 中
```

---

## FD-459（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-459
problem_type: 优化决策
domain: 工程优化/管道布置
method: 统一管线单价, 忽略城区拆迁附加费
failure: 城区管线含21~24万元/km拆迁补偿, 与郊区7.2万元/km差异巨大
cause: 城区管线含21~24万元/km拆迁补偿, 与郊区7.2万元/km差异巨大
signal: 总费用估算偏低, 方案费用排序错误
lesson: 避免把城区/郊区管线等同计价; 必须分区域建模并计入附加费
avoid: 
source: 输油管的布置-2010大学生年数学建模大赛优秀论文|https://max.book118.com/html/2020/0906/7125151136002165.shtm|2010
confidence: 高
```

---

## FD-460（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-460
problem_type: 优化决策
domain: 工程优化/管道布置
method: 只枚举车站在炼油厂投影点等端点
failure: 最优车站E位于两厂之间郊区连续区间, 端点枚举漏掉真实最优
cause: 最优车站E位于两厂之间郊区连续区间, 端点枚举漏掉真实最优
signal: 求得费用非最小, 与优化解差距明显
lesson: 不要仅枚举离散候选点; 连续决策变量须用非线性规划全局寻优
avoid: 
source: 输油管的布置-2010大学生年数学建模大赛优秀论文|https://max.book118.com/html/2020/0906/7125151136002165.shtm|2010
confidence: 高
```

---

## FD-461（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-461
problem_type: 优化决策
domain: 工程优化/管道布置
method: 对三家咨询估算直接简单平均
failure: 公司一具甲级资质、二/三乙级, 可信度不同, 等权平均失真
cause: 公司一具甲级资质、二/三乙级, 可信度不同, 等权平均失真
signal: 附加费基准偏离, 敏感性区间偏移
lesson: 避免对异质专家估计等权平均; 用AHP按资质赋权综合(得e=21.4)
avoid: 
source: 输油管的布置-2010大学生年数学建模大赛优秀论文|https://max.book118.com/html/2020/0906/7125151136002165.shtm|2010
confidence: 高
```

---

## FD-462（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-462
problem_type: 优化决策
domain: 工程优化/管道布置
method: 假定共用管线与非共用管线费用相同
failure: 问题三两厂生产能力不同, 管价5.6/6.0≠7.2, 假设不成立
cause: 问题三两厂生产能力不同, 管价5.6/6.0≠7.2, 假设不成立
signal: 问题三沿用问题二模型会高估费用
lesson: 不要默认共用/非共用管线同价; 先判断费用结构再选几何或势能模型
avoid: 
source: 输油管的布置-2010大学生年数学建模大赛优秀论文|https://max.book118.com/html/2020/0906/7125151136002165.shtm|2010
confidence: 高
```

---

## FD-463（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-463
problem_type: 优化决策
domain: 组合优化/资源分装
method: 对全部原料建单一大整数规划
failure: 规格三变量过多, 求解规模爆炸
cause: 规格三变量过多, 求解规模爆炸
signal: LINGO长时间不收敛, 超30分钟时限
lesson: 避免对多规格大样本直接整体规划; 先按规格分组局部最优再汇总
avoid: 
source: 数学建模天然肠衣国家二等奖论文|https://wk.baidu.com/view/28ffbe51c850ad02de80417c?pcf=2|2004
confidence: 高
```

---

## FD-464（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-464
problem_type: 优化决策
domain: 组合优化/资源分装
method: 正序(小规格先装)贪心
failure: 短料被优先耗尽, 长料无法成捆
cause: 短料被优先耗尽, 长料无法成捆
signal: 总捆数明显偏少
lesson: 不要正序取料; 采用倒序(大规格优先)以保护稀缺长料
avoid: 
source: 数学建模天然肠衣国家二等奖论文|https://wk.baidu.com/view/28ffbe51c850ad02de80417c?pcf=2|2004
confidence: 高
```

---

## FD-465（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-465
problem_type: 优化决策
domain: 组合优化/资源分装
method: 忽略余料降级
failure: 剩余长料不能装入原规格即被丢弃
cause: 剩余长料不能装入原规格即被丢弃
signal: 原料利用率低, 总捆数损失约12捆
lesson: 不要丢弃规格余料; 用降级规则(规格三→二→一)再规划消化
avoid: 
source: 数学建模天然肠衣国家二等奖论文|https://wk.baidu.com/view/28ffbe51c850ad02de80417c?pcf=2|2004
confidence: 高
```

---

## FD-466（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-466
problem_type: 优化决策
domain: 组合优化/资源分装
method: 不考虑±0.5米与根数-1容限
failure: 严格相等约束使多数组合不可行
cause: 严格相等约束使多数组合不可行
signal: 可行解极少甚至无解
lesson: 避免忽略题目给定的误差容限; 把±0.5米/少1根写入约束以扩大可行域
avoid: 
source: 数学建模天然肠衣国家二等奖论文|https://wk.baidu.com/view/28ffbe51c850ad02de80417c?pcf=2|2004
confidence: 高
```

---

## FD-467（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-467
problem_type: 优化决策
domain: 新能源/光伏布置优化
method: 北墙也铺设电池板
failure: 北半球北立面受照极弱, 单位面积发电为负收益
cause: 北半球北立面受照极弱, 单位面积发电为负收益
signal: 总利润下降、回收期变长
lesson: 避免在北立面铺设; 仅选南向及东西受照面, 用K值量化取舍
avoid: 
source: 2012年全国大学生数学建模获奖范文(太阳能小屋的设计, 省一等奖)|https://max.book118.com/html/2015/0608/18664649.shtm|2012
confidence: 高
```

---

## FD-468（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-468
problem_type: 优化决策
domain: 新能源/光伏布置优化
method: 固定倾角(贴附0°)不优化
failure: 倾角偏离最佳值使年辐射量显著下降
cause: 倾角偏离最佳值使年辐射量显著下降
signal: 发电量比最优低约一倍(466176 vs 990722 kWh)
lesson: 不要固定倾角; 对当地纬度以细步长枚举辐射积分求最佳倾角
avoid: 
source: 2012年全国大学生数学建模获奖范文(太阳能小屋的设计, 省一等奖)|https://max.book118.com/html/2015/0608/18664649.shtm|2012
confidence: 高
```

---

## FD-469（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-469
problem_type: 优化决策
domain: 新能源/光伏布置优化
method: 逆变器随意选型不匹配功率
failure: 串并联电压/功率不满足, 部分能量无法逆变上网
cause: 串并联电压/功率不满足, 部分能量无法逆变上网
signal: 理论发电量无法转化为收益
lesson: 避免逆变器与阵列功率脱节; 按总功率与单位成本最低贪心选配
avoid: 
source: 2012年全国大学生数学建模获奖范文(太阳能小屋的设计, 省一等奖)|https://max.book118.com/html/2015/0608/18664649.shtm|2012
confidence: 高
```

---

## FD-470（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-470
problem_type: 优化决策
domain: 新能源/光伏布置优化
method: 忽略电池类型性价比差异
failure: 薄膜电池便宜但单位面积功率低, 平铺浪费受照面
cause: 薄膜电池便宜但单位面积功率低, 平铺浪费受照面
signal: 同等面积发电量偏低
lesson: 不要同视各类电池; 用K=功率/价格筛选, 强受照面用高K单晶硅
avoid: 
source: 2012年全国大学生数学建模获奖范文(太阳能小屋的设计, 省一等奖)|https://max.book118.com/html/2015/0608/18664649.shtm|2012
confidence: 高
```

---

## FD-471（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-471
problem_type: 优化决策
domain: 路径规划/计算几何
method: 折线转弯(节点处直接拐弯)
failure: 题目要求转弯由相切圆弧组成, 折线不可行且会侵入危险区
cause: 题目要求转弯由相切圆弧组成, 折线不可行且会侵入危险区
signal: 路径被判违规或实际距离算错
lesson: 避免折线转弯; 必须用直线段+相切圆弧的线圆结构建模
avoid: 
source: 2012全国大学生数学建模机器人避障问题优秀论文模型|https://wk.baidu.com/view/9635073577a20029bd64783e0912a21615797fca|2012
confidence: 高
```

---

## FD-472（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-472
problem_type: 优化决策
domain: 路径规划/计算几何
method: 不对外扩10的危险区建模
failure: 机器人以半径10转弯会擦碰障碍原边界
cause: 机器人以半径10转弯会擦碰障碍原边界
signal: 求得路径实际碰撞
lesson: 不要忽略最小转弯半径; 先外扩障碍10单位再规划
avoid: 
source: 2012全国大学生数学建模机器人避障问题优秀论文模型|https://wk.baidu.com/view/9635073577a20029bd64783e0912a21615797fca|2012
confidence: 高
```

---

## FD-473（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-473
problem_type: 优化决策
domain: 路径规划/计算几何
method: 最短时间直接取最小半径R=10
failure: 较大半径可拉直路径、减少总弧长与转弯耗时
cause: 较大半径可拉直路径、减少总弧长与转弯耗时
signal: 时间非最小(优于97.1698的解被漏掉)
lesson: 不要把'最短路径半径'等同于'最短时间半径'; 对R建T(R)寻优
avoid: 
source: 2012全国大学生数学建模机器人避障问题优秀论文模型|https://wk.baidu.com/view/9635073577a20029bd64783e0912a21615797fca|2012
confidence: 高
```

---

## FD-474（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-474
problem_type: 优化决策
domain: 路径规划/计算几何
method: 不建可视图直接穷举拐点
failure: 凸顶点组合过多, 计算爆炸
cause: 凸顶点组合过多, 计算爆炸
signal: 无法在合理时间出解
lesson: 不要盲目枚举; 先用Dijkstra在可视图上定必经危险点序列
avoid: 
source: 2012全国大学生数学建模机器人避障问题优秀论文模型|https://wk.baidu.com/view/9635073577a20029bd64783e0912a21615797fca|2012
confidence: 高
```

---

## FD-475（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-475
problem_type: 数据分析/优化决策
domain: 城市交通/调度优化
method: 未清洗即全量统计
failure: 借车车站号29999等为无效/异常记录混入
cause: 借车车站号29999等为无效/异常记录混入
signal: 站点频次排序异常, 热点站误判
lesson: 不要跳过数据清洗; 先剔除异常站号与缺失记录再统计
avoid: 
source: 公共自行车服务系统—大学生数学建模竞赛论文|https://m.book118.com/html/2015/1217/31548128.shtm|2015
confidence: 高
```

---

## FD-476（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-476
problem_type: 数据分析/优化决策
domain: 城市交通/调度优化
method: 对所有站点无差别统一调度
failure: 各站供需失衡程度差异大, 平摊运力效率低
cause: 各站供需失衡程度差异大, 平摊运力效率低
signal: 紧缺站仍租还难, 运力浪费
lesson: 避免均匀调度; 用车锁比α分级, 优先调度α≤0.1或≥0.9的站
avoid: 
source: 公共自行车服务系统—大学生数学建模竞赛论文|https://m.book118.com/html/2015/1217/31548128.shtm|2015
confidence: 高
```

---

## FD-477（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-477
problem_type: 数据分析/优化决策
domain: 城市交通/调度优化
method: 仅以调度成本最小为单目标
failure: 忽视用户满意度导致缺车/满桩站体验差
cause: 忽视用户满意度导致缺车/满桩站体验差
signal: 成本降但租还难加剧
lesson: 不要单目标优化成本; 同时纳入满意度(周转率)建多目标
avoid: 
source: 公共自行车服务系统—大学生数学建模竞赛论文|https://m.book118.com/html/2015/1217/31548128.shtm|2015
confidence: 高
```

---

## FD-478（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-478
problem_type: 数据分析/优化决策
domain: 城市交通/调度优化
method: 忽略站点编号非连续
failure: 编号1-107、109-181、1000不连续, 按连续索引错位
cause: 编号1-107、109-181、1000不连续, 按连续索引错位
signal: 站点映射错误
lesson: 不要假设编号连续; 按实际站点集合建索引
avoid: 
source: 公共自行车服务系统—大学生数学建模竞赛论文|https://m.book118.com/html/2015/1217/31548128.shtm|2015
confidence: 高
```

---

## FD-479（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-479
problem_type: 优化决策
domain: 农业经营/生产计划
method: 忽略盈亏平衡点直接定产仔量
failure: 未核算固定成本与单位变动成本, 繁育目标无依据
cause: 未核算固定成本与单位变动成本, 繁育目标无依据
signal: 经营可能长期亏损
lesson: 不要跳过盈亏平衡分析; 先用平衡点反推每头母猪年产仔底线(本题18头)
avoid: 
source: 数学建模比赛C题省二等奖论文(生猪养殖场的经营管理)|https://m.renrendoc.com/paper/207871332.html|2014
confidence: 高
```

---

## FD-480（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-480
problem_type: 优化决策
domain: 农业经营/生产计划
method: 不限制总存栏容量
failure: 优化解超出猪场10000头上限, 方案不可行
cause: 优化解超出猪场10000头上限, 方案不可行
signal: 求得的存栏数超物理上限
lesson: 不要忘记容量硬约束; 把10000头上限写入规划
avoid: 
source: 数学建模比赛C题省二等奖论文(生猪养殖场的经营管理)|https://m.renrendoc.com/paper/207871332.html|2014
confidence: 高
```

---

## FD-481（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-481
problem_type: 优化决策
domain: 农业经营/生产计划
method: 全年统一出栏节奏
failure: 忽视三年价格周期, 低价期集中出栏
cause: 忽视三年价格周期, 低价期集中出栏
signal: 平均年利润明显偏低
lesson: 不要固定出栏; 按价格预测分周期调配肉猪/猪苗比例择机出售
avoid: 
source: 数学建模比赛C题省二等奖论文(生猪养殖场的经营管理)|https://m.renrendoc.com/paper/207871332.html|2014
confidence: 高
```

---

## FD-482（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-482
problem_type: 优化决策
domain: 农业经营/生产计划
method: 种猪比例随意设定
failure: 种猪不足则繁育链断裂, 过多则占用肉猪产能
cause: 种猪不足则繁育链断裂, 过多则占用肉猪产能
signal: 长期存栏结构失调
lesson: 不要随意定选种比; 在饱和规模下优化求得合理比例(本题约1:30)
avoid: 
source: 数学建模比赛C题省二等奖论文(生猪养殖场的经营管理)|https://m.renrendoc.com/paper/207871332.html|2014
confidence: 高
```

---

## FD-483（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-483
problem_type: 优化决策
domain: 工业工程/设施布局
method: 忽略两侧≥2mm间隙, 取W=Dmax
failure: 药盒与隔板无间隙会卡滞或推送受阻
cause: 药盒与隔板无间隙会卡滞或推送受阻
signal: 方案实际不可装配
lesson: 不要取槽宽=药盒最大宽; 须满足W≥Dmax+4留出间隙
avoid: 
source: 大学生数学建模(储药柜的设计, 国赛论文)|https://m.renrendoc.com/paper/210440230.html|2016
confidence: 高
```

---

## FD-484（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-484
problem_type: 优化决策
domain: 工业工程/设施布局
method: 槽宽≥2倍最小宽
failure: 槽内两药盒并排, 推送时重叠
cause: 槽内两药盒并排, 推送时重叠
signal: 违背'不并排重叠'约束
lesson: 不要使槽宽≥2*Dmin; 须满足W≤2*Dmin-1防并排
avoid: 
source: 大学生数学建模(储药柜的设计, 国赛论文)|https://m.renrendoc.com/paper/210440230.html|2016
confidence: 高
```

---

## FD-485（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-485
problem_type: 优化决策
domain: 工业工程/设施布局
method: 只追求类型最少(5种)
failure: 类型少则单槽宽冗余大, 空间浪费严重
cause: 类型少则单槽宽冗余大, 空间浪费严重
signal: 总宽度冗余过高
lesson: 不要单目标最少类型; 用逐步分裂迭代在类型数与冗余间权衡
avoid: 
source: 大学生数学建模(储药柜的设计, 国赛论文)|https://m.renrendoc.com/paper/210440230.html|2016
confidence: 高
```

---

## FD-486（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-486
problem_type: 优化决策
domain: 工业工程/设施布局
method: 忽略侧翻与水平旋转约束
failure: 仅按宽约束分档, 高宽比异常药盒会侧翻/旋转
cause: 仅按宽约束分档, 高宽比异常药盒会侧翻/旋转
signal: 槽内药盒姿态失控
lesson: 不要只控宽度; 须同时以高宽/长宽对角线约束防止侧翻与水平旋转
avoid: 
source: 大学生数学建模(储药柜的设计, 国赛论文)|https://m.renrendoc.com/paper/210440230.html|2016
confidence: 高
```

---

## FD-487（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-487
problem_type: 调度优化
domain: 制造系统/离散事件调度
method: 直接整数规划求8小时最大成料数
failure: 该规划为NP问题, 传统方法规模爆炸
cause: 该规划为NP问题, 传统方法规模爆炸
signal: 无法在合理时间求解
lesson: 不要硬解精确规划; NP难调度改用多原则仿真求局部最优
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(B217): 基于多原则比较和蒙特卡洛模拟的RGV动态调度模型|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018btlw/240206/1699832.shtml|2018
confidence: 高
```

---

## FD-488（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-488
problem_type: 调度优化
domain: 制造系统/离散事件调度
method: 双工序随机指定CNC工序布局
failure: 各CNC工序分配直接影响瓶颈与等待
cause: 各CNC工序分配直接影响瓶颈与等待
signal: 成料数明显低于最优(如未达253/212/241件)
lesson: 不要随机定布局; 双工序须遍历布局并按刀具配比4:4/3:5/5:3择优
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(B217): 基于多原则比较和蒙特卡洛模拟的RGV动态调度模型|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018btlw/240206/1699832.shtml|2018
confidence: 高
```

---

## FD-489（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-489
problem_type: 调度优化
domain: 制造系统/离散事件调度
method: 只用单一调度原则
failure: 单一启发式在部分参数组非最优
cause: 单一启发式在部分参数组非最优
signal: 某组数据效率偏低
lesson: 不要只用一种原则; 就近/FIFO/HRRN多原则比较, 按数据组选优
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(B217): 基于多原则比较和蒙特卡洛模拟的RGV动态调度模型|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018btlw/240206/1699832.shtml|2018
confidence: 高
```

---

## FD-490（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-490
problem_type: 调度优化
domain: 制造系统/离散事件调度
method: 忽略故障扰动
failure: 真实系统CNC会故障, 理想调度偏离实际
cause: 真实系统CNC会故障, 理想调度偏离实际
signal: 策略鲁棒性差
lesson: 不要假设参数恒定; 用负载因子/空闲时间插入法做故障随机模拟
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(B217): 基于多原则比较和蒙特卡洛模拟的RGV动态调度模型|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018btlw/240206/1699832.shtml|2018
confidence: 高
```

---

## FD-491（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-491
problem_type: 排序优化
domain: 制造排程/装配排序
method: 忽略颜色衔接(蓝色只能与白色间隔)
failure: 蓝车与其他色相邻违反喷涂要求
cause: 蓝车与其他色相邻违反喷涂要求
signal: 顺序被判不可行
lesson: 不要忽视颜色衔接硬约束; 先据此构图再排序
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(D027): 汽车总装线配置的优化模型研究|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018dtlw/240206/1699827.shtml|2018
confidence: 高
```

---

## FD-492（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-492
problem_type: 排序优化
domain: 制造排程/装配排序
method: 全量0-1规划求最小切换
failure: 车数多时变量指数增长, 无法求解
cause: 车数多时变量指数增长, 无法求解
signal: 模型不可解或极慢
lesson: 不要硬解大规模排序规划; 用图遍历+遗传算法求近优
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(D027): 汽车总装线配置的优化模型研究|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018dtlw/240206/1699827.shtml|2018
confidence: 高
```

---

## FD-493（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-493
problem_type: 排序优化
domain: 制造排程/装配排序
method: 不先定位黑色车
failure: 黑色车特殊要求未优先处理, 搜索空间过大
cause: 黑色车特殊要求未优先处理, 搜索空间过大
signal: 求解效率低、易陷局部最优
lesson: 不要全量随机初始化; 先手工填入强约束车(黑车)缩小规模
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(D027): 汽车总装线配置的优化模型研究|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018dtlw/240206/1699827.shtml|2018
confidence: 高
```

---

## FD-494（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-494
problem_type: 排序优化
domain: 制造排程/装配排序
method: 单纯贪心填色
failure: 局部连续但尾部复杂色无法衔接
cause: 局部连续但尾部复杂色无法衔接
signal: 末尾出现不可填空位
lesson: 不要只用贪心; 末尾复杂色用有向图+遗传算法全局协调
avoid: 
source: 2018年全国大学生数学建模竞赛论文展示(D027): 汽车总装线配置的优化模型研究|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2018qgdxssxjmjslwzs_2018dtlw/240206/1699827.shtml|2018
confidence: 高
```

---

## FD-495（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-495
problem_type: 决策优化/排队论
domain: 交通运营/司乘匹配
method: 只算蓄车池等待, 忽略返城空载成本
failure: 返城有空载费且损失潜在市区客源, 单向估算失真
cause: 返城有空载费且损失潜在市区客源, 单向估算失真
signal: 决策偏离真实最优
lesson: 不要单边估算; 同时建模等待成本与返城空载/机会成本比较
avoid: 
source: 2019数学建模竞赛B题优秀论文-基于'互联网+'机场的出租车问题|https://blog.csdn.net/weixin_43796658/article/details/103402800|2019
confidence: 高
```

---

## FD-496（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-496
problem_type: 决策优化/排队论
domain: 交通运营/司乘匹配
method: 用单一平均到港比例α
failure: α受季节/时段/天气等强烈影响, 均值掩盖波动
cause: α受季节/时段/天气等强烈影响, 均值掩盖波动
signal: 高峰/恶劣天气决策错误
lesson: 不要取固定α; 用AHP综合多因素权重动态估算
avoid: 
source: 2019数学建模竞赛B题优秀论文-基于'互联网+'机场的出租车问题|https://blog.csdn.net/weixin_43796658/article/details/103402800|2019
confidence: 高
```

---

## FD-497（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-497
problem_type: 决策优化/排队论
domain: 交通运营/司乘匹配
method: 设单上车点
failure: 单服务台成瓶颈, 乘车区吞吐受限
cause: 单服务台成瓶颈, 乘车区吞吐受限
signal: 乘客等待长、蓄车池溢出
lesson: 不要单点瓶颈; 用两条并行车道设上车点提升吞吐
avoid: 
source: 2019数学建模竞赛B题优秀论文-基于'互联网+'机场的出租车问题|https://blog.csdn.net/weixin_43796658/article/details/103402800|2019
confidence: 高
```

---

## FD-498（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-498
problem_type: 决策优化/排队论
domain: 交通运营/司乘匹配
method: 长短途无差别排队
failure: 短途车占蓄车池久、收益低, 逐渐流失
cause: 短途车占蓄车池久、收益低, 逐渐流失
signal: 短途乘客打车难
lesson: 不要长短途一律; 设短途绿色通道(如≤3公里优先)平衡收益
avoid: 
source: 2019数学建模竞赛B题优秀论文-基于'互联网+'机场的出租车问题|https://blog.csdn.net/weixin_43796658/article/details/103402800|2019
confidence: 高
```

---

## FD-499（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-499
problem_type: 决策优化/资源规划
domain: 游戏策略/动态规划
method: 起点少买食物、多买水
failure: 食物单价高于水, 村庄补食物不划算, 应在起点一次买足
cause: 食物单价高于水, 村庄补食物不划算, 应在起点一次买足
signal: 后续资金被食物补给吞掉, 剩余资金偏低
lesson: 不要在起点吝啬买食物; 食物贵应在起点按满载上限多买, 水可在村庄补
avoid: 
source: 2020年数学建模B题国二论文: 穿越沙漠的最佳策略|https://max.book118.com/html/2023/0911/6205213114005225.shtm|2020
confidence: 高
```

---

## FD-500（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-500
problem_type: 决策优化/资源规划
domain: 游戏策略/动态规划
method: 忽略村庄补给的'先使用后记账'优化
failure: 村庄补给时序组合爆炸, 朴素枚举不可行
cause: 村庄补给时序组合爆炸, 朴素枚举不可行
signal: 算法超时或无法求解
lesson: 不要朴素穷举补给; 用'先使用后记账'+剪枝处理资源缺口
avoid: 
source: 2020年数学建模B题国二论文: 穿越沙漠的最佳策略|https://max.book118.com/html/2023/0911/6205213114005225.shtm|2020
confidence: 高
```

---

## FD-501（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-501
problem_type: 决策优化/资源规划
domain: 游戏策略/动态规划
method: 不确定天气按全高温/全晴朗单一假设
failure: 实际天气随机, 单一极端假设偏离期望最优
cause: 实际天气随机, 单一极端假设偏离期望最优
signal: 实际收益波动大、非最优
lesson: 不要取单一天气假设; 用概率与数学期望量化策略收益
avoid: 
source: 2020年数学建模B题国二论文: 穿越沙漠的最佳策略|https://max.book118.com/html/2023/0911/6205213114005225.shtm|2020
confidence: 高
```

---

## FD-502（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-502
problem_type: 决策优化/资源规划
domain: 游戏策略/动态规划
method: 多玩家直接套单玩家最优
failure: 人人走最短路会重复路径、互相拖累, 陷入损人不利己均衡
cause: 人人走最短路会重复路径、互相拖累, 陷入损人不利己均衡
signal: 整体收益下降
lesson: 不要忽略博弈; 多玩家用纳什均衡分配路线(如最短路+次短路)
avoid: 
source: 2020年数学建模B题国二论文: 穿越沙漠的最佳策略|https://max.book118.com/html/2023/0911/6205213114005225.shtm|2020
confidence: 高
```

---

## FD-503（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-503
problem_type: 优化决策
domain: 电力系统/经济调度
method: 只求最小购电费用忽略线路限值
failure: 便宜机组集中出力使某线路潮流超安全限值
cause: 便宜机组集中出力使某线路潮流超安全限值
signal: 预案造成输电阻塞, 违规
lesson: 不要只优化经济; 必须把线路潮流限值作为硬约束
avoid: 
source: 电力市场的输电阻塞管理(2004全国大学生数学建模竞赛全国二等奖论文)|https://m.diyifanwen.net/wenku/1417729.html|2004
confidence: 高
```

---

## FD-504（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-504
problem_type: 优化决策
domain: 电力系统/经济调度
method: 阻塞费用规则不公平(只罚序外)
failure: 序内少发与序外多发均产生阻塞成本, 单边计费失真
cause: 序内少发与序外多发均产生阻塞成本, 单边计费失真
signal: 市场方与机组方争议
lesson: 不要单边计费; 序内少发按清算价与段价差、序外多发按段价分别结算
avoid: 
source: 电力市场的输电阻塞管理(2004全国大学生数学建模竞赛全国二等奖论文)|https://m.diyifanwen.net/wenku/1417729.html|2004
confidence: 高
```

---

## FD-505（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-505
problem_type: 优化决策
domain: 电力系统/经济调度
method: 忽略爬坡速率约束
failure: 机组相邻时段出力变化受限, 跨时段大幅调整不可行
cause: 机组相邻时段出力变化受限, 跨时段大幅调整不可行
signal: 预案不可执行
lesson: 不要忽略爬坡速率; 把它写入经济调度约束
avoid: 
source: 电力市场的输电阻塞管理(2004全国大学生数学建模竞赛全国二等奖论文)|https://m.diyifanwen.net/wenku/1417729.html|2004
confidence: 高
```

---

## FD-506（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-506
problem_type: 优化决策
domain: 电力系统/经济调度
method: 用等比例分配出力
failure: 未按段价排序, 贵机组先发推高清算价
cause: 未按段价排序, 贵机组先发推高清算价
signal: 购电费用明显高于最优
lesson: 不要等比例分配; 按段价由低到高优先调用便宜容量
avoid: 
source: 电力市场的输电阻塞管理(2004全国大学生数学建模竞赛全国二等奖论文)|https://m.diyifanwen.net/wenku/1417729.html|2004
confidence: 高
```

---

## FD-507（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-507
problem_type: 评价分类
domain: 建筑设计/综合评价
method: 等权简单加权
failure: 忽略各指标重要性差异, 把经济/舒适/安全等同对待
cause: 忽略各指标重要性差异, 把经济/舒适/安全等同对待
signal: 不同等权设定下方案排名剧烈翻转
lesson: 避免对多属性方案直接用等权求和, 须用AHP或熵权法客观赋权后再综合
avoid: 
source: 2010数模D题 宿舍方案优化设计(基于AHP的学生宿舍设计方案评价)|https://m.renrendoc.com/paper/231326836.html|2010
confidence: 高
```

---

## FD-508（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-508
problem_type: 评价分类
domain: 建筑设计/综合评价
method: 硬性阈值判定(达标/不达标二值化)
failure: 未处理'舒适''方便'等定性模糊指标
cause: 未处理'舒适''方便'等定性模糊指标
signal: 同一方案在阈值微调后结论反转
lesson: 避免用硬性阈值判定模糊指标, 改用模糊综合评价或线性隶属度映射到[0,1]
avoid: 
source: 2010数模D题 宿舍方案优化设计(基于AHP的学生宿舍设计方案评价)|https://m.renrendoc.com/paper/231326836.html|2010
confidence: 高
```

---

## FD-509（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-509
problem_type: 评价分类
domain: 建筑设计/综合评价
method: 仅用准则层权重对各方案排序
failure: 未计算指标层到目标的组合权重
cause: 未计算指标层到目标的组合权重
signal: 方案2在舒适/安全单准则最优, 但综合并非第一
lesson: 避免只用准则层权重排序, 须计算组合权重(准则权重×指标权重)再做综合评价
avoid: 
source: 2010数模D题 宿舍方案优化设计(基于AHP的学生宿舍设计方案评价)|https://m.renrendoc.com/paper/231326836.html|2010
confidence: 高
```

---

## FD-510（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-510
problem_type: 评价分类
domain: 建筑设计/综合评价
method: 主观把差异指标(如防盗)设为常数
failure: 为简化把本可量化/有差异的指标假设相同
cause: 为简化把本可量化/有差异的指标假设相同
signal: 放松'防盗系数相同'假设后方案4优势收窄
lesson: 避免把本可据方案特征取值的指标假设为常数, 应基于平面图标定各方案实际值
avoid: 
source: 2010数模D题 宿舍方案优化设计(基于AHP的学生宿舍设计方案评价)|https://m.renrendoc.com/paper/231326836.html|2010
confidence: 高
```

---

## FD-511（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-511
problem_type: 评价分类
domain: 食品科学/质量评价
method: 直接用两组评酒员评分均值比较
failure: 未做显著性检验与可信度比较
cause: 未做显著性检验与可信度比较
signal: 两组对同一样品排名差异很大
lesson: 避免直接采信原始均值, 须先做双向显著性检验/置信区间法判定哪组更可信(本例红酒取第一组、白酒取第二组)
avoid: 
source: 葡萄酒的质量分析与评价(A335, 2012高教社杯全国大学生数学建模竞赛优秀候选论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2012qgdxssxjmjslwzs/121030/1191829.shtml|2012
confidence: 高
```

---

## FD-512（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-512
problem_type: 评价分类
domain: 食品科学/质量评价
method: 把全部高度相关理化指标直接放入回归
failure: 指标间强相关未降维
cause: 指标间强相关未降维
signal: 回归系数与常识相反或方差膨胀
lesson: 避免把高度相关指标直接塞入回归, 先用PCA/典型相关降维再建模
avoid: 
source: 葡萄酒的质量分析与评价(A335, 2012高教社杯全国大学生数学建模竞赛优秀候选论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2012qgdxssxjmjslwzs/121030/1191829.shtml|2012
confidence: 高
```

---

## FD-513（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-513
problem_type: 评价分类
domain: 食品科学/质量评价
method: 人为设定固定阈值对葡萄分级
failure: 未用数据驱动的分级方法
cause: 未用数据驱动的分级方法
signal: 同一阈值区间内样本过多, 等级无意义
lesson: 避免人为硬阈值分级, 改用均值聚类/优势因子矩阵等数据驱动方式定级
avoid: 
source: 葡萄酒的质量分析与评价(A335, 2012高教社杯全国大学生数学建模竞赛优秀候选论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2012qgdxssxjmjslwzs/121030/1191829.shtml|2012
confidence: 高
```

---

## FD-514（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-514
problem_type: 评价分类
domain: 食品科学/质量评价
method: 仅看两两相关系数判断指标联系
failure: 多指标混杂, 简单相关无法剥离
cause: 多指标混杂, 简单相关无法剥离
signal: 多个相关系数同时显著却互相矛盾
lesson: 避免只看两两相关, 用典型相关/逐步回归分离主次关联并给出可解释方程
avoid: 
source: 葡萄酒的质量分析与评价(A335, 2012高教社杯全国大学生数学建模竞赛优秀候选论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2012qgdxssxjmjslwzs/121030/1191829.shtml|2012
confidence: 高
```

---

## FD-515（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-515
problem_type: 评价分类
domain: 地产规划/综合评价
method: 仅按参筹者满意度最大设计(忽略开发商利益)
failure: 过分追求网民购房意愿, 削弱开发商利益最大化
cause: 过分追求网民购房意愿, 削弱开发商利益最大化
signal: 方案II投资回报率18%<25%红线
lesson: 避免单目标最大化, 必须把投资回报率≥25%作为硬约束纳入规划, 用双目标/分层序列法兼顾
avoid: 
source: 1D11001-D001 众筹筑屋规划方案设计(2015高教社杯全国大学生数学建模竞赛国家一等奖论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2015qgdxssxjmjslwzs/210621/1700975.shtml|2015
confidence: 高
```

---

## FD-516（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-516
problem_type: 评价分类
domain: 地产规划/综合评价
method: 忽略增值率20%普宅免税临界点
failure: 未核算房型一增值率21.62%已超免税阈值
cause: 未核算房型一增值率21.62%已超免税阈值
signal: 房型一增值率21.62%>20%
lesson: 避免忽略税务临界, 将增值率20%普宅免税条件纳入约束, 微调配比/售价可显著增收益(本例调价后收益增919万元)
avoid: 
source: 1D11001-D001 众筹筑屋规划方案设计(2015高教社杯全国大学生数学建模竞赛国家一等奖论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2015qgdxssxjmjslwzs/210621/1700975.shtml|2015
confidence: 高
```

---

## FD-517（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-517
problem_type: 评价分类
domain: 地产规划/综合评价
method: 把跨量级指标(成本亿元/套数百)直接相加进目标
failure: 未做归一化处理
cause: 未做归一化处理
signal: 目标函数对套数变化不敏感
lesson: 避免跨量级指标直接求和, 须先归一化或取对数再组合
avoid: 
source: 1D11001-D001 众筹筑屋规划方案设计(2015高教社杯全国大学生数学建模竞赛国家一等奖论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2015qgdxssxjmjslwzs/210621/1700975.shtml|2015
confidence: 高
```

---

## FD-518（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-518
problem_type: 评价分类
domain: 地产规划/综合评价
method: 把房型9/10计入容积率
failure: 未注意赛题规则中房型9/10不列入容积率计算
cause: 未注意赛题规则中房型9/10不列入容积率计算
signal: 容积率超上限约束
lesson: 避免混淆计入/不计入容积率的房型, 按赛题规则用0-1系数区分(本例房型9/10不计入)
avoid: 
source: 1D11001-D001 众筹筑屋规划方案设计(2015高教社杯全国大学生数学建模竞赛国家一等奖论文)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2015qgdxssxjmjslwzs/210621/1700975.shtml|2015
confidence: 高
```

---

## FD-519（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-519
problem_type: 评价分类
domain: 交通评价/微观仿真
method: 仅定性讨论开放利弊
failure: 缺乏仿真/数学模型
cause: 缺乏仿真/数学模型
signal: 论文只有文字结论无前后延时差数据
lesson: 避免只定性, 须用元胞自动机/交通流模型给出前后延时差等定量证据
avoid: 
source: 小区开放对道路通行能力的影响(2016年高教社杯全国大学生数学建模竞赛一等奖, 南京大学)|https://simlab.nju.edu.cn/0f/8d/c30091a462733/page.htm|2016
confidence: 高
```

---

## FD-520（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-520
problem_type: 评价分类
domain: 交通评价/微观仿真
method: 忽略小区出入口分合流效应
failure: 只看交叉口延误缩短, 漏掉出入口合流排队
cause: 只看交叉口延误缩短, 漏掉出入口合流排队
signal: 简化模型前后延时差恒正, 完整模型出现负值
lesson: 避免忽略小区出入口分合流效应, 须同时计入交叉口延误缩短与出入口排队增长两项相反作用
avoid: 
source: 小区开放对道路通行能力的影响(2016年高教社杯全国大学生数学建模竞赛一等奖, 南京大学)|https://simlab.nju.edu.cn/0f/8d/c30091a462733/page.htm|2016
confidence: 高
```

---

## FD-521（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-521
problem_type: 评价分类
domain: 交通评价/微观仿真
method: 用BP神经网络建评价体系
failure: 数据驱动模型不适配小样本缺数据场景
cause: 数据驱动模型不适配小样本缺数据场景
signal: 指标权重随样本波动大
lesson: 避免在本就缺数据的题目硬上BP神经网络, 优先AHP等数据要求低的方法
avoid: 
source: 小区开放对道路通行能力的影响(2016年高教社杯全国大学生数学建模竞赛一等奖, 南京大学)|https://simlab.nju.edu.cn/0f/8d/c30091a462733/page.htm|2016
confidence: 高
```

---

## FD-522（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-522
problem_type: 评价分类
domain: 交通评价/微观仿真
method: 一刀切认为开放必缓解拥堵
failure: 未区分车流量与小区内部结构条件
cause: 未区分车流量与小区内部结构条件
signal: 前后延时差为负的比率与车流量在0.01显著性水平正相关
lesson: 避免一刀切, 须用控制变量法区分车流量/内部道路长度/节点数等条件再给开放策略
avoid: 
source: 小区开放对道路通行能力的影响(2016年高教社杯全国大学生数学建模竞赛一等奖, 南京大学)|https://simlab.nju.edu.cn/0f/8d/c30091a462733/page.htm|2016
confidence: 高
```

---

## FD-523（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-523
problem_type: 评价分类
domain: 体育赛程/综合评价
method: 仅主观(AHP)赋权
failure: 忽略各指标数据本身的客观差异
cause: 忽略各指标数据本身的客观差异
signal: 不同专家赋权得到不同排名
lesson: 避免单一主观赋权, 用AHP+熵权组合赋权兼顾经验与数据客观差异
avoid: 
source: nba赛程的分析与评价数学建模论文(2008高教社杯D题获奖论文)|https://www.wenkub.com/doc/357211.html|2008
confidence: 高
```

---

## FD-524（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-524
problem_type: 评价分类
domain: 体育赛程/综合评价
method: 只看对手强度, 忽略背靠背/连续客场
failure: 疲劳类指标被忽视
cause: 疲劳类指标被忽视
signal: 背靠背次数全联盟跨度达15-23, 差异巨大
lesson: 避免只重对手强度, 必须纳入背靠背次数与连续客场之旅等疲劳指标
avoid: 
source: nba赛程的分析与评价数学建模论文(2008高教社杯D题获奖论文)|https://www.wenkub.com/doc/357211.html|2008
confidence: 高
```

---

## FD-525（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-525
problem_type: 评价分类
domain: 体育赛程/综合评价
method: 沿用原随机'赛3场'安排
failure: 未做结构优化
cause: 未做结构优化
signal: 原商业价值仅1068.2
lesson: 避免沿用原始安排, 用0-1规划在平衡约束下最大化目标(本例商业价值提升54.95%)
avoid: 
source: nba赛程的分析与评价数学建模论文(2008高教社杯D题获奖论文)|https://www.wenkub.com/doc/357211.html|2008
confidence: 高
```

---

## FD-526（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-526
problem_type: 评价分类
domain: 体育赛程/综合评价
method: 忽略休息时间分布均匀度(方差)
failure: 只盯总场次, 不看间隔分布
cause: 只盯总场次, 不看间隔分布
signal: 魔术时间间隔方差最小0.36796而部分队远大于此
lesson: 避免忽略休息均匀度, 用两场比赛间隔的方差刻画赛程友好度
avoid: 
source: nba赛程的分析与评价数学建模论文(2008高教社杯D题获奖论文)|https://www.wenkub.com/doc/357211.html|2008
confidence: 高
```

---

## FD-527（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-527
problem_type: 评价分类
domain: 气象评价/统计检验
method: 网格预报值直接与站点实测值相减
failure: 未做站点-网格空间匹配(插值)
cause: 未做站点-网格空间匹配(插值)
signal: 坐标不对应, 误差量级异常
lesson: 避免直接错位相减, 先用最邻近点插值或改进反距离加权平均(δ=0.3)把网格值映射到91个站点再比较
avoid: 
source: 雨量预报方法的评价模型(伍利兵等, 工程数学学报2005; 2005高教社杯全国大学生数学建模竞赛全国一等奖)|https://blog.sciencenet.cn/upload/blog/file/2008/11/20081112222131814898.pdf|2005
confidence: 高
```

---

## FD-528（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-528
problem_type: 评价分类
domain: 气象评价/统计检验
method: 仅用单一RMSE
failure: 单指标片面
cause: 单指标片面
signal: 两方法RMSE接近, 无法判定
lesson: 避免单指标, 同时用误差均值E/方差D/误差平方和根多指标(本例最近邻法方法一平方和根449.44<方法二474.22)
avoid: 
source: 雨量预报方法的评价模型(伍利兵等, 工程数学学报2005; 2005高教社杯全国大学生数学建模竞赛全国一等奖)|https://blog.sciencenet.cn/upload/blog/file/2008/11/20081112222131814898.pdf|2005
confidence: 高
```

---

## FD-529（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-529
problem_type: 评价分类
domain: 气象评价/统计检验
method: 只用绝对误差忽略雨量等级
failure: 未对雨量分等级
cause: 未对雨量分等级
signal: 小雨量绝对误差占比大但公众不敏感
lesson: 避免只用绝对误差, 按7级雨量定义满意度/相对误差函数(级差0→满意1, 级差6→0)
avoid: 
source: 雨量预报方法的评价模型(伍利兵等, 工程数学学报2005; 2005高教社杯全国大学生数学建模竞赛全国一等奖)|https://blog.sciencenet.cn/upload/blog/file/2008/11/20081112222131814898.pdf|2005
confidence: 高
```

---

## FD-530（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-530
problem_type: 评价分类
domain: 气象评价/统计检验
method: 只看误差均值选方法
failure: 忽略误差方差
cause: 忽略误差方差
signal: 方法二误差方差大于方法一
lesson: 避免只看均值, 须比较误差方差D以挑选更稳定(波动更小)的方法
avoid: 
source: 雨量预报方法的评价模型(伍利兵等, 工程数学学报2005; 2005高教社杯全国大学生数学建模竞赛全国一等奖)|https://blog.sciencenet.cn/upload/blog/file/2008/11/20081112222131814898.pdf|2005
confidence: 高
```

---

## FD-531（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-531
problem_type: 评价分类
domain: 人岗匹配/分类评价
method: 仅按笔试排序录用
failure: 忽视面试表现与岗位要求
cause: 忽视面试表现与岗位要求
signal: 综合权重qij与笔试排名不一致
lesson: 避免只按笔试, 须用AHP融合笔试(按r)、面试与岗位要求得综合权重qij再分配
avoid: 
source: 公务员招聘(2004年高教社杯获得者论文: 层次分析法+0-1整数规划)|https://wenku.baidu.com/view/18f658bf68ec0975f46527d3240c844769eaa08e.html|2004
confidence: 高
```

---

## FD-532（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-532
problem_type: 评价分类
domain: 人岗匹配/分类评价
method: 忽略志愿约束
failure: 未做双向选择
cause: 未做双向选择
signal: 分配到未申报的类别
lesson: 避免忽略志愿, 用申报矩阵S(第一/二志愿/未报)转双向权重, 并强制未报类xij=0
avoid: 
source: 公务员招聘(2004年高教社杯获得者论文: 层次分析法+0-1整数规划)|https://wenku.baidu.com/view/18f658bf68ec0975f46527d3240c844769eaa08e.html|2004
confidence: 高
```

---

## FD-533（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-533
problem_type: 评价分类
domain: 人岗匹配/分类评价
method: 用匈牙利算法做多人类-多类分配
failure: 问题本质是多对多0-1规划而非1-1指派
cause: 问题本质是多对多0-1规划而非1-1指派
signal: 每类Mj>1, 匈牙利无法处理
lesson: 避免硬套匈牙利算法, 用0-1整数规划max ΣΣxij·qij并加类容量约束
avoid: 
source: 公务员招聘(2004年高教社杯获得者论文: 层次分析法+0-1整数规划)|https://wenku.baidu.com/view/18f658bf68ec0975f46527d3240c844769eaa08e.html|2004
confidence: 高
```

---

## FD-534（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-534
problem_type: 评价分类
domain: 人岗匹配/分类评价
method: 笔试面试固定等权
failure: 未设比例系数r
cause: 未设比例系数r
signal: 部门偏好与权重不符
lesson: 避免固定等权, 用比例系数r(由部门对笔试/面试的重视程度定)区分二者权重
avoid: 
source: 公务员招聘(2004年高教社杯获得者论文: 层次分析法+0-1整数规划)|https://wenku.baidu.com/view/18f658bf68ec0975f46527d3240c844769eaa08e.html|2004
confidence: 高
```

---

## FD-535（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-535
problem_type: 评价分类
domain: 运动力学/击球评价
method: 仅用扭矩(力臂)解释甜区
failure: 忽略球棒振动与转动惯量
cause: 忽略球棒振动与转动惯量
signal: 末端出球并非最大
lesson: 避免纯扭矩刚体解释, 须建含转动惯量与振动模态的动力学模型
avoid: 
source: 2010 MCM Problem A 棒球甜区建模论文(自然振动模态与节点分析)|https://www.doc88.com/p-4334721419338.html|2010
confidence: 高
```

---

## FD-536（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-536
problem_type: 评价分类
domain: 运动力学/击球评价
method: 假设球棒为纯刚体
failure: 忽略柔性振动
cause: 忽略柔性振动
signal: 模型输出无节点/无手感项
lesson: 避免把球棒当纯刚体, 须作柔性梁求自然振动模态与节点(本例一级≈215Hz、二级≈670Hz、三级≈1252Hz)
avoid: 
source: 2010 MCM Problem A 棒球甜区建模论文(自然振动模态与节点分析)|https://www.doc88.com/p-4334721419338.html|2010
confidence: 高
```

---

## FD-537（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-537
problem_type: 评价分类
domain: 运动力学/击球评价
method: 仅看最大出球速度定甜区
failure: 忽略舒适度(振动对手的力)
cause: 忽略舒适度(振动对手的力)
signal: 高初速点手感差、易界外
lesson: 避免单看出球速度, 须同时最小化对手振动力(节点处最小)
avoid: 
source: 2010 MCM Problem A 棒球甜区建模论文(自然振动模态与节点分析)|https://www.doc88.com/p-4334721419338.html|2010
confidence: 高
```

---

## FD-538（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-538
problem_type: 评价分类
domain: 运动力学/击球评价
method: 忽略材料差异(木/铝)
failure: 假设材料无关
cause: 假设材料无关
signal: 铝棒甜区/性能异于木
lesson: 避免忽略材料(COR与质量分布), 须比较木(梣木)与铝的参数差异及corking影响
avoid: 
source: 2010 MCM Problem A 棒球甜区建模论文(自然振动模态与节点分析)|https://www.doc88.com/p-4334721419338.html|2010
confidence: 高
```

---

## FD-539（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-539
problem_type: 评价分类
domain: 体育评价/综合排名
method: 直接合计原始胜场
failure: 忽略不同项目赛季长度差异
cause: 忽略不同项目赛季长度差异
signal: 不同项目胜场量级差倍
lesson: 避免直接合计原始胜场, 须按赛季长度转为有效胜率标准化后再比较
avoid: 
source: 2011 MCM Problem A: College Coaching Legends (COMAP官方成绩页, 杰出奖含北大/清华)|https://www.contest.comap.com/undergraduate/contests/mcm/contests/2011/results|2011
confidence: 中
```

---

## FD-540（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-540
problem_type: 评价分类
domain: 体育评价/综合排名
method: 忽略项目难度
failure: 未做难度校正
cause: 未做难度校正
signal: 项目间竞争强度差异显著
lesson: 避免忽略项目难度, 用赛季长度/竞争强度校正因子消除不可比
avoid: 
source: 2011 MCM Problem A: College Coaching Legends (COMAP官方成绩页, 杰出奖含北大/清华)|https://www.contest.comap.com/undergraduate/contests/mcm/contests/2011/results|2011
confidence: 中
```

---

## FD-541（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-541
problem_type: 评价分类
domain: 体育评价/综合排名
method: 等权综合多指标
failure: 未赋权
cause: 未赋权
signal: 排名对权重敏感
lesson: 避免等权, 用AHP/熵权赋权并对权重做敏感性分析
avoid: 
source: 2011 MCM Problem A: College Coaching Legends (COMAP官方成绩页, 杰出奖含北大/清华)|https://www.contest.comap.com/undergraduate/contests/mcm/contests/2011/results|2011
confidence: 中
```

---

## FD-542（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-542
problem_type: 评价分类
domain: 体育评价/综合排名
method: 忽略时代(ERA)差异
failure: 未做历史背景校正
cause: 未做历史背景校正
signal: 早期与近期教练不可直接比
lesson: 避免忽略时代, 须做历史背景/时代(ERA)校正再比较
avoid: 
source: 2011 MCM Problem A: College Coaching Legends (COMAP官方成绩页, 杰出奖含北大/清华)|https://www.contest.comap.com/undergraduate/contests/mcm/contests/2011/results|2011
confidence: 中
```

---

## FD-547（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-547
problem_type: 评价分类
domain: 人力资源/战略评价
method: 仅看人力成本
failure: 单指标评价
cause: 单指标评价
signal: 部门与战略不匹配
lesson: 避免只看成本, 须用模糊综合评价量化战略契合与部门间距离
avoid: 
source: Strategic Human Resource Management and Corporate Performance (ICM 2015 MCM C 人力资本论文, scirp)|https://scirp.org/journal/paperabs.aspx?paperid=90134|2015
confidence: 高
```

---

## FD-548（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-548
problem_type: 评价分类
domain: 人力资源/战略评价
method: 静态配置不动态
failure: 忽略动态演化
cause: 忽略动态演化
signal: 高流失下职位完整性骤降
lesson: 避免静态配置, 须用动态模型(Lyapunov/Pajek)模拟流失-补员演化
avoid: 
source: Strategic Human Resource Management and Corporate Performance (ICM 2015 MCM C 人力资本论文, scirp)|https://scirp.org/journal/paperabs.aspx?paperid=90134|2015
confidence: 高
```

---

## FD-549（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-549
problem_type: 评价分类
domain: 人力资源/战略评价
method: 忽略流失率情景
failure: 单情景假设
cause: 单情景假设
signal: 18%与35%流失预算差异巨大
lesson: 避免单情景, 须做多流失率(18%/25%/35%)情景分析定预算(本例18%→34.22σ)
avoid: 
source: Strategic Human Resource Management and Corporate Performance (ICM 2015 MCM C 人力资本论文, scirp)|https://scirp.org/journal/paperabs.aspx?paperid=90134|2015
confidence: 高
```

---

## FD-550（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-550
problem_type: 评价分类
domain: 人力资源/战略评价
method: 均匀培训投入
failure: 未识别最关键因素
cause: 未识别最关键因素
signal: 敏感性显示各层级人数影响最大
lesson: 避免均匀投入, 优先保障对人力资本价值影响最大的层级(各层级员工数量)编制
avoid: 
source: Strategic Human Resource Management and Corporate Performance (ICM 2015 MCM C 人力资本论文, scirp)|https://scirp.org/journal/paperabs.aspx?paperid=90134|2015
confidence: 高
```

---

## FD-551（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-551
problem_type: 物理建模
domain: 流体力学/几何反演
method: 忽略变位直接套用无变位罐容表
failure: 地基变形致罐体倾斜/偏转, 油位探针读数偏离真实液面
cause: 地基变形致罐体倾斜/偏转, 油位探针读数偏离真实液面
signal: 低液位(h≈0.1m)相对误差可达 60%+, 整体平均影响率 4.87%
lesson: 避免假设罐体无变位; 标定前必须先识别变位参数, 并用分段积分修正罐容表
avoid: 
source: 储油罐的变位识别与罐容表标定(2010高教社杯全国大学生数学建模竞赛A题一等奖, 重庆大学 王建等)|https://www.docin.com/p-476164223.html|2010
confidence: 高
```

---

## FD-552（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-552
problem_type: 物理建模
domain: 流体力学/几何反演
method: 用单一近似公式替代分段积分求倾斜罐容积
failure: 倾斜后油位计在高/低位失效, 存在无法测量的 5 个分区, 单一公式无法覆盖
cause: 倾斜后油位计在高/低位失效, 存在无法测量的 5 个分区, 单一公式无法覆盖
signal: 变位后理论值与实测值之差 0.0454–0.0910 m³, 相对误差 1.56%–5.18%
lesson: 避免对变位罐用单一闭式公式; 应分段积分并单独处理探针失效区(区域1/5体积)
avoid: 
source: 储油罐的变位识别与罐容表标定(2010高教社杯全国大学生数学建模竞赛A题一等奖, 重庆大学 王建等)|https://www.docin.com/p-476164223.html|2010
confidence: 高
```

---

## FD-553（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-553
problem_type: 物理建模
domain: 流体力学/几何反演
method: 球冠体体积直接忽略或粗略近似
failure: 实际罐两端球冠体积表达式复杂, 近似省略导致系统性偏差
cause: 实际罐两端球冠体积表达式复杂, 近似省略导致系统性偏差
signal: 模型对球冠部分积分困难, 参数估计可能偏离实际(论文自述缺点)
lesson: 避免直接丢弃球冠体积; 用蒙特卡洛模拟补算被忽略部分并验证一致度(重庆大学队达 99%)
avoid: 
source: 储油罐的变位识别与罐容表标定(2010高教社杯全国大学生数学建模竞赛A题一等奖, 重庆大学 王建等)|https://www.docin.com/p-476164223.html|2010
confidence: 高
```

---

## FD-554（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-554
problem_type: 物理建模
domain: 流体力学/几何反演
method: 仅用少量实测点做最小二乘参数估计
failure: V-h-变位参数 函数关系极复杂, 数据少易陷入局部最优/偏离真值
cause: V-h-变位参数 函数关系极复杂, 数据少易陷入局部最优/偏离真值
signal: 论文自述: 仅用部分数据估计, 变位参数与实际值可能相差较远
lesson: 避免只用部分实测点估计变位参数; 应等间距穷举或多段数据联合搜索, 以稳健标定
avoid: 
source: 储油罐的变位识别与罐容表标定(2010高教社杯全国大学生数学建模竞赛A题一等奖, 重庆大学 王建等)|https://www.docin.com/p-476164223.html|2010
confidence: 高
```

---

## FD-555（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-555
problem_type: 物理建模
domain: 轨道力学/最优控制
method: 匀速下降/分段匀速规划
failure: 燃料非最优, 且难同时满足主减速末速57m/s与落点精度
cause: 燃料非最优, 且难同时满足主减速末速57m/s与落点精度
signal: 燃料消耗大、落点偏差超限
lesson: 避免匀速下降; 主减速段应采用推力最大且方向恒定的最优制导(线性正切制导率), 以燃料最优到达57m/s
avoid: 
source: 嫦娥三号软着陆轨道设计与控制策略(2014高教社杯全国大学生数学建模竞赛优秀论文选登, 东南大学 吉张鹤轩等)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2014qgdxssxjmjslwzs/211022/1700790.shtml|2014
confidence: 高
```

---

## FD-556（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-556
problem_type: 物理建模
domain: 轨道力学/最优控制
method: 忽略月面地形直接定点着陆
failure: 虹湾存在陨石坑与障碍, 直接定点可能落入危险区
cause: 虹湾存在陨石坑与障碍, 直接定点可能落入危险区
signal: 落点落入危险区/障碍
lesson: 避免忽略高程图; 须用K均值聚类+栅格化筛选最大安全半径落点(东南大学最优点(1275,1000))
avoid: 
source: 嫦娥三号软着陆轨道设计与控制策略(2014高教社杯全国大学生数学建模竞赛优秀论文选登, 东南大学 吉张鹤轩等)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2014qgdxssxjmjslwzs/211022/1700790.shtml|2014
confidence: 高
```

---

## FD-557（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-557
problem_type: 物理建模
domain: 轨道力学/最优控制
method: 正面求解近月点位置(无反推)
failure: 问题一只给高度约束, 正向条件不足、方程组欠定
cause: 问题一只给高度约束, 正向条件不足、方程组欠定
signal: 无法直接定位近月点经纬度
lesson: 避免正面硬解; 用主减速段水平位移逆推近月点经纬度(东南大学反推得水平位移385.21m)
avoid: 
source: 嫦娥三号软着陆轨道设计与控制策略(2014高教社杯全国大学生数学建模竞赛优秀论文选登, 东南大学 吉张鹤轩等)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2014qgdxssxjmjslwzs/211022/1700790.shtml|2014
confidence: 高
```

---

## FD-558（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-558
problem_type: 物理建模
domain: 轨道力学/最优控制
method: 忽略初始轨道误差传播
failure: 近月点位置/速度误差会沿轨迹放大到落点
cause: 近月点位置/速度误差会沿轨迹放大到落点
signal: 落点偏差超限、控制失效
lesson: 避免不做误差分析; 须用协方差/敏感度分析量化初始误差影响(水平位移对推力敏感度0.189)
avoid: 
source: 嫦娥三号软着陆轨道设计与控制策略(2014高教社杯全国大学生数学建模竞赛优秀论文选登, 东南大学 吉张鹤轩等)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2014qgdxssxjmjslwzs/211022/1700790.shtml|2014
confidence: 高
```

---

## FD-559（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-559
problem_type: 物理建模
domain: 结构力学/几何优化
method: 仅按美观设计桌面形状(如矩形桌面+垂直腿)
failure: 矩形对称桌面配垂直腿, 任意水平力即倾覆, 无实际稳定性
cause: 矩形对称桌面配垂直腿, 任意水平力即倾覆, 无实际稳定性
signal: 桌子遇水平力倒塌
lesson: 避免只求美观; 桌面形状须使支撑腿构成稳定多边形(如黄金梯形/圆形), 保证重心投影落在支撑区内
avoid: 
source: 创意平板折叠桌(2014高教社杯全国大学生数学建模竞赛三等奖论文, 开槽长度序列与几何模型)|https://m.renrendoc.com/p-23651209.html|2014
confidence: 高
```

---

## FD-560（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-560
problem_type: 物理建模
domain: 结构力学/几何优化
method: 经验试错开槽(不建模)
failure: 开槽长度由钢筋滑动起止点决定, 经验值难保证桌面平整
cause: 开槽长度由钢筋滑动起止点决定, 经验值难保证桌面平整
signal: 展开后桌面不平、桌脚不齐
lesson: 避免凭经验开槽; 须由平铺与折叠两状态钢筋到铰链距离差精确求各木条开槽长度(单侧序列20.093→0cm)
avoid: 
source: 创意平板折叠桌(2014高教社杯全国大学生数学建模竞赛三等奖论文, 开槽长度序列与几何模型)|https://m.renrendoc.com/p-23651209.html|2014
confidence: 高
```

---

## FD-561（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-561
problem_type: 物理建模
domain: 结构力学/几何优化
method: 取满20根木条不留间隙
failure: 锯缝与刀片厚度占用宽度, 满根数导致木条相互干涉松动
cause: 锯缝与刀片厚度占用宽度, 满根数导致木条相互干涉松动
signal: 木条装不下/相互摩擦松动
lesson: 避免忽略加工间隙; 木条数应在50/2.5=20基础上减去锯缝取19根
avoid: 
source: 创意平板折叠桌(2014高教社杯全国大学生数学建模竞赛三等奖论文, 开槽长度序列与几何模型)|https://m.renrendoc.com/p-23651209.html|2014
confidence: 高
```

---

## FD-562（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-562
problem_type: 物理建模
domain: 结构力学/几何优化
method: 忽略重心/支撑稳定性校核
failure: 折叠桌重心可能落在支撑脚外
cause: 折叠桌重心可能落在支撑脚外
signal: 桌体易倒
lesson: 避免不做静力学校核; 须验证重心投影落在支撑腿构成的稳定区域内
avoid: 
source: 创意平板折叠桌(2014高教社杯全国大学生数学建模竞赛三等奖论文, 开槽长度序列与几何模型)|https://m.renrendoc.com/p-23651209.html|2014
confidence: 高
```

---

## FD-563（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-563
problem_type: 物理建模
domain: 天文几何/视运动
method: 直接用赤纬判断月出时刻
failure: 赤纬属赤道系, 月出于地平需地平系高度, 缺坐标变换
cause: 赤纬属赤道系, 月出于地平需地平系高度, 缺坐标变换
signal: 时刻偏差大
lesson: 避免直接用赤纬判月出; 须做赤道→地平坐标变换(球面三角)求地平高度再反解时角
avoid: 
source: 月上柳梢头(2015高教社杯全国大学生数学建模竞赛C题, 含国一优秀论文 PDF)|https://yuque.com/mcm/cumcm/om8nox|2015
confidence: 高
```

---

## FD-564（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-564
problem_type: 物理建模
domain: 天文几何/视运动
method: 忽视大气折射与视差修正
failure: 低空天体高度受折射影响, 阈值附近误差显著
cause: 低空天体高度受折射影响, 阈值附近误差显著
signal: 黄昏/月出时刻不准
lesson: 避免在低高度角判定时忽略大气折射; 改进模型应加折射与视差修正(改进模型章节)
avoid: 
source: 月上柳梢头(2015高教社杯全国大学生数学建模竞赛C题, 含国一优秀论文 PDF)|https://yuque.com/mcm/cumcm/om8nox|2015
confidence: 高
```

---

## FD-565（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-565
problem_type: 物理建模
domain: 天文几何/视运动
method: 把'月上柳梢头'当固定时刻查表
failure: 诗句是模糊情景, 无唯一时刻, 且随日期地点变化
cause: 诗句是模糊情景, 无唯一时刻, 且随日期地点变化
signal: 无法推广与验证
lesson: 避免把模糊诗意当固定时刻; 须先量化定义(月亮高度角10°–15°)再建模
avoid: 
source: 月上柳梢头(2015高教社杯全国大学生数学建模竞赛C题, 含国一优秀论文 PDF)|https://yuque.com/mcm/cumcm/om8nox|2015
confidence: 高
```

---

## FD-566（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-566
problem_type: 物理建模
domain: 天文几何/视运动
method: 忽略农历十五共线约束逐日搜索
failure: 全年遍历效率低, 且丢失物理意义
cause: 全年遍历效率低, 且丢失物理意义
signal: 计算量大、结论无解释
lesson: 避免盲目逐日遍历; 利用'日落月出同时=地日月共线≈农历十五'缩到每月十三~十八六天判定
avoid: 
source: 月上柳梢头(2015高教社杯全国大学生数学建模竞赛C题, 含国一优秀论文 PDF)|https://yuque.com/mcm/cumcm/om8nox|2015
confidence: 高
```

---

## FD-567（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-567
problem_type: 物理建模
domain: 海洋工程/悬链线力学
method: 忽略锚链悬链线(当直线段)
failure: 锚链在水下呈悬链弯曲, 直线近似误算张力与末端夹角
cause: 锚链在水下呈悬链弯曲, 直线近似误算张力与末端夹角
signal: 末端夹角/张力算错, 系泊失效
lesson: 避免把锚链当直线; 必须用悬链线或分段集中质量法描述链形再求末端与海床夹角
avoid: 
source: 2016年数学建模竞赛A题优秀论文(系泊系统的设计, 基于力学分析)|https://www.bodocs.net/doc/4920463175.html|2016
confidence: 高
```

---

## FD-568（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-568
problem_type: 物理建模
domain: 海洋工程/悬链线力学
method: 固定重物球质量不做调节(36m/s工况)
failure: 原重物偏小, 36m/s下钢桶9.66°、锚链夹角21°超约束, 设备工作效果差
cause: 原重物偏小, 36m/s下钢桶9.66°、锚链夹角21°超约束, 设备工作效果差
signal: 钢桶倾角/锚链夹角超限, 系统不稳
lesson: 避免固定重物质量; 须以重物球质量为调节变量(二分/搜索)使钢桶<5°、锚链夹角<16°
avoid: 
source: 2016年数学建模竞赛A题优秀论文(系泊系统的设计, 基于力学分析)|https://www.bodocs.net/doc/4920463175.html|2016
confidence: 高
```

---

## FD-569（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-569
problem_type: 物理建模
domain: 海洋工程/悬链线力学
method: 多变量同时调参(锚链型号+长度+重物)
failure: 变量耦合难归因, 易陷入无效组合
cause: 变量耦合难归因, 易陷入无效组合
signal: 找不到满足约束的配置
lesson: 避免多变量盲目同调; 问题3应控制单一变量先定锚链型号(Ⅴ型), 再联合优化长度与重物质量
avoid: 
source: 2016年数学建模竞赛A题优秀论文(系泊系统的设计, 基于力学分析)|https://www.bodocs.net/doc/4920463175.html|2016
confidence: 高
```

---

## FD-570（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-570
problem_type: 物理建模
domain: 海洋工程/悬链线力学
method: 仅静力、不校核极端海况
failure: 12/24m/s稳态满足, 但36m/s+1.5m/s流极端工况下失稳
cause: 12/24m/s稳态满足, 但36m/s+1.5m/s流极端工况下失稳
signal: 设计在风暴下失效
lesson: 避免只校核中低海况; 须以最大风速36m/s、最大流速1.5m/s作为设计指标校核
avoid: 
source: 2016年数学建模竞赛A题优秀论文(系泊系统的设计, 基于力学分析)|https://www.bodocs.net/doc/4920463175.html|2016
confidence: 高
```

---

## FD-571（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-571
problem_type: 物理建模
domain: 医学成像/积分反演
method: 直接反投影不滤波
failure: 高频噪声被放大, 直接反投影产生星状伪影与模糊
cause: 高频噪声被放大, 直接反投影产生星状伪影与模糊
signal: 图像不清、边缘振铃
lesson: 避免直接反投影; 须用滤波反投影(FBP), 先滤波(如Ram-Lak/Shepp-Logan)再反投影
avoid: 
source: 基于单目标优化模型和图像重建算法的CT系统研究(2017国赛国家一等奖A题优秀论文)|https://m.renrendoc.com/p-84299505.html|2017
confidence: 高
```

---

## FD-572（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-572
problem_type: 物理建模
domain: 医学成像/积分反演
method: 忽略旋转中心标定
failure: 旋转中心未知则所有投影几何错位
cause: 旋转中心未知则所有投影几何错位
signal: 重建图像整体偏移/失真
lesson: 避免跳过标定; 须先用模板最小二乘/遍历搜索标定旋转中心(国一得(9.3040,6.2149))与探测器间距(0.2768mm)
avoid: 
source: 基于单目标优化模型和图像重建算法的CT系统研究(2017国赛国家一等奖A题优秀论文)|https://m.renrendoc.com/p-84299505.html|2017
confidence: 高
```

---

## FD-573（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-573
problem_type: 物理建模
domain: 医学成像/积分反演
method: 探测器间距当已知常量
failure: 实际间距0.2768mm须由模板几何反推, 错值致尺度失真
cause: 实际间距0.2768mm须由模板几何反推, 错值致尺度失真
signal: 重建尺寸错误
lesson: 避免把探测器单元距离当已知; 须由模板边缘对应的探测器个数(椭圆短轴29、圆直径109)几何反推间距
avoid: 
source: 基于单目标优化模型和图像重建算法的CT系统研究(2017国赛国家一等奖A题优秀论文)|https://m.renrendoc.com/p-84299505.html|2017
confidence: 高
```

---

## FD-574（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-574
problem_type: 物理建模
domain: 医学成像/积分反演
method: 忽略吸收系数非负/单色近似失效
failure: 多色X射线或负值导致物理不可解
cause: 多色X射线或负值导致物理不可解
signal: 出现负吸收率伪影
lesson: 避免忽略物理约束; 重建后应施加吸收系数非负约束并考虑单色平行束近似适用范围
avoid: 
source: 基于单目标优化模型和图像重建算法的CT系统研究(2017国赛国家一等奖A题优秀论文)|https://m.renrendoc.com/p-84299505.html|2017
confidence: 高
```

---

## FD-575（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-575
problem_type: 物理建模
domain: 热传导/多层介质PDE
method: 稳态近似忽略瞬态
failure: 升温过程皮肤可能短时超47°C, 仅凭稳态达标会误判安全
cause: 升温过程皮肤可能短时超47°C, 仅凭稳态达标会误判安全
signal: 安全误判(实际灼伤风险)
lesson: 避免稳态近似; 须做一维瞬态导热求解, 检查整个工作时段皮肤温度是否超47°C且>44°C累计≤5min
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛A题优秀论文(高温作业专用服装设计, 多层织物热传递模型)|https://max.book118.com/html/2024/0523/8137051072006072.shtm|2018
confidence: 高
```

---

## FD-576（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-576
problem_type: 物理建模
domain: 热传导/多层介质PDE
method: 忽略外表面对流边界(用绝热/固定温度)
failure: Ⅰ层与外界换热由对流主导, 绝热假设失真
cause: Ⅰ层与外界换热由对流主导, 绝热假设失真
signal: 温度场偏差大
lesson: 避免忽略对流; 须用Robin边界(牛顿冷却), 并由附件2实测最小二乘反演对流系数h≈8.64202
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛A题优秀论文(高温作业专用服装设计, 多层织物热传递模型)|https://max.book118.com/html/2024/0523/8137051072006072.shtm|2018
confidence: 高
```

---

## FD-577（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-577
problem_type: 物理建模
domain: 热传导/多层介质PDE
method: 把Ⅱ层/Ⅳ层当题设固定
failure: 问题2/3要求反向设计厚度, 固定则无法满足安全约束
cause: 问题2/3要求反向设计厚度, 固定则无法满足安全约束
signal: 找不到可行设计
lesson: 避免把层厚当已知; 须以Ⅱ层(及问题3的Ⅳ层)为决策变量枚举/优化搜索满足安全约束的最薄配置(19.20mm/21.9mm+6.4mm)
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛A题优秀论文(高温作业专用服装设计, 多层织物热传递模型)|https://max.book118.com/html/2024/0523/8137051072006072.shtm|2018
confidence: 高
```

---

## FD-578（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-578
problem_type: 物理建模
domain: 热传导/多层介质PDE
method: 忽略层间界面条件
failure: 界面热流不连续导致温度跳变错误
cause: 界面热流不连续导致温度跳变错误
signal: 层间温度不连续、解失真
lesson: 避免忽略界面; 须施加界面热流量相等、接触面温度相等条件(多层耦合PDE)
avoid: 
source: 2018年高教社杯全国大学生数学建模竞赛A题优秀论文(高温作业专用服装设计, 多层织物热传递模型)|https://max.book118.com/html/2024/0523/8137051072006072.shtm|2018
confidence: 高
```

---

## FD-579（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-579
problem_type: 物理建模
domain: 流体力学/微分方程
method: 忽略燃油可压缩(用不可压假设)
failure: 压力-密度状态方程缺失, 压力波动算不出
cause: 压力-密度状态方程缺失, 压力波动算不出
signal: 模型失真, 压力恒定错误
lesson: 避免忽略可压缩; 须用注1 dp/dρ=E/ρ 与附件3分段拟合E(p), 把压力-密度耦合进ODE
avoid: 
source: 2019全国大学生数学建模竞赛(高教社杯)A题题解(高压油管的压力控制)|https://www.cnblogs.com/Mayfly-nymph/p/11753977.html|2019
confidence: 高
```

---

## FD-580（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-580
problem_type: 物理建模
domain: 流体力学/微分方程
method: 固定单向阀开启时长不优化
failure: 进油量与10次/秒喷油不匹配, 压力长期漂移
cause: 进油量与10次/秒喷油不匹配, 压力长期漂移
signal: 压力偏离100MPa/150MPa目标
lesson: 避免固定时长; 须以开启时长为决策变量二分/网格搜索使周期净流量≈0(100MPa→0.285ms)
avoid: 
source: 2019全国大学生数学建模竞赛(高教社杯)A题题解(高压油管的压力控制)|https://www.cnblogs.com/Mayfly-nymph/p/11753977.html|2019
confidence: 高
```

---

## FD-581（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-581
problem_type: 物理建模
domain: 流体力学/微分方程
method: 忽略弹性模量随压力非线性
failure: E(p)非线性, 常数E导致ρ(p)关系错误
cause: E(p)非线性, 常数E导致ρ(p)关系错误
signal: 压力-密度换算偏差
lesson: 避免把弹性模量当常数; 须由附件3数据分段拟合E(p)再积分/离散求ρ(p)
avoid: 
source: 2019全国大学生数学建模竞赛(高教社杯)A题题解(高压油管的压力控制)|https://www.cnblogs.com/Mayfly-nymph/p/11753977.html|2019
confidence: 高
```

---

## FD-582（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-582
problem_type: 物理建模
domain: 流体力学/微分方程
method: 问题3直接套用单喷嘴策略
failure: 双喷孔+减压阀下流量不匹配, 波动增大
cause: 双喷孔+减压阀下流量不匹配, 波动增大
signal: 压力控制失败
lesson: 避免直接套用; 须采用定差/定比策略+减压阀闭环反馈, 使进油匹配总喷油并消除超压
avoid: 
source: 2019全国大学生数学建模竞赛(高教社杯)A题题解(高压油管的压力控制)|https://www.cnblogs.com/Mayfly-nymph/p/11753977.html|2019
confidence: 高
```

---

## FD-583（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-583
problem_type: 物理建模
domain: 多体协同控制/刚体动力学
method: 把鼓当单质点忽略转动自由度
failure: 发力误差必致鼓面倾斜, 单质点模型丢失倾斜
cause: 发力误差必致鼓面倾斜, 单质点模型丢失倾斜
signal: 无法解释/控制倾斜, 球偏离竖直
lesson: 避免忽略转动; 须用欧拉转动分解为竖直平动+绕X/Y两自由度小角度转动(倾斜角0.2124°–0.4123°)
avoid: 
source: “同心协力”策略研究(2019高教社杯全国大学生数学建模竞赛B题, 同心鼓颠球, 赛题全文)|https://www.icourse163.org/forum/1237117709/topic-1342038971.htm|2019
confidence: 高
```

---

## FD-584（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-584
problem_type: 物理建模
domain: 多体协同控制/刚体动力学
method: 假设发力精确无误差
failure: 现实中发力时机/力度有误差, 鼓面倾斜使球斜跳
cause: 现实中发力时机/力度有误差, 鼓面倾斜使球斜跳
signal: 颠球失败/次数骤降
lesson: 避免假设理想发力; 须建模发力误差(时滞0.2–0.4s、高斯噪声)并设计拉力/站位/倾斜三方面的调整策略
avoid: 
source: “同心协力”策略研究(2019高教社杯全国大学生数学建模竞赛B题, 同心鼓颠球, 赛题全文)|https://www.icourse163.org/forum/1237117709/topic-1342038971.htm|2019
confidence: 高
```

---

## FD-585（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-585
problem_type: 物理建模
domain: 多体协同控制/刚体动力学
method: 碰撞用完全弹性/忽略恢复系数
failure: 球-鼓能量损失显著, 完全弹性高估反弹高度
cause: 球-鼓能量损失显著, 完全弹性高估反弹高度
signal: 反弹高度算错
lesson: 避免忽略能量损失; 须用恢复系数e∈[0.6,0.85]的动量+能量守恒处理球鼓碰撞
avoid: 
source: “同心协力”策略研究(2019高教社杯全国大学生数学建模竞赛B题, 同心鼓颠球, 赛题全文)|https://www.icourse163.org/forum/1237117709/topic-1342038971.htm|2019
confidence: 高
```

---

## FD-586（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-586
problem_type: 物理建模
domain: 多体协同控制/刚体动力学
method: 沿用理想策略不做现实调整
failure: 问题1理想策略在倾斜下失效
cause: 问题1理想策略在倾斜下失效
signal: 策略不可实施
lesson: 避免直接套用理想策略; 须据问题2倾斜模型从拉力大小、鼓面倾斜、站位三方面调整(问题3/4)
avoid: 
source: “同心协力”策略研究(2019高教社杯全国大学生数学建模竞赛B题, 同心鼓颠球, 赛题全文)|https://www.icourse163.org/forum/1237117709/topic-1342038971.htm|2019
confidence: 高
```

---

## FD-587（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-587
problem_type: 物理建模
domain: 热传导/有限差分
method: 忽略升温斜率约束
failure: 升温>3°C/s损伤元件/焊膏, 降温>6°C/s致开裂
cause: 升温>3°C/s损伤元件/焊膏, 降温>6°C/s致开裂
signal: 工艺失败、虚焊或元件损坏
lesson: 避免忽略斜率; 须把升温≤3°C/s、降温≤6°C/s作为硬约束校核炉温曲线
avoid: 
source: 国赛优秀论文2020年A题: 基于一维热传导方程的炉温曲线机理模型研究|http://www.madio.net/forum.php?mod=viewthread&tid=490621&extra=page%3D1&ordertype=1|2020
confidence: 高
```

---

## FD-588（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-588
problem_type: 物理建模
domain: 热传导/有限差分
method: 稳态近似忽略瞬态
failure: 板上温度滞后于炉温, 稳态会漏掉峰值与回流时间
cause: 板上温度滞后于炉温, 稳态会漏掉峰值与回流时间
signal: 曲线失真、误判工艺窗口
lesson: 避免稳态近似; 须用一维瞬态导热(集总参数+牛顿冷却)逐层差分求解
avoid: 
source: 国赛优秀论文2020年A题: 基于一维热传导方程的炉温曲线机理模型研究|http://www.madio.net/forum.php?mod=viewthread&tid=490621&extra=page%3D1&ordertype=1|2020
confidence: 高
```

---

## FD-589（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-589
problem_type: 物理建模
domain: 热传导/有限差分
method: 固定温区温度不优化
failure: 默认温区组合不满足面积最小/对称
cause: 默认温区组合不满足面积最小/对称
signal: 热冲击大、焊接质量差
lesson: 避免固定温区; 须以4组温区温度+带速为决策变量(模拟退火/爬山)优化217°C以上面积与对称性
avoid: 
source: 国赛优秀论文2020年A题: 基于一维热传导方程的炉温曲线机理模型研究|http://www.madio.net/forum.php?mod=viewthread&tid=490621&extra=page%3D1&ordertype=1|2020
confidence: 高
```

---

## FD-590（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-590
problem_type: 物理建模
domain: 热传导/有限差分
method: 忽略炉前/炉后及间隙温度
failure: 炉前25cm/炉后25cm/间隙5cm无控温, 温度由相邻温区决定
cause: 炉前25cm/炉后25cm/间隙5cm无控温, 温度由相邻温区决定
signal: 边界温度算错
lesson: 避免忽略无控温区; 须用直肋导热模型描述炉前(m=0.05)/炉后(m=0.017)及间隙的温度过渡
avoid: 
source: 国赛优秀论文2020年A题: 基于一维热传导方程的炉温曲线机理模型研究|http://www.madio.net/forum.php?mod=viewthread&tid=490621&extra=page%3D1&ordertype=1|2020
confidence: 高
```

---

## FD-591（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-591
problem_type: 图模型/选址优化
domain: 图论/应急设施选址/警力调度
method: 均匀布点、不分析发案率
failure: 
cause: 
signal: 6个节点到最近平台距离>3km, 出警超3分钟
lesson: 避免凭直觉均匀布点; 必须以发案率与最短路距离驱动选址, 先验证'3km/3分钟'覆盖是否全员满足
avoid: 
source: Python小白的数学建模课-A1.国赛赛题类型分析(含2011B题)|https://blog.csdn.net/youcans/article/details/117410678|2011
confidence: 中
```

---

## FD-592（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-592
problem_type: 图模型/选址优化
domain: 图论/应急设施选址/警力调度
method: 仅按就近原则分配管辖
failure: 
cause: 
signal: 各平台管辖节点数/发案率差异大, 变异系数偏高
lesson: 不要只追求平均响应最短而忽视均衡; 应同时以'工作量变异系数'为约束/目标, 在0.90931min与0.96659min两方案间选均衡更优者
avoid: 
source: Python小白的数学建模课-A1.国赛赛题类型分析(含2011B题)|https://blog.csdn.net/youcans/article/details/117410678|2011
confidence: 中
```

---

## FD-593（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-593
problem_type: 图模型/选址优化
domain: 图论/应急设施选址/警力调度
method: 封锁调度用'总路程最小'目标
failure: 
cause: 
signal: 某一封锁路口到达时间远大于其余
lesson: 避免用总路程/总时间最小化来调度封锁; 对'全面完成'类任务必须用最大到达时间最小(minimax), 否则短板路口拖垮全局
avoid: 
source: Python小白的数学建模课-A1.国赛赛题类型分析(含2011B题)|https://blog.csdn.net/youcans/article/details/117410678|2011
confidence: 中
```

---

## FD-594（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-594
problem_type: 图模型/选址优化
domain: 图论/应急设施选址/警力调度
method: 新增平台只看'新增数最少
failure: 
cause: 
signal: 最长出警时间或变异系数未达预期
lesson: 不要只追求少建平台; 应在'新增数最少'与'最长出警≤2.71min、变异系数尽量小(0.1526)'之间做 Pareto 权衡, 逐步求精确定位置
avoid: 
source: Python小白的数学建模课-A1.国赛赛题类型分析(含2011B题)|https://blog.csdn.net/youcans/article/details/117410678|2011
confidence: 中
```

---

## FD-595（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-595
problem_type: 图模型/选址优化
domain: 图论/应急设施选址/警力调度
method: 忽略路网单行/拥堵做静态最短路
failure: 
cause: 
signal: 模型响应时间偏乐观
lesson: 不要把最短路距离直接等同于出警时间而不做敏感性说明; 至少应给出车速假设并讨论拥堵下的鲁棒性
avoid: 
source: Python小白的数学建模课-A1.国赛赛题类型分析(含2011B题)|https://blog.csdn.net/youcans/article/details/117410678|2011
confidence: 中
```

---

## FD-596（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-596
problem_type: 图匹配/数字图像处理
domain: 计算机视觉/图像拼接/组合复原
method: 对横纵切碎片仍用纯边界贪心配对
failure: 
cause: 
signal: 纯边界匹配在问题二出现明显错配, 英文正确率仅65.1%
lesson: 避免对横纵切/双面碎片套用纵切的纯边界贪心; 必须先按行特征聚类缩小空间, 再在类内做边界匹配
avoid: 
source: 碎纸片的拼接复原-西南交通大学(2013高教社杯全国大学生数学建模竞赛优秀论文选登)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700228.shtml|2013
confidence: 高
```

---

## FD-597（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-597
problem_type: 图匹配/数字图像处理
domain: 计算机视觉/图像拼接/组合复原
method: 忽略行结构, 只用总灰度误差最小拼接
failure: 
cause: 
signal: 复原结果行列错位
lesson: 不要只用单一总误差指标; 对横纵切问题应显式建模'行聚类+行内排序+行间上下匹配'三层结构
avoid: 
source: 碎纸片的拼接复原-西南交通大学(2013高教社杯全国大学生数学建模竞赛优秀论文选登)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700228.shtml|2013
confidence: 高
```

---

## FD-598（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-598
problem_type: 图匹配/数字图像处理
domain: 计算机视觉/图像拼接/组合复原
method: 聚类类数完全自动确定(中文15类/英文16类直接采用)
failure: 
cause: 
signal: 聚类结果类大小不一
lesson: 不要盲信自动聚类的类数; 应结合'原文件每行19张'等先验, 人工干预合并/降维到每类19张
avoid: 
source: 碎纸片的拼接复原-西南交通大学(2013高教社杯全国大学生数学建模竞赛优秀论文选登)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700228.shtml|2013
confidence: 高
```

---

## FD-599（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-599
problem_type: 图匹配/数字图像处理
domain: 计算机视觉/图像拼接/组合复原
method: 问题三忽略正反面(a/b面)直接匹配
failure: 
cause: 
signal: 匹配结果自相矛盾
lesson: 避免对双面碎片做单面匹配; 必须用'两次特征匹配'(先一面配, 再对匹配面二次校验)锁定同面同类
avoid: 
source: 碎纸片的拼接复原-西南交通大学(2013高教社杯全国大学生数学建模竞赛优秀论文选登)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700228.shtml|2013
confidence: 高
```

---

## FD-600（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-600
problem_type: 图匹配/数字图像处理
domain: 计算机视觉/图像拼接/组合复原
method: 依赖完全自动、拒绝任何人工干预
failure: 
cause: 
signal: 自动排序与正确答案有偏差
lesson: 不要追求零人工干预而牺牲精度; 在聚类合并等关键歧义处引入少量人工干预可显著提升正确率
avoid: 
source: 碎纸片的拼接复原-西南交通大学(2013高教社杯全国大学生数学建模竞赛优秀论文选登)|https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmlw_2013qgdxssxjmjslwzs/220808/1700228.shtml|2013
confidence: 高
```

---

## FD-601（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-601
problem_type: 图模型/路径优化与排班
domain: 最短路/分区巡检/人力资源排班
method: 套用中国邮递员问题(CPP)/欧拉回路
failure: 
cause: 
signal: 结果要求遍历边而非覆盖点, 与赛题'26个点'矛盾
lesson: 避免把'巡检点覆盖'误当作'街道遍历'; 先判断是点路由(TSP/分区)还是弧路由(CPP), 本题属前者
avoid: 
source: 2017年国赛高教杯数学建模D题巡检线路的排班解题全过程文档及程序|https://blog.csdn.net/weixin_43292788/article/details/142359829|2017
confidence: 高
```

---

## FD-602（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-602
problem_type: 图模型/路径优化与排班
domain: 最短路/分区巡检/人力资源排班
method: 单条TSP回路覆盖全部26点
failure: 
cause: 
signal: 回路周期>>35min
lesson: 不要试图用一条回路覆盖所有点; 当总耗时超周期上限时必须多路线分区, 每条≤35min
avoid: 
source: 2017年国赛高教杯数学建模D题巡检线路的排班解题全过程文档及程序|https://blog.csdn.net/weixin_43292788/article/details/142359829|2017
confidence: 高
```

---

## FD-603（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-603
problem_type: 图模型/路径优化与排班
domain: 最短路/分区巡检/人力资源排班
method: 只看'人数最少'忽略均衡度
failure: 
cause: 
signal: 分区模型均衡度达0.35(偏大)
lesson: 不要只优化人数最少; 必须同时以均衡度(各路线时间max/min或方差)为约束/目标, 并采用轮倒制平衡长期工作量
avoid: 
source: 2017年国赛高教杯数学建模D题巡检线路的排班解题全过程文档及程序|https://blog.csdn.net/weixin_43292788/article/details/142359829|2017
confidence: 高
```

---

## FD-604（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-604
problem_type: 图模型/路径优化与排班
domain: 最短路/分区巡检/人力资源排班
method: 问题二忽略休息与进餐约束
failure: 
cause: 
signal: 按无休息排班会导致中途无人巡检
lesson: 避免对'含休息/进餐'的排班直接套用无休息模型; 应分段线路、增人轮换进餐(第一班需11人轮换)
avoid: 
source: 2017年国赛高教杯数学建模D题巡检线路的排班解题全过程文档及程序|https://blog.csdn.net/weixin_43292788/article/details/142359829|2017
confidence: 高
```

---

## FD-605（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-605
problem_type: 图模型/路径优化与排班
domain: 最短路/分区巡检/人力资源排班
method: 固时上班强行采用不分区4人下限
failure: 
cause: 
signal: 班次循环断裂
lesson: 不要把理论人数下限直接当可行排班; 须验证班次能否循环, 固时上班应取5人, 仅错时上班才能降到4人
avoid: 
source: 2017年国赛高教杯数学建模D题巡检线路的排班解题全过程文档及程序|https://blog.csdn.net/weixin_43292788/article/details/142359829|2017
confidence: 高
```

---

## FD-606（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-606
problem_type: 图模型/网络流与仿真
domain: 应急疏散/网络科学/元胞自动机
method: 标准Dijkstra静态最短路分配(不封口、不避危险区)
failure: 
cause: 
signal: 出口处人群堆积, 疏散时间异常长
lesson: 避免直接用裸最短路分配大人群; 必须给出口加容量上限(α)、剔除危险区边、设Visual Range(如21m)不可达, 否则模型失真
avoid: 
source: 2019 ICM Problem D 拆解笔记(Paper #1900007, O奖分析)|http://pzrain.github.io/COMAP/paper/2019D|2019
confidence: 高
```

---

## FD-607（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-607
problem_type: 图模型/网络流与仿真
domain: 应急疏散/网络科学/元胞自动机
method: 仅做2D模型不补3D可视化
failure: 
cause: 
signal: 论文表现力弱
lesson: 不要只停留在2D抽象; 对可三维实现的疏散/布局题, 用Pathfinder等做3D元胞自动机仿真并画热点图, 既能增色也能间接验证假设
avoid: 
source: 2019 ICM Problem D 拆解笔记(Paper #1900007, O奖分析)|http://pzrain.github.io/COMAP/paper/2019D|2019
confidence: 高
```

---

## FD-608（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-608
problem_type: 图模型/网络流与仿真
domain: 应急疏散/网络科学/元胞自动机
method: 以'通过人员比例'判定出口拥堵
failure: 
cause: 
signal: 密度增大出口1通过人数显著上升却未超比例限制, 实际不合理
lesson: 避免用'比例'而非'绝对人数'判定出口拥塞; 应同时约束绝对吞吐能力, 否则密度敏感性失真
avoid: 
source: 2019 ICM Problem D 拆解笔记(Paper #1900007, O奖分析)|http://pzrain.github.io/COMAP/paper/2019D|2019
confidence: 高
```

---

## FD-609（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-609
problem_type: 图模型/网络流与仿真
domain: 应急疏散/网络科学/元胞自动机
method: 忽略人群多样性(语言/团体/残疾)
failure: 
cause: 
signal: 赛题明确提及多样性却未充分体现
lesson: 不要只按移动速度简化人群; 对跨国场馆题应至少在指示牌多语言、团体引导等策略上体现多样性应对
avoid: 
source: 2019 ICM Problem D 拆解笔记(Paper #1900007, O奖分析)|http://pzrain.github.io/COMAP/paper/2019D|2019
confidence: 高
```

---

## FD-610（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-610
problem_type: 图模型/网络流与仿真
domain: 应急疏散/网络科学/元胞自动机
method: 把空间离散成稀疏网格后直接当连续移动
failure: 
cause: 
signal: 路径不连续
lesson: 避免网格过稀; 离散化后若移动显跳跃, 应加密网格(代价是Dijkstra耗时增加), 或在假设中说明
avoid: 
source: 2019 ICM Problem D 拆解笔记(Paper #1900007, O奖分析)|http://pzrain.github.io/COMAP/paper/2019D|2019
confidence: 高
```

---

## FD-611（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-611
problem_type: 排队论/医疗调度
domain: 医疗资源配置/排队网络/仿真
method: 纯FCFS排队安排所有非急症病人
failure: 
cause: 
signal: Wq=12.3天, 队列积压
lesson: 避免对所有病种用同一FCFS; 必须按'病种×手术日匹配度'设优先级, 让入院日尽量贴近其手术日, 可把利用率从58.4%提到83.0%
avoid: 
source: 眼科医院一等奖论文(2009高教社杯B题, M/M/79排队模型)|https://max.book118.com/html/2017/0923/134812897.shtm|2009
confidence: 高
```

---

## FD-612（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-612
problem_type: 排队论/医疗调度
domain: 医疗资源配置/排队网络/仿真
method: 忽略手术日约束直接排程
failure: 
cause: 
signal: 术前等待时间长
lesson: 不要脱离手术日表排入院; 入院决策应以'距最近合适手术日的间隔'为优先级核心
avoid: 
source: 眼科医院一等奖论文(2009高教社杯B题, M/M/79排队模型)|https://max.book118.com/html/2017/0923/134812897.shtm|2009
confidence: 高
```

---

## FD-613（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-613
problem_type: 排队论/医疗调度
domain: 医疗资源配置/排队网络/仿真
method: 周末不手术却仍按原优先级
failure: 
cause: 
signal: B从83%降到36.1%
lesson: 周末停刀时必须重算优先级(而非改手术日); 盲改白内障到周二四反而更差(B=29.0%), 应保留原手术日只调模型优先级
avoid: 
source: 眼科医院一等奖论文(2009高教社杯B题, M/M/79排队模型)|https://max.book118.com/html/2017/0923/134812897.shtm|2009
confidence: 高
```

---

## FD-614（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-614
problem_type: 排队论/医疗调度
domain: 医疗资源配置/排队网络/仿真
method: 用单一平均指标不仿真
failure: 
cause: 
signal: 问题三无法给出区间
lesson: 不要只报平均值; 对排队题应做仿真给出等待分布与置信区间(本题等待12/13天占71%, 区间约11-14天)
avoid: 
source: 眼科医院一等奖论文(2009高教社杯B题, M/M/79排队模型)|https://max.book118.com/html/2017/0923/134812897.shtm|2009
confidence: 高
```

---

## FD-615（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-615
problem_type: 排队论/医疗调度
domain: 医疗资源配置/排队网络/仿真
method: 固定床位比例随意设定
failure: 
cause: 
signal: 平均逗留时间非最优
lesson: 不要随意定固定比例; 问题五应以平均逗留最短为目标用整数规划/粒子群求解(典型 外伤8/白内障双16/单12/青光21/视网膜22)
avoid: 
source: 眼科医院一等奖论文(2009高教社杯B题, M/M/79排队模型)|https://max.book118.com/html/2017/0923/134812897.shtm|2009
confidence: 高
```

---

## FD-616（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-616
problem_type: 图模型/交通流仿真
domain: 交通工程/收费广场合并优化
method: 只做几何面积最小化设计收费广场
failure: 
cause: 
signal: 流量/容量比进入u型曲线高危区
lesson: 避免把收费广场当纯几何优化; 必须同时以吞吐量、事故率(PET)、成本为三目标, 流量/容量比与事故率呈u型, 需取平衡区
avoid: 
source: 美赛2017b题优秀论文总结(5篇O奖: 56731/68303/69427/70174/70545)|https://www.cnblogs.com/clover-blog/p/14322409.html|2017
confidence: 高
```

---

## FD-617（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-617
problem_type: 图模型/交通流仿真
domain: 交通工程/收费广场合并优化
method: 只追求最大吞吐量
failure: 
cause: 
signal: 事故率随吞吐上升
lesson: 不要单追最大吞吐; 用'最小风险最大流量'的图论合流或控制时间模型, 在吞吐与安全间权衡
avoid: 
source: 美赛2017b题优秀论文总结(5篇O奖: 56731/68303/69427/70174/70545)|https://www.cnblogs.com/clover-blog/p/14322409.html|2017
confidence: 高
```

---

## FD-618（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-618
problem_type: 图模型/交通流仿真
domain: 交通工程/收费广场合并优化
method: 忽略服务时间随机性(只用均值)
failure: 
cause: 
signal: 重交通下排队远超均值预测
lesson: 不要只用平均服务时间; 应假定服务时间独立同分布正态(均值15s、方差4), 用M/G/K排队而非M/M排队
avoid: 
source: 美赛2017b题优秀论文总结(5篇O奖: 56731/68303/69427/70174/70545)|https://www.cnblogs.com/clover-blog/p/14322409.html|2017
confidence: 高
```

---

## FD-619（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-619
problem_type: 图模型/交通流仿真
domain: 交通工程/收费广场合并优化
method: 不仿真直接给合并方案
failure: 
cause: 
signal: 轻重交通表现差异大
lesson: 避免只做解析; 必须用VISSIM等仿真在轻/重交通下验证吞吐、延迟、队长、合并点数, 并用PCA定位主因(延迟→吞吐、合并点队列→成本、合并点数→事故)
avoid: 
source: 美赛2017b题优秀论文总结(5篇O奖: 56731/68303/69427/70174/70545)|https://www.cnblogs.com/clover-blog/p/14322409.html|2017
confidence: 高
```

---

## FD-620（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-620
problem_type: 图模型/交通流仿真
domain: 交通工程/收费广场合并优化
method: 把自动驾驶与ETC当作无关因素忽略
failure: 
cause: 
signal: 混合车流下原方案性能下降
lesson: 不要忽略外生车辆结构; 自动驾驶应设专用AV车道, ETC比例升高时需重新评估合并风险与吞吐权衡
avoid: 
source: 美赛2017b题优秀论文总结(5篇O奖: 56731/68303/69427/70174/70545)|https://www.cnblogs.com/clover-blog/p/14322409.html|2017
confidence: 高
```

---

## FD-621（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-621
problem_type: 图模型/多旅行商(MTSP)分区
domain: 图论/最佳推销员回路/灾情巡视
method: 不分组做单条长回路
failure: 
cause: 
signal: 单组巡视时间远超24h
lesson: 避免对大规模巡游用单回路; 必须按组数分区, 每组从O出发回O, 限时内完成(本题至少4组)
avoid: 
source: 建模案例:最佳灾情巡视路线(1998 CUMCM B)|https://www.bodocs.net/doc/413476347.html|1998
confidence: 高
```

---

## FD-622（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-622
problem_type: 图模型/多旅行商(MTSP)分区
domain: 图论/最佳推销员回路/灾情巡视
method: 随机/任意分组后直接求回路
failure: 
cause: 
signal: α=54.2%(均衡很差)
lesson: 不要随机分组; 应先按O点最短路树的干枝聚类(同干枝同组、相邻干枝同组、长干枝配短干枝), 再按均衡度α微调(可降到11.69%)
avoid: 
source: 建模案例:最佳灾情巡视路线(1998 CUMCM B)|https://www.bodocs.net/doc/413476347.html|1998
confidence: 高
```

---

## FD-623（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-623
problem_type: 图模型/多旅行商(MTSP)分区
domain: 图论/最佳推销员回路/灾情巡视
method: 只取一个初始圈的二边逐次修正法
failure: 
cause: 
signal: 不同初值结果差异大
lesson: 不要用单一初值; 应同时用多种初值产生法(输入初值、对角线完全算法、随机搜2000个H圈)再取最优
avoid: 
source: 建模案例:最佳灾情巡视路线(1998 CUMCM B)|https://www.bodocs.net/doc/413476347.html|1998
confidence: 高
```

---

## FD-624（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-624
problem_type: 图模型/多旅行商(MTSP)分区
domain: 图论/最佳推销员回路/灾情巡视
method: 忽略停留时间只按路程分组
failure: 
cause: 
signal: 组时间=路程/35+停留 超24h
lesson: 不要只均衡路程; 限时问题须把停留时间(T=2h乡镇、t=1h村, 共69h)纳入, 加准则四使各组停留时间相等(4组各约17.25h)
avoid: 
source: 建模案例:最佳灾情巡视路线(1998 CUMCM B)|https://www.bodocs.net/doc/413476347.html|1998
confidence: 高
```

---

## FD-625（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-625
problem_type: 图模型/多旅行商(MTSP)分区
domain: 图论/最佳推销员回路/灾情巡视
method: 把最佳推销员回路当可精确求解
failure: 
cause: 
signal: 精确求解超时
lesson: 不要追求精确最优; 对53节点用Floyd完备图+近似算法(二边逐次修正)得近似最优解即可, 重点在分组均衡
avoid: 
source: 建模案例:最佳灾情巡视路线(1998 CUMCM B)|https://www.bodocs.net/doc/413476347.html|1998
confidence: 高
```

---

## FD-626（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-626
problem_type: 图模型/全覆盖路径规划
domain: 网格化矩形区域搜索路径/多组协同
method: 随机游走/无覆盖路径搜索
failure: 
cause: 
signal: 计算结果耗时巨大且无收敛
lesson: 避免随机游走, 必须用网格分区+蛇形扫描保证全境无遗漏覆盖
avoid: 
source: 地面搜索(2008高教社杯全国大学生数学建模竞赛C题)|https://www.bodocs.net/doc/307175172.html|2008
confidence: 高
```

---

## FD-627（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-627
problem_type: 图模型/全覆盖路径规划
domain: 网格化矩形区域搜索路径/多组协同
method: 用平均耗时代替最远队员耗时
failure: 
cause: 
signal: 平均时间<48h但实测最远队员>48h
lesson: 避免以平均时间为判据, 必须以'最远队员/最慢组耗时'作为能否按时完成的标准
avoid: 
source: 地面搜索(2008高教社杯全国大学生数学建模竞赛C题)|https://www.bodocs.net/doc/307175172.html|2008
confidence: 高
```

---

## FD-628（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-628
problem_type: 图模型/全覆盖路径规划
domain: 网格化矩形区域搜索路径/多组协同
method: 圆形滚动扫描(弧线运动)
failure: 
cause: 
signal: 模型中出现队员距离组长>1000m
lesson: 避免圆形滚动扫描, 须用S型直线扫描或MST树状链路保证全程通信可达
avoid: 
source: 地面搜索(2008高教社杯全国大学生数学建模竞赛C题)|https://www.bodocs.net/doc/307175172.html|2008
confidence: 高
```

---

## FD-629（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-629
problem_type: 图模型/全覆盖路径规划
domain: 网格化矩形区域搜索路径/多组协同
method: 单组大编制不分组(如50人不分)
failure: 
cause: 
signal: 末端失联或各组耗时差过大
lesson: 避免超大单组, 应按卫星电话数(3台)分3组并行, 每组内独立均衡
avoid: 
source: 地面搜索(2008高教社杯全国大学生数学建模竞赛C题)|https://www.bodocs.net/doc/307175172.html|2008
confidence: 高
```

---

## FD-630（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-630
problem_type: 系统科学/网络科学/多目标政策模型
domain: 星际移民社会系统 / 劳动力-教育-平等政策优化
method: 单目标最大化GDP
failure: 
cause: 
signal: 优化结果幸福感骤降、平等指标恶化
lesson: 避免单目标, 须用多目标/Pareto前沿显式权衡GDP与幸福感
avoid: 
source: ICM 2017 Problem F: Migration to Mars: Utopian Workforce of the 2100 Urban Society|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/problems|2017
confidence: 高
```

---

## FD-631（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-631
problem_type: 系统科学/网络科学/多目标政策模型
domain: 星际移民社会系统 / 劳动力-教育-平等政策优化
method: 越界纳入医疗/健康政策
failure: 
cause: 
signal: 赛题'排除医疗保健'被忽略
lesson: 避免越界, 严格按赛题边界(本题排除医疗)建模
avoid: 
source: ICM 2017 Problem F: Migration to Mars: Utopian Workforce of the 2100 Urban Society|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/problems|2017
confidence: 高
```

---

## FD-632（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-632
problem_type: 系统科学/网络科学/多目标政策模型
domain: 星际移民社会系统 / 劳动力-教育-平等政策优化
method: 静态/集总模型忽略可扩展性与动态
failure: 
cause: 
signal: 模型对群体规模敏感、无演化轨迹
lesson: 避免静态集总, 须用系统动力学+多层网络刻画可扩展与动态
avoid: 
source: ICM 2017 Problem F: Migration to Mars: Utopian Workforce of the 2100 Urban Society|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/problems|2017
confidence: 高
```

---

## FD-633（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-633
problem_type: 系统科学/网络科学/多目标政策模型
domain: 星际移民社会系统 / 劳动力-教育-平等政策优化
method: 忽略26个月发射窗口节律
failure: 
cause: 
signal: 补给批次过密、与航天常识冲突
lesson: 避免把星际补给当连续流, 须按26个月窗口离散化批次
avoid: 
source: ICM 2017 Problem F: Migration to Mars: Utopian Workforce of the 2100 Urban Society|https://contest.comap.com/undergraduate/contests/mcm/contests/2017/problems|2017
confidence: 高
```

---

## FD-634（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-634
problem_type: 多目标规划/运筹调度
domain: 城市公交线路发车调度
method: 全天固定发车间隔
failure: 
cause: 
signal: 满载率极端(>120%或<50%)、抱怨率飙升
lesson: 避免固定间隔, 须按客流分段(典型5段)分时调度
avoid: 
source: 公交车调度方案的优化模型(2001年B题)|http://www.bodocs.net/doc/4a17008335.html|2001
confidence: 高
```

---

## FD-635（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-635
problem_type: 多目标规划/运筹调度
domain: 城市公交线路发车调度
method: 单目标最小化车辆数
failure: 
cause: 
signal: 平均等待时间远超约束、抱怨百分比高
lesson: 避免单目标, 须多目标权衡公司效益与乘客利益
avoid: 
source: 公交车调度方案的优化模型(2001年B题)|http://www.bodocs.net/doc/4a17008335.html|2001
confidence: 高
```

---

## FD-636（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-636
problem_type: 多目标规划/运筹调度
domain: 城市公交线路发车调度
method: 只取一组权重做灵敏度分析
failure: 
cause: 
signal: 评阅意见'最好多取几组权系数进行比较
lesson: 避免单组权重, 须多组权重求Pareto前沿并比较
avoid: 
source: 公交车调度方案的优化模型(2001年B题)|http://www.bodocs.net/doc/4a17008335.html|2001
confidence: 高
```

---

## FD-637（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-637
problem_type: 多目标规划/运筹调度
domain: 城市公交线路发车调度
method: 忽略满载率下限(≥50%)
failure: 
cause: 
signal: 平峰满载率<50%
lesson: 避免只设上限, 满载率须双向约束(≤120%且一般≥50%)
avoid: 
source: 公交车调度方案的优化模型(2001年B题)|http://www.bodocs.net/doc/4a17008335.html|2001
confidence: 高
```

---

## FD-638（公开经验库·华数杯实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-638
problem_type: 多目标优化/组合优化
domain: 算力网络/电力-算力协同
method: 储能 LP 峰值约束写为 P - gb + gs ≤ 0
failure: 售电被强制为 0，优化退化为全电网买，解反常
cause: 约束方向写反，等价于 gs ≤ gb - P ≤ 0
signal: 解出现'不卖电反而亏'的反常值（gs=0）
lesson: LP 约束写完后做一次手工可行解对照，挡掉符号写反
avoid: 
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-639（公开经验库·华数杯实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-639
problem_type: 多目标优化/组合优化
domain: 算力网络/电力-算力协同
method: QoS 定义为 1 - delay/W（与'越早越好'绑定）
failure: 新能源感知排程下延迟变负→QoS 饱和 1.0，无分辨力
cause: 指标与绝对时延单调绑定，无下限阈值
signal: 所有 Pareto 解 QoS≈1.0
lesson: 改用'柔性任务完成时延 < ½ 最大容忍时延'的比例指标
avoid: 
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-640（公开经验库·华数杯实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-640
problem_type: 多目标优化/组合优化
domain: 算力网络/电力-算力协同
method: P4 placement 按逐到达循环（28800 次/调用 × 80 点）
failure: 子进程静默 exit 1、无输出（2 分钟超时）
cause: O(n) 循环未向量化，单代不可承受
signal: 进程无 stdout 直接退出
lesson: 改按任务类型聚合的 O(12) 向量化；输出重定向到日志文件排查
avoid: 
source: 2026华数杯C题 | 计算-电力协同调度 | 2026
confidence: 高
source_quality: 高
memory_type: human_replay
```

---


---

## FD-641（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-641
problem_type: 评价分类
domain: 网络科学/影响力评价
method: 仅看发文量
failure: 单指标评价
cause: 单指标评价
signal: 影响力低估
lesson: 避免只看出文量, 须结合中心度与被引多维评价
avoid: 
source: 2014 MCM Problem C: Networks|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## FD-642（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-642
problem_type: 评价分类
domain: 网络科学/影响力评价
method: 忽略自引与合著贡献分配
failure: 未清洗数据
cause: 未清洗数据
signal: 自引拉高引用数
lesson: 避免忽略自引与共著, 须清洗自引并按合著人数归一化贡献
avoid: 
source: 2014 MCM Problem C: Networks|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## FD-643（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-643
problem_type: 评价分类
domain: 网络科学/影响力评价
method: 用单一中心度排名
failure: 不同中心度刻画不同角色
cause: 不同中心度刻画不同角色
signal: 排名相互矛盾
lesson: 避免单中心度, 用PCA综合多中心度成统一影响力指数
avoid: 
source: 2014 MCM Problem C: Networks|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## FD-644（公开经验库·WorkBuddy9）

```yaml
failure_id: FD-644
problem_type: 评价分类
domain: 网络科学/影响力评价
method: 忽略时间权重
failure: 未对合作加权时间
cause: 未对合作加权时间
signal: 历史节点权重过高
lesson: 避免忽略时间, 给近期合作更高权重以反映当前影响力
avoid: 
source: 2014 MCM Problem C: Networks|https://www.contest.comap.com/undergraduate/contests/|2014
confidence: 中
```

---

## FD-645（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-645
problem_type: 优化决策
domain: 工业工程/生产质量管理
method: 固定样本(n,c)方案作为主方案
failure: 在p接近阈值时样本量浪费、且未贴合'序贯'题意
cause: 固定样本不随观测结果提前停止
signal: ASN曲线在p=0.10处峰值157，附近效率低
lesson: 质检抽样优先用序贯方案
avoid: 
source: 2024高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2024
confidence: 中
source_quality: 高
memory_type: human_replay
```

---

## FD-646（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-646
problem_type: 优化决策
domain: 工业工程/生产质量管理
method: fig5灵敏度图直接 zip 场景参数
failure: NameError scenarios 未定义 / ValueError 解包过多值
cause: 绘图时未显式绑定场景参数且 zip 长度不齐
signal: 运行报错
lesson: 绘图前显式绑定每组参数，zip 元组长度需对齐
avoid: 
source: 2024高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2024
confidence: 中
source_quality: 高
memory_type: human_replay
```

---

## FD-647（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-647
problem_type: 优化决策
domain: 工业工程/生产质量管理
method: JSON键以 str(float) 反查
failure: KeyError '0.02'
cause: JSON键为字符串'0.02'但检索用 str(float('0.02')) 经浮点往返不一致
signal: KeyError
lesson: JSON数值键统一用原始字符串迭代，避免浮点往返
avoid: 
source: 2024高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2024
confidence: 中
source_quality: 高
memory_type: human_replay
```

---

## FD-648（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-648
problem_type: 几何覆盖/测线优化
domain: 海洋测绘/多波束测深
method: 附件.xlsx 深度网格解析（rows[2] 读 x）
failure: x 坐标范围错成 20.8–197.2 m（应为 0–4 NM）
cause: 首版把 depth 网格行误当 x 轴，坐标错位
signal: x 范围异常、D.max 与题给不符
lesson: 解析 Excel 网格前先打印维度与首尾行列，明确 x/y/depth 的行列归属
avoid: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-649（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-649
problem_type: 几何覆盖/测线优化
domain: 海洋测绘/多波束测深
method: solve_q34 取 q3res['eta0_0.10']
failure: KeyError 'eta0_0.10'
cause: JSON 键为 'eta0_0.1'（float 格式化 0.10→0.1）
signal: KeyError
lesson: JSON 数值键统一用原始字符串迭代，避免浮点往返
avoid: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-650（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-650
problem_type: 几何覆盖/测线优化
domain: 海洋测绘/多波束测深
method: Q3 重叠率 d=xs_m[i]-xs_m[i-1]
failure: 重叠率算成 186% 而非 13%
cause: 位置递减使 d 为负
signal: 重叠率>100% 异常
lesson: 间距取绝对值 d=abs(...)
avoid: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-651（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-651
problem_type: 几何覆盖/测线优化
domain: 海洋测绘/多波束测深
method: np.linalg.eig 求协方差主方向
failure: 返回非实数特征值
cause: 对称矩阵用一般 eig 数值不稳
signal: 复数特征值
lesson: 对称矩阵改用 np.linalg.eigh
avoid: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-652（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-652
problem_type: 几何覆盖/测线优化
domain: 海洋测绘/多波束测深
method: Q4 初版旋转线段布设
failure: 漏测 9.21%
cause: 线段未延伸覆盖四角 + strike 角误算
signal: 栅格化漏测率>0
lesson: 线段两端各延伸 W_max/2 覆盖四角；取 φ=π/2(N-S) 与主导 E-W 梯度垂直
avoid: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-653（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-653
problem_type: 几何覆盖/测线优化
domain: 海洋测绘/多波束测深
method: pandoc 转 Word（figure 用 PDF）
failure: docx 图片丢失
cause: Word 不能内嵌显示 PDF 图片
signal: media 为空
lesson: 转 docx 前用 PyMuPDF 把 figure PDF 渲成 PNG
avoid: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-654（公开经验库·国赛实战）

source_quality: 高
memory_type: human_replay
```yaml
failure_id: FD-654
problem_type: 几何覆盖/测线优化
domain: 海洋测绘/多波束测深
method: pandoc 命令调用
failure: command not found
cause: winget 安装路径不在 PATH
signal: pandoc 不在 PATH
lesson: 用全路径调用（WinGet Packages 深路径）
avoid: 
source: 2023高教社杯全国大学生数学建模竞赛B题|http://www.mcm.edu.cn/|2023
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-655（公开经验库·国赛实战）

```yaml
failure_id: FD-655
problem_type: 优化决策
domain: 化学/催化工艺优化（乙醇偶合制 C4 烯烃）
method: 直接以随机森林预测峰值作为最优
failure: RF 平滑低估真实峰值，且一度选到无 HAP 组合(HAP=0)，物理错误
cause: 小样本高维下树模型对峰值平滑；无 HAP 为负对照未被排除
signal: 预测最优收率低于观测 A3；HAP=0 与 A11 负对照矛盾
lesson: 小样本响应面不可直接当最优；优化域须显式排除负对照(无 HAP)
avoid: 
source: 2021 高教社杯全国大学生数学建模竞赛 B 题（乙醇偶合制备 C4 烯烃） | 2021
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-656（公开经验库·国赛实战）

```yaml
failure_id: FD-656
problem_type: 优化决策
domain: 化学/催化工艺优化（乙醇偶合制 C4 烯烃）
method: 因素线性系数直接外推乙醇浓度方向
failure: 乙醇浓度全局线性系数为正，但与装料质量/Co 负载量混杂，方向不可信
cause: 乙醇浓度在不同装料质量家族内效应相反
signal: 同一装料质量家族内低乙醇反而对应更高选择性
lesson: 混杂因素的方向性结论须结合具体配方解读，不可单凭全局线性系数外推
avoid: 
source: 2021 高教社杯全国大学生数学建模竞赛 B 题（乙醇偶合制备 C4 烯烃） | 2021
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-657（公开经验库·国赛实战）

```yaml
failure_id: FD-657
problem_type: 优化决策
domain: 化学/催化工艺优化（乙醇偶合制 C4 烯烃）
method: 纯 GPR-UCB 取 Top-5 实验
failure: 采样点聚在高温大装量区，与叙述理由脱节
cause: UCB 在最高收率区集中
signal: 5 点高度相似，缺乏多样性与可解释目的
lesson: 序贯实验设计应目的驱动 + GPR 量化支持，而非纯采集函数取优
avoid: 
source: 2021 高教社杯全国大学生数学建模竞赛 B 题（乙醇偶合制备 C4 烯烃） | 2021
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-658（公开经验库·国赛实战）

```yaml
failure_id: FD-658
problem_type: 优化决策
domain: 公共安全/运筹优化/交通网络
method: 
failure: 
cause: 
signal: 凡路网+覆盖类题必用最短路
lesson: 路网弯曲，须用Dijkstra精确最短路作为覆盖判据
avoid: 
source: cumcm2011B题 | 交巡警服务平台的设置与调度 | 2011
confidence: 高
source_quality: 高
memory_type: human_replay
```

---

## FD-659（公开经验库·国赛实战）

```yaml
failure_id: FD-659
problem_type: 优化决策
domain: 公共安全/运筹优化/交通网络
method: 
failure: 
cause: 
signal: DIR未触发时应先查检索层接线
lesson: 需将dataset/public_replay/*.jsonl纳入检索源并修正路径
avoid: 
source: cumcm2011B题 | 交巡警服务平台的设置与调度 | 2011
confidence: 高
source_quality: 高
memory_type: human_replay
```


---

## FD-660（自研·检索系统）

```yaml
failure_id: FD-660
problem_type: 检索系统
method: ranking 的 reuse×freshness 加权排序
failure: 直接同题先例（低复用/略旧）被压出 TOP-12，被无关泛化条目（质检/响应面）占据
cause: reuse_factor(低复用=0.5)×freshness(2020年≈0.53) 乘积惩罚过重，压过了相似度
signal: n_matched=1433 但 TOP-12 全是 noise；relevant_in_pool 需手动补录
lesson: 检索排序必须给同题先例（source 含题名关键词）强 boost，不能让复用率×新鲜度主导；直接相关 > 高频
source: 2020国赛B穿越沙漠测试 | 经验驱动首次验证复盘 | 2026
confidence: 高
```

---

## FD-661（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/运输调度
method: 储能 LP 峰值约束写为 P - gb + gs ≤ 0
failure: LP 约束符号写反，解出现"不卖电反而亏"的反常值(gs=0)
cause: 峰谷约束方向与"可充可放"的物理含义没对上
signal: 解出现不卖电反而亏的反常值(gs=0)
lesson: LP 约束写完后做一次手工可行解对照，挡掉符号写反
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-662（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/多目标
method: QoS 定义为 1 - delay/W（与"越早越好"绑定）
failure: 所有 Pareto 解 QoS≈1.0，多目标失去区分度
cause: QoS 定义方式让"完成即满分"，没有惩罚延迟
signal: 所有 Pareto 解 QoS≈1.0
lesson: 改用"柔性任务完成时延 < ½ 最大容忍时延"的比例指标
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-663（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/调度
method: P4 placement 按逐到达循环（28800 次/调用 × 80 点）
failure: 进程无 stdout 直接退出，疑似超时/内存崩
cause: 逐到达循环嵌套爆炸，O(28800×80) 每调用
signal: 进程无 stdout 直接退出
lesson: 改按任务类型聚合的 O(12) 向量化；输出重定向到日志文件排查
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-664（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: 朴素谐振效率公式 η=k²Q₁Q₂/(1+k²Q₁Q₂)
failure: Q1 数值偏离官方 56.20%（缺一个 Q 项与 1/(k²Q₁Q₂) 交叉项）
cause: 常见简化式忽略 Q₂/Q₁ 比与交叉项
signal: 复算数值对不上官方参考答案
lesson: 必须用含 Q₂/Q₁ 比与 1/(k²Q₁Q₂) 的完整 ABCD 闭式
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-665（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 任意（代码）
method: Python f-string 含字面 % 与 % 运算符混用
failure: 打印语句含"(eta>80%)"又用 % 运算符格式化，抛 ValueError 使整段 Q4 报错
cause: 字面 % 与格式化 % 冲突
signal: 打印行报 ValueError
lesson: 统一改用 f-string，避免字面 % 与 % 运算符混用
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-666（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理（窄领域）
method: 经验库检索（问题指纹）
failure: 窄领域机理题（WPT）检索命中1582条但无专属 SD/FD，top-12 无 WPT 专属条目
cause: 库内无该窄领域经验，泛化条目占满
signal: n_matched 高但 top 全是泛化条目
lesson: 窄领域机理题勿过度依赖经验库，以第一性原理+文献为主，检索仅作方法论弱信号
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 中
```

---

## FD-667（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: R₂ 口径未拆分（附件给的接收装置电阻 RL 当线圈电阻）
failure: 附件2 的 RL=432.24Ω 已含负载，当线圈电阻会数值漂移
cause: 口径混淆（接收装置电阻 vs 线圈电阻）
signal: Q1 数值不稳定
lesson: 按同工艺 R₂=R₁=1.55Ω，R_L=432.24−1.55=430.69Ω；正文/求解/代码三处口径须一致
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-668（外部交付·2019C机场出租车）

```yaml
failure_id: FD-668
problem_type: 优化决策/排队
method: 设单上车点
failure: 乘客等待长、蓄车池溢出，单点成瓶颈
cause: 单车道单上车点吞吐受限
signal: 等待队伍长、吞吐不随需求涨
lesson: 双车道设多上车点（4-6个），吞吐近似 k·μ 线性提升；勿设单点瓶颈
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-669（外部交付·2019C机场出租车）

```yaml
failure_id: FD-669
problem_type: 优化决策/排队
method: 只算蓄车池等待、忽略返城空载成本
failure: 司机决策偏离真实最优
cause: 单边估算只建模等待成本，漏了空载机会成本
signal: 结论与现实中"高峰空返"矛盾
lesson: 双边成本同时建模：等待成本与返城空载/机会成本比较，再决定排队或空返
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-670（外部交付·2019C机场出租车）

```yaml
failure_id: FD-670
problem_type: 优化决策/排队
method: 长短途无差别排队
failure: 短途乘客打车难，短途供给不足
cause: 长短途单位时间收益差大（15 vs 29.5元/h），无差别排队让短途司机不接
signal: 短途车少、乘客等车难
lesson: 设短途绿色通道（≤L0公里优先凭证），平衡长短途收益
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-671（外部交付·2019E薄利多销）

```yaml
failure_id: FD-671
problem_type: 数据/财务分析
method: 忽略成本价缺失，直接用售价当成本
failure: 利润率>100%不合理
cause: 非打折商品成本价缺失时未估计，直接以售价充当成本，缺利润率约束
signal: 大量日期利润率>80%/100%
lesson: 用标价隐含利润率估计缺失成本（成本=原价×(1-θ)），以整体利润率20%-40%区间校准
source: 国赛2019E|薄利多销|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-672（外部交付·低温防护服）

```yaml
method: DSC 数据直接按题面取值
failure: 题面温度区间(14.7-25°C)与附件2(14-26°C)不一致，直接按题面会算错
cause: 题面概述 vs 附件实测数据冲突
signal: 相变温度区间对不上
lesson: 附件数据为准——题面 vs 附件不一致时以附件表头/实测为准，逐项核对单位
source: 华数杯2021A|低温防护服御寒|外部交付(2026-08-14)
confidence: 高
failure_id: FD-672
```

---

## FD-673（外部交付·低温防护服）

```yaml
method: 相变潜热直接乘 mW/mg 造成功率
failure: 潜热功率虚高，温度曲线算不准
cause: DSC 输出是功率密度(mW/mg)，直接乘会造成功率虚高
signal: 升温/降温过快
lesson: 相变潜热用 DSC 曲线积分归一化（面积=潜热），避免直接乘 mW/mg
source: 华数杯2021A|低温防护服御寒|外部交付(2026-08-14)
confidence: 高
failure_id: FD-673
```

---

## FD-674（公开经验库·公开）

```yaml
failure_id: FD-674
problem_type: 优化决策
domain: 算力调度/能源电力协同
method: 对AI训练尖峰序列沿用季节朴素/周同均值预测
failure: 测试RMSE显著偏高
cause: AI训练需求高离散、强尖峰
signal: RegionB训练序列RMSE较GBRT高48.5%
lesson: 尖峰/高离散序列须用非线性集成(GBRT)而非朴素时序
avoid: 
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## FD-675（公开经验库·公开）

```yaml
failure_id: FD-675
problem_type: 优化决策
domain: 算力调度/能源电力协同
method: 上层事件驱动贪心+边际评分
failure: 离散分配路径可能陷入局部最优
cause: 任务处理顺序、紧迫度系数与多目标权重敏感
signal: 无全局最优保证
lesson: 启发式须标注局限性，必要时用精确方法或更多情景交叉验证
avoid: 
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## FD-676（公开经验库·公开）

```yaml
failure_id: FD-676
problem_type: 优化决策
domain: 算力调度/能源电力协同
method: 储能连续LP未显式设置充放电互斥二元变量
failure: 实际运行可能同时充放
cause: 连续LP无0-1互斥约束
signal: 工程复核时发现需增加互斥校验
lesson: 储能模型必须显式充放电互斥或附加工程复核校验
avoid: 
source: 2026华数杯C|算-储-电协同调度|CM2600472
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## FD-677（公开经验库·公开）

```yaml
failure_id: FD-677
problem_type: 优化
domain: VLSI布图
method: 直接HPWL估计线长
failure: 多接口(≥4)组线长偏差大
cause: HPWL对RSMT逼近误差大
signal: 接口数≥4的组贡献45%长度
lesson: 按接口数分类修正
avoid: 一刀切用HPWL
source: 2024华数杯B|VLSI自动布局|CM2401166
confidence: 高
source_quality: 中
memory_type: paper_extract
```

---

## FD-678（公开经验库·公开）

```yaml
failure_id: FD-678
problem_type: 优化
domain: VLSI布图
method: 模拟退火+硬约束
failure: 单元重叠超阈值
cause: 密度是软约束当硬约束卡太死
signal: 大量网格超密度0.9
lesson: 区分软/硬约束
avoid: 惩罚项权重拍脑袋
source: 2024华数杯B|VLSI自动布局|CM2401166
confidence: 高
source_quality: 中
memory_type: paper_extract
```

## FD-543

```yaml
problem_type: 优化
situation: 综合效率,多损失机制,因子分解
method: 把系统总效率按损失机制分解为若干子效率因子，每个因子独立建模后连乘合成
failure: 把系统总效率按损失机制分解为若干子效率因子，每个因子独立建模后连乘合成
lesson: 不同损失的物理机理各异，分别处理可降低单步建模难度并便于定位效率瓶颈
avoid: 其值受到多个因素的影响，包括阴影遮挡效率、余弦效率、大气透射率、集热器截断效率以及镜面反射率等
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-544

```yaml
problem_type: 优化
situation: 三维几何,坐标系转换,投影求交
method: 建立镜场/镜面/入射光线等多个坐标系，用旋转平移矩阵互转，把遮挡与截获化为直线-平面求交与包含判定
failure: 建立镜场/镜面/入射光线等多个坐标系，用旋转平移矩阵互转，把遮挡与截获化为直线-平面求交与包含判定
lesson: 把空间几何问题代数化，可用解析或数值方法稳定求解
avoid: 为了便于计算，我们需要进行多次的坐标变换
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-545

```yaml
problem_type: 优化
situation: 连续锥形反射光线无法解析计算截断效率
method: 径向n1等分+周向n2等分的双层离散，把光锥变成n1×n2条等能量光线样本
failure: 径向n1等分+周向n2等分的双层离散，把光锥变成n1×n2条等能量光线样本
lesson: 将连续能量分布抽样为可枚举射线，命中计数即可估计能量比例，精度由离散数控制
avoid: 通过径向方向离散和圆周方向离散，将锥形太阳反射光离散化为若干条光线，认为每条光线所包含的太阳辐射能相等，均为E。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-546

```yaml
problem_type: 机理
situation: 模型评估阶段需诚实暴露简化代价
method: 主动列出模型缺点并说明其方向性影响(忽略吸收塔阴影使遮挡效率偏大)
failure: 主动列出模型缺点并说明其方向性影响(忽略吸收塔阴影使遮挡效率偏大)
lesson: 指出缺点的同时给出偏差方向，证明作者理解模型局限，比笼统的"有待改进"更有说服力
avoid: 忽略了吸收塔在定日镜表面形成的阴影，求得的阴影遮挡效率偏大。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-679

```yaml
problem_type: 优化
situation: 设计参数（塔位置、镜尺寸、高度、数目、位置）未知需反求
method: 先建效率计算黑箱模型（机理仿真），再以单位面积功率为目标枚举设计变量寻优，算-优两阶段
failure: 先建效率计算黑箱模型（机理仿真），再以单位面积功率为目标枚举设计变量寻优，算-优两阶段
lesson: 机理仿真无法解析求梯度，嵌入枚举循环即可求解，复用问题一模型
avoid: 摘要：建立定日镜场的效率优化模型；5.1：决策变量为吸收塔位置坐标、定日镜尺寸、安装高度、数目与位置
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-680

```yaml
problem_type: 评价
situation: 年度指标连续时间计算代价高，题目给定简化口径
method: 遵守题目简化假设，年均指标只需每月21日9:00至15:00共5个时刻计算
failure: 遵守题目简化假设，年均指标只需每月21日9:00至15:00共5个时刻计算
lesson: 把连续年均问题离散为60个时刻的有限样本，控制计算规模
avoid: 摘要：题中简化计算年均指标只需计算每月21日5个时间点
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-681

```yaml
problem_type: 机理
situation: 需由几何物理关系建立可代入参数直接计算的解析模型
method: 先建坐标系几何化场景，沿“海水深度→覆盖宽度→重叠率”依赖链逐层推导，每步注明所用定理（相似三角形、正弦定理）
failure: 先建坐标系几何化场景，沿“海水深度→覆盖宽度→重叠率”依赖链逐层推导，每步注明所用定理（相似三角形、正弦定理）
lesson: 公式可代入参数直接求值，便于批量计算并支持控制变量法做规律探究
avoid: 以海域中心点为原点建立三维直角坐标系，用相似三角形原理求海水深度，再通过正弦定理将角与边联系起来求覆盖宽度（原文问题一建模）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-682

```yaml
problem_type: 机理
situation: 三维空间需求沿测线任意位置的海水深度与覆盖宽度所在直线的夹角
method: 用两平面法向量叉乘求交线方向向量，由点向式方程求深度；用线面角公式求夹角
failure: 用两平面法向量叉乘求交线方向向量，由点向式方程求深度；用线面角公式求夹角
lesson: 把立体几何推导转为向量代数，降低作图复杂度，公式易推广到任意测线方向
avoid: 由于已知平面I与平面II的法向量，则面I与面II的交线m的方向向量可利用二者叉乘来表示（原文问题二）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-683

```yaml
problem_type: 机理
situation: 斜坡二维几何,求覆盖宽度与重叠率的解析式
method: 用三角函数与正弦定理把几何关系代数化,水深随距离线性变化后代入宽度公式
failure: 用三角函数与正弦定理把几何关系代数化,水深随距离线性变化后代入宽度公式
lesson: 解析式可退化检验且能直接复用于后续问题,是整篇的模型地基
avoid: 针对问题1，运用几何分析和正弦定理，求解海水深度D 关于测线距中心点距离x 的函数关系式，以及条带覆盖宽度W 的函数表达式。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-684

```yaml
problem_type: 机理
situation: 测线方向任意(三维),变量增加
method: 先推线面角关于坡度α与测线方向角β的三角关系,再整体替换二维公式中的坡度参数
failure: 先推线面角关于坡度α与测线方向角β的三角关系,再整体替换二维公式中的坡度参数
lesson: 保持原模型形式只换参数,推广成本低且一致性可检验
avoid: 先分析本题和问题1的联系与区别,决定沿用问题1的大致函数模型,找出变化后的线面角关于α、β的表达式,再代入原函数求解。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-685

```yaml
problem_type: 优化
situation: 几何计算表出现负重叠率
method: 通过结果表反查方案缺陷，把漏测显性化
failure: 通过结果表反查方案缺陷，把漏测显性化
lesson: 负重叠率是模型失效的硬证据，比定性讨论更有说服力
avoid: 可以发现最后两条测线出现了漏测，更详细的数值计算结果将在表格文件result1.xlsx 中展示。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-686

```yaml
problem_type: 优化
situation: 算法初跑鲁棒性差
method: 如实记录失败并给出分区重构的对策
failure: 如实记录失败并给出分区重构的对策
lesson: 承认失败并止损，展示工程化迭代能力而非一次成型
avoid: 经过初步尝试，发现不同起始线最后以固定�探索出来的路径不同，且在某些区域存在漏测和鲁棒性较差等问题，可用性较差
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-687

```yaml
problem_type: 统计
situation: 需判断多个品类/单品连续销量序列之间的关联关系时
method: 先声明变量为连续变量，选用非参数的Spearman相关系数做等级化相关分析，并附显著性检验（P值、置信水平）
failure: 先声明变量为连续变量，选用非参数的Spearman相关系数做等级化相关分析，并附显著性检验（P值、置信水平）
lesson: 非参数方法对分布不做正态假设，等级化处理稳健，检验给出显著性证据而非只报系数
avoid: 由于蔬菜各品类的销售量为连续变量，因此本次建模采用Spearman 相关系数用于分析蔬菜各品类销售量的相关关系。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-688

```yaml
problem_type: 统计
situation: 需判断销量与定价两个变量的线性关系并给出定量表达时
method: 先算Pearson相关系数看符号与显著性，再以销量为自变量、定价为因变量做最小二乘线性回归，分品类给出方程
failure: 先算Pearson相关系数看符号与显著性，再以销量为自变量、定价为因变量做最小二乘线性回归，分品类给出方程
lesson: 系数为负且P值远小于0.05才敢断言负线性相关，回归方程把关系量化为可解释的边际影响
avoid: 花菜类、食用菌、辣椒类、茄类、花叶类和水生根茎类的销售总量与成本加成定价的相关系数都小于0，故各蔬菜品类的销售总量与成本加成定价呈负线性相关关系。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-689

```yaml
problem_type: 统计
situation: 拿到三年逐笔销售明细需建模
method: 先按单品编码透视成日销售数据集，统一时间粒度再分析
failure: 先按单品编码透视成日销售数据集，统一时间粒度再分析
lesson: 逐笔数据噪声大且无法直接建模，日汇总得1084样本规整输入
avoid: 将该数据以单品编码为关键字，通过数据透视形成新的销售数据集，即日销售数据，计1084 个样本。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-690

```yaml
problem_type: 优化
situation: 收益最大化补货定价优化
method: 目标函数按利润=销售总价-成本总价从业务口径推导
failure: 目标函数按利润=销售总价-成本总价从业务口径推导
lesson: 目标与约束有实际含义支撑、参数含义明确，便于解释与答辩
avoid: 商超经营过程中，成本利润率和损耗率有关，通常损耗率越高，成本利润率越低，损耗率越低，成本利润率越高。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-691

```yaml
problem_type: 机理/统计
situation: 分析销量与定价等经济变量关系时直接做相关性分析
method: 先按经济学理论选模型（双对数需求函数）控制其他变量，而不是直接算相关系数
failure: 先按经济学理论选模型（双对数需求函数）控制其他变量，而不是直接算相关系数
lesson: 时间序列受宏观因素共同驱动，简单相关会得到虚假关系
avoid: 直接对销量与定价的关系进行相关性分析难以得出正确的结论。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-692

```yaml
problem_type: 评价
situation: 用销量直接刻画单品需求度
method: 以销量与销售次数双指标做VIKOR综合评价得出需求度，再排序筛除末尾单品
failure: 以销量与销售次数双指标做VIKOR综合评价得出需求度，再排序筛除末尾单品
lesson: 单看销量会忽略少量多次的购买模式，评价失真
avoid: 单纯从购买销量角度衡量顾客对单品的需求度可能会忽视单笔销量质量较小，但是订单购买次数较多的单品。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-693

```yaml
problem_type: 统计
situation: 不同品类/单品销量绝对值差异大，难以直接横向比较时
method: 将销量按时间维度比例化（月/周/年销量除以总销量）后再比较分布规律
failure: 将销量按时间维度比例化（月/周/年销量除以总销量）后再比较分布规律
lesson: 绝对值量纲不同会掩盖分布形状的异同，占比标准化后可跨品类跨单品比较
avoid: 由于不同的品类及不同的单品之间存在着较大的销量绝对值差异，因此按照一定时间范围内的销量比例来计算，比如计算月销量规律时，将每个品类或单品的每个月销量除以总销量，
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-694

```yaml
problem_type: 统计
situation: 单品缺失记录过多、无共同时间点可比时
method: 相关性分析前剔除总销量后25%的单品，剩余单品缺失日期用0填充
failure: 相关性分析前剔除总销量后25%的单品，剩余单品缺失日期用0填充
lesson: 缺失过多导致无法找到共同时间点对比，且会偏高或偏低扭曲相关系数，剔除后分析更干净
avoid: 针对三年来总销量很少的单品，在计算单品间相关系数的环节，删去了总销量后25%的单品，一方面因为缺失值过多的单品之间往往无法找到相同的时间点进行销量对比，另一方面
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-695

```yaml
problem_type: 优化
situation: 问题重述含'给出生产计划使某指标最大/最小'与容量约束
method: 看到'产量最大/损失最小+容量限制'即锁定优化题, 再细分排产与随机化
failure: 看到'产量最大/损失最小+容量限制'即锁定优化题, 再细分排产与随机化
lesson: 目标函数与约束的措辞直接决定主标签, 无需等建模再定
avoid: 2、在问题1 的基础上，给出112 个标准羊栏的具体生产计划，使得年化出栏羊只数量最大。
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-696

```yaml
problem_type: 优化
situation: 决策对象是'何时配种、配多少母羊'的时序安排
method: 把生产安排抽象为(批次间隔g, 每批数量x)二元决策
failure: 把生产安排抽象为(批次间隔g, 每批数量x)二元决策
lesson: 从题目核心自由度提炼决策变量, 为整个建模定骨架
avoid: 为了简化问题的复杂度, 我们考虑较为规律的生产模式, 即每隔固定的天数让固定数量的母羊进行交配.
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-697

```yaml
problem_type: 预测
situation: 描述时序数据特征,需量化支撑
method: 用时段划分+均值±标准差量化描述趋势特征
failure: 用时段划分+均值±标准差量化描述趋势特征
lesson: “含沙量较低/较高”配具体数值区间与统计量，描述可验证、显专业
avoid: (1) 10 月15 日至来年6 月30 日含沙量较低，一般不超过4kg/m3，均值为2.23 kg/m3，标准差为0.96 kg/m3；
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-698

```yaml
problem_type: 预测
situation: 预测结果展示,需先证模型可信
method: 内预测拟合验证模型后再做外预测，并报告贴合度
failure: 内预测拟合验证模型后再做外预测，并报告贴合度
lesson: 先用训练期内预测与实测贴合度（90%）证明模型可靠，外预测结论才有说服力
avoid: 基于SARIMA模型对水沙通量数据进行预测，并将实际数据与预测数据进行拟合。得到图18，此时贴合度为90%。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-699

```yaml
problem_type: 预测
situation: 原始数据日期不连续、存在大量缺失、跨闰年
method: 先补全日期序列，缺失用邻近值替代，统一一年365天，再按日/月/年整理成时间序列
failure: 先补全日期序列，缺失用邻近值替代，统一一年365天，再按日/月/年整理成时间序列
lesson: 等间隔时间序列是周期、突变、频谱分析有效的前提，预处理规范直接决定后续分析可靠性
avoid: 首先,检查日期是否连续,如果不连续,就补充完整。其次,由于数据存在缺失,就用邻近值代替。第三,为了排除闰年的影响,一年定为365 天。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-700

```yaml
problem_type: 预测
situation: 需系统刻画时间序列变化规律
method: 按统计特征、季节性、周期性、突变性四个维度递进分析，各维度配专门方法
failure: 按统计特征、季节性、周期性、突变性四个维度递进分析，各维度配专门方法
lesson: 四维框架覆盖全面，方法各司其职（统计描述/月份指数/三角函数/非参检验），结构清晰不易漏项
avoid: 研究它们的变化规律，需要从统计特征、季节性、周期性和突变性四个方面来入手。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-701

```yaml
problem_type: 统计
situation: 原始坐标点直接求导数波动剧烈,无法直接判别图元类型
method: 对离散点先按窗口分块求平均一阶/二阶导数,并设置阈值将图形模式编码为类别变量(1水平线/2斜线/3圆)
failure: 对离散点先按窗口分块求平均一阶/二阶导数,并设置阈值将图形模式编码为类别变量(1水平线/2斜线/3圆)
lesson: 把连续导数转成带阈值的离散判别量,既抗噪声又可直接用于定位各图元区间
avoid: 选择阈值和分别表示一阶导数阈值和二阶导数值，并即滑窗内区域的图形模式为Y，平行直线、斜线、圆分别使用1、2、3表示。
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-702

```yaml
problem_type: 统计
situation: 工件整体倾斜导致测量坐标带旋转偏差
method: 用多条斜率相近直线的斜率平均估计倾斜角,再用旋转矩阵校正,以圆心等特征点验证平移量
failure: 用多条斜率相近直线的斜率平均估计倾斜角,再用旋转矩阵校正,以圆心等特征点验证平移量
lesson: 多数同向直线斜率取平均可抵消单条直线拟合误差,旋转矩阵校正使各问数据统一到水平坐标系
avoid: 通过几个特别的点，比如圆心验证。
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-703

```yaml
problem_type: 机理拟合
situation: 自定义区间分段拟合
method: 人工按散点图选择拟合区间导致断点不精确、精度受限
failure: 人工按散点图选择拟合区间导致断点不精确、精度受限
lesson: 区间选取依赖肉眼,同一数据不同人结果不同,评审会质疑稳定性
avoid: 在函数的拟合刻画时，我们截取的数据为自定义的区间范围内的散点拟合，导致函数的精确度还可以提高。
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-704

```yaml
problem_type: 机理拟合
situation: 简化假设与物理真实不符
method: 把实际为椭圆的倾斜截面强制按标准圆拟合,产生系统偏差
failure: 把实际为椭圆的倾斜截面强制按标准圆拟合,产生系统偏差
lesson: 简化假设与真实几何不符时参数出现微小但可解释的偏差
avoid: 在模型的建立中，我们为了简化模型将图中所有轮廓只看成直线与圆的组合，导致了红色轮廓计算的工件1参数与蓝色轮廓计算的工件1参数存在微小差异
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-705

```yaml
problem_type: 统计
situation: 题目给出大量实测点列, 要求自动标注槽口宽/半径/圆心距/夹角等几何参数
method: 实测离散数据加几何要素自动标注即锁定统计/数据处理题
failure: 实测离散数据加几何要素自动标注即锁定统计/数据处理题
lesson: 从数据形态与输出类型判断主标签, 无需等建模再定
avoid: 假设被测工件的轮廓线是由直线和圆弧构成的平面曲线，建立数学模型，根据附件所提供的轮廓仪测量数据
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-706

```yaml
problem_type: 统计
situation: 轮廓由直线与圆弧构成, 需先自动区分图形基元
method: 一阶导数判水平/斜线, 二阶导数判直线/圆, 两者联合成判据
failure: 一阶导数判水平/斜线, 二阶导数判直线/圆, 两者联合成判据
lesson: 导数零与非零是基元的解析本质特征, 可直接编程判别
avoid: 注意到直线的二阶导数为零，而圆的二阶导数不为零，用二阶导数区分圆和直线，而斜线和水平线可以用一阶导数来区分。
source: 2020国赛D|基于接触式轮廓仪测量数据的工件形状自动标注方法|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-707

```yaml
problem_type: 统计
situation: 题目给出大量离散测量点列, 要求标注槽口宽/半径/弧长/夹角等几何参数
method: 实测离散点列加几何要素标注即锁定数据处理/统计题, 主线是曲线拟合与参数计算
failure: 实测离散点列加几何要素标注即锁定数据处理/统计题, 主线是曲线拟合与参数计算
lesson: 从数据形态与输出类型即可判断主标签与建模主线, 无需等建模再定
avoid: 假设被测量的工件的轮廓都是由圆弧和直线所组成的。请建立数学模型
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-708

```yaml
problem_type: 统计
situation: 轮廓由24段直线圆弧构成, 需逐段拟合
method: 按几何形态分类选拟合形式: 水平线取y均值, 斜线一元线性回归, 圆弧圆一般方程
failure: 按几何形态分类选拟合形式: 水平线取y均值, 斜线一元线性回归, 圆弧圆一般方程
lesson: 每段形态简单, 分类后各用最简参数形式, 参数由方程系数直接给出
avoid: 将直线的计算分为两种，倾斜角为0，和倾斜角非0。
source: 2020国赛D|接触式轮廓仪校准问题|2020D
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-709

```yaml
problem_type: 优化
situation: 切割方案有主次优先级目标
method: 拆成两阶段模型：第一阶段切割损失最小整数规划，第二阶段固定最优损失下最小化平均绝对偏差
failure: 拆成两阶段模型：第一阶段切割损失最小整数规划，第二阶段固定最优损失下最小化平均绝对偏差
lesson: 题目要求先保证损失最小再满足用户目标值，分层比加权单目标更能守住优先级
avoid: 将整线性规划模型所求的切割损失最小值固定，构造平均绝对偏差来刻画满足用户目标值，在切割损失最小的前提下，建立了最小平均绝对偏差模型
source: 2021国赛D|连铸切割的在线优化模型|D017
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-710

```yaml
problem_type: 优化
situation: 结晶器异常产生0.8米报废段
method: 按“尾坏+废坏”连接类型（三种类型）分类设计实时切割算法
failure: 按“尾坏+废坏”连接类型（三种类型）分类设计实时切割算法
lesson: 不同连接类型的可切组合不同，分类讨论保证每种异常情形都有最优调整方案
avoid: 本文将分三种情况讨论尾坏与废坏的连接类型，并给出相应的切割算法。
source: 2021国赛D|连铸切割的在线优化模型|D017
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-711

```yaml
problem_type: 优化
situation: 12个尾坏长度,批量求解,结果列表
method: 将12个尾坏长度逐一代入模型求解并列表给出切割方案与切割损失
failure: 将12个尾坏长度逐一代入模型求解并列表给出切割方案与切割损失
lesson: 数据驱动的结果呈现，评阅人可直接核对每组数据
avoid: 最后求得这12种长度的尾坏的最优切割方案和切割损失情况如表1所示。
source: 2021国赛D|连铸切割的在线优化|D026
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-712

```yaml
problem_type: 优化
situation: 异常时刻,时间窗口,时间单元
method: 以9个异常时刻定义9个窗口、8个时间单元，作为实时方案的时间划分
failure: 以9个异常时刻定义9个窗口、8个时间单元，作为实时方案的时间划分
lesson: 统一时段口径，便于方案叠加与调整判断
avoid: 定义：以每个异常时刻为时间窗口，则有9个窗口；以相邻两个异常时刻为时间单元，则有8个时间单元。
source: 2021国赛D|连铸切割的在线优化|D026
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-713

```yaml
problem_type: 单段切割优化
situation: 给定尾坏长度与用户目标值和范围，求最小损失切割方案
method: 先按目标值切分求段数与基础损失g，再用目标范围差构造总浮动量E，得损失区间[Imin,Imax]，按Imin符号分情形枚举最优组合
failure: 先按目标值切分求段数与基础损失g，再用目标范围差构造总浮动量E，得损失区间[Imin,Imax]，按Imin符号分情形枚举最优组合
lesson: 把连续区间约束化为可枚举的浮动量，无需搜索即可构造最优方案
avoid: 全部切割为N=9.5的切割方案的切割损失为g=S-F*N=109-11*9.5=4.5米...以上切割方案的切割损失的最小值设为Imin=g-E=4.5-5.5=-1米
source: 2021国赛D|连铸切割的在线优化|2021_D_D034
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-714

```yaml
problem_type: 机理
situation: 物理过程清楚、需建立动力学方程
method: 受力分析枚举全部力/力矩后由牛顿第二定律列二阶常微分方程组
failure: 受力分析枚举全部力/力矩后由牛顿第二定律列二阶常微分方程组
lesson: 从基本物理定律出发，方程结构可解释、参数有物理含义
avoid: 则由牛顿第二定律可得浮子和振子的垂荡运动模型为：(mf+m)r,(t)=fe+fe+fr-pro；mzw,(t)=fPTO
source: 2022国赛A|波浪能装置输出功率优化设计|A001
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-715

```yaml
problem_type: 机理
situation: 二阶多元微分方程需要数值求解
method: 降阶转化为一阶多元方程组后四阶龙格库塔递推
failure: 降阶转化为一阶多元方程组后四阶龙格库塔递推
lesson: 龙格库塔处理一阶初值问题，降阶使算法可实施且精度O(h5)
avoid: 由于本问题求解的方程为二阶二元微分方程，故需要将方程转化为一阶多元方程，同时一阶导数项移到等式左侧，余项移到等式右侧，再使用龙格库塔算法求解。
source: 2022国赛A|波浪能装置输出功率优化设计|A001
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-716

```yaml
problem_type: 机理
situation: 需量化PTO系统输出功率以作优化目标
method: 把输出功率定义为阻尼系数乘以浮子振子相对速度(角速度)平方,对稳态段采样做trapz梯形积分取平均
failure: 把输出功率定义为阻尼系数乘以浮子振子相对速度(角速度)平方,对稳态段采样做trapz梯形积分取平均
lesson: 功率只与阻尼系数和相对运动有关,积分平均给出可计算的标量目标函数
avoid: 由于阻尼做功只与阻尼系数以及浮子和振子间的相对运动有关，取PTO为装置的能量转化功率
source: 2022国赛A|波浪能装置输出功率最大化模型|A022
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-717

```yaml
problem_type: 机理
situation: 求线性阻尼恒定时的最优阻尼解析解
method: 利用稳态频率等于激励频率,把二阶微分方程组改写为频域复数代数方程,对响应模长求导得最优阻尼公式
failure: 利用稳态频率等于激励频率,把二阶微分方程组改写为频域复数代数方程,对响应模长求导得最优阻尼公式
lesson: 频域化把微分方程变成代数方程,解析求导即得最优参数,并可与数值解互验
avoid: 利用稳态时浮子和振子的运动频率同海浪相等，可将其改写为复数代数方程，对此式求导可知n_best时有最大功率
source: 2022国赛A|波浪能装置输出功率最大化模型|A022
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-718

```yaml
problem_type: 机理
situation: 方案适用前提严苛
method: 调整方案假定条件严苛,适用范围被局限
failure: 调整方案假定条件严苛,适用范围被局限
lesson: 依赖至少三架同圆基准等假设,不满足时方案失效
avoid: 调整方案模型适用的假定前提存在一定的严苛性，使得调整的适用范围被局限。
source: 2022国赛B|无人机遂行编队飞行中的纯方位无源定位|B030
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-719

```yaml
problem_type: 机理
situation: 利用对称性归并类别
method: 为方便遍历在程序上忽略对称类别③,若对称性判断失误会漏解
failure: 为方便遍历在程序上忽略对称类别③,若对称性判断失误会漏解
lesson: 归并依赖旋转等价成立,一旦形态不对称则覆盖不全
avoid: 且在程序上为方便遍历，也忽略了类别③。
source: 2022国赛B|无人机遂行编队飞行中的纯方位无源定位|B030
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-720

```yaml
problem_type: 机理
situation: 纯方位角度定位问题
method: 优先挖掘几何性质，用“等角对等边”把定位转化为两圆轨迹求交点
failure: 优先挖掘几何性质，用“等角对等边”把定位转化为两圆轨迹求交点
lesson: 正弦定理法需按四个区域分类讨论，几何法统一且可利用对称性避开联立方程
avoid: 由于第一个方法在计算上涉及多个分类讨论的过程，我们选择了图中的几何性质，即等角对等边这个模型来求解待测无人机的坐标
source: 2022国赛B|基于计算几何与带阈值启发式搜索的无人机无源定位模型|B035
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-721

```yaml
problem_type: 机理
situation: 锥形编队出现三点共线、四点共圆
method: 预设信号发射顺序（同随机种子生成相同随机序列），四点共圆时判定无法定位不调整
failure: 预设信号发射顺序（同随机种子生成相同随机序列），四点共圆时判定无法定位不调整
lesson: 通过发射次序反推编号，规避共圆造成的定位精度退化
avoid: 我们可以预先设定无人机发射信号的顺序……无人机都可以通过接收信号的次数判断当前发射信号的无人机编号，并基于此利用与问题一相同的作圆求交方法实现定位
source: 2022国赛B|基于计算几何与带阈值启发式搜索的无人机无源定位模型|B035
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-722

```yaml
problem_type: 机理定位
situation: 圆形编队,信号源排布,对称性,分情况讨论
method: 两架圆周信号源与圆心信号源共四种排布，需分情况逐一讨论
failure: 两架圆周信号源与圆心信号源共四种排布，需分情况逐一讨论
lesson: 覆盖全部几何位置，避免漏解
avoid: 由于圆的高度对称性，主动机的排布共分四种
source: 2022国赛B|基于局部最优模型的无人机位置调整策略与仿真定位|B086
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-723

```yaml
problem_type: 机理定位
situation: 误差假设,信号源数目,有效定位
method: 在方向角误差±5°假设下，仅需再一架信号源即可有效定位
failure: 在方向角误差±5°假设下，仅需再一架信号源即可有效定位
lesson: 给出问题二的关键数量结论
avoid: 在假设3.4误差土5°内，除FY00和FY01外，只需要一架无人机发射信号，就可以实现无人机的有效定位。
source: 2022国赛B|基于局部最优模型的无人机位置调整策略与仿真定位|B086
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-724

```yaml
problem_type: 分类变量相关性+描述统计+风化前预测
situation: 需分析风化与颜色/类型/纹饰关系，描述分组统计规律，预测风化前成分
method: 分类变量用Pearson卡方检验（期望计数小者用Yates校正），连续变量用均值/标准差/变异系数/偏度/峰度与箱线图，预测先Q型聚类建时序再对CLR数据回归并平移反推
failure: 分类变量用Pearson卡方检验（期望计数小者用Yates校正），连续变量用均值/标准差/变异系数/偏度/峰度与箱线图，预测先Q型聚类建时序再对CLR数据回归并平移反推
lesson: 按变量类型与问题目标匹配方法，避免方法误用
avoid: 本文对超过20%的比例期望计教小于5的组别建立Pearson卡方检验法：并对不满足卡方检验前提的组别建立Yates校正卡方检验法
source: 2022国赛C|基于成分数据的古代玻璃制品的成分分析与鉴别|2022_C_C155
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-725

```yaml
problem_type: 图论调度
situation: 广播/共享类问题需最小化轮次
method: 先计数信息总量与单轮容量得下界，再构造方案证明可达
failure: 先计数信息总量与单轮容量得下界，再构造方案证明可达
lesson: 计数下界+构造性证明是离散调度问题的标准闭环
avoid: 针对上述不等式，给出N个主站间的传输方案模型，来证明K可以取到(N-2)/1.5+1
source: 2022国赛D|气象报文信息卫星通信传输|D999
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-726

```yaml
problem_type: 图论调度
situation: 需要给出具体可执行的传输方案
method: 按对称性原则从相邻站点递推构造传输序列
failure: 按对称性原则从相邻站点递推构造传输序列
lesson: 对称构造保持各站信息状态一致，便于递推与验证
avoid: 本着对称性原则，第一次发送信息结束后各站点均掌握2条信息
source: 2022国赛D|气象报文信息卫星通信传输|D999
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-727

```yaml
problem_type: 统计
situation: 22453条原始需求记录需聚焦重点物料
method: 对物料编码去重并用COUNTIF/SUMIF统计频数与数量,计算平均销售单价与销售总额,结合趋势特征综合筛选
failure: 对物料编码去重并用COUNTIF/SUMIF统计频数与数量,计算平均销售单价与销售总额,结合趋势特征综合筛选
lesson: 多指标(客户规模/需求总量/盈利/趋势)联合排序,筛选依据可量化可复现
avoid: 对物料编码去重复，得到共284个不同的物料编码，再用COUNTIF函数分类计数得到不同物料编码的频数，用SUMIF函数分类求和得到不同物料编码的数量
source: 2022国赛E|基于时间序列预测的物料生产安排模型|E014
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-728

```yaml
problem_type: 预测
situation: 需逐周预测需求并保证预测值物理合理
method: 以周为单位聚合需求量构成时间序列,用前t周数据滚动预测t+1周,预测值为负时截断为0
failure: 以周为单位聚合需求量构成时间序列,用前t周数据滚动预测t+1周,预测值为负时截断为0
lesson: 滚动预测匹配"每周运行一次"的实际场景,负值截断保证生产计划非负
avoid: 利用y.ya.-yo预测yio...再利用yi.y2yo预测y2.以此类推...如果遇到周需求量预测值y<0，校准取3，=0
source: 2022国赛E|基于时间序列预测的物料生产安排模型|E014
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-729

```yaml
problem_type: 优化
situation: 综合效率,多损失机制,因子分解
method: 把系统总效率按损失机制分解为若干子效率因子，每个因子独立建模后连乘合成
failure: 把系统总效率按损失机制分解为若干子效率因子，每个因子独立建模后连乘合成
lesson: 不同损失的物理机理各异，分别处理可降低单步建模难度并便于定位效率瓶颈
avoid: 其值受到多个因素的影响，包括阴影遮挡效率、余弦效率、大气透射率、集热器截断效率以及镜面反射率等
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-730

```yaml
problem_type: 优化
situation: 三维几何,坐标系转换,投影求交
method: 建立镜场/镜面/入射光线等多个坐标系，用旋转平移矩阵互转，把遮挡与截获化为直线-平面求交与包含判定
failure: 建立镜场/镜面/入射光线等多个坐标系，用旋转平移矩阵互转，把遮挡与截获化为直线-平面求交与包含判定
lesson: 把空间几何问题代数化，可用解析或数值方法稳定求解
avoid: 为了便于计算，我们需要进行多次的坐标变换
source: 2023国赛A|定日镜场优化设计|A092
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-731

```yaml
problem_type: 优化
situation: 连续锥形反射光线无法解析计算截断效率
method: 径向n1等分+周向n2等分的双层离散，把光锥变成n1×n2条等能量光线样本
failure: 径向n1等分+周向n2等分的双层离散，把光锥变成n1×n2条等能量光线样本
lesson: 将连续能量分布抽样为可枚举射线，命中计数即可估计能量比例，精度由离散数控制
avoid: 通过径向方向离散和圆周方向离散，将锥形太阳反射光离散化为若干条光线，认为每条光线所包含的太阳辐射能相等，均为E。
source: 2023国赛A|定日镜场的输出功率优化|A127
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-732

```yaml
problem_type: 机理
situation: 模型评估阶段需诚实暴露简化代价
method: 主动列出模型缺点并说明其方向性影响(忽略吸收塔阴影使遮挡效率偏大)
failure: 主动列出模型缺点并说明其方向性影响(忽略吸收塔阴影使遮挡效率偏大)
lesson: 指出缺点的同时给出偏差方向，证明作者理解模型局限，比笼统的"有待改进"更有说服力
avoid: 忽略了吸收塔在定日镜表面形成的阴影，求得的阴影遮挡效率偏大。
source: 2023国赛A|基于机理分析法的定日镜场优化设计模型|A165
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-733

```yaml
problem_type: 优化
situation: 设计参数（塔位置、镜尺寸、高度、数目、位置）未知需反求
method: 先建效率计算黑箱模型（机理仿真），再以单位面积功率为目标枚举设计变量寻优，算-优两阶段
failure: 先建效率计算黑箱模型（机理仿真），再以单位面积功率为目标枚举设计变量寻优，算-优两阶段
lesson: 机理仿真无法解析求梯度，嵌入枚举循环即可求解，复用问题一模型
avoid: 摘要：建立定日镜场的效率优化模型；5.1：决策变量为吸收塔位置坐标、定日镜尺寸、安装高度、数目与位置
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-734

```yaml
problem_type: 评价
situation: 年度指标连续时间计算代价高，题目给定简化口径
method: 遵守题目简化假设，年均指标只需每月21日9:00至15:00共5个时刻计算
failure: 遵守题目简化假设，年均指标只需每月21日9:00至15:00共5个时刻计算
lesson: 把连续年均问题离散为60个时刻的有限样本，控制计算规模
avoid: 摘要：题中简化计算年均指标只需计算每月21日5个时间点
source: 2023国赛A|定日镜场的优化设计模型|A175
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-735

```yaml
problem_type: 机理
situation: 需由几何物理关系建立可代入参数直接计算的解析模型
method: 先建坐标系几何化场景，沿“海水深度→覆盖宽度→重叠率”依赖链逐层推导，每步注明所用定理（相似三角形、正弦定理）
failure: 先建坐标系几何化场景，沿“海水深度→覆盖宽度→重叠率”依赖链逐层推导，每步注明所用定理（相似三角形、正弦定理）
lesson: 公式可代入参数直接求值，便于批量计算并支持控制变量法做规律探究
avoid: 以海域中心点为原点建立三维直角坐标系，用相似三角形原理求海水深度，再通过正弦定理将角与边联系起来求覆盖宽度（原文问题一建模）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-736

```yaml
problem_type: 机理
situation: 三维空间需求沿测线任意位置的海水深度与覆盖宽度所在直线的夹角
method: 用两平面法向量叉乘求交线方向向量，由点向式方程求深度；用线面角公式求夹角
failure: 用两平面法向量叉乘求交线方向向量，由点向式方程求深度；用线面角公式求夹角
lesson: 把立体几何推导转为向量代数，降低作图复杂度，公式易推广到任意测线方向
avoid: 由于已知平面I与平面II的法向量，则面I与面II的交线m的方向向量可利用二者叉乘来表示（原文问题二）
source: 2023国赛B|多波束测线布设|B226
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-737

```yaml
problem_type: 机理
situation: 斜坡二维几何,求覆盖宽度与重叠率的解析式
method: 用三角函数与正弦定理把几何关系代数化,水深随距离线性变化后代入宽度公式
failure: 用三角函数与正弦定理把几何关系代数化,水深随距离线性变化后代入宽度公式
lesson: 解析式可退化检验且能直接复用于后续问题,是整篇的模型地基
avoid: 针对问题1，运用几何分析和正弦定理，求解海水深度D 关于测线距中心点距离x 的函数关系式，以及条带覆盖宽度W 的函数表达式。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-738

```yaml
problem_type: 机理
situation: 测线方向任意(三维),变量增加
method: 先推线面角关于坡度α与测线方向角β的三角关系,再整体替换二维公式中的坡度参数
failure: 先推线面角关于坡度α与测线方向角β的三角关系,再整体替换二维公式中的坡度参数
lesson: 保持原模型形式只换参数,推广成本低且一致性可检验
avoid: 先分析本题和问题1的联系与区别,决定沿用问题1的大致函数模型,找出变化后的线面角关于α、β的表达式,再代入原函数求解。
source: 2023国赛B|基于主要目标法的测线设计问题|B311
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-739

```yaml
problem_type: 优化
situation: 几何计算表出现负重叠率
method: 通过结果表反查方案缺陷，把漏测显性化
failure: 通过结果表反查方案缺陷，把漏测显性化
lesson: 负重叠率是模型失效的硬证据，比定性讨论更有说服力
avoid: 可以发现最后两条测线出现了漏测，更详细的数值计算结果将在表格文件result1.xlsx 中展示。
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-740

```yaml
problem_type: 优化
situation: 算法初跑鲁棒性差
method: 如实记录失败并给出分区重构的对策
failure: 如实记录失败并给出分区重构的对策
lesson: 承认失败并止损，展示工程化迭代能力而非一次成型
avoid: 经过初步尝试，发现不同起始线最后以固定�探索出来的路径不同，且在某些区域存在漏测和鲁棒性较差等问题，可用性较差
source: 2023国赛B|多波束测深合理探测方案的设计及效果分析|B477
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-741

```yaml
problem_type: 统计
situation: 需判断多个品类/单品连续销量序列之间的关联关系时
method: 先声明变量为连续变量，选用非参数的Spearman相关系数做等级化相关分析，并附显著性检验（P值、置信水平）
failure: 先声明变量为连续变量，选用非参数的Spearman相关系数做等级化相关分析，并附显著性检验（P值、置信水平）
lesson: 非参数方法对分布不做正态假设，等级化处理稳健，检验给出显著性证据而非只报系数
avoid: 由于蔬菜各品类的销售量为连续变量，因此本次建模采用Spearman 相关系数用于分析蔬菜各品类销售量的相关关系。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-742

```yaml
problem_type: 统计
situation: 需判断销量与定价两个变量的线性关系并给出定量表达时
method: 先算Pearson相关系数看符号与显著性，再以销量为自变量、定价为因变量做最小二乘线性回归，分品类给出方程
failure: 先算Pearson相关系数看符号与显著性，再以销量为自变量、定价为因变量做最小二乘线性回归，分品类给出方程
lesson: 系数为负且P值远小于0.05才敢断言负线性相关，回归方程把关系量化为可解释的边际影响
avoid: 花菜类、食用菌、辣椒类、茄类、花叶类和水生根茎类的销售总量与成本加成定价的相关系数都小于0，故各蔬菜品类的销售总量与成本加成定价呈负线性相关关系。
source: 2023国赛C|蔬菜类商品动态定价与补货决策研究|C050
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-743

```yaml
problem_type: 统计
situation: 拿到三年逐笔销售明细需建模
method: 先按单品编码透视成日销售数据集，统一时间粒度再分析
failure: 先按单品编码透视成日销售数据集，统一时间粒度再分析
lesson: 逐笔数据噪声大且无法直接建模，日汇总得1084样本规整输入
avoid: 将该数据以单品编码为关键字，通过数据透视形成新的销售数据集，即日销售数据，计1084 个样本。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-744

```yaml
problem_type: 优化
situation: 收益最大化补货定价优化
method: 目标函数按利润=销售总价-成本总价从业务口径推导
failure: 目标函数按利润=销售总价-成本总价从业务口径推导
lesson: 目标与约束有实际含义支撑、参数含义明确，便于解释与答辩
avoid: 商超经营过程中，成本利润率和损耗率有关，通常损耗率越高，成本利润率越低，损耗率越低，成本利润率越高。
source: 2023国赛C|商超蔬菜销售数据的统计分析及建模|C126
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-745

```yaml
problem_type: 机理/统计
situation: 分析销量与定价等经济变量关系时直接做相关性分析
method: 先按经济学理论选模型（双对数需求函数）控制其他变量，而不是直接算相关系数
failure: 先按经济学理论选模型（双对数需求函数）控制其他变量，而不是直接算相关系数
lesson: 时间序列受宏观因素共同驱动，简单相关会得到虚假关系
avoid: 直接对销量与定价的关系进行相关性分析难以得出正确的结论。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-746

```yaml
problem_type: 评价
situation: 用销量直接刻画单品需求度
method: 以销量与销售次数双指标做VIKOR综合评价得出需求度，再排序筛除末尾单品
failure: 以销量与销售次数双指标做VIKOR综合评价得出需求度，再排序筛除末尾单品
lesson: 单看销量会忽略少量多次的购买模式，评价失真
avoid: 单纯从购买销量角度衡量顾客对单品的需求度可能会忽视单笔销量质量较小，但是订单购买次数较多的单品。
source: 2023国赛C|基于价格弹性的蔬菜类商品自动定价与补货决策|C228
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-747

```yaml
problem_type: 统计
situation: 不同品类/单品销量绝对值差异大，难以直接横向比较时
method: 将销量按时间维度比例化（月/周/年销量除以总销量）后再比较分布规律
failure: 将销量按时间维度比例化（月/周/年销量除以总销量）后再比较分布规律
lesson: 绝对值量纲不同会掩盖分布形状的异同，占比标准化后可跨品类跨单品比较
avoid: 由于不同的品类及不同的单品之间存在着较大的销量绝对值差异，因此按照一定时间范围内的销量比例来计算，比如计算月销量规律时，将每个品类或单品的每个月销量除以总销量，以得到月销量比例其他时间维度同理，方便不同品类或单品之间的比较。
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-748

```yaml
problem_type: 统计
situation: 单品缺失记录过多、无共同时间点可比时
method: 相关性分析前剔除总销量后25%的单品，剩余单品缺失日期用0填充
failure: 相关性分析前剔除总销量后25%的单品，剩余单品缺失日期用0填充
lesson: 缺失过多导致无法找到共同时间点对比，且会偏高或偏低扭曲相关系数，剔除后分析更干净
avoid: 针对三年来总销量很少的单品，在计算单品间相关系数的环节，删去了总销量后25%的单品，一方面因为缺失值过多的单品之间往往无法找到相同的时间点进行销量对比，另一方面缺失值过多也会对于相关系数的计算产生偏高或者偏低的影响。
source: 2023国赛C|基于历史数据的蔬菜类商品定价与补货决策模型|C235
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-749

```yaml
problem_type: 优化
situation: 问题重述含'给出生产计划使某指标最大/最小'与容量约束
method: 看到'产量最大/损失最小+容量限制'即锁定优化题, 再细分排产与随机化
failure: 看到'产量最大/损失最小+容量限制'即锁定优化题, 再细分排产与随机化
lesson: 目标函数与约束的措辞直接决定主标签, 无需等建模再定
avoid: 2、在问题1 的基础上，给出112 个标准羊栏的具体生产计划，使得年化出栏羊只数量最大。
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-750

```yaml
problem_type: 优化
situation: 决策对象是'何时配种、配多少母羊'的时序安排
method: 把生产安排抽象为(批次间隔g, 每批数量x)二元决策
failure: 把生产安排抽象为(批次间隔g, 每批数量x)二元决策
lesson: 从题目核心自由度提炼决策变量, 为整个建模定骨架
avoid: 为了简化问题的复杂度, 我们考虑较为规律的生产模式, 即每隔固定的天数让固定数量的母羊进行交配.
source: 2023国赛D|圈养湖羊空间利用率的优化问题|D039
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-751

```yaml
problem_type: 预测
situation: 描述时序数据特征,需量化支撑
method: 用时段划分+均值±标准差量化描述趋势特征
failure: 用时段划分+均值±标准差量化描述趋势特征
lesson: “含沙量较低/较高”配具体数值区间与统计量，描述可验证、显专业
avoid: (1) 10 月15 日至来年6 月30 日含沙量较低，一般不超过4kg/m3，均值为2.23 kg/m3，标准差为0.96 kg/m3；
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-752

```yaml
problem_type: 预测
situation: 预测结果展示,需先证模型可信
method: 内预测拟合验证模型后再做外预测，并报告贴合度
failure: 内预测拟合验证模型后再做外预测，并报告贴合度
lesson: 先用训练期内预测与实测贴合度（90%）证明模型可靠，外预测结论才有说服力
avoid: 基于SARIMA模型对水沙通量数据进行预测，并将实际数据与预测数据进行拟合。得到图18，此时贴合度为90%。
source: 2023国赛E|基于时间序列分析预测的黄河水沙监测模型|E032
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-753

```yaml
problem_type: 预测
situation: 原始数据日期不连续、存在大量缺失、跨闰年
method: 先补全日期序列，缺失用邻近值替代，统一一年365天，再按日/月/年整理成时间序列
failure: 先补全日期序列，缺失用邻近值替代，统一一年365天，再按日/月/年整理成时间序列
lesson: 等间隔时间序列是周期、突变、频谱分析有效的前提，预处理规范直接决定后续分析可靠性
avoid: 首先,检查日期是否连续,如果不连续,就补充完整。其次,由于数据存在缺失,就用邻近值代替。第三,为了排除闰年的影响,一年定为365 天。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-754

```yaml
problem_type: 预测
situation: 需系统刻画时间序列变化规律
method: 按统计特征、季节性、周期性、突变性四个维度递进分析，各维度配专门方法
failure: 按统计特征、季节性、周期性、突变性四个维度递进分析，各维度配专门方法
lesson: 四维框架覆盖全面，方法各司其职（统计描述/月份指数/三角函数/非参检验），结构清晰不易漏项
avoid: 研究它们的变化规律，需要从统计特征、季节性、周期性和突变性四个方面来入手。
source: 2023国赛E|基于小波变换和背包模型的小浪底水库最优监测方案研究|E176
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-755

```yaml
problem_type: 机理
situation: 题干文字几何参数转化为模型常量
method: 把板长、孔径、孔心距等文字尺寸折算为模型常量，龙头板与普通板分段取值。
failure: 把板长、孔径、孔心距等文字尺寸折算为模型常量，龙头板与普通板分段取值。
lesson: 几何机理建模的第一步就是参数抽取，任一常量算错则全部结果失真
avoid: 已知龙头板长341cm：龙身和龙尾板凳长220cm，孔的中心离最近的板头距离为27.5cm。
source: 2024国赛A|基于几何模型的舞龙队位置和速度分析|A016
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-756

```yaml
problem_type: 机理
situation: 递推得到多节点位置速度后挖掘规律
method: 用路程差-时间图发现规律：路程差单调递增且为凹函数，推出龙身速度必衰减、越靠尾衰减越大
failure: 用路程差-时间图发现规律：路程差单调递增且为凹函数，推出龙身速度必衰减、越靠尾衰减越大
lesson: 把海量表格数据压缩成可解释的物理规律，与龙头恒速的题设相互印证
avoid: ①龙身与龙头前把手的路程差均关于时间单调递增，函数图像为凹函数，斜率不断增大。
source: 2024国赛A|基于自标优化的板凳龙形态调节|A053
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-757

```yaml
problem_type: 机理
situation: 螺旋运动坐标分量分析
method: 对x方向位移画图发现周期性变化、幅值随螺旋内收递减，且不同节间呈相位差滞后
failure: 对x方向位移画图发现周期性变化、幅值随螺旋内收递减，且不同节间呈相位差滞后
lesson: 用分量图佐证螺旋加滞后的运动特性，解释后续递推建模的合理性
avoid: 每一块板竞前把手在x方向的位移随着时间呈现周期性变化，且位移幅值随时间的增大而减小。
source: 2024国赛A|基于自标优化的板凳龙形态调节|A053
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-758

```yaml
problem_type: 机理
situation: 质点沿已知参数曲线（螺线）恒速运动，求位置-时间关系
method: 用弧长积分把“恒速×时间”与曲线参数（极角）关联，反解参数后经坐标变换得位置
failure: 用弧长积分把“恒速×时间”与曲线参数（极角）关联，反解参数后经坐标变换得位置
lesson: 把运动学问题化为单变量求根，避免对整条链做微分方程数值积分
avoid: 根据螺线长度积分公式，能够得到以下关系式：o·to=∫√(ρ(θ)²+ρ'(θ)²)dθ
source: 2024国赛A|基于几何模型的板凳龙运动路径问题|A163
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-759

```yaml
problem_type: 机理
situation: 链式刚体逐节递推各把手位置
method: 由前把手位置加定长约束，用余弦定理建隐式方程求后把手参数，逐节递推整链构型
failure: 由前把手位置加定长约束，用余弦定理建隐式方程求后把手参数，逐节递推整链构型
lesson: 定长约束给出闭式几何关系，可批量生成整链逐时刻数据
avoid: 联立式（1）、式（2）：采用二分求零点的方法可解得θ1与θ2，进而通过坐标转化公式得到该板凳后把手中心位置的坐标
source: 2024国赛A|基于几何模型的板凳龙运动路径问题|A163
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-760

```yaml
problem_type: 机理
situation: 求链式刚体上各点速度
method: 利用同一刚体上两点沿连体方向速度分量相等，结合各点速度方向与连线的夹角递推速度
failure: 利用同一刚体上两点沿连体方向速度分量相等，结合各点速度方向与连线的夹角递推速度
lesson: 把刚体约束转化为速度递推，比整体动力学模型计算量小得多
avoid: 利用前后把手关于板竞的关联速度建立速度选代公式，由龙头前把手的恒定速度得到各个时刻整个舞龙队各把手的速度
source: 2024国赛A|基于几何模型的板凳龙运动路径问题|A163
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-761

```yaml
problem_type: 机理
situation: 判定舞龙队板凳之间是否碰撞
method: 把碰撞检测化为关键角点到相邻板凳前后把手连线距离与半板宽的比较，逐时刻检查
failure: 把碰撞检测化为关键角点到相邻板凳前后把手连线距离与半板宽的比较，逐时刻检查
lesson: 避免复杂多边形相交计算，判据简单且可编程逐时刻执行
avoid: 本文利用角点到弦所在直线的距离来刻画碰撞与否：当距离小于板完的半宽时说明已经发生了碰撞。
source: 2024国赛A|基于几何模型的板凳龙运动路径问题|A163
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-762

```yaml
problem_type: 机理
situation: 多值函数,分段轨迹,极角约束
method: 轨迹为极角多值函数时仍以极角求位置，约束复杂难解（应时间参数化）
failure: 轨迹为极角多值函数时仍以极角求位置，约束复杂难解（应时间参数化）
lesson: 论文摘要自述该困难并改用单值函数解决，说明此坑真实存在且直接影响求解
avoid: 由于运动轨迹关于极角为多值函数，在求解位置时，对极角的约束十分复杂，因此我们使用单值函用于龙身位置和速度的求解。
source: 2024国赛A|板凳龙表演的行进路径与速度控制|A178
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-763

```yaml
problem_type: 机理
situation: 离散判定,连续过程,碰撞漏检
method: 对连续运动只做离散时刻碰撞判定，存在漏检局限
failure: 对连续运动只做离散时刻碰撞判定，存在漏检局限
lesson: 论文模型缺点自述，评审可能追问步长选择依据，应主动声明局限并加密步长
avoid: 对于“板凳龙”运动这一连续过程，本文仅对离散时刻进行碰撞判定。
source: 2024国赛A|板凳龙表演的行进路径与速度控制|A178
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-764

```yaml
problem_type: 机理
situation: 连续运动链需要全体把手的位置与速度
method: 先解龙头（源头）再沿链递推：极坐标微分方程求龙头位置函数→余弦定理逆推相邻把手→对递推式求导得速度
failure: 先解龙头（源头）再沿链递推：极坐标微分方程求龙头位置函数→余弦定理逆推相邻把手→对递推式求导得速度
lesson: 把223节的整体运动拆成“源头+递推”两个子问题，避免逐节独立列方程，计算复杂度线性化
avoid: 针对龙头位置：建立有关极角的微分方程：利用微积分及一分法求解龙头前把手的极坐标，维继而利用余弦定理，逆推求解相邻板完的位置关系，获得各把手的位置函数。
source: 2024国赛A|基于动态搜索的“板凳龙”运动状态及路线研究|A242
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-765

```yaml
problem_type: 机理
situation: 调头路径由螺线、两段圆弧组合，轨迹方程不统一
method: 把全程路径按几何特征切分为P/M/N/Q四段，逐段给出参数方程，再按把手跨段情况分类递推
failure: 把全程路径按几何特征切分为P/M/N/Q四段，逐段给出参数方程，再按把手跨段情况分类递推
lesson: 复杂组合曲线无法用一个方程表达，分段建模+跨段判别使每段都可用简单方程求解
avoid: 我们将从一100s至100s舞龙队经过的路径分为四块，如图17所示
source: 2024国赛A|基于动态搜索的“板凳龙”运动状态及路线研究|A242
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-766

```yaml
problem_type: 优化
situation: 多小问综合题的结果呈现
method: 每一问先给决策依据再给决策指标，最终以“最终决策方案+决策指标终值”表收束
failure: 每一问先给决策依据再给决策指标，最终以“最终决策方案+决策指标终值”表收束
lesson: 使“依据→指标→方案→数值”链条完整，评委可逐问核对
avoid: 以单件合格成品利润期望量最大化为决策依据，单件合格成品利润期望值为决策指标。可整理每种情况最终决策方案如下表
source: 2024国赛B|生产过程中的决策优化设计|B159
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-767

```yaml
problem_type: 优化
situation: 多阶段生产流程的检验与拆解决策
method: 将流程拆为阶段，每个'是否检验/拆解'决策编码为0-1变量，目标统一转化为净利润期望的单目标优化
failure: 将流程拆为阶段，每个'是否检验/拆解'决策编码为0-1变量，目标统一转化为净利润期望的单目标优化
lesson: 把非结构化流程决策变成可优化的变量向量，单目标可解且结论易于翻译成文字方案
avoid: 将决策转化为概率事件，把决策对应的价值期望转化为净利润的比较，建立以最大化利润为目标的单目标决策优化模型（摘要与5.2节概括）
source: 2024国赛B|基于多阶段模拟仿真的生产决策问题|B195
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-768

```yaml
problem_type: 优化
situation: 题目未给真实产品数据
method: 按现象规律生成正态分布仿真数据，设定随机种子做多次重复抽样实验
failure: 按现象规律生成正态分布仿真数据，设定随机种子做多次重复抽样实验
lesson: 数据自洽可复现，多次重复实验使比较结论具有统计意义
avoid: 根据实际现象规律，生成一组正态分布数据，并根据标准正态分布、给定的次品率得到次品的数据范围，再比较不同抽样的仿真结果得出优劣（5.1.4概括）
source: 2024国赛B|基于多阶段模拟仿真的生产决策问题|B195
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-769

```yaml
problem_type: 优化
situation: 抽样检测样本量设计,方差未知,显著性水平反解
method: 二项分布→莫弗-拉普拉斯正态近似→方差未知构造t统计量→假设检验反解(n,k)，取满足均值误差允许范围的最小样本量与最大可接受次品数
failure: 二项分布→莫弗-拉普拉斯正态近似→方差未知构造t统计量→假设检验反解(n,k)，取满足均值误差允许范围的最小样本量与最大可接受次品数
lesson: 把“检测次数尽可能少”转化为显著性水平约束下的最小n与临界k，使方案可执行且统计意义明确
avoid: 我们设定了一个误差允许范围，即均值误差需控制在10%以内，以此作为误差接受的标准。据此，当样本量Ⅱ达到1600次时，参数k达到其最大值176，对应的样本均值为0.11，恰好满足我们所设定的临界条件
source: 2024国赛B|基于蚁群算法与遗传算法优化的蒙特卡洛模拟在生产决策优化中的应用研究|B196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-770

```yaml
problem_type: 优化
situation: 生产决策,成本分解,利润目标函数,数量流
method: 按购买/检测/装配/拆解/调换六类成本逐项公式化，装配率=(1-次品率×检测决策)，收益只计合格成品销量，利润=收益-成本
failure: 按购买/检测/装配/拆解/调换六类成本逐项公式化，装配率=(1-次品率×检测决策)，收益只计合格成品销量，利润=收益-成本
lesson: 全口径列式避免成本漏项，且目标函数可直接写入模拟程序逐路径计算期望利润
avoid: 根据决策流程图可知，问题二中的企业生产成本有如下六个来源：零件购买成本（C）零件检测成本（C）成品装配成本（C3）、成品检测成本（C4）、成品拆解成本（Cs）以及用户调换成本（Cg）
source: 2024国赛B|基于蚁群算法与遗传算法优化的蒙特卡洛模拟在生产决策优化中的应用研究|B196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-771

```yaml
problem_type: 优化
situation: 问题一需确定未来7年预期销售量的基准值
method: 直接用2023年各季次实际产量作为2024-2030年的预期销售量
failure: 直接用2023年各季次实际产量作为2024-2030年的预期销售量
lesson: 题目假设各参数与2023年保持一致,用历史产量作需求基准最直接且可复现
avoid: 问题一假设未来各类农作物的预期销售量，种植成本，亩产量及销售价格相较2023年保持不变。固此，在问题一中，2024至2030年期间的农作物预期销售量等同于2023年的产量。
source: 2024国赛C|基于差分遗传算法的农作物种植策略优化|C038
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-772

```yaml
problem_type: 优化
situation: 需识别哪些作物利润高以指导种植结构安排
method: 分类计算亩均利润并排名,得到粮食<蔬菜<食用菌的利润梯度
failure: 分类计算亩均利润并排名,得到粮食<蔬菜<食用菌的利润梯度
lesson: 利润排名直接决定种植倾向,是后续约束设定和目标函数的数据支撑
avoid: 蔬菜类作物的亩均利润显著高于粮食类，尤其是黄瓜，空心菜等高附加值品种，亩均利润突破了50000元
source: 2024国赛C|基于差分遗传算法的农作物种植策略优化|C038
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-773

```yaml
problem_type: 优化
situation: 不确定性参数只给波动区间,需生成情景以评估风险
method: 用蒙特卡洛模拟生成1000个情景覆盖销量/产量/成本/价格波动
failure: 用蒙特卡洛模拟生成1000个情景覆盖销量/产量/成本/价格波动
lesson: 情景化使CVaR可计算,且得到适用于所有情景的全局最优方案
avoid: 通过蒙特卡落模拟生成1000个不同情景：涵盖预期销售量，亩产量，种植成本和销售价格等多种市场条件的变化。
source: 2024国赛C|基于差分遗传算法的农作物种植策略优化|C038
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-774

```yaml
problem_type: 统计
situation: 随机抽样实验设计
method: 状态抽样组数前后不一致(6组/16组/1000组/11组典型),叙述混乱
failure: 状态抽样组数前后不一致(6组/16组/1000组/11组典型),叙述混乱
lesson: 评审会质疑实验设计的稳定性与可复现性
avoid: 那么我们首先随机拍取6组种植自然状态如下表：通过随机拍样的方法针对4种不确定性因素抽取16组种植状态样本
source: 2024国赛C|基于优化算法的农作物最优种植模型|C063
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-775

```yaml
problem_type: 评价
situation: 数据预处理简化
method: 销售单价取价格区间最大值最小值的平均值,丢失区间内分布信息
failure: 销售单价取价格区间最大值最小值的平均值,丢失区间内分布信息
lesson: 简化处理虽可行,但未说明区间分布对结果的影响
avoid: 此处采用平均值法价格最大值和最小值的平均值为每种农作物的销售单价
source: 2024国赛C|基于优化算法的农作物最优种植模型|C063
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-776

```yaml
problem_type: 优化
situation: 多地块多作物多年种植分配
method: 构建收益最大化线性规划：连续面积变量+0-1种植变量，大M法耦合
failure: 构建收益最大化线性规划：连续面积变量+0-1种植变量，大M法耦合
lesson: 面积分配与是否种植的耦合是混合整数结构，大M线性化使其可被求解器处理
avoid: 利用大M法链接Xeue与Y
source: 2024国赛C|基于随机优化的农作物种植策略模型|C094
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-777

```yaml
problem_type: 优化
situation: 作物间存在可替代与互补关系
method: 替代因子α转移需求（总需求不变）+互补系数修正产量与成本
failure: 替代因子α转移需求（总需求不变）+互补系数修正产量与成本
lesson: 用稳定增长作物替代不稳定作物并利用豆类轮作增产，贴近真实农业
avoid: 替代公式：替代因子0属于0.11. Requestk+=XRequesttek,Requestk=RequestukX(l-a)
source: 2024国赛C|基于随机优化的农作物种植策略模型|C094
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-778

```yaml
problem_type: 优化
situation: 耕地资源,地块类型,豆类轮作,重茬约束
method: 耕地1213亩分平旱地/梯田/山坡地/水浇地/普通大棚/智慧大棚6类，每块地3年内至少种一次豆科且不能连续重茬
failure: 耕地1213亩分平旱地/梯田/山坡地/水浇地/普通大棚/智慧大棚6类，每块地3年内至少种一次豆科且不能连续重茬
lesson: 交代问题数据规模与硬性约束，支撑后续约束建模
avoid: 其耕地面积1213亩，包含平早地、梯田、山坡地、水浇地，普通大期与智息大用共6种类型。为提高农作物的产量，母块耕地3年内全少种植一次豆科植物且每种农作物不能在同一块地连续重茬种植。
source: 2024国赛C|基于遗传算法的最优种植策略|C234
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-779

```yaml
problem_type: 优化
situation: 华北山区,自然灾害,寒潮,干旱,损失率
method: 据文献华北地区约1.9年一次严重寒潮、干旱损失率9.3%，据此设定灾害因子
failure: 据文献华北地区约1.9年一次严重寒潮、干旱损失率9.3%，据此设定灾害因子
lesson: 灾害减产比例有文献依据，避免凭空设定参数
avoid: 1959年~2009年华北地区50年间，发生持续性寒潮共出26次平均1.9年就会出现一次严重的寒潮
source: 2024国赛C|基于遗传算法的最优种植策略|C234
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-780

```yaml
problem_type: 单弹命中概率优化
situation: 定位误差已知分布，求使命中概率最大的落点与引爆深度
method: 以落点(t,s)与引爆深度d为决策变量，按d与潜艇位置的5种相对位置给出命中概率表达式，用深度区间最优定理+定长区间积分最大化引理证明最优方案，落点为定位点即看哪打哪
failure: 以落点(t,s)与引爆深度d为决策变量，按d与潜艇位置的5种相对位置给出命中概率表达式，用深度区间最优定理+定长区间积分最大化引理证明最优方案，落点为定位点即看哪打哪
lesson: 先解析推导一般关系并证明，再代入参数数值计算，结论可证可算
avoid: 投弹命中概率最大的投弹方案为：东西方向1=0.南北方向5=0.印投弹落点平面坐标为“看哪打哪”定深引信引爆深度设定在潜艇砖=h-H与=h+H之间，即潜艇上下表面之间
source: 2024国赛D|反潜航空深弹命中概率的优化问题|2024_D_D033
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-781

```yaml
problem_type: 优化
situation: 单点信号配时与干线协调
method: Webster公式求单点最优周期，按交叉口距离算相位差做绿波协调
failure: Webster公式求单点最优周期，按交叉口距离算相位差做绿波协调
lesson: 经典配时公式有理论支撑，绿波协调提升干线通行效率
avoid: 方法一采用韦佰斯特（webster）信号配时方法计算单点信号控制最优方案。根据各交叉口距离计算相位差，选取公共周期下限与上限，以2s为步长寻优干线协调绿波控制方案
source: 2024国赛E|交通流量管控|E010
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-782

```yaml
problem_type: 统计
situation: 一天24小时车流需划分为可操作时段
method: 按小时聚合车流量并标准化,用K-Means聚类,以肘部法(组内平方和WCSS)确定最优聚类数k=3,得到高峰/中峰/低峰时段
failure: 按小时聚合车流量并标准化,用K-Means聚类,以肘部法(组内平方和WCSS)确定最优聚类数k=3,得到高峰/中峰/低峰时段
lesson: 数据驱动划分时段,聚类结果可视(散点图),时段边界由聚类结构而非主观划定
avoid: 通过时部法分析结果，确定最佳聚类数kG通常是使WCSS降低速度明显减缓的k值：如图中建议选择=3。
source: 2024国赛E|基于多目标优化的交通管理评估分析|E061
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-783

```yaml
problem_type: 统计
situation: 车辆在监控点间的速度与访问频次可计算
method: 以监控点距离/时间差算车速,以同一监控点半小时间隔连续访问至少3次判重复出现,低速(<15km/h)与重复出现取集合交集得巡游车辆
failure: 以监控点距离/时间差算车速,以同一监控点半小时间隔连续访问至少3次判重复出现,低速(<15km/h)与重复出现取集合交集得巡游车辆
lesson: 双条件把"巡游"这一模糊概念操作化为可编程的判定规则,降低单一条件误判
avoid: 最终的巡游车辆集合S.为：S.=S,nSr 即车辆必须同时满足低速和重复出现的条件。
source: 2024国赛E|基于多目标优化的交通管理评估分析|E061
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-784

```yaml
problem_type: 统计
situation: K-means聚类划分时段
method: 聚类只关注数据相似点,未考虑车流量时间连续性
failure: 聚类只关注数据相似点,未考虑车流量时间连续性
lesson: 相邻小时流量被分到不同时期,时段划分合理性受损
avoid: 本文所使用的K-均值算法没有考患车流量的时间连续性：只关注数据的相似点
source: 2024国赛E|基于Python语言的交通流量管控与预测分析|E218
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-785

```yaml
problem_type: 统计
situation: 排队论估算停车需求
method: 排队论模型难以应对交通事故等极端情况
failure: 排队论模型难以应对交通事故等极端情况
lesson: 到达/服务率平稳假设在突发事件下失效
avoid: 排队论模型难以应对极端的情况：例如发生交通事故。
source: 2024国赛E|基于Python语言的交通流量管控与预测分析|E218
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-786

```yaml
problem_type: 通用
situation: 仿真验证规模受限
method: 路口多时间有限,仅对两个路口做VISSIM仿真
failure: 路口多时间有限,仅对两个路口做VISSIM仿真
lesson: 验证样本少,外推全网络结论的支撑力有限
avoid: 没有模拟所有的交叉路口，只对其中两个路口进行模拟仿真：后期会将本仿真模拟进行进一步地完善。
source: 2024国赛E|基于Python语言的交通流量管控与预测分析|E218
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-787

```yaml
problem_type: 机理
situation: 判定圆柱目标是否被烟幕完全遮挡
method: 视线线段与球体相交判定（二次方程判别式），并证明只需判定上下底面圆周
failure: 视线线段与球体相交判定（二次方程判别式），并证明只需判定上下底面圆周
lesson: 对圆柱整面离散取点效率低，外轮廓/凸性证明将判定维数大幅压缩
avoid: 只需判断柱体上下两个底面圆周是否被完全遮蔽，即可判定整个圆柱体是否被完全遮蔽
source: 2025国赛A|多情形下无人机烟幕遮蔽策略的建模与优化研究|A196
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-788

```yaml
problem_type: 机理
situation: 数据来源,反射率光谱,不同入射角,附件划分
method: 附件1、2提供碳化硅片不同入射角（10°和15°）的反射率光谱数据，附件3、4提供硅晶片数据；问题2用前两者测厚，问题3用后两者分析多光束效应
failure: 附件1、2提供碳化硅片不同入射角（10°和15°）的反射率光谱数据，附件3、4提供硅晶片数据；问题2用前两者测厚，问题3用后两者分析多光束效应
lesson: 同一套数据按题目分问使用，且两入射角互为重复实验样本
avoid: 对附件提供的不 同入射角的碳化硅片的光谱实验数据进行分折计开，给出计异结来并评估结果的可靠性（原文：用红外光反射率光谱计算碳化硅外延层的厚度）
source: 2025国赛B|红外干涉法测量外延层厚度的建模分析|B060
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-789

```yaml
problem_type: 双光束干涉测厚机理建模
situation: 在仅考虑两界面各一次反射的假设下建立厚度与反射光谱的关系
method: Snell定律修正入射角得层内折射角，推光程差与相位差，Fresnel公式算两界面反射系数，Cauchy模型描述折射率色散，组合成总反射率随波数变化的模型
failure: Snell定律修正入射角得层内折射角，推光程差与相位差，Fresnel公式算两界面反射系数，Cauchy模型描述折射率色散，组合成总反射率随波数变化的模型
lesson: 从物理第一性原理逐层推导，模型可解释且可外推
avoid: 根据Snell定律，外延层中的折射角为nosindo=ni()sind1
source: 2025国赛B|碳化硅外延层厚度的双光束和多光束干涉法测量研究|2025_B_B157
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-790

```yaml
problem_type: 优化
situation: 检测时点决策
method: 期望损失最小化：技术失败风险+时间风险+正则化
failure: 期望损失最小化：技术失败风险+时间风险+正则化
lesson: 风险函数显式刻画安全-及时-可执行三目标权衡
avoid: 该风险由两部分构成：技术失败风险（t，b）：在推荐孕周t进行抽血检测时，胎儿Y染色体浓度仍未达到阈值θ=4%的概率
source: 2025国赛C|基于混合效应模型的NIPT时点优化与胎儿异常判定|C023
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-791

```yaml
problem_type: 统计
situation: 同一孕妇多次检测构成重复测量层次数据
method: 用线性混合效应模型刻画:固定效应估计孕周/BMI/身高总体效应,随机截距捕捉孕妇个体间变异,REML估计参数
failure: 用线性混合效应模型刻画:固定效应估计孕周/BMI/身高总体效应,随机截距捕捉孕妇个体间变异,REML估计参数
lesson: 同时处理个体内相关性与个体间异质性,避免普通回归低估标准误导致虚假显著
avoid: 该模型通过引人随机效应项来捕提个体层面的随机变异，同时保留固定效应项来估计总体层面的平均效应
source: 2025国赛C|基于统计建模与元学习的NIPT检测决策优化与异常识别|C132
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-792

```yaml
problem_type: 预测
situation: 每位孕妇观测点稀疏,需推断最早达标孕周T_attain
method: 三阶段分层决策:单点观测直接判达标与否,多点观测先算趋势相关系数,相关为正才用GPR外推,再以实测达标点取保守最小并做边界截断
failure: 三阶段分层决策:单点观测直接判达标与否,多点观测先算趋势相关系数,相关为正才用GPR外推,再以实测达标点取保守最小并做边界截断
lesson: 稀疏数据下模型外推不可靠,实测数据优先+保守修正,降低错误推断风险
avoid: 若corrt.<0，这表明观测数据显示浓度随孕周增加而下降...暂时无法建立有意义的增长模型...若cOrC.y≥0，趋势合理，则以y)拟合独立GPR模型
source: 2025国赛C|基于统计建模与元学习的NIPT检测决策优化与异常识别|C132
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-793

```yaml
problem_type: 机理
situation: 三维网络规模增大
method: 模型计算复杂度高,三维模型中随巷道网络规模增大计算量大幅增加
failure: 模型计算复杂度高,三维模型中随巷道网络规模增大计算量大幅增加
lesson: 大规模巷道网络下推演耗时长,实用性受限
avoid: 在涉及到多种复杂情况（如多个突水点，矿工逃生路径设计等）时，模型的计算复杂度较高。
source: 2025国赛D|矿井突水水流漫延模型与逃生方案问题|D037
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-794

```yaml
problem_type: 通用
situation: 模型一般化程度不足
method: 只针对给定突水点数量与巷道高度建四个模型,未一般化
failure: 只针对给定突水点数量与巷道高度建四个模型,未一般化
lesson: 换参数需重新建模,缺乏可推广的统一框架
avoid: 由于时间有限，我们建立了四个模型，解决问题一到问题四，我们可以进一步以突水点数量和巷道高度为变量，从而建立一个更一般化的模型。
source: 2025国赛D|矿井突水水流漫延模型与逃生方案问题|D037
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-795

```yaml
problem_type: 图论
situation: 矿工位置在巷道内而非端点
method: 把矿工位置直接近似为端点参与Dijkstra计算
failure: 把矿工位置直接近似为端点参与Dijkstra计算
lesson: 近似忽略矿工在巷道内的精确位置,引入一定误差
avoid: 进一步运用Dijkstra算法：将矿工位置P近似为在“P0661”端点
source: 2025国赛D|矿井突水水流漫延模型与逃生方案问题|D037
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-796

```yaml
problem_type: 统计
situation: 识别起跳与落地时刻
method: 脚部四点均值+一阶微分（速度序列）+突变阈值±150px/s自动识别
failure: 脚部四点均值+一阶微分（速度序列）+突变阈值±150px/s自动识别
lesson: 起跳离地/落地触地对应垂直速度突变，力学机理明确，识别客观可复现
avoid: 本文采用数值一阶微分方法，对起践与落地时刻进行自动识别
source: 2025国赛E|基于姿态识别的AI辅助智能体测研究|E030
confidence: 中
source_quality: 中
memory_type: paper_extract
```

## FD-797

```yaml
problem_type: 统计
situation: 小样本且变量可能非正态
method: 采用Spearman秩相关分析体质/姿态因素与成绩的关系
failure: 采用Spearman秩相关分析体质/姿态因素与成绩的关系
lesson: 秩相关不依赖正态分布假设，适合小样本
avoid: 由于数据样本量较少，并且部分变量之间可能不满足正态分布假设，因此采用斯皮尔曼相关分析
source: 2025国赛E|基于姿态识别的AI辅助智能体测研究|E030
confidence: 中
source_quality: 中
memory_type: paper_extract
```


---

## FD-798（外部交付·2019C机场出租车）

```yaml
failure_id: FD-798
problem_type: 优化决策/排队
method: 设单上车点
failure: 乘客等待长、蓄车池溢出，单点成瓶颈
cause: 单车道单上车点吞吐受限
signal: 等待队伍长、吞吐不随需求涨
lesson: 双车道设多上车点（4-6个），吞吐近似 k·μ 线性提升；勿设单点瓶颈
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-799（外部交付·2019C机场出租车）

```yaml
failure_id: FD-799
problem_type: 优化决策/排队
method: 只算蓄车池等待、忽略返城空载成本
failure: 司机决策偏离真实最优
cause: 单边估算只建模等待成本，漏了空载机会成本
signal: 结论与现实中"高峰空返"矛盾
lesson: 双边成本同时建模：等待成本与返城空载/机会成本比较，再决定排队或空返
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-800（外部交付·2019C机场出租车）

```yaml
failure_id: FD-800
problem_type: 优化决策/排队
method: 长短途无差别排队
failure: 短途乘客打车难，短途供给不足
cause: 长短途单位时间收益差大（15 vs 29.5元/h），无差别排队让短途司机不接
signal: 短途车少、乘客等车难
lesson: 设短途绿色通道（≤L0公里优先凭证），平衡长短途收益
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-801（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: 朴素谐振效率公式 η=k²Q₁Q₂/(1+k²Q₁Q₂)
failure: Q1 数值偏离官方 56.20%（缺一个 Q 项与 1/(k²Q₁Q₂) 交叉项）
cause: 常见简化式忽略 Q₂/Q₁ 比与交叉项
signal: 复算数值对不上官方参考答案
lesson: 必须用含 Q₂/Q₁ 比与 1/(k²Q₁Q₂) 的完整 ABCD 闭式
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-802（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 任意（代码）
method: Python f-string 含字面 % 与 % 运算符混用
failure: 打印语句含"(eta>80%)"又用 % 运算符格式化，抛 ValueError 使整段 Q4 报错
cause: 字面 % 与格式化 % 冲突
signal: 打印行报 ValueError
lesson: 统一改用 f-string，避免字面 % 与 % 运算符混用
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-803（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理（窄领域）
method: 经验库检索（问题指纹）
failure: 窄领域机理题（WPT）检索命中1582条但无专属 SD/FD，top-12 无 WPT 专属条目
cause: 库内无该窄领域经验，泛化条目占满
signal: n_matched 高但 top 全是泛化条目
lesson: 窄领域机理题勿过度依赖经验库，以第一性原理+文献为主，检索仅作方法论弱信号
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 中
```

---

## FD-804（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: R₂ 口径未拆分（附件给的接收装置电阻 RL 当线圈电阻）
failure: 附件2 的 RL=432.24Ω 已含负载，当线圈电阻会数值漂移
cause: 口径混淆（接收装置电阻 vs 线圈电阻）
signal: Q1 数值不稳定
lesson: 按同工艺 R₂=R₁=1.55Ω，R_L=432.24−1.55=430.69Ω；正文/求解/代码三处口径须一致
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-805（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/运输调度
method: 储能 LP 峰值约束写为 P - gb + gs ≤ 0
failure: LP 约束符号写反，解出现"不卖电反而亏"的反常值(gs=0)
cause: 峰谷约束方向与"可充可放"的物理含义没对上
signal: 解出现不卖电反而亏的反常值(gs=0)
lesson: LP 约束写完后做一次手工可行解对照，挡掉符号写反
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-806（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/多目标
method: QoS 定义为 1 - delay/W（与"越早越好"绑定）
failure: 所有 Pareto 解 QoS≈1.0，多目标失去区分度
cause: QoS 定义方式让"完成即满分"，没有惩罚延迟
signal: 所有 Pareto 解 QoS≈1.0
lesson: 改用"柔性任务完成时延 < ½ 最大容忍时延"的比例指标
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-807（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/调度
method: P4 placement 按逐到达循环（28800 次/调用 × 80 点）
failure: 进程无 stdout 直接退出，疑似超时/内存崩
cause: 逐到达循环嵌套爆炸，O(28800×80) 每调用
signal: 进程无 stdout 直接退出
lesson: 改按任务类型聚合的 O(12) 向量化；输出重定向到日志文件排查
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-808（外部交付·2019C机场出租车）

```yaml
failure_id: FD-808
problem_type: 优化决策/排队
method: 设单上车点
failure: 乘客等待长、蓄车池溢出，单点成瓶颈
cause: 单车道单上车点吞吐受限
signal: 等待队伍长、吞吐不随需求涨
lesson: 双车道设多上车点（4-6个），吞吐近似 k·μ 线性提升；勿设单点瓶颈
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-809（外部交付·2019C机场出租车）

```yaml
failure_id: FD-809
problem_type: 优化决策/排队
method: 只算蓄车池等待、忽略返城空载成本
failure: 司机决策偏离真实最优
cause: 单边估算只建模等待成本，漏了空载机会成本
signal: 结论与现实中"高峰空返"矛盾
lesson: 双边成本同时建模：等待成本与返城空载/机会成本比较，再决定排队或空返
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-810（外部交付·2019C机场出租车）

```yaml
failure_id: FD-810
problem_type: 优化决策/排队
method: 长短途无差别排队
failure: 短途乘客打车难，短途供给不足
cause: 长短途单位时间收益差大（15 vs 29.5元/h），无差别排队让短途司机不接
signal: 短途车少、乘客等车难
lesson: 设短途绿色通道（≤L0公里优先凭证），平衡长短途收益
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-811（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: 朴素谐振效率公式 η=k²Q₁Q₂/(1+k²Q₁Q₂)
failure: Q1 数值偏离官方 56.20%（缺一个 Q 项与 1/(k²Q₁Q₂) 交叉项）
cause: 常见简化式忽略 Q₂/Q₁ 比与交叉项
signal: 复算数值对不上官方参考答案
lesson: 必须用含 Q₂/Q₁ 比与 1/(k²Q₁Q₂) 的完整 ABCD 闭式
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-812（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 任意（代码）
method: Python f-string 含字面 % 与 % 运算符混用
failure: 打印语句含"(eta>80%)"又用 % 运算符格式化，抛 ValueError 使整段 Q4 报错
cause: 字面 % 与格式化 % 冲突
signal: 打印行报 ValueError
lesson: 统一改用 f-string，避免字面 % 与 % 运算符混用
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-813（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理（窄领域）
method: 经验库检索（问题指纹）
failure: 窄领域机理题（WPT）检索命中1582条但无专属 SD/FD，top-12 无 WPT 专属条目
cause: 库内无该窄领域经验，泛化条目占满
signal: n_matched 高但 top 全是泛化条目
lesson: 窄领域机理题勿过度依赖经验库，以第一性原理+文献为主，检索仅作方法论弱信号
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 中
```

---

## FD-814（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: R₂ 口径未拆分（附件给的接收装置电阻 RL 当线圈电阻）
failure: 附件2 的 RL=432.24Ω 已含负载，当线圈电阻会数值漂移
cause: 口径混淆（接收装置电阻 vs 线圈电阻）
signal: Q1 数值不稳定
lesson: 按同工艺 R₂=R₁=1.55Ω，R_L=432.24−1.55=430.69Ω；正文/求解/代码三处口径须一致
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-815（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/运输调度
method: 储能 LP 峰值约束写为 P - gb + gs ≤ 0
failure: LP 约束符号写反，解出现"不卖电反而亏"的反常值(gs=0)
cause: 峰谷约束方向与"可充可放"的物理含义没对上
signal: 解出现不卖电反而亏的反常值(gs=0)
lesson: LP 约束写完后做一次手工可行解对照，挡掉符号写反
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-816（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/多目标
method: QoS 定义为 1 - delay/W（与"越早越好"绑定）
failure: 所有 Pareto 解 QoS≈1.0，多目标失去区分度
cause: QoS 定义方式让"完成即满分"，没有惩罚延迟
signal: 所有 Pareto 解 QoS≈1.0
lesson: 改用"柔性任务完成时延 < ½ 最大容忍时延"的比例指标
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-817（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/调度
method: P4 placement 按逐到达循环（28800 次/调用 × 80 点）
failure: 进程无 stdout 直接退出，疑似超时/内存崩
cause: 逐到达循环嵌套爆炸，O(28800×80) 每调用
signal: 进程无 stdout 直接退出
lesson: 改按任务类型聚合的 O(12) 向量化；输出重定向到日志文件排查
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-818（外部交付·2019C机场出租车）

```yaml
failure_id: FD-818
problem_type: 优化决策/排队
method: 设单上车点
failure: 乘客等待长、蓄车池溢出，单点成瓶颈
cause: 单车道单上车点吞吐受限
signal: 等待队伍长、吞吐不随需求涨
lesson: 双车道设多上车点（4-6个），吞吐近似 k·μ 线性提升；勿设单点瓶颈
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-819（外部交付·2019C机场出租车）

```yaml
failure_id: FD-819
problem_type: 优化决策/排队
method: 只算蓄车池等待、忽略返城空载成本
failure: 司机决策偏离真实最优
cause: 单边估算只建模等待成本，漏了空载机会成本
signal: 结论与现实中"高峰空返"矛盾
lesson: 双边成本同时建模：等待成本与返城空载/机会成本比较，再决定排队或空返
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-820（外部交付·2019C机场出租车）

```yaml
failure_id: FD-820
problem_type: 优化决策/排队
method: 长短途无差别排队
failure: 短途乘客打车难，短途供给不足
cause: 长短途单位时间收益差大（15 vs 29.5元/h），无差别排队让短途司机不接
signal: 短途车少、乘客等车难
lesson: 设短途绿色通道（≤L0公里优先凭证），平衡长短途收益
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-821（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: 朴素谐振效率公式 η=k²Q₁Q₂/(1+k²Q₁Q₂)
failure: Q1 数值偏离官方 56.20%（缺一个 Q 项与 1/(k²Q₁Q₂) 交叉项）
cause: 常见简化式忽略 Q₂/Q₁ 比与交叉项
signal: 复算数值对不上官方参考答案
lesson: 必须用含 Q₂/Q₁ 比与 1/(k²Q₁Q₂) 的完整 ABCD 闭式
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-822（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 任意（代码）
method: Python f-string 含字面 % 与 % 运算符混用
failure: 打印语句含"(eta>80%)"又用 % 运算符格式化，抛 ValueError 使整段 Q4 报错
cause: 字面 % 与格式化 % 冲突
signal: 打印行报 ValueError
lesson: 统一改用 f-string，避免字面 % 与 % 运算符混用
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-823（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理（窄领域）
method: 经验库检索（问题指纹）
failure: 窄领域机理题（WPT）检索命中1582条但无专属 SD/FD，top-12 无 WPT 专属条目
cause: 库内无该窄领域经验，泛化条目占满
signal: n_matched 高但 top 全是泛化条目
lesson: 窄领域机理题勿过度依赖经验库，以第一性原理+文献为主，检索仅作方法论弱信号
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 中
```

---

## FD-824（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: R₂ 口径未拆分（附件给的接收装置电阻 RL 当线圈电阻）
failure: 附件2 的 RL=432.24Ω 已含负载，当线圈电阻会数值漂移
cause: 口径混淆（接收装置电阻 vs 线圈电阻）
signal: Q1 数值不稳定
lesson: 按同工艺 R₂=R₁=1.55Ω，R_L=432.24−1.55=430.69Ω；正文/求解/代码三处口径须一致
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-825（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/运输调度
method: 储能 LP 峰值约束写为 P - gb + gs ≤ 0
failure: LP 约束符号写反，解出现"不卖电反而亏"的反常值(gs=0)
cause: 峰谷约束方向与"可充可放"的物理含义没对上
signal: 解出现不卖电反而亏的反常值(gs=0)
lesson: LP 约束写完后做一次手工可行解对照，挡掉符号写反
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-826（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/多目标
method: QoS 定义为 1 - delay/W（与"越早越好"绑定）
failure: 所有 Pareto 解 QoS≈1.0，多目标失去区分度
cause: QoS 定义方式让"完成即满分"，没有惩罚延迟
signal: 所有 Pareto 解 QoS≈1.0
lesson: 改用"柔性任务完成时延 < ½ 最大容忍时延"的比例指标
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-827（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/调度
method: P4 placement 按逐到达循环（28800 次/调用 × 80 点）
failure: 进程无 stdout 直接退出，疑似超时/内存崩
cause: 逐到达循环嵌套爆炸，O(28800×80) 每调用
signal: 进程无 stdout 直接退出
lesson: 改按任务类型聚合的 O(12) 向量化；输出重定向到日志文件排查
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-828（外部交付·2019C机场出租车）

```yaml
failure_id: FD-828
problem_type: 优化决策/排队
method: 设单上车点
failure: 乘客等待长、蓄车池溢出，单点成瓶颈
cause: 单车道单上车点吞吐受限
signal: 等待队伍长、吞吐不随需求涨
lesson: 双车道设多上车点（4-6个），吞吐近似 k·μ 线性提升；勿设单点瓶颈
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-829（外部交付·2019C机场出租车）

```yaml
failure_id: FD-829
problem_type: 优化决策/排队
method: 只算蓄车池等待、忽略返城空载成本
failure: 司机决策偏离真实最优
cause: 单边估算只建模等待成本，漏了空载机会成本
signal: 结论与现实中"高峰空返"矛盾
lesson: 双边成本同时建模：等待成本与返城空载/机会成本比较，再决定排队或空返
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-830（外部交付·2019C机场出租车）

```yaml
failure_id: FD-830
problem_type: 优化决策/排队
method: 长短途无差别排队
failure: 短途乘客打车难，短途供给不足
cause: 长短途单位时间收益差大（15 vs 29.5元/h），无差别排队让短途司机不接
signal: 短途车少、乘客等车难
lesson: 设短途绿色通道（≤L0公里优先凭证），平衡长短途收益
source: 国赛2019C|机场出租车|外部用户交付(2026-08-13)
confidence: 高
```

---

## FD-831（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: 朴素谐振效率公式 η=k²Q₁Q₂/(1+k²Q₁Q₂)
failure: Q1 数值偏离官方 56.20%（缺一个 Q 项与 1/(k²Q₁Q₂) 交叉项）
cause: 常见简化式忽略 Q₂/Q₁ 比与交叉项
signal: 复算数值对不上官方参考答案
lesson: 必须用含 Q₂/Q₁ 比与 1/(k²Q₁Q₂) 的完整 ABCD 闭式
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-832（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 任意（代码）
method: Python f-string 含字面 % 与 % 运算符混用
failure: 打印语句含"(eta>80%)"又用 % 运算符格式化，抛 ValueError 使整段 Q4 报错
cause: 字面 % 与格式化 % 冲突
signal: 打印行报 ValueError
lesson: 统一改用 f-string，避免字面 % 与 % 运算符混用
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-833（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理（窄领域）
method: 经验库检索（问题指纹）
failure: 窄领域机理题（WPT）检索命中1582条但无专属 SD/FD，top-12 无 WPT 专属条目
cause: 库内无该窄领域经验，泛化条目占满
signal: n_matched 高但 top 全是泛化条目
lesson: 窄领域机理题勿过度依赖经验库，以第一性原理+文献为主，检索仅作方法论弱信号
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 中
```

---

## FD-834（2021华数杯A PSR第二场）

```yaml
failure_id: ?
problem_type: 机理/电路
method: R₂ 口径未拆分（附件给的接收装置电阻 RL 当线圈电阻）
failure: 附件2 的 RL=432.24Ω 已含负载，当线圈电阻会数值漂移
cause: 口径混淆（接收装置电阻 vs 线圈电阻）
signal: Q1 数值不稳定
lesson: 按同工艺 R₂=R₁=1.55Ω，R_L=432.24−1.55=430.69Ω；正文/求解/代码三处口径须一致
source: 2021华数杯A|电动汽车无线充电优化匹配|2026-08-13 PSR第二场
confidence: 高
```

---

## FD-835（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/运输调度
method: 储能 LP 峰值约束写为 P - gb + gs ≤ 0
failure: LP 约束符号写反，解出现"不卖电反而亏"的反常值(gs=0)
cause: 峰谷约束方向与"可充可放"的物理含义没对上
signal: 解出现不卖电反而亏的反常值(gs=0)
lesson: LP 约束写完后做一次手工可行解对照，挡掉符号写反
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-836（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/多目标
method: QoS 定义为 1 - delay/W（与"越早越好"绑定）
failure: 所有 Pareto 解 QoS≈1.0，多目标失去区分度
cause: QoS 定义方式让"完成即满分"，没有惩罚延迟
signal: 所有 Pareto 解 QoS≈1.0
lesson: 改用"柔性任务完成时延 < ½ 最大容忍时延"的比例指标
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```

---

## FD-837（2021华数杯B PSR验证场）

```yaml
failure_id: ?
problem_type: 优化/调度
method: P4 placement 按逐到达循环（28800 次/调用 × 80 点）
failure: 进程无 stdout 直接退出，疑似超时/内存崩
cause: 逐到达循环嵌套爆炸，O(28800×80) 每调用
signal: 进程无 stdout 直接退出
lesson: 改按任务类型聚合的 O(12) 向量化；输出重定向到日志文件排查
source: 2021华数杯B|进出口货物装运策略|2026-08-13 PSR验证场
confidence: 高
```
