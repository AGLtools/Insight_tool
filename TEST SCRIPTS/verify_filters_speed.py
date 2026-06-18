# -*- coding: utf-8 -*-
"""Standalone verification: filter parity (dashboard vs PPTX) + get_stats_annee speed."""
import os, json, time
import numpy as np
import pandas as pd

ROOT = r"C:\AGL_Analytics"
DATA = r"C:\AGL_Analytics\DATA\TESTING\BASE IMPORT 3 MOIS 2026 vs 2025.xlsx"
EXCLUDED_CLIENTS_FILE = os.path.join(ROOT, 'excluded_clients.json')

MOIS_NUM_TO_NAME = {1:'Janvier',2:'Février',3:'Mars',4:'Avril',5:'Mai',6:'Juin',
                    7:'Juillet',8:'Août',9:'Septembre',10:'Octobre',11:'Novembre',12:'Décembre'}
EXPECTED_COLS = {
    'Transitaire':['TRANSITAIRE','FORWARDER','CONSIGNATAIRE'],
    'NOMBRE_TEU':['NOMBRE_TEU','VOLUME','TEUS','TEU','QTE'],
    'Mois escale':['MOIS ESCALE','MOIS','MONTH'],
    'Année escale':['ANNÉE ESCALE','ANNEE ESCALE','ANNEE','YEAR'],
    'I_IMP_E_EXP':['I_IMP_E_EXP','FLUX','SENS','TYPE']}

def load_excluded():
    with open(EXCLUDED_CLIENTS_FILE,'r',encoding='utf-8') as f:
        return json.load(f).get('excluded_clients',[])
_EXC = {c.upper() for c in load_excluded()}
def _is_excluded_client(name):
    up=str(name).upper().strip()
    if up in _EXC: return True
    for kw in ['MINISTERE','MINISTRY','MINE ','MINES ','MINING','GOLD MINE']:
        if kw in up: return True
    return False

def clean_numeric_col(s):
    return pd.to_numeric(s.astype(str).str.replace(' ','',regex=False).str.replace('\xa0','',regex=False).str.strip(),errors='coerce').fillna(0)
def normalize_mois(series):
    def _c(val):
        if pd.isna(val): return None
        try:
            n=int(float(str(val).strip()))
            if 1<=n<=12: return MOIS_NUM_TO_NAME[n]
        except: pass
        return str(val).strip()
    return series.apply(_c)

# ── OLD get_stats_annee (per-group lambda) ──
def get_stats_old(df_annee, annee, client_col):
    if df_annee.empty:
        return pd.DataFrame(columns=[client_col,f'Total_Marche_{annee}',f'AGL_Volume_{annee}',f'PDM_{annee}'])
    stats=df_annee.groupby(client_col).agg(
        Total_Marche=('NOMBRE_TEU','sum'),
        AGL_Volume=('NOMBRE_TEU',lambda x: x[df_annee.loc[x.index,'Transitaire'].astype(str).str.contains('AFRICA GLOBAL',case=False,na=False)].sum())
    ).reset_index()
    stats[f'PDM_{annee}']=(stats['AGL_Volume']/stats['Total_Marche'])*100
    return stats.rename(columns={'Total_Marche':f'Total_Marche_{annee}','AGL_Volume':f'AGL_Volume_{annee}'})

# ── NEW get_stats_annee (vectorized) ──
def get_stats_new(df_annee, annee, client_col):
    if df_annee.empty:
        return pd.DataFrame(columns=[client_col,f'Total_Marche_{annee}',f'AGL_Volume_{annee}',f'PDM_{annee}'])
    d=df_annee[[client_col,'NOMBRE_TEU','Transitaire']].copy()
    is_agl=d['Transitaire'].astype(str).str.contains('AFRICA GLOBAL',case=False,na=False)
    d['_agl']=d['NOMBRE_TEU'].where(is_agl,0)
    stats=d.groupby(client_col,sort=False).agg(Total_Marche=('NOMBRE_TEU','sum'),AGL_Volume=('_agl','sum')).reset_index()
    tm=stats['Total_Marche'].replace(0,np.nan)
    stats[f'PDM_{annee}']=((stats['AGL_Volume']/tm)*100).fillna(0)
    return stats.rename(columns={'Total_Marche':f'Total_Marche_{annee}','AGL_Volume':f'AGL_Volume_{annee}'})

