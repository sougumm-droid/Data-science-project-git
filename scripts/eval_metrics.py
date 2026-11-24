"""评价：训练集 vs 测试集的 R2 / RMSE / MAPE（同比口径 + 指数水平口径）（运行：python scripts/eval_metrics.py）"""
import os, numpy as np, pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')   # 仓库里的 data/ 文件夹
m = pd.read_csv(os.path.join(D, 'final/final_model_main.csv')); m = m[m.split != 'covid_excluded'].reset_index(drop=True)
lv = pd.read_csv(os.path.join(D, 'final/final_levels_monthly.csv')).set_index('month').y_vol_4759_sa
base = (m.y_level / np.exp(m.y_yoy / 100)).values  # 去年同月指数
AR = ['y_yoy_L2', 'y_yoy_L3']; GT = [c for c in m if c.startswith('gt_')]; RET = [c for c in m if c.startswith('ret_')]
ALL = [c for c in m if '__' in c]
rid = lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 40)))
rf = lambda: RandomForestRegressor(500, min_samples_leaf=3, random_state=0)
def r2(y, p): return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
def met(y, p, b):
    yl, pl = b * np.exp(y / 100), b * np.exp(p / 100)
    return dict(R2_同比=r2(y, p), RMSE_同比=np.sqrt(np.mean((y - p) ** 2)), R2_指数=r2(yl, pl),
                RMSE_指数=np.sqrt(np.mean((yl - pl) ** 2)), MAPE_指数=100 * np.mean(np.abs(yl - pl) / yl))
tr, te = (m.split == 'train').values, (m.split == 'test').values
rows = []
for nm, mk, cols in [('AR 基准', rid, AR), ('Ridge ARX 全特征', rid, AR + ALL), ('Ridge 搜索+零售调查', rid, AR + GT + RET),
                     ('随机森林 全特征', rf, AR + ALL)]:
    md = mk().fit(m.loc[tr, cols], m.y_yoy[tr])
    for s, mask in [('训练', tr), ('测试', te)]:
        rows.append(dict(模型=nm, 集=s, 特征数=len(cols), **met(m.y_yoy[mask].values, md.predict(m.loc[mask, cols]), base[mask])))
r = pd.DataFrame(rows).round(3); print(r.to_string(index=False)); r.to_csv(os.path.join(D, 'final/eval_metrics.csv'), index=False)
print('测试期 y_yoy 均值/标准差', m.y_yoy[te].mean().round(2), m.y_yoy[te].std().round(2), '训练期', m.y_yoy[tr].mean().round(2), m.y_yoy[tr].std().round(2))
