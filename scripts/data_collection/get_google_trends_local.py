# 在你自己的电脑上运行：pip install pytrends pandas && python get_google_trends_local.py
# 输出 google_trends_monthly_FR.csv（月度，2004-01 起），放到 furniture-data/raw/ 下即可。
import time, pandas as pd
from pytrends.request import TrendReq
jobs = {'meuble':['meuble'],'canapé':['canapé'],'matelas':['matelas'],'déménagement':['déménagement'],'ikea':['ikea'],
        'maisons_du_monde':['maisons du monde'],'conforama':['conforama'],'crédit_immobilier':['crédit immobilier']}
p = TrendReq(hl='fr-FR', tz=-60)
cols = {}
for name, kw in jobs.items():
    p.build_payload(kw, geo='FR', timeframe='all')          # 'all' => Google 直接返回月度值
    cols['gt_'+name] = p.interest_over_time()[kw[0]]; print(name, 'ok'); time.sleep(10)
p.build_payload(['meuble','canapé','matelas','déménagement','ikea'], geo='FR', timeframe='all')
j = p.interest_over_time().drop(columns='isPartial'); j.columns = ['gtjoint_'+c for c in j.columns]
time.sleep(10)
p.build_payload([''], cat=270, geo='FR', timeframe='all')   # 类别 270 = Home Furnishings
cols['gt_cat_home_furnishings'] = p.interest_over_time().iloc[:,0]
df = pd.concat([pd.DataFrame(cols), j], axis=1); df.index = df.index.strftime('%Y-%m'); df.index.name = 'month'
df.to_csv('google_trends_monthly_FR.csv'); print(df.tail())
