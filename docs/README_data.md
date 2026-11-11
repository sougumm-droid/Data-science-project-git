# 法国家具需求 Nowcasting 数据包

下载日期：2026-11-10。所有数据都来自官方公开源，已对齐成月度（`YYYY-MM`）。

## 文件

| 文件 | 内容 |
|---|---|
| `furniture_nowcast_monthly_panel.csv` | **主表**：月度宽表，2004-01 至 2026-10，每列一个变量（目标 Y 在最前面） |
| `coverage.csv` | 每个变量的起止月份和观测数 |
| `raw/_series_catalog.csv` | 每个序列的来源、序列 ID、原始频率、标题和网页链接 |
| `raw/dvf_monthly_national.csv` | DVF 按月汇总（全国） |
| `raw/dvf_monthly_by_departement.csv` | DVF 按月 × 省汇总（成交笔数、m² 中位价），可用于做地区面板或人口密度交互 |
| `raw/google_trends_monthly_FR.csv` | Google Trends 月度检索指数（法国） |
| `raw/macro_and_target_monthly_raw.csv` | INSEE / Eurostat / ECB / FRED 原始月度序列 |
| `raw/eurostat_rdb_quarterly.csv`, `raw/insee_house_price_index_quarterly.csv`, `raw/eurostat_population_annual.csv` | 原始季度/年度序列（主表里已转月度） |

## 变量说明（主表）

### 目标变量 Y（INSEE，NAF 47.59「Commerce de détail de meubles, appareils d'éclairage et autres articles de ménage」）
| 列 | 含义 | 时间范围 |
|---|---|---|
| `y_vol_4759_sa` | **推荐 Y**：销量指数（volume des ventes），季调+工作日调整，2021=100。INSEE idbank 010770085 | 2005-01 → 2026-08 |
| `y_vol_4759_nsa` | 同上，未季调（如果想自己建季节特征/假日效应用这个）。010770084 | 2005-01 → 2026-08 |
| `y_ca_4759_sa` / `_nsa` | 营业额指数（名义，含价格）。010770861 / 010770477 | 2004-01 → 2026-08 |
| `y_ca_4759A_meubles_nsa` | **只有家具**（47.59A），营业额，未季调。010770863 | 2004-01 → 2026-08 |
| `vol_475_sa`, `eu_vol_G475_sa` | 更宽的 47.5「家居设备」零售销量（INSEE / Eurostat sts_trtu_m），可做稳健性对照 | 2005-01 → |
| `eu_vol_G47_sa` | 整体零售销量（对照基准） | 2004-01 → |

> Eurostat 的 `sts_trtu_m` 没有 47.59 这一层（最细只到 G475），所以家具专属的 Y 要用 INSEE。

### 房产 X₁
| 列 | 含义 | 来源 | 时间范围 |
|---|---|---|---|
| `dvf_n_sales` | 当月住宅成交笔数（含至少一套 Maison/Appartement 的 Vente + VEFA，按 id_mutation 去重） | DVF（geo-dvf，data.gouv.fr） | 2021-01 → 2025-12 |
| `dvf_n_maison` / `dvf_n_appart` / `dvf_n_vefa` | 分类型成交笔数（VEFA = 期房） | DVF | 同上 |
| `dvf_median_price`, `dvf_median_price_m2`(+`_maison`/`_appart`) | 单套住宅交易的中位总价、中位 €/m²（剔除 €/m² 不在 300–30000 的异常值） | DVF | 同上 |
| `dvf_total_value_meur` | 当月住宅成交总额（百万欧元） | DVF | 同上 |
| `sitadel_logements_commences_sa` / `_autorises_sa` | 新建住宅开工 / 获批数，季调 | INSEE（Sitadel） | 2004 → 2026-09 |
| `sitadel_*_cumul12m` | 同上 12 个月滚动累计（未季调） | INSEE | 同上 |
| `house_price_index_ancien_sa` | 二手房价格指数（Notaires-INSEE，季度值复制到当季各月） | INSEE 010567059 | → 2026-06 |
| `mortgage_rate_new_business` | 新发放住房贷款利率 % | ECB MIR | → 2026-09 |
| `enq_intention_achat_logement_sa` | 家庭「一年内买房意向」余额 | INSEE 家庭景气调查 | → 2026-10 |

