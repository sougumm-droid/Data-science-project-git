# 数据对齐 SOP：法国家具需求 Nowcasting

这份 SOP 从已经下载好的数据出发，一步步做到「可以直接喂给 OLS / RF / XGBoost / ARX 的建模表」。
第 1–2 步已经替你做完了，从第 3 步开始的处理都写在 `scripts/prepare_features.py` 里，运行一次就能得到最终的建模表。每一步都写了「做什么、为什么、写进报告的哪里」。

---

## 第 0 步：准备环境

```bash
pip install pandas numpy scikit-learn statsmodels xgboost matplotlib
cd Data-science-project-git   # 进入仓库根目录
python scripts/prepare_features.py
```

运行后会生成三个文件：

| 文件 | 用途 |
|---|---|
| `model_A_long.csv` | 长样本，2007-01 – 2026-08，236 行，**不含 DVF**。用于主模型。 |
| `model_B_dvf.csv` | DVF 子样本，2022-10 – 2026-06，45 行，**含 DVF**。用于「加入 DVF 是否提升」的对比实验。 |
| `feature_dictionary.csv` | 每个特征来自哪个原始变量、做了什么变换、滞后几期。可以直接放进报告附录。 |

---

## 第 1 步：统一时间索引（已完成）

**做什么：** 所有序列都转成 `YYYY-MM` 的月度索引，合并到一张宽表 `furniture_nowcast_monthly_panel.csv`，范围是 2004-01 – 2026-10。

**为什么：** 不同来源的日期格式不一样（INSEE 是 `2024-03`，Eurostat 季度是 `2024-Q1`，Google Trends 是 `2024-03-01`），必须先统一成同一个索引才能合并。

**代码里怎么写：**
```python
panel.index = pd.PeriodIndex(panel.index, freq='M')
```

---

## 第 2 步：统一频率（已完成）

不同频率的变量用不同规则转成月度。**规则取决于变量是「流量」还是「存量/价格」**，这一点要写进报告。

| 原始频率 | 变量 | 转换规则 | 理由 |
|---|---|---|---|
| 逐笔交易 | DVF | 按 `date_mutation` 归到月份，统计笔数和 €/m² 中位数 | 交易是事件，按月计数 |
| 季度 | 家庭可支配收入 | **季度值 ÷ 3**，分配给当季每个月 | 收入是流量，总量要守恒 |
| 季度 | 二手房价格指数 | **季度值原样复制**给当季每个月 | 价格指数是水平值，不能除 |
| 年度 | 人口 | 1 月 1 日数值之间**线性插值** | 人口变化平滑 |
| 月度 | Google Trends | 不用转换（`timeframe='all'` 直接返回月度值） | — |

> **如果你想在报告里展示「周度 → 月度」的处理**（你提纲里的 4 周滑动平均）：用 pytrends 拉 5 年窗口（`timeframe='today 5-y'`）会得到周度数据，然后：
> ```python
> weekly.rolling(4).mean().resample('MS').mean()
> ```
> 再和我给的原生月度数据画在一起对比，这可以作为「数据困难说明」的一个小节。

**写进报告：** 第 3 章 Datasets and Preprocessing 的「频率对齐」段落，可以直接用上表。

---

## 第 3 步：处理「发布滞后」（这是 nowcasting 的核心）

**做什么：** 每个变量的发布时间不一样。站在 t 月底，你能拿到的数据只到 t − pub 月。**特征的滞后期不能小于它的发布滞后**，否则模型在训练时等于「偷看了未来」。

| 变量 | 发布滞后 pub（月） | 允许的滞后 |
|---|---|---|
| Google Trends、家庭调查、国债利率 | 0 | t, t−1, t−3 … |
| Sitadel 开工、房贷利率、失业率、家具 HICP | 1 | t−1, t−3, t−6 |
| 二手房价格指数、可支配收入（季度） | 3 | t−3, t−6 |
| **DVF** | **6**（每年 4 月和 10 月各更新一次） | **t−6, t−9** |
| **Y 本身**（INSEE 零售指数） | 约 2 | t−2, t−3, t−12 |

**为什么：** 这正是 nowcasting 的价值所在。Y 要 2 个月后才发布，而 Google Trends 和调查数据当月就有，所以可以用「快变量」提前估计「慢变量」。

