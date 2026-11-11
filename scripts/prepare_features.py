"""
数据对齐与特征构建（对应 SOP 第 3–8 步）
运行：python scripts/prepare_features.py   （在仓库根目录下运行）
输入输出都在 data/ 文件夹里
输入：furniture_nowcast_monthly_panel.csv
输出：model_A_long.csv          长样本（不含 DVF），2007-01 – 2026-08
      model_B_dvf.csv           DVF 子样本（含 DVF），2022-10 – 2026-06
      feature_dictionary.csv    每个特征的来源变量、变换、滞后
"""
import numpy as np, pandas as pd, os

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
panel = pd.read_csv(os.path.join(BASE, 'furniture_nowcast_monthly_panel.csv'), index_col='month')
panel.index = pd.PeriodIndex(panel.index, freq='M')          # 统一成月度 PeriodIndex
panel = panel.sort_index()

# ---------------------------------------------------------------- 1. 目标变量
Y_COL = 'y_vol_4759_sa'                  # 家具零售销量指数（季调）
y_log = np.log(panel[Y_COL])
target = pd.DataFrame(index=panel.index)
target['y_level'] = panel[Y_COL]
target['y_yoy'] = 100 * (y_log - y_log.shift(12))          # 同比增长率 %（主要建模目标）
target['y_mom'] = 100 * (y_log - y_log.shift(1))           # 环比增长率 %（备选）

# ---------------------------------------------------------------- 2. 变量配置
# kind:  'log'  -> 指数/数量/金额，做 log 同比 (%)
#        'diff' -> 利率/调查余额/失业率，做 12 个月差分（百分点）
#        'gt'   -> Google Trends 0–100，做 log(1+x) 同比
# pub:   发布滞后（月）：在 t 月底能拿到的最新数据是 t-pub 月的
# lags:  候选滞后；小于 pub 的会被自动去掉（避免用到当时还没发布的数据）
CFG = {
    # 房产
    'dvf_n_sales':                    dict(kind='log',  pub=6, lags=[6, 9]),
    'dvf_median_price_m2':            dict(kind='log',  pub=6, lags=[6, 9]),
    'sitadel_logements_commences_sa': dict(kind='log',  pub=1, lags=[1, 3, 6]),
    'sitadel_logements_autorises_sa': dict(kind='log',  pub=1, lags=[1, 3, 6]),
    'house_price_index_ancien_sa':    dict(kind='log',  pub=3, lags=[3, 6]),
    'mortgage_rate_new_business':     dict(kind='diff', pub=1, lags=[1, 3, 6]),
    'enq_intention_achat_logement_sa':dict(kind='diff', pub=0, lags=[0, 3, 6]),
    # 搜索意向
    'gt_meuble':                      dict(kind='gt',   pub=0, lags=[0, 1, 3]),
    'gt_canapé':                      dict(kind='gt',   pub=0, lags=[0, 1, 3]),
    'gt_matelas':                     dict(kind='gt',   pub=0, lags=[0, 1, 3]),
    'gt_déménagement':                dict(kind='gt',   pub=0, lags=[0, 3, 6]),
    'gt_ikea':                        dict(kind='gt',   pub=0, lags=[0, 1, 3]),
    'gt_cat_home_furnishings':        dict(kind='gt',   pub=0, lags=[0, 1, 3]),
    'gt_crédit_immobilier':           dict(kind='gt',   pub=0, lags=[0, 3, 6]),
    # 宏观
    'rdb_real_meur_monthly':          dict(kind='log',  pub=3, lags=[3]),
    'hicp_furniture_relative':        dict(kind='log',  pub=1, lags=[1]),
    'conf_menages_sa':                dict(kind='diff', pub=0, lags=[0, 1, 3]),
    'enq_achats_importants_sa':       dict(kind='diff', pub=0, lags=[0, 1, 3]),
    'enq_amenagement_logement_sa':    dict(kind='diff', pub=0, lags=[0, 1, 3]),
    'unemployment_rate_sa':           dict(kind='diff', pub=1, lags=[1, 3]),
    'oat10y_rate':                    dict(kind='diff', pub=0, lags=[0, 3]),
}
Y_AR_LAGS = [2, 3, 12]       # Y 自身滞后（ARX 用）；Y 约在 t+2 月才发布，所以从 2 开始

