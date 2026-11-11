import sys,io,urllib.request,pandas as pd
sys.path.insert(0,'/tmp/claude-0/scripts'); import insee
OUT='/mnt/project-files/furniture-data/raw/'
def get(u): return urllib.request.urlopen(u,timeout=180).read().decode()
# ---- INSEE monthly series
ins={
 '010770085':'y_vol_4759_sa','010770084':'y_vol_4759_nsa',
 '010770861':'y_ca_4759_sa','010770477':'y_ca_4759_nsa','010770863':'y_ca_4759A_meubles_nsa',
 '010770075':'vol_475_sa',
 '011794497':'conso_equip_logement_vol_sa','011794493':'conso_biens_durables_vol_sa',
 '001587668':'conf_menages_sa','001616795':'enq_amenagement_logement_sa','000857193':'enq_achats_importants_sa','001616793':'enq_achats_equipement_sa','001616794':'enq_intention_achat_logement_sa',
 '010752277':'sitadel_logements_commences_sa','010752271':'sitadel_logements_autorises_sa',
 '001718274':'sitadel_commences_cumul12m','001718162':'sitadel_autorises_cumul12m',
}
r=insee.series(list(ins))
rows=[];meta=[]
for k,(a,obs) in r.items():
    for t,v in obs: rows.append((t,ins[k],float(v)))
    meta.append(dict(var=ins[k],source='INSEE BDM',id=k,freq=a.get('FREQ'),start=min(o[0] for o in obs),end=max(o[0] for o in obs),title=a.get('TITLE_FR'),url=f'https://www.insee.fr/fr/statistiques/serie/{k}'))
insm=pd.DataFrame(rows,columns=['month','var','v']).pivot(index='month',columns='var',values='v')
# ---- INSEE quarterly house price index
q=insee.series(['010567059'])
a,obs=q['010567059']; hp=pd.Series({t:float(v) for t,v in obs}); meta.append(dict(var='house_price_index_ancien_sa',source='INSEE BDM',id='010567059',freq='T',start=min(hp.index),end=max(hp.index),title=a.get('TITLE_FR'),url='https://www.insee.fr/fr/statistiques/serie/010567059'))
# ---- Eurostat
E='https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/'
def es(path,name,title):
    d=pd.read_csv(io.StringIO(get(E+path+('&' if '?' in path else '?')+'format=SDMX-CSV')))
    s=d.set_index('TIME_PERIOD').OBS_VALUE.sort_index(); meta.append(dict(var=name,source='Eurostat',id=path.split('?')[0],freq=path.split('/')[1][0],start=s.index[0],end=s.index[-1],title=title,url='https://ec.europa.eu/eurostat/databrowser/view/'+path.split('/')[0])); return s.rename(name)
eu=[es('sts_trtu_m/M.VOL_SLS.G475.SCA.I21.FR?startPeriod=2000-01','eu_vol_G475_sa','Retail trade volume, NACE G47.5 household equipment, SCA, 2021=100'),
    es('sts_trtu_m/M.VOL_SLS.G47.SCA.I21.FR?startPeriod=2000-01','eu_vol_G47_sa','Retail trade volume, total retail G47, SCA, 2021=100'),
    es('prc_hicp_minr/M.I25.CP0511.FR?startPeriod=2000-01','hicp_furniture','HICP 05.1.1 furniture & furnishings, 2025=100'),
    es('prc_hicp_minr/M.I25.TOTAL.FR?startPeriod=2000-01','hicp_total','HICP all items, 2025=100'),
    es('une_rt_m/M.SA.TOTAL.PC_ACT.T.FR?startPeriod=2000-01','unemployment_rate_sa','Unemployment rate, SA, %')]
rdb=es('nasq_10_nf_tr/Q.CP_MEUR.RECV.S14_S15.B6G.SCA.FR?startPeriod=2000','rdb_households_meur_q','Households+NPISH gross disposable income, current prices, SCA, M EUR per quarter')
pop=es('demo_gind/A.JAN.FR?startPeriod=2000','population_jan1','Population on 1 January, France')
# ---- ECB mortgage rate
m=pd.read_csv('/tmp/claude-0/raw/mir.csv')  # downloaded earlier from data-api.ecb.europa.eu (MIR key below)
mort=m.set_index('TIME_PERIOD').OBS_VALUE.rename('mortgage_rate_new_business'); meta.append(dict(var='mortgage_rate_new_business',source='ECB MIR',id='MIR.M.FR.B.A2C.A.R.A.2250.EUR.N',freq='M',start=mort.index[0],end=mort.index[-1],title='Bank interest rate, new loans to households for house purchase, France, %',url='https://data.ecb.europa.eu/data/datasets/MIR/MIR.M.FR.B.A2C.A.R.A.2250.EUR.N'))
# ---- FRED 10y OAT
f=pd.read_csv(io.StringIO(get('https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRLTLT01FRM156N')))
f.columns=['d','v']; oat=pd.Series(f.v.values,index=f.d.str[:7],name='oat10y_rate'); oat=pd.to_numeric(oat,errors='coerce'); meta.append(dict(var='oat10y_rate',source='FRED (OECD)',id='IRLTLT01FRM156N',freq='M',start=oat.index[0],end=oat.index[-1],title='France 10-year government bond yield, %',url='https://fred.stlouisfed.org/series/IRLTLT01FRM156N'))
# save raw
for s,n in [(rdb,'eurostat_rdb_quarterly'),(pop,'eurostat_population_annual'),(hp,'insee_house_price_index_quarterly')]: s.to_csv(OUT+n+'.csv',header=True)
monthly=pd.concat([insm]+eu+[mort,oat],axis=1); monthly.index.name='month'; monthly=monthly.sort_index()
monthly.to_csv(OUT+'macro_and_target_monthly_raw.csv')
pd.DataFrame(meta).to_csv(OUT+'_series_catalog.csv',index=False)
print(pd.DataFrame(meta)[['var','freq','start','end']].to_string())
