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
scripts/
  prepare_features.py                数据对齐与特征构建（主要运行这个）
  data_collection/                   当初下载数据用的脚本，仅供参考
docs/
  SOP_数据对齐.md                     数据对齐的步骤说明
  README_data.md                     数据来源说明
```

## 如何运行

```bash
pip install -r requirements.txt
python scripts/prepare_features.py
```

运行后会重新生成 `data/model_A_long.csv`、`data/model_B_dvf.csv` 和 `data/feature_dictionary.csv`。