# ---------------------------------------------------------------- 3. 平稳化变换
def transform(s, kind):
    if kind == 'log':  return 100 * (np.log(s) - np.log(s.shift(12)))
    if kind == 'gt':   return 100 * (np.log1p(s) - np.log1p(s.shift(12)))
    if kind == 'diff': return s - s.shift(12)
    raise ValueError(kind)

# ---------------------------------------------------------------- 4. 滞后项
feats, rows = {}, []
for col, c in CFG.items():
    x = transform(panel[col], c['kind'])
    for L in c['lags']:
        if L < c['pub']:
            continue
        name = f'{col}__yoy_L{L}'
        feats[name] = x.shift(L)
        rows.append(dict(feature=name, source=col, transform=c['kind'] + '_yoy', lag=L, pub_lag=c['pub']))
for L in Y_AR_LAGS:
    feats[f'y_yoy_L{L}'] = target['y_yoy'].shift(L)
    rows.append(dict(feature=f'y_yoy_L{L}', source=Y_COL, transform='log_yoy', lag=L, pub_lag=2))
X = pd.DataFrame(feats)

# 事件虚拟变量：新冠封控期间非必需商店关闭
covid = ['2020-03', '2020-04', '2020-05', '2020-11', '2021-04']
X['covid_closure'] = X.index.astype(str).isin(covid).astype(int)
rows.append(dict(feature='covid_closure', source='manual', transform='dummy', lag=0, pub_lag=0))
# 季节：用同比后基本消除，这里保留月份供 NSA 模型或画图用
X['month_of_year'] = X.index.month
rows.append(dict(feature='month_of_year', source='calendar', transform='int', lag=0, pub_lag=0))

data = target.join(X)

# ---------------------------------------------------------------- 5. 两个样本 + 缺失值处理
dvf_cols = [c for c in X if c.startswith('dvf_')]
non_dvf = [c for c in X if c not in dvf_cols]

A = data[['y_level', 'y_yoy', 'y_mom'] + non_dvf].dropna()          # 长样本：去掉 DVF
B = data[['y_level', 'y_yoy', 'y_mom'] + list(X.columns)].dropna()   # 短样本：含 DVF

# ---------------------------------------------------------------- 6. 训练/测试切分标记（按时间，不打乱）
A['split'] = np.where(A.index <= pd.Period('2021-12', 'M'), 'train', 'test')
nB = len(B); B['split'] = ['train'] * int(nB * 0.75) + ['test'] * (nB - int(nB * 0.75))

for df, fn in [(A, 'model_A_long.csv'), (B, 'model_B_dvf.csv')]:
    df.index = df.index.astype(str); df.index.name = 'month'
    df.to_csv(os.path.join(BASE, fn))
pd.DataFrame(rows).to_csv(os.path.join(BASE, 'feature_dictionary.csv'), index=False)

print(f'model_A_long.csv : {A.index[0]} → {A.index[-1]}, {len(A)} 行, {len(non_dvf)} 个特征, '
      f'train {sum(A.split=="train")} / test {sum(A.split=="test")}')
print(f'model_B_dvf.csv  : {B.index[0]} → {B.index[-1]}, {len(B)} 行, {X.shape[1]} 个特征, '
      f'train {sum(B.split=="train")} / test {sum(B.split=="test")}')

# 快速检查：训练集里与 y_yoy 相关性最高的 10 个特征（PCC）
tr = A[A.split == 'train'].drop(columns=['y_level', 'y_mom', 'split'])
print('\n长样本训练集 |PCC| 前 10：')
print(tr.corr()['y_yoy'].drop('y_yoy').abs().sort_values(ascending=False).head(10).round(2).to_string())
