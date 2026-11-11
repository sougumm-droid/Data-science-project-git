import pandas as pd,glob,sys
cols=['id_mutation','date_mutation','nature_mutation','valeur_fonciere','code_departement','type_local','surface_reelle_bati']
nat=[]; dep=[]
for f in sorted(glob.glob('/tmp/claude-0/raw/dvf/full_*.csv.gz')):
    d=pd.read_csv(f,usecols=cols,dtype={'code_departement':str,'id_mutation':str})
    d=d[d.nature_mutation.isin(['Vente',"Vente en l'état futur d'achèvement"])]
    d['is_m']=(d.type_local=='Maison').astype(int); d['is_a']=(d.type_local=='Appartement').astype(int)
    d['s_res']=d.surface_reelle_bati.where(d.type_local.isin(['Maison','Appartement']),0).fillna(0)
    g=d.groupby('id_mutation').agg(date=('date_mutation','first'),nature=('nature_mutation','first'),val=('valeur_fonciere','first'),
        dep=('code_departement','first'),n_mais=('is_m','sum'),n_app=('is_a','sum'),surf=('s_res','sum'))
    g=g[(g.n_mais+g.n_app)>=1].copy()
    g['month']=g.date.str[:7]
    g['single']=(g.n_mais+g.n_app)==1
    g['ptype']=g.n_mais.gt(0).map({True:'maison',False:'appart'})
    g['pm2']=g.val/g.surf
    ok=g.single&g.surf.gt(9)&g.pm2.between(300,30000)
    g['ok']=ok
    nat.append(g); print(f,len(g),file=sys.stderr)
g=pd.concat(nat)
m=g.groupby('month')
out=pd.DataFrame({'dvf_n_sales':m.size(),
 'dvf_n_maison':g[g.ptype=='maison'].groupby('month').size(),
 'dvf_n_appart':g[g.ptype=='appart'].groupby('month').size(),
 'dvf_n_vefa':g[g.nature!='Vente'].groupby('month').size(),
 'dvf_median_price':g[g.ok].groupby('month').val.median(),
 'dvf_median_price_m2':g[g.ok].groupby('month').pm2.median(),
 'dvf_median_price_m2_maison':g[g.ok&(g.ptype=='maison')].groupby('month').pm2.median(),
 'dvf_median_price_m2_appart':g[g.ok&(g.ptype=='appart')].groupby('month').pm2.median(),
 'dvf_total_value_meur':m.val.sum()/1e6})
out.index.name='month'
out.to_csv('/mnt/project-files/furniture-data/raw/dvf_monthly_national.csv')
dd=g.groupby(['month','dep']).agg(n_sales=('val','size')).join(g[g.ok].groupby(['month','dep']).agg(median_price_m2=('pm2','median')))
dd.to_csv('/mnt/project-files/furniture-data/raw/dvf_monthly_by_departement.csv')
print(out.to_string())
