# 数据处理与机器学习数值合理性检查规范

本规范适用于数据清洗、特征工程、统计分析、机器学习模型（XGBoost/随机森林/ARIMA/LSTM等）。建模完成后必须执行数值合理性自检，确保"代码运行了但结果是错的"的情况被及时发现。

## 一、必须检查的项目

### 1. 数据完整性检查

```python
def check_data_completeness(df, required_columns=None):
    """检查数据完整性：无空值、无重复行、列数正确。"""
    issues = []

    # 空值检查
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            ratio = count / len(df)
            issues.append(f"列 {col} 有 {count} 个空值（{ratio:.1%}）")

    # 重复行检查
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append(f"有 {dup_count} 行重复数据")

    # 必需列检查
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            issues.append(f"缺少必需列: {', '.join(missing_cols)}")

    if issues:
        return False, f"数据不完整: {'; '.join(issues)}"
    return True, f"数据完整: {len(df)} 行, {len(df.columns)} 列, 无空值无重复"
```

### 2. 异常值检查

```python
def check_outliers(df, columns=None, method="iqr", threshold=3.0):
    """检查异常值：IQR 方法或 Z-score 方法。"""
    import numpy as np
    issues = []
    check_cols = columns or df.select_dtypes(include=[np.number]).columns

    for col in check_cols:
        if col not in df.columns:
            continue
        data = df[col].dropna()
        if len(data) < 10:
            continue

        if method == "iqr":
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = data[(data < lower) | (data > upper)]
        else:  # z-score
            z_scores = np.abs((data - data.mean()) / data.std())
            outliers = data[z_scores > threshold]

        if len(outliers) > 0:
            ratio = len(outliers) / len(data)
            if ratio > 0.05:  # 超过5%才警告
                issues.append(
                    f"列 {col} 有 {len(outliers)} 个异常值（{ratio:.1%}），"
                    f"范围 [{outliers.min():.2f}, {outliers.max():.2f}]"
                )

    if issues:
        return False, f"发现异常值: {'; '.join(issues)}"
    return True, "未发现显著异常值"
```

### 3. 预测值范围检查

```python
def check_prediction_range(y_pred, y_true=None, problem_type="regression"):
    """检查预测值范围是否合理。"""
    import numpy as np
    issues = []

    # inf/nan 检查
    if np.any(np.isinf(y_pred)) or np.any(np.isnan(y_pred)):
        inf_count = np.sum(np.isinf(y_pred))
        nan_count = np.sum(np.isnan(y_pred))
        issues.append(f"预测值中有 {inf_count} 个 inf、{nan_count} 个 nan")

    # 分类问题：预测概率范围 [0, 1]
    if problem_type == "classification" and y_pred.min() < 0:
        issues.append(f"分类预测概率小于 0: {y_pred.min()}")
    if problem_type == "classification" and y_pred.max() > 1:
        issues.append(f"分类预测概率大于 1: {y_pred.max()}")

    # 回归问题：预测值与真实值量级一致
    if y_true is not None and len(y_true) > 0:
        true_range = y_true.max() - y_true.min()
        pred_range = y_pred.max() - y_pred.min()
        if true_range > 0 and pred_range / true_range > 10:
            issues.append(
                f"预测值范围 ({pred_range:.2f}) 远大于真实值范围 ({true_range:.2f})，"
                f"可能是预测异常"
            )

    if issues:
        return False, f"预测值不合理: {'; '.join(issues)}"
    return True, f"预测值合理: 范围 [{y_pred.min():.4f}, {y_pred.max():.4f}]"
```

### 4. 评估指标合理性检查

```python
def check_metrics_reasonable(metrics, problem_type="regression"):
    """检查评估指标是否合理。"""
    issues = []

    if problem_type == "classification":
        # AUC 范围 [0, 1]
        if "auc" in metrics:
            auc = metrics["auc"]
            if auc < 0 or auc > 1:
                issues.append(f"AUC 超出 [0,1] 范围: {auc}")
            elif auc < 0.5:
                issues.append(f"AUC < 0.5 ({auc:.4f})，模型效果比随机猜测还差")
        # 准确率范围 [0, 1]
        if "accuracy" in metrics:
            acc = metrics["accuracy"]
            if acc < 0 or acc > 1:
                issues.append(f"准确率超出 [0,1] 范围: {acc}")
    elif problem_type == "regression":
        # R² 范围（理论上可以 < 0，但 < 0 说明模型很差）
        if "r2" in metrics and metrics["r2"] < 0:
            issues.append(f"R² < 0 ({metrics['r2']:.4f})，模型效果比均值预测还差")
        # RMSE 应该 > 0
        if "rmse" in metrics and metrics["rmse"] < 0:
            issues.append(f"RMSE 为负数: {metrics['rmse']}")
        # MAE 应该 <= RMSE
        if "mae" in metrics and "rmse" in metrics and metrics["mae"] > metrics["rmse"]:
            issues.append(f"MAE ({metrics['mae']:.4f}) > RMSE ({metrics['rmse']:.4f})，指标计算可能有误")

    if issues:
        return False, f"评估指标不合理: {'; '.join(issues)}"
    return True, "评估指标合理"
```

### 5. 过拟合检测