**代码里怎么写：** 脚本里的 `CFG` 字典给每个变量设了 `pub`，小于 `pub` 的滞后会被自动跳过：
```python
'dvf_n_sales': dict(kind='log', pub=6, lags=[6, 9]),
'gt_canapé':   dict(kind='gt',  pub=0, lags=[0, 1, 3]),
```

**注意：** 你提纲里写的 DVF「t−1, t−3, t−6」在真实 nowcasting 场景下只有 t−6 能用。建议在报告里写清楚这一点，这本身就是一个亮点。

---

## 第 4 步：平稳化变换

**做什么：** 把所有变量变成「同比变化」，按变量类型选择不同的变换方式。

| 类型 | 变量 | 变换 |
|---|---|---|
| 指数 / 数量 / 金额 | Y、DVF 笔数和价格、Sitadel、房价、收入、HICP | `100 × (log x_t − log x_{t−12})`，即同比增长率 % |
| 利率 / 调查余额 / 失业率 | 房贷利率、国债利率、家庭信心、调查余额 | `x_t − x_{t−12}`，即同比变化（百分点） |
| Google Trends（0–100，可能有 0） | gt_* | `100 × (log(1+x_t) − log(1+x_{t−12}))` |

**为什么：**
1. 2021–2026 年 Y 和 DVF 都在下降。直接用水平值做回归会出现「伪相关」（两个都有趋势的序列看起来高度相关），用同比变化可以去掉共同趋势。
2. 同比变换同时消除了季节性，不需要再单独做季节调整（11 月黑五、1 月和 7 月打折季的影响基本被抵消）。
3. 树模型（RF / XGBoost）无法外推趋势，测试期的水平值一旦超出训练范围就会预测失败，用增长率可以避免这个问题。

**检验（建议放进报告附录）：** 对变换后的 Y 和主要特征做 ADF 单位根检验：
```python
from statsmodels.tsa.stattools import adfuller
p = adfuller(df['y_yoy'].dropna())[1]   # p < 0.05 说明平稳
```

---

## 第 5 步：构建滞后特征

**做什么：** 每个变换后的变量按第 3 步允许的滞后生成多列，命名规则是 `变量名__yoy_L滞后期`，例如 `dvf_n_sales__yoy_L6`、`gt_canapé__yoy_L1`。

另外还加了：
- `y_yoy_L2`, `y_yoy_L3`, `y_yoy_L12`：Y 自身的滞后，ARX 模型用（OLS / RF 可以加也可以不加，两种都跑一遍做对比）。
- `covid_closure`：非必需商店关闭的月份（2020-03/04/05、2020-11、2021-04）取 1。不加这个变量，新冠期间的暴跌暴涨会主导整个回归。
- `month_of_year`：月份，只在用未季调的 Y 时需要。

**写进报告：** 第 3 章特征构建表格，「预处理与特征构建」一栏可以写「log 同比 + t−6/t−9 滞后（受发布时间约束）」。

---

## 第 6 步：缺失值处理

**做什么：** 构建完滞后项以后，**直接删掉有缺失的行**（`dropna`），不做中位数填充。

**为什么不用中位数填充：**
- 这里的缺失**不是随机的**，而是来自「序列还没开始」（例如 DVF 2021 年以前没有数据）或「滞后/同比造成的开头空行」。用中位数填进去等于凭空编造了一段历史。
- 用全样本中位数填充还会把测试期的信息漏进训练期（数据泄漏）。

**唯一的例外：实时 nowcast 的最后几个月（ragged edge）。** 比如要预测 2026-09，季度收入只到 2026-06。这时可以用最近一个可得值向前填充（`ffill(limit=3)`），但**只在做最终预测时用**，训练时不要用。

**写进报告：** 你提纲里写的「缺失值中位数填充」建议改成上面的说法，并说明原因。审稿人/老师很可能会问这一点。

---

## 第 7 步：裁剪时间范围（两个样本）

| 样本 | 范围 | 行数 | 特征数 | 用途 |
|---|---|---|---|---|
| **A 长样本** | 2007-01 – 2026-08 | 236 | 55（不含 DVF） | 主模型：OLS、RF、XGBoost、ARX、LSTM 的比较 |
| **B DVF 样本** | 2022-10 – 2026-06 | 45 | 59（含 DVF） | 对比实验：同一时间段内，「加 DVF」和「不加 DVF」的模型谁更准 |

为什么样本 A 从 2007 年开始：Y 从 2005-01 开始，同比变换要用掉 12 个月，Y 的 12 期滞后又要再用掉 12 个月。
为什么样本 B 这么短：DVF 只有 2021–2025 年，同比变换要用掉 12 个月，6 个月的发布滞后又往后推了 6 个月。

