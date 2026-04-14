import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AGL Market Share Dashboard", page_icon="📊", layout="wide")

# --- FONCTIONS DE CHARGEMENT ET TRAITEMENT (Mise en cache) ---
@st.cache_data
def load_data(uploaded_file):
    """Charge les données Excel en cache."""
    return pd.read_excel(uploaded_file, sheet_name='Export')

@st.cache_data
def get_stats_annee(df_annee, annee):
    """Calcule les statistiques de base pour une année donnée."""
    if df_annee.empty:
        return pd.DataFrame(columns=['Destinataire', f'Total_Marche_{annee}', f'AGL_Volume_{annee}', f'PDM_{annee}'])
    
    stats = df_annee.groupby('Destinataire').agg(
        Total_Marche=('NOMBRE_TEU', 'sum'),
        AGL_Volume=('NOMBRE_TEU', lambda x: x[df_annee.loc[x.index, 'Transitaire'] == 'AFRICA GLOBAL LOGISTICS'].sum())
    ).reset_index()
    
    stats[f'PDM_{annee}'] = (stats['AGL_Volume'] / stats['Total_Marche']) * 100
    stats = stats.rename(columns={'Total_Marche': f'Total_Marche_{annee}', 'AGL_Volume': f'AGL_Volume_{annee}'})
    return stats

