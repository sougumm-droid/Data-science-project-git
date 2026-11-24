# 法国家具零售销量 Nowcasting

用房产交易（DVF）、Google Trends 搜索量和宏观经济数据，预测法国家具零售销量指数（同比增长率）。

## 文件夹结构

```
data/
  raw/                               原始数据（INSEE、Eurostat、ECB、DVF、Google Trends）
  furniture_nowcast_monthly_panel.csv  合并后的月度面板
  model_A_long.csv                   长样本建模表（不含 DVF），2007-01 – 2026-08
  model_B_dvf.csv                    DVF 子样本建模表，2022-10 – 2026-06
  feature_dictionary.csv             每个特征的来源、变换和滞后
  coverage.csv                       每个变量的时间覆盖范围
  final/                             最终建模表和所有模型结果（脚本生成）
notebooks/
  furniture_nowcast_demo.ipynb       演示用 notebook：数据 → 特征 → 模型 → 结果
figures/                             流程图等图片
scripts/
  prepare_features.py                数据对齐与特征构建
  build_final_table.py               生成最终建模表 data/final/final_model_*.csv
  feature_selection_experiment.py    特征筛选 + 各模型对比
  eval_metrics.py                    训练/测试的 R2、RMSE、MAPE
  explain_x_on_y.py                  OLS 解释回归（HAC 标准误）
  next_steps_dvf_live.py             DVF 子样本滚动评价 + 2026 实时预测
  data_collection/                   当初下载数据用的脚本，仅供参考
docs/
  SOP_数据对齐.md                     数据对齐的步骤说明
  README_data.md                     数据来源说明
```

## 如何运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**演示**：在 VS Code 打开 `notebooks/furniture_nowcast_demo.ipynb`，右上角选 `.venv` 内核，点 Run All。

**重新生成所有结果**（在仓库根目录，按顺序）：

```bash
python scripts/prepare_features.py
python scripts/build_final_table.py
python scripts/feature_selection_experiment.py
python scripts/eval_metrics.py
python scripts/explain_x_on_y.py
python scripts/next_steps_dvf_live.py
```

主要结果（测试期 2022-07 → 2026-08，同比 RMSE）：AR 基准 4.48，Ridge 全特征 3.91（−13%），Ridge 搜索+零售调查 3.77（−16%）。
