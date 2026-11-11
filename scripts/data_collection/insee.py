import re,sys,urllib.request,os
def keys(df):
    p=f'/tmp/claude-0/raw/{df}.keys.xml'
    if not os.path.exists(p):
        urllib.request.urlretrieve(f'https://bdm.insee.fr/series/sdmx/data/{df}?detail=nodata',p)
    t=open(p).read()
    return [dict(re.findall(r'(\w+)="([^"]*)"',s)) for s in re.findall(r'<Series ([^>]*)>',t)]
def series(ids):
    t=urllib.request.urlopen('https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/'+'+'.join(ids),timeout=120).read().decode()
    out={}
    for s in re.findall(r'<Series (.*?)</Series>',t,re.S):
        a=dict(re.findall(r'(\w+)="([^"]*)"',s.split('>')[0]))
        out[a['IDBANK']]=(a,re.findall(r'TIME_PERIOD="([^"]+)" OBS_VALUE="([^"]+)"',s))
    return out
if __name__=='__main__':
    df=sys.argv[1]; pat=sys.argv[2] if len(sys.argv)>2 else '.'
    for a in keys(df):
        if re.search(pat,a.get('TITLE_FR',''),re.I): print(a['IDBANK'],a.get('FREQ'),a.get('CORRECTION'),'|',a.get('TITLE_FR')[:200])
