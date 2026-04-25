import sys
import os

_portable_site = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python_portable", "Lib", "site-packages")
if os.path.isdir(_portable_site) and _portable_site not in sys.path:
    sys.path.insert(0, _portable_site)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import io

# Module externe pour la génération du rapport PPTX (page standalone)
from Insight_generation import render_pptx_page

COLUMN_NAMES_CACHE_FILE = os.path.join(os.path.dirname(__file__), '.column_names_cache.json')
EXCLUDED_CLIENTS_FILE = os.path.join(os.path.dirname(__file__), 'excluded_clients.json')

def load_column_names_cache():
    if os.path.exists(COLUMN_NAMES_CACHE_FILE):
        try:
            with open(COLUMN_NAMES_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_column_names_cache(cache_data):
    try:
        with open(COLUMN_NAMES_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except:
        pass

def clear_column_names_cache():
    if os.path.exists(COLUMN_NAMES_CACHE_FILE):
        try:
            os.remove(COLUMN_NAMES_CACHE_FILE)
        except:
            pass

# ─────────────────────────────────────────────
#  1. PAGE CONFIG & GLOBAL CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AGL | Analytics",
    page_icon=(
        next(
            (
                p for p in (
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images", "Logo_streamLit.png"),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images", "Logo _AGL.png"),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images", "Logo_AGL.ico"),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"),
                )
                if os.path.exists(p)
            ),
            "🌐",
        )
    ),
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""
<style>
#MainMenu {display: none !important;}
footer {display: none !important;}
header[data-testid="stHeader"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
button[kind="header"] {display: none !important;}
:root { color-scheme: light !important; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {
  background-color: #F0F3F8 !important;
  color: #1a2840 !important;
}
</style>
""", unsafe_allow_html=True)

ICON_UP      = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1f77b4" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
ICON_DOWN    = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>'
ICON_SETTINGS= '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93l-1.41 1.41M16.95 16.95l1.41 1.41M4.93 4.93l1.41 1.41M7.05 16.95l-1.41 1.41M21 12h-3M6 12H3M12 3V6m0 12v3"/></svg>'

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');

  html, body, [class*="css"], .stApp {{ font-family: 'DM Sans', sans-serif !important; background-color: #F0F3F8 !important; transition: all 0.3s ease; }}
  header[data-testid="stHeader"] {{ background-color: transparent !important; }}
  .block-container {{ padding: 0 2rem 2rem 2rem !important; max-width: 100% !important; }}

  section[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #001f4d 0%, #002d6e 60%, #003380 100%) !important; border-right: 1px solid rgba(229,168,35,0.2); min-width: 300px !important; width: 300px !important; transform: none !important; position: relative !important; display: flex !important; }}
  section[data-testid="stSidebar"] > div:first-child {{ width: 300px !important; }}
  section[data-testid="stSidebar"][aria-expanded="false"] {{ min-width: 300px !important; width: 300px !important; transform: none !important; margin-left: 0 !important; display: flex !important; }}
  [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
  section[data-testid="stSidebar"] * {{ color: #e8edf5 !important; }}
  section[data-testid="stSidebar"] .stMarkdown h2 {{ color: #E5A823 !important; font-weight: 600 !important; font-size: 0.7rem !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; border-bottom: 1px solid rgba(229,168,35,0.3) !important; padding-bottom: 6px !important; }}
  [data-testid="collapsedControl"] {{ display: none !important; }}
  button[data-testid="stSidebarCollapseButton"] {{ display: none !important; }}
  [data-testid="stSidebarNavCollapseIcon"] {{ display: none !important; }}
  section[data-testid="stSidebar"] button[kind="headerNoPadding"] {{ display: none !important; }}
  section[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] {{ display: none !important; }}
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] {{ background: #E5A823 !important; border: 2px solid #E5A823 !important; border-radius: 8px !important; padding: 12px !important; box-shadow: 0 4px 12px rgba(229,168,35,0.25); }}
  section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{ background: #E5A823 !important; border: 2px dashed #001f4d !important; }}
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] label,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] p,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] div {{ color: #001f4d !important; font-size: 0.85rem !important; font-weight: 500 !important; }}
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{ background: #001f4d !important; color: #E5A823 !important; font-weight: 600 !important; border: none !important; border-radius: 6px !important; }}
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {{ background: #002d6e !important; color: #ffffff !important; }}
  section[data-testid="stSidebar"] .stButton button {{ background: rgba(229,168,35,0.15) !important; color: #E5A823 !important; border: 1px solid rgba(229,168,35,0.4) !important; font-weight: 600 !important; border-radius: 6px !important; }}
  section[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(229,168,35,0.3) !important; color: #ffffff !important; }}

  /* FIX: sidebar selectbox & multiselect lisibilité */
  section[data-testid="stSidebar"] [data-baseweb="select"] > div,
  section[data-testid="stSidebar"] [data-baseweb="select"] input,
  section[data-testid="stSidebar"] [data-baseweb="popover"] {{ background: #002d6e !important; border-color: rgba(229,168,35,0.4) !important; color: #e8edf5 !important; }}
  section[data-testid="stSidebar"] [data-baseweb="tag"] {{ background: rgba(229,168,35,0.25) !important; color: #e8edf5 !important; }}
  section[data-testid="stSidebar"] .stMultiSelect span {{ color: #e8edf5 !important; }}
  section[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="menu"] {{ background: #002d6e !important; }}
  section[data-testid="stSidebar"] [data-baseweb="option"] {{ background: #002d6e !important; color: #e8edf5 !important; }}
  section[data-testid="stSidebar"] [data-baseweb="option"]:hover {{ background: rgba(229,168,35,0.2) !important; }}
  section[data-testid="stSidebar"] [aria-selected="true"] {{ background: rgba(229,168,35,0.3) !important; }}
  section[data-testid="stSidebar"] label {{ color: #E5A823 !important; font-size: 0.75rem !important; font-weight: 600 !important; letter-spacing: 0.06em !important; text-transform: uppercase !important; }}
  section[data-testid="stSidebar"] .stCheckbox label {{ color: #e8edf5 !important; text-transform: none !important; letter-spacing: 0 !important; font-size: 0.85rem !important; }}

  .agl-topbar {{ background: linear-gradient(135deg, #001f4d 0%, #002d6e 100%); border-radius: 12px; padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,31,77,0.1); border: 1px solid rgba(229,168,35,0.15); }}
  .agl-topbar-title {{ font-family: 'Playfair Display', Georgia, serif; font-size: 1.5rem; font-weight: 700; color: #ffffff; line-height: 1.2; }}
  .agl-topbar-subtitle {{ font-size: 0.8rem; color: rgba(229,168,35,0.85); letter-spacing: 0.1em; text-transform: uppercase; margin-top: 4px; font-weight: 500; }}

  .step-header {{ background: #ffffff; padding: 12px 18px; border-left: 4px solid #E5A823; border-radius: 4px; margin: 20px 0 16px 0; font-weight: 600; color: #001f4d; font-size: 0.85rem; letter-spacing: 0.08em; text-transform: uppercase; border: 1px solid #e2e8f0; }}

  .log-box {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 4px; padding: 10px 14px; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; font-size: 0.85rem; color: #1a2840; }}
  .log-box-ok {{ border-left: 4px solid #34d399; }}
  .log-box-err {{ border-left: 4px solid #ef4444; color: #ef4444; font-weight: 500; }}

  .stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: transparent; padding: 0; border-bottom: 2px solid #e2e8f0 !important; margin-bottom: 20px; }}
  .stTabs [data-baseweb="tab"] {{ font-weight: 600; font-size: 0.85rem; color: #5a6a8a !important; background: transparent !important; padding: 10px 20px !important; border: none !important; border-radius: 0 !important; letter-spacing: 0.05em; }}
  .stTabs [aria-selected="true"] {{ color: #001f4d !important; border-bottom: 3px solid #E5A823 !important; }}
  .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

  .agl-section-title {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #001f4d; padding: 10px 0 8px 0; border-bottom: 1px solid #E5A823; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
  .agl-section-title-warn {{ border-bottom-color: #ef4444; }}

  .stDataFrame {{ border-radius: 6px; border: 1px solid #e2e8f0 !important; }}
  .stDataFrame thead tr th {{ background: #001f4d !important; color: #ffffff !important; font-size: 0.7rem !important; font-weight: 600 !important; letter-spacing: 0.06em !important; text-transform: uppercase !important; padding: 8px 12px !important; }}

  .agl-summary-block {{ background: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,31,77,0.04); border: 1px solid #e2e8f0; margin-bottom: 20px; transition: all 0.3s ease; }}
  .agl-summary-group {{ margin-bottom: 16px; }}
  .agl-summary-title {{ font-size: 1rem; color: #001f4d; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; font-weight: 600; }}
  .agl-summary-triangle {{ width: 0; height: 0; border-top: 6px solid transparent; border-bottom: 6px solid transparent; border-left: 10px solid #E5A823; }}
  .agl-summary-list {{ list-style-type: none; padding-left: 28px; margin: 0; }}
  .agl-summary-list li {{ font-size: 0.9rem; color: #1a2840; margin-bottom: 4px; position: relative; }}
  .agl-summary-list li::before {{ content: "•"; position: absolute; left: -14px; color: #001f4d; font-weight: bold; }}
  .val-pos {{ color: #1f77b4; font-weight: bold; margin-left: 10px; }}
  .val-neg {{ color: #ef4444; font-weight: bold; margin-left: 10px; }}
  .val-neu {{ color: #94a3b8; font-weight: bold; margin-left: 10px; }}

  .stSlider > label {{ color: #001f4d !important; font-weight: 600 !important; text-transform: uppercase; font-size: 0.75rem !important; letter-spacing: 0.05em; }}
  [data-baseweb="slider"] [role="slider"] {{ background-color: #E5A823 !important; border-color: #E5A823 !important; }}
  [data-testid="stSliderTrack"] > div:first-child {{ background: rgba(229,168,35,0.25) !important; }}
  [data-testid="stSliderTrack"] > div:nth-child(2) {{ background: #E5A823 !important; }}

  .filter-warning {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 10px 14px; margin: 8px 0; font-size: 0.82rem; color: #856404; }}
  .filter-info {{ background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 6px; padding: 10px 14px; margin: 8px 0; font-size: 0.82rem; color: #0c5460; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  2. SESSION STATE INIT
# ─────────────────────────────────────────────
for key, val in [
    ('validated', False),
    ('sheet_confirmed', False),
    ('df_propre', None),
    ('client_col', None),
    ('is_single_month', False),
    ('data_type', 'maritime'),
    ('metric_unit', 'Teus'),
    ('pptx_data', None),
    ('show_confirm_purge', False),
    # FIX: stocker la selection liste noire sans reloader
    ('blacklist_pending_add', []),
    ('blacklist_pending_remove', []),
    # Cache des options filtres rapport
    ('rpt_pays_options', []),
    ('rpt_commodity_options', []),
]:
    if key not in st.session_state:
        st.session_state[key] = val

def reset_validation():
    st.session_state.validated = False
    st.session_state.sheet_confirmed = False
    st.session_state.pptx_data = None


# ─────────────────────────────────────────────
#  3. CONFIGURATION COLONNES & CACHE
# ─────────────────────────────────────────────

def load_excluded_clients():
    if os.path.exists(EXCLUDED_CLIENTS_FILE):
        try:
            with open(EXCLUDED_CLIENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('excluded_clients', [])
        except:
            return []
    return []

def save_excluded_clients(clients_list):
    try:
        with open(EXCLUDED_CLIENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'excluded_clients': clients_list}, f, ensure_ascii=False, indent=2)
    except:
        pass

def add_excluded_clients(new_clients):
    current = load_excluded_clients()
    updated = list(set(current + new_clients))
    save_excluded_clients(updated)

def remove_excluded_clients(clients_to_remove):
    current = load_excluded_clients()
    updated = [c for c in current if c not in clients_to_remove]
    save_excluded_clients(updated)

def _is_excluded_client(name):
    up = str(name).upper().strip()
    excluded_list = load_excluded_clients()
    excluded_upper = {c.upper() for c in excluded_list}
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

MOIS_NUM_TO_NAME = {1:'Janvier',2:'Février',3:'Mars',4:'Avril',5:'Mai',6:'Juin',
                    7:'Juillet',8:'Août',9:'Septembre',10:'Octobre',11:'Novembre',12:'Décembre'}

def normalize_mois_column(series):
    """
    Convertit une colonne Mois en noms français, que les valeurs soient
    numériques (1, 2, 3, 3.0...) ou déjà des noms.
    FIX: résout le problème "YTD 3.0" pour les fichiers aériens.
    """
    def _convert(val):
        if pd.isna(val):
            return None
        # Essayer conversion numérique d'abord
        try:
            n = int(float(str(val).strip()))
            if 1 <= n <= 12:
                return MOIS_NUM_TO_NAME[n]
        except (ValueError, TypeError):
            pass
        # Déjà un nom de mois
        s = str(val).strip()
        if s in MOIS_NUM_TO_NAME.values():
            return s
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

@st.cache_data
def get_sheet_names(f): return pd.ExcelFile(f).sheet_names

@st.cache_data
def scan_all_sheets(f, sheet_names):
    best, best_m = sheet_names[0], -1
    for s in sheet_names:
        df_tmp = pd.read_excel(f, sheet_name=s, nrows=5)
        up = [str(c).upper() for c in df_tmp.columns]
        m_mar = sum(1 for al in EXPECTED_COLS.values() if any(a in up for a in al))
        m_aer = sum(1 for al in EXPECTED_COLS_AERIEN.values() if any(a in up for a in al))
        m = max(m_mar, m_aer)
        if m > best_m: best_m, best = m, s
    return best


@st.cache_data
def get_stats_annee(df_annee, annee, client_col):
    if df_annee.empty:
        return pd.DataFrame(columns=[client_col, f'Total_Marche_{annee}', f'AGL_Volume_{annee}', f'PDM_{annee}'])
    stats = df_annee.groupby(client_col).agg(
        Total_Marche=('NOMBRE_TEU', 'sum'),
        AGL_Volume=('NOMBRE_TEU', lambda x: x[df_annee.loc[x.index, 'Transitaire'].astype(str).str.contains('AFRICA GLOBAL', case=False, na=False)].sum())
    ).reset_index()
    stats[f'PDM_{annee}'] = (stats['AGL_Volume'] / stats['Total_Marche']) * 100
    return stats.rename(columns={'Total_Marche': f'Total_Marche_{annee}', 'AGL_Volume': f'AGL_Volume_{annee}'})

@st.cache_data
def get_monthly_trend(df, client_col):
    trend = df.groupby(['Année escale', 'Mois escale', client_col, 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
    total_market = trend.groupby(['Année escale', 'Mois escale', client_col])['NOMBRE_TEU'].sum().reset_index().rename(columns={'NOMBRE_TEU': 'Total_Marche'})
    trend = pd.merge(trend, total_market, on=['Année escale', 'Mois escale', client_col])
    trend['PDM'] = (trend['NOMBRE_TEU'] / trend['Total_Marche']) * 100
    mois_dict = {'Janvier':1,'Février':2,'Mars':3,'Avril':4,'Mai':5,'Juin':6,'Juillet':7,'Août':8,'Septembre':9,'Octobre':10,'Novembre':11,'Décembre':12}
    trend['Mois_Num'] = trend['Mois escale'].map(mois_dict)
    trend = trend.sort_values(['Année escale', 'Mois_Num'])
    trend['Date_Label'] = trend['Mois escale'] + " " + trend['Année escale'].astype(str)
    return trend

def get_global_column_names():
    cache = load_column_names_cache()
    if 'global_column_names' not in st.session_state:
        st.session_state['global_column_names'] = cache.get('global_column_names', {})
    return st.session_state['global_column_names']

def save_global_column_names(names_dict):
    st.session_state['global_column_names'] = names_dict
    cache = load_column_names_cache()
    cache['global_column_names'] = names_dict
    save_column_names_cache(cache)

def render_column_rename_interface(available_cols):
    with st.expander("PERSONNALISER LES NOMS DE COLONNES (s'applique a tous les tableaux)", expanded=False):
        st.caption("Les modifications sont sauvegardées automatiquement et persistantes entre les sessions.")
        global_names = get_global_column_names()
        cols = st.columns(min(4, len(available_cols)))
        new_names = {}
        for i, col in enumerate(available_cols):
            with cols[i % len(cols)]:
                current_name = global_names.get(col, col)
                new_name = st.text_input(f"{col}", value=current_name, key=f"global_col_rename_{i}", label_visibility="visible")
                new_names[col] = new_name if new_name else col
        if new_names != global_names:
            save_global_column_names(new_names)
        return new_names

def apply_column_names(df, label_periode=None, cur_year=None, prev_year=None):
    global_names = get_global_column_names()
    rename_map = {}
    for col in df.columns:
        if label_periode:
            base_col_search = col.replace(f' {label_periode.upper()}', '')
        else:
            base_col_search = col
        if col in global_names:
            rename_map[col] = global_names[col]
        elif base_col_search in global_names:
            new_name = global_names[base_col_search]
            if label_periode and label_periode.upper() in col:
                if cur_year:
                    new_name = new_name.replace(str(cur_year), f' {label_periode.upper()} {cur_year}')
                if prev_year:
                    new_name = new_name.replace(str(prev_year), f' {label_periode.upper()} {prev_year}')
            rename_map[col] = new_name
    return df.rename(columns=rename_map) if rename_map else df

def editable_dataframe(df, key_prefix, has_total_row=True, use_global_names=False, label_periode=None):
    if df is None or (hasattr(df, 'empty') and df.empty) or len(df) == 0:
        st.info("Aucune donnée à afficher.")
        return pd.DataFrame()

    df = df.copy().reset_index(drop=True)

    total_row = None
    df_data = df.copy()
    if has_total_row and len(df) > 0:
        first_col = df.columns[0]
        try:
            mask_total = df[first_col].astype(str).str.upper().str.contains('TOTAL', na=False)
            if mask_total.any():
                total_row = df[mask_total].copy()
                df_data = df[~mask_total].copy()
        except:
            pass

    if use_global_names:
        global_names = get_global_column_names()
        display_cols = [global_names.get(c, c) for c in df_data.columns]
        col_mapping = {global_names.get(c, c): c for c in df_data.columns}
    else:
        display_cols = list(df_data.columns)
        col_mapping = {c: c for c in df_data.columns}

    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        sort_col_display = st.selectbox("Trier par", options=["-- Aucun tri --"] + display_cols, key=f"sort_col_{key_prefix}", label_visibility="collapsed")
    with col_ctrl2:
        sort_order = st.radio("Ordre", options=["Desc", "Asc"], horizontal=True, key=f"sort_order_{key_prefix}", label_visibility="collapsed")

    if sort_col_display != "-- Aucun tri --":
        original_col = col_mapping.get(sort_col_display, sort_col_display)
        if original_col in df_data.columns:
            ascending = (sort_order == "Asc")
            try:
                df_data['_sort_key'] = pd.to_numeric(df_data[original_col], errors='coerce')
                df_data = df_data.sort_values(by='_sort_key', ascending=ascending, na_position='last')
                df_data = df_data.drop(columns=['_sort_key'])
            except:
                try:
                    df_data = df_data.sort_values(by=original_col, ascending=ascending)
                except:
                    pass

    if total_row is not None:
        df_display = pd.concat([df_data, total_row], ignore_index=True)
    else:
        df_display = df_data

    if use_global_names:
        df_final = apply_column_names(df_display, label_periode)
    else:
        df_final = df_display

    df_final.index = range(1, len(df_final) + 1)

    for col in df_final.columns:
        try:
            if df_final[col].dtype == 'object':
                numeric_vals = pd.to_numeric(df_final[col], errors='coerce')
                if numeric_vals.notna().sum() > 0.5 * len(df_final):
                    df_final[col] = numeric_vals.fillna(0).astype(int)
                else:
                    df_final[col] = df_final[col].fillna('').astype(str)
            elif pd.api.types.is_numeric_dtype(df_final[col]):
                df_final[col] = df_final[col].fillna(0)
        except:
            df_final[col] = df_final[col].astype(str)

    column_config = {}
    for col in df_final.columns:
        if 'PDM' in col.upper():
            # Stocker en fraction (0-1) et utiliser le preset "percent" :
            # ainsi le menu de formatage interactif des colonnes Streamlit
            # (« Percentage ») reste cohérent avec l'affichage par défaut
            # (au lieu de multiplier par 100 une valeur déjà en pourcent).
            try:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0) / 100.0
            except Exception:
                pass
            column_config[col] = st.column_config.NumberColumn(col, format="percent")

    st.dataframe(df_final, use_container_width=True, hide_index=True, column_config=column_config)
    return df_final


def format_view_table(df, label_periode, client_col, cur_year, prev_year):
    if df.empty: return pd.DataFrame()
    unit_upper = st.session_state.get('metric_unit', 'Teus').upper()

    col_tm_cur = f'Total_Marche_{cur_year}'
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_pd_cur = f'PDM_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'
    col_pd_prv = f'PDM_{prev_year}'

    cols_to_keep = [client_col, col_tm_cur, col_ag_cur, col_pd_cur]
    has_prev = col_tm_prv in df.columns
    if has_prev:
        cols_to_keep += [col_tm_prv, col_ag_prv, col_pd_prv, 'Variation_Volume']

    res = df[cols_to_keep].copy()

    total_row = {client_col: "TOTAL GLOBAL"}
    total_row[col_tm_cur] = res[col_tm_cur].sum()
    total_row[col_ag_cur] = res[col_ag_cur].sum()
    total_row[col_pd_cur] = (total_row[col_ag_cur] / total_row[col_tm_cur] * 100) if total_row[col_tm_cur] > 0 else 0

    if has_prev:
        total_row[col_tm_prv] = res[col_tm_prv].sum()
        total_row[col_ag_prv] = res[col_ag_prv].sum()
        total_row[col_pd_prv] = (total_row[col_ag_prv] / total_row[col_tm_prv] * 100) if total_row[col_tm_prv] > 0 else 0
        total_row['Variation_Volume'] = res['Variation_Volume'].sum()

    res = pd.concat([pd.DataFrame([total_row]), res], ignore_index=True)

    new_cols = ['CLIENTS', f'MARCHÉ {label_periode.upper()} {cur_year}', f'AGL {unit_upper} {cur_year}', f'PDM {cur_year}']
    if has_prev:
        new_cols += [f'MARCHÉ {label_periode.upper()} {prev_year}', f'AGL {unit_upper} {prev_year}', f'PDM {prev_year}', 'VARIATION']
    res.columns = new_cols

    res['CLIENTS'] = res['CLIENTS'].astype(str)
    for col in res.columns:
        if any(k in col for k in [unit_upper, 'VARIATION', 'MARCHÉ', 'PDM']):
            res[col] = res[col].fillna(0).astype(int)
    return res


def format_delta_html(val):
    def _fmt_space(value):
        return f"{abs(int(value)):,}".replace(",", " ")
    unit = st.session_state.get('metric_unit', 'Teus')
    if val > 0: return f'<span class="val-pos">+ {_fmt_space(val)} {unit}</span>'
    if val < 0: return f'<span class="val-neg">- {_fmt_space(val)} {unit}</span>'
    return f'<span class="val-neu">0 {unit}</span>'


# ─────────────────────────────────────────────
#  4. SIDEBAR & OPTIONS
# ─────────────────────────────────────────────
with st.sidebar:
    import base64, os as _os
    _logo_path = _os.path.join(_os.path.dirname(__file__), 'Images', 'Logo _AGL.png')
    try:
        with open(_logo_path, 'rb') as _f:
            _logo_b64 = base64.b64encode(_f.read()).decode()
        st.markdown(f'<div style="padding:20px 10px 4px 10px;text-align:center;background:linear-gradient(180deg,#001f4d 0%,#002d6e 100%);border-radius:8px;"><img src="data:image/png;base64,{_logo_b64}" style="width:240px;max-width:100%;display:block;margin:0 auto;" /></div>', unsafe_allow_html=True)
    except:
        st.markdown('<div style="padding:20px;text-align:center;color:#E5A823;font-weight:bold;font-size:1.2rem;">AGL Analytics</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:rgba(229,168,35,.25);margin:12px 0 20px;"></div>', unsafe_allow_html=True)

    # ─── Navigation principale (Dashboard / Rapport PPTX) ─────────────────
    st.markdown('<div style="font-weight:600;font-size:0.75rem;color:#E5A823;letter-spacing:0.1em;margin-bottom:10px;">MODE</div>', unsafe_allow_html=True)
    app_mode = st.radio(
        "Navigation",
        ["Dashboard", "Rapport PPTX"],
        key="app_mode",
        label_visibility="collapsed",
    )
    st.markdown('<div style="height:1px;background:rgba(229,168,35,.25);margin:20px 0;"></div>', unsafe_allow_html=True)

    st.markdown('<div style="font-weight:600;font-size:0.75rem;color:#E5A823;letter-spacing:0.1em;margin-bottom:10px;">SOURCE DE DONNÉES</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Fichier Excel (.xlsx)", type=['xlsx'], label_visibility="collapsed", on_change=reset_validation)

    st.markdown('<div style="height:1px;background:rgba(229,168,35,.25);margin:20px 0;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:600;font-size:0.75rem;color:#E5A823;letter-spacing:0.1em;margin-bottom:10px;display:flex;align-items:center;gap:8px;">{ICON_SETTINGS} OPTIONS SYSTÈME</div>', unsafe_allow_html=True)

    if st.button("Purger le cache et réinitialiser", type="secondary"):
        st.session_state.show_confirm_purge = True

    if st.session_state.get('show_confirm_purge', False):
        st.warning("Êtes-vous sûr de vouloir purger le cache et réinitialiser l'application ?")
        col_y, col_n = st.columns(2)
        with col_y:
            if st.button("Oui, purger", type="primary"):
                st.cache_data.clear()
                clear_column_names_cache()
                st.session_state.clear()
                st.rerun()
        with col_n:
            if st.button("Annuler"):
                st.session_state.show_confirm_purge = False
                st.rerun()


# ─────────────────────────────────────────────
#  5. TOP BAR & IMPORT
# ─────────────────────────────────────────────

# ── Branche : page Rapport PPTX standalone ──
if st.session_state.get("app_mode", "Dashboard") == "Rapport PPTX":
    render_pptx_page(st)
    st.stop()

st.markdown("""
<div class="agl-topbar">
  <div>
    <div class="agl-topbar-title">Tableau de Bord Stratégique</div>
    <div class="agl-topbar-subtitle">Part de Marché & Analyse Concurrentielle</div>
  </div>
</div>
""", unsafe_allow_html=True)

if uploaded_file and not st.session_state.validated:
    st.markdown('<div class="step-header">PROCESSUS D\'IMPORTATION ET MAPPING</div>', unsafe_allow_html=True)

    with st.spinner("Chargement des feuilles Excel..."):
        sheet_names = get_sheet_names(uploaded_file)
        if 'best_sheet' not in st.session_state:
            st.session_state.best_sheet = scan_all_sheets(uploaded_file, sheet_names)

    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        selected_sheet = st.selectbox("Feuille Excel cible :", sheet_names, index=sheet_names.index(st.session_state.best_sheet))
    with col_s2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ANALYSER CETTE FEUILLE", type="secondary"):
            st.session_state.sheet_confirmed = True

    if st.session_state.sheet_confirmed:
        with st.spinner("Analyse de la feuille en cours..."):
            df_raw   = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            raw_cols = df_raw.columns.tolist()
            upper_cols = {str(c).upper(): c for c in raw_cols}

        data_type = detect_data_type(raw_cols)
        active_expected = EXPECTED_COLS_AERIEN if data_type == 'aerien' else EXPECTED_COLS
        active_optional = OPTIONAL_COLS_AERIEN if data_type == 'aerien' else OPTIONAL_COLS
        type_label = "AÉRIEN" if data_type == 'aerien' else "MARITIME"

        final_mapping   = {}
        all_required_ok = True

        st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
        st.markdown(f"<div class='log-box log-box-ok'>Mode détecté : <b>{type_label}</b></div>", unsafe_allow_html=True)
        st.markdown("<b style='font-size:0.9rem;'>RÉSULTAT DU SCAN AUTOMATIQUE :</b>", unsafe_allow_html=True)

        for std_col, aliases in active_expected.items():
            found = next((upper_cols[a] for a in aliases if a in upper_cols), None)
            if found:
                st.markdown(f"<div class='log-box log-box-ok'>Succès : <b>{std_col}</b> → <code>{found}</code></div>", unsafe_allow_html=True)
                final_mapping[std_col] = found
            else:
                st.markdown(f"<div class='log-box log-box-err'>Action requise : <b>{std_col}</b> introuvable.</div>", unsafe_allow_html=True)
                user_choice = st.selectbox(f"Assigner '{std_col}' manuellement :", ["-- Sélectionner --"] + raw_cols, key=f"req_{std_col}")
                if user_choice != "-- Sélectionner --":
                    final_mapping[std_col] = user_choice
                else:
                    all_required_ok = False

        st.markdown("<br><b style='font-size:0.9rem;'>COLONNES OPTIONNELLES :</b>", unsafe_allow_html=True)
        for std_col, aliases in active_optional.items():
            found = next((upper_cols[a] for a in aliases if a in upper_cols), None)
            if found:
                st.markdown(f"<div class='log-box log-box-ok'>Info : <b>{std_col}</b> → <code>{found}</code></div>", unsafe_allow_html=True)
                final_mapping[std_col] = found
            else:
                user_choice = st.selectbox(f"Représentation de '{std_col}' :", ["— Non mappée (ignorer) —"] + raw_cols, key=f"opt_{std_col}")
                if user_choice != "— Non mappée (ignorer) —":
                    final_mapping[std_col] = user_choice

        if all_required_ok:
            st.markdown("<br>", unsafe_allow_html=True)
            inverse_mapping = {v: k for k, v in final_mapping.items()}
            df_mapped = df_raw.rename(columns=inverse_mapping)

            flux_options = df_mapped['I_IMP_E_EXP'].dropna().unique()
            flux_choisi  = st.radio("SÉLECTION DU FLUX MÉTIER POUR LE DASHBOARD :", flux_options, horizontal=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("VALIDER ET ACCÉDER AU DASHBOARD", type="primary"):
                with st.spinner("Préparation du tableau de bord..."):
                    df_clean = df_mapped[df_mapped['I_IMP_E_EXP'] == flux_choisi].copy()

                    # FIX: toujours normaliser la colonne Mois escale (maritime et aérien)
                    df_clean['NOMBRE_TEU'] = clean_numeric_col(df_clean['NOMBRE_TEU'])
                    df_clean['Année escale'] = clean_numeric_col(df_clean['Année escale']).astype(int)
                    df_clean['Mois escale'] = normalize_mois_column(df_clean['Mois escale'])

                    st.session_state.validated    = True
                    st.session_state.df_propre    = df_clean
                    st.session_state.data_type    = data_type
                    st.session_state.metric_unit  = 'Kg' if data_type == 'aerien' else 'Teus'
                    flux_upper = str(flux_choisi).upper().strip()
                    st.session_state.client_col   = "Destinataire" if flux_upper.startswith('I') else "Chargeur"
                    annees = df_clean['Année escale'].dropna().unique()
                    st.session_state.is_single_month = len(annees) == 1
                    time.sleep(0.5)
                st.rerun()

elif not uploaded_file:
    st.markdown("""
    <div style="text-align:center;padding:48px 24px;background:#ffffff;border-radius:8px;border:1px solid #e2e8f0;">
      <div style="font-size:1.2rem;font-weight:600;color:#001f4d;margin-bottom:8px;">EN ATTENTE DE DONNÉES</div>
      <div style="font-size:0.9rem;color:#5a6a8a;max-width:500px;margin:0 auto;">Veuillez charger votre fichier Excel via le panneau de navigation latéral. L'outil procédera automatiquement au mapping.</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  5b. GÉNÉRATION RAPPORT PPTX
# ─────────────────────────────────────────────
TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DATA', 'template.pptx')

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
    # Liste noire (excluded_clients.json + mots-clés) appliquée comme dans le PPTX original
    c = c[~c[client_col].apply(_is_excluded_client)]
    col_ag_cur = f'AGL_Volume_{cur_year}'
    col_ag_prv = f'AGL_Volume_{prev_year}'
    col_tm_cur = f'Total_Marche_{cur_year}'
    col_tm_prv = f'Total_Marche_{prev_year}'

    c['Variation'] = c[col_ag_cur] - c[col_ag_prv]
    c['Var_Marche'] = c[col_tm_cur] - c[col_tm_prv]
    c['PDM_prv'] = c.apply(lambda r: r[col_ag_prv] / r[col_tm_prv] if r[col_tm_prv] > 0 else 0, axis=1)
    c['PDM_cur'] = c.apply(lambda r: r[col_ag_cur] / r[col_tm_cur] if r[col_tm_cur] > 0 else 0, axis=1)
    # Test PDM sur la valeur ARRONDIE affichée (>= 95%) — aligné sur l'original
    c['_PDM_prv_pct'] = (c['PDM_prv'] * 100).round().astype(int)
    c['_PDM_cur_pct'] = (c['PDM_cur'] * 100).round().astype(int)

    active_both = c[(c[col_tm_prv] > 0) & (c[col_tm_cur] > 0)]
    captive = active_both[(active_both['_PDM_prv_pct'] >= 95) & (active_both['_PDM_cur_pct'] >= 95) &
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
    idx_align = Alignment(horizontal='right')
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
#  GÉNÉRATION PPTX
# ─────────────────────────────────────────────
def generate_pptx_report(sections_data, label_periode, is_single_month):
    import copy
    from pptx import Presentation
    from pptx.util import Pt
    from lxml import etree

    # FIX: Déterminer les années dynamiquement depuis les données réelles
    all_years = set()
    for sec_data in sections_data.values():
        df_cible = sec_data.get('df_cible', pd.DataFrame())
        if 'Année escale' in df_cible.columns:
            valid_years = [int(y) for y in df_cible['Année escale'].dropna().unique() if int(y) > 2000]
            all_years.update(valid_years)
    current_year = int(max(all_years)) if all_years else pd.Timestamp.now().year
    previous_year = current_year - 1

    # FIX: Extraire le mois depuis label_periode dynamiquement
    MOIS_ALL = list(MOIS_NUM_TO_NAME.values())
    MOIS_ALL_UPPER = [m.upper() for m in MOIS_ALL]

    # Déterminer le mois cible depuis le label_periode (ex: "YTD Mars" -> "Mars", "Mars" -> "Mars")
    label_words = label_periode.strip().split()
    period_month_name = None
    for word in reversed(label_words):
        if word.capitalize() in MOIS_ALL:
            period_month_name = word.capitalize()
            break
        if word.upper() in MOIS_ALL_UPPER:
            period_month_name = MOIS_ALL[MOIS_ALL_UPPER.index(word.upper())]
            break
    if period_month_name is None:
        period_month_name = MOIS_ALL[-1]  # fallback: dernier mois connu

    if not os.path.isfile(TEMPLATE_FILE):
        available = [f for f in os.listdir(os.path.dirname(TEMPLATE_FILE)) if f.endswith('.pptx')]
        raise FileNotFoundError(
            f"Template PPTX introuvable : {TEMPLATE_FILE}\n"
            f"Fichiers .pptx disponibles : {available if available else 'Aucun'}"
        )

    out_prs = Presentation(TEMPLATE_FILE)

    # ── Helpers texte ───────────────────────────────────────────────────────

    def _set_run_text(run, text):
        run.text = text

    def _set_paragraph_text(para, text):
        if para.runs:
            para.runs[0].text = text
            for r in para.runs[1:]:
                r.text = ""
        else:
            para.text = text

    def _set_shape_text(shape, new_text):
        if shape is None or not hasattr(shape, 'text_frame'):
            return
        tf = shape.text_frame
        if tf.paragraphs and tf.paragraphs[0].runs:
            tf.paragraphs[0].runs[0].text = new_text
            for r in tf.paragraphs[0].runs[1:]:
                r.text = ""
        else:
            tf.paragraphs[0].text = new_text

    # ── Remplacement des dates/périodes — version entièrement dynamique ──────

    def replace_period_in_text(text):
        """
        FIX: Remplace toutes les occurrences de dates/mois dans une chaîne.
        Utilise current_year et previous_year calculés dynamiquement.
        """
        if not text or not isinstance(text, str):
            return text

        import re
        result = text

        # Remplacer les paires d'années (ex: 2024/2025 ou 2024-2025)
        # FIX: ignorer yr_offset=1 si old_cur == previous_year pour éviter
        # de remplacer l'année précédente correcte (ex: VS 2025 → VS 2026)
        for yr_offset in range(1, 8):
            old_cur = current_year - yr_offset
            old_prv = old_cur - 1
            # Si old_cur EST l'année précédente, les années sont déjà correctes
            # dans le template, ne pas les remplacer
            if old_cur == previous_year:
                continue
            result = result.replace(f'{old_prv}/{old_cur}', f'{previous_year}/{current_year}')
            result = result.replace(f'{old_prv}-{old_cur}', f'{previous_year}-{current_year}')
            result = result.replace(str(old_cur), str(current_year))
            result = result.replace(str(old_prv), str(previous_year))

        # FIX: Remplacer les noms de mois dynamiquement
        period_upper = period_month_name.upper()
        period_title = period_month_name

        # Déterminer si YTD ou mois seul
        is_ytd = 'YTD' in label_periode.upper()

        # Expressions CUMUL
        cumul_prefixes_upper = ['CUMUL A FIN ', 'CUMUL À FIN ', 'CUMUL AU MOIS DE ', 'CUMUL ']
        cumul_prefixes_title = ['Cumul a fin ', 'Cumul à fin ', 'Cumul au mois de ', 'Cumul ']

        for mu, mt in zip(MOIS_ALL_UPPER, MOIS_ALL):
            for prefix_u in cumul_prefixes_upper:
                result = result.replace(f'{prefix_u}{mu}', f'{prefix_u}{period_upper}')
            for prefix_t in cumul_prefixes_title:
                result = result.replace(f'{prefix_t}{mt}', f'{prefix_t}{period_title}')

        # Mois standalone (majuscules et titre) — uniquement si différent du mois cible
        for mu, mt in zip(MOIS_ALL_UPPER, MOIS_ALL):
            if mu != period_upper:
                result = result.replace(mu, period_upper)
            if mt != period_title and mt != period_month_name:
                result = result.replace(mt, period_title)

        return result

    def apply_period_to_run(run):
        if run.text:
            new_text = replace_period_in_text(run.text)
            if new_text != run.text:
                run.text = new_text

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
                            for run in para.runs:
                                apply_period_to_run(run)
                            if not para.runs and para.text:
                                new_text = replace_period_in_text(para.text)
                                if new_text != para.text:
                                    para.text = new_text
                return
            if hasattr(shape, 'text_frame') and shape.text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        apply_period_to_run(run)
                    if not para.runs and para.text:
                        new_text = replace_period_in_text(para.text)
                        if new_text != para.text:
                            para.text = new_text
        except Exception:
            pass

    def find_table(slide):
        for sh in slide.shapes:
            if sh.has_table:
                return sh.table
        return None

    def find_textbox_containing(slide, text_fragment):
        frag_upper = text_fragment.upper()
        best_sh = None
        for sh in slide.shapes:
            try:
                if hasattr(sh, 'text') and sh.text and frag_upper in sh.text.upper():
                    best_sh = sh
            except:
                pass
        return best_sh

    # ── Remplissage slide Market Overview ───────────────────────────────────

    def fill_market_overview(slide, sections_data, current_year, previous_year, label_per, is_single):
        total_marche_cur = 0; total_agl_cur = 0
        total_marche_prv = 0; total_agl_prv = 0

        col_tm_cur = f'Total_Marche_{current_year}'
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_tm_prv = f'Total_Marche_{previous_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'

        for sec_name, sd in sections_data.items():
            comp = sd['comparison']
            if col_tm_cur in comp.columns:
                total_marche_cur += int(comp[col_tm_cur].sum())
            if col_ag_cur in comp.columns:
                total_agl_cur += int(comp[col_ag_cur].sum())
            if not is_single and col_tm_prv in comp.columns:
                total_marche_prv += int(comp[col_tm_prv].sum())
            if not is_single and col_ag_prv in comp.columns:
                total_agl_prv += int(comp[col_ag_prv].sum())

        pdm_cur = f"{round(total_agl_cur / total_marche_cur * 100)}%" if total_marche_cur > 0 else "0%"
        pdm_prv = f"{round(total_agl_prv / total_marche_prv * 100)}%" if total_marche_prv > 0 else "0%"
        var_marche = total_marche_cur - total_marche_prv
        var_agl = total_agl_cur - total_agl_prv

        def _fmt(v):
            return f"{int(v):,}".replace(",", " ")

        tbl = find_table(slide)
        if tbl is not None:
            vals = [
                _fmt(total_marche_cur), _fmt(total_agl_cur), pdm_cur,
                _fmt(total_marche_prv), _fmt(total_agl_prv), pdm_prv,
                _fmt(var_marche), _fmt(var_agl)
            ]
            data_row_idx = 1 if len(tbl.rows) > 1 else 0
            for c_idx in range(min(len(vals), len(tbl.columns))):
                try:
                    cell = tbl.cell(data_row_idx, c_idx)
                    _set_paragraph_text(cell.text_frame.paragraphs[0], vals[c_idx])
                except:
                    pass

        for sh in slide.shapes:
            try:
                if not hasattr(sh, 'text_frame'):
                    continue
                for para in sh.text_frame.paragraphs:
                    for run in para.runs:
                        apply_period_to_run(run)
            except:
                pass

    def fill_synthese_table(slide, comp, metric_unit, label_per, is_single):
        tbl = find_table(slide)
        if tbl is None:
            return
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
            except:
                pass

    def fill_top20_table(slide, comp, df_cible, client_col, metric_unit, is_single):
        tbl = find_table(slide)
        if tbl is None:
            return
        col_tm_cur = f'Total_Marche_{current_year}'
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'

        df_c_cur = df_cible[df_cible['Année escale'] == current_year]
        if df_c_cur.empty:
            return

        dg = df_c_cur.groupby([client_col, 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
        do = dg[~dg['Transitaire'].astype(str).str.contains('AFRICA GLOBAL', case=False, na=False)]
        if do.empty:
            tc = pd.DataFrame(columns=[client_col, '1ER_CONC', 'TEUS_CONC'])
        else:
            tc = _select_primary_competitor_rows(do, client_col).rename(
                columns={'Transitaire': '1ER_CONC', 'NOMBRE_TEU': 'TEUS_CONC'})
        merged = pd.merge(comp, tc[[client_col, '1ER_CONC', 'TEUS_CONC']], on=client_col, how='left').fillna(0)
        merged['VOL_CONC'] = merged[col_tm_cur] - merged[col_ag_cur]
        mask_non_apure = merged['1ER_CONC'].apply(_is_non_apure)
        merged.loc[mask_non_apure & (merged['TEUS_CONC'] <= 0), 'TEUS_CONC'] = merged.loc[mask_non_apure & (merged['TEUS_CONC'] <= 0), 'VOL_CONC']
        if not is_single and col_ag_prv in merged.columns:
            merged['Variation'] = merged[col_ag_cur] - merged[col_ag_prv]
            # FIX: appliquer aussi le filtre PDM AGL < 50% (cohérence avec onglet Concurrence)
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
            vals = [str(i+1), str(row[client_col]), str(tm), str(ta), pdm, str(vc), conc_name, str(tc_val), pdm_c]
            for c in range(min(len(vals), len(tbl.columns))):
                if r_idx < len(tbl.rows):
                    try:
                        cell = tbl.cell(r_idx, c)
                        _set_paragraph_text(cell.text_frame.paragraphs[0], vals[c])
                    except:
                        pass

        for r_idx in range(len(merged) + 1, len(tbl.rows)):
            for c in range(len(tbl.columns)):
                try:
                    cell = tbl.cell(r_idx, c)
                    _set_paragraph_text(cell.text_frame.paragraphs[0], "")
                except:
                    pass

    def update_comments_text(slide, comp, metric_unit, client_col, is_single):
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
        lines = [f"Nous notons que les Volumes d'AGL sont en baisse ( {abs(total_loss):,} {unit}).".replace(",", " ")]
        lines.append("Les 10 Principaux Acteurs de cette Baisse sont:")
        lines.append("")
        for _, row in top10.iterrows():
            agl_loss = abs(int(row['Variation']))
            market_var = int(row['Var_Marche'])
            market_dir = "Hausse" if market_var >= 0 else "Baisse"
            name = str(row[client_col])[:40]
            lines.append(f"{name} - {agl_loss:,} {unit} ( {market_dir} de {abs(market_var):,} {unit})".replace(",", " "))
        best_sh = None; best_len = 0
        for sh in slide.shapes:
            if sh.shape_type == 17 and hasattr(sh, 'text'):
                if len(sh.text) > best_len and 'notons' in sh.text.lower():
                    best_len = len(sh.text); best_sh = sh
        if best_sh is None:
            for sh in slide.shapes:
                if sh.shape_type == 17 and hasattr(sh, 'text') and len(sh.text) > 100:
                    best_sh = sh; break
        if best_sh:
            tf = best_sh.text_frame
            tf.clear()
            for i, line in enumerate(lines):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                r = p.add_run(); r.text = line; r.font.size = Pt(9)

    def update_analyse_group(slide, comp, mu, is_single):
        col_ag_cur = f'AGL_Volume_{current_year}'
        col_ag_prv = f'AGL_Volume_{previous_year}'
        col_tm_cur = f'Total_Marche_{current_year}'
        col_tm_prv = f'Total_Marche_{previous_year}'
        if is_single:
            return
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

        def _fmt(val):
            v = int(val); s = f"{abs(v):,}".replace(",", " ")
            return f"+ {s}" if v >= 0 else f"- {s}"

        def _get_texts_recursive(group):
            texts = []
            for sh in group.shapes:
                if sh.shape_type == 6: texts.extend(_get_texts_recursive(sh))
                elif hasattr(sh, 'text') and sh.text.strip(): texts.append(sh.text)
            return texts

        def _set_shape_multiline(shape, text):
            tf = shape.text_frame
            saved_size, saved_bold, saved_color = None, None, None
            if tf.paragraphs and tf.paragraphs[0].runs:
                f = tf.paragraphs[0].runs[0].font
                saved_size = f.size; saved_bold = f.bold
                try: saved_color = f.color.rgb
                except: pass
            tf.clear()
            for i, line in enumerate(text.split('\n')):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                r = p.add_run(); r.text = line
                if saved_size: r.font.size = saved_size
                if saved_bold is not None: r.font.bold = saved_bold
                if saved_color: r.font.color.rgb = saved_color

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
                _set_shape_multiline(summary_sh, f"{n_pdm100} Clients à 100 % de PDM  {_fmt(total_pdm100)} {mu}")
                _set_shape_multiline(detail_sh,
                    f"{len(pdm100_up):02d} Clients qui ont une croissance  {_fmt(int(pdm100_up['Variation'].sum()))} {mu}\n"
                    f"{len(pdm100_down):02d} Clients qui ont une baisse         {_fmt(int(pdm100_down['Variation'].sum()))} {mu}")
            elif 'actifs' in combined.lower() and 'inactifs' in combined.lower():
                _set_shape_multiline(summary_sh, f"Clients Actifs et Inactifs  {_fmt(total_ai)} {mu}")
                _set_shape_multiline(detail_sh,
                    f"{n_actifs:02d} Clients Actifs en {current_year}        {_fmt(vol_actifs)} {mu}\n"
                    f"{n_inactifs:02d} Clients Inactifs en {current_year}      {_fmt(vol_inactifs)} {mu}")
            else:
                _set_shape_multiline(summary_sh, f"Autres Clients en Hausse et en Baisse  {_fmt(total_autres)} {mu}")
                _set_shape_multiline(detail_sh,
                    f"{len(others_up)} Clients qui ont une Hausse    {_fmt(int(others_up['Variation'].sum()))} {mu}\n"
                    f"{len(others_down)} Clients qui ont une baisse      {_fmt(int(others_down['Variation'].sum()))} {mu}")

        for sh in slide.shapes:
            if hasattr(sh, 'text') and 'travaillé en' in sh.text.lower():
                _set_shape_multiline(sh,
                    f"Actifs   = travaillé en {current_year} et pas en {previous_year}.\nInactifs = pas travaillé en {current_year} et travaillé en {previous_year}")
                break

    # ── Application mise à jour textes sur TOUTES les slides ────────────────
    slides = list(out_prs.slides)

    for slide in slides:
        for sh in slide.shapes:
            apply_period_to_shape_recursive(sh)

    # ── Slide 2 (Market Overview, index 1) ──────────────────────────────────
    if len(slides) > 1:
        fill_market_overview(slides[1], sections_data, current_year, previous_year, label_periode, is_single_month)

    # ── Mapping sections → slides ────────────────────────────────────────────
    section_map = {
        'Import Maritime':  (2, 3, 4),
        'Export Maritime':  (7, 8, 9),
        'Import Aérien':   (12, 13, 14),
    }

    for sec_name, (sep_idx, synth_idx, top20_idx) in section_map.items():
        if sec_name not in sections_data:
            continue
        sd = sections_data[sec_name]
        comp = sd['comparison']
        df_cible = sd['df_cible']
        ccol = sd['client_col']
        mu = sd['metric_unit']
        sec_single = sd.get('is_single', is_single_month)

        if synth_idx < len(slides):
            synth_slide = slides[synth_idx]
            fill_synthese_table(synth_slide, comp, mu, label_periode, sec_single)
            update_comments_text(synth_slide, comp, mu, ccol, sec_single)
            update_analyse_group(synth_slide, comp, mu, sec_single)

        if top20_idx < len(slides):
            top20_slide = slides[top20_idx]
            fill_top20_table(top20_slide, comp, df_cible, ccol, mu, sec_single)

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
#  5c. OVERRIDE — utiliser la version améliorée d'Insight_generation.py
# ─────────────────────────────────────────────
# Les fonctions ci-dessus restent disponibles mais sont surchargées par
# la version refactorisée qui gère le formatage couleur identique au template.
from Insight_generation import (
    generate_pptx_report,
    render_pptx_page,
    _render_marche_hors_integres_config,
)


# ─────────────────────────────────────────────
#  6. DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────
if st.session_state.validated:
    df_source  = st.session_state.df_propre
    client_col = st.session_state.client_col
    is_single_month = st.session_state.is_single_month

    dashboard_years = sorted(df_source['Année escale'].dropna().unique()) if 'Année escale' in df_source.columns else []
    current_display_year  = int(max(dashboard_years)) if dashboard_years else pd.Timestamp.now().year
    previous_display_year = current_display_year - 1

    mois_dict_ref = {'Janvier':1,'Février':2,'Mars':3,'Avril':4,'Mai':5,'Juin':6,
                     'Juillet':7,'Août':8,'Septembre':9,'Octobre':10,'Novembre':11,'Décembre':12}
    mois_presents_tries = sorted(df_source['Mois escale'].dropna().unique(), key=lambda x: mois_dict_ref.get(x, 99))

    with st.expander("PARAMÈTRES ET FILTRES GLOBAUX", expanded=True):
        has_prise_charge = 'Pays de prise en charge' in df_source.columns
        filter_cols = st.columns(5 if has_prise_charge else 4)
        with filter_cols[0]: analyse_type = st.radio("TYPE D'ANALYSE", ["Mois Spécifique", "Cumul (YTD)"])
        with filter_cols[1]: mois_cible = st.selectbox("PÉRIODE ANALYSÉE", mois_presents_tries)
        with filter_cols[2]:
            if st.session_state.get('data_type') == 'aerien':
                geo_label = "AÉROPORT D'ORIGINE"; geo_col_dash = 'Pays de livraison'
            elif has_prise_charge:
                geo_label = "PAYS DE PRISE EN CHARGE"; geo_col_dash = 'Pays de prise en charge'
            else:
                geo_label = "PAYS DE DESTINATION"; geo_col_dash = 'Pays de livraison'
            if geo_col_dash in df_source.columns:
                pays_prise_charge = st.multiselect(geo_label, df_source[geo_col_dash].dropna().unique())
            else: pays_prise_charge = []
        pays_livraison_extra = []
        if has_prise_charge:
            with filter_cols[3]:
                if 'Pays de livraison' in df_source.columns:
                    pays_livraison_extra = st.multiselect("PAYS DE LIVRAISON", df_source['Pays de livraison'].dropna().unique())
            cond_col_idx = 4
        else:
            cond_col_idx = 3
        with filter_cols[cond_col_idx]:
            cond_label = "MARCHANDISE" if st.session_state.get('data_type') == 'aerien' else "CONDITIONNEMENT"
            if 'Conditionnement' in df_source.columns:
                conditionnements = st.multiselect(cond_label, df_source['Conditionnement'].dropna().unique())
            else: conditionnements = []

    df_all = df_source.copy()
    if pays_prise_charge: df_all = df_all[df_all[geo_col_dash].isin(pays_prise_charge)]
    if pays_livraison_extra and 'Pays de livraison' in df_all.columns:
        df_all = df_all[df_all['Pays de livraison'].isin(pays_livraison_extra)]
    if conditionnements: df_all = df_all[df_all['Conditionnement'].isin(conditionnements)]

    mois_num = mois_dict_ref.get(mois_cible, 0)
    if analyse_type == "Cumul (YTD)":
        valid_months = [m for m in mois_presents_tries if mois_dict_ref.get(m, 0) <= mois_num]
        df_cible = df_all[df_all['Mois escale'].isin(valid_months)]
        label_periode = f"YTD {mois_cible}"
    else:
        df_cible = df_all[df_all['Mois escale'] == mois_cible]
        label_periode = mois_cible

    df_years = sorted(df_cible['Année escale'].dropna().unique())
    df_current_year  = int(max(df_years)) if df_years else current_display_year
    df_previous_year = df_current_year - 1

    res_cur = get_stats_annee(df_cible[df_cible['Année escale'] == df_current_year], df_current_year, client_col)
    if not is_single_month:
        res_prv = get_stats_annee(df_cible[df_cible['Année escale'] == df_previous_year], df_previous_year, client_col)
        comparison = pd.merge(res_prv, res_cur, on=client_col, how='outer').fillna(0)
    else:
        comparison = res_cur.copy()
        comparison[f'AGL_Volume_{df_previous_year}']   = 0
        comparison[f'Total_Marche_{df_previous_year}'] = 0
        comparison[f'PDM_{df_previous_year}']          = 0

    st.markdown("<br>", unsafe_allow_html=True)

    tab_globe, tab_agl, tab_evo, tab_conc, tab_raw = st.tabs([
        "GLOBAL OVERVIEW", "FOCUS AGL", "ÉVOLUTION PDM", "CONCURRENCE", "DONNÉES BRUTES"
    ])

    # ─────────────────────────────────────────────
    #  ONGLET GLOBAL OVERVIEW
    # ─────────────────────────────────────────────
    COUNTRY_COORDS = {
        "COTE D'IVOIRE": (7.54, -5.55), "COTE D IVOIRE": (7.54, -5.55), "IVORY COAST": (7.54, -5.55),
        "FRANCE": (46.60, 2.21), "BELGIQUE": (50.50, 4.47), "BELGIUM": (50.50, 4.47),
        "PAYS-BAS": (52.13, 5.29), "NETHERLANDS": (52.13, 5.29), "ALLEMAGNE": (51.17, 10.45),
        "GERMANY": (51.17, 10.45), "ESPAGNE": (40.46, -3.75), "SPAIN": (40.46, -3.75),
        "ITALIE": (41.87, 12.57), "ITALY": (41.87, 12.57), "PORTUGAL": (39.40, -8.22),
        "ROYAUME-UNI": (55.38, -3.44), "UNITED KINGDOM": (55.38, -3.44), "ANGLETERRE": (55.38, -3.44),
        "SUISSE": (46.82, 8.23), "TURQUIE": (38.96, 35.24), "TURKEY": (38.96, 35.24),
        "GRECE": (39.07, 21.82), "GREECE": (39.07, 21.82),
        "USA": (37.09, -95.71), "ETATS-UNIS": (37.09, -95.71), "UNITED STATES": (37.09, -95.71),
        "CANADA": (56.13, -106.35), "BRESIL": (-14.24, -51.93), "BRAZIL": (-14.24, -51.93),
        "ARGENTINE": (-38.42, -63.62), "COLOMBIE": (4.57, -74.30), "MEXIQUE": (23.63, -102.55),
        "CHILI": (-35.68, -71.54), "PEROU": (-9.19, -75.01),
        "CHINE": (35.86, 104.20), "CHINA": (35.86, 104.20), "INDE": (20.59, 78.96), "INDIA": (20.59, 78.96),
        "JAPON": (36.20, 138.25), "JAPAN": (36.20, 138.25), "COREE DU SUD": (35.91, 127.77),
        "SOUTH KOREA": (35.91, 127.77), "COREE": (35.91, 127.77),
        "VIETNAM": (14.06, 108.28), "THAILANDE": (15.87, 100.99), "THAILAND": (15.87, 100.99),
        "MALAISIE": (4.21, 101.98), "MALAYSIA": (4.21, 101.98), "INDONESIE": (-0.79, 113.92),
        "SINGAPOUR": (1.35, 103.82), "SINGAPORE": (1.35, 103.82), "PHILIPPINES": (12.88, 121.77),
        "PAKISTAN": (30.38, 69.35), "BANGLADESH": (23.68, 90.36), "SRI LANKA": (7.87, 80.77),
        "TAIWAN": (23.70, 120.96), "MYANMAR": (21.91, 95.96),
        "EMIRATS ARABES UNIS": (23.42, 53.85), "UAE": (23.42, 53.85), "ARABIE SAOUDITE": (23.89, 45.08),
        "SAUDI ARABIA": (23.89, 45.08), "QATAR": (25.35, 51.18), "OMAN": (21.47, 55.98),
        "KOWEIT": (29.31, 47.48), "BAHREIN": (26.07, 50.56), "JORDANIE": (30.59, 36.24),
        "LIBAN": (33.85, 35.86), "ISRAEL": (31.05, 34.85), "IRAK": (33.22, 43.68),
        "IRAN": (32.43, 53.69), "YEMEN": (15.55, 48.52), "DJIBOUTI": (11.83, 42.59),
        "SYRIE": (34.80, 38.99),
        "SENEGAL": (14.50, -14.45), "MALI": (17.57, -4.00), "BURKINA FASO": (12.24, -1.56),
        "GUINEE": (9.95, -9.70), "GUINEE-BISSAU": (11.80, -15.18), "GUINEE EQUATORIALE": (1.65, 10.27),
        "GAMBIE": (13.44, -15.31), "SIERRA LEONE": (8.46, -11.78),
        "LIBERIA": (6.43, -9.43), "GHANA": (7.95, -1.02), "TOGO": (8.62, 1.21),
        "BENIN": (9.31, 2.32), "NIGER": (17.61, 8.08), "NIGERIA": (9.08, 8.68),
        "CAMEROUN": (7.37, 12.35), "CAMEROON": (7.37, 12.35), "GABON": (-0.80, 11.61),
        "CONGO": (-4.26, 15.28), "CONGO (BRAZZA)": (-4.26, 15.28), "CONGO (BRAZZAVILLE)": (-4.26, 15.28),
        "REPUBLIQUE DEMOCRATIQUE DU CONGO": (-4.04, 21.76), "RDC": (-4.04, 21.76),
        "ANGOLA": (-11.20, 17.87), "MOZAMBIQUE": (-18.67, 35.53),
        "TANZANIE": (-6.37, 34.89), "KENYA": (-0.02, 37.91), "OUGANDA": (1.37, 32.29),
        "ETHIOPIE": (9.15, 40.49), "ERYTHREE": (15.18, 39.78), "SOMALIE": (5.15, 46.20),
        "MADAGASCAR": (-18.77, 46.87), "MAURICE": (-20.35, 57.55), "REUNION": (-21.12, 55.54),
        "COMORES": (-11.65, 43.33), "SEYCHELLES": (-4.68, 55.49),
        "AFRIQUE DU SUD": (-30.56, 22.94), "SOUTH AFRICA": (-30.56, 22.94), "NAMIBIE": (-22.96, 18.49),
        "ZIMBABWE": (-19.02, 29.15), "ZAMBIE": (-13.13, 27.85), "MALAWI": (-13.25, 34.30),
        "BOTSWANA": (-22.33, 24.68), "RWANDA": (-1.94, 29.87), "BURUNDI": (-3.37, 29.92),
        "TCHAD": (15.45, 18.73), "CENTRAFRIQUE": (6.61, 20.94), "SOUDAN": (12.86, 30.22),
        "EGYPTE": (26.82, 30.80), "EGYPT": (26.82, 30.80), "LIBYE": (26.34, 17.23),
        "TUNISIE": (33.89, 9.54), "ALGERIE": (28.03, 1.66), "MAROC": (31.79, -7.09), "MOROCCO": (31.79, -7.09),
        "MAURITANIE": (21.01, -10.94), "CAP-VERT": (16.00, -24.01),
        "AUSTRALIE": (-25.27, 133.78), "AUSTRALIA": (-25.27, 133.78), "NOUVELLE-ZELANDE": (-40.90, 174.89),
        "RUSSIE": (61.52, 105.32), "UKRAINE": (48.38, 31.17), "POLOGNE": (51.92, 19.15),
        "ROUMANIE": (45.94, 24.97), "HONGRIE": (47.16, 19.50), "AUTRICHE": (47.52, 14.55),
        "REPUBLIQUE TCHEQUE": (49.82, 15.47), "BULGARIE": (42.73, 25.49),
        "CROATIE": (45.10, 15.20), "SERBIE": (44.02, 21.01), "SUEDE": (60.13, 18.64),
        "NORVEGE": (60.47, 8.47), "DANEMARK": (56.26, 9.50), "FINLANDE": (61.92, 25.75),
        "IRLANDE": (53.14, -7.69), "CUBA": (21.52, -77.78), "HAITI": (18.97, -72.29),
        "JAMAIQUE": (18.11, -77.30), "TRINITE-ET-TOBAGO": (10.69, -61.22),
    }

    def _normalize_country(name):
        if pd.isna(name): return None
        s = str(name).upper().strip()
        s = s.replace("'", "'").replace("'", "'").replace("\u2019", "'")
        return s

    def _get_coords(country_name):
        norm = _normalize_country(country_name)
        if norm is None: return None
        if norm in COUNTRY_COORDS: return COUNTRY_COORDS[norm]
        for k, v in COUNTRY_COORDS.items():
            if k in norm or norm in k: return v
        return None

    with tab_globe:
        is_export_data = (client_col == 'Chargeur')
        has_prise_charge = 'Pays de prise en charge' in df_cible.columns
        has_livraison = 'Pays de livraison' in df_cible.columns
        if is_export_data:
            origin_col = 'Pays de prise en charge' if has_prise_charge else 'Pays de livraison'
            dest_col = 'Pays de livraison' if has_prise_charge else None
        else:
            origin_col = 'Pays de livraison'
            dest_col = 'Pays de prise en charge' if has_prise_charge else None

        has_geo = origin_col in df_cible.columns
        if not has_geo:
            st.info("Aucune donnée géographique disponible dans ce dataset.")
        else:
            unit_label = st.session_state.get('metric_unit', 'Teus')
            unit_upper_g = unit_label.upper()
            df_globe = df_cible.copy()

            total_vol = df_globe['NOMBRE_TEU'].sum()
            nb_countries = df_globe[origin_col].nunique()
            nb_clients = df_globe[client_col].nunique() if client_col in df_globe.columns else 0
            nb_transitaires = df_globe['Transitaire'].nunique()
            agl_vol = df_globe[df_globe['Transitaire'].astype(str).str.contains('AFRICA GLOBAL', case=False, na=False)]['NOMBRE_TEU'].sum()
            pdm_global = round(agl_vol / total_vol * 100) if total_vol > 0 else 0

            kpi_html = f"""
            <style>
            .globe-kpi-row {{display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;}}
            .globe-kpi {{flex:1; min-width:140px; background:linear-gradient(135deg,#1a1a2e,#16213e); border-radius:12px; padding:18px 16px; text-align:center; border:1px solid #0f3460; box-shadow:0 4px 15px rgba(0,0,0,0.3);}}
            .globe-kpi-val {{font-size:1.8rem; font-weight:800; background:linear-gradient(90deg,#E5A823,#f0c040); -webkit-background-clip:text; -webkit-text-fill-color:transparent;}}
            .globe-kpi-label {{font-size:0.72rem; color:#8892b0; text-transform:uppercase; letter-spacing:1.5px; margin-top:4px;}}
            .globe-kpi.agl .globe-kpi-val {{background:linear-gradient(90deg,#00c851,#00e676); -webkit-background-clip:text; -webkit-text-fill-color:transparent;}}
            .globe-kpi.pdm .globe-kpi-val {{background:linear-gradient(90deg,#2196F3,#42a5f5); -webkit-background-clip:text; -webkit-text-fill-color:transparent;}}
            </style>
            <div class="globe-kpi-row">
                <div class="globe-kpi"><div class="globe-kpi-val">{total_vol:,.0f}</div><div class="globe-kpi-label">Volume Total {unit_upper_g}</div></div>
                <div class="globe-kpi agl"><div class="globe-kpi-val">{agl_vol:,.0f}</div><div class="globe-kpi-label">Volume AGL</div></div>
                <div class="globe-kpi pdm"><div class="globe-kpi-val">{pdm_global}%</div><div class="globe-kpi-label">PDM Globale</div></div>
                <div class="globe-kpi"><div class="globe-kpi-val">{nb_countries}</div><div class="globe-kpi-label">Pays</div></div>
                <div class="globe-kpi"><div class="globe-kpi-val">{nb_clients}</div><div class="globe-kpi-label">Clients</div></div>
                <div class="globe-kpi"><div class="globe-kpi-val">{nb_transitaires}</div><div class="globe-kpi-label">Transitaires</div></div>
            </div>
            """
            st.markdown(kpi_html, unsafe_allow_html=True)

            country_agg = df_globe.groupby(origin_col).agg(
                Volume=('NOMBRE_TEU', 'sum'),
                Nb_Clients=(client_col, 'nunique') if client_col in df_globe.columns else ('NOMBRE_TEU', 'count'),
                Nb_Transitaires=('Transitaire', 'nunique'),
            ).reset_index()
            country_agg.rename(columns={origin_col: 'Pays'}, inplace=True)
            agl_by_country = df_globe[df_globe['Transitaire'].astype(str).str.contains('AFRICA GLOBAL', case=False, na=False)].groupby(origin_col)['NOMBRE_TEU'].sum().reset_index()
            agl_by_country.columns = ['Pays', 'AGL_Volume']
            country_agg = pd.merge(country_agg, agl_by_country, on='Pays', how='left').fillna(0)
            country_agg['PDM'] = (country_agg['AGL_Volume'] / country_agg['Volume'] * 100).round(1)
            country_agg['lat'] = country_agg['Pays'].apply(lambda x: (_get_coords(x) or (0, 0))[0])
            country_agg['lon'] = country_agg['Pays'].apply(lambda x: (_get_coords(x) or (0, 0))[1])
            country_agg = country_agg[(country_agg['lat'] != 0) | (country_agg['lon'] != 0)]

            if country_agg.empty:
                st.warning("Impossible de géolocaliser les pays du dataset.")
            else:
                fig = go.Figure()
                ci_coords = COUNTRY_COORDS.get("COTE D'IVOIRE", (7.54, -5.55))
                if dest_col and dest_col in df_globe.columns:
                    if is_export_data:
                        flow_agg = df_globe.groupby(dest_col)['NOMBRE_TEU'].sum().reset_index()
                    else:
                        flow_agg = df_globe.groupby(dest_col)['NOMBRE_TEU'].sum().reset_index()
                    flow_agg.columns = ['Dest', 'Volume']
                    flow_agg = flow_agg.sort_values('Volume', ascending=False)
                    fmax = flow_agg['Volume'].max() if not flow_agg.empty else 1
                    for _, frow in flow_agg.iterrows():
                        coords = _get_coords(frow['Dest'])
                        if coords is None: continue
                        if is_export_data:
                            lat_pair = [ci_coords[0], coords[0]]; lon_pair = [ci_coords[1], coords[1]]
                            arrow = f"CI → {frow['Dest']}"
                        else:
                            lat_pair = [coords[0], ci_coords[0]]; lon_pair = [coords[1], ci_coords[1]]
                            arrow = f"{frow['Dest']} → CI"
                        fig.add_trace(go.Scattergeo(
                            lat=lat_pair, lon=lon_pair, mode='lines',
                            line=dict(width=max(0.5, min(4, frow['Volume'] / fmax * 4)), color='rgba(229,168,35,0.4)'),
                            hoverinfo='text', text=f"{arrow}<br>{int(frow['Volume']):,} {unit_upper_g}", showlegend=False))
                else:
                    for _, crow in country_agg.iterrows():
                        if is_export_data:
                            lat_pair = [ci_coords[0], crow['lat']]; lon_pair = [ci_coords[1], crow['lon']]
                            arrow = f"CI → {crow['Pays']}"
                        else:
                            lat_pair = [crow['lat'], ci_coords[0]]; lon_pair = [crow['lon'], ci_coords[1]]
                            arrow = f"{crow['Pays']} → CI"
                        fig.add_trace(go.Scattergeo(
                            lat=lat_pair, lon=lon_pair, mode='lines',
                            line=dict(width=max(0.5, min(4, crow['Volume'] / country_agg['Volume'].max() * 4)), color='rgba(229,168,35,0.35)'),
                            hoverinfo='text', text=f"{arrow}<br>{int(crow['Volume']):,} {unit_upper_g}", showlegend=False))

                max_vol = country_agg['Volume'].max() if not country_agg.empty else 1
                country_agg['bubble_size'] = (country_agg['Volume'] / max_vol * 35).clip(lower=6)
                country_agg['color'] = country_agg['PDM'].apply(lambda p: '#00c851' if p >= 50 else ('#E5A823' if p >= 20 else '#ff5252'))

                fig.add_trace(go.Scattergeo(
                    lat=country_agg['lat'].tolist(), lon=country_agg['lon'].tolist(),
                    mode='markers+text',
                    marker=dict(size=country_agg['bubble_size'].tolist(), color=country_agg['color'].tolist(),
                                opacity=0.85, line=dict(width=1, color='white'), sizemode='diameter'),
                    text=country_agg['Pays'].apply(lambda x: str(x)[:15]).tolist(),
                    textposition='top center', textfont=dict(size=8, color='white'),
                    hovertemplate=(
                        '<b>%{customdata[0]}</b><br>'
                        f'Volume: %{{customdata[1]:,.0f}} {unit_upper_g}<br>'
                        f'AGL: %{{customdata[2]:,.0f}} {unit_upper_g}<br>'
                        'PDM: %{customdata[3]:.1f}%<br>Clients: %{customdata[4]}<br>Transitaires: %{customdata[5]}<extra></extra>'),
                    customdata=country_agg[['Pays', 'Volume', 'AGL_Volume', 'PDM', 'Nb_Clients', 'Nb_Transitaires']].values.tolist(),
                    showlegend=False))

                fig.add_trace(go.Scattergeo(
                    lat=[ci_coords[0]], lon=[ci_coords[1]], mode='markers',
                    marker=dict(size=18, color='#E5A823', symbol='star', line=dict(width=2, color='white')),
                    hovertemplate=f"<b>CÔTE D'IVOIRE</b><br>Hub AGL<extra></extra>", showlegend=False))

                flux_label_g = "EXPORT" if is_export_data else "IMPORT"
                fig.update_layout(
                    geo=dict(projection_type='orthographic', showland=True, landcolor='#1a1a2e',
                             showocean=True, oceancolor='#0a0a1a', showcountries=True, countrycolor='#2a2a4a',
                             showlakes=True, lakecolor='#0a0a1a', showcoastlines=True, coastlinecolor='#2a2a4a',
                             bgcolor='#0a0a1a', projection_rotation=dict(lon=-5, lat=10)),
                    paper_bgcolor='#0a0a1a', plot_bgcolor='#0a0a1a',
                    margin=dict(l=0, r=0, t=40, b=0), height=600,
                    title=dict(
                        text=f"<b>FLUX {flux_label_g} — {label_periode.upper()} {current_display_year}</b>",
                        font=dict(color='#E5A823', size=16), x=0.5, xanchor='center'),
                    dragmode='orbit')
                st.plotly_chart(fig, use_container_width=True, key="globe_chart")

                st.markdown("<hr style='border-color:#1a1a2e;margin:10px 0'>", unsafe_allow_html=True)
                col_tbl, col_chart = st.columns([3, 2], gap="large")
                with col_tbl:
                    st.markdown(f"<b style='color:#E5A823;'>TOP PAYS PAR VOLUME ({unit_upper_g})</b>", unsafe_allow_html=True)
                    top_countries = country_agg.sort_values('Volume', ascending=False).head(20)
                    disp_countries = top_countries[['Pays', 'Volume', 'AGL_Volume', 'PDM', 'Nb_Clients', 'Nb_Transitaires']].copy()
                    disp_countries.columns = ['PAYS', f'VOLUME {unit_upper_g}', f'AGL {unit_upper_g}', 'PDM %', 'CLIENTS', 'TRANSITAIRES']
                    for c in disp_countries.columns:
                        if c not in ('PAYS',): disp_countries[c] = disp_countries[c].fillna(0).astype(int)
                    disp_countries = disp_countries.reset_index(drop=True)
                    disp_countries.index = disp_countries.index + 1
                    st.dataframe(disp_countries, use_container_width=True, height=400)

                with col_chart:
                    st.markdown(f"<b style='color:#E5A823;'>RÉPARTITION PAR PAYS</b>", unsafe_allow_html=True)
                    top10 = country_agg.sort_values('Volume', ascending=False).head(10)
                    others_vol = country_agg.sort_values('Volume', ascending=False).iloc[10:]['Volume'].sum()
                    if others_vol > 0:
                        top10 = pd.concat([top10, pd.DataFrame([{'Pays': 'Autres', 'Volume': others_vol}])], ignore_index=True)
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=top10['Pays'].tolist(), values=top10['Volume'].tolist(), hole=0.45,
                        marker=dict(colors=['#E5A823','#f0c040','#00c851','#2196F3','#ff5252',
                                            '#9c27b0','#ff9800','#00bcd4','#8bc34a','#e91e63','#607d8b']),
                        textinfo='label+percent', textfont=dict(size=10), outsidetextfont=dict(size=9),
                        insidetextorientation='radial',
                        hovertemplate='<b>%{label}</b><br>%{value:,.0f} ' + unit_upper_g + '<br>%{percent}<extra></extra>')])
                    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                          margin=dict(l=10, r=10, t=10, b=10), height=400, showlegend=False)
                    st.plotly_chart(fig_pie, use_container_width=True, key="pie_chart")

                st.markdown("<hr style='border-color:#1a1a2e;margin:10px 0'>", unsafe_allow_html=True)
                st.markdown(f"<b style='color:#E5A823;'>TOP 15 TRANSITAIRES — VOLUMES {unit_upper_g}</b>", unsafe_allow_html=True)
                top_trans = df_globe.groupby('Transitaire')['NOMBRE_TEU'].sum().reset_index()
                top_trans = top_trans.sort_values('NOMBRE_TEU', ascending=True).tail(15)
                top_trans['is_agl'] = top_trans['Transitaire'].astype(str).str.contains('AFRICA GLOBAL', case=False, na=False)
                fig_bar = go.Figure(data=[go.Bar(
                    y=top_trans['Transitaire'].apply(lambda x: str(x)[:35]).tolist(),
                    x=top_trans['NOMBRE_TEU'].tolist(), orientation='h',
                    marker=dict(color=top_trans['is_agl'].apply(lambda x: '#E5A823' if x else '#2196F3').tolist(), line=dict(width=0)),
                    hovertemplate='<b>%{y}</b><br>%{x:,.0f} ' + unit_upper_g + '<extra></extra>')])
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      xaxis=dict(gridcolor='#1a1a2e', tickfont=dict(color='#8892b0')),
                                      yaxis=dict(tickfont=dict(color='#8892b0', size=9)),
                                      margin=dict(l=10, r=20, t=10, b=30), height=420)
                st.plotly_chart(fig_bar, use_container_width=True, key="bar_transitaires")

                # ── TABLEAU TOP 20 TRANSITAIRES (même contenu que slide 2 du PPTX) ──
                try:
                    from Insight_generation import compute_top20_transitaires_overview
                    if 'Année escale' in df_globe.columns:
                        years_avail = sorted(df_globe['Année escale'].dropna().unique().tolist())
                        if len(years_avail) >= 2:
                            cur_y = int(years_avail[-1]); prv_y = int(years_avail[-2])
                            # Mêmes filtres que la slide 2 (Marché Hors Transitaires Intégrés)
                            # uniquement pour les flux Import Maritime.
                            apply_hti_filter = (
                                client_col == 'Destinataire'
                                and st.session_state.get('data_type') != 'aerien'
                            )
                            board_df = compute_top20_transitaires_overview(
                                df_globe, cur_y, prv_y,
                                filter_marche_hors_integres=apply_hti_filter,
                            )
                            if not board_df.empty:
                                st.markdown("<hr style='border-color:#1a1a2e;margin:10px 0'>", unsafe_allow_html=True)
                                title_suffix = " — MARCHÉ HORS TRANSITAIRES INTÉGRÉS" if apply_hti_filter else ""
                                st.markdown(
                                    f"<b style='color:#E5A823;'>TABLEAU TOP 20 TRANSITAIRES{title_suffix} — "
                                    f"{prv_y} VS {cur_y}</b>",
                                    unsafe_allow_html=True)
                                # Les PDM et Variation % sont stockés en fraction (0-1) :
                                # on utilise le preset "percent" de Streamlit qui multiplie
                                # automatiquement par 100, ce qui rend l'affichage cohérent
                                # avec le menu « format → Percentage » de la colonne.
                                pct_cols = [c for c in board_df.columns
                                            if c.startswith('PDM ') or c == 'Variation %']
                                int_cols = [c for c in board_df.columns
                                            if c.startswith('Volume ') or c == "Variation d'unite"]
                                top20_col_cfg = {
                                    c: st.column_config.NumberColumn(c, format="percent")
                                    for c in pct_cols
                                }
                                for c in int_cols:
                                    top20_col_cfg[c] = st.column_config.NumberColumn(c, format="%d")
                                st.dataframe(board_df, use_container_width=True,
                                             hide_index=True, height=560,
                                             column_config=top20_col_cfg)
                except Exception as _e:
                    pass

            # ── Configuration filtres slide 2 / TOP 20 (dans le dashboard) ──
            if apply_hti_filter:
                _render_marche_hors_integres_config(st, df=df_globe, key_prefix="dash")

    # ─────────────────────────────────────────────
    #  FONCTION render_dashboard
    # ─────────────────────────────────────────────
    def render_dashboard(comp_df, prefix_key, is_single, label_per):
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            seuil_pdm = st.slider("SEUIL DE PDM (%) POUR LE RÉSUMÉ :", min_value=10, max_value=100, value=95, step=1, key=f"slider_{prefix_key}")

        rd_years = sorted(df_source['Année escale'].dropna().unique()) if 'Année escale' in df_source.columns else []
        rd_cur_year  = int(max(rd_years)) if rd_years else pd.Timestamp.now().year
        rd_prv_year  = rd_cur_year - 1

        col_ag_cur = f'AGL_Volume_{rd_cur_year}'
        col_ag_prv = f'AGL_Volume_{rd_prv_year}'
        col_tm_cur = f'Total_Marche_{rd_cur_year}'
        col_tm_prv = f'Total_Marche_{rd_prv_year}'
        col_pd_cur = f'PDM_{rd_cur_year}'
        col_pd_prv = f'PDM_{rd_prv_year}'

        mode_nouveaux = "Stricts (absents du marché l'année précédente)"
        if not is_single:
            with col_ctrl2:
                mode_nouveaux = st.radio("DÉFINITION DES NOUVEAUX CLIENTS :",
                    ["Stricts (absents du marché l'année précédente)", "Larges (aucun volume AGL l'année précédente)"],
                    key=f"mode_{prefix_key}")

        st.markdown("<hr style='margin: 10px 0 20px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

        if not is_single:
            comp_df['Variation_Volume'] = comp_df[col_ag_cur] - comp_df[col_ag_prv]

            if "Stricts" in mode_nouveaux:
                m_actifs_new = (comp_df[col_ag_cur] > 0) & (comp_df[col_tm_prv] == 0)
                m_inactifs   = (comp_df[col_ag_prv] > 0) & (comp_df[col_tm_cur] == 0)
            else:
                m_actifs_new = (comp_df[col_ag_cur] > 0) & (comp_df[col_ag_prv] == 0)
                m_inactifs   = (comp_df[col_ag_prv] > 0) & (comp_df[col_ag_cur] == 0)

            m_present = ~(m_actifs_new | m_inactifs) & ((comp_df[col_ag_cur] > 0) | (comp_df[col_ag_prv] > 0))
            m_seuil   = (comp_df[col_pd_cur] >= seuil_pdm) & (comp_df[col_pd_prv] >= seuil_pdm)
            m_crois   = comp_df['Variation_Volume'] >= 0
            m_baisse  = comp_df['Variation_Volume'] < 0

            df_100_crois  = comp_df[m_present & m_crois & m_seuil].sort_values('Variation_Volume', ascending=False)
            df_100_baisse = comp_df[m_present & m_baisse & m_seuil].sort_values('Variation_Volume')
            df_aut_crois  = comp_df[m_present & m_crois & ~m_seuil].sort_values('Variation_Volume', ascending=False)
            df_aut_baisse = comp_df[m_present & m_baisse & ~m_seuil].sort_values('Variation_Volume')
            df_new  = comp_df[m_actifs_new].sort_values('Variation_Volume', ascending=False)
            df_lost = comp_df[m_inactifs].sort_values('Variation_Volume')

            vol_100       = df_100_crois['Variation_Volume'].sum() + df_100_baisse['Variation_Volume'].sum()
            vol_act_inact = df_new['Variation_Volume'].sum() + df_lost['Variation_Volume'].sum()
            vol_aut       = df_aut_crois['Variation_Volume'].sum() + df_aut_baisse['Variation_Volume'].sum()

            html_str = f"""
            <div class="agl-summary-block">
                <div class="agl-summary-group">
                    <div class="agl-summary-title"><div class="agl-summary-triangle"></div><span>{len(df_100_crois) + len(df_100_baisse)} Clients à ≥ {seuil_pdm}% de PDM {format_delta_html(vol_100)}</span></div>
                    <ul class="agl-summary-list">
                        <li><b>{len(df_100_crois):02d}</b> Clients qui ont une croissance {format_delta_html(df_100_crois['Variation_Volume'].sum())}</li>
                        <li><b>{len(df_100_baisse):02d}</b> Clients qui ont une baisse {format_delta_html(df_100_baisse['Variation_Volume'].sum())}</li>
                    </ul>
                </div>
                <div class="agl-summary-group">
                    <div class="agl-summary-title"><div class="agl-summary-triangle"></div><span>Clients Actifs et Inactifs {format_delta_html(vol_act_inact)}</span></div>
                    <ul class="agl-summary-list">
                        <li><b>{len(df_new):02d}</b> Clients Actifs en {rd_cur_year} {format_delta_html(df_new['Variation_Volume'].sum())}</li>
                        <li><b>{len(df_lost):02d}</b> Clients Inactifs en {rd_cur_year} {format_delta_html(df_lost['Variation_Volume'].sum())}</li>
                    </ul>
                </div>
                <div class="agl-summary-group" style="margin-bottom:0;">
                    <div class="agl-summary-title"><div class="agl-summary-triangle"></div><span>Autres Clients {format_delta_html(vol_aut)}</span></div>
                    <ul class="agl-summary-list">
                        <li><b>{len(df_aut_crois):02d}</b> Clients en hausse  {format_delta_html(df_aut_crois['Variation_Volume'].sum())}</li>
                        <li><b>{len(df_aut_baisse):02d}</b> Clients en baisse {format_delta_html(df_aut_baisse['Variation_Volume'].sum())}</li>
                    </ul>
                </div>
            </div>
            """
            st.markdown(html_str.replace('\n', ''), unsafe_allow_html=True)

            col_g, col_d = st.columns(2, gap="large")
            with col_g:
                st.markdown(f'<div class="agl-section-title">{ICON_UP} PDM ≥ {seuil_pdm}% · CROISSANCE & STABLES</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_100_crois, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_100c")
                st.markdown(f'<div class="agl-section-title" style="margin-top:16px">{ICON_UP} NOUVEAUX CLIENTS ACTIFS</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_new, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_new")
                st.markdown(f'<div class="agl-section-title" style="margin-top:16px">{ICON_UP} AUTRES CLIENTS EN HAUSSE & STABLES</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_aut_crois, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_autc")
            with col_d:
                st.markdown(f'<div class="agl-section-title agl-section-title-warn">{ICON_DOWN} PDM ≥ {seuil_pdm}% · DÉCROISSANCE</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_100_baisse, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_100b")
                st.markdown(f'<div class="agl-section-title agl-section-title-warn" style="margin-top:16px">{ICON_DOWN} CLIENTS PERDUS (INACTIFS)</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_lost, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_lost")
                st.markdown(f'<div class="agl-section-title agl-section-title-warn" style="margin-top:16px">{ICON_DOWN} AUTRES CLIENTS EN BAISSE</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_aut_baisse, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_autb")
        else:
            df_100 = comp_df[comp_df[col_pd_cur] >= seuil_pdm].sort_values(col_ag_cur, ascending=False)
            df_aut = comp_df[comp_df[col_pd_cur] < seuil_pdm].sort_values(col_ag_cur, ascending=False)
            col_g, col_d = st.columns(2, gap="large")
            with col_g:
                st.markdown(f'<div class="agl-section-title">{ICON_UP} CLIENTS PDM ≥ {seuil_pdm}%</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_100, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_100")
            with col_d:
                st.markdown(f'<div class="agl-section-title agl-section-title-warn">{ICON_DOWN} AUTRES CLIENTS (< {seuil_pdm}%)</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_aut, label_per, client_col, rd_cur_year, rd_prv_year), f"{prefix_key}_aut")

    # ─────────────────────────────────────────────
    #  ONGLETS
    # ─────────────────────────────────────────────
    with tab_agl:
        unit_upper = st.session_state.get('metric_unit', 'Teus').upper()
        cols_for_rename = ['CLIENTS',
                           f'MARCHÉ {label_periode.upper()} {current_display_year}',
                           f'AGL {unit_upper} {current_display_year}',
                           f'PDM {current_display_year}']
        if not is_single_month:
            cols_for_rename += [f'MARCHÉ {label_periode.upper()} {previous_display_year}',
                                f'AGL {unit_upper} {previous_display_year}',
                                f'PDM {previous_display_year}', 'VARIATION']
        render_column_rename_interface(cols_for_rename)

        comp_agl = comparison[(comparison[f'AGL_Volume_{df_current_year}'] > 0) |
                              (comparison[f'AGL_Volume_{df_previous_year}'] > 0)].copy()
        render_dashboard(comp_agl, "agl", is_single_month, label_periode)

        # ── TABLEAUX SECONDAIRES ──────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="agl-section-title" style="margin-top:8px;">TABLEAUX SECONDAIRES</div>', unsafe_allow_html=True)

        unit_upper_ts = st.session_state.get('metric_unit', 'Teus').upper()
        col_tm_cur_ts = f'Total_Marche_{df_current_year}'
        col_ag_cur_ts = f'AGL_Volume_{df_current_year}'
        col_tm_prv_ts = f'Total_Marche_{df_previous_year}'
        col_ag_prv_ts = f'AGL_Volume_{df_previous_year}'
        role_ts = 'IMPORTATEURS' if client_col == 'Destinataire' else 'EXPORTATEURS'

        ts_tab_top100, ts_tab_ceva, ts_tab_sdma, ts_tab_maersk = st.tabs([
            f"TOP 100 {role_ts}", "PORTEFEUILLE CEVA LOGISTICS", "PORTEFEUILLE SDMA", "PORTEFEUILLE MAERSK"
        ])

        with ts_tab_top100:
            st.markdown(f"**TOP 100 {role_ts} — {label_periode.upper()} {df_current_year}**")
            top100_ts = comparison.copy()
            top100_ts['_PDM_cur'] = (top100_ts[col_ag_cur_ts] / top100_ts[col_tm_cur_ts].clip(lower=1) * 100).round(1)
            if not is_single_month and col_ag_prv_ts in top100_ts.columns:
                top100_ts['_Var'] = (top100_ts[col_ag_cur_ts] - top100_ts[col_ag_prv_ts]).astype(int)
                top100_ts['_PDM_prv'] = (top100_ts[col_ag_prv_ts] / top100_ts[col_tm_prv_ts].clip(lower=1) * 100).round(1)
            top100_ts = top100_ts.sort_values(col_tm_cur_ts, ascending=False).head(100)

            disp_top100_cols = [client_col, col_tm_cur_ts, col_ag_cur_ts, '_PDM_cur']
            disp_top100_names = ['CLIENTS', f'MARCHÉ {unit_upper_ts} {df_current_year}',
                                 f'AGL {unit_upper_ts} {df_current_year}', f'PDM {df_current_year}']
            if not is_single_month and col_tm_prv_ts in top100_ts.columns:
                disp_top100_cols += [col_tm_prv_ts, col_ag_prv_ts, '_PDM_prv', '_Var']
                disp_top100_names += [f'MARCHÉ {unit_upper_ts} {df_previous_year}',
                                      f'AGL {unit_upper_ts} {df_previous_year}',
                                      f'PDM {df_previous_year}', 'VARIATION']

            disp_top100 = top100_ts[disp_top100_cols].copy()
            disp_top100.columns = disp_top100_names
            for c in disp_top100.columns:
                if c != 'CLIENTS':
                    disp_top100[c] = pd.to_numeric(disp_top100[c], errors='coerce').fillna(0).astype(int)
            disp_top100 = disp_top100.reset_index(drop=True)
            disp_top100.index = disp_top100.index + 1
            # PDM stockés en fraction (0-1) + preset "percent" : cohérent avec le
            # menu de format des colonnes Streamlit.
            for c in disp_top100.columns:
                if 'PDM' in c:
                    disp_top100[c] = disp_top100[c] / 100.0
            col_cfg_ts = {c: st.column_config.NumberColumn(c, format="percent")
                          for c in disp_top100.columns if 'PDM' in c}
            st.dataframe(disp_top100, use_container_width=True, hide_index=False, column_config=col_cfg_ts, height=500)

        for ts_tab_widget, (pattern, label) in zip(
            [ts_tab_ceva, ts_tab_sdma, ts_tab_maersk],
            [('CEVA', 'CEVA LOGISTICS'), ('SDMA', 'SDMA'), ('MAERSK', 'MAERSK')]
        ):
            with ts_tab_widget:
                st.markdown(f"**PORTEFEUILLE {label} — {label_periode.upper()} {df_current_year}**")
                df_cur_ts = df_cible[df_cible['Année escale'] == df_current_year]
                cf_ts = df_cur_ts[df_cur_ts['Transitaire'].astype(str).str.contains(pattern, case=False, na=False)]
                if cf_ts.empty:
                    st.info(f"Aucune donnée pour {label} sur cette période.")
                else:
                    portfolio_ts = cf_ts.groupby(client_col)['NOMBRE_TEU'].sum().reset_index()
                    portfolio_ts = portfolio_ts.sort_values('NOMBRE_TEU', ascending=False)
                    total_vol_ts = int(portfolio_ts['NOMBRE_TEU'].sum())
                    col_ptf_left, col_ptf_right = st.columns([4, 1])
                    with col_ptf_left:
                        portfolio_ts.columns = ['CLIENTS', unit_upper_ts]
                        portfolio_ts[unit_upper_ts] = portfolio_ts[unit_upper_ts].fillna(0).astype(int)
                        portfolio_ts = portfolio_ts.reset_index(drop=True)
                        portfolio_ts.index = portfolio_ts.index + 1
                        st.dataframe(portfolio_ts, use_container_width=True, hide_index=False, height=500)
                    with col_ptf_right:
                        st.metric(f"Total {unit_upper_ts}", f"{total_vol_ts:,}".replace(',', ' '))
                        st.metric("Nb Clients", len(portfolio_ts))

    with tab_evo:
        trend_data = get_monthly_trend(df_all, client_col)
        if not trend_data.empty:
            clients_list = trend_data[client_col].dropna().unique().tolist()
            if clients_list:
                selected_client = st.selectbox(f"SÉLECTIONNER UN {client_col.upper()} :", clients_list, key="evo_dest")
                df_filtered = trend_data[trend_data[client_col] == selected_client].copy().reset_index(drop=True)
                if not df_filtered.empty:
                    transitaires = df_filtered['Transitaire'].unique()
                    CONCURRENT_COLORS = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
                                         "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
                                         "#aec7e8","#ffbb78","#98df8a","#ff9896","#c5b0d5"]
                    color_idx = 0; color_map = {}
                    for t in transitaires:
                        if 'AFRICA GLOBAL' in str(t).upper(): color_map[t] = "#E5A823"
                        else: color_map[t] = CONCURRENT_COLORS[color_idx % len(CONCURRENT_COLORS)]; color_idx += 1
                    fig = go.Figure()
                    for transitaire in transitaires:
                        df_trans = df_filtered[df_filtered['Transitaire'] == transitaire]
                        lc = color_map.get(transitaire, "#c8d6e8")
                        lw = 4 if 'AFRICA GLOBAL' in str(transitaire).upper() else 2
                        ms = 9 if 'AFRICA GLOBAL' in str(transitaire).upper() else 6
                        fig.add_trace(go.Scatter(x=df_trans['Date_Label'].tolist(), y=df_trans['PDM'].tolist(),
                                                 mode='lines+markers', name=str(transitaire),
                                                 line=dict(color=lc, width=lw), marker=dict(size=ms)))
                    fig.update_layout(
                        title=f"ÉVOLUTION DE LA PDM — {selected_client}",
                        font=dict(family="DM Sans, sans-serif", color="#1a2840"),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=50, b=30, l=20, r=20),
                        title_font=dict(family="Playfair Display, serif", size=15, color="#001f4d"),
                        xaxis=dict(gridcolor="#e8eef6", linecolor="#d0d9ea", title=""),
                        yaxis=dict(gridcolor="#e8eef6", linecolor="#d0d9ea", title="PDM (%)"),
                        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1, orientation="v"))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Données insuffisantes pour ce client.")
            else:
                st.info("Aucun client disponible pour l'analyse.")
        else:
            st.info("Données insuffisantes pour tracer l'évolution temporelle.")

    # ─────────────────────────────────────────────
    #  ONGLET CONCURRENCE
    #  FIX: sélection liste noire sans rechargement
    # ─────────────────────────────────────────────
    with tab_conc:
        Y = df_current_year
        P = df_previous_year
        col_tm_Y = f'Total_Marche_{Y}'
        col_ag_Y = f'AGL_Volume_{Y}'
        col_ag_P = f'AGL_Volume_{P}'
        col_pd_Y = f'PDM_{Y}'

        df_cible_current = df_cible[df_cible['Année escale'] == Y]
        comp_filtered = pd.DataFrame()  # init vide

        if not df_cible_current.empty:
            df_comp = df_cible_current.groupby([client_col, 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
            df_others = df_comp[~df_comp['Transitaire'].astype(str).str.contains('AFRICA GLOBAL LOGISTICS', case=False, na=False)]
            top_comp = _select_primary_competitor_rows(df_others, client_col).rename(
                columns={'Transitaire': f'1ER CONCURRENT EN {Y}', 'NOMBRE_TEU': 'TEUS 1ER CONCURRENT'})

            comp = pd.merge(res_cur, top_comp[[client_col, f'1ER CONCURRENT EN {Y}', 'TEUS 1ER CONCURRENT']], on=client_col, how='left')
            comp['VOL. CONCURRENCE'] = comp[col_tm_Y] - comp[col_ag_Y]
            mask_non_apure = comp[f'1ER CONCURRENT EN {Y}'].apply(_is_non_apure)
            comp.loc[mask_non_apure & (comp['TEUS 1ER CONCURRENT'].fillna(0) <= 0), 'TEUS 1ER CONCURRENT'] = \
                comp.loc[mask_non_apure & (comp['TEUS 1ER CONCURRENT'].fillna(0) <= 0), 'VOL. CONCURRENCE']
            comp['PDM CONCURRENT'] = (comp['TEUS 1ER CONCURRENT'] / comp[col_tm_Y]) * 100
            comp = comp.fillna(0)

            if not is_single_month and col_ag_P in comparison.columns:
                comp = pd.merge(comp, comparison[[client_col, col_ag_P]], on=client_col, how='left')
                comp[col_ag_P] = comp[col_ag_P].fillna(0)
            else:
                comp[col_ag_P] = 0
            comp['Variation_AGL'] = comp[col_ag_Y] - comp[col_ag_P]

            # FIX: appliquer la liste noire depuis le fichier (lecture fraiche à chaque render)
            current_blacklist = load_excluded_clients()
            comp_no_blacklist = comp[~comp[client_col].apply(_is_excluded_client)]
            comp_filtered = comp_no_blacklist[(comp_no_blacklist['Variation_AGL'] < 0) & (comp_no_blacklist[col_pd_Y] <= 50)]

            if comp_filtered.empty:
                st.info("Aucun client en baisse avec PDM AGL ≤ 50% dans cette période.")
            else:
                comp_filtered = comp_filtered.copy()
                comp_filtered['Var_Marche_Moins_AGL'] = comp_filtered[col_tm_Y] - comp_filtered[col_ag_Y]
                comp_top20 = comp_filtered.nlargest(20, 'Var_Marche_Moins_AGL')

                unit_upper_conc = st.session_state.get('metric_unit', 'Teus').upper()
                col_marche_disp = f'MARCHÉ {label_periode.upper()} {Y}'
                col_agl_disp    = f'AGL {unit_upper_conc} {Y}'
                col_var_disp    = f'VAR MARCHÉ - AGL {unit_upper_conc}'
                conc_col_name   = f'1ER CONCURRENT {Y}'

                disp = comp_top20[[client_col, col_tm_Y, col_ag_Y, col_pd_Y,
                                   'VOL. CONCURRENCE', f'1ER CONCURRENT EN {Y}',
                                   'TEUS 1ER CONCURRENT', 'PDM CONCURRENT', 'Var_Marche_Moins_AGL']].copy()
                disp.columns = ['CLIENTS', col_marche_disp, col_agl_disp, 'PDM AGL',
                                'VOL. CONCURRENCE', conc_col_name,
                                f'{unit_upper_conc} CONCURRENT', 'PDM CONCURRENT', col_var_disp]

                disp[conc_col_name] = (disp[conc_col_name].astype(str)
                                       .replace('0', 'NON APURE').replace('0.0', 'NON APURE').replace('', 'NON APURE'))

                for col in disp.columns:
                    if any(k in col for k in [unit_upper_conc, 'VOL', 'MARCHÉ', 'PDM', 'VAR']):
                        disp[col] = disp[col].fillna(0).astype(int)

                st.markdown("<hr style='margin: 10px 0 20px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
                editable_dataframe(disp, "concurrence", has_total_row=False)
        else:
            st.info("Aucune donnée d'analyse concurrentielle pour cette période.")

        st.markdown("---")
        st.markdown("### CLIENTS NON DÉSIRABLES : GESTION DE LA LISTE NOIRE")

        # FIX: Obtenir la liste complète des clients disponibles (pas seulement comp_filtered)
        # On utilise comp (avant filtre liste noire) pour que les clients exclus restent sélectionnables
        all_clients_for_blacklist = []
        if not df_cible_current.empty and 'comp' in dir():
            all_clients_for_blacklist = sorted(comp[client_col].dropna().unique().tolist())

        current_blacklist = load_excluded_clients()

        # ── Section Ajouter à la liste noire ────────────────────────────────
        with st.expander("Sélectionner des clients à exclure des analyses", expanded=False):
            if not all_clients_for_blacklist:
                st.info("Aucun client disponible.")
            else:
                # Formulaire : la sélection ne déclenche PAS de rechargement —
                # seul le clic sur « Ajouter » provoque le rerun.
                with st.form("blacklist_add_form", clear_on_submit=True):
                    selected_for_exclusion = st.multiselect(
                        "Choisissez les clients à ajouter à la liste noire",
                        options=[c for c in all_clients_for_blacklist if c not in current_blacklist],
                        default=[],
                        key="exclusion_multiselect_conc"
                    )
                    submitted_add_bl = st.form_submit_button(
                        "Ajouter à la liste noire", type="primary"
                    )
                if submitted_add_bl:
                    if selected_for_exclusion:
                        add_excluded_clients(selected_for_exclusion)
                        st.success(f"{len(selected_for_exclusion)} client(s) ajouté(s) à la liste noire.")
                        st.rerun()
                    else:
                        st.warning("Aucun client sélectionné.")

                if current_blacklist:
                    preview = ', '.join(current_blacklist[:5])
                    if len(current_blacklist) > 5:
                        preview += f" … (+{len(current_blacklist)-5})"
                    st.info(f"Liste noire actuelle : {len(current_blacklist)} clients — {preview}")
                else:
                    st.info("Aucun client exclu pour l'instant.")

                if st.button("Vider la liste noire", type="secondary", key="btn_clear_blacklist"):
                    save_excluded_clients([])
                    st.success("Liste noire vidée.")
                    st.rerun()

        # ── Section Retirer de la liste noire ───────────────────────────────
        if current_blacklist:
            with st.expander("Retirer des clients de la liste noire", expanded=False):
                # Formulaire : aucun rechargement tant que l'utilisateur
                # n'a pas cliqué sur « Retirer ».
                with st.form("blacklist_remove_form", clear_on_submit=True):
                    to_remove = st.multiselect(
                        "Clients à retirer",
                        options=current_blacklist,
                        key="remove_multiselect_conc"
                    )
                    submitted_rm_bl = st.form_submit_button("Retirer de la liste noire")
                if submitted_rm_bl:
                    if to_remove:
                        remove_excluded_clients(to_remove)
                        st.success(f"{len(to_remove)} client(s) retiré(s).")
                        st.rerun()
                    else:
                        st.warning("Sélectionnez au moins un client.")

    with tab_raw:
        editable_dataframe(df_all, "raw_data", has_total_row=False)