@st.cache_data
def get_monthly_trend(df):
    """Prépare les données pour l'évolution mensuelle de la PDM."""
    trend = df.groupby(['Année escale', 'Mois escale', 'Destinataire', 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
    total_market = trend.groupby(['Année escale', 'Mois escale', 'Destinataire'])['NOMBRE_TEU'].sum().reset_index()
    total_market = total_market.rename(columns={'NOMBRE_TEU': 'Total_Marche'})
    
    trend = pd.merge(trend, total_market, on=['Année escale', 'Mois escale', 'Destinataire'])
    trend['PDM'] = (trend['NOMBRE_TEU'] / trend['Total_Marche']) * 100
    
    mois_dict = {'Janvier': 1, 'Février': 2, 'Mars': 3, 'Avril': 4, 'Mai': 5, 'Juin': 6, 
                 'Juillet': 7, 'Août': 8, 'Septembre': 9, 'Octobre': 10, 'Novembre': 11, 'Décembre': 12}
    trend['Mois_Num'] = trend['Mois escale'].map(mois_dict)
    trend = trend.sort_values(by=['Année escale', 'Mois_Num'])
    trend['Date_Label'] = trend['Mois escale'] + " " + trend['Année escale'].astype(str)
    
    return trend

def format_view_table(df, mois_cible):
    """Formate les colonnes pour correspondre aux captures d'écran."""
    if df.empty:
        return pd.DataFrame()
    
    res = df[['Destinataire', 'Total_Marche_2026', 'AGL_Volume_2026', 'PDM_2026',
              'Total_Marche_2025', 'AGL_Volume_2025', 'PDM_2025', 'Variation_Volume']].copy()
    
    # Renommage
    res.columns = [
        'DESTINATAIRES', 
        f'VOLUME TEUS {mois_cible.upper()} 2026', 
        f'AGL TEUS {mois_cible.upper()} 2026', 
        'PDM 2026',
        f'VOLUME TEUS {mois_cible.upper()} 2025', 
        f'AGL TEUS {mois_cible.upper()} 2025', 
        'PDM 2025', 
        'VARIATION'
    ]
    
    # Formatage des pourcentages
    res['PDM 2026'] = res['PDM 2026'].fillna(0).apply(lambda x: f"{x:.0f}%")
    res['PDM 2025'] = res['PDM 2025'].fillna(0).apply(lambda x: f"{x:.0f}%")
    
    # Arrondi des volumes (pour enlever les .0 si entiers)
    for col in res.columns:
        if 'TEUS' in col or 'VARIATION' in col:
            res[col] = res[col].fillna(0).astype(int)
            
    return res

# --- FONCTIONS DE RENDU DES ONGLETS ---

def render_tab_vue_generale(comparison, mois_cible):
    st.subheader(f"📊 Segments de Marché : {mois_cible}")
    
    # --- LOGIQUE DE SEGMENTATION ---
    comparison = comparison.fillna(0)
    comparison['Variation_Volume'] = comparison['AGL_Volume_2026'] - comparison['AGL_Volume_2025']
    
    m_actifs_new = (comparison['Total_Marche_2026'] > 0) & (comparison['Total_Marche_2025'] == 0)
    m_inactifs = (comparison['Total_Marche_2026'] == 0) & (comparison['Total_Marche_2025'] > 0)
    
    m_100_crois = (comparison['PDM_2026'] >= 99.9) & (comparison['Variation_Volume'] > 0) & ~m_actifs_new
    m_100_decrois = (comparison['PDM_2026'] >= 99.9) & (comparison['Variation_Volume'] < 0) & ~m_inactifs
    
    m_hausses = (comparison['Variation_Volume'] > 0) & ~m_100_crois & ~m_actifs_new
    m_baisses = (comparison['Variation_Volume'] < 0) & ~m_100_decrois & ~m_inactifs

    # Création des sous-dataframes
    df_100_crois = comparison[m_100_crois].sort_values('Variation_Volume', ascending=False)
    df_100_decrois = comparison[m_100_decrois].sort_values('Variation_Volume', ascending=True)
    df_actifs_new = comparison[m_actifs_new].sort_values('Variation_Volume', ascending=False)
    df_inactifs = comparison[m_inactifs].sort_values('Variation_Volume', ascending=True)
    df_hausses = comparison[m_hausses].sort_values('Variation_Volume', ascending=False)
    df_baisses = comparison[m_baisses].sort_values('Variation_Volume', ascending=True)

    # --- TABLEAU RÉCAPITULATIF (SUMMARY) ---
    st.markdown("### 📋 RÉCAPITULATIF DES VOLUMES AGL")
    summary_data = [
        {"Catégorie": "Clients PDM 100% (volume en croissance)", "2026": df_100_crois['AGL_Volume_2026'].sum(), "2025": df_100_crois['AGL_Volume_2025'].sum()},
        {"Catégorie": "Clients PDM 100% (volume en décroissance)", "2026": df_100_decrois['AGL_Volume_2026'].sum(), "2025": df_100_decrois['AGL_Volume_2025'].sum()},
        {"Catégorie": "Clients Actifs en 2026 et non en 2025", "2026": df_actifs_new['AGL_Volume_2026'].sum(), "2025": df_actifs_new['AGL_Volume_2025'].sum()},
        {"Catégorie": "Clients Inactifs en 2026 et actifs en 2025", "2026": df_inactifs['AGL_Volume_2026'].sum(), "2025": df_inactifs['AGL_Volume_2025'].sum()},
        {"Catégorie": "Autres Clients en Hausses", "2026": df_hausses['AGL_Volume_2026'].sum(), "2025": df_hausses['AGL_Volume_2025'].sum()},
        {"Catégorie": "Autres Clients en Baisses", "2026": df_baisses['AGL_Volume_2026'].sum(), "2025": df_baisses['AGL_Volume_2025'].sum()},
    ]
    df_summary = pd.DataFrame(summary_data)
    df_summary[f'{mois_cible.upper()} 2026'] = df_summary['2026'].astype(int)
    df_summary[f'{mois_cible.upper()} 2025'] = df_summary['2025'].astype(int)
    df_summary['Variation'] = (df_summary['2026'] - df_summary['2025']).astype(int)
    
    total_2026 = comparison['AGL_Volume_2026'].sum()
    total_2025 = comparison['AGL_Volume_2025'].sum()
    df_summary.loc[len(df_summary)] = ["Total AGL", total_2026, total_2025, int(total_2026), int(total_2025), int(total_2026 - total_2025)]
    
    # Affichage Récap
    st.dataframe(df_summary[['Catégorie', f'{mois_cible.upper()} 2026', f'{mois_cible.upper()} 2025', 'Variation']], use_container_width=True, hide_index=True)
    st.markdown("---")

    # --- AFFICHAGE DES SEGMENTS DÉTAILLÉS ---
    col_g, col_d = st.columns(2)
    
    with col_g:
        st.markdown("#### 🟦 CLIENTS A 100% DE PDM AVEC VOLUME EN CROISSANCE")
        st.dataframe(format_view_table(df_100_crois, mois_cible), use_container_width=True, hide_index=True)
        
        st.markdown("#### 🟦 CLIENTS ACTIFS (Nouveaux)")
        st.dataframe(format_view_table(df_actifs_new, mois_cible), use_container_width=True, hide_index=True)
        
        st.markdown("#### 🟦 CLIENTS EN HAUSSES")
        st.dataframe(format_view_table(df_hausses, mois_cible), use_container_width=True, hide_index=True)

    with col_d:
        st.markdown("#### 🟧 CLIENTS A 100% DE PDM AVEC VOLUME EN DECROISSANCE")
        st.dataframe(format_view_table(df_100_decrois, mois_cible), use_container_width=True, hide_index=True)
        
        st.markdown("#### 🟧 CLIENTS NON ACTIFS (Perdus)")
        st.dataframe(format_view_table(df_inactifs, mois_cible), use_container_width=True, hide_index=True)
        
        st.markdown("#### 🟧 CLIENTS EN BAISSES")
        st.dataframe(format_view_table(df_baisses, mois_cible), use_container_width=True, hide_index=True)

def render_tab_evolution(df_all):
    st.subheader("📈 Évolution de la PDM au fil du temps")
    trend_data = get_monthly_trend(df_all)
    
    if trend_data.empty:
        st.warning("Pas de données disponibles pour l'évolution.")
        return

    destinataires_list = trend_data['Destinataire'].unique().tolist()
    selected_dest = st.selectbox("Choisir un Destinataire pour voir l'évolution", destinataires_list, key="evo_dest")
    
    df_filtered = trend_data[trend_data['Destinataire'] == selected_dest]
    
    transitaires = df_filtered['Transitaire'].unique()
    color_map = {t: "lightgrey" for t in transitaires}
    if 'AFRICA GLOBAL LOGISTICS' in color_map:
        color_map['AFRICA GLOBAL LOGISTICS'] = "#1f77b4" 
    
    fig = px.line(df_filtered, x='Date_Label', y='PDM', color='Transitaire', 
                  markers=True, color_discrete_map=color_map,
                  title=f"Évolution de la PDM pour {selected_dest}")
    
    fig.update_traces(line=dict(width=3))
    for trace in fig.data:
        if trace.name == 'AFRICA GLOBAL LOGISTICS':
            trace.line.width = 5
    
    st.plotly_chart(fig, use_container_width=True)

def render_tab_concurrence(df_mois_2026, res_2026, mois_cible):
    st.subheader(f"⚖️ Positionnement Concurrentiel Global ({mois_cible} 2026)")
    
    if df_mois_2026.empty:
        st.warning("Aucune donnée pour 2026 ce mois-ci.")
        return

    # 1. Calcul du total par destinataire/transitaire
    df_comp = df_mois_2026.groupby(['Destinataire', 'Transitaire'])['NOMBRE_TEU'].sum().reset_index()
    
    # 2. Identifier le 1er concurrent (Exclure AGL)
    df_others = df_comp[df_comp['Transitaire'] != 'AFRICA GLOBAL LOGISTICS']
    idx = df_others.groupby('Destinataire')['NOMBRE_TEU'].idxmax()
    top_comp = df_others.loc[idx.dropna()].rename(columns={
        'Transitaire': '1er Concurrent en 2026', 
        'NOMBRE_TEU': 'TEUS 1er Concurrent 2026'
    })

    # 3. Fusionner avec les données AGL globales
    comp_merge = pd.merge(res_2026, top_comp[['Destinataire', '1er Concurrent en 2026', 'TEUS 1er Concurrent 2026']], on='Destinataire', how='left')
    
    # 4. Calculs des parts
    comp_merge['VOLUME TRAITE PAR LA CONCURRENCE'] = comp_merge['Total_Marche_2026'] - comp_merge['AGL_Volume_2026']
    comp_merge['PDM 1er Concurrent 2026'] = (comp_merge['TEUS 1er Concurrent 2026'] / comp_merge['Total_Marche_2026']) * 100
    
    # Formatage final
    comp_merge = comp_merge.fillna(0)
    comp_display = comp_merge[[
        'Destinataire', 'Total_Marche_2026', 'AGL_Volume_2026', 'PDM_2026', 
        'VOLUME TRAITE PAR LA CONCURRENCE', '1er Concurrent en 2026', 
        'TEUS 1er Concurrent 2026', 'PDM 1er Concurrent 2026'
    ]].copy()
    
    comp_display.columns = ['CLIENTS', f'TEUS VOLUME {mois_cible.upper()} 2026', f'TEUS AGL {mois_cible.upper()} 2026', 
                            'PDM AGL 2026', 'VOLUME TRAITE PAR LA CONCURRENCE', 
                            '1er Concurrent en 2026', 'TEUS 1er Concurrent 2026', 'PDM 1er Concurrent 2026']
    
    comp_display['PDM AGL 2026'] = comp_display['PDM AGL 2026'].apply(lambda x: f"{x:.0f}%")
    comp_display['PDM 1er Concurrent 2026'] = comp_display['PDM 1er Concurrent 2026'].apply(lambda x: f"{x:.0f}%" if x > 0 else "")
    comp_display['1er Concurrent en 2026'] = comp_display['1er Concurrent en 2026'].replace(0, "Aucun")
    
    for col in comp_display.columns:
        if 'TEUS' in col or 'VOLUME' in col:
            comp_display[col] = comp_display[col].astype(int)

    # Affichage du tableau global
    st.dataframe(comp_display.sort_values(by=f'TEUS VOLUME {mois_cible.upper()} 2026', ascending=False), use_container_width=True, hide_index=True)


# --- STRUCTURE PRINCIPALE (UI) ---
st.title("📊 Tableau de Bord : Part de Marché AGL")

with st.sidebar:
    st.header("⚙️ Paramètres Principaux")
    uploaded_file = st.file_uploader("Choisir le fichier Excel", type=['xlsx'])
    mois_cible = st.selectbox("Sélectionner le mois", 
                              ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
                               'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'])
    
    st.markdown("---")
    with st.expander("ℹ️ Aide & Définitions"):
        st.markdown("**PDM (Part de Marché)** : Volume AGL divisé par Volume Total.")
        st.markdown("**Variation** : Différence de **VOLUME AGL** entre l'année 2026 et 2025 (Ex: Volume AGL 2026 - Volume AGL 2025).")
        st.markdown("**TEU** : Conteneur équivalent 20 pieds.")
        st.markdown("**Transitaire / Concurrent** : L'organisateur de transport.")


# --- LOGIQUE DE TRAITEMENT ---
if uploaded_file:
    df_all = load_data(uploaded_file)
    df_mois = df_all[df_all['Mois escale'] == mois_cible]

    # Calculs de base
    res_2025 = get_stats_annee(df_mois[df_mois['Année escale'] == 2025], 2025)
    res_2026 = get_stats_annee(df_mois[df_mois['Année escale'] == 2026], 2026)

    # Fusion globale
    comparison = pd.merge(res_2025, res_2026, on='Destinataire', how='outer').fillna(0)

    # --- CRÉATION DES ONGLETS ---
    tab1, tab2, tab3 = st.tabs([
        "📊 Vue Générale (Segments)", 
        "📈 Évolution PDM", 
        "⚖️ Comparaison Concurrents", 
    ])

    with tab1:
        render_tab_vue_generale(comparison, mois_cible)
    with tab2:
        render_tab_evolution(df_all)
    with tab3:
        # On passe uniquement les données brutes 2026 pour recalculer les concurrents
        render_tab_concurrence(df_mois[df_mois['Année escale'] == 2026], res_2026, mois_cible)

else:
    st.info("👋 Bienvenue ! Veuillez charger votre fichier Excel dans la barre latérale.")