# -*- coding: utf-8 -*-
"""Generate the real PPTX via live code and inspect the embedded 100% PDM excel + counts."""
import os, sys, io, zipfile
import pandas as pd
sys.path.insert(0, r"C:\AGL_Analytics")
import Insight_generation as IG

DATA = r"C:\AGL_Analytics\DATA\TESTING\BASE IMPORT 3 MOIS 2026 vs 2025.xlsx"
MOIS = IG.MOIS_NUM_TO_NAME
EXPECTED_COLS = {'Transitaire':['TRANSITAIRE','CONSIGNATAIRE'],'NOMBRE_TEU':['NOMBRE_TEU','VOLUME','TEUS'],
    'Mois escale':['MOIS ESCALE','MOIS'],'Année escale':['ANNÉE ESCALE','ANNEE ESCALE','ANNEE'],
    'I_IMP_E_EXP':['I_IMP_E_EXP','FLUX','SENS']}
def cn(s): return pd.to_numeric(s.astype(str).str.replace(' ','',regex=False).str.replace('\xa0','',regex=False).str.strip(),errors='coerce').fillna(0)
def nm(series):
    def _c(v):
        if pd.isna(v): return None
        try:
            n=int(float(str(v).strip()))
            if 1<=n<=12: return MOIS[n]
        except: pass
        return str(v).strip()
    return series.apply(_c)

xl=pd.ExcelFile(DATA)
best=max(xl.sheet_names,key=lambda s:sum(1 for al in EXPECTED_COLS.values() if any(a in [str(c).upper() for c in pd.read_excel(xl,sheet_name=s,nrows=5).columns] for a in al)))
df=pd.read_excel(xl,sheet_name=best)
up={str(c).upper():c for c in df.columns}
df=df.rename(columns={next((up[a] for a in al if a in up),None):k for k,al in EXPECTED_COLS.items() if next((up[a] for a in al if a in up),None)})
df['NOMBRE_TEU']=cn(df['NOMBRE_TEU']); df['Année escale']=cn(df['Année escale']).astype(int); df['Mois escale']=nm(df['Mois escale'])

def _log(m,l="info"): pass
# Build section: Import Maritime, YTD Mars (3 mois)
res=IG.build_section_from_filtered_df(df,'maritime','I','YTD','Mars',_log)
sec_name,sd=res
sections={sec_name:sd}
print("section:",sec_name,"| comp rows:",len(sd['comparison']),"| df_cible rows:",len(sd['df_cible']))

pptx=IG.generate_pptx_report(sections,'YTD Mars',False)
out=r"C:\AGL_Analytics\DATA\TESTING\_TEST_GENERATED.pptx"
with open(out,'wb') as f: f.write(pptx)
print("written",out,len(pptx),"bytes")

# Inspect embedded xlsx client lists. detail[0]=captive(100%PDM), detail[2]=hausse/baisse
z=zipfile.ZipFile(io.BytesIO(pptx))
def count_clients(name):
    data=z.read(name)
    wb=pd.read_excel(io.BytesIO(data),header=None)
    # client rows = rows where col B is a non-empty string and not a header/title
    colB=[str(v) for v in wb.iloc[:,1].tolist()]
    skip={'CLIENTS','NAN','',}
    n=0
    for v in colB:
        s=v.strip().upper()
        if s in skip or s=='NAN' or s.startswith('TOTAL') or 'CLIENTS A 100%' in s or s in (
            'CLIENTS EN HAUSSES','CLIENTS EN BAISSES','CLIENTS ACTIFS','CLIENTS NON ACTIFS'):
            continue
        n+=1
    return n, wb.shape
for lbl,fn in [('100%PDM (captive up+down)','Microsoft_Excel_Worksheet.xlsx'),
               ('ACTIFS/INACTIFS','Microsoft_Excel_Worksheet1.xlsx'),
               ('HAUSSES/BAISSES','Microsoft_Excel_Worksheet2.xlsx')]:
    full='ppt/embeddings/'+fn
    if full in z.namelist():
        n,shp=count_clients(full)
        print(f"  embedded [{lbl:28s}] client-rows~{n}  shape={shp}")
    else:
        print(f"  {full} not found")
