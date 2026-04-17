import sys
import os

# Garantir l'accès aux packages de python_portable (UV trampoline)
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
import importlib

def check_pptx_available():
    try:
        importlib.import_module('pptx')
        return True
    except Exception as e:
        print(f"[PPTX CHECK] Import failed: {type(e).__name__}: {e}")
        return False

# Fichier cache pour les noms de colonnes personnalisés
COLUMN_NAMES_CACHE_FILE = os.path.join(os.path.dirname(__file__), '.column_names_cache.json')

def load_column_names_cache():
    """Charge les noms de colonnes personnalisés depuis le fichier cache."""
    if os.path.exists(COLUMN_NAMES_CACHE_FILE):
        try:
            with open(COLUMN_NAMES_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_column_names_cache(cache_data):
    """Sauvegarde les noms de colonnes personnalisés dans le fichier cache."""
    try:
        with open(COLUMN_NAMES_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except:
        pass

def clear_column_names_cache():
    """Supprime le fichier cache des noms de colonnes."""
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
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Cacher menu + footer + forcer le mode clair
st.markdown("""
<style>
/* Cacher complètement le menu natif Streamlit */
#MainMenu {display: none !important;}
footer {display: none !important;}
header[data-testid="stHeader"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
button[kind="header"] {display: none !important;}

/* Forcer le mode clair (override du dark mode natif) */
:root {
  color-scheme: light !important;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {
  background-color: #F0F3F8 !important;
  color: #1a2840 !important;
}
</style>
""", unsafe_allow_html=True)

# ── SVG Icons (STRICTEMENT SANS EMOJIS) ────────────────────────────────────────
ICON_UP      = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1f77b4" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
ICON_DOWN    = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>'
ICON_SETTINGS= '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93l-1.41 1.41M16.95 16.95l1.41 1.41M4.93 4.93l1.41 1.41M7.05 16.95l-1.41 1.41M21 12h-3M6 12H3M12 3V6m0 12v3"/></svg>'

AGL_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 80" width="180">
  <ellipse cx="110" cy="18" rx="16" ry="11" fill="none" stroke="#E5A823" stroke-width="2"/>
  <ellipse cx="110" cy="18" rx="7" ry="11" fill="none" stroke="#E5A823" stroke-width="1.2"/>
  <line x1="94" y1="18" x2="126" y2="18" stroke="#E5A823" stroke-width="1.2"/>
  <path d="M109 10 c-1 0-3 1-3 3 s1 4 0 6 s2 3 3 2 s2-3 3-2 s1-4 0-6 s-2-3-3-3z" fill="#E5A823" opacity="0.7"/>
  <text x="110" y="52" font-family="Georgia, serif" font-size="26" font-weight="700" fill="#E5A823" text-anchor="middle" letter-spacing="6">AGL</text>
  <text x="110" y="66" font-family="'Trebuchet MS', sans-serif" font-size="7.5" fill="#E5A823" text-anchor="middle" letter-spacing="2.5">AFRICA GLOBAL LOGISTICS</text>
</svg>
"""

# BASE CSS
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');

  html, body, [class*="css"], .stApp {{ font-family: 'DM Sans', sans-serif !important; background-color: #F0F3F8 !important; transition: all 0.3s ease; }}
  header[data-testid="stHeader"] {{ background-color: transparent !important; }}
  .block-container {{ padding: 0 2rem 2rem 2rem !important; max-width: 100% !important; }}

  /* Sidebar - force always visible */
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
  /* File uploader - OR AGL box, Bleu AGL text */
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] {{ background: #E5A823 !important; border: 2px solid #E5A823 !important; border-radius: 8px !important; padding: 12px !important; box-shadow: 0 4px 12px rgba(229,168,35,0.25); }}
  section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{ background: #E5A823 !important; border: 2px dashed #001f4d !important; }}
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] label,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] p,
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] div {{ color: #001f4d !important; font-size: 0.85rem !important; font-weight: 500 !important; }}
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{ background: #001f4d !important; color: #E5A823 !important; font-weight: 600 !important; border: none !important; border-radius: 6px !important; }}
  section[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {{ background: #002d6e !important; color: #ffffff !important; }}
  /* Sidebar buttons (Purger etc.) */
  section[data-testid="stSidebar"] .stButton button {{ background: rgba(229,168,35,0.15) !important; color: #E5A823 !important; border: 1px solid rgba(229,168,35,0.4) !important; font-weight: 600 !important; border-radius: 6px !important; }}
  section[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(229,168,35,0.3) !important; color: #ffffff !important; }}
  
  /* Top bar */
  .agl-topbar {{ background: linear-gradient(135deg, #001f4d 0%, #002d6e 100%); border-radius: 12px; padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,31,77,0.1); border: 1px solid rgba(229,168,35,0.15); }}
  .agl-topbar-title {{ font-family: 'Playfair Display', Georgia, serif; font-size: 1.5rem; font-weight: 700; color: #ffffff; line-height: 1.2; }}
  .agl-topbar-subtitle {{ font-size: 0.8rem; color: rgba(229,168,35,0.85); letter-spacing: 0.1em; text-transform: uppercase; margin-top: 4px; font-weight: 500; }}
  
  .step-header {{ background: #ffffff; padding: 12px 18px; border-left: 4px solid #E5A823; border-radius: 4px; margin: 20px 0 16px 0; font-weight: 600; color: #001f4d; font-size: 0.85rem; letter-spacing: 0.08em; text-transform: uppercase; border: 1px solid #e2e8f0; }}
  
  /* Log box */
  .log-box {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 4px; padding: 10px 14px; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; font-size: 0.85rem; color: #1a2840; }}
  .log-box-ok {{ border-left: 4px solid #34d399; }}
  .log-box-err {{ border-left: 4px solid #ef4444; color: #ef4444; font-weight: 500; }}

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: transparent; padding: 0; border-bottom: 2px solid #e2e8f0 !important; margin-bottom: 20px; }}
  .stTabs [data-baseweb="tab"] {{ font-weight: 600; font-size: 0.85rem; color: #5a6a8a !important; background: transparent !important; padding: 10px 20px !important; border: none !important; border-radius: 0 !important; letter-spacing: 0.05em; }}
  .stTabs [aria-selected="true"] {{ color: #001f4d !important; border-bottom: 3px solid #E5A823 !important; }}
  .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
  
  /* Section titles */
  .agl-section-title {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #001f4d; padding: 10px 0 8px 0; border-bottom: 1px solid #E5A823; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
  .agl-section-title-warn {{ border-bottom-color: #ef4444; }}
  
  /* Dataframes */
  .stDataFrame {{ border-radius: 6px; border: 1px solid #e2e8f0 !important; }}
  .stDataFrame thead tr th {{ background: #001f4d !important; color: #ffffff !important; font-size: 0.7rem !important; font-weight: 600 !important; letter-spacing: 0.06em !text-transform: uppercase !important; padding: 8px 12px !important; }}
  
  /* Summary Block */
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

  /* Slider in Tab */
  .stSlider > label {{ color: #001f4d !important; font-weight: 600 !important; text-transform: uppercase; font-size: 0.75rem !important; letter-spacing: 0.05em; }}
  [data-baseweb="slider"] [role="slider"] {{ background-color: #E5A823 !important; border-color: #E5A823 !important; }}
  [data-testid="stSliderTrack"] > div:first-child {{ background: rgba(229,168,35,0.25) !important; }}
  [data-testid="stSliderTrack"] > div:nth-child(2) {{ background: #E5A823 !important; }}
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
    ('metric_unit', 'Teus')
]:
    if key not in st.session_state:
        st.session_state[key] = val

def reset_validation():
    st.session_state.validated = False
    st.session_state.sheet_confirmed = False


# ─────────────────────────────────────────────
#  3. CONFIGURATION COLONNES & CACHE
# ─────────────────────────────────────────────
EXPECTED_COLS = {
    'Transitaire':    ['TRANSITAIRE', 'FORWARDER', 'CONSIGNATAIRE'],
    'NOMBRE_TEU':     ['NOMBRE_TEU', 'VOLUME', 'TEUS', 'TEU', 'QTE'],
    'Mois escale':    ['MOIS ESCALE', 'MOIS', 'MONTH'],
    'Année escale':   ['ANNÉE ESCALE', 'ANNEE ESCALE', 'ANNEE', 'YEAR'],
    'I_IMP_E_EXP':    ['I_IMP_E_EXP', 'FLUX', 'SENS', 'TYPE']
}
OPTIONAL_COLS = {
    'Pays de livraison': ['PAYS DE LIVRAISON', 'PAYS DE LIVRA', 'PAYS', 'DESTINATION'],
    'Conditionnement':   ['CODE_CONDIT', 'CONDITIONNEMENT', 'TYPE CONTAINER', 'EQUIPEMENT', 'TAILLE']
}

# ── Configurations Aérien ──
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

PDM_COLUMN_CONFIG = {
    "PDM 2026": st.column_config.NumberColumn("PDM 2026", format="%d %%"),
    "PDM 2025": st.column_config.NumberColumn("PDM 2025", format="%d %%"),
    "PDM AGL":  st.column_config.NumberColumn("PDM AGL",  format="%d %%"),
    "PDM CONCURRENT": st.column_config.NumberColumn("PDM CONCURRENT", format="%d %%")
}

# Colonnes standard pour les tableaux AGL (utilisées pour le renommage global)
STANDARD_COLUMNS = [
    'CLIENTS', 'MARCHÉ 2026', 'AGL TEUS 2026', 'PDM 2026',
    'MARCHÉ 2025', 'AGL TEUS 2025', 'PDM 2025', 'VARIATION'
]

def get_global_column_names():
    """Récupère les noms de colonnes globaux depuis le cache."""
    cache = load_column_names_cache()
    if 'global_column_names' not in st.session_state:
        st.session_state['global_column_names'] = cache.get('global_column_names', {})
    return st.session_state['global_column_names']

def save_global_column_names(names_dict):
    """Sauvegarde les noms de colonnes globaux dans le cache."""
    st.session_state['global_column_names'] = names_dict
    cache = load_column_names_cache()
    cache['global_column_names'] = names_dict
    save_column_names_cache(cache)

def render_column_rename_interface(available_cols):
    """Affiche l'interface de renommage de colonnes pour tous les tableaux."""
    with st.expander("PERSONNALISER LES NOMS DE COLONNES (s'applique a tous les tableaux)", expanded=False):
        st.caption("Les modifications sont sauvegardées automatiquement et persistantes entre les sessions.")
        global_names = get_global_column_names()
        
        cols = st.columns(min(4, len(available_cols)))
        new_names = {}
        for i, col in enumerate(available_cols):
            with cols[i % len(cols)]:
                current_name = global_names.get(col, col)
                new_name = st.text_input(
                    f"{col}",
                    value=current_name,
                    key=f"global_col_rename_{i}",
                    label_visibility="visible"
                )
                new_names[col] = new_name if new_name else col
        
        # Sauvegarder si changement
        if new_names != global_names:
            save_global_column_names(new_names)
        
        return new_names

def apply_column_names(df, label_periode=None):
    """Applique les noms de colonnes personnalisés au DataFrame."""
    global_names = get_global_column_names()
    rename_map = {}
    
    for col in df.columns:
        # Chercher correspondance avec les colonnes standard (avec ou sans période)
        base_col = col
        if label_periode:
            # Normaliser pour la recherche: "MARCHÉ YTD MARS 2026" -> "MARCHÉ 2026"
            base_col_search = col.replace(f' {label_periode.upper()}', '')
        else:
            base_col_search = col
        
        # Chercher d'abord la colonne exacte, sinon la version sans période
        if col in global_names:
            rename_map[col] = global_names[col]
        elif base_col_search in global_names:
            # Appliquer le renommage en conservant la période
            new_name = global_names[base_col_search]
            if label_periode and label_periode.upper() in col:
                new_name = new_name.replace(' 2026', f' {label_periode.upper()} 2026').replace(' 2025', f' {label_periode.upper()} 2025')
            rename_map[col] = new_name
    
    return df.rename(columns=rename_map) if rename_map else df

# Fonction pour créer un éditeur avec tri (sans renommage par tableau)
def editable_dataframe(df, key_prefix, has_total_row=True, use_global_names=False, label_periode=None):
    """Affiche un DataFrame interactif avec tri via st.dataframe()."""
    if df is None or (hasattr(df, 'empty') and df.empty) or len(df) == 0:
        st.info("Aucune donnée à afficher.")
        return pd.DataFrame()
    
    # Créer une copie propre du DataFrame
    df = df.copy().reset_index(drop=True)
    
    # Séparer la ligne TOTAL si elle existe
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
    
    # Colonnes pour le tri
    if use_global_names:
        global_names = get_global_column_names()
        display_cols = [global_names.get(c, c) for c in df_data.columns]
        col_mapping = {global_names.get(c, c): c for c in df_data.columns}
    else:
        display_cols = list(df_data.columns)
        col_mapping = {c: c for c in df_data.columns}
    
    # Contrôles de tri
    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        sort_col_display = st.selectbox(
            "Trier par",
            options=["-- Aucun tri --"] + display_cols,
            key=f"sort_col_{key_prefix}",
            label_visibility="collapsed"
        )
    with col_ctrl2:
        sort_order = st.radio(
            "Ordre",
            options=["Desc", "Asc"],
            horizontal=True,
            key=f"sort_order_{key_prefix}",
            label_visibility="collapsed"
        )
    
    # Appliquer le tri
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
    
    # Remettre TOTAL à la fin
    if total_row is not None:
        df_display = pd.concat([df_data, total_row], ignore_index=True)
    else:
        df_display = df_data
    
    # Renommage global
    if use_global_names:
        df_final = apply_column_names(df_display, label_periode)
    else:
        df_final = df_display
    
    # Nettoyage des types pour compatibilité pyarrow
    for col in df_final.columns:
        try:
            # Convertir les colonnes numériques
            if df_final[col].dtype == 'object':
                # Vérifier si c'est une colonne numérique déguisée en object
                numeric_vals = pd.to_numeric(df_final[col], errors='coerce')
                if numeric_vals.notna().sum() > 0.5 * len(df_final):
                    df_final[col] = numeric_vals.fillna(0).astype(int)
                else:
                    df_final[col] = df_final[col].fillna('').astype(str)
            elif pd.api.types.is_numeric_dtype(df_final[col]):
                df_final[col] = df_final[col].fillna(0)
        except:
            df_final[col] = df_final[col].astype(str)
    
    # Configuration des colonnes pour PDM
    column_config = {}
    for col in df_final.columns:
        if 'PDM' in col.upper():
            column_config[col] = st.column_config.NumberColumn(col, format="%d %%")
    
    # Afficher avec st.dataframe interactif
    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )
    return df_final

def format_view_table(df, label_periode, client_col):
    """Prépare les données pour le data_editor avec Ligne Total intégrée et triée en haut."""
    if df.empty: return pd.DataFrame()
    unit_upper = st.session_state.get('metric_unit', 'Teus').upper()

    cols_to_keep = [client_col, 'Total_Marche_2026', 'AGL_Volume_2026', 'PDM_2026']
    if 'Total_Marche_2025' in df.columns:
        cols_to_keep += ['Total_Marche_2025', 'AGL_Volume_2025', 'PDM_2025', 'Variation_Volume']

    res = df[cols_to_keep].copy()

    total_row = {client_col: "TOTAL GLOBAL"}
    total_row['Total_Marche_2026'] = res['Total_Marche_2026'].sum()
    total_row['AGL_Volume_2026']   = res['AGL_Volume_2026'].sum()
    total_row['PDM_2026'] = (total_row['AGL_Volume_2026'] / total_row['Total_Marche_2026'] * 100) if total_row['Total_Marche_2026'] > 0 else 0

    if 'Total_Marche_2025' in res.columns:
        total_row['Total_Marche_2025'] = res['Total_Marche_2025'].sum()
        total_row['AGL_Volume_2025']   = res['AGL_Volume_2025'].sum()
        total_row['PDM_2025'] = (total_row['AGL_Volume_2025'] / total_row['Total_Marche_2025'] * 100) if total_row['Total_Marche_2025'] > 0 else 0
        total_row['Variation_Volume']  = res['Variation_Volume'].sum()

    res = pd.concat([pd.DataFrame([total_row]), res], ignore_index=True)

    new_cols = ['CLIENTS', f'MARCHÉ {label_periode.upper()} 2026', f'AGL {unit_upper} 2026', 'PDM 2026']
    if 'Total_Marche_2025' in df.columns:
        new_cols += [f'MARCHÉ {label_periode.upper()} 2025', f'AGL {unit_upper} 2025', 'PDM 2025', 'VARIATION']
    res.columns = new_cols

    # Assurer les types de colonnes pour compatibilité pyarrow
    res['CLIENTS'] = res['CLIENTS'].astype(str)
    for col in res.columns:
        if any(k in col for k in [unit_upper, 'VARIATION', 'MARCHÉ', 'PDM']):
            res[col] = res[col].fillna(0).astype(int)
    return res

def format_delta_html(val):
    unit = st.session_state.get('metric_unit', 'Teus')
    if val > 0: return f'<span class="val-pos">+ {int(val):,} {unit}</span>'
    if val < 0: return f'<span class="val-neg">- {abs(int(val)):,} {unit}</span>'
    return f'<span class="val-neu">0 {unit}</span>'


# ─────────────────────────────────────────────
#  4. SIDEBAR & OPTIONS
# ─────────────────────────────────────────────
with st.sidebar:
    import base64, os as _os
    _logo_path = _os.path.join(_os.path.dirname(__file__), 'Images', 'Logo _AGL.png')
    with open(_logo_path, 'rb') as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()
    st.markdown(f'<div style="padding:20px 10px 4px 10px;text-align:center;background:linear-gradient(180deg,#001f4d 0%,#002d6e 100%);border-radius:8px;"><img src="data:image/png;base64,{_logo_b64}" style="width:240px;max-width:100%;display:block;margin:0 auto;" /></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:rgba(229,168,35,.25);margin:12px 0 20px;"></div>', unsafe_allow_html=True)
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
                clear_column_names_cache()  # Supprime aussi le cache des noms de colonnes
                st.session_state.clear()
                st.rerun()
        with col_n:
            if st.button("Annuler"):
                st.session_state.show_confirm_purge = False
                st.rerun()


# ─────────────────────────────────────────────
#  5. TOP BAR & IMPORT
# ─────────────────────────────────────────────
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

        # Détection automatique du type de données
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

                    # Nettoyage données aériennes (espaces dans nombres, mois numériques)
                    if data_type == 'aerien':
                        df_clean['NOMBRE_TEU'] = clean_numeric_col(df_clean['NOMBRE_TEU'])
                        df_clean['Année escale'] = clean_numeric_col(df_clean['Année escale']).astype(int)
                        try:
                            mois_vals = df_clean['Mois escale'].astype(str).str.replace(' ', '', regex=False).str.strip()
                            mois_numeric = pd.to_numeric(mois_vals, errors='coerce')
                            if mois_numeric.notna().all():
                                df_clean['Mois escale'] = mois_numeric.astype(int).map(MOIS_NUM_TO_NAME)
                        except:
                            pass

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
def generate_pptx_report(df_source, comparison, res_2026, df_cible, df_all, client_col, label_periode, is_single_month, metric_unit):
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    AGL_NAVY = RGBColor(0, 31, 77)
    AGL_GOLD = RGBColor(229, 168, 35)
    WHITE = RGBColor(255, 255, 255)
    LIGHT_GRAY = RGBColor(240, 243, 248)
    unit_upper = metric_unit.upper()

    def add_title_slide(title, subtitle):
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = AGL_NAVY
        # Title
        txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11), Inches(1.5))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
        # Subtitle
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(18)
        p2.font.color.rgb = AGL_GOLD
        p2.alignment = PP_ALIGN.CENTER
        # Gold line
        slide.shapes.add_shape(1, Inches(4), Inches(4), Inches(5), Pt(3)).fill.solid()
        slide.shapes[-1].fill.fore_color.rgb = AGL_GOLD
        slide.shapes[-1].line.fill.background()
        return slide

    def add_table_slide(title, df, max_rows=20):
        if df is None or df.empty:
            return
        df_show = df.head(max_rows).copy()
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        # Title bar
        title_shape = slide.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.7))
        title_shape.fill.solid()
        title_shape.fill.fore_color.rgb = AGL_NAVY
        title_shape.line.fill.background()
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.08), Inches(12), Inches(0.55))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = AGL_GOLD

        rows, cols = len(df_show) + 1, len(df_show.columns)
        tbl_width = min(Inches(12.5), Inches(cols * 1.6))
        tbl = slide.shapes.add_table(rows, cols, Inches(0.4), Inches(0.9), tbl_width, Inches(min(5.8, 0.35 * rows))).table

        # Header
        for j, col_name in enumerate(df_show.columns):
            cell = tbl.cell(0, j)
            cell.text = str(col_name)
            cell.fill.solid()
            cell.fill.fore_color.rgb = AGL_NAVY
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(9)
                paragraph.font.bold = True
                paragraph.font.color.rgb = WHITE
                paragraph.alignment = PP_ALIGN.CENTER
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

        # Data
        for i in range(len(df_show)):
            for j in range(cols):
                cell = tbl.cell(i + 1, j)
                val = df_show.iloc[i, j]
                cell.text = str(int(val)) if isinstance(val, (int, float)) and not pd.isna(val) else str(val)
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else LIGHT_GRAY
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(8)
                    paragraph.font.color.rgb = AGL_NAVY
                    paragraph.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        return slide

    def add_chart_image_slide(title, fig):
        try:
            img_bytes = fig.to_image(format="png", width=1200, height=500, scale=2)
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            # Title bar
            title_shape = slide.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.7))
            title_shape.fill.solid()
            title_shape.fill.fore_color.rgb = AGL_NAVY
            title_shape.line.fill.background()
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.08), Inches(12), Inches(0.55))
            tf = txBox.text_frame
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = AGL_GOLD
            # Image
            img_stream = io.BytesIO(img_bytes)
            slide.shapes.add_picture(img_stream, Inches(0.6), Inches(1), Inches(12), Inches(5.8))
            return slide
        except:
            return None

    # ── SLIDE 1: TITRE ──
    data_type_label = "Aérien" if st.session_state.get('data_type') == 'aerien' else "Maritime"
    add_title_slide(
        "AGL | Rapport Stratégique",
        f"{data_type_label} — {label_periode} 2026 — Part de Marché & Concurrence"
    )

    # ── SLIDE 2: KPIs RÉSUMÉ ──
    slide_kpi = prs.slides.add_slide(prs.slide_layouts[6])
    title_shape = slide_kpi.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(0.7))
    title_shape.fill.solid()
    title_shape.fill.fore_color.rgb = AGL_NAVY
    title_shape.line.fill.background()
    txBox = slide_kpi.shapes.add_textbox(Inches(0.5), Inches(0.08), Inches(12), Inches(0.55))
    p = txBox.text_frame.paragraphs[0]
    p.text = "INDICATEURS CLÉS"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = AGL_GOLD

    total_marche = comparison['Total_Marche_2026'].sum()
    total_agl = comparison['AGL_Volume_2026'].sum()
    pdm_global = (total_agl / total_marche * 100) if total_marche > 0 else 0
    nb_clients_agl = len(comparison[comparison['AGL_Volume_2026'] > 0])

    kpis = [
        (f"Marché Total", f"{int(total_marche):,} {metric_unit}"),
        (f"Volume AGL", f"{int(total_agl):,} {metric_unit}"),
        (f"PDM Globale", f"{pdm_global:.1f} %"),
        (f"Clients AGL", f"{nb_clients_agl}"),
    ]
    for idx, (kpi_title, kpi_val) in enumerate(kpis):
        left = Inches(0.5 + idx * 3.1)
        shape = slide_kpi.shapes.add_shape(1, left, Inches(1.5), Inches(2.8), Inches(2))
        shape.fill.solid()
        shape.fill.fore_color.rgb = WHITE
        shape.line.color.rgb = RGBColor(226, 232, 240)
        tf = shape.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = kpi_title
        p1.font.size = Pt(12)
        p1.font.color.rgb = AGL_NAVY
        p1.alignment = PP_ALIGN.CENTER
        p2 = tf.add_paragraph()
        p2.text = kpi_val
        p2.font.size = Pt(28)
        p2.font.bold = True
        p2.font.color.rgb = AGL_GOLD
        p2.alignment = PP_ALIGN.CENTER

    # ── SLIDE 3: FOCUS AGL (tableau) ──
    comp_agl = comparison[(comparison['AGL_Volume_2026'] > 0) | (comparison['AGL_Volume_2025'] > 0)].copy()
    if not comp_agl.empty:
        if not is_single_month:
            comp_agl['Variation_Volume'] = comp_agl['AGL_Volume_2026'] - comp_agl['AGL_Volume_2025']
        tbl_agl = format_view_table(comp_agl, label_periode, client_col)
        add_table_slide(f"FOCUS AGL — {label_periode.upper()} 2026", tbl_agl)

    # ── SLIDE 4: TOP PDM CHART ──
    if not comp_agl.empty:
        top20 = comp_agl.nlargest(15, 'AGL_Volume_2026')
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=top20[client_col], y=top20['AGL_Volume_2026'],
            marker_color='#E5A823', name=f'AGL {unit_upper} 2026'
        ))
        if not is_single_month:
            fig_bar.add_trace(go.Bar(
                x=top20[client_col], y=top20['AGL_Volume_2025'],
                marker_color='#001f4d', name=f'AGL {unit_upper} 2025', opacity=0.6
            ))
        fig_bar.update_layout(
            title=f"TOP 15 CLIENTS AGL — {label_periode.upper()}",
            font=dict(family="DM Sans", color="#1a2840"),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(tickangle=-45), barmode='group',
            margin=dict(t=50, b=120, l=60, r=30)
        )
        add_chart_image_slide(f"TOP 15 CLIENTS AGL — {label_periode.upper()}", fig_bar)

    # ── SLIDE 5: CONCURRENCE ──
    df_cible_2026 = df_cible[df_cible['Année escale'] == 2026]
    if not df_cible_2026.empty:
        df_comp = df_cible_2026.groupby([client_col, 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
        df_others = df_comp[~df_comp['Transitaire'].astype(str).str.contains('AFRICA GLOBAL LOGISTICS', case=False, na=False)]
        idx_max = df_others.groupby(client_col)['NOMBRE_TEU'].idxmax()
        top_comp = df_others.loc[idx_max.dropna()].rename(columns={'Transitaire': '1ER CONCURRENT', 'NOMBRE_TEU': f'{unit_upper} CONCURRENT'})
        comp_tbl = pd.merge(res_2026, top_comp[[client_col, '1ER CONCURRENT', f'{unit_upper} CONCURRENT']], on=client_col, how='left')
        comp_tbl['VOL. CONCURRENCE'] = comp_tbl['Total_Marche_2026'] - comp_tbl['AGL_Volume_2026']
        comp_tbl = comp_tbl.fillna(0)
        disp_conc = comp_tbl[[client_col, 'Total_Marche_2026', 'AGL_Volume_2026', 'PDM_2026', 'VOL. CONCURRENCE', '1ER CONCURRENT', f'{unit_upper} CONCURRENT']].copy()
        disp_conc.columns = ['CLIENTS', f'MARCHÉ 2026', f'AGL {unit_upper}', 'PDM %', 'CONCURRENCE', '1ER CONCURRENT', f'{unit_upper} CONC.']
        disp_conc = disp_conc.sort_values(f'MARCHÉ 2026', ascending=False).head(20)
        for c in disp_conc.columns:
            if c not in ['CLIENTS', '1ER CONCURRENT']:
                disp_conc[c] = disp_conc[c].fillna(0).astype(int)
        disp_conc['1ER CONCURRENT'] = disp_conc['1ER CONCURRENT'].astype(str).replace('0', 'Aucun').replace('0.0', 'Aucun')
        add_table_slide(f"ANALYSE CONCURRENTIELLE — {label_periode.upper()} 2026", disp_conc)

    # ── SLIDE 6: PDM PIE CHART ──
    if not df_cible_2026.empty:
        df_trans = df_cible_2026.groupby('Transitaire')['NOMBRE_TEU'].sum().reset_index()
        df_trans = df_trans.sort_values('NOMBRE_TEU', ascending=False).head(10)
        colors = ['#E5A823' if 'AFRICA GLOBAL' in str(t).upper() else '#001f4d' for t in df_trans['Transitaire']]
        fig_pie = go.Figure(go.Pie(
            labels=df_trans['Transitaire'], values=df_trans['NOMBRE_TEU'],
            marker=dict(colors=colors), textinfo='label+percent', hole=0.4
        ))
        fig_pie.update_layout(
            title="RÉPARTITION PDM — TOP 10 TRANSITAIRES",
            font=dict(family="DM Sans", color="#1a2840"),
            paper_bgcolor="white", margin=dict(t=50, b=30, l=30, r=30),
            showlegend=False
        )
        add_chart_image_slide("RÉPARTITION PDM — TOP 10 TRANSITAIRES", fig_pie)

    # ── EXPORT ──
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output.getvalue()


# ─────────────────────────────────────────────
#  6. DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────
if st.session_state.validated:
    df_source  = st.session_state.df_propre
    client_col = st.session_state.client_col
    is_single_month = st.session_state.is_single_month

    mois_dict_ref = {'Janvier':1,'Février':2,'Mars':3,'Avril':4,'Mai':5,'Juin':6,'Juillet':7,'Août':8,'Septembre':9,'Octobre':10,'Novembre':11,'Décembre':12}
    mois_presents_tries = sorted(df_source['Mois escale'].dropna().unique(), key=lambda x: mois_dict_ref.get(x, 99))

    with st.expander("PARAMÈTRES ET FILTRES GLOBAUX", expanded=True):
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        with r1c1: analyse_type = st.radio("TYPE D'ANALYSE", ["Mois Spécifique", "Cumul (YTD)"])
        with r1c2: mois_cible = st.selectbox("PÉRIODE ANALYSÉE", mois_presents_tries)
        with r1c3:
            geo_label = "AÉROPORT D'ORIGINE" if st.session_state.get('data_type') == 'aerien' else "PAYS DE DESTINATION"
            if 'Pays de livraison' in df_source.columns:
                pays_livraison = st.multiselect(geo_label, df_source['Pays de livraison'].dropna().unique())
            else: pays_livraison = []
        with r1c4:
            cond_label = "MARCHANDISE" if st.session_state.get('data_type') == 'aerien' else "CONDITIONNEMENT"
            if 'Conditionnement' in df_source.columns:
                conditionnements = st.multiselect(cond_label, df_source['Conditionnement'].dropna().unique())
            else: conditionnements = []

    # Application des filtres globaux
    df_all = df_source.copy()
    if pays_livraison:   df_all = df_all[df_all['Pays de livraison'].isin(pays_livraison)]
    if conditionnements: df_all = df_all[df_all['Conditionnement'].isin(conditionnements)]

    mois_num = mois_dict_ref.get(mois_cible, 0)
    if analyse_type == "Cumul (YTD)":
        valid_months = [m for m in mois_presents_tries if mois_dict_ref.get(m, 0) <= mois_num]
        df_cible = df_all[df_all['Mois escale'].isin(valid_months)]
        label_periode = f"YTD {mois_cible}"
    else:
        df_cible = df_all[df_all['Mois escale'] == mois_cible]
        label_periode = mois_cible

    res_2026 = get_stats_annee(df_cible[df_cible['Année escale'] == 2026], 2026, client_col)
    if not is_single_month:
        res_2025 = get_stats_annee(df_cible[df_cible['Année escale'] == 2025], 2025, client_col)
        comparison = pd.merge(res_2025, res_2026, on=client_col, how='outer').fillna(0)
    else:
        comparison = res_2026.copy()
        comparison['AGL_Volume_2025'] = 0
        comparison['Total_Marche_2025'] = 0
        comparison['PDM_2025'] = 0

    st.markdown("<br>", unsafe_allow_html=True)

    # Bouton export PPTX
    col_export, col_spacer = st.columns([1, 5])
    with col_export:
        if st.button("EXPORTER RAPPORT PPTX", type="secondary"):
            with st.spinner("Génération du rapport PowerPoint..."):
                try:
                    pptx_data = generate_pptx_report(
                        df_source, comparison, res_2026, df_cible, df_all,
                        client_col, label_periode, is_single_month,
                        st.session_state.get('metric_unit', 'Teus')
                    )
                    st.session_state['pptx_data'] = pptx_data
                except Exception as e:
                    import sys
                    st.error(f"Erreur génération PPTX : {e}")
                    st.code(f"sys.executable = {sys.executable}\nsys.path = {sys.path}", language="text")
    if st.session_state.get('pptx_data'):
        col_dl, _ = st.columns([1, 5])
        with col_dl:
            data_type_label = "Aerien" if st.session_state.get('data_type') == 'aerien' else "Maritime"
            st.download_button(
                label="TÉLÉCHARGER LE RAPPORT",
                data=st.session_state['pptx_data'],
                file_name=f"AGL_Rapport_{data_type_label}_{label_periode.replace(' ', '_')}_2026.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary"
            )

    tab_agl, tab_evo, tab_conc, tab_raw = st.tabs([
        "FOCUS AGL", "ÉVOLUTION PDM", "CONCURRENCE", "DONNÉES BRUTES"
    ])

    # ─────────────────────────────────────────────
    #  FONCTION DE RENDU DES VUES AVEC ÉDITEUR (DATA_EDITOR)
    # ─────────────────────────────────────────────
    def render_dashboard(comp_df, prefix_key, is_single, label_per):
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            seuil_pdm = st.slider("SEUIL DE PDM (%) POUR LE RÉSUMÉ :", min_value=10, max_value=100, value=95, step=1, key=f"slider_{prefix_key}")
        
        mode_nouveaux = "Stricts (absents du marché l'année précédente)"
        if not is_single:
            with col_ctrl2:
                mode_nouveaux = st.radio("DÉFINITION DES NOUVEAUX CLIENTS :", ["Stricts (absents du marché l'année précédente)", "Larges (aucun volume AGL l'année précédente)"], key=f"mode_{prefix_key}")
        
        st.markdown("<hr style='margin: 10px 0 20px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

        if not is_single:
            comp_df['Variation_Volume'] = comp_df['AGL_Volume_2026'] - comp_df['AGL_Volume_2025']
            
            if "Stricts" in mode_nouveaux:
                m_actifs_new = (comp_df['AGL_Volume_2026'] > 0) & (comp_df['Total_Marche_2025'] == 0)
                m_inactifs   = (comp_df['AGL_Volume_2025'] > 0) & (comp_df['Total_Marche_2026'] == 0)
            else:
                m_actifs_new = (comp_df['AGL_Volume_2026'] > 0) & (comp_df['AGL_Volume_2025'] == 0)
                m_inactifs   = (comp_df['AGL_Volume_2025'] > 0) & (comp_df['AGL_Volume_2026'] == 0)
                
            m_present = ~(m_actifs_new | m_inactifs) & ((comp_df['AGL_Volume_2026'] > 0) | (comp_df['AGL_Volume_2025'] > 0))

            m_seuil = (comp_df['PDM_2026'] >= seuil_pdm) & (comp_df['PDM_2025'] >= seuil_pdm)
            m_crois = comp_df['Variation_Volume'] >= 0
            m_baisse = comp_df['Variation_Volume'] < 0

            df_100_crois  = comp_df[m_present & m_crois & m_seuil].sort_values('Variation_Volume', ascending=False)
            df_100_baisse = comp_df[m_present & m_baisse & m_seuil].sort_values('Variation_Volume')
            
            df_aut_crois  = comp_df[m_present & m_crois & ~m_seuil].sort_values('Variation_Volume', ascending=False)
            df_aut_baisse = comp_df[m_present & m_baisse & ~m_seuil].sort_values('Variation_Volume')

            df_new  = comp_df[m_actifs_new].sort_values('Variation_Volume', ascending=False)
            df_lost = comp_df[m_inactifs].sort_values('Variation_Volume')

            vol_100 = df_100_crois['Variation_Volume'].sum() + df_100_baisse['Variation_Volume'].sum()
            vol_act_inact = df_new['Variation_Volume'].sum() + df_lost['Variation_Volume'].sum()
            vol_aut = df_aut_crois['Variation_Volume'].sum() + df_aut_baisse['Variation_Volume'].sum()

            html_str = f"""
            <div class="agl-summary-block">
                <div class="agl-summary-group">
                    <div class="agl-summary-title"><div class="agl-summary-triangle"></div><span>{len(df_100_crois) + len(df_100_baisse)} Clients à ≥ {seuil_pdm}% de PDM {format_delta_html(vol_100)}</span></div>
                    <ul class="agl-summary-list">
                        <li><b>{len(df_100_crois):02d}</b> Croissance ou Stabilité {format_delta_html(df_100_crois['Variation_Volume'].sum())}</li>
                        <li><b>{len(df_100_baisse):02d}</b> Baisse {format_delta_html(df_100_baisse['Variation_Volume'].sum())}</li>
                    </ul>
                </div>
                <div class="agl-summary-group">
                    <div class="agl-summary-title"><div class="agl-summary-triangle"></div><span>Clients Actifs et Inactifs {format_delta_html(vol_act_inact)}</span></div>
                    <ul class="agl-summary-list">
                        <li><b>{len(df_new):02d}</b> Nouveaux Clients 2026 {format_delta_html(df_new['Variation_Volume'].sum())}</li>
                        <li><b>{len(df_lost):02d}</b> Clients Inactifs en 2026 {format_delta_html(df_lost['Variation_Volume'].sum())}</li>
                    </ul>
                </div>
                <div class="agl-summary-group" style="margin-bottom:0;">
                    <div class="agl-summary-title"><div class="agl-summary-triangle"></div><span>Autres Clients {format_delta_html(vol_aut)}</span></div>
                    <ul class="agl-summary-list">
                        <li><b>{len(df_aut_crois):02d}</b> Hausse ou Stabilité {format_delta_html(df_aut_crois['Variation_Volume'].sum())}</li>
                        <li><b>{len(df_aut_baisse):02d}</b> Baisse {format_delta_html(df_aut_baisse['Variation_Volume'].sum())}</li>
                    </ul>
                </div>
            </div>
            """
            st.markdown(html_str.replace('\n', ''), unsafe_allow_html=True)

            col_g, col_d = st.columns(2, gap="large")
            with col_g:
                st.markdown(f'<div class="agl-section-title">{ICON_UP} PDM ≥ {seuil_pdm}% · CROISSANCE & STABLES</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_100_crois, label_per, client_col), f"{prefix_key}_100c", use_global_names=True, label_periode=label_per)
                
                st.markdown(f'<div class="agl-section-title" style="margin-top:16px">{ICON_UP} NOUVEAUX CLIENTS ACTIFS</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_new, label_per, client_col), f"{prefix_key}_new", use_global_names=True, label_periode=label_per)
                
                st.markdown(f'<div class="agl-section-title" style="margin-top:16px">{ICON_UP} AUTRES CLIENTS EN HAUSSE & STABLES</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_aut_crois, label_per, client_col), f"{prefix_key}_autc", use_global_names=True, label_periode=label_per)

            with col_d:
                st.markdown(f'<div class="agl-section-title agl-section-title-warn">{ICON_DOWN} PDM ≥ {seuil_pdm}% · DÉCROISSANCE</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_100_baisse, label_per, client_col), f"{prefix_key}_100b", use_global_names=True, label_periode=label_per)
                
                st.markdown(f'<div class="agl-section-title agl-section-title-warn" style="margin-top:16px">{ICON_DOWN} CLIENTS PERDUS (INACTIFS)</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_lost, label_per, client_col), f"{prefix_key}_lost", use_global_names=True, label_periode=label_per)
                
                st.markdown(f'<div class="agl-section-title agl-section-title-warn" style="margin-top:16px">{ICON_DOWN} AUTRES CLIENTS EN BAISSE</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_aut_baisse, label_per, client_col), f"{prefix_key}_autb", use_global_names=True, label_periode=label_per)

        else: 
            df_100 = comp_df[comp_df['PDM_2026'] >= seuil_pdm].sort_values('AGL_Volume_2026', ascending=False)
            df_aut = comp_df[comp_df['PDM_2026'] < seuil_pdm].sort_values('AGL_Volume_2026', ascending=False)
            
            col_g, col_d = st.columns(2, gap="large")
            with col_g:
                st.markdown(f'<div class="agl-section-title">{ICON_UP} CLIENTS PDM ≥ {seuil_pdm}%</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_100, label_per, client_col), f"{prefix_key}_100", use_global_names=True, label_periode=label_per)
            with col_d:
                st.markdown(f'<div class="agl-section-title agl-section-title-warn">{ICON_DOWN} AUTRES CLIENTS (< {seuil_pdm}%)</div>', unsafe_allow_html=True)
                editable_dataframe(format_view_table(df_aut, label_per, client_col), f"{prefix_key}_aut", use_global_names=True, label_periode=label_per)

    # ─────────────────────────────────────────────
    #  EXÉCUTION DES ONGLETS
    # ─────────────────────────────────────────────
    with tab_agl:
        # Interface de renommage des colonnes (s'applique à tous les tableaux)
        unit_upper = st.session_state.get('metric_unit', 'Teus').upper()
        cols_for_rename = ['CLIENTS', f'MARCHÉ {label_periode.upper()} 2026', f'AGL {unit_upper} 2026', 'PDM 2026']
        if not is_single_month:
            cols_for_rename += [f'MARCHÉ {label_periode.upper()} 2025', f'AGL {unit_upper} 2025', 'PDM 2025', 'VARIATION']
        render_column_rename_interface(cols_for_rename)
        
        comp_agl = comparison[(comparison['AGL_Volume_2026'] > 0) | (comparison['AGL_Volume_2025'] > 0)].copy()
        render_dashboard(comp_agl, "agl", is_single_month, label_periode)
        
    with tab_evo:
        trend_data = get_monthly_trend(df_all, client_col)
        if not trend_data.empty:
            clients_list = trend_data[client_col].dropna().unique().tolist()
            if clients_list:
                selected_client = st.selectbox(f"SÉLECTIONNER UN {client_col.upper()} :", clients_list, key="evo_dest")
                df_filtered = trend_data[trend_data[client_col] == selected_client].copy()
                df_filtered = df_filtered.reset_index(drop=True)
                
                if not df_filtered.empty:
                    transitaires = df_filtered['Transitaire'].unique()

                    # Palette de couleurs dynamiques pour les concurrents
                    CONCURRENT_COLORS = [
                        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
                        "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
                    ]
                    color_idx = 0
                    color_map = {}
                    for t in transitaires:
                        if 'AFRICA GLOBAL' in str(t).upper():
                            color_map[t] = "#E5A823"
                        else:
                            color_map[t] = CONCURRENT_COLORS[color_idx % len(CONCURRENT_COLORS)]
                            color_idx += 1

                    # Utiliser go.Figure au lieu de px.line pour éviter les problèmes de compatibilité
                    fig = go.Figure()
                    for transitaire in transitaires:
                        df_trans = df_filtered[df_filtered['Transitaire'] == transitaire]
                        line_color = color_map.get(transitaire, "#c8d6e8")
                        line_width = 4 if 'AFRICA GLOBAL' in str(transitaire).upper() else 2
                        marker_size = 9 if 'AFRICA GLOBAL' in str(transitaire).upper() else 6
                        fig.add_trace(go.Scatter(
                            x=df_trans['Date_Label'].tolist(),
                            y=df_trans['PDM'].tolist(),
                            mode='lines+markers',
                            name=str(transitaire),
                            line=dict(color=line_color, width=line_width),
                            marker=dict(size=marker_size)
                        ))
                    
                    fig.update_layout(
                        title=f"ÉVOLUTION DE LA PDM — {selected_client}",
                        font=dict(family="DM Sans, sans-serif", color="#1a2840"), 
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=50, b=30, l=20, r=20), 
                        title_font=dict(family="Playfair Display, serif", size=15, color="#001f4d"),
                        xaxis=dict(gridcolor="#e8eef6", linecolor="#d0d9ea", title=""), 
                        yaxis=dict(gridcolor="#e8eef6", linecolor="#d0d9ea", title="PDM (%)"),
                        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1, orientation="v")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Données insuffisantes pour ce client.")
            else:
                st.info("Aucun client disponible pour l'analyse.")
        else:
            st.info("Données insuffisantes pour tracer l'évolution temporelle.")

    with tab_conc:
        df_cible_2026 = df_cible[df_cible['Année escale'] == 2026]
        if not df_cible_2026.empty:
            df_comp = df_cible_2026.groupby([client_col, 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
            df_others = df_comp[~df_comp['Transitaire'].astype(str).str.contains('AFRICA GLOBAL LOGISTICS', case=False, na=False)]
            idx = df_others.groupby(client_col)['NOMBRE_TEU'].idxmax()
            top_comp = df_others.loc[idx.dropna()].rename(columns={'Transitaire': '1ER CONCURRENT EN 2026', 'NOMBRE_TEU': 'TEUS 1ER CONCURRENT'})

            comp = pd.merge(res_2026, top_comp[[client_col, '1ER CONCURRENT EN 2026', 'TEUS 1ER CONCURRENT']], on=client_col, how='left')
            comp['VOL. CONCURRENCE'] = comp['Total_Marche_2026'] - comp['AGL_Volume_2026']
            comp['PDM CONCURRENT']    = (comp['TEUS 1ER CONCURRENT'] / comp['Total_Marche_2026']) * 100
            comp = comp.fillna(0)

            disp = comp[[client_col, 'Total_Marche_2026', 'AGL_Volume_2026', 'PDM_2026', 'VOL. CONCURRENCE', '1ER CONCURRENT EN 2026', 'TEUS 1ER CONCURRENT', 'PDM CONCURRENT']].copy()
            unit_upper_conc = st.session_state.get('metric_unit', 'Teus').upper()
            disp.columns = ['CLIENTS', f'MARCHÉ {label_periode.upper()} 2026', f'AGL {unit_upper_conc} 2026', 'PDM AGL', 'VOL. CONCURRENCE', '1ER CONCURRENT 2026', f'{unit_upper_conc} CONCURRENT', 'PDM CONCURRENT']
            
            # Convertir en string AVANT le remplacement pour éviter les types mixtes
            disp['1ER CONCURRENT 2026'] = disp['1ER CONCURRENT 2026'].astype(str).replace('0', 'Aucun').replace('0.0', 'Aucun')
            
            for col in disp.columns:
                if any(k in col for k in [unit_upper_conc, 'VOL', 'MARCHÉ', 'PDM']):
                    disp[col] = disp[col].fillna(0).astype(int)

            editable_dataframe(disp.sort_values(by=f'MARCHÉ {label_periode.upper()} 2026', ascending=False), "concurrence", has_total_row=False)
        else:
            st.info("Aucune donnée d'analyse concurrentielle pour cette période.")

    with tab_raw:
        editable_dataframe(df_all, "raw_data", has_total_row=False)