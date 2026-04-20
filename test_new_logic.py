import sys, os
sys.path.insert(0, 'python_portable/Lib/site-packages')
import pandas as pd

df_tim = pd.read_excel('DATA/REPORT/BASES IMPORT TIM JANV 2026 VS 2025.xlsx', sheet_name='Export')
df_tim['NOMBRE_TEU'] = pd.to_numeric(df_tim['NOMBRE_TEU'], errors='coerce').fillna(0)
flux_col = df_tim['I_IMP_E_EXP'].fillna('').astype(str).str.upper().str.strip()

def is_agl(t): return 'AFRICA GLOBAL' in str(t).upper()

def get_stats(d, year, ccol):
    total = d.groupby(ccol)['NOMBRE_TEU'].sum().reset_index()
    total.columns = [ccol, 'Total_Marche_%d' % year]
    agl = d[d['Transitaire'].apply(is_agl)].groupby(ccol)['NOMBRE_TEU'].sum().reset_index()
    agl.columns = [ccol, 'AGL_Volume_%d' % year]
    m = pd.merge(total, agl, on=ccol, how='left').fillna(0)
    m['PDM_%d' % year] = (m['AGL_Volume_%d' % year] / m['Total_Marche_%d' % year] * 100).round(2)
    return m

ccol = 'Destinataire'
df_f = df_tim[flux_col.str.startswith('I')].copy()
ci = df_f[df_f['Pays de livraison'].astype(str).str.upper().str.contains('IVOIRE', na=False)]
jan = ci[ci['Mois escale'] == 'Janvier']
d26 = jan[jan['Année escale'] == 2026]
d25 = jan[jan['Année escale'] == 2025]

r26 = get_stats(d26, 2026, ccol)
r25 = get_stats(d25, 2025, ccol)
comp = pd.merge(r25, r26, on=ccol, how='outer').fillna(0)

# === NEW LOGIC (matching dashboard Stricts mode, seuil=100) ===
comp_a = comp[(comp['AGL_Volume_2026'] > 0) | (comp['AGL_Volume_2025'] > 0)].copy()
comp_a['Variation'] = comp_a['AGL_Volume_2026'] - comp_a['AGL_Volume_2025']

m_actifs = (comp_a['AGL_Volume_2026'] > 0) & (comp_a['Total_Marche_2025'] == 0)
m_inactifs = (comp_a['AGL_Volume_2025'] > 0) & (comp_a['Total_Marche_2026'] == 0)
m_present = ~(m_actifs | m_inactifs)
m_seuil = (comp_a['PDM_2026'] >= 100) & (comp_a['PDM_2025'] >= 100)
m_crois = comp_a['Variation'] >= 0
m_baisse = comp_a['Variation'] < 0

pdm100_up = comp_a[m_present & m_crois & m_seuil]
pdm100_dn = comp_a[m_present & m_baisse & m_seuil]
actifs = comp_a[m_actifs]
inactifs = comp_a[m_inactifs]
oth_up = comp_a[m_present & m_crois & ~m_seuil]
oth_dn = comp_a[m_present & m_baisse & ~m_seuil]

n_pdm = len(pdm100_up) + len(pdm100_dn)
v_pdm = int(pdm100_up['Variation'].sum() + pdm100_dn['Variation'].sum())

print('=== IMPORT MARITIME - Dashboard-aligned logic (Stricts, seuil=100) ===')
print('PDM100: %d %+d (up=%d %+d, dn=%d %+d)' % (n_pdm, v_pdm, len(pdm100_up), int(pdm100_up['Variation'].sum()), len(pdm100_dn), int(pdm100_dn['Variation'].sum())))
print('Actifs: %d %+d' % (len(actifs), int(actifs['Variation'].sum())))
print('Inactifs: %d %+d' % (len(inactifs), int(inactifs['Variation'].sum())))
print('Hausse: %d %+d' % (len(oth_up), int(oth_up['Variation'].sum())))
print('Baisse: %d %+d' % (len(oth_dn), int(oth_dn['Variation'].sum())))
total = n_pdm + len(actifs) + len(inactifs) + len(oth_up) + len(oth_dn)
print('Total: %d' % total)
print()
print('ORIGINAL: PDM100=21 +212 (12 +272, 09 -60)')
print('ORIGINAL: Actifs=40 +285, Inactifs=35 -175')
print('ORIGINAL: Hausse=54 +1507, Baisse=37 -738, Total=187')

# Also test Export Maritime
print()
df_e = df_tim[flux_col.str.startswith('E')].copy()
geo = 'Pays de prise en charge'
if geo in df_e.columns:
    ci_e = df_e[df_e[geo].astype(str).str.upper().str.contains('IVOIRE', na=False)]
else:
    ci_e = df_e[df_e['Pays de livraison'].astype(str).str.upper().str.contains('IVOIRE', na=False)]
ccol_e = 'Chargeur'
jan_e = ci_e[ci_e['Mois escale'] == 'Janvier']
e26 = jan_e[jan_e['Année escale'] == 2026]
e25 = jan_e[jan_e['Année escale'] == 2025]
er26 = get_stats(e26, 2026, ccol_e)
er25 = get_stats(e25, 2025, ccol_e)
ecomp = pd.merge(er25, er26, on=ccol_e, how='outer').fillna(0)

ea = ecomp[(ecomp['AGL_Volume_2026'] > 0) | (ecomp['AGL_Volume_2025'] > 0)].copy()
ea['Variation'] = ea['AGL_Volume_2026'] - ea['AGL_Volume_2025']
em_a = (ea['AGL_Volume_2026'] > 0) & (ea['Total_Marche_2025'] == 0)
em_i = (ea['AGL_Volume_2025'] > 0) & (ea['Total_Marche_2026'] == 0)
em_p = ~(em_a | em_i)
em_s = (ea['PDM_2026'] >= 100) & (ea['PDM_2025'] >= 100)
em_c = ea['Variation'] >= 0
em_b = ea['Variation'] < 0
epu = ea[em_p & em_c & em_s]
epd = ea[em_p & em_b & em_s]
eact = ea[em_a]
eina = ea[em_i]
eou = ea[em_p & em_c & ~em_s]
eod = ea[em_p & em_b & ~em_s]
en_pdm = len(epu) + len(epd)
ev_pdm = int(epu['Variation'].sum() + epd['Variation'].sum())

print('=== EXPORT MARITIME - Dashboard-aligned logic ===')
print('PDM100: %d %+d (up=%d %+d, dn=%d %+d)' % (en_pdm, ev_pdm, len(epu), int(epu['Variation'].sum()), len(epd), int(epd['Variation'].sum())))
print('Actifs: %d %+d' % (len(eact), int(eact['Variation'].sum())))
print('Inactifs: %d %+d' % (len(eina), int(eina['Variation'].sum())))
print('Hausse: %d %+d' % (len(eou), int(eou['Variation'].sum())))
print('Baisse: %d %+d' % (len(eod), int(eod['Variation'].sum())))
print('Total: %d' % (en_pdm + len(eact) + len(eina) + len(eou) + len(eod)))
print()
print('ORIGINAL: PDM100=42 +955 (15 +1120, 09 -165)')
print('ORIGINAL: Actifs=12 +65, Inactifs=21 -232')
print('ORIGINAL: Hausse=27 +2137, Baisse=25 -1657, Total=147')

os.remove(__file__)
