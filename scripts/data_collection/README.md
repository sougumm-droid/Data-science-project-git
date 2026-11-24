# 数据采集脚本

这些脚本是当初下载原始数据时用的，记录数据来源和处理过程。路径都已经改成仓库里的 `data/raw/`。
处理好的原始数据已经在 `data/raw/` 里，**平时不需要运行这些脚本**，直接用 `scripts/prepare_features.py` 和后面的建模脚本即可。

| 脚本 | 作用 | 需要联网 |
|---|---|---|
| `build_macro.py` + `insee.py` | 下载 INSEE、Eurostat、ECB、FRED 的宏观和目标数据 → `data/raw/` | 是 |
| `trends2.py` / `get_google_trends_local.py` | 下载 Google Trends（需要 `pip install pytrends`） | 是 |
| `dvf_agg.py` | 把 DVF 逐笔交易汇总成月度（先把 `full_YYYY.csv.gz` 放到 `data/raw/downloads/dvf/`） | 否 |
| `merge.py` | 合并所有原始数据 → `data/furniture_nowcast_monthly_panel.csv` | 否 |

下载的临时文件放在 `data/raw/downloads/`，这个文件夹不会提交到 GitHub。
