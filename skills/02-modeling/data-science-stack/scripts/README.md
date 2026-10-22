# data-science-stack · 模板脚本

赛时直接调用，少写 80% 重复代码。所有脚本输出落盘，供 orchestrator result_registry 与论文组装使用。

## 脚本列表

| 脚本 | 功能 | 用法 |
|---|---|---|
| `eda_report.py` | 一键 EDA：逐列体检报告（缺失/异常/分布/相关性/高相关对）+ 三张基础图 | `python eda_report.py data.csv --target 目标列` |
| `timeseries_pipeline.py` | 时间序列全流程：ADF → 差分 → AIC 定阶 ARIMA → 留出验证 → 外推预测 + 置信区间 | `python timeseries_pipeline.py data.csv --date 日期列 --col 目标列 --steps 12` |

## 快速开始

```bash
# EDA：10 分钟出数据报告 + 图表
python scripts/eda_report.py 附件1.csv --target 销量 --out eda_out

# 时间序列：预测未来 12 期
python scripts/timeseries_pipeline.py data.csv --date date --col val --steps 12 --out ts_out
```

## 依赖

```bash
pip install pandas numpy matplotlib scipy statsmodels
```

- `statsmodels` 仅 `timeseries_pipeline.py` 需要
- 中文字体已内置配置（SimHei / Microsoft YaHei / Noto Sans CJK），图表自动适配国赛论文

## 输出对接

| 输出 | 论文用途 | 后续处理 |
|---|---|---|
| `report.md` | "数据预处理 / 探索性分析"节素材 | 直接摘录表格与结论 |
| `figures/distributions.png` 等 | 探索性分析配图 | 交给 modelviz 生成并由 scipilot-figure-skill 质检后再入论文 |
| `summary.txt` + `forecast.csv` | "模型建立 / 检验 / 预测结果"节 | 数字必须原样引用（结果只从代码生成） |
| `forecast.png` | 预测结果图 | 同上 |

## 约定

- 随机种子固定（seed=42），结果可复现
- 所有数字与图从脚本输出产生，论文引用不得手改
- 训练/验证划分由脚本自动完成（后 20% 留出），杜绝数据泄漏
