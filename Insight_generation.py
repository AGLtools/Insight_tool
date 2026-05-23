"""
Insight_generation.py
─────────────────────────────────────────────────────────────────────────────
Génération du rapport PPTX AGL Business Insight + UI Streamlit standalone.

Ce module est autonome (helpers dupliqués depuis app.py si nécessaire) afin
d'éviter les imports circulaires.
"""
import os
import io
import re
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
# Fichiers de configuration (modifiables via UI sans toucher au code)
NON_COMPLIANCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'non_compliance_products.json')
INTEGRATED_TRANSITAIRES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             'integrated_transitaires.json')

# Valeurs par défaut utilisées si les fichiers JSON sont absents / vides / invalides.
# Ces couples (Transitaire intégré, Importateurs clés) sont issus du tableau
# de référence interne AGL « TRANSITAIRES INTÉGRÉS ».
_DEFAULT_INTEGRATED_TRANSITAIRES = {
    'STRACOTRANS': ['SOCIAM', 'CI PLASTIQUES', 'COTIPLAST',
                    'STE.INDUS.PRDT.PLAS.ET CHIMIQU', 'NANO CI',
                    'STE AFRIC.FABRICA.DE PLASTIQUE'],
    'E.TRANSIT': ['RIMCO CI', 'SETACI', 'BERNABE CI',
                  'STE DE TRANSFO.INDUST.EN CI SA', 'MONDIAL CYCLES NOUVELLE CI',
                  'UNIVERSELLE INDUSTRIE CI', 'PEYRISSAC CI'],
    'GLOBAL MANUTENTION': ['CAPRACI', 'CIE AFRICAINE DE PROD',
                           'FLEXIBLE PACKAGING CI', 'LES MOULINS MODERNES DE CI',
                           'EMBACI', 'MICI', 'STE DE DISTRI.DE TTES MSE CI'],
    'TRANSIT CENTER': ['PROSUMA'],
    'TGR': ['SIPROCHIM CI'],
    'MOVIS TRANSIT': ['SUCRIVOIRE', 'PALMCI'],
    'TTS': ['NEXANS COTE D', 'TOLES IVOIRE CI'],
    'MONDIAL TRANSIT': ['STE REDA ET FILS CI'],
    'PACKING SERVICE': ['TOLES IVOIRE CI'],
    'ELDATRANS': ['CACOMIAF CI', 'SABIMEX'],
    'MANTRA IVOIRE': ['OLAM IVOIRE CI'],
}
_DEFAULT_NON_COMPLIANCE_PATTERNS = ['CONGEL', 'FRIPERIE', 'QUINCAILLERIE']


