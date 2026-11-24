"""用 X 解释 Y：训练期（2006-04 – 2020-02）OLS，每个变量取一个滞后，HAC 稳健标准误（运行：python scripts/explain_x_on_y.py）"""
import os, pandas as pd, statsmodels.api as sm
B = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
m = pd.read_csv(os.path.join(B, 'final/final_model_main.csv'), index_col=0); m = m[m.split == 'train']
sel = ['y_yoy_L2', 'gt_cat_home_furnishings__yoy_L0', 'gt_canapé__yoy_L0', 'unemployment_rate_sa__yoy_L1',
       'enq_amenagement_logement_sa__yoy_L3', 'sitadel_logements_autorises_sa__yoy_L3',
       'house_price_index_ancien_sa__yoy_L3', 'hicp_furniture_relative__yoy_L1']
o = sm.OLS(m.y_yoy, sm.add_constant(m[sel])).fit(cov_type='HAC', cov_kwds={'maxlags': 12})
pd.DataFrame({'coef': o.params, 'std_err': o.bse, 'p_value': o.pvalues}).round(4).to_csv(os.path.join(B, 'final/explain_ols.csv'))
print(o.summary())
