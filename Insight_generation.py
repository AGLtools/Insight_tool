"""
Insight_generation.py
─────────────────────────────────────────────────────────────────────────────
Génération du rapport PPTX AGL Business Insight + UI Streamlit standalone.

Ce module est autonome (helpers dupliqués depuis app.py si nécessaire) afin
d'éviter les imports circulaires.
"""
import os
import io
import json
import sys

# Assurer le chemin portable
_portable_site = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "python_portable", "Lib", "site-packages")
if os.path.isdir(_portable_site) and _portable_site not in sys.path:
    sys.path.insert(0, _portable_site)

import pandas as pd

# ─────────────────────────────────────────────
#  CONSTANTES (dupliquées depuis app.py)
# ─────────────────────────────────────────────
TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'DATA', 'template.pptx')
EXCLUDED_CLIENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'excluded_clients.json')

MOIS_NUM_TO_NAME = {1:'Janvier',2:'Février',3:'Mars',4:'Avril',5:'Mai',6:'Juin',
                    7:'Juillet',8:'Août',9:'Septembre',10:'Octobre',11:'Novembre',12:'Décembre'}

# Abréviations utilisées dans le template (en-têtes de tableaux : "Janv 2026", etc.)
ABBREV_BY_FULL = {
    'Janvier': 'Janv', 'Février': 'Févr', 'Mars': 'Mars', 'Avril': 'Avr',
    'Mai': 'Mai',     'Juin': 'Juin',    'Juillet': 'Juil', 'Août': 'Août',
    'Septembre': 'Sept', 'Octobre': 'Oct', 'Novembre': 'Nov', 'Décembre': 'Déc',
}

EXPECTED_COLS = {
    'Transitaire':    ['TRANSITAIRE', 'FORWARDER', 'CONSIGNATAIRE'],
    'NOMBRE_TEU':     ['NOMBRE_TEU', 'VOLUME', 'TEUS', 'TEU', 'QTE'],
    'Mois escale':    ['MOIS ESCALE', 'MOIS', 'MONTH'],
    'Année escale':   ['ANNÉE ESCALE', 'ANNEE ESCALE', 'ANNEE', 'YEAR'],
    'I_IMP_E_EXP':    ['I_IMP_E_EXP', 'FLUX', 'SENS', 'TYPE']
}
OPTIONAL_COLS = {
    'Pays de livraison': ['PAYS DE LIVRAISON', 'PAYS DE LIVRA', 'DESTINATION'],
    'Pays de prise en charge': ['PAYS DE PRISE EN CHARGE', 'PAYS PRISE EN CHARGE', 'PAYS ORIGINE'],
    'Conditionnement':   ['CODE_CONDIT', 'CONDITIONNEMENT', 'TYPE CONTAINER', 'EQUIPEMENT', 'TAILLE']
}
EXPECTED_COLS_AERIEN = {
    'Transitaire':    ['TRANSITAIRE', 'FORWARDER', 'CONSIGNATAIRE'],
    'NOMBRE_TEU':     ['POIDS MARCHANDISE', 'POIDS', 'WEIGHT', 'POIDS BRUT'],
    'Mois escale':    ['MOIS ESCALE', 'MOIS', 'MONTH'],
    'Année escale':   ['ANNÉE ESCALE', 'ANNEE ESCALE', 'ANNEE', 'YEAR'],
    'I_IMP_E_EXP':    ['SENS', 'I_IMP_E_EXP', 'FLUX', 'TYPE']
}
OPTIONAL_COLS_AERIEN = {
    'Pays de livraison': ['AÉROPORT CHARGEMENT', 'AEROPORT CHARGEMENT', 'AÉROPORT DÉCHARGEMENT', 'AEROPORT DECHARGEMENT'],
    'Conditionnement':   ['MARCHANDISE', 'COMMODITY', 'DESCRIPTION']
}


