"""下一步实验：(1) DVF 子样本  (2) 2026-09/10 实时预测（运行：python scripts/next_steps_dvf_live.py）"""
import os, numpy as np, pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')   # 仓库里的 data/ 文件夹
rid = lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 40)))
rmse = lambda a, b: float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))
AR = ['y_yoy_L2', 'y_yoy_L3']

# ---------- (0) 复现主结果 ----------
m = pd.read_csv(os.path.join(D, 'final/final_model_main.csv')); m = m[m.split != 'covid_excluded']
GT = [c for c in m if c.startswith('gt_')]; RET = [c for c in m if c.startswith('ret_')]
tr, te = m.split == 'train', m.split == 'test'
for nm, cols in [('AR', AR), ('AR+X2+零售调查', AR + GT + RET)]:
    p = rid().fit(m.loc[tr, cols], m.loc[tr, 'y_yoy']).predict(m.loc[te, cols])
    print('复现', nm, round(rmse(m.loc[te, 'y_yoy'], p), 2))

# ---------- (1) DVF 子样本：扩展窗口（rolling-origin） ----------
d = pd.read_csv(os.path.join(D, 'final/final_model_dvf.csv'))
DVF = [c for c in d if c.startswith('dvf_')]
X1o = [c for c in d if c.startswith(('sitadel', 'house_price'))]
ALL = [c for c in d if '__' in c]
sets = {'AR': AR, 'AR+X2+零售调查': AR + GT + RET, 'AR+X2+零售调查+DVF': AR + GT + RET + DVF,
        'AR+DVF': AR + DVF, '全部(不含DVF)': AR + [c for c in ALL if c not in DVF], '全部(含DVF)': AR + ALL}
START = 24  # 前 24 个月做初始训练，之后每月重训、预测下一个月
res = []
for nm, cols in sets.items():
    pr = [rid().fit(d.loc[:t - 1, cols], d.loc[:t - 1, 'y_yoy']).predict(d.loc[[t], cols])[0] for t in range(START, len(d))]
    res.append((nm, len(cols), round(rmse(d.y_yoy.iloc[START:], pr), 2)))
r = pd.DataFrame(res, columns=['模型', '特征数', 'RMSE_同比'])
r['相对AR_%'] = (100 * (r.RMSE_同比 / r.RMSE_同比.iloc[0] - 1)).round(1)
print(f'DVF 子样本 {d.month.iloc[0]}..{d.month.iloc[-1]}，预测 {d.month.iloc[START]}..{d.month.iloc[-1]} 共 {len(d)-START} 个月'); print(r.to_string(index=False))
r.to_csv(os.path.join(D, 'final/dvf_subsample_results.csv'), index=False)

# ---------- (2) 实时预测 2026-09、2026-10 ----------
lv = pd.read_csv(os.path.join(D, 'final/final_levels_monthly.csv')).set_index('month')
F = pd.DataFrame(index=lv.index)
F['y_yoy'] = 100 * (np.log(lv.y_vol_4759_sa) - np.log(lv.y_vol_4759_sa.shift(12)))
for L in (2, 3): F[f'y_yoy_L{L}'] = F.y_yoy.shift(L)
for c in [x for x in lv if x.startswith('gt_')]:
    g = 100 * (np.log1p(lv[c]) - np.log1p(lv[c].shift(12)))
    for L in (0, 1, 3): F[f'{c}__yoy_L{L}'] = g.shift(L)
for L in (0, 1, 3): F[f'ret_eqlog_past_sales__lvl_L{L}'] = lv.ret_eqlog_past_sales.shift(L)
cols = AR + GT + RET
assert all(c in F for c in cols)
idx = pd.PeriodIndex(F.index, freq='M')
ok = ~((idx >= pd.Period('2020-03', 'M')) & (idx <= pd.Period('2022-06', 'M')))
fit = F[ok & F[cols + ['y_yoy']].notna().all(1)]
mdl = rid().fit(fit[cols], fit.y_yoy)
# 用测试期残差估计 80% 区间（训练到 2020-02 的模型在测试期的误差）
resid_sd = 3.77
out = []
for mo in ['2026-07', '2026-08', '2026-09', '2026-10']:
    x = F.loc[[mo], cols]
    yy = float(mdl.predict(x)[0]); base = lv.loc[str(pd.Period(mo, 'M') - 12), 'y_vol_4759_sa']
    out.append(dict(月份=mo, 预测同比=round(yy, 2), 区间80_低=round(yy - 1.28 * resid_sd, 1), 区间80_高=round(yy + 1.28 * resid_sd, 1),
                    预测指数=round(base * np.exp(yy / 100), 2), 去年同月=base, 实际指数=lv.loc[mo, 'y_vol_4759_sa'],
                    实际同比=round(F.loc[mo, 'y_yoy'], 2) if pd.notna(F.loc[mo, 'y_yoy']) else np.nan))
o = pd.DataFrame(out); print(f'训练样本 {fit.index[0]}..{fit.index[-1]}，{len(fit)} 个月'); print(o.to_string(index=False))
o.to_csv(os.path.join(D, 'final/live_nowcast_2026.csv'), index=False)