### 搜索意向 X₂（Google Trends，法国，`timeframe='all'` 直接返回**月度**）
`gt_meuble`, `gt_canapé`, `gt_matelas`, `gt_déménagement`, `gt_ikea`, `gt_maisons_du_monde`, `gt_conforama`, `gt_crédit_immobilier`, `gt_cat_home_furnishings`（Google 类别 270「家居用品」）：每个词单独归一化到 0–100。
`gtjoint_*`：5 个词放在同一次请求里，彼此可比较大小。2004-01 起。

### 宏观 X₃
| 列 | 含义 | 来源 |
|---|---|---|
| `rdb_households_meur_monthly` | 家庭可支配收入（名义，季度值 ÷3 摊到月） | Eurostat nasq_10_nf_tr |
| `rdb_real_meur_monthly` | 同上按 HICP 平减 | 计算 |
| `rdb_per_capita_eur_monthly` | 人均可支配收入 | 计算 |
| `population`, `pop_density_per_km2` | 1 月 1 日人口，月度线性插值；密度 = 人口 / 632 734 km² | Eurostat demo_gind |
| `hicp_furniture`, `hicp_total`, `hicp_furniture_relative` | 家具 HICP（COICOP 05.1.1）、总体 HICP、家具相对价格 | Eurostat prc_hicp_minr |
| `conf_menages_sa` | 家庭信心综合指标 | INSEE |
| `enq_achats_importants_sa`, `enq_achats_equipement_sa`, `enq_amenagement_logement_sa` | 「现在是否适合大额消费」「计划购买家电家具」「计划装修住房」的调查余额 | INSEE |
| `conso_equip_logement_vol_sa`, `conso_biens_durables_vol_sa` | 家庭月度「住房设备」「耐用品」消费量 | INSEE |
| `unemployment_rate_sa` | 失业率 | Eurostat |
| `oat10y_rate` | 10 年期国债收益率 | FRED IRLTLT01FRM156N |

## 主要缺口与处理建议

0. **Google Trends 已下载**（云端被限流约 30 分钟后重试成功）。`scripts/get_google_trends_local.py` 留作以后在本地更新数据用。注意 2026-11 是不完整月份（isPartial）。
1. **DVF 只有 2021-01 → 2025-12（60 个月）**。data.gouv 只公开最近 5 年，更早的年份已下架。而 Y 从 2005 年开始。两种做法：
   - 主模型用 2005–2026 的长序列，房产特征用 Sitadel 开工量、房贷利率、二手房价格指数、买房意向；DVF 只在 2021–2025 子样本里做「加入 DVF 后是否提升」的对比实验。
   - 补长期成交量：IGEDD（原 CGEDD，Jacques Friggit）发布了 2000 年以来二手房 12 个月滚动成交量，文件在 https://www.cgedd.fr/nombre-vente-maison-appartement-ancien.xls 。这个站点不允许自动抓取，需要你在浏览器里手动下载。
2. **DVF 不含阿尔萨斯–摩泽尔（57、67、68 省）和马约特**，这是 DVF 本身的覆盖范围。
3. **Google Trends 原生月度**：对 2004 至今的全时段请求，Google 直接给月度值，所以不需要「周度 → 4 周滑动平均 → 月度」这一步。如果报告里想展示频率对齐的处理，可以用 5 年窗口拉周度数据再聚合，作为对照。
4. **人口密度在全国层面几乎是常数**（20 年里只变了约 8%），对全国月度模型几乎没有解释力。想用它的话，建议用 `dvf_monthly_by_departement.csv` 做分省面板。
5. **频率对齐**：季度可支配收入是 ÷3 摊到月；房价指数是同一季度各月取同一值；人口是年度线性插值。这些都可以写进报告的「数据困难说明」。
6. **发布滞后**：Y 最新到 2026-08，调查数据到 2026-10，这正好可以用来说明 nowcasting 的意义（用更早发布的 X 预测还没发布的 Y）。

## 初步检查
在 2021–2025 子样本里，`y_vol_4759_sa` 和 `dvf_n_sales` 的相关系数：同期 0.45，滞后 3 个月 0.51，**滞后 6 个月 0.68**。这和「先买房，后买家具」的假设一致，但两个序列在这段时间都在下降，所以这个相关性有一部分来自共同趋势，建模前要先做差分或去趋势。

## 复现
下载脚本在 `scripts/`。INSEE 序列可以按 idbank 拉取：`https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/<idbank>`；Eurostat：`https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/<dataset>/<key>?format=SDMX-CSV`。
