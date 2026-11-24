"""
最终选定变量的大表（在仓库根目录运行：python scripts/build_final_table.py）
输出 data/final/final_levels_monthly.csv   选定列的原始水平值（已统一成月度），2006-01 – 2026-10
     data/final/final_model_main.csv       主模型特征表（不含 DVF），变换 + 滞后 + split
     data/final/final_model_dvf.csv        DVF 子样本特征表（含 DVF）
     data/final/final_feature_list.csv     每个特征的来源、变换、滞后
"""
import os, numpy as np, pandas as pd
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
OUT = os.path.join(BASE, 'final'); os.makedirs(OUT, exist_ok=True)
p = pd.read_csv(os.path.join(BASE, 'furniture_nowcast_monthly_panel.csv'), index_col='month')
p.index = pd.PeriodIndex(p.index, freq='M')
# INSEE 零售业景气调查（住房设备专业零售，不含信息通信），CVS 余额；idbank 001580044
rs = pd.read_csv(os.path.join(BASE, 'raw/insee_retail_survey_home_equipment.csv'), index_col='month')
rs.index = pd.PeriodIndex(rs.index, freq='M')
p['ret_eqlog_past_sales'] = rs['ret_eqlog_past_sales'].reindex(p.index)

# 组别, 列, 变换, 发布滞后, 滞后
SEL = [
 ('Y',  'y_vol_4759_sa',                  'log',  2, []),
 ('X1', 'dvf_n_sales',                    'log',  6, [6, 9]),
 ('X1', 'dvf_median_price',               'log',  6, [6, 9]),
 ('X1', 'sitadel_logements_autorises_sa', 'log',  1, [1, 3, 6]),
 ('X1', 'house_price_index_ancien_sa',    'log',  3, [3, 6]),
 ('X2', 'gt_cat_home_furnishings',        'gt',   0, [0, 1, 3]),
 ('X2', 'gt_canapé',                      'gt',   0, [0, 1, 3]),
 ('X2', 'gt_meuble',                      'gt',   0, [0, 1, 3]),
 ('X2', 'gt_ikea',                        'gt',   0, [0, 1, 3]),
 ('X2', 'gt_conforama',                   'gt',   0, [0, 1, 3]),
 ('X3', 'unemployment_rate_sa',           'diff', 1, [1, 3]),
 ('X3', 'enq_amenagement_logement_sa',    'diff', 0, [0, 1, 3]),
 ('X3', 'hicp_furniture_relative',        'log',  1, [1]),
 ('X3', 'ret_eqlog_past_sales',           'level', 0, [0, 1, 3]),
]
def tf(s, k):
    if k == 'log': return 100 * (np.log(s) - np.log(s.shift(12)))
    if k == 'gt':  return 100 * (np.log1p(s) - np.log1p(s.shift(12)))
    if k == 'level': return s          # 调查余额本身已是「变化」的度量，直接用水平
    return s - s.shift(12)

lv = p[[c for _, c, *_ in SEL]].loc['2006-01':'2026-10']
lv.index = lv.index.astype(str); lv.index.name = 'month'
lv.round(3).to_csv(os.path.join(OUT, 'final_levels_monthly.csv'))

F, rows = pd.DataFrame(index=p.index), []
F['y_level'] = p.y_vol_4759_sa
F['y_yoy'] = tf(p.y_vol_4759_sa, 'log')
for L in (2, 3):
    F[f'y_yoy_L{L}'] = F.y_yoy.shift(L); rows.append(('Y', f'y_yoy_L{L}', 'y_vol_4759_sa', 'log_yoy', L))
for g, c, k, pub, lags in SEL[1:]:
    x = tf(p[c], k)
    for L in lags:
        nm = f'{c}__lvl_L{L}' if k == 'level' else f'{c}__yoy_L{L}'
        F[nm] = x.shift(L); rows.append((g, nm, c, k if k == 'level' else k + '_yoy', L))
covid = (F.index >= pd.Period('2020-03', 'M')) & (F.index <= pd.Period('2022-06', 'M'))
F['split'] = np.where(covid, 'covid_excluded', np.where(F.index <= pd.Period('2020-02', 'M'), 'train', 'test'))
dvf = [c for c in F if c.startswith('dvf_')]
main = F.drop(columns=dvf).dropna()
main = main[main.index >= pd.Period('2006-04', 'M')]
sub = F.dropna().copy(); n = len(sub); sub['split'] = ['train'] * int(n * .75) + ['test'] * (n - int(n * .75))
for d, fn in [(main, 'final_model_main.csv'), (sub, 'final_model_dvf.csv')]:
    d = d.copy(); d.index = d.index.astype(str); d.index.name = 'month'; d.round(4).to_csv(os.path.join(OUT, fn))
pd.DataFrame(rows, columns=['group', 'feature', 'source', 'transform', 'lag']).to_csv(os.path.join(OUT, 'final_feature_list.csv'), index=False)
print('levels', lv.shape, '| main', main.shape, main.index[0], main.index[-1], main.split.value_counts().to_dict(),
      '| dvf', sub.shape, sub.index[0], sub.index[-1], sub.split.value_counts().to_dict())
