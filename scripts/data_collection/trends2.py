# 下载 Google Trends（每个关键词一个文件）→ data/raw/downloads/gt/，之后运行 merge.py 合并
# 需要：pip install pytrends
import time,os,pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]            # 仓库根目录
RAW = ROOT / 'data' / 'raw'                            # 处理好的原始数据
DL = RAW / 'downloads'                                 # 下载的临时文件（不提交到 GitHub）
from pytrends.request import TrendReq
D=str(DL/'gt')+'/'; os.makedirs(D,exist_ok=True)
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