**样本 B 只有 45 行，特征却有 59 个，所以不能把所有特征都放进去。** 建议：
- 只选 3–6 个特征（例如 `y_yoy_L12` + 2 个 Google Trends + 1–2 个 DVF），用 OLS 或 Ridge 回归。
- 用「加 DVF」和「不加 DVF」两个模型做对比，看样本外 RMSE 的差别，不要追求 R² 本身。
- 在报告里明确写出「样本 B 太小，结论只能作为参考」，这是诚实的局限性说明。

---

## 第 8 步：训练集 / 测试集切分（按时间，不能打乱）

**做什么：**
- 样本 A：训练集 2007-01 – 2021-12（180 行），测试集 2022-01 – 2026-08（56 行）。文件里的 `split` 列已经标好。
- 样本 B：前 75% 作为训练集（33 行），后 25% 作为测试集（12 行）。

**为什么：** 时间序列不能用随机的 `train_test_split`，否则模型会用 2025 年的数据预测 2023 年。调参做交叉验证时用：
```python
from sklearn.model_selection import TimeSeriesSplit
cv = TimeSeriesSplit(n_splits=5)
```

**标准化（Standard scaling）在这一步做**，而且**只能用训练集拟合**：
```python
from sklearn.preprocessing import StandardScaler
sc = StandardScaler().fit(X_train)
X_train_s, X_test_s = sc.transform(X_train), sc.transform(X_test)
```

---

## 第 9 步：读入建模表，开始建模

```python
import pandas as pd
df = pd.read_csv('model_A_long.csv', index_col='month')
y = df['y_yoy']
X = df.drop(columns=['y_level', 'y_yoy', 'y_mom', 'split', 'month_of_year'])
tr, te = df['split'] == 'train', df['split'] == 'test'
X_train, X_test, y_train, y_test = X[tr], X[te], y[tr], y[te]
```

**特征筛选（对应你提纲里的 PCC vs RF Gini）：只在训练集上算。**
```python
pcc = X_train.corrwith(y_train).abs().sort_values(ascending=False)
from sklearn.ensemble import RandomForestRegressor
rf = RandomForestRegressor(500, random_state=0).fit(X_train, y_train)
gini = pd.Series(rf.feature_importances_, X_train.columns).sort_values(ascending=False)
```

**脚本跑出来的初步结果**（样本 A 训练集，与 `y_yoy` 的 |PCC| 前几名）：
`y_yoy_L12` 0.64，`gt_meuble` 滞后 1 期 0.50，`gt_matelas` 滞后 1 期 0.47，「是否适合大额消费」调查 0.45，`gt_canapé` 滞后 1 期 0.43。也就是说，搜索数据的信号比宏观变量强，可以作为报告结论的一个方向。
在样本 B 中，`dvf_n_sales` 滞后 9 期 0.40，`dvf_median_price_m2` 滞后 6 期 0.52。

**最后汇报的指标：** 测试集上的 R²、RMSE、MAPE。注意 MAPE 不能直接用在 `y_yoy` 上，因为它接近 0 时会爆炸。要么把预测的同比增长率还原回指数水平再算 MAPE：
```python
y_level_pred = df['y_level'].shift(12)[te] * np.exp(y_pred / 100)
```
要么只报 R² 和 RMSE。

---

## 第 10 步：检查清单（交报告前逐条确认）

- [ ] 每个特征的滞后期 ≥ 它的发布滞后（看 `feature_dictionary.csv` 的 `lag` ≥ `pub_lag`）
- [ ] 标准化器、特征筛选、超参数都只用了训练集
- [ ] 测试集在时间上整体排在训练集之后
- [ ] 报告里写了频率转换规则（第 2 步的表）
- [ ] 报告里说明了 DVF 只有 5 年，并且样本 B 的结论只能作为参考
- [ ] 画了测试期「真实 vs 预测」折线图，用指数水平画，比增长率更直观

---

## 想改设置时改哪里

所有设置都在 `scripts/prepare_features.py` 顶部：
- 换目标变量（比如用只含家具的 47.59A）：改 `Y_COL`
- 增删特征或改滞后期：改 `CFG` 字典
- 改测试集起点：改 `'2021-12'` 那一行
- 改完重新运行 `python scripts/prepare_features.py` 即可。