# ─────────────────────────────────────────────
#  HELPERS (dupliqués depuis app.py)
# ─────────────────────────────────────────────
def load_excluded_clients():
    if os.path.exists(EXCLUDED_CLIENTS_FILE):
        try:
            with open(EXCLUDED_CLIENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('excluded_clients', [])
        except Exception:
            return []
    return []

def _is_excluded_client(name):
    up = str(name).upper().strip()
    excluded_upper = {c.upper() for c in load_excluded_clients()}
    if up in excluded_upper:
        return True
    for kw in ['MINISTERE', 'MINISTRY', 'MINE ', 'MINES ', 'MINING', 'GOLD MINE']:
        if kw in up:
            return True
    return False

def _is_non_apure(value):
    if pd.isna(value):
        return True
    s = str(value).strip().upper()
    return s in ('', '0', '0.0', 'NAN', 'N/A', 'NON APURE', 'NONE')

def _select_primary_competitor_rows(df_comp, client_col, trans_col='Transitaire', volume_col='NOMBRE_TEU'):
    if df_comp.empty:
        return pd.DataFrame(columns=[client_col, trans_col, volume_col])
    selected_rows = []
    for client in df_comp[client_col].dropna().unique():
        client_data = df_comp[df_comp[client_col] == client].sort_values(volume_col, ascending=False)
        if client_data.empty:
            continue
        chosen_row = None
        for _, row in client_data.iterrows():
            vol = pd.to_numeric(row[volume_col], errors='coerce')
            vol = float(vol) if pd.notna(vol) else 0.0
            if (not _is_non_apure(row[trans_col])) and (vol > 0):
                chosen_row = row.copy()
                break
        if chosen_row is None:
            chosen_row = client_data.iloc[0].copy()
            chosen_row[trans_col] = 'NON APURE'
        selected_rows.append(chosen_row)
    if not selected_rows:
        return pd.DataFrame(columns=[client_col, trans_col, volume_col])
    return pd.DataFrame(selected_rows)

def normalize_mois_column(series):
    def _convert(val):
        if pd.isna(val):
            return None
        try:
            n = int(float(str(val).strip()))
            if 1 <= n <= 12:
                return MOIS_NUM_TO_NAME[n]
        except (ValueError, TypeError):
            pass
        s = str(val).strip()
        return s
    return series.apply(_convert)

def detect_data_type(columns):
    upper = [str(c).upper() for c in columns]
    aerien_markers = ['POIDS MARCHANDISE', 'NUMERO LTA', 'NUMÉRO LTA', 'COMPAGNIE', 'AÉROPORT ESCALE', 'AEROPORT ESCALE']
    maritime_markers = ['NOMBRE_TEU', 'TEUS', 'NAVIRE', 'PORT ESCALE', 'CONNAISSEMENT']
    a = sum(1 for m in aerien_markers if any(m in u for u in upper))
    s = sum(1 for m in maritime_markers if any(m in u for u in upper))
    return 'aerien' if a > s else 'maritime'

def clean_numeric_col(series):
    return pd.to_numeric(
        series.astype(str).str.replace(' ', '', regex=False).str.replace('\xa0', '', regex=False).str.strip(),
        errors='coerce'
    ).fillna(0)

def get_stats_annee(df_annee, annee, client_col):
    if df_annee.empty:
        return pd.DataFrame(columns=[client_col, f'Total_Marche_{annee}', f'AGL_Volume_{annee}', f'PDM_{annee}'])
    stats = df_annee.groupby(client_col).agg(
        Total_Marche=('NOMBRE_TEU', 'sum'),
        AGL_Volume=('NOMBRE_TEU', lambda x: x[df_annee.loc[x.index, 'Transitaire'].astype(str).str.contains('AFRICA GLOBAL', case=False, na=False)].sum())
    ).reset_index()
    stats[f'PDM_{annee}'] = (stats['AGL_Volume'] / stats['Total_Marche']) * 100
    return stats.rename(columns={'Total_Marche': f'Total_Marche_{annee}', 'AGL_Volume': f'AGL_Volume_{annee}'})


# ─────────────────────────────────────────────
#  GÉNÉRATION DES FEUILLES EXCEL EMBARQUÉES
# ─────────────────────────────────────────────
def _make_dual_xlsx(left_title, right_title, left_df, right_df,
                    client_col, label_per, unit, cur_year, prev_year, right_extra_col=None):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = 'Feuil1'
    lp = label_per.upper().split()[-1] if ' ' in label_per else label_per.upper()
    u = unit.upper()

    thin = Side(style='thin')
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    title_font = Font(bold=True, size=10)
    left_hdr_fill = PatternFill('solid', fgColor='4472C4')
    right_hdr_fill = PatternFill('solid', fgColor='ED7D31')
    hdr_font = Font(bold=True, size=9, color='FFFFFF')
    hdr_align_c = Alignment(horizontal='center', vertical='center', wrap_text=True)
    hdr_align_l = Alignment(horizontal='left', vertical='center', wrap_text=True)
    data_font = Font(size=9)
    data_font_bold = Font(size=9, bold=True)
    num_align = Alignment(horizontal='center')
    left_align = Alignment(horizontal='left')
    idx_align = Alignment(horizontal='right')
    num_fmt = '#,##0'
    pct_fmt = '0%'

    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 35
    for col in ['C', 'D', 'E', 'F', 'G', 'H', 'I']:
        ws.column_dimensions[col].width = 12
    ws.column_dimensions['J'].width = 5
    ws.column_dimensions['K'].width = 36
    for col in ['L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S']:
        ws.column_dimensions[col].width = 12

    ws.cell(2, 2, left_title).font = title_font
    ws.cell(2, 11, right_title).font = title_font

    hdrs = ['CLIENTS',
            f'VOLUME {lp} {cur_year} {u}', f'AGL {lp} {cur_year} {u}', f'PDM {cur_year}',
            f'VOLUME {lp} {prev_year} {u}', f'AGL {lp} {prev_year} {u}', f'PDM {prev_year}',
            'VARIATION']
    for i, h in enumerate(hdrs):
        cl = ws.cell(4, 2 + i, h)
        cl.font = hdr_font; cl.fill = left_hdr_fill
        cl.alignment = hdr_align_l if i == 0 else hdr_align_c; cl.border = border_all
        cr = ws.cell(4, 11 + i, h)
        cr.font = hdr_font; cr.fill = right_hdr_fill
        cr.alignment = hdr_align_l if i == 0 else hdr_align_c; cr.border = border_all

    col_tm_cur = f'Total_Marche_{cur_year}'
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'

    def _write_side(df, num_col, data_col, is_right=False, hdr_fill=None):
        for idx, (_, row) in enumerate(df.iterrows()):
            r = 5 + idx
            tm_cur = int(row.get(col_tm_cur, 0))
            ta_cur = int(row.get(col_ag_cur, 0))
            tm_prv = int(row.get(col_tm_prv, 0))
            ta_prv = int(row.get(col_ag_prv, 0))
            c_idx = ws.cell(r, num_col, idx + 1)
            c_idx.font = data_font; c_idx.number_format = num_fmt; c_idx.alignment = idx_align
            c_name = ws.cell(r, data_col, str(row[client_col]))
            c_name.font = data_font; c_name.alignment = left_align; c_name.border = border_all
            for off, val in [(1, tm_cur), (2, ta_cur), (4, tm_prv), (5, ta_prv)]:
                cc = ws.cell(r, data_col + off, val)
                cc.font = data_font; cc.number_format = num_fmt; cc.alignment = num_align; cc.border = border_all
            c_p_cur = ws.cell(r, data_col + 3, ta_cur / tm_cur if tm_cur > 0 else 0)
            c_p_cur.font = data_font; c_p_cur.number_format = pct_fmt; c_p_cur.alignment = num_align; c_p_cur.border = border_all
            c_p_prv = ws.cell(r, data_col + 6, ta_prv / tm_prv if tm_prv > 0 else 0)
            c_p_prv.font = data_font; c_p_prv.number_format = pct_fmt; c_p_prv.alignment = num_align; c_p_prv.border = border_all
            c_var = ws.cell(r, data_col + 7, int(ta_cur - ta_prv))
            c_var.font = data_font; c_var.number_format = num_fmt; c_var.alignment = num_align
            if is_right and right_extra_col and right_extra_col in row.index:
                c_vm = ws.cell(r, data_col + 8, int(row[right_extra_col]))
                c_vm.font = data_font; c_vm.number_format = num_fmt; c_vm.alignment = num_align
        if len(df) > 0:
            r = 5 + len(df)
            s_cur = int(df[col_tm_cur].sum()); a_cur = int(df[col_ag_cur].sum())
            s_prv = int(df[col_tm_prv].sum()) if col_tm_prv in df.columns else 0
            a_prv = int(df[col_ag_prv].sum()) if col_ag_prv in df.columns else 0
            c_t = ws.cell(r, data_col, 'TOTAL')
            c_t.font = data_font_bold; c_t.alignment = left_align; c_t.border = border_all
            for off, val in [(1, s_cur), (2, a_cur), (4, s_prv), (5, a_prv)]:
                cc = ws.cell(r, data_col + off, val)
                cc.font = data_font_bold; cc.number_format = num_fmt; cc.alignment = num_align; cc.border = border_all
            for off, num, den in [(3, a_cur, s_cur), (6, a_prv, s_prv)]:
                cc = ws.cell(r, data_col + off, num / den if den > 0 else 0)
                cc.font = data_font_bold; cc.number_format = pct_fmt; cc.alignment = num_align; cc.border = border_all
            cc = ws.cell(r, data_col + 7, int(a_cur - a_prv))
            cc.font = data_font_bold; cc.number_format = num_fmt; cc.alignment = num_align
            if is_right and right_extra_col and right_extra_col in df.columns:
                cc = ws.cell(r, data_col + 8, int(df[right_extra_col].sum()))
                cc.font = data_font_bold; cc.number_format = num_fmt; cc.alignment = num_align

    _write_side(left_df, 1, 2, False, left_hdr_fill)
    _write_side(right_df, 10, 11, True, right_hdr_fill)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _categorize_clients(comp, client_col, cur_year, prev_year):
    c = comp.copy()
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'
    col_tm_cur = f'Total_Marche_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'

    c['Variation'] = c[col_ag_cur] - c[col_ag_prv]
    c['Var_Marche'] = c[col_tm_cur] - c[col_tm_prv]
    c['PDM_prv'] = c.apply(lambda r: r[col_ag_prv] / r[col_tm_prv] if r[col_tm_prv] > 0 else 0, axis=1)
    c['PDM_cur'] = c.apply(lambda r: r[col_ag_cur] / r[col_tm_cur] if r[col_tm_cur] > 0 else 0, axis=1)

    active_both = c[(c[col_tm_prv] > 0) & (c[col_tm_cur] > 0)]
    captive = active_both[(active_both['PDM_prv'] >= 0.95) & (active_both['PDM_cur'] >= 0.95) &
                          (active_both[col_ag_prv] > 0) & (active_both[col_ag_cur] > 0)]
    non_captive = active_both[~active_both.index.isin(captive.index)]

    return {
        'captive_up':   captive[captive['Variation'] >= 0].sort_values('Variation', ascending=False),
        'captive_down': captive[captive['Variation'] < 0].sort_values('Variation', ascending=True),
        'new':          c[(c[col_tm_prv] == 0) & (c[col_ag_cur] > 0)].sort_values('Variation', ascending=False),
        'lost':         c[(c[col_tm_cur] == 0) & (c[col_ag_prv] > 0)].sort_values('Variation', ascending=True),
        'hausse':       non_captive[non_captive['Variation'] > 0].sort_values('Variation', ascending=False),
        'baisse':       non_captive[non_captive['Variation'] < 0].sort_values('Variation', ascending=True),
        'all': c,
    }


def _make_top100_xlsx(comp, client_col, label_per, unit, cur_year, prev_year):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = 'Feuil1'
    lp = label_per.upper().split()[-1] if ' ' in label_per else label_per.upper()
    u = unit.upper()
    col_tm_cur = f'Total_Marche_{cur_year}'
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'

    c = comp.copy()
    c['Variation'] = c[col_ag_cur] - c[col_ag_prv]
    top = c.sort_values(col_tm_cur, ascending=False).head(100)
    role = 'IMPORTATEURS' if client_col == 'Destinataire' else 'EXPORTATEURS'

    thin = Side(style='thin')
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    title_font = Font(bold=True, size=10)
    hdr_fill = PatternFill('solid', fgColor='4472C4')
    hdr_font = Font(bold=True, size=9, color='FFFFFF')
    hdr_align_c = Alignment(horizontal='center', vertical='center', wrap_text=True)
    hdr_align_l = Alignment(horizontal='left', vertical='center', wrap_text=True)
    data_font = Font(size=9)
    num_align = Alignment(horizontal='center')
    left_align = Alignment(horizontal='left')
    num_fmt = '#,##0'
    pct_fmt = '0%'

    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 55
    for col in ['C', 'D', 'E', 'F', 'G', 'H', 'I']:
        ws.column_dimensions[col].width = 12

    ws.cell(2, 2, f"TOP 100 {role} COTE D'IVOIRE").font = title_font

    hdrs = [role,
            f'VOLUME {u} {lp} {cur_year}', f'AGL {u} {lp} {cur_year}', f'PDM {cur_year}',
            f'VOLUME {u} {lp} {prev_year}', f'AGL {u} {lp} {prev_year}', f'PDM {prev_year}',
            'VARIATION']
    for i, h in enumerate(hdrs):
        cl = ws.cell(4, 2 + i, h)
        cl.font = hdr_font; cl.fill = hdr_fill
        cl.alignment = hdr_align_l if i == 0 else hdr_align_c; cl.border = border_all

    for idx, (_, row) in enumerate(top.iterrows()):
        r = 5 + idx
        tm_cur = int(row.get(col_tm_cur, 0)); ta_cur = int(row.get(col_ag_cur, 0))
        tm_prv = int(row.get(col_tm_prv, 0)); ta_prv = int(row.get(col_ag_prv, 0))
        ws.cell(r, 1, idx + 1).font = data_font
        c_name = ws.cell(r, 2, str(row[client_col]))
        c_name.font = data_font; c_name.alignment = left_align; c_name.border = border_all
        for off, val in [(3, tm_cur), (4, ta_cur), (6, tm_prv), (7, ta_prv)]:
            cc = ws.cell(r, off, val); cc.font = data_font; cc.number_format = num_fmt
            cc.alignment = num_align; cc.border = border_all
        c_p_cur = ws.cell(r, 5, ta_cur / tm_cur if tm_cur > 0 else 0)
        c_p_cur.font = data_font; c_p_cur.number_format = pct_fmt; c_p_cur.alignment = num_align; c_p_cur.border = border_all
        c_p_prv = ws.cell(r, 8, ta_prv / tm_prv if tm_prv > 0 else 0)
        c_p_prv.font = data_font; c_p_prv.number_format = pct_fmt; c_p_prv.alignment = num_align; c_p_prv.border = border_all
        c_var = ws.cell(r, 9, int(ta_cur - ta_prv))
        c_var.font = data_font; c_var.number_format = num_fmt; c_var.alignment = num_align

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_competitor_xlsx(df_cible, pattern, label, client_col, unit, cur_year):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = 'Feuil1'
    u = unit.upper()
    df_cur = df_cible[df_cible['Année escale'] == cur_year]
    cf = df_cur[df_cur['Transitaire'].astype(str).str.contains(pattern, case=False, na=False)]
    portfolio = cf.groupby(client_col)['NOMBRE_TEU'].sum().reset_index()
    portfolio = portfolio.sort_values('NOMBRE_TEU', ascending=False)

    thin = Side(style='thin')
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    title_font = Font(bold=True, size=10)
    hdr_fill = PatternFill('solid', fgColor='002060')
    hdr_font = Font(bold=True, size=9, color='FFFFFF')
    hdr_align_c = Alignment(horizontal='center', vertical='center')
    hdr_align_l = Alignment(horizontal='left', vertical='center')
    data_font = Font(size=9)
    data_font_bold = Font(size=9, bold=True)
    num_align = Alignment(horizontal='center')
    left_align = Alignment(horizontal='left')
    num_fmt = '#,##0'

    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 52
    ws.column_dimensions['C'].width = 12

    ws.cell(2, 2, f'PORTEFEUILLE {label}  {cur_year} EN {u}').font = title_font

    cl = ws.cell(4, 2, 'CLIENTS')
    cl.font = hdr_font; cl.fill = hdr_fill; cl.alignment = hdr_align_l; cl.border = border_all
    cr = ws.cell(4, 3, u)
    cr.font = hdr_font; cr.fill = hdr_fill; cr.alignment = hdr_align_c; cr.border = border_all

    for idx, (_, row) in enumerate(portfolio.iterrows()):
        r = 5 + idx
        ws.cell(r, 1, idx + 1 if idx < 20 else '').font = data_font
        c_name = ws.cell(r, 2, str(row[client_col]))
        c_name.font = data_font; c_name.alignment = left_align; c_name.border = border_all
        c_val = ws.cell(r, 3, int(row['NOMBRE_TEU']))
        c_val.font = data_font; c_val.number_format = num_fmt; c_val.alignment = num_align; c_val.border = border_all

    r_total = 5 + len(portfolio)
    c_t = ws.cell(r_total, 2, 'Total général')
    c_t.font = data_font_bold; c_t.alignment = left_align; c_t.border = border_all
    c_tv = ws.cell(r_total, 3, int(portfolio['NOMBRE_TEU'].sum()))
    c_tv.font = data_font_bold; c_tv.number_format = num_fmt; c_tv.alignment = num_align; c_tv.border = border_all

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _generate_embedded_excels(sections_data, label_periode, cur_year, prev_year):
    EMBEDDED_MAP = {
        'Import Maritime': {
            'detail': ['Microsoft_Excel_Worksheet.xlsx', 'Microsoft_Excel_Worksheet1.xlsx',
                       'Microsoft_Excel_Worksheet2.xlsx', 'Microsoft_Excel_Worksheet3.xlsx'],
            'fonds': ['Microsoft_Excel_Worksheet4.xlsx', 'Microsoft_Excel_Worksheet5.xlsx',
                      'Microsoft_Excel_Worksheet6.xlsx'],
        },
        'Export Maritime': {
            'detail': ['Microsoft_Excel_Worksheet7.xlsx', 'Microsoft_Excel_Worksheet8.xlsx',
                       'Microsoft_Excel_Worksheet9.xlsx', 'Microsoft_Excel_Worksheet10.xlsx'],
            'fonds': ['Microsoft_Excel_Worksheet11.xlsx', 'Microsoft_Excel_Worksheet12.xlsx',
                      'Microsoft_Excel_Worksheet13.xlsx'],
        },
        'Import Aérien': {
            'detail': ['Microsoft_Excel_Worksheet14.xlsx', 'Microsoft_Excel_Worksheet15.xlsx',
                       'Microsoft_Excel_Worksheet16.xlsx', 'Microsoft_Excel_Worksheet17.xlsx'],
            'fonds': ['Microsoft_Excel_Worksheet18.xlsx', 'Microsoft_Excel_Worksheet19.xlsx',
                      'Microsoft_Excel_Worksheet20.xlsx'],
        },
    }
    COMPETITORS = [('CEVA', 'CEVA LOGISTICS'), ('SDMA', 'SDMA'), ('MAERSK', 'MAERSK')]

    replacements = {}
    for sec_name, sd in sections_data.items():
        if sec_name not in EMBEDDED_MAP:
            continue
        comp = sd['comparison']
        df_cible = sd['df_cible']
        ccol = sd['client_col']
        mu = sd['metric_unit']
        files = EMBEDDED_MAP[sec_name]
        cats = _categorize_clients(comp, ccol, cur_year, prev_year)

        replacements[f'ppt/embeddings/{files["detail"][0]}'] = _make_dual_xlsx(
            'CLIENTS A 100% DE PDM AVEC VOLUME EN CROISSANCE',
            'CLIENTS A 100% DE PDM AVEC VOLUME EN DECROISSANCE',
            cats['captive_up'], cats['captive_down'], ccol, label_periode, mu, cur_year, prev_year)
        replacements[f'ppt/embeddings/{files["detail"][1]}'] = _make_dual_xlsx(
            'CLIENTS ACTIFS', 'CLIENTS NON ACTIFS',
            cats['new'], cats['lost'], ccol, label_periode, mu, cur_year, prev_year)
        replacements[f'ppt/embeddings/{files["detail"][2]}'] = _make_dual_xlsx(
            'CLIENTS EN HAUSSES', 'CLIENTS EN BAISSES',
            cats['hausse'], cats['baisse'], ccol, label_periode, mu, cur_year, prev_year,
            right_extra_col='Var_Marche')
        replacements[f'ppt/embeddings/{files["detail"][3]}'] = _make_top100_xlsx(
            comp, ccol, label_periode, mu, cur_year, prev_year)
        for i, (pattern, label) in enumerate(COMPETITORS):
            replacements[f'ppt/embeddings/{files["fonds"][i]}'] = _make_competitor_xlsx(
                df_cible, pattern, label, ccol, mu, cur_year)
    return replacements


# ─────────────────────────────────────────────
#  GÉNÉRATION DU PPTX
# ─────────────────────────────────────────────
# Couleurs identiques au template
COLOR_BLUE = (0x00, 0x70, 0xC0)   # 0070C0 = positif
COLOR_RED  = (0xFF, 0x00, 0x00)   # FF0000 = négatif
COLOR_NAVY = (0x1C, 0x35, 0x5E)   # titres

def generate_pptx_report(sections_data, label_periode, is_single_month):
    from pptx import Presentation
    from pptx.util import Pt
    from pptx.dml.color import RGBColor

    # Années dynamiques
    all_years = set()
    for sec_data in sections_data.values():
        df_cible = sec_data.get('df_cible', pd.DataFrame())
        if 'Année escale' in df_cible.columns:
            valid_years = [int(y) for y in df_cible['Année escale'].dropna().unique() if int(y) > 2000]
            all_years.update(valid_years)
    current_year = int(max(all_years)) if all_years else pd.Timestamp.now().year
    previous_year = current_year - 1

    # Mois cible
    MOIS_ALL = list(MOIS_NUM_TO_NAME.values())
    MOIS_ALL_UPPER = [m.upper() for m in MOIS_ALL]
    label_words = label_periode.strip().split()
    period_month_name = None
    for word in reversed(label_words):
        if word.capitalize() in MOIS_ALL:
            period_month_name = word.capitalize(); break
        if word.upper() in MOIS_ALL_UPPER:
            period_month_name = MOIS_ALL[MOIS_ALL_UPPER.index(word.upper())]; break
    if period_month_name is None:
        period_month_name = MOIS_ALL[-1]

    if not os.path.isfile(TEMPLATE_FILE):
        available = [f for f in os.listdir(os.path.dirname(TEMPLATE_FILE)) if f.endswith('.pptx')]
        raise FileNotFoundError(
            f"Template PPTX introuvable : {TEMPLATE_FILE}\n"
            f"Fichiers .pptx disponibles : {available if available else 'Aucun'}"
        )

    out_prs = Presentation(TEMPLATE_FILE)

    # ───────── Helpers texte ─────────
    def _set_paragraph_text(para, text):
        if para.runs:
            para.runs[0].text = text
            for r in para.runs[1:]:
                r.text = ""
        else:
            para.text = text

    def replace_period_in_text(text):
        if not text or not isinstance(text, str):
            return text
        result = text
        # Plage large pour gérer n'importe quelle année cible (ex: 2035 vs template 2025)
        cur_2 = str(current_year)[-2:]
        prv_2 = str(previous_year)[-2:]
        for yr_offset in range(1, 25):
            old_cur = current_year - yr_offset
            old_prv = old_cur - 1
            if old_cur == previous_year:
                continue
            result = result.replace(f'{old_prv}/{old_cur}', f'{previous_year}/{current_year}')
            result = result.replace(f'{old_prv}-{old_cur}', f'{previous_year}-{current_year}')
            result = result.replace(str(old_cur), str(current_year))
            result = result.replace(str(old_prv), str(previous_year))
            # Format court "PDM 26" / "PDM 25" présent dans certains en-têtes
            old_cur_2 = str(old_cur)[-2:]
            old_prv_2 = str(old_prv)[-2:]
            if old_cur_2 != cur_2:
                result = result.replace(f'PDM {old_cur_2}', f'PDM {cur_2}')
            if old_prv_2 != prv_2:
                result = result.replace(f'PDM {old_prv_2}', f'PDM {prv_2}')

        period_upper = period_month_name.upper()
        period_title = period_month_name
        cumul_prefixes_upper = ['CUMUL A FIN ', 'CUMUL À FIN ', 'CUMUL AU MOIS DE ', 'CUMUL ']
        cumul_prefixes_title = ['Cumul a fin ', 'Cumul à fin ', 'Cumul au mois de ', 'Cumul ']
        for mu, mt in zip(MOIS_ALL_UPPER, MOIS_ALL):
            for prefix_u in cumul_prefixes_upper:
                result = result.replace(f'{prefix_u}{mu}', f'{prefix_u}{period_upper}')
            for prefix_t in cumul_prefixes_title:
                result = result.replace(f'{prefix_t}{mt}', f'{prefix_t}{period_title}')

        # Remplacement des noms de mois COMPLETS d'abord
        for mu, mt in zip(MOIS_ALL_UPPER, MOIS_ALL):
            if mu != period_upper:
                result = result.replace(mu, period_upper)
            if mt != period_title:
                result = result.replace(mt, period_title)

        # Puis remplacement des ABRÉVIATIONS (Janv, Févr, Sept, etc.)
        # On le fait après les noms complets pour ne pas casser "Janvier" en "Marsier"
        period_abbrev = ABBREV_BY_FULL.get(period_month_name, period_month_name)
        period_abbrev_upper = period_abbrev.upper()
        for full, abbrev in ABBREV_BY_FULL.items():
            if abbrev == period_abbrev:
                continue
            au = abbrev.upper()
            # On évite de toucher aux abréviations qui sont déjà préfixe de la pleine
            # forme (or les pleines formes ont déjà été remplacées juste avant)
            result = result.replace(au, period_abbrev_upper)
            result = result.replace(abbrev, period_abbrev)
        return result

    def _apply_to_paragraph(para):
        """
        Remplace les noms de mois et années au niveau du paragraphe complet
        (utile quand un mot est fragmenté entre plusieurs runs).
        Préserve la mise en forme de la première run.
        """
        if not para.runs:
            if para.text:
                new = replace_period_in_text(para.text)
                if new != para.text:
                    para.text = new
            return
        full = "".join(r.text for r in para.runs)
        new = replace_period_in_text(full)
        if new == full:
            return
        # Réécriture : on met tout dans la première run, on vide les autres
        para.runs[0].text = new
        for r in para.runs[1:]:
            r.text = ""

    def apply_period_to_shape_recursive(shape):
        try:
            if shape.shape_type == 6:
                for sub in shape.shapes:
                    apply_period_to_shape_recursive(sub)
                return
            if shape.has_table:
                tbl = shape.table
                for row in tbl.rows:
                    for cell in row.cells:
                        for para in cell.text_frame.paragraphs:
                            _apply_to_paragraph(para)
                return
            if hasattr(shape, 'text_frame') and shape.text_frame:
                for para in shape.text_frame.paragraphs:
                    _apply_to_paragraph(para)
        except Exception:
            pass

    def find_table(slide):
        for sh in slide.shapes:
            if sh.has_table:
                return sh.table
        return None

    # ───────── Helpers formatage avancé (couleurs) ─────────
    def _capture_para_props(para):
        """Retourne (size, font_name) de la première run d'un paragraphe."""
        size = None
        font_name = None
        if para.runs:
            f = para.runs[0].font
            if f.size: size = f.size
            if f.name: font_name = f.name
        return size, font_name

    def _add_run(para, text, *, bold=False, color=None, size=None, font_name=None):
        r = para.add_run()
        r.text = text
        if bold:
            r.font.bold = True
        if size:
            r.font.size = size
        if font_name:
            r.font.name = font_name
        if color:
            r.font.color.rgb = RGBColor(*color)
        return r

    def _fmt_signed(val, unit):
        s = f"{abs(int(val)):,}".replace(",", " ")
        sign = '+' if int(val) >= 0 else '-'
        return f"{sign} {s} {unit}"

    def _value_color(val):
        return COLOR_BLUE if int(val) >= 0 else COLOR_RED

    def _set_summary_rect_formatted(shape, label, value, unit):
        """
        Rectangle de résumé : 'XX Clients à 100 % de PDM   + 212 Teus'
        - label en regular
        - value en gras + couleur (bleu si +, rouge si -)
        """
        tf = shape.text_frame
        size, font_name = _capture_para_props(tf.paragraphs[0]) if tf.paragraphs else (Pt(12), None)
        size = size or Pt(12)
        tf.clear()
        p = tf.paragraphs[0]
        _add_run(p, f"{label}  ", size=size, font_name=font_name)
        _add_run(p, _fmt_signed(value, unit), bold=True, color=_value_color(value),
                 size=size, font_name=font_name)

    def _set_detail_rect_formatted(shape, lines, unit):
        """
        Rectangle de détail multi-lignes :
        lines = [(count, label, value), ...]
        - count : gras
        - label : regular
        - value : gras + couleur
        """
        tf = shape.text_frame
        size, font_name = _capture_para_props(tf.paragraphs[0]) if tf.paragraphs else (Pt(11), None)
        size = size or Pt(11)
        tf.clear()
        for i, (count, label, value) in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            _add_run(p, f"{int(count):02d} ", bold=True, size=size, font_name=font_name)
            _add_run(p, f"{label}  ", size=size, font_name=font_name)
            _add_run(p, _fmt_signed(value, unit), bold=True, color=_value_color(value),
                     size=size, font_name=font_name)

    # ───────── Slide Market Overview ─────────
    def fill_market_overview(slide, sections_data, current_year, previous_year, label_per, is_single):
        total_marche_cur = total_agl_cur = 0
        total_marche_prv = total_agl_prv = 0
        col_tm_cur = f'Total_Marche_{current_year}'
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_tm_prv = f'Total_Marche_{previous_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'
        for sec_name, sd in sections_data.items():
            comp = sd['comparison']
            if col_tm_cur in comp.columns: total_marche_cur += int(comp[col_tm_cur].sum())
            if col_ag_cur in comp.columns: total_agl_cur += int(comp[col_ag_cur].sum())
            if not is_single and col_tm_prv in comp.columns: total_marche_prv += int(comp[col_tm_prv].sum())
            if not is_single and col_ag_prv in comp.columns: total_agl_prv += int(comp[col_ag_prv].sum())
        pdm_cur = f"{round(total_agl_cur / total_marche_cur * 100)}%" if total_marche_cur > 0 else "0%"
        pdm_prv = f"{round(total_agl_prv / total_marche_prv * 100)}%" if total_marche_prv > 0 else "0%"
        var_marche = total_marche_cur - total_marche_prv
        var_agl = total_agl_cur - total_agl_prv
        def _fmt(v): return f"{int(v):,}".replace(",", " ")
        tbl = find_table(slide)
        if tbl is not None:
            vals = [_fmt(total_marche_cur), _fmt(total_agl_cur), pdm_cur,
                    _fmt(total_marche_prv), _fmt(total_agl_prv), pdm_prv,
                    _fmt(var_marche), _fmt(var_agl)]
            data_row_idx = 1 if len(tbl.rows) > 1 else 0
            for c_idx in range(min(len(vals), len(tbl.columns))):
                try:
                    cell = tbl.cell(data_row_idx, c_idx)
                    _set_paragraph_text(cell.text_frame.paragraphs[0], vals[c_idx])
                except Exception:
                    pass

    def fill_synthese_table(slide, comp, metric_unit, label_per, is_single, current_year, previous_year):
        tbl = find_table(slide)
        if tbl is None: return
        col_tm_cur = f'Total_Marche_{current_year}'
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_tm_prv = f'Total_Marche_{previous_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'
        tm_cur = int(comp[col_tm_cur].sum()) if col_tm_cur in comp.columns else 0
        ta_cur = int(comp[col_ag_cur].sum()) if col_ag_cur in comp.columns else 0
        pdm_cur = f"{round(ta_cur/tm_cur*100)}%" if tm_cur > 0 else "0%"
        tm_prv = int(comp[col_tm_prv].sum()) if (not is_single and col_tm_prv in comp.columns) else 0
        ta_prv = int(comp[col_ag_prv].sum()) if (not is_single and col_ag_prv in comp.columns) else 0
        pdm_prv = f"{round(ta_prv/tm_prv*100)}%" if tm_prv > 0 else "0%"
        var_m = tm_cur - tm_prv
        var_a = ta_cur - ta_prv
        vals = [f"{tm_cur:,}".replace(",", " "), f"{ta_cur:,}".replace(",", " "), pdm_cur,
                f"{tm_prv:,}".replace(",", " "), f"{ta_prv:,}".replace(",", " "), pdm_prv,
                f"{var_m:,}".replace(",", " "), f"{var_a:,}".replace(",", " ")]
        for c in range(min(len(vals), len(tbl.columns))):
            try:
                cell = tbl.cell(1, c)
                _set_paragraph_text(cell.text_frame.paragraphs[0], vals[c])
            except Exception:
                pass

    def fill_top20_table(slide, comp, df_cible, client_col, metric_unit, is_single,
                          current_year, previous_year):
        tbl = find_table(slide)
        if tbl is None: return
        col_tm_cur = f'Total_Marche_{current_year}'
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'
        df_c_cur = df_cible[df_cible['Année escale'] == current_year]
        if df_c_cur.empty: return

        dg = df_c_cur.groupby([client_col, 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
        do = dg[~dg['Transitaire'].astype(str).str.contains('AFRICA GLOBAL', case=False, na=False)]
        if do.empty:
            tc = pd.DataFrame(columns=[client_col, '1ER_CONC', 'TEUS_CONC'])
        else:
            tc = _select_primary_competitor_rows(do, client_col).rename(
                columns={'Transitaire': '1ER_CONC', 'NOMBRE_TEU': 'TEUS_CONC'})
        merged = pd.merge(comp, tc[[client_col, '1ER_CONC', 'TEUS_CONC']],
                          on=client_col, how='left').fillna(0)
        merged['VOL_CONC'] = merged[col_tm_cur] - merged[col_ag_cur]
        mask_non_apure = merged['1ER_CONC'].apply(_is_non_apure)
        merged.loc[mask_non_apure & (merged['TEUS_CONC'] <= 0), 'TEUS_CONC'] = \
            merged.loc[mask_non_apure & (merged['TEUS_CONC'] <= 0), 'VOL_CONC']
        if not is_single and col_ag_prv in merged.columns:
            merged['Variation'] = merged[col_ag_cur] - merged[col_ag_prv]
            # FIX: filtre PDM AGL <= 50% appliqué partout
            merged['_PDM_cur'] = merged.apply(
                lambda r: r[col_ag_cur] / r[col_tm_cur] * 100 if r[col_tm_cur] > 0 else 0, axis=1)
            merged = merged[(merged['Variation'] < 0) & (merged['_PDM_cur'] <= 50)]
        merged = merged.sort_values('VOL_CONC', ascending=False).head(20)

        for i, (_, row) in enumerate(merged.iterrows()):
            if i >= 20: break
            r_idx = i + 1
            tm = int(row[col_tm_cur]); ta = int(row[col_ag_cur])
            pdm = f"{round(ta/tm*100)}%" if tm > 0 else "0%"
            vc = int(row['VOL_CONC'])
            conc_name = str(row.get('1ER_CONC', ''))
            if conc_name in ('0', '0.0', ''): conc_name = 'NON APURE'
            tc_val = int(row.get('TEUS_CONC', 0))
            pdm_c = f"{round(tc_val/tm*100)}%" if tm > 0 and tc_val > 0 else "0%"
            vals = [str(i+1), str(row[client_col]), str(tm), str(ta), pdm, str(vc),
                    conc_name, str(tc_val), pdm_c]
            for c in range(min(len(vals), len(tbl.columns))):
                if r_idx < len(tbl.rows):
                    try:
                        cell = tbl.cell(r_idx, c)
                        _set_paragraph_text(cell.text_frame.paragraphs[0], vals[c])
                    except Exception:
                        pass
        for r_idx in range(len(merged) + 1, len(tbl.rows)):
            for c in range(len(tbl.columns)):
                try:
                    cell = tbl.cell(r_idx, c)
                    _set_paragraph_text(cell.text_frame.paragraphs[0], "")
                except Exception:
                    pass

    def update_comments_text(slide, comp, metric_unit, client_col, is_single,
                              current_year, previous_year):
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'
        col_tm_cur = f'Total_Marche_{current_year}'
        col_tm_prv = f'Total_Marche_{previous_year}'
        if is_single or col_ag_prv not in comp.columns:
            return
        comp_c = comp.copy()
        comp_c['Variation'] = comp_c[col_ag_cur] - comp_c[col_ag_prv]
        comp_c['Var_Marche'] = comp_c[col_tm_cur] - comp_c[col_tm_prv]
        unit = metric_unit
        comp_c = comp_c[~comp_c[client_col].apply(_is_excluded_client)]
        declining = comp_c[comp_c['Variation'] < 0].copy()
        total_loss = int(declining['Variation'].sum())
        top10 = declining.nsmallest(10, 'Variation')

        # Trouver la zone COMMENTAIRES
        best_sh = None; best_len = 0
        for sh in slide.shapes:
            if sh.shape_type == 17 and hasattr(sh, 'text'):
                if len(sh.text) > best_len and 'notons' in sh.text.lower():
                    best_len = len(sh.text); best_sh = sh
        if best_sh is None:
            for sh in slide.shapes:
                if sh.shape_type == 17 and hasattr(sh, 'text') and len(sh.text) > 100:
                    best_sh = sh; break
        if best_sh is None:
            return

        tf = best_sh.text_frame
        size, font_name = _capture_para_props(tf.paragraphs[0]) if tf.paragraphs else (Pt(12), None)
        size = size or Pt(12)
        tf.clear()

        # Ligne 1 : intro avec valeur en rouge
        loss_str = f"{abs(total_loss):,}".replace(",", " ")
        p0 = tf.paragraphs[0]
        _add_run(p0, "Nous notons que les Volumes d'AGL sont en baisse ( ", size=size, font_name=font_name)
        _add_run(p0, f"{loss_str} {unit}", bold=True, color=COLOR_RED, size=size, font_name=font_name)
        _add_run(p0, ").", size=size, font_name=font_name)

        # Ligne 2
        p1 = tf.add_paragraph()
        _add_run(p1, "Les 10 Principaux Acteurs de cette Baisse sont:", size=size, font_name=font_name)

        # Ligne vide
        tf.add_paragraph()

        # Top 10 clients : nom + variation AGL en rouge + (marché direction Hausse/Baisse)
        for _, row in top10.iterrows():
            agl_loss = abs(int(row['Variation']))
            market_var = int(row['Var_Marche'])
            market_dir = "Hausse" if market_var >= 0 else "Baisse"
            market_color = COLOR_BLUE if market_var >= 0 else COLOR_RED
            name = str(row[client_col])[:40]
            p = tf.add_paragraph()
            _add_run(p, f"{name}  ", size=size, font_name=font_name)
            _add_run(p, f"- {agl_loss:,} {unit}".replace(",", " "),
                     bold=True, color=COLOR_RED, size=size, font_name=font_name)
            _add_run(p, "  ( ", size=size, font_name=font_name)
            _add_run(p, f"{market_dir} de {abs(market_var):,} {unit}".replace(",", " "),
                     bold=True, color=market_color, size=size, font_name=font_name)
            _add_run(p, " )", size=size, font_name=font_name)

    def update_analyse_group(slide, comp, mu, is_single, current_year, previous_year):
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'
        col_tm_cur = f'Total_Marche_{current_year}'
        col_tm_prv = f'Total_Marche_{previous_year}'
        if is_single: return
        comp_a = comp.copy()
        comp_a['Variation'] = comp_a[col_ag_cur] - comp_a[col_ag_prv]
        comp_a = comp_a[(comp_a[col_ag_cur] > 0) | (comp_a[col_ag_prv] > 0)]
        comp_a['PDM_r_cur'] = comp_a.apply(lambda r: r[col_ag_cur] / r[col_tm_cur] if r[col_tm_cur] > 0 else 0, axis=1)
        comp_a['PDM_r_prv'] = comp_a.apply(lambda r: r[col_ag_prv] / r[col_tm_prv] if r[col_tm_prv] > 0 else 0, axis=1)
        active_both = comp_a[(comp_a[col_tm_prv] > 0) & (comp_a[col_tm_cur] > 0)]
        captive = active_both[(active_both['PDM_r_prv'] >= 0.95) & (active_both['PDM_r_cur'] >= 0.95) &
                              (active_both[col_ag_prv] > 0) & (active_both[col_ag_cur] > 0)]
        non_captive = active_both[~active_both.index.isin(captive.index)]
        actifs = comp_a[(comp_a[col_tm_prv] == 0) & (comp_a[col_ag_cur] > 0)]
        inactifs = comp_a[(comp_a[col_tm_cur] == 0) & (comp_a[col_ag_prv] > 0)]
        pdm100_up = captive[captive['Variation'] >= 0]
        pdm100_down = captive[captive['Variation'] < 0]
        others_up = non_captive[non_captive['Variation'] > 0]
        others_down = non_captive[non_captive['Variation'] < 0]
        n_pdm100 = len(pdm100_up) + len(pdm100_down)
        total_pdm100 = int(pdm100_up['Variation'].sum() + pdm100_down['Variation'].sum())
        n_actifs, vol_actifs = len(actifs), int(actifs['Variation'].sum())
        n_inactifs, vol_inactifs = len(inactifs), int(inactifs['Variation'].sum())
        total_ai = vol_actifs + vol_inactifs
        total_autres = int(others_up['Variation'].sum() + others_down['Variation'].sum())

        def _get_texts_recursive(group):
            texts = []
            for sh in group.shapes:
                if sh.shape_type == 6:
                    texts.extend(_get_texts_recursive(sh))
                elif hasattr(sh, 'text') and sh.text.strip():
                    texts.append(sh.text)
            return texts

        analyse_group = None
        for sh in slide.shapes:
            if sh.shape_type == 6:
                texts = _get_texts_recursive(sh)
                if any('100 %' in t for t in texts):
                    analyse_group = sh; break
        if not analyse_group:
            return

        for sub in analyse_group.shapes:
            if sub.shape_type != 6: continue
            sub_texts = _get_texts_recursive(sub)
            combined = ' '.join(sub_texts)
            rects = [sh for sh in sub.shapes if sh.shape_type == 1 and hasattr(sh, 'text') and sh.text.strip()]
            if len(rects) < 2: continue
            rects.sort(key=lambda s: len(s.text))
            summary_sh, detail_sh = rects[0], rects[1]
            if '100 %' in combined:
                _set_summary_rect_formatted(summary_sh,
                    f"{n_pdm100} Clients à 100 % de PDM", total_pdm100, mu)
                _set_detail_rect_formatted(detail_sh, [
                    (len(pdm100_up),   "Clients qui ont une croissance", int(pdm100_up['Variation'].sum())),
                    (len(pdm100_down), "Clients qui ont une baisse",      int(pdm100_down['Variation'].sum())),
                ], mu)
            elif 'actifs' in combined.lower() and 'inactifs' in combined.lower():
                _set_summary_rect_formatted(summary_sh,
                    "Clients Actifs et Inactifs", total_ai, mu)
                _set_detail_rect_formatted(detail_sh, [
                    (n_actifs,   f"Clients Actifs en {current_year}",   vol_actifs),
                    (n_inactifs, f"Clients Inactifs en {current_year}", vol_inactifs),
                ], mu)
            else:
                _set_summary_rect_formatted(summary_sh,
                    "Autres Clients en Hausse et en Baisse", total_autres, mu)
                _set_detail_rect_formatted(detail_sh, [
                    (len(others_up),   "Clients qui ont une Hausse", int(others_up['Variation'].sum())),
                    (len(others_down), "Clients qui ont une baisse", int(others_down['Variation'].sum())),
                ], mu)

        # Texte "POUR RAPPEL" : Actifs/Inactifs avec années dynamiques
        # Le rectangle est parfois imbriqué dans un groupe — recherche récursive
        def _find_rappel_recursive(shape):
            try:
                if shape.shape_type == 6:
                    for sub in shape.shapes:
                        found = _find_rappel_recursive(sub)
                        if found is not None:
                            return found
                    return None
                if hasattr(shape, 'text') and 'travaillé en' in shape.text.lower():
                    return shape
            except Exception:
                pass
            return None

        rappel_sh = None
        for sh in slide.shapes:
            rappel_sh = _find_rappel_recursive(sh)
            if rappel_sh is not None:
                break

        if rappel_sh is not None:
            tf = rappel_sh.text_frame
            size, font_name = _capture_para_props(tf.paragraphs[0]) if tf.paragraphs else (Pt(11), None)
            size = size or Pt(11)
            tf.clear()
            p0 = tf.paragraphs[0]
            _add_run(p0, "Actifs ", bold=True, size=size, font_name=font_name)
            _add_run(p0, f"  = travaillé en {current_year} et pas en {previous_year}.",
                     size=size, font_name=font_name)
            p1 = tf.add_paragraph()
            _add_run(p1, "Inactifs ", bold=True, size=size, font_name=font_name)
            _add_run(p1, f"= pas travaillé en {current_year} et travaillé en {previous_year}",
                     size=size, font_name=font_name)

    # ───────── Application ─────────
    slides = list(out_prs.slides)

    for slide in slides:
        for sh in slide.shapes:
            apply_period_to_shape_recursive(sh)

    if len(slides) > 1:
        fill_market_overview(slides[1], sections_data, current_year, previous_year, label_periode, is_single_month)

    section_map = {
        'Import Maritime':  (2, 3, 4),
        'Export Maritime':  (7, 8, 9),
        'Import Aérien':    (12, 13, 14),
    }
    for sec_name, (sep_idx, synth_idx, top20_idx) in section_map.items():
        if sec_name not in sections_data: continue
        sd = sections_data[sec_name]
        comp = sd['comparison']
        df_cible = sd['df_cible']
        ccol = sd['client_col']
        mu = sd['metric_unit']
        sec_single = sd.get('is_single', is_single_month)

        if synth_idx < len(slides):
            synth_slide = slides[synth_idx]
            fill_synthese_table(synth_slide, comp, mu, label_periode, sec_single, current_year, previous_year)
            update_comments_text(synth_slide, comp, mu, ccol, sec_single, current_year, previous_year)
            update_analyse_group(synth_slide, comp, mu, sec_single, current_year, previous_year)

        if top20_idx < len(slides):
            fill_top20_table(slides[top20_idx], comp, df_cible, ccol, mu, sec_single,
                              current_year, previous_year)

    output = io.BytesIO()
    out_prs.save(output)

    if not is_single_month:
        import zipfile
        excel_replacements = _generate_embedded_excels(sections_data, label_periode, current_year, previous_year)
        if excel_replacements:
            output.seek(0)
            final = io.BytesIO()
            with zipfile.ZipFile(output, 'r') as zin:
                with zipfile.ZipFile(final, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        if item.filename in excel_replacements:
                            zout.writestr(item, excel_replacements[item.filename])
                        else:
                            zout.writestr(item, zin.read(item.filename))
            final.seek(0)
            return final.getvalue()

    output.seek(0)
    return output.getvalue()


# ─────────────────────────────────────────────
#  TRAITEMENT DES FICHIERS RAPPORT
# ─────────────────────────────────────────────
def scan_uploaded_file(file_obj):
    """
    Scanne un fichier Excel et retourne les métadonnées :
    {sheet, dtype, columns_mapping, df_raw, mois_dispo, annees, flux_dispo,
     pays_dispo, conditionnement_dispo}
    """
    xls = pd.ExcelFile(file_obj)
    sheet_names = xls.sheet_names

    best_sheet, best_score, dtype = sheet_names[0], -1, 'maritime'
    for s in sheet_names:
        df_tmp = pd.read_excel(file_obj, sheet_name=s, nrows=5)
        up = [str(c).upper() for c in df_tmp.columns]
        score_mar = sum(1 for al in EXPECTED_COLS.values() if any(a in up for a in al))
        score_aer = sum(1 for al in EXPECTED_COLS_AERIEN.values() if any(a in up for a in al))
        if score_mar >= score_aer and score_mar > best_score:
            best_score, best_sheet, dtype = score_mar, s, 'maritime'
        if score_aer > score_mar and score_aer > best_score:
            best_score, best_sheet, dtype = score_aer, s, 'aerien'
        if score_mar == score_aer and score_mar > best_score:
            dt = detect_data_type(df_tmp.columns.tolist())
            best_score, best_sheet, dtype = score_mar, s, dt

    expected = EXPECTED_COLS_AERIEN if dtype == 'aerien' else EXPECTED_COLS
    optional = OPTIONAL_COLS_AERIEN if dtype == 'aerien' else OPTIONAL_COLS

    df_raw = pd.read_excel(file_obj, sheet_name=best_sheet)
    upper_cols = {str(c).upper(): c for c in df_raw.columns}
    mapping = {}
    for std_col, aliases in {**expected, **optional}.items():
        found = next((upper_cols[a] for a in aliases if a in upper_cols), None)
        if found:
            mapping[std_col] = found

    missing = [k for k in expected if k not in mapping]
    if missing:
        return {'error': f"Colonnes manquantes : {', '.join(missing)}",
                'sheet': best_sheet, 'dtype': dtype}

    inverse = {v: k for k, v in mapping.items()}
    df = df_raw.rename(columns=inverse)
    df['NOMBRE_TEU'] = clean_numeric_col(df['NOMBRE_TEU'])
    df['Année escale'] = clean_numeric_col(df['Année escale']).astype(int)
    df['Mois escale'] = normalize_mois_column(df['Mois escale'])
    df = df[df['Année escale'] >= 2000].copy()

    mois_dispo = sorted(
        [m for m in df['Mois escale'].dropna().unique() if str(m) not in ('nan', 'None', '')],
        key=lambda m: list(MOIS_NUM_TO_NAME.values()).index(str(m)) if str(m) in MOIS_NUM_TO_NAME.values() else 99
    )
    annees = sorted([int(a) for a in df['Année escale'].dropna().unique() if int(a) >= 2000])

    flux_vals = df['I_IMP_E_EXP'].dropna().astype(str).str.upper().str.strip().unique()
    flux_dispo = []
    if any(str(v).startswith('I') for v in flux_vals): flux_dispo.append('Import')
    if any(str(v).startswith('E') for v in flux_vals): flux_dispo.append('Export')

    pays_set = set()
    for col in ['Pays de livraison', 'Pays de prise en charge']:
        if col in df.columns:
            pays_set.update(df[col].dropna().astype(str).str.strip().unique())
    pays_dispo = sorted(p for p in pays_set if p and p.upper() not in ('NAN', ''))

    cond_dispo = []
    if 'Conditionnement' in df.columns:
        cond_dispo = sorted(
            v for v in df['Conditionnement'].dropna().astype(str).str.strip().unique()
            if v and v.upper() not in ('NAN', '')
        )

    return {
        'sheet': best_sheet, 'dtype': dtype, 'df': df,
        'mois_dispo': mois_dispo, 'annees': annees, 'flux_dispo': flux_dispo,
        'pays_dispo': pays_dispo, 'cond_dispo': cond_dispo,
    }


def build_section_from_filtered_df(df, dtype, flux_letter, period_mode, period_month, log_func):
    """
    À partir d'un DataFrame déjà filtré (pays/marchandise),
    construit la section pour un flux donné.
    period_mode : 'YTD' ou 'MOIS'
    period_month : nom du mois (str)
    """
    mois_dict_rpt = {n: i for i, n in MOIS_NUM_TO_NAME.items()}
    flux_col = df['I_IMP_E_EXP'].fillna('').astype(str).str.upper().str.strip()
    df_flux = df[flux_col.str.startswith(flux_letter)].copy()
    if df_flux.empty:
        return None

    flux_name = "Import" if flux_letter == 'I' else "Export"
    dtype_name = "Aérien" if dtype == 'aerien' else "Maritime"
    sec_name = f"{flux_name} {dtype_name}"
    ccol = "Destinataire" if flux_letter == 'I' else "Chargeur"
    if ccol not in df_flux.columns:
        alt = "Chargeur" if ccol == "Destinataire" else "Destinataire"
        ccol = alt if alt in df_flux.columns else None
        if ccol is None:
            log_func(f"{sec_name} : colonne client introuvable", "warn")
            return None

    mois_num_max = mois_dict_rpt.get(period_month, 1)
    if period_mode == 'YTD':
        valid_m = [m for m in df_flux['Mois escale'].dropna().unique()
                   if mois_dict_rpt.get(str(m), 0) <= mois_num_max]
        df_cible = df_flux[df_flux['Mois escale'].isin(valid_m)].copy()
    else:
        df_cible = df_flux[df_flux['Mois escale'] == period_month].copy()

    if df_cible.empty:
        return None

    annees = sorted([int(y) for y in df_cible['Année escale'].dropna().unique() if int(y) >= 2000])
    if not annees:
        return None
    cur_year = int(max(annees))
    prv_year = cur_year - 1
    is_single = len(annees) == 1

    res_cur = get_stats_annee(df_cible[df_cible['Année escale'] == cur_year], cur_year, ccol)
    if not is_single:
        res_prv = get_stats_annee(df_cible[df_cible['Année escale'] == prv_year], prv_year, ccol)
        comp = pd.merge(res_prv, res_cur, on=ccol, how='outer').fillna(0)
    else:
        comp = res_cur.copy()
        comp[f'AGL_Volume_{prv_year}']   = 0
        comp[f'Total_Marche_{prv_year}'] = 0
        comp[f'PDM_{prv_year}']          = 0

    metric_unit = 'Kg' if dtype == 'aerien' else 'Teus'
    return sec_name, {
        'comparison': comp, 'res_2026': res_cur, 'df_cible': df_cible,
        'client_col': ccol, 'metric_unit': metric_unit, 'data_type': dtype,
        'is_single': is_single,
    }


# ─────────────────────────────────────────────
#  UI STREAMLIT — PAGE RAPPORT PPTX STANDALONE
# ─────────────────────────────────────────────
def render_pptx_page(st):
    """Page Streamlit dédiée à la génération du rapport PPTX."""
    st.markdown("""
    <div class="agl-topbar">
      <div>
        <div class="agl-topbar-title">Génération du Rapport PPTX</div>
        <div class="agl-topbar-subtitle">Business Insight — Côte d'Ivoire</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="step-header">ÉTAPE 1 — CHARGEMENT DES FICHIERS RAPPORT</div>',
                unsafe_allow_html=True)

    files = st.file_uploader(
        "Fichiers Excel rapport (Import/Export, Maritime/Aérien)",
        type=['xlsx'], accept_multiple_files=True, key="pptx_page_uploader"
    )

    if not files:
        st.info("Veuillez charger un ou plusieurs fichiers Excel pour démarrer.")
        return

    # ── ÉTAPE 2 : Auto-détection ────────────────────────────────────────────
    st.markdown('<div class="step-header">ÉTAPE 2 — AUTO-DÉTECTION DES FICHIERS</div>',
                unsafe_allow_html=True)

    if 'pptx_page_scans' not in st.session_state:
        st.session_state['pptx_page_scans'] = {}

    # Re-scan si la liste change
    current_keys = [f"{f.name}_{f.size}" for f in files]
    if list(st.session_state['pptx_page_scans'].keys()) != current_keys:
        st.session_state['pptx_page_scans'] = {}
        with st.spinner("Analyse des fichiers..."):
            for f, key in zip(files, current_keys):
                try:
                    f.seek(0)
                    st.session_state['pptx_page_scans'][key] = (f.name, scan_uploaded_file(f))
                except Exception as e:
                    st.session_state['pptx_page_scans'][key] = (f.name, {'error': str(e)})

    scans = st.session_state['pptx_page_scans']
    all_pays_maritime = set()
    all_pays_aerien = set()
    all_cond = set()
    all_mois = set()
    all_annees = set()
    has_valid = False
    has_aerien = False

    for key, (fname, scan) in scans.items():
        if 'error' in scan:
            st.markdown(f"<div class='log-box log-box-err'>[ERREUR] <b>{fname}</b> : {scan['error']}</div>",
                        unsafe_allow_html=True)
            continue
        has_valid = True
        if scan['dtype'] == 'aerien':
            has_aerien = True
            all_pays_aerien.update(scan['pays_dispo'])
        else:
            all_pays_maritime.update(scan['pays_dispo'])
        all_cond.update(scan['cond_dispo'])
        all_mois.update(scan['mois_dispo'])
        all_annees.update(scan['annees'])
        type_label = "AÉRIEN" if scan['dtype'] == 'aerien' else "MARITIME"
        st.markdown(
            f"<div class='log-box log-box-ok'><b>{fname}</b> &middot; "
            f"Type: <b>{type_label}</b> &middot; Feuille: <code>{scan['sheet']}</code> &middot; "
            f"{len(scan['df']):,} lignes &middot; Mois: {', '.join(map(str, scan['mois_dispo']))} &middot; "
            f"Années: {', '.join(map(str, scan['annees']))} &middot; "
            f"Flux: {', '.join(scan['flux_dispo'])}</div>",
            unsafe_allow_html=True
        )

    if not has_valid:
        st.error("Aucun fichier valide. Vérifiez les colonnes attendues.")
        return

    # ── ÉTAPE 3 : Filtres ───────────────────────────────────────────────────
    st.markdown('<div class="step-header">ÉTAPE 3 — FILTRES POUR LA GÉNÉRATION</div>',
                unsafe_allow_html=True)

    mois_sorted = sorted(
        all_mois,
        key=lambda m: list(MOIS_NUM_TO_NAME.values()).index(str(m)) if str(m) in MOIS_NUM_TO_NAME.values() else 99
    )

    fc1, fc2, fc3, fc4 = st.columns([1, 1, 2, 2])
    with fc1:
        period_mode = st.radio("TYPE D'ANALYSE",
            ["Mois Spécifique", "Cumul (YTD)"],
            index=1 if len(mois_sorted) > 1 else 0,
            key="pptx_period_mode")
    with fc2:
        if mois_sorted:
            default_idx = len(mois_sorted) - 1
            period_month = st.selectbox("PÉRIODE ANALYSÉE",
                mois_sorted, index=default_idx, key="pptx_period_month")
        else:
            period_month = None
    with fc3:
        flux_filter = st.multiselect("FLUX À INCLURE",
            options=["Import", "Export"], default=["Import", "Export"],
            key="pptx_flux_filter")
    with fc4:
        dtype_filter = st.multiselect("TYPE DE DONNÉES",
            options=["Maritime", "Aérien"], default=["Maritime", "Aérien"],
            key="pptx_dtype_filter")

    fc5, fc6 = st.columns(2)
    with fc5:
        pays_filter_maritime = st.multiselect(
            "PAYS — MARITIME (vide = tous, défaut = Côte d'Ivoire)",
            options=sorted(all_pays_maritime),
            default=[p for p in sorted(all_pays_maritime) if 'IVOIRE' in p.upper()],
            key="pptx_pays_filter_mar",
            help="Pays de livraison ou de prise en charge — appliqué uniquement aux fichiers maritimes."
        )
    with fc6:
        cond_filter = st.multiselect(
            "CONDITIONNEMENT / MARCHANDISE (vide = tous)",
            options=sorted(all_cond), default=[],
            key="pptx_cond_filter"
        )

    pays_filter_aerien = []
    if has_aerien:
        pays_filter_aerien = st.multiselect(
            "AÉROPORT — AÉRIEN (vide = tous)",
            options=sorted(all_pays_aerien),
            default=[],
            key="pptx_pays_filter_aer",
            help="Aéroport de chargement ou déchargement — appliqué uniquement aux fichiers aériens."
        )

    # ── ÉTAPE 4 : Génération ────────────────────────────────────────────────
    st.markdown('<div class="step-header">ÉTAPE 4 — GÉNÉRATION DU RAPPORT</div>',
                unsafe_allow_html=True)

    if st.button("GÉNÉRER LE RAPPORT PPTX", type="primary", key="pptx_page_generate"):
        log_container = st.container()
        logs = []
        def _log(msg, level="info"):
            logs.append((level, msg))
            color = {"info": "#5a6a8a", "ok": "#1a7f3c", "warn": "#b07a16", "err": "#b22222"}.get(level, "#5a6a8a")
            prefix = {"info": "[INFO]", "ok": "[OK]", "warn": "[WARN]", "err": "[ERR]"}.get(level, "[INFO]")
            with log_container:
                st.markdown(f"<div style='font-size:0.82rem;color:{color};padding:2px 0;'>{prefix} {msg}</div>",
                            unsafe_allow_html=True)

        try:
            sections = {}
            period_mode_key = 'YTD' if 'YTD' in period_mode or 'Cumul' in period_mode else 'MOIS'
            label_periode = f"YTD {period_month}" if period_mode_key == 'YTD' else str(period_month)

            for key, (fname, scan) in scans.items():
                if 'error' in scan: continue
                dtype = scan['dtype']
                dtype_label = "Aérien" if dtype == 'aerien' else "Maritime"
                if dtype_label not in dtype_filter:
                    _log(f"{fname} : type {dtype_label} exclu", "warn"); continue

                df = scan['df'].copy()

                # Filtre pays selon le type
                pays_filter = pays_filter_aerien if dtype == 'aerien' else pays_filter_maritime
                if pays_filter:
                    geo_cols = [c for c in ['Pays de livraison', 'Pays de prise en charge'] if c in df.columns]
                    if geo_cols:
                        mask = pd.Series(False, index=df.index)
                        for c in geo_cols:
                            mask = mask | df[c].astype(str).isin(pays_filter)
                        n_before = len(df)
                        df = df[mask].copy()
                        _log(f"{fname} : filtre pays -> {len(df):,} lignes (etait {n_before:,})", "ok")

                # Filtre conditionnement
                if cond_filter and 'Conditionnement' in df.columns:
                    n_before = len(df)
                    df = df[df['Conditionnement'].astype(str).isin(cond_filter)].copy()
                    _log(f"{fname} : filtre conditionnement → {len(df):,} lignes (était {n_before:,})", "ok")

                if df.empty:
                    _log(f"{fname} : vide après filtrage", "warn"); continue

                for flux_name in flux_filter:
                    flux_letter = 'I' if flux_name == 'Import' else 'E'
                    result = build_section_from_filtered_df(
                        df, dtype, flux_letter, period_mode_key, str(period_month), _log
                    )
                    if result is None:
                        _log(f"{fname} / {flux_name} {dtype_label} : aucune donnée pour {label_periode}", "warn")
                        continue
                    sec_name, sec_data = result
                    if sec_name in sections:
                        _log(f"{sec_name} : déjà chargé, écrasé par {fname}", "warn")
                    sections[sec_name] = sec_data
                    total = int(sec_data['df_cible']['NOMBRE_TEU'].sum())
                    _log(f"{sec_name} : {len(sec_data['df_cible']):,} lignes - {total:,} {sec_data['metric_unit']}", "ok")

            if not sections:
                _log("Aucune section valide à générer.", "err")
                return

            _log(f"Génération du PPTX — {len(sections)} section(s) : {', '.join(sections.keys())}")
            report_single = all(s.get('is_single', False) for s in sections.values())
            with st.spinner("Génération du rapport PPTX..."):
                pptx_data = generate_pptx_report(sections, label_periode, report_single)
            _log("Rapport généré avec succès", "ok")
            st.session_state['pptx_page_data'] = pptx_data
            st.session_state['pptx_page_label'] = label_periode

        except Exception as exc:
            import traceback
            _log(f"Erreur : {exc}", "err")
            _log(f"Détail : {traceback.format_exc()[:600]}", "err")

    if st.session_state.get('pptx_page_data'):
        cur_year = max(all_annees) if all_annees else pd.Timestamp.now().year
        label = st.session_state.get('pptx_page_label', 'rapport')
        st.download_button(
            label="TÉLÉCHARGER LE RAPPORT PPTX",
            data=st.session_state['pptx_page_data'],
            file_name=f"AGL_Rapport_{label.replace(' ', '_')}_{cur_year}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            type="primary",
            key="pptx_page_download"
        )
