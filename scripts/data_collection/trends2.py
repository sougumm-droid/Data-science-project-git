import time,os,pandas as pd
from pytrends.request import TrendReq
D='/tmp/claude-0/raw/gt/'; os.makedirs(D,exist_ok=True)
jobs=[('meuble',['meuble'],0),('canapé',['canapé'],0),('matelas',['matelas'],0),('déménagement',['déménagement'],0),('ikea',['ikea'],0),
      ('maisons du monde',['maisons du monde'],0),('conforama',['conforama'],0),('crédit immobilier',['crédit immobilier'],0),
      ('joint',['meuble','canapé','matelas','déménagement','ikea'],0),('cat_home_furnishings',[''],270)]
for attempt in range(12):
    left=[j for j in jobs if not os.path.exists(D+j[0]+'.csv')]
    if not left: break
    for name,kw,cat in left:
        try:
            p=TrendReq(hl='fr-FR',tz=-60,timeout=(10,30))
            p.build_payload(kw,cat=cat,geo='FR',timeframe='all'); d=p.interest_over_time()
            d.to_csv(D+name+'.csv'); print(time.strftime('%X'),name,'ok',len(d),flush=True)
        except Exception as e: print(time.strftime('%X'),name,'err',str(e)[:80],flush=True)
        time.sleep(75)
    time.sleep(300)
print('done',flush=True)
