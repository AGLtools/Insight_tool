# -*- coding: utf-8 -*-
"""Use the LIVE Insight_generation functions to compare PPTX captive list vs dashboard."""
import os, sys, time
import numpy as np
import pandas as pd
sys.path.insert(0, r"C:\AGL_Analytics")
import Insight_generation as IG

DATA = r"C:\AGL_Analytics\DATA\TESTING\BASE IMPORT 3 MOIS 2026 vs 2025.xlsx"
MOIS_NUM_TO_NAME = IG.MOIS_NUM_TO_NAME

# ---- replicate the dashboard data prep (app.py) ----
EXPECTED_COLS = {
    'Transitaire':['TRANSITAIRE','FORWARDER','CONSIGNATAIRE'],
    'NOMBRE_TEU':['NOMBRE_TEU','VOLUME','TEUS','TEU','QTE'],
    'Mois escale':['MOIS ESCALE','MOIS','MONTH'],
    'Année escale':['ANNÉE ESCALE','ANNEE ESCALE','ANNEE','YEAR'],
    'I_IMP_E_EXP':['I_IMP_E_EXP','FLUX','SENS','TYPE']}
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

xl=pd.ExcelFile(DATA)
def score(s):
    up=[str(c).upper() for c in pd.read_excel(xl,sheet_name=s,nrows=5).columns]
    return sum(1 for al in EXPECTED_COLS.values() if any(a in up for a in al))
best=max(xl.sheet_names,key=score)
df_raw=pd.read_excel(xl,sheet_name=best)
upper={str(c).upper():c for c in df_raw.columns}
mapping={k:next((upper[a] for a in al if a in upper),None) for k,al in EXPECTED_COLS.items()}
df=df_raw.rename(columns={v:k for k,v in mapping.items() if v})
flux=df['I_IMP_E_EXP'].dropna().unique()[0]
df=df[df['I_IMP_E_EXP']==flux].copy()
df['NOMBRE_TEU']=clean_numeric_col(df['NOMBRE_TEU'])
df['Année escale']=clean_numeric_col(df['Année escale']).astype(int)
df['Mois escale']=normalize_mois(df['Mois escale'])
client_col='Destinataire' if str(flux).upper().startswith('I') else 'Chargeur'
years=sorted(df['Année escale'].dropna().unique()); cur,prv=int(max(years)),int(max(years))-1
months=sorted(df['Mois escale'].dropna().unique(), key=lambda m:{n:i for i,n in MOIS_NUM_TO_NAME.items()}.get(m,99))
print("flux",flux,"client",client_col,"years",years,"months",months)

# ---- build the SAME comparison both paths use ----
# Use the LIVE get_stats_annee from Insight_generation
def build_comp(dframe):
    res_cur=IG.get_stats_annee(dframe[dframe['Année escale']==cur],cur,client_col)
    res_prv=IG.get_stats_annee(dframe[dframe['Année escale']==prv],prv,client_col)
    return pd.merge(res_prv,res_cur,on=client_col,how='outer').fillna(0)

# === DASHBOARD default = "Mois Spécifique" on FIRST month; PPTX default? ===
# Test BOTH a single-month and the YTD-3-months to expose period mismatch.
def dashboard_captive(comp, seuil=95, mode='strict'):
    ac,ap=f'AGL_Volume_{cur}',f'AGL_Volume_{prv}'
    tc,tp=f'Total_Marche_{cur}',f'Total_Marche_{prv}'
    pc,pp=f'PDM_{cur}',f'PDM_{prv}'
    c=comp.copy(); c['Var']=c[ac]-c[ap]
    if mode=='strict':
        new=(c[ac]>0)&(c[tp]==0); lost=(c[ap]>0)&(c[tc]==0)
    else:
        new=(c[ac]>0)&(c[ap]==0); lost=(c[ap]>0)&(c[ac]==0)
    present=~(new|lost)&((c[ac]>0)|(c[ap]>0))
    seuilm=(c[pc]>=seuil)&(c[pp]>=seuil)
    cap=c[present&seuilm]
    return cap

def pptx_captive(comp):
    cats=IG._categorize_clients(comp, client_col, cur, prv)
    return pd.concat([cats['captive_up'],cats['captive_down']])

def dashboard_all(comp, seuil=95, mode='strict'):
    ac,ap=f'AGL_Volume_{cur}',f'AGL_Volume_{prv}'
    tc,tp=f'Total_Marche_{cur}',f'Total_Marche_{prv}'
    pc,pp=f'PDM_{cur}',f'PDM_{prv}'
    c=comp.copy(); c['Var']=c[ac]-c[ap]
    new=(c[ac]>0)&(c[tp]==0); lost=(c[ap]>0)&(c[tc]==0)
    present=~(new|lost)&((c[ac]>0)|(c[ap]>0))
    seuilm=(c[pc]>=seuil)&(c[pp]>=seuil)
    return {
        'captive': c[present&seuilm],
        'new':     c[new],
        'lost':    c[lost],
        'hausse':  c[present&(c['Var']>=0)&~seuilm],
        'baisse':  c[present&(c['Var']<0)&~seuilm],
    }

for mode_lbl, dsub, label in [
    ("YTD 3 mois", df, "YTD"),
    (f"Mois unique [{months[0]}]", df[df['Mois escale']==months[0]], months[0]),
]:
    comp=build_comp(dsub)
    dash=dashboard_all(comp)
    cats=IG._categorize_clients(comp, client_col, cur, prv)
    ppt={'captive':pd.concat([cats['captive_up'],cats['captive_down']]),
         'new':cats['new'],'lost':cats['lost'],'hausse':cats['hausse'],'baisse':cats['baisse']}
    print(f"\n=== {mode_lbl} (comp rows {len(comp)}) ===")
    print(f"  {'category':10s} {'DASH':>6s} {'PPTX':>6s}  match")
    for k in ['captive','new','lost','hausse','baisse']:
        nd,npp=len(dash[k]),len(ppt[k])
        sd=set(dash[k][client_col]); spp=set(ppt[k][client_col])
        print(f"  {k:10s} {nd:6d} {npp:6d}  {'OK' if sd==spp else 'DIFF -> ppt_only='+str(len(spp-sd))+' dash_only='+str(len(sd-spp))}")