# ── captive (100% PDM) counting: OLD rounded vs NEW raw ──
def captive_counts(comp, ccol, cur, prv, rounded):
    c=comp.copy()
    c=c[~c[ccol].apply(_is_excluded_client)]
    ac,ap=f'AGL_Volume_{cur}',f'AGL_Volume_{prv}'
    tc,tp=f'Total_Marche_{cur}',f'Total_Marche_{prv}'
    c['Var']=c[ac]-c[ap]
    c['pdm_p']=np.where(c[tp]>0,c[ap]/c[tp].replace(0,np.nan),0)
    c['pdm_c']=np.where(c[tc]>0,c[ac]/c[tc].replace(0,np.nan),0)
    ab=c[(c[tp]>0)&(c[tc]>0)]
    if rounded:
        pp=(ab['pdm_p']*100).round().astype(int); pc=(ab['pdm_c']*100).round().astype(int)
        cap=ab[(pp>=95)&(pc>=95)&(ab[ap]>0)&(ab[ac]>0)]
    else:
        cap=ab[(ab['pdm_p']>=0.95)&(ab['pdm_c']>=0.95)&(ab[ap]>0)&(ab[ac]>0)]
    return len(cap), cap

print("Loading Excel...")
xl=pd.ExcelFile(DATA)
# pick sheet with most expected columns (like scan_all_sheets)
def score(s):
    up=[str(c).upper() for c in pd.read_excel(xl,sheet_name=s,nrows=5).columns]
    return sum(1 for al in EXPECTED_COLS.values() if any(a in up for a in al))
best=max(xl.sheet_names,key=score); print("  best sheet:",best)
t=time.time(); df_raw=pd.read_excel(xl,sheet_name=best); print(f"  read_excel: {time.time()-t:.1f}s, shape={df_raw.shape}")
upper={str(c).upper():c for c in df_raw.columns}
mapping={k:next((upper[a] for a in al if a in upper),None) for k,al in EXPECTED_COLS.items()}
print("  mapping:",mapping)
df=df_raw.rename(columns={v:k for k,v in mapping.items() if v})
flux=df['I_IMP_E_EXP'].dropna().unique()[0]
print("  flux:",flux)
df=df[df['I_IMP_E_EXP']==flux].copy()
df['NOMBRE_TEU']=clean_numeric_col(df['NOMBRE_TEU'])
df['Année escale']=clean_numeric_col(df['Année escale']).astype(int)
df['Mois escale']=normalize_mois(df['Mois escale'])
client_col='Destinataire' if str(flux).upper().startswith('I') else 'Chargeur'
print("  client_col:",client_col,"rows:",len(df))

years=sorted(df['Année escale'].dropna().unique())
cur,prv=int(max(years)),int(max(years))-1
print("  years:",years,"-> cur",cur,"prv",prv)

# Benchmark speed
print("\n=== SPEED get_stats_annee (current year slice) ===")
dcur=df[df['Année escale']==cur]
t=time.time(); old=get_stats_old(dcur,cur,client_col); t_old=time.time()-t
t=time.time(); new=get_stats_new(dcur,cur,client_col); t_new=time.time()-t
print(f"  OLD lambda : {t_old:.2f}s")
print(f"  NEW vector : {t_new:.2f}s   speedup x{t_old/max(t_new,1e-6):.0f}")
# correctness
m=old.merge(new,on=client_col,suffixes=('_o','_n'))
for base in ['Total_Marche','AGL_Volume','PDM']:
    co,cn=f'{base}_{cur}_o',f'{base}_{cur}_n'
    diff=(m[co].fillna(0)-m[cn].fillna(0)).abs().max()
    print(f"  max diff {base}: {diff:.6f}")

# Build comparison and check captive parity
res_cur=get_stats_new(df[df['Année escale']==cur],cur,client_col)
res_prv=get_stats_new(df[df['Année escale']==prv],prv,client_col)
comp=pd.merge(res_prv,res_cur,on=client_col,how='outer').fillna(0)
print("\n=== 100% PDM (captive) client count ===")
n_round,cap_r=captive_counts(comp,client_col,cur,prv,rounded=True)
n_raw,cap_raw=captive_counts(comp,client_col,cur,prv,rounded=False)
print(f"  OLD (_categorize_clients, ROUNDED >=95): {n_round} clients")
print(f"  NEW (dashboard parity, RAW >=95%)      : {n_raw} clients")
print(f"  EXTRA clients shown only by rounding    : {n_round-n_raw}")
extra=cap_r[~cap_r.index.isin(cap_raw.index)]
if len(extra):
    print("  --- clients wrongly included (94.5-95% band) ---")
    for _,r in extra.iterrows():
        print(f"    {str(r[client_col])[:45]:45s} pdm_prv={r['pdm_p']*100:.2f}%  pdm_cur={r['pdm_c']*100:.2f}%")
