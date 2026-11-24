"""
第三步：特征筛选 + 对照实验（运行：python scripts/feature_selection_experiment.py）
输入 data/final/final_model_main.csv；输出 data/final/fs_ranking.csv、data/final/fs_results.csv
特征打分只用训练集（2006-04 – 2020-02），测试集 2022-07 – 2026-08
"""
import os, numpy as np, pandas as pd
from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
B = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
m = pd.read_csv(os.path.join(B, 'final/final_model_main.csv'), index_col=0)
p = pd.read_csv(os.path.join(B, 'furniture_nowcast_monthly_panel.csv'), index_col=0)
m = m[m.split != 'covid_excluded']
idx = pd.PeriodIndex(m.index, freq='M')
m['l12'] = [p.y_vol_4759_sa.get(str(t - 12)) for t in idx]
tr, te = m.split == 'train', m.split == 'test'
AR = ['y_yoy_L2', 'y_yoy_L3']
X_all = [c for c in m if '__yoy_L' in c or '__lvl_L' in c]   # 外部特征
K = 10
pcc = m.loc[tr, X_all].corrwith(m.loc[tr, 'y_yoy']).abs().sort_values(ascending=False)
rf0 = RandomForestRegressor(500, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(m.loc[tr, AR + X_all], m.loc[tr, 'y_yoy'])
gini = pd.Series(rf0.feature_importances_, AR + X_all).drop(AR).sort_values(ascending=False)
pd.DataFrame({'PCC_abs': pcc.round(3), 'RF_importance': gini.round(3)}).sort_values('PCC_abs', ascending=False).to_csv(os.path.join(B, 'final/fs_ranking.csv'))
sets = {'全部特征': X_all, f'PCC 前 {K}': list(pcc.index[:K]), f'RF 前 {K}': list(gini.index[:K])}
models = {
 'ARX (Ridge)': lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 40))),
 'ARX (OLS)':   lambda: make_pipeline(StandardScaler(), LinearRegression()),
 'Random Forest': lambda: RandomForestRegressor(500, min_samples_leaf=5, random_state=0, n_jobs=-1),
 'Gradient Boosting': lambda: GradientBoostingRegressor(max_depth=2, learning_rate=0.05, n_estimators=300, subsample=0.8, random_state=0),
}
def ev(model, cols):
    model.fit(m.loc[tr, cols], m.loc[tr, 'y_yoy'])
    pa, pb = model.predict(m.loc[tr, cols]), model.predict(m.loc[te, cols])
    lv = m.loc[te, 'l12'] * np.exp(pb / 100)
    return dict(train_R2=r2_score(m.loc[tr, 'y_yoy'], pa), test_R2=r2_score(m.loc[te, 'y_yoy'], pb),
                test_RMSE=np.sqrt(mean_squared_error(m.loc[te, 'y_yoy'], pb)),
                level_R2=r2_score(m.loc[te, 'y_level'], lv), level_MAPE=100 * mean_absolute_percentage_error(m.loc[te, 'y_level'], lv))
rows = [dict(model='Baseline: AR only', features='Y 自身滞后', n=2, **ev(LinearRegression(), AR))]
for mn, mk in models.items():
    for sn, cols in sets.items():
        rows.append(dict(model=mn, features=sn, n=len(cols) + 2, **ev(mk(), AR + cols)))
R = pd.DataFrame(rows); R['RMSE_vs_AR_%'] = 100 * (R.test_RMSE / R.test_RMSE[0] - 1)
R.round(3).to_csv(os.path.join(B, 'final/fs_results.csv'), index=False)
print(pd.DataFrame({'PCC': pcc.round(2).head(K).reset_index().values.tolist(), 'RF': gini.round(3).head(K).reset_index().values.tolist()}).to_string())
print(R.round(2).to_string())
