# 数据处理与机器学习代码注释规范

本规范适用于数据清洗、特征工程、统计分析、机器学习模型（XGBoost/随机森林/ARIMA/LSTM等）的代码。注释必须是纯粹的技术说明，禁止元话语、负向回响、内部讨论和 AI 协作痕迹。

## 一、必须有注释的位置

### 1. 文件头

每个 Python 文件开头必须有 1-3 行说明这个文件做什么。

```python
"""
企业信贷风险评估：数据清洗 + 特征工程 + XGBoost模型
输入：123家企业进销项发票数据（CSV）
输出：信用评级、违约概率、特征重要性
"""
```

### 2. 数据加载和清洗

```python
# 加载原始发票数据，编码=gbk（中文Windows导出默认编码）
df = pd.read_csv('data/invoices.csv', encoding='gbk')

# 数据清洗：删除空值行（<1%，直接删除不影响结果）
df = df.dropna(subset=['invoice_amount', 'invoice_date'])

# 异常值处理：发票金额>1000万的标记为异常（占比0.3%，可能是录入错误）
df['is_outlier'] = df['invoice_amount'] > 10000000

# 日期解析：发票日期转为datetime，用于计算账龄
df['invoice_date'] = pd.to_datetime(df['invoice_date'])
```

### 3. 特征工程

每个特征必须注释说明含义、计算方式、业务意义。

```python
# 特征1：企业总交易额（所有发票金额之和），反映企业经营规模
df['total_amount'] = df.groupby('company_id')['invoice_amount'].transform('sum')

# 特征2：交易频次（发票数量），反映企业经营活跃度
df['transaction_count'] = df.groupby('company_id')['invoice_id'].transform('count')

# 特征3：平均账期（发票日期到付款日期的平均天数），反映企业资金周转能力
df['avg_payment_days'] = (df['payment_date'] - df['invoice_date']).dt.days.groupby(df['company_id']).transform('mean')

# 特征4：进项销项比（进项金额/销项金额），反映企业上下游关系
df['input_output_ratio'] = df['input_amount'] / df['output_amount']
```

### 4. 模型配置和训练

```python
# 模型：XGBoost二分类（违约预测），选择原因：处理非线性关系+特征交互+缺失值鲁棒
model = XGBClassifier(
    n_estimators=200,        # 树的数量：200（交叉验证确定，100以下欠拟合，300以上过拟合）
    max_depth=6,             # 树深度：6（标准值，太深则过拟合，太浅则欠拟合）
    learning_rate=0.1,       # 学习率：0.1（标准值，与n_estimators权衡）
    subsample=0.8,           # 行采样：0.8（防止过拟合）
    colsample_bytree=0.8,    # 列采样：0.8（防止过拟合）
    random_state=42           # 随机种子：42（结果可复现）
)

# 训练集/测试集划分：7:3，分层抽样（保证正负样本比例一致）
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)

# 模型训练
model.fit(X_train, y_train)
```

### 5. 模型评估

```python
# 评估指标：AUC（主要指标，衡量排序能力）、准确率、召回率、F1
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, y_pred_proba)
accuracy = accuracy_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"AUC: {auc:.4f}")      # AUC=0.9942，排序能力强
print(f"准确率: {accuracy:.4f}")
print(f"召回率: {recall:.4f}")
print(f"F1: {f1:.4f}")

# 交叉验证：5折，验证模型稳定性（不同数据划分下性能波动<1.2%）
cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
print(f"5折CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
```

### 6. 特征重要性

```python
# 特征重要性：Top10特征，用于模型解释和业务洞察
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("Top10重要特征：")
print(feature_importance.head(10))
```

## 二、注释内容红线

注释中**禁止**出现以下内容：

| 类别 | 禁止内容 | 错误示例 | 正确做法 |
|------|---------|---------|---------|
| 内部讨论 | 经讨论、团队决定、agent建议 | `# 经讨论决定用XGBoost` | `# 模型：XGBoost二分类（处理非线性+特征交互）` |
| AI思考 | 首先、其次、让我、经过分析 | `# 首先清洗数据，然后特征工程` | `# 数据清洗：删除空值行（<1%）` |
| 元话语 | 本文将、以下代码、接下来 | `# 以下代码训练模型` | `# 模型训练：XGBoost，参数见配置` |
| 负向回响 | 之前用、v2修正、尝试了、失败 | `# 之前用随机森林效果不好，改用XGBoost` | `# 模型：XGBoost（AUC=0.994，优于随机森林0.978）` |
| AI协作 | agent、prompt、审查、由H5生成 | `# 由H5 agent生成` | 直接删除 |

## 三、不需要注释的位置

- 显而易见的代码（`import pandas as pd`、`for i in range(n):`）
- 简单的变量赋值（`n = 10`、`result = []`）
- 标准库函数调用（`print(...)`、`len(...)`）
- 自解释的简单调用（`df.head()`、`df.describe()`）

## 四、注释密度参考

| 代码类型 | 注释密度 |
|---------|---------|
| 数据加载和清洗 | 每个关键步骤1行注释（做什么+为什么） |
| 特征工程 | 每个特征1行注释（含义+计算方式+业务意义） |
| 模型配置 | 每个参数1行注释（含义+取值依据+影响） |
| 模型训练 | 关键步骤1行注释 |
| 模型评估 | 每个指标1行注释（含义+结果解读） |
| 特征重要性 | 1行注释（用途） |
| 工具函数 | docstring + 复杂逻辑行内注释 |

## 五、自检清单

写完代码后，逐项检查：

- [ ] 文件头有 1-3 行说明
- [ ] 数据加载和清洗有关键步骤注释
- [ ] 每个特征有注释（含义+计算方式+业务意义）
- [ ] 模型配置每个参数有注释（含义+取值依据+影响）
- [ ] 模型评估每个指标有注释（含义+结果解读）
- [ ] 随机算法固定了 seed（结果可复现）
- [ ] 注释中没有元话语、负向回响、内部讨论、AI协作痕迹
- [ ] 没有过度注释（显而易见的代码不注释）
- [ ] 数据来源有说明（文件路径+编码+行数）
- [ ] 训练集/测试集划分有说明（比例+抽样方式+随机种子）