```python
def check_overfitting(train_score, test_score, threshold=0.15):
    """检测过拟合：训练集和测试集性能差距过大。"""
    gap = abs(train_score - test_score)
    if train_score > 0:  # 分类指标（越大越好）
        relative_gap = gap / (abs(train_score) + 1e-10)
        if relative_gap > threshold:
            return False, (
                f"疑似过拟合：训练集 {train_score:.4f}，测试集 {test_score:.4f}，"
                f"相对差距 {relative_gap:.1%} > {threshold:.0%}"
            )
    else:  # 回归误差指标（越小越好）
        if test_score > 0 and train_score > 0:
            ratio = test_score / train_score
            if ratio > 1 + threshold:
                return False, (
                    f"疑似过拟合：训练集误差 {train_score:.4f}，测试集误差 {test_score:.4f}，"
                    f"测试集是训练集的 {ratio:.1f} 倍"
                )
    return True, f"无明显过拟合：训练集 {train_score:.4f}，测试集 {test_score:.4f}"
```

### 6. 特征工程合理性检查

```python
def check_feature_reasonability(X, feature_names=None):
    """检查特征是否合理：无 inf/nan、无量级差异过大。"""
    import numpy as np
    issues = []

    # inf/nan 检查
    if np.any(np.isinf(X.values if hasattr(X, 'values') else X)):
        issues.append("特征矩阵中有 inf 值")
    if np.any(np.isnan(X.values if hasattr(X, 'values') else X)):
        issues.append("特征矩阵中有 nan 值")

    # 量级差异检查
    if hasattr(X, 'columns'):
        stds = X.std()
        if len(stds) > 0 and stds.max() > 0:
            ratio = stds.max() / (stds.min() + 1e-10)
            if ratio > 1e6:
                max_col = stds.idxmax()
                min_col = stds.idxmin()
                issues.append(
                    f"特征量级差异过大: {max_col} (std={stds.max():.2e}) vs "
                    f"{min_col} (std={stds.min():.2e})，比值 {ratio:.0e}，建议标准化"
                )

    if issues:
        return False, f"特征不合理: {'; '.join(issues)}"
    return True, "特征合理: 无 inf/nan，量级差异正常"
```

### 7. 时间序列稳定性检查（ARIMA/LSTM）

```python
def check_time_series_stationarity(series, threshold=0.05):
    """检查时间序列平稳性：ADF 检验。"""
    from statsmodels.tsa.stattools import adfuller
    result = adfuller(series.dropna())
    p_value = result[1]
    if p_value > threshold:
        return False, (
            f"时间序列不平稳: ADF p-value = {p_value:.4f} > {threshold}，"
            f"建议差分或使用其他方法"
        )
    return True, f"时间序列平稳: ADF p-value = {p_value:.4f} <= {threshold}"
```

## 二、自检脚本模板

```python
def numerical_sanity_check_ml(model, X_train, X_test, y_train, y_test, problem_type="regression"):
    """机器学习模型数值合理性自检。"""
    checks = []

    # 1. 数据完整性
    ok, msg = check_data_completeness(X_train)
    checks.append(("训练数据完整性", ok, msg))

    # 2. 特征合理性
    ok, msg = check_feature_reasonability(X_train)
    checks.append(("特征合理性", ok, msg))

    # 3. 预测值范围
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    ok, msg = check_prediction_range(y_pred_test, y_test, problem_type)
    checks.append(("预测值范围", ok, msg))

    # 4. 评估指标
    if problem_type == "classification":
        from sklearn.metrics import accuracy_score, roc_auc_score
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred_test),
            "auc": roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
        }
    else:
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        import numpy as np
        metrics = {
            "r2": r2_score(y_test, y_pred_test),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred_test)),
            "mae": mean_absolute_error(y_test, y_pred_test)
        }
    ok, msg = check_metrics_reasonable(metrics, problem_type)
    checks.append(("评估指标合理性", ok, msg))

    # 5. 过拟合检测
    if problem_type == "classification":
        train_score = accuracy_score(y_train, y_pred_train)
        test_score = accuracy_score(y_test, y_pred_test)
    else:
        train_score = r2_score(y_train, y_pred_train)
        test_score = r2_score(y_test, y_pred_test)
    ok, msg = check_overfitting(train_score, test_score)
    checks.append(("过拟合检测", ok, msg))

    all_passed = all(ok for _, ok, _ in checks)
    return all_passed, checks
```

## 三、常见问题与处理

| 问题 | 可能原因 | 处理方法 |
|------|---------|---------|
| 数据有空值 | 原始数据缺失、合并错误 | 删除/填充空值、检查数据合并逻辑 |
| 预测值 inf/nan | 特征中有 inf/nan、模型溢出 | 检查特征、增加正则化、调整学习率 |
| AUC < 0.5 | 标签反了、特征无预测能力 | 检查标签、重新选择特征 |
| R² < 0 | 模型比均值还差 | 重新选择特征、调整模型、检查数据 |
| 过拟合 | 模型太复杂、训练数据太少 | 增加正则化、增加数据、简化模型、早停 |
| 特征量级差异过大 | 未标准化 | 标准化/归一化特征 |
| 时间序列不平稳 | 有趋势/季节性 | 差分、去趋势、使用 Prophet 等方法 |

## 四、自检清单

建模完成后，逐项检查：

- [ ] 训练/测试数据完整（无空值、无重复、列数正确）
- [ ] 特征矩阵无 inf/nan
- [ ] 特征量级差异正常（< 1e6 倍，否则需标准化）
- [ ] 预测值无 inf/nan，范围合理
- [ ] 分类预测概率在 [0, 1] 范围内
- [ ] 评估指标合理（AUC 在 [0,1]、准确率在 [0,1]、R² 不太差）
- [ ] 无明显过拟合（训练集和测试集性能差距 < 15%）
- [ ] 时间序列平稳（如适用）
- [ ] 异常值已处理（< 5%）
- [ ] 随机种子已固定，结果可复现
- [ ] 自检结果写入 run_manifest