def load_non_compliance_patterns():
    """Retourne la liste des motifs (str.contains, MAJUSCULES) de marchandises
    « non compliance » à exclure. Lit le fichier JSON ou retourne les défauts."""
    if os.path.exists(NON_COMPLIANCE_FILE):
        try:
            with open(NON_COMPLIANCE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            patterns = data.get('patterns', [])
            if isinstance(patterns, list) and patterns:
                return [str(p).upper().strip() for p in patterns if str(p).strip()]
        except Exception:
            pass
    return list(_DEFAULT_NON_COMPLIANCE_PATTERNS)


def save_non_compliance_patterns(patterns):
    try:
        with open(NON_COMPLIANCE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                '_comment': "Liste des marchandises (Libellé marchandise) à exclure "
                            "de la vue 'Marché Hors Transitaires Intégrés'. "
                            "Matching en MAJUSCULES via str.contains.",
                'patterns': [str(p).upper().strip() for p in patterns if str(p).strip()],
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_integrated_transitaires():
    """Retourne le dict {transitaire_pattern: [importateur_patterns...]}."""
    if os.path.exists(INTEGRATED_TRANSITAIRES_FILE):
        try:
            with open(INTEGRATED_TRANSITAIRES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            couples = data.get('couples', {})
            if isinstance(couples, dict) and couples:
                return {str(k).upper().strip(): [str(v).upper().strip() for v in vs]
                        for k, vs in couples.items() if str(k).strip() and isinstance(vs, list)}
        except Exception:
            pass
    return {k: list(v) for k, v in _DEFAULT_INTEGRATED_TRANSITAIRES.items()}


def save_integrated_transitaires(couples):
    try:
        clean = {str(k).upper().strip(): [str(v).upper().strip() for v in vs if str(v).strip()]
                 for k, vs in couples.items() if str(k).strip()}
        with open(INTEGRATED_TRANSITAIRES_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                '_comment': "Couples (Transitaire intégré, Importateurs clés) à "
                            "exclure de la vue 'Marché Hors Transitaires Intégrés'. "
                            "Une ligne est exclue si Transitaire contient la clé ET "
                            "Destinataire contient l'un des importateurs.",
                'couples': clean,
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def apply_marche_hors_integres_filter(df, trans_col='Transitaire',
                                       dest_col='Destinataire',
                                       pays_col='Pays de livraison',
                                       lib_col='Libellé marchandise'):
    """
    Applique les filtres de la vue « Marché Hors Transitaires Intégrés »
    (slide 2 PPTX & onglet TOP 20 Transitaires du dashboard) :
      1. Pays de livraison = COTE D'IVOIRE (si la colonne existe)
      2. Exclusion des couples (Transitaire intégré, Importateur clé)
         définis dans ``integrated_transitaires.json``
      3. Exclusion des marchandises « non compliance » (motifs définis dans
         ``non_compliance_products.json``) si la colonne libellé existe.
    Les lignes NON APURE (transitaire vide / 0 / NON APURE) sont conservées :
    elles sont agrégées dans la ligne « AUTRES TRANSITAIRES ».
    """
    if df is None or df.empty:
        return df
    out = df

    # 1. Pays de livraison = COTE D'IVOIRE
    if pays_col in out.columns:
        pays_u = out[pays_col].fillna('').astype(str).str.upper()
        mask_ci = pays_u.str.contains("COTE D'IVOIRE", regex=False, na=False) | \
                  pays_u.str.contains("COTE D IVOIRE", regex=False, na=False)
        if mask_ci.any():
            out = out[mask_ci]

    # 2. Exclusion couples (Transitaire, Importateur clé)
    integrated = load_integrated_transitaires()
    if integrated and trans_col in out.columns and dest_col in out.columns:
        trans_u = out[trans_col].fillna('').astype(str).str.upper()
        dest_u = out[dest_col].fillna('').astype(str).str.upper()
        mask_integrated = pd.Series(False, index=out.index)
        for trans_pat, importers in integrated.items():
            if not trans_pat or not importers:
                continue
            m_t = trans_u.str.contains(re.escape(trans_pat), na=False)
            m_i = pd.Series(False, index=out.index)
            for imp in importers:
                if imp:
                    m_i |= dest_u.str.contains(re.escape(imp), na=False)
            mask_integrated |= (m_t & m_i)
        out = out[~mask_integrated]

    # 3. Exclusion marchandises non compliance
    nc_patterns = load_non_compliance_patterns()
    if nc_patterns and lib_col in out.columns:
        regex = '|'.join(re.escape(p) for p in nc_patterns if p)
        if regex:
            lib_u = out[lib_col].fillna('').astype(str).str.upper()
            mask_nc = lib_u.str.contains(regex, regex=True, na=False)
            out = out[~mask_nc]

    return out


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

def compute_top20_transitaires_overview(df, current_year, previous_year, metric_col='NOMBRE_TEU',
                                         filter_marche_hors_integres=False):
    """
    Calcule la vue Top 20 Transitaires (utilisée à la fois sur la slide 2
    et dans le Dashboard). Retourne un DataFrame prêt à afficher avec :
    Rang, Transitaire, Volume prv, PDM prv, Volume cur, PDM cur, Variation, Variation %
    + 3 lignes de totaux (TOP 20, AUTRES, TOTAL MARCHE).

    Si ``filter_marche_hors_integres=True``, applique les filtres de la vue
    « Marché Hors Transitaires Intégrés » (Pays = CI, exclusion des couples
    Transitaires intégrés / Importateurs clés, exclusion des marchandises
    non compliance).
    """
    if df is None or df.empty or 'Transitaire' not in df.columns or metric_col not in df.columns:
        return pd.DataFrame()
    if filter_marche_hors_integres:
        df = apply_marche_hors_integres_filter(df)
        if df is None or df.empty:
            return pd.DataFrame()
    df_cur = df[df['Année escale'] == current_year]
    df_prv = df[df['Année escale'] == previous_year]
    g_cur = df_cur.groupby('Transitaire')[metric_col].sum()
    g_prv = df_prv.groupby('Transitaire')[metric_col].sum() if not df_prv.empty else pd.Series(dtype=float)
    merged = pd.concat([g_cur.rename('cur'), g_prv.rename('prv')], axis=1).fillna(0)
    merged = merged[merged.index.astype(str).str.strip() != '']
    merged = merged[~merged.index.astype(str).str.upper().isin(['0', 'NAN', 'NONE'])]
    total_cur = float(merged['cur'].sum()); total_prv = float(merged['prv'].sum())
    # NON APURE est conservé dans le total mais exclu du classement Top 20 :
    # son volume est ajouté à la ligne « AUTRES TRANSITAIRES ».
    idx_upper = merged.index.astype(str).str.strip().str.upper()
    napure_mask = (idx_upper == 'NON APURE')
    napure = merged[napure_mask]
    ranked = merged[~napure_mask].sort_values('cur', ascending=False)
    top20 = ranked.head(20).copy()
    autres = pd.concat([ranked.iloc[20:], napure])

    def _row(name, vol_prv, vol_cur):
        var_u = vol_cur - vol_prv
        # Variation en fraction (0-1) pour permettre le format "percent" Streamlit
        var_p = (var_u / vol_prv) if vol_prv > 0 else (1.0 if vol_cur > 0 else 0.0)
        # PDM stockés en fraction (0-1) — formatés via column_config="percent"
        # côté UI ; cohérent avec le menu de format des colonnes Streamlit
        # qui multiplie par 100 lorsqu'il applique « Percentage ».
        return {
            'Transitaire': name,
            f'Volume {previous_year}': int(round(vol_prv)),
            f'PDM {previous_year}': (vol_prv / total_prv) if total_prv > 0 else 0.0,
            f'Volume {current_year}': int(round(vol_cur)),
            f'PDM {current_year}': (vol_cur / total_cur) if total_cur > 0 else 0.0,
            "Variation d'unite": int(round(var_u)),
            'Variation %': round(var_p, 4),
        }

    rows = []
    for i, (name, r) in enumerate(top20.iterrows(), start=1):
        rows.append({'Rang': i, **_row(str(name), float(r['prv']), float(r['cur']))})
    rows.append({'Rang': '', **_row('TOP 20 TRANSITAIRES', float(top20['prv'].sum()), float(top20['cur'].sum()))})
    rows.append({'Rang': '', **_row('AUTRES TRANSITAIRES', float(autres['prv'].sum()), float(autres['cur'].sum()))})
    rows.append({'Rang': '', **_row('TOTAL MARCHE', total_prv, total_cur)})
    return pd.DataFrame(rows)


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
                    client_col, label_per, unit, cur_year, prev_year,
                    right_extra_col=None, layout='actifs'):
    """
    Reproduit la mise en forme EXACTE du template original :
      - Titre (gras, taille 10) en ligne 2 : col 2 (gauche) / col 11 (droite)
      - En-têtes (gras blanc, fond navy 002060) en ligne 4
      - Données à partir de la ligne 5
      - Index col 1 (gauche) / col 10 (droite), 1 puis '=1+ref'
      - Ordre années : COURANTE puis PRÉCÉDENTE (comme original)
      - Format en-têtes : 'VOLUME TEUS 12 MOIS 2025'
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = 'Feuil1'
    lp = label_per.upper()
    u = unit.upper()

    thin = Side(style='thin')
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    title_font = Font(bold=True, size=10, name='Gill Sans MT')
    hdr_font = Font(bold=True, size=9, color='FFFFFFFF', name='Gill Sans MT')
    hdr_fill = PatternFill('solid', fgColor='FF002060')
    hdr_align_c = Alignment(horizontal='center', vertical='center', wrap_text=True)
    hdr_align_l = Alignment(horizontal='left', vertical='center', wrap_text=True)
    data_font = Font(size=9, name='Gill Sans MT')
    data_font_bold = Font(size=9, bold=True, name='Gill Sans MT')
    num_align = Alignment(horizontal='center')
    left_align = Alignment(horizontal='left')
    num_fmt = '#,##0'
    pct_fmt = '0%'

    # Coordonnées identiques pour tous les layouts (alignées sur le template)
    L_IDX, L_CLI, L_TIT = 1, 2, 2
    R_IDX, R_CLI, R_TIT = 10, 11, 11
    HDR_ROW = 4
    DATA_ROW = 5

    ws.column_dimensions[get_column_letter(L_IDX)].width = 11.43
    ws.column_dimensions[get_column_letter(L_CLI)].width = 50
    for k in range(7):
        ws.column_dimensions[get_column_letter(L_CLI + 1 + k)].width = 11.43
    ws.column_dimensions[get_column_letter(R_IDX)].width = 11.43
    ws.column_dimensions[get_column_letter(R_CLI)].width = 50
    for k in range(7 + (1 if right_extra_col else 0)):
        ws.column_dimensions[get_column_letter(R_CLI + 1 + k)].width = 11.43

    # Titres (ligne 2)
    ws.cell(2, L_TIT, left_title).font = title_font
    ws.cell(2, R_TIT, right_title).font = title_font

    # En-têtes (ligne 4) — ordre ORIGINAL : COURANTE puis PRÉCÉDENTE
    hdrs = ['CLIENTS',
            f'VOLUME {u} {lp} {cur_year}',  f'AGL {u} {lp} {cur_year}',  f'PDM {cur_year}',
            f'VOLUME {u} {lp} {prev_year}', f'AGL {u} {lp} {prev_year}', f'PDM {prev_year}',
            'VARIATION']
    for i, h in enumerate(hdrs):
        for base in (L_CLI, R_CLI):
            cell = ws.cell(HDR_ROW, base + i, h)
            cell.font = hdr_font; cell.fill = hdr_fill
            cell.alignment = hdr_align_l if i == 0 else hdr_align_c
            cell.border = border_all

    col_tm_cur = f'Total_Marche_{cur_year}'
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'

    def _write_side(df, num_col, data_col, is_right=False):
        for idx, (_, row) in enumerate(df.iterrows()):
            r = DATA_ROW + idx
            tm_cur = int(row.get(col_tm_cur, 0))
            ta_cur = int(row.get(col_ag_cur, 0))
            tm_prv = int(row.get(col_tm_prv, 0))
            ta_prv = int(row.get(col_ag_prv, 0))
            if idx == 0:
                c_idx = ws.cell(r, num_col, 1)
            else:
                prev_ref = f"{get_column_letter(num_col)}{r-1}"
                c_idx = ws.cell(r, num_col, f"=1+{prev_ref}")
            c_idx.font = data_font; c_idx.number_format = num_fmt; c_idx.alignment = num_align
            c_name = ws.cell(r, data_col, str(row[client_col]))
            c_name.font = data_font; c_name.alignment = left_align; c_name.border = border_all
            # Ordre CUR (1,2) PDM cur (3) PRV (4,5) PDM prv (6) VAR (7)
            for off, val in [(1, tm_cur), (2, ta_cur), (4, tm_prv), (5, ta_prv)]:
                cc = ws.cell(r, data_col + off, val)
                cc.font = data_font; cc.number_format = num_fmt; cc.alignment = num_align; cc.border = border_all
            c_p_cur = ws.cell(r, data_col + 3, ta_cur / tm_cur if tm_cur > 0 else 0)
            c_p_cur.font = data_font; c_p_cur.number_format = pct_fmt; c_p_cur.alignment = num_align; c_p_cur.border = border_all
            c_p_prv = ws.cell(r, data_col + 6, ta_prv / tm_prv if tm_prv > 0 else 0)
            c_p_prv.font = data_font; c_p_prv.number_format = pct_fmt; c_p_prv.alignment = num_align; c_p_prv.border = border_all
            c_var = ws.cell(r, data_col + 7, int(ta_cur - ta_prv))
            c_var.font = data_font; c_var.number_format = num_fmt; c_var.alignment = num_align; c_var.border = border_all
            if is_right and right_extra_col and right_extra_col in row.index:
                c_vm = ws.cell(r, data_col + 8, int(row[right_extra_col]))
                c_vm.font = data_font; c_vm.number_format = num_fmt; c_vm.alignment = num_align; c_vm.border = border_all
        if len(df) > 0:
            r = DATA_ROW + len(df)
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
            cc.font = data_font_bold; cc.number_format = num_fmt; cc.alignment = num_align; cc.border = border_all
            if is_right and right_extra_col and right_extra_col in df.columns:
                cc = ws.cell(r, data_col + 8, int(df[right_extra_col].sum()))
                cc.font = data_font_bold; cc.number_format = num_fmt; cc.alignment = num_align; cc.border = border_all

    _write_side(left_df, L_IDX, L_CLI, False)
    _write_side(right_df, R_IDX, R_CLI, True)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _categorize_clients(comp, client_col, cur_year, prev_year):
    # Pas de filtre liste noire ici : les Excel embarqués doivent refléter
    # exactement les mêmes données que le dashboard et les slides PPTX.
    c = comp.copy()
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'
    col_tm_cur = f'Total_Marche_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'

    c['Variation'] = c[col_ag_cur] - c[col_ag_prv]
    c['Var_Marche'] = c[col_tm_cur] - c[col_tm_prv]
    # PDM en fraction (0-1) — comparaison directe sans arrondi pour rester
    # cohérent avec update_analyse_group et render_dashboard (seuil 0.95 / 95)
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
    """
    Top 100 importateurs/exportateurs au format ORIGINAL :
    12 colonnes (A→L) : idx, NOM, VOL N, VOL N-1, Variat° unité, Variat° %,
                         TEUS AGL N, TEUS AGL N-1, Variat° unité AGL,
                         Variat° % AGL, PDM N AGL, PDM N-1 AGL.
    Pas de remplissage de couleur sur les en-têtes (fond blanc).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = 'Export'  # nom de feuille du fichier original
    u = unit.upper()
    col_tm_cur = f'Total_Marche_{cur_year}'
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'

    c = comp.copy()
    top = c.sort_values(col_tm_cur, ascending=False).head(100)
    role = 'IMPORTATEURS' if client_col == 'Destinataire' else 'EXPORTATEURS'

    thin = Side(style='thin')
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    title_font = Font(bold=True, size=10, name='Gill Sans MT')
    hdr_font = Font(bold=True, size=9, color='FFFFFFFF', name='Gill Sans MT')
    hdr_fill = PatternFill('solid', fgColor='FF002060')
    hdr_align_c = Alignment(horizontal='center', vertical='center', wrap_text=True)
    hdr_align_l = Alignment(horizontal='left', vertical='center', wrap_text=True)
    data_font = Font(size=9, name='Gill Sans MT')
    num_align = Alignment(horizontal='center')
    left_align = Alignment(horizontal='left')
    num_fmt = '#,##0'
    pct_fmt_signed = '#,##0\\ %;\\-#,##0\\ %;#,##0\\ %'
    pct_fmt_pdm = '0\\ %;\\-0\\ %;0\\ %'

    ws.column_dimensions['A'].width = 11.43
    ws.column_dimensions['B'].width = 55
    for col in ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
        ws.column_dimensions[col].width = 13

    ws.cell(2, 2, f"TOP 100 {role} COTE D'IVOIRE").font = title_font

    hdrs = [role,
            f'VOLUME {u} N', f'VOLUME {u} N-1',
            "Variat\u00b0 en unit\u00e9 d'oeuvre", "Variat\u00b0 en %",
            f'{u} AGL CI N', f'{u} AGL CI N-1',
            "Variat\u00b0 en unit\u00e9 d'oeuvre AGL CI", "Variat\u00b0 en % AGL CI",
            'PDM N AGL CI', 'PDM N-1 AGL CI']
    for i, h in enumerate(hdrs):
        cl = ws.cell(4, 2 + i, h)
        cl.font = hdr_font; cl.fill = hdr_fill
        cl.alignment = hdr_align_l if i == 0 else hdr_align_c; cl.border = border_all

    for idx, (_, row) in enumerate(top.iterrows()):
        r = 5 + idx
        tm_cur = int(row.get(col_tm_cur, 0)); ta_cur = int(row.get(col_ag_cur, 0))
        tm_prv = int(row.get(col_tm_prv, 0)); ta_prv = int(row.get(col_ag_prv, 0))
        # Index col
        if idx == 0:
            ws.cell(r, 1, 1).font = data_font
        else:
            ws.cell(r, 1, f"=1+A{r-1}").font = data_font
        c_name = ws.cell(r, 2, str(row[client_col]))
        c_name.font = data_font; c_name.alignment = left_align; c_name.border = border_all
        # Volumes marché N et N-1
        for off, val in [(0, tm_cur), (1, tm_prv)]:
            cc = ws.cell(r, 3 + off, val); cc.font = data_font; cc.number_format = num_fmt
            cc.alignment = num_align; cc.border = border_all
        # Variation marché unité + %
        c_v = ws.cell(r, 5, tm_cur - tm_prv); c_v.font = data_font; c_v.number_format = num_fmt
        c_v.alignment = num_align; c_v.border = border_all
        c_vp = ws.cell(r, 6, (tm_cur - tm_prv) / tm_prv if tm_prv > 0 else 0)
        c_vp.font = data_font; c_vp.number_format = pct_fmt_signed; c_vp.alignment = num_align; c_vp.border = border_all
        # Volumes AGL N et N-1
        for off, val in [(0, ta_cur), (1, ta_prv)]:
            cc = ws.cell(r, 7 + off, val); cc.font = data_font; cc.number_format = num_fmt
            cc.alignment = num_align; cc.border = border_all
        # Variation AGL unité + %
        c_a = ws.cell(r, 9, ta_cur - ta_prv); c_a.font = data_font; c_a.number_format = num_fmt
        c_a.alignment = num_align; c_a.border = border_all
        c_ap = ws.cell(r, 10, (ta_cur - ta_prv) / ta_prv if ta_prv > 0 else 0)
        c_ap.font = data_font; c_ap.number_format = pct_fmt_pdm; c_ap.alignment = num_align; c_ap.border = border_all
        # PDM N et N-1
        c_pn = ws.cell(r, 11, ta_cur / tm_cur if tm_cur > 0 else 0)
        c_pn.font = data_font; c_pn.number_format = pct_fmt_pdm; c_pn.alignment = num_align; c_pn.border = border_all
        c_pp = ws.cell(r, 12, ta_prv / tm_prv if tm_prv > 0 else 0)
        c_pp.font = data_font; c_pp.number_format = pct_fmt_pdm; c_pp.alignment = num_align; c_pp.border = border_all

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_competitor_xlsx(df_cible, pattern, label, client_col, unit, cur_year, label_per='3 MOIS'):
    """
    Portefeuille concurrent au format ORIGINAL :
      - Titre ligne 2 (B2) en gras
      - En-têtes ligne 4 (B4/C4) avec fond navy 002060 + texte blanc
      - Données à partir de la ligne 5
      - Pas de colonne d'index, total général en bas.
    """
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
    title_font = Font(bold=True, size=10, name='Gill Sans MT')
    hdr_font = Font(bold=True, size=9, color='FFFFFFFF', name='Gill Sans MT')
    hdr_fill = PatternFill('solid', fgColor='FF002060')
    hdr_align_c = Alignment(horizontal='center', vertical='center')
    hdr_align_l = Alignment(horizontal='left', vertical='center')
    data_font = Font(size=9, name='Gill Sans MT')
    data_font_bold = Font(size=9, bold=True, name='Gill Sans MT')
    num_align = Alignment(horizontal='center')
    left_align = Alignment(horizontal='left')
    num_fmt = '#,##0'

    ws.column_dimensions['A'].width = 11.43
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 11.43

    # Titre ligne 2 (B2) sans remplissage
    c_title = ws.cell(2, 2, f'PORTEFEUILLE CLIENTS {label} {cur_year} EN {u}')
    c_title.font = title_font

    # En-têtes ligne 4
    cl = ws.cell(4, 2, 'CLIENTS')
    cl.font = hdr_font; cl.fill = hdr_fill; cl.alignment = hdr_align_l; cl.border = border_all
    cr = ws.cell(4, 3, u)
    cr.font = hdr_font; cr.fill = hdr_fill; cr.alignment = hdr_align_c; cr.border = border_all

    # Données à partir ligne 5
    for idx, (_, row) in enumerate(portfolio.iterrows()):
        r = 5 + idx
        c_name = ws.cell(r, 2, str(row[client_col]))
        c_name.font = data_font; c_name.alignment = left_align; c_name.border = border_all
        c_val = ws.cell(r, 3, int(row['NOMBRE_TEU']))
        c_val.font = data_font; c_val.number_format = num_fmt; c_val.alignment = num_align; c_val.border = border_all

    if len(portfolio) > 0:
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
            cats['captive_up'], cats['captive_down'], ccol, label_periode, mu, cur_year, prev_year,
            layout='captive')
        replacements[f'ppt/embeddings/{files["detail"][1]}'] = _make_dual_xlsx(
            'CLIENTS  ACTIFS', 'CLIENTS NON ACTIFS',
            cats['new'], cats['lost'], ccol, label_periode, mu, cur_year, prev_year,
            layout='actifs')
        replacements[f'ppt/embeddings/{files["detail"][2]}'] = _make_dual_xlsx(
            'CLIENTS EN HAUSSES', 'CLIENTS EN BAISSES',
            cats['hausse'], cats['baisse'], ccol, label_periode, mu, cur_year, prev_year,
            right_extra_col='Var_Marche', layout='hausses')
        replacements[f'ppt/embeddings/{files["detail"][3]}'] = _make_top100_xlsx(
            comp, ccol, label_periode, mu, cur_year, prev_year)
        for i, (pattern, label) in enumerate(COMPETITORS):
            replacements[f'ppt/embeddings/{files["fonds"][i]}'] = _make_competitor_xlsx(
                df_cible, pattern, label, ccol, mu, cur_year, label_periode)
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

    # Index du mois (1..12) — utilisé pour le format YTD "N MOIS"
    period_month_idx = MOIS_ALL.index(period_month_name) + 1
    period_month_upper = period_month_name.upper()

    # ────────────────────────────────────────────────────────────────────
    # Nomenclature exacte du rapport original :
    #
    # ── Mode mois spécifique (ex: "Mars") ──
    #   • Titres slides       : "MARS 2026"      / "Mars 2026"
    #   • En-têtes tableaux   : "Mars 2026"
    #
    # ── Mode YTD / Cumul (ex: "3 MOIS") ──
    #   • Cover               : "CUMUL A FIN MARS 2026 VS 2025"   (déjà "A FIN" dans template)
    #   • Synthèse + Marché   : "... A FIN MARS 2026"             (ajout de "A FIN")
    #   • Tableaux + Top 20   : "... 3 MOIS 2026"                 (forme courte)
    #   • Fonds de commerce   : "... 3 MOIS 2026"                 (forme courte)
    # ────────────────────────────────────────────────────────────────────
    if is_single_month:
        long_upper  = period_month_upper                     # "MARS"
        long_title  = period_month_name                      # "Mars"
        short_upper = period_month_upper                     # "MARS"
        short_title = period_month_name                      # "Mars"
        # En mode mois spécifique, on étend même les abréviations au nom complet
        # afin que les en-têtes de tableaux affichent "Février 2026" et non "Févr 2026"
        abbrev_upper = period_month_upper
        abbrev_title = period_month_name
    else:
        long_upper  = f"A FIN {period_month_upper}"          # "A FIN MARS"
        long_title  = f"A fin {period_month_name}"           # "A fin Mars"
        short_upper = f"{period_month_idx} MOIS"             # "3 MOIS"
        short_title = f"{period_month_idx} MOIS"
        abbrev_upper = f"{period_month_idx} MOIS"
        abbrev_title = f"{period_month_idx} MOIS"

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

    def _detect_context(text):
        """Retourne (already_has_a_fin, is_title_context) à partir d'un texte
        (typiquement le texte complet d'un text_frame ou d'une cellule)."""
        if not text:
            return False, False
        up = text.upper()
        already = ('A FIN' in up) or ('À FIN' in up)
        is_title = any(kw in up for kw in (
            'SYNTHESE', 'SYNTHÈSE', 'MARCHE HORS', 'MARCHÉ HORS'
        ))
        return already, is_title

    def replace_period_in_text(text, *, force_already_has_a_fin=None, force_title_context=None):
        if not text or not isinstance(text, str):
            return text
        result = text
        # ── 1) Années ──
        # Le template contient des années fixes (TEMPLATE_CUR / TEMPLATE_PRV).
        # On remappe TOUTES les années 4 chiffres rencontrées dans le texte vers
        # les années réelles des données chargées, en une seule passe regex
        # (évite les cascades du type "2026"→"2025"→"2024" lors de .replace successifs).
        TEMPLATE_CUR = 2026
        TEMPLATE_PRV = 2025
        cur_2 = str(current_year)[-2:]
        prv_2 = str(previous_year)[-2:]
        tcur_2 = str(TEMPLATE_CUR)[-2:]
        tprv_2 = str(TEMPLATE_PRV)[-2:]

        def _remap_year(m):
            y = int(m.group(0))
            if y == TEMPLATE_CUR:
                return str(current_year)
            if y == TEMPLATE_PRV:
                return str(previous_year)
            # Toute autre année 4 chiffres "récente" est aussi normalisée
            # (ex: vieux templates avec 2024/2023) en suivant son décalage relatif.
            if 2000 <= y <= 2100:
                offset = TEMPLATE_CUR - y
                return str(current_year - offset)
            return m.group(0)

        # Remplacement des années 4 chiffres (passe unique)
        result = re.sub(r'\b(20\d{2})\b', _remap_year, result)
        # Remplacement des PDM XX (2 chiffres) en passe unique également
        def _remap_pdm(m):
            yy = m.group(1)
            if yy == tcur_2:
                return f'PDM {cur_2}'
            if yy == tprv_2:
                return f'PDM {prv_2}'
            return m.group(0)
        result = re.sub(r'PDM\s+(\d{2})\b', _remap_pdm, result)

        # ── 2) Détection du contexte (forçable depuis l'appelant) ──
        if force_already_has_a_fin is not None or force_title_context is not None:
            already_has_a_fin = bool(force_already_has_a_fin)
            is_title_context = bool(force_title_context)
        else:
            already_has_a_fin, is_title_context = _detect_context(result)

        if already_has_a_fin:
            sub_upper = period_month_upper
            sub_title = period_month_name
        elif is_title_context:
            sub_upper = long_upper
            sub_title = long_title
        else:
            sub_upper = short_upper
            sub_title = short_title

        # ── 3) Remplacement des noms de mois COMPLETS (pass unique via regex pour
        #       éviter de re-substituer un mois introduit par la substitution précédente,
        #       ex: JANVIER → "A FIN MARS" puis MARS qui serait re-remplacé) ──
        # Pattern UPPERCASE
        pat_upper = re.compile(r'\b(' + '|'.join(re.escape(m) for m in MOIS_ALL_UPPER) + r')\b')
        result = pat_upper.sub(sub_upper, result)
        # Pattern Title-case
        pat_title = re.compile(r'\b(' + '|'.join(re.escape(m) for m in MOIS_ALL) + r')\b')
        result = pat_title.sub(sub_title, result)

        # ── 4) Remplacement des ABRÉVIATIONS (Janv, Févr, Sept, ...) en pass unique ──
        # Exclure les abréviations qui sont identiques au nom complet d'un mois
        # (ex: "Mars" est à la fois full-name et abbrev) afin de ne pas re-substituer
        # un mois déjà traité à l'étape 3.
        all_abbrevs = [a for a in ABBREV_BY_FULL.values() if a not in MOIS_ALL]
        if all_abbrevs:
            pat_abbrev_upper = re.compile(r'\b(' + '|'.join(re.escape(a.upper()) for a in all_abbrevs) + r')\b')
            result = pat_abbrev_upper.sub(abbrev_upper, result)
            pat_abbrev_title = re.compile(r'\b(' + '|'.join(re.escape(a) for a in all_abbrevs) + r')\b')
            result = pat_abbrev_title.sub(abbrev_title, result)

        # ── 5) Cas particulier : typo "ANVIER" présente dans certains en-têtes du template
        # (ex: "AGL ANVIER 2026" au lieu de "AGL JANVIER 2026")
        if 'ANVIER' in result:
            # En-tête de tableau → forme courte
            result = result.replace('ANVIER', short_upper)
        return result

    def _apply_to_paragraph(para, *, force_already=None, force_title=None):
        """
        Remplace les noms de mois et années au niveau du paragraphe complet
        (utile quand un mot est fragmenté entre plusieurs runs).
        Préserve la mise en forme de la première run.
        """
        if not para.runs:
            if para.text:
                new = replace_period_in_text(para.text,
                                             force_already_has_a_fin=force_already,
                                             force_title_context=force_title)
                if new != para.text:
                    para.text = new
            return
        full = "".join(r.text for r in para.runs)
        new = replace_period_in_text(full,
                                     force_already_has_a_fin=force_already,
                                     force_title_context=force_title)
        if new == full:
            return
        # Réécriture : on met tout dans la première run, on vide les autres
        para.runs[0].text = new
        for r in para.runs[1:]:
            r.text = ""

    def _tf_full_text(tf):
        try:
            return "\n".join(p.text for p in tf.paragraphs)
        except Exception:
            return ""

    def _slide_full_text(slide):
        chunks = []
        def _walk(sh):
            try:
                if sh.shape_type == 6:
                    for sub in sh.shapes: _walk(sub)
                    return
                if hasattr(sh, 'has_table') and sh.has_table:
                    return  # On exclut les tableaux du contexte slide
                if hasattr(sh, 'text_frame') and sh.text_frame:
                    chunks.append("\n".join(p.text for p in sh.text_frame.paragraphs))
            except Exception:
                pass
        for sh in slide.shapes: _walk(sh)
        return "\n".join(chunks)

    def apply_period_to_shape_recursive(shape, *, slide_already=False, slide_title=False):
        try:
            if shape.shape_type == 6:
                for sub in shape.shapes:
                    apply_period_to_shape_recursive(sub,
                                                    slide_already=slide_already,
                                                    slide_title=slide_title)
                return
            if shape.has_table:
                tbl = shape.table
                # Dans les cellules de tableau : JAMAIS de forme longue "A FIN MARS",
                # toujours forme courte "3 MOIS" (sauf si la cellule contient déjà "A FIN")
                for row in tbl.rows:
                    for cell in row.cells:
                        full_cell = _tf_full_text(cell.text_frame)
                        c_already, _ = _detect_context(full_cell)
                        for para in cell.text_frame.paragraphs:
                            _apply_to_paragraph(para,
                                                force_already=c_already,
                                                force_title=False)
                return
            if hasattr(shape, 'text_frame') and shape.text_frame:
                # Pour un text_frame :
                #  - already_has_a_fin = vrai si le text_frame OU la slide a "A FIN"
                #  - is_title_context = vrai si le text_frame OU la slide est de type titre
                full_tf = _tf_full_text(shape.text_frame)
                tf_already, tf_title = _detect_context(full_tf)
                eff_already = tf_already or slide_already
                eff_title = tf_title or slide_title
                for para in shape.text_frame.paragraphs:
                    _apply_to_paragraph(para,
                                        force_already=eff_already,
                                        force_title=eff_title)
        except Exception:
            pass

    def find_table(slide):
        for sh in slide.shapes:
            if sh.has_table:
                return sh.table
        return None

    # ───────── Helpers formatage avancé (couleurs) ─────────
    from copy import deepcopy as _deepcopy

    def _capture_para_props(para):
        """Retourne (size, font_name) de la première run d'un paragraphe."""
        size = None
        font_name = None
        if para.runs:
            f = para.runs[0].font
            if f.size: size = f.size
            if f.name: font_name = f.name
        return size, font_name

    def _clear_para_runs(para):
        """Supprime tous les runs (a:r, a:br, a:fld) du paragraphe SANS toucher au pPr.
        Préserve donc les puces, l'indentation et la mise en forme du paragraphe."""
        from pptx.oxml.ns import qn
        p = para._p
        for tag in ('a:r', 'a:br', 'a:fld'):
            for child in p.findall(qn(tag)):
                p.remove(child)

    def _clone_pPr_into(target_para, source_para):
        """Copie le <a:pPr> de source_para dans target_para (préserve puces/indent)."""
        from pptx.oxml.ns import qn
        src_pPr = source_para._p.find(qn('a:pPr'))
        if src_pPr is None:
            return
        tgt_p = target_para._p
        old = tgt_p.find(qn('a:pPr'))
        if old is not None:
            tgt_p.remove(old)
        new_pPr = _deepcopy(src_pPr)
        tgt_p.insert(0, new_pPr)

    def _add_paragraph_like(tf, template_para):
        """Ajoute un nouveau paragraphe et copie le pPr d'un paragraphe modèle."""
        new_p = tf.add_paragraph()
        if template_para is not None:
            _clone_pPr_into(new_p, template_para)
        return new_p

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
        Préserve la puce et la mise en forme du paragraphe d'origine.
        """
        tf = shape.text_frame
        if not tf.paragraphs:
            return
        p = tf.paragraphs[0]
        size, font_name = _capture_para_props(p)
        size = size or Pt(12)
        _clear_para_runs(p)
        _add_run(p, f"{label}  ", size=size, font_name=font_name)
        _add_run(p, _fmt_signed(value, unit), bold=True, color=_value_color(value),
                 size=size, font_name=font_name)
        # Supprime les paragraphes suivants éventuels (template multi-lignes inutile)
        from pptx.oxml.ns import qn
        all_p = tf._txBody.findall(qn('a:p'))
        for extra in all_p[1:]:
            tf._txBody.remove(extra)

    def _set_detail_rect_formatted(shape, lines, unit):
        """
        Rectangle de détail multi-lignes :
        lines = [(count, label, value), ...]
        Préserve la puce/indentation des paragraphes d'origine.
        """
        tf = shape.text_frame
        if not tf.paragraphs:
            return
        from pptx.oxml.ns import qn
        existing = list(tf.paragraphs)
        first = existing[0]
        size, font_name = _capture_para_props(first)
        size = size or Pt(11)
        # 1) Réécrit les paragraphes existants (jusqu'au nombre de lignes nécessaires)
        for i, (count, label, value) in enumerate(lines):
            if i < len(existing):
                p = existing[i]
                _clear_para_runs(p)
            else:
                # Nouveau paragraphe : clone le pPr du dernier existant pour garder la puce
                p = _add_paragraph_like(tf, existing[-1])
            _add_run(p, f"{int(count):02d} ", bold=True, size=size, font_name=font_name)
            _add_run(p, f"{label}  ", size=size, font_name=font_name)
            _add_run(p, _fmt_signed(value, unit), bold=True, color=_value_color(value),
                     size=size, font_name=font_name)
        # 2) Supprime les paragraphes excédentaires
        all_p = tf._txBody.findall(qn('a:p'))
        for extra in all_p[len(lines):]:
            tf._txBody.remove(extra)

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

    # ───────── Slide 2 : Top 20 Transitaires (Marché Hors Transitaires Intégrés) ─────────
    def fill_top20_transitaires_board(slide, sections_data, current_year, previous_year, is_single):
        """
        Remplace l'image hardcodée 'Image 10' par un vrai tableau dynamique
        des Top 20 Transitaires (Import Maritime), avec totaux et part de marché.
        """
        if 'Import Maritime' not in sections_data:
            return
        sd = sections_data['Import Maritime']
        df = sd.get('df_cible')
        if df is None or df.empty or 'Transitaire' not in df.columns:
            return
        metric_col = 'NOMBRE_TEU'
        if metric_col not in df.columns:
            return

        # Filtres « Marché Hors Transitaires Intégrés » :
        # - Pays de livraison = COTE D'IVOIRE
        # - Exclusion des couples (Transitaire intégré, Importateur clé)
        # - Exclusion des marchandises non compliance (Congelés/Friperie/Quincaillerie)
        df = apply_marche_hors_integres_filter(df)
        if df is None or df.empty:
            return

        # Agrégation par transitaire
        df_cur = df[df['Année escale'] == current_year]
        df_prv = df[df['Année escale'] == previous_year] if not is_single else None
        g_cur = df_cur.groupby('Transitaire')[metric_col].sum()
        if df_prv is not None and not df_prv.empty:
            g_prv = df_prv.groupby('Transitaire')[metric_col].sum()
        else:
            g_prv = pd.Series(dtype=float)
        merged = pd.concat([g_cur.rename('cur'), g_prv.rename('prv')], axis=1).fillna(0)
        # Exclure les valeurs vides / 0 / NaN
        merged = merged[merged.index.astype(str).str.strip() != '']
        merged = merged[~merged.index.astype(str).str.upper().isin(['0', 'NAN', 'NONE'])]

        total_cur = float(merged['cur'].sum())
        total_prv = float(merged['prv'].sum())
        # NON APURE : conservé dans le total mais exclu du classement Top 20
        # (volume agrégé dans la ligne « AUTRES TRANSITAIRES »).
        idx_upper = merged.index.astype(str).str.strip().str.upper()
        napure_mask = (idx_upper == 'NON APURE')
        napure = merged[napure_mask]
        ranked = merged[~napure_mask].sort_values('cur', ascending=False)
        top20 = ranked.head(20).copy()
        autres = pd.concat([ranked.iloc[20:], napure])
        autres_cur = float(autres['cur'].sum())
        autres_prv = float(autres['prv'].sum())
        top20_cur = float(top20['cur'].sum())
        top20_prv = float(top20['prv'].sum())

        # Localiser l'image et la supprimer
        image_left = image_top = image_width = image_height = None
        for sh in list(slide.shapes):
            if sh.shape_type == 13 and sh.name == 'Image 10':
                image_left, image_top = sh.left, sh.top
                image_width, image_height = sh.width, sh.height
                sp = sh._element
                sp.getparent().remove(sp)
                break
        if image_left is None:
            # Pas d'image trouvée : on ne génère rien
            return

        from pptx.util import Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN

        # Colonnes: Rank | Transitaire | Vol prv | PDM prv | Vol cur | PDM cur | Var unit | Var %
        n_cols = 7 if is_single else 7  # rank+name+volcur+pdmcur+volprv+pdmprv+var (simplified single)
        # Pour rester fidèle au rapport original, on ajoute toujours toutes les colonnes
        headers = ["TRANSITAIRES",
                   f"VOLUME {previous_year} TEUS", f"PDM {str(previous_year)[-2:]}",
                   f"VOLUME {current_year} TEUS", f"PDM {str(current_year)[-2:]}",
                   "VARIATION D'UNITE D'OEUVRE", "VARIATION %"]
        n_cols = len(headers) + 1  # + colonne rang
        # 1 ligne header + 20 lignes top20 + 1 ligne TOP20 + 1 ligne AUTRES + 1 ligne TOTAL
        n_rows = 1 + len(top20) + 3

        tbl_shape = slide.shapes.add_table(n_rows, n_cols, image_left, image_top, image_width, image_height)
        tbl = tbl_shape.table

        # Largeurs de colonnes : rang petit, nom large, autres équilibrées
        from pptx.util import Emu
        total_w = image_width
        col_widths_pct = [0.04, 0.30, 0.11, 0.07, 0.11, 0.07, 0.15, 0.15]
        for i, pct in enumerate(col_widths_pct):
            tbl.columns[i].width = Emu(int(total_w * pct))

        # Couleurs du rapport original
        COLOR_HEADER_BG = RGBColor(0x1C, 0x35, 0x5E)   # Navy
        COLOR_HEADER_FG = RGBColor(0xFF, 0xFF, 0xFF)
        COLOR_RANK_BG   = RGBColor(0xD9, 0xE1, 0xF2)
        COLOR_TOP20_BG  = RGBColor(0xC6, 0xE0, 0xB4)   # Vert clair
        COLOR_AUTRES_BG = RGBColor(0xF8, 0xCB, 0xAD)   # Orange clair
        COLOR_TOTAL_BG  = RGBColor(0xA9, 0xD0, 0x8E)   # Vert plus foncé
        COLOR_BLUE_TXT  = RGBColor(0x00, 0x70, 0xC0)
        COLOR_RED_TXT   = RGBColor(0xC0, 0x00, 0x00)

        def _set_cell(cell, text, *, bold=False, color=None, bg=None, align=None, size=Pt(9)):
            cell.text = ""
            tf = cell.text_frame
            p = tf.paragraphs[0]
            for r in p.runs:
                r.text = ""
            r = p.add_run()
            r.text = text
            r.font.size = size
            r.font.bold = bold
            if color:
                r.font.color.rgb = color
            if align:
                p.alignment = align
            if bg:
                from pptx.oxml.ns import qn
                from lxml import etree
                tcPr = cell._tc.get_or_add_tcPr()
                # remove existing fill
                for child in tcPr.findall(qn('a:solidFill')):
                    tcPr.remove(child)
                solidFill = etree.SubElement(tcPr, qn('a:solidFill'))
                srgb = etree.SubElement(solidFill, qn('a:srgbClr'))
                srgb.set('val', f"{bg[0]:02X}{bg[1]:02X}{bg[2]:02X}")
            cell.margin_left = Emu(36000)
            cell.margin_right = Emu(36000)
            cell.margin_top = Emu(18000)
            cell.margin_bottom = Emu(18000)

        # ── Header (ligne 0) ──
        _set_cell(tbl.cell(0, 0), "", bg=(0x1C, 0x35, 0x5E))
        for ci, hdr in enumerate(headers):
            _set_cell(tbl.cell(0, ci + 1), hdr, bold=True, color=COLOR_HEADER_FG,
                      bg=(0x1C, 0x35, 0x5E), align=PP_ALIGN.CENTER, size=Pt(9))

        def _fmt_int(v): return f"{int(round(v)):,}".replace(",", " ")
        def _fmt_pct(num, den):
            if den <= 0: return "0%"
            return f"{round(num / den * 100)}%"
        def _fmt_signed(v):
            sign = "" if v >= 0 else "-"
            return f"{sign}{_fmt_int(abs(v))}"

        # ── Top 20 (lignes 1..20) ──
        for i, (name, row) in enumerate(top20.iterrows()):
            r_idx = i + 1
            cur = float(row['cur']); prv = float(row['prv'])
            var_u = cur - prv
            var_pct = (var_u / prv * 100) if prv > 0 else (100.0 if cur > 0 else 0.0)
            _set_cell(tbl.cell(r_idx, 0), str(i + 1), bold=True, bg=(0xD9, 0xE1, 0xF2),
                      align=PP_ALIGN.CENTER, color=COLOR_BLUE_TXT)
            _set_cell(tbl.cell(r_idx, 1), str(name)[:40], bold=True, color=COLOR_BLUE_TXT, size=Pt(9))
            _set_cell(tbl.cell(r_idx, 2), _fmt_int(prv), align=PP_ALIGN.CENTER, color=COLOR_BLUE_TXT)
            _set_cell(tbl.cell(r_idx, 3), _fmt_pct(prv, total_prv), align=PP_ALIGN.CENTER, color=COLOR_BLUE_TXT)
            _set_cell(tbl.cell(r_idx, 4), _fmt_int(cur), align=PP_ALIGN.CENTER, color=COLOR_BLUE_TXT)
            _set_cell(tbl.cell(r_idx, 5), _fmt_pct(cur, total_cur), align=PP_ALIGN.CENTER, color=COLOR_BLUE_TXT)
            var_color = COLOR_BLUE_TXT if var_u >= 0 else COLOR_RED_TXT
            _set_cell(tbl.cell(r_idx, 6), _fmt_signed(var_u), align=PP_ALIGN.CENTER, color=var_color, bold=True)
            _set_cell(tbl.cell(r_idx, 7), f"{round(var_pct)}%", align=PP_ALIGN.CENTER, color=var_color, bold=True)

        # ── Ligne TOP 20 TRANSITAIRES ──
        r_idx = 1 + len(top20)
        _set_cell(tbl.cell(r_idx, 0), "", bg=(0xC6, 0xE0, 0xB4))
        _set_cell(tbl.cell(r_idx, 1), "TOP 20 TRANSITAIRES", bold=True, bg=(0xC6, 0xE0, 0xB4))
        _set_cell(tbl.cell(r_idx, 2), _fmt_int(top20_prv), bold=True, bg=(0xC6, 0xE0, 0xB4), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 3), _fmt_pct(top20_prv, total_prv), bold=True, bg=(0xC6, 0xE0, 0xB4), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 4), _fmt_int(top20_cur), bold=True, bg=(0xC6, 0xE0, 0xB4), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 5), _fmt_pct(top20_cur, total_cur), bold=True, bg=(0xC6, 0xE0, 0xB4), align=PP_ALIGN.CENTER)
        var_t = top20_cur - top20_prv
        var_t_pct = (var_t / top20_prv * 100) if top20_prv > 0 else 0
        col_t = COLOR_BLUE_TXT if var_t >= 0 else COLOR_RED_TXT
        _set_cell(tbl.cell(r_idx, 6), _fmt_signed(var_t), bold=True, bg=(0xC6, 0xE0, 0xB4), align=PP_ALIGN.CENTER, color=col_t)
        _set_cell(tbl.cell(r_idx, 7), f"{round(var_t_pct)}%", bold=True, bg=(0xC6, 0xE0, 0xB4), align=PP_ALIGN.CENTER, color=col_t)

        # ── Ligne AUTRES TRANSITAIRES ──
        r_idx += 1
        _set_cell(tbl.cell(r_idx, 0), "", bg=(0xF8, 0xCB, 0xAD))
        _set_cell(tbl.cell(r_idx, 1), "AUTRES TRANSITAIRES", bold=True, bg=(0xF8, 0xCB, 0xAD))
        _set_cell(tbl.cell(r_idx, 2), _fmt_int(autres_prv), bold=True, bg=(0xF8, 0xCB, 0xAD), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 3), _fmt_pct(autres_prv, total_prv), bold=True, bg=(0xF8, 0xCB, 0xAD), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 4), _fmt_int(autres_cur), bold=True, bg=(0xF8, 0xCB, 0xAD), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 5), _fmt_pct(autres_cur, total_cur), bold=True, bg=(0xF8, 0xCB, 0xAD), align=PP_ALIGN.CENTER)
        var_a = autres_cur - autres_prv
        var_a_pct = (var_a / autres_prv * 100) if autres_prv > 0 else 0
        col_a = COLOR_BLUE_TXT if var_a >= 0 else COLOR_RED_TXT
        _set_cell(tbl.cell(r_idx, 6), _fmt_signed(var_a), bold=True, bg=(0xF8, 0xCB, 0xAD), align=PP_ALIGN.CENTER, color=col_a)
        _set_cell(tbl.cell(r_idx, 7), f"{round(var_a_pct)}%", bold=True, bg=(0xF8, 0xCB, 0xAD), align=PP_ALIGN.CENTER, color=col_a)

        # ── Ligne TOTAL MARCHE ──
        r_idx += 1
        _set_cell(tbl.cell(r_idx, 0), "", bg=(0xA9, 0xD0, 0x8E))
        _set_cell(tbl.cell(r_idx, 1), "TOTAL MARCHE", bold=True, bg=(0xA9, 0xD0, 0x8E))
        _set_cell(tbl.cell(r_idx, 2), _fmt_int(total_prv), bold=True, bg=(0xA9, 0xD0, 0x8E), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 3), "100%", bold=True, bg=(0xA9, 0xD0, 0x8E), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 4), _fmt_int(total_cur), bold=True, bg=(0xA9, 0xD0, 0x8E), align=PP_ALIGN.CENTER)
        _set_cell(tbl.cell(r_idx, 5), "100%", bold=True, bg=(0xA9, 0xD0, 0x8E), align=PP_ALIGN.CENTER)
        var_tm = total_cur - total_prv
        var_tm_pct = (var_tm / total_prv * 100) if total_prv > 0 else 0
        col_tm = COLOR_BLUE_TXT if var_tm >= 0 else COLOR_RED_TXT
        _set_cell(tbl.cell(r_idx, 6), _fmt_signed(var_tm), bold=True, bg=(0xA9, 0xD0, 0x8E), align=PP_ALIGN.CENTER, color=col_tm)
        _set_cell(tbl.cell(r_idx, 7), f"{round(var_tm_pct)}%", bold=True, bg=(0xA9, 0xD0, 0x8E), align=PP_ALIGN.CENTER, color=col_tm)

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

    def _replace_unit_teus_to_kgs(slide):
        """Remplace 'TEUS' -> 'KGS' et 'Teus' -> 'Kgs' dans tous les text frames
        (utile pour la section Aérien dont le template est en TEUS)."""
        def _walk(sh):
            try:
                if sh.shape_type == 6:
                    for sub in sh.shapes: _walk(sub)
                    return
                if hasattr(sh, 'has_table') and sh.has_table:
                    for row in sh.table.rows:
                        for cell in row.cells:
                            for para in cell.text_frame.paragraphs:
                                for run in para.runs:
                                    if run.text and ('TEUS' in run.text or 'Teus' in run.text or 'teus' in run.text):
                                        run.text = run.text.replace('TEUS', 'KGS').replace('Teus', 'Kgs').replace('teus', 'kgs')
                    return
                if hasattr(sh, 'text_frame') and sh.text_frame:
                    for para in sh.text_frame.paragraphs:
                        for run in para.runs:
                            if run.text and ('TEUS' in run.text or 'Teus' in run.text or 'teus' in run.text):
                                run.text = run.text.replace('TEUS', 'KGS').replace('Teus', 'Kgs').replace('teus', 'kgs')
            except Exception:
                pass
        for sh in slide.shapes: _walk(sh)

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
        # Liste noire (excluded_clients.json) — même filtrage que pour le dashboard
        merged = merged[~merged[client_col].apply(_is_excluded_client)]
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
            def _fmt(v): return f"{int(v):,}".replace(",", " ")
            vals = [str(i+1), str(row[client_col]), _fmt(tm), _fmt(ta), pdm, _fmt(vc),
                    conc_name, _fmt(tc_val), pdm_c]
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
        from pptx.oxml.ns import qn
        # Capture les pPr (puces, indentation) des paragraphes du template
        # P0 = "Nous notons" (bullet niv 0), P1 = "Les 10 Principaux" (no bullet),
        # P2 = ligne vide, P3..P12 = clients (bullet niv 1)
        existing = list(tf.paragraphs)
        tpl_p0 = existing[0] if len(existing) > 0 else None
        tpl_p1 = existing[1] if len(existing) > 1 else tpl_p0
        tpl_p2 = existing[2] if len(existing) > 2 else tpl_p1
        tpl_p_client = existing[3] if len(existing) > 3 else tpl_p0
        size, font_name = _capture_para_props(tpl_p0) if tpl_p0 else (Pt(12), None)
        size = size or Pt(12)

        # Vide tous les paragraphes existants (mais garde le premier comme support)
        for extra in existing[1:]:
            tf._txBody.remove(extra._p)
        # Ligne 1 : intro avec valeur en rouge — réutilise pPr de P0
        loss_str = f"{abs(total_loss):,}".replace(",", " ")
        p0 = tf.paragraphs[0]
        _clear_para_runs(p0)
        _add_run(p0, "Nous notons que les Volumes d'AGL sont en baisse ( ", size=size, font_name=font_name)
        _add_run(p0, f"{loss_str} {unit}", bold=True, color=COLOR_RED, size=size, font_name=font_name)
        _add_run(p0, ").", size=size, font_name=font_name)

        # Ligne 2 : pas de puce
        p1 = _add_paragraph_like(tf, tpl_p1)
        _add_run(p1, "Les 10 Principaux Acteurs de cette Baisse sont:", size=size, font_name=font_name)

        # Ligne vide
        _add_paragraph_like(tf, tpl_p2)

        # Top 10 clients : nom + variation AGL en rouge + (marché direction Hausse/Baisse)
        for _, row in top10.iterrows():
            agl_loss = abs(int(row['Variation']))
            market_var = int(row['Var_Marche'])
            market_dir = "Hausse" if market_var >= 0 else "Baisse"
            market_color = COLOR_BLUE if market_var >= 0 else COLOR_RED
            name = str(row[client_col])[:40]
            p = _add_paragraph_like(tf, tpl_p_client)
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
            from pptx.oxml.ns import qn
            existing = list(tf.paragraphs)
            template_para = existing[0] if existing else None
            size, font_name = _capture_para_props(template_para) if template_para else (Pt(11), None)
            size = size or Pt(11)
            # Réutilise les 2 premiers paragraphes du template (pour préserver les puces)
            if len(existing) >= 1:
                p0 = existing[0]
                _clear_para_runs(p0)
            else:
                p0 = tf.paragraphs[0]
            _add_run(p0, "Actifs ", bold=True, size=size, font_name=font_name)
            _add_run(p0, f"  = travaillé en {current_year} et pas en {previous_year}.",
                     size=size, font_name=font_name)
            if len(existing) >= 2:
                p1 = existing[1]
                _clear_para_runs(p1)
            else:
                p1 = _add_paragraph_like(tf, template_para)
            _add_run(p1, "Inactifs ", bold=True, size=size, font_name=font_name)
            _add_run(p1, f"= pas travaillé en {current_year} et travaillé en {previous_year}",
                     size=size, font_name=font_name)
            # Supprime paragraphes excédentaires
            all_p = tf._txBody.findall(qn('a:p'))
            for extra in all_p[2:]:
                tf._txBody.remove(extra)

    # ───────── Application ─────────
    slides = list(out_prs.slides)

    for slide in slides:
        slide_text = _slide_full_text(slide)
        s_already, s_title = _detect_context(slide_text)
        for sh in slide.shapes:
            apply_period_to_shape_recursive(sh,
                                            slide_already=s_already,
                                            slide_title=s_title)

    if len(slides) > 1:
        fill_market_overview(slides[1], sections_data, current_year, previous_year, label_periode, is_single_month)
        # Tableau dynamique Top 20 Transitaires (remplace l'image hardcodée du template)
        fill_top20_transitaires_board(slides[1], sections_data, current_year, previous_year, is_single_month)

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
            # Pour l'Aérien : remplacer 'TEUS' par 'KGS' dans les en-têtes du Top 20
            # (le template utilise TEUS partout par défaut)
            if str(mu).lower().startswith('kg'):
                _replace_unit_teus_to_kgs(slides[top20_idx])

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
        'comparison': comp, 'res_cur': res_cur, 'df_cible': df_cible,
        'client_col': ccol, 'metric_unit': metric_unit, 'data_type': dtype,
        'is_single': is_single,
    }


# ─────────────────────────────────────────────
#  UI STREAMLIT — PAGE RAPPORT PPTX STANDALONE
# ─────────────────────────────────────────────
def _render_marche_hors_integres_config(st, df=None, key_prefix="pptx"):
    """UI pour gérer dynamiquement les filtres de la slide 2 PPTX et du
    tableau TOP 20 du dashboard (transitaires intégrés + marchandises non
    compliance). Les modifications sont persistées dans des fichiers JSON.

    Parameters
    ----------
    df : pd.DataFrame or None
        Dataset chargé. Quand fourni, la section « marchandises non compliance »
        affiche un multiselect peuplé depuis les valeurs réelles du jeu de données
        (colonne *Libellé marchandise*), ce qui évite la saisie manuelle.
    key_prefix : str
        Préfixe unique pour les clés Streamlit — évite les collisions entre la
        page PPTX et le dashboard.
    """
    kp = key_prefix  # raccourci
    with st.expander("Configuration — Marché Hors Transitaires Intégrés (slide 2)",
                     expanded=False):
        st.caption(
            "Ces filtres sont appliqués automatiquement à la slide 2 du PPTX "
            "et au tableau TOP 20 TRANSITAIRES du dashboard. "
            "Les modifications sont sauvegardées dans `non_compliance_products.json` "
            "et `integrated_transitaires.json`."
        )

        # ─── Marchandises Non Compliance ───────────────────────────────────
        st.markdown("**Marchandises « non compliance » à exclure**")
        nc_patterns = load_non_compliance_patterns()

        lib_col = 'Libellé marchandise'
        has_lib = (df is not None and not df.empty and lib_col in df.columns)

        if has_lib:
            # Construire la liste des produits disponibles dans le dataset
            all_products = sorted(
                df[lib_col].dropna().astype(str).str.strip().str.upper().unique().tolist()
            )
            # Pré-sélection : produits du dataset correspondant aux patterns actifs
            pre_selected = [
                p for p in all_products
                if any(
                    pat.strip().upper() in p
                    for pat in nc_patterns
                )
            ]
            st.caption(
                f"{len(all_products)} produits disponibles dans les données. "
                "Sélectionnez ceux à exclure, puis cliquez sur **Appliquer**."
            )
            # ── formulaire : sélection sans rechargement ──────────────────
            with st.form(f"{kp}_nc_form", clear_on_submit=False):
                nc_selection = st.multiselect(
                    "Produits à exclure (non compliance)",
                    options=all_products,
                    default=pre_selected,
                    key=f"{kp}_nc_multiselect",
                    help="La sélection n'est prise en compte qu'après « Appliquer »."
                )
                submitted_nc = st.form_submit_button("Appliquer la sélection")
            if submitted_nc:
                if save_non_compliance_patterns(nc_selection):
                    st.success(f"{len(nc_selection)} produit(s) sauvegardé(s).")
                    st.rerun()
                else:
                    st.error("Échec de la sauvegarde.")
        else:
            # Fallback saisie manuelle (page PPTX sans données chargées)
            st.caption("Motifs recherchés (sous-chaîne, insensible à la casse) "
                       "dans la colonne *Libellé marchandise*. "
                       "Chargez un fichier de données pour obtenir une sélection dynamique.")
            with st.form(f"{kp}_nc_form", clear_on_submit=False):
                nc_input = st.text_area(
                    "Un motif par ligne",
                    value="\n".join(nc_patterns), height=120,
                    key=f"{kp}_nc_textarea",
                    help="Ex.: CONGEL, FRIPERIE, QUINCAILLERIE."
                )
                submitted_nc = st.form_submit_button("Appliquer")
            if submitted_nc:
                new_list = [ln.strip().upper() for ln in nc_input.splitlines()
                            if ln.strip()]
                if save_non_compliance_patterns(new_list):
                    st.success(f"{len(new_list)} motif(s) sauvegardé(s).")
                    st.rerun()
                else:
                    st.error("Échec de la sauvegarde.")

        st.caption(
            f"Actif : **{len(nc_patterns)}** entrée(s) — "
            f"{', '.join(nc_patterns[:5]) if nc_patterns else '(aucune)'}"
            + (" …" if len(nc_patterns) > 5 else "")
        )

        st.markdown("---")

        # ─── Transitaires Intégrés ─────────────────────────────────────────
        st.markdown("**Transitaires intégrés et leurs importateurs clés**")
        st.caption("Une ligne du dataset est exclue si SON *Transitaire* contient "
                   "le motif clé ET son *Destinataire* contient l'un des "
                   "importateurs associés.")
        integrated = load_integrated_transitaires()

        # Affichage tableau récapitulatif
        if integrated:
            recap = pd.DataFrame([
                {'Transitaire (motif)': k,
                 'Importateurs clés': ' | '.join(v),
                 'Nb importateurs': len(v)}
                for k, v in integrated.items()
            ])
            st.dataframe(recap, use_container_width=True, hide_index=True, height=240)

        # Ajouter / mettre à jour un transitaire
        # Construire les listes de choix depuis le dataset quand disponible
        has_trans_col = (df is not None and not df.empty and 'Transitaire' in df.columns)
        has_dest_col  = (df is not None and not df.empty and 'Destinataire' in df.columns)
        all_trans_opts = (
            sorted(df['Transitaire'].dropna().astype(str).str.strip().str.upper().unique().tolist())
            if has_trans_col else []
        )
        all_dest_opts = (
            sorted(df['Destinataire'].dropna().astype(str).str.strip().str.upper().unique().tolist())
            if has_dest_col else []
        )

        with st.form(f"{kp}_integrated_add_form", clear_on_submit=True):
            st.markdown("*Ajouter / mettre à jour un transitaire intégré*")
            cc1, cc2 = st.columns([1, 2])
            with cc1:
                if all_trans_opts:
                    new_trans = st.selectbox(
                        "Motif Transitaire",
                        options=[""] + all_trans_opts,
                        key=f"{kp}_new_trans",
                        help="Sélectionnez un transitaire présent dans les données."
                    )
                else:
                    new_trans = st.text_input(
                        "Motif Transitaire",
                        placeholder="Ex.: STRACOTRANS",
                        key=f"{kp}_new_trans"
                    )
            with cc2:
                if all_dest_opts:
                    # Pré-sélection : importateurs déjà associés à ce transitaire
                    existing_imps = integrated.get((new_trans or "").strip().upper(), [])
                    new_imps_list = st.multiselect(
                        "Importateurs clés",
                        options=all_dest_opts,
                        default=[d for d in existing_imps if d in all_dest_opts],
                        key=f"{kp}_new_imps_multi",
                        help="Sélectionnez les importateurs à associer à ce transitaire."
                    )
                    new_imps = None  # signale qu'on utilise new_imps_list
                else:
                    new_imps_list = None
                    new_imps = st.text_input(
                        "Importateurs clés (séparés par |)",
                        placeholder="Ex.: SOCIAM | NANO CI | COTIPLAST",
                        key=f"{kp}_new_imps"
                    )
            submitted_add = st.form_submit_button("Ajouter / Mettre à jour")
            if submitted_add:
                ikey = (new_trans or "").strip().upper()
                if new_imps_list is not None:
                    imps = [s.strip().upper() for s in new_imps_list if s.strip()]
                else:
                    imps = [s.strip().upper() for s in (new_imps or "").split('|')
                            if s.strip()]
                if not ikey or not imps:
                    st.warning("Sélectionnez un transitaire ET au moins un importateur.")
                else:
                    integrated[ikey] = imps
                    if save_integrated_transitaires(integrated):
                        st.success(f"« {ikey} » → {len(imps)} importateur(s) sauvegardé(s).")
                        st.rerun()
                    else:
                        st.error("Échec de la sauvegarde.")

        # Supprimer un transitaire — aussi dans un form pour éviter les rechargements
        if integrated:
            with st.form(f"{kp}_integrated_remove_form", clear_on_submit=True):
                st.markdown("*Supprimer un transitaire intégré*")
                to_remove = st.multiselect(
                    "Sélectionnez les transitaires à supprimer",
                    options=sorted(integrated.keys()),
                    key=f"{kp}_hti_remove_select"
                )
                rsub = st.form_submit_button("Supprimer")
                if rsub:
                    if to_remove:
                        for k in to_remove:
                            integrated.pop(k, None)
                        if save_integrated_transitaires(integrated):
                            st.success(f"{len(to_remove)} transitaire(s) supprimé(s).")
                            st.rerun()
                    else:
                        st.warning("Aucun transitaire sélectionné.")


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

    # ── Configuration « Marché Hors Transitaires Intégrés » (slide 2) ──────
    _render_marche_hors_integres_config(st)

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
            # Construire un label parseable contenant le NOM du mois (ex: "YTD Mars" / "Mars")
            try:
                _pm_int = int(period_month)
                _pm_name = MOIS_NUM_TO_NAME.get(_pm_int, str(period_month))
            except (TypeError, ValueError):
                _pm_name = str(period_month)
            label_periode = f"YTD {_pm_name}" if period_mode_key == 'YTD' else _pm_name

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
            # Mode "mois spécifique" => titres et tableaux utilisent le nom du mois
            # (ex: "Février 2026") plutôt que la forme YTD ("2 MOIS 2026")
            report_single = (period_mode_key == 'MOIS')
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
