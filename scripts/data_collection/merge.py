# 合并所有原始数据 → data/furniture_nowcast_monthly_panel.csv 和 data/coverage.csv
# 运行：python scripts/data_collection/merge.py（不需要联网）
import pandas as pd,glob,os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]            # 仓库根目录
RAW = ROOT / 'data' / 'raw'                            # 处理好的原始数据
DL = RAW / 'downloads'                                 # 下载的临时文件（不提交到 GitHub）
R=str(RAW)+'/'; O=str(ROOT/'data')+'/'
m=pd.read_csv(R+'macro_and_target_monthly_raw.csv',index_col='month')
idx=pd.period_range('2004-01','2026-10',freq='M').astype(str)
m=m.reindex(idx)
# quarterly RDB -> monthly (quarter value /3, assigned to each month of quarter)
q=pd.read_csv(R+'eurostat_rdb_quarterly.csv',index_col=0).iloc[:,0]
qm={}
for k,v in q.items():
    y,qq=k.split('-Q'); 
    for i in range(3): qm[f'{y}-{(int(qq)-1)*3+i+1:02d}']=v/3
m['rdb_households_meur_monthly']=pd.Series(qm)
hp=pd.read_csv(R+'insee_house_price_index_quarterly.csv',index_col=0).iloc[:,0]
hm={}
for k,v in hp.items():
    y,qq=k.split('-Q')
    for i in range(3): hm[f'{y}-{(int(qq)-1)*3+i+1:02d}']=v
m['house_price_index_ancien_sa']=pd.Series(hm)
# population annual (1 Jan) -> monthly linear interpolation
pop=pd.read_csv(R+'eurostat_population_annual.csv',index_col=0).iloc[:,0]
ps=pd.Series({f'{y}-01':v for y,v in pop.items()}).reindex(idx).astype(float).interpolate(limit_area='inside')
m['population']=ps
m['pop_density_per_km2']=ps/632734
m['rdb_per_capita_eur_monthly']=m.rdb_households_meur_monthly*1e6/ps
m['rdb_real_meur_monthly']=m.rdb_households_meur_monthly/(m.hicp_total/100)
m['hicp_furniture_relative']=m.hicp_furniture/m.hicp_total*100
# DVF
d=pd.read_csv(R+'dvf_monthly_national.csv',index_col='month'); m=m.join(d)
# Google Trends
gt={}
for f in glob.glob(str(DL/'gt'/'*.csv')):
    n=os.path.basename(f)[:-4]; x=pd.read_csv(f,index_col=0); x.index=x.index.str[:7]; x=x.drop(columns='isPartial',errors='ignore')
    if n=='joint': 
        for c in x: gt['gtjoint_'+c.replace(' ','_')]=x[c]
    else: gt['gt_'+n.replace(' ','_')]=x.iloc[:,0]
if not gt and os.path.exists(R+'google_trends_monthly_FR.csv'):
    g=pd.read_csv(R+'google_trends_monthly_FR.csv',index_col=0); g.index=g.index.astype(str).str[:7]; m=m.join(g)
if gt:
    g=pd.DataFrame(gt); g.index.name='month'; g.sort_index().to_csv(R+'google_trends_monthly_FR.csv'); m=m.join(g)
m.index.name='month'
lead=['y_vol_4759_sa','y_vol_4759_nsa','y_ca_4759_sa','y_ca_4759_nsa','y_ca_4759A_meubles_nsa']
m=m[lead+[c for c in m if c not in lead]]
m.to_csv(O+'furniture_nowcast_monthly_panel.csv')
cov=pd.DataFrame({'first':m.apply(lambda s:s.first_valid_index()),'last':m.apply(lambda s:s.last_valid_index()),'n_obs':m.notna().sum()})
cov.to_csv(O+'coverage.csv'); print(cov.to_string()); print(m.shape)
