from urllib.parse import quote
import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import folium_static

# Configuration de la page
st.set_page_config(
    page_title="Suivi de Recherche d'Appartements",
    page_icon="🏡",
    layout="wide",
)

# URL d'export CSV public de votre Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1kaozoe4IX09695Ibf-Cl99x3B0O_BSq954lCS_889xo/export?format=csv&gid=0"


@st.cache_data(ttl=60)
def load_data():
  try:
    df = pd.read_csv(SHEET_URL)
    return df
  except Exception as e:
    st.error(f"Erreur lors du chargement du Google Sheet : {e}")
    return pd.DataFrame()


df = load_data()


# Géocodage hybride ultra-robuste
@st.cache_data(ttl=3600)
def get_lat_lon(query_str):
  if not query_str or pd.isna(query_str):
    return 43.6767, 4.6278  # Centre par défaut (Arles)

  query_str = str(query_str).strip()
  query_lower = query_str.lower()

  # 1. Base locale sécurisée pour les villes et quartiers principaux (évite les bugs d'API)
  villes_fixes = {
      "saint-gilles": {"lat": 43.6811, "lon": 4.4328},
      "arles": {"lat": 43.6767, "lon": 4.6278},
      "bellegarde": {"lat": 43.7533, "lon": 4.5158},
      "garons": {"lat": 43.7844, "lon": 4.4372},
      "fourques": {"lat": 43.6822, "lon": 4.6033},
      "mas thibert": {"lat": 43.5858, "lon": 4.6897},
      "trinquetaille": {"lat": 43.6785, "lon": 4.6200},
      "barousse": {"lat": 43.6710, "lon": 4.6350},
      "griffeuille": {"lat": 43.6680, "lon": 4.6380},
  }

  for k, coords in villes_fixes.items():
    if k in query_lower and len(query_str) < 25:
      return coords["lat"], coords["lon"]

  # 2. Pour les adresses précises (ex: "19 Av. Anatole France, 30800 Saint-Gilles"), interrogation directe de l'API
  url = f"https://nominatim.openstreetmap.org/search?q={quote(query_str)}&format=json&limit=1"

  try:
    headers = {"User-Agent": "AppartementSearchApp/2.0"}
    response = requests.get(url, headers=headers, timeout=3)
    if response.status_code == 200:
      data = response.json()
      if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
  except Exception:
    pass

  return 43.6767, 4.6278


# Style CSS Mode Sombre épuré
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1f2937 100%, #111827 0%);
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        text-align: center;
        border: 1px solid #374151;
        margin-bottom: 20px;
    }
    .kpi-title {
        font-size: 14px;
        color: #9ca3af;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 36px;
        color: #f9fafb;
        font-weight: 800;
    }
    .rdv-card {
        background-color: #1f2937;
        padding: 22px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        margin-bottom: 15px;
        border-left: 6px solid #ef4444;
        border-top: 1px solid #374151;
        border-right: 1px solid #374151;
        border-bottom: 1px solid #374151;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🏡 Suivi de Recherche d'Appartements")
st.markdown(
    "Organisez, visitez et suivez vos coups de cœur à deux en toute simplicité."
)

if not df.empty:
  if "Loyer" in df.columns:
    df["Loyer_Num"] = (
        df["Loyer"]
        .astype(str)
        .str.replace("€", "", regex=True)
        .str.replace(" ", "", regex=True)
    )
    df["Loyer_Num"] = pd.to_numeric(df["Loyer_Num"], errors="coerce")

  # --- BARRE LATÉRALE DE FILTRES ---
  st.sidebar.header("🔍 Filtres & Recherche")

  recherche_texte = st.sidebar.text_input(
      "Recherche rapide", placeholder="Ex: Agence, Centre..."
  )

  if "Ville / Quartier" in df.columns:
    villes = ["Toutes"] + list(df["Ville / Quartier"].dropna().unique())
    ville_choisie = st.sidebar.selectbox("Filtrer par Ville / Quartier", villes)
    if ville_choisie != "Toutes":
      df = df[df["Ville / Quartier"] == ville_choisie]

  if "Pièces" in df.columns:
    pieces = ["Toutes"] + list(df["Pièces"].dropna().unique())
    piece_choisie = st.sidebar.selectbox("Filtrer par Pièces", pieces)
    if piece_choisie != "Toutes":
      df = df[df["Pièces"] == piece_choisie]

  if "Loyer_Num" in df.columns and not df["Loyer_Num"].dropna().empty:
    max_loyer_val = int(df["Loyer_Num"].max())
  else:
    max_loyer_val = 1000

  budget_max = st.sidebar.slider(
      "Budget Loyer Max (€)", 400, 1500, max_loyer_val, 25
  )
  if "Loyer_Num" in df.columns:
    df = df[df["Loyer_Num"].fillna(budget_max) <= budget_max]

  if recherche_texte:
    mask = df.astype(str).apply(
        lambda x: x.str.contains(recherche_texte, case=False, na=False)
    ).any(axis=1)
    df = df[mask]

  # --- KPIs ---
  col_kpi1, col_kpi2 = st.columns(2)
  nb_annonces = len(df)
  loyer_moyen_val = (
      int(df["Loyer_Num"].mean())
      if "Loyer_Num" in df.columns and not df["Loyer_Num"].dropna().empty
      else 0
  )

  with col_kpi1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">📋 Annonces affichées</div>
            <div class="kpi-value">{nb_annonces}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_kpi2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">💰 Loyer Moyen</div>
            <div class="kpi-value">{loyer_moyen_val} €</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- ONGLETS ---
  tab1, tab2, tab3 = st.tabs(
      [
          "📋 Tableau des Annonces",
          "📅 Planning des RDV",
          "🗺️ Carte Interactive",
      ]
  )

  with tab1:
    st.subheader("📋 Liste des appartements")
    st.dataframe(
        df.drop(columns=["Loyer_Num"], errors="ignore"),
        use_container_width=True,
    )

  with tab2:
    st.subheader("📅 Planning des RDV et Visites confirmées")
    rdv_col = "RDV pris ?" if "RDV pris ?" in df.columns else None

    df_rdv = pd.DataFrame()
    if rdv_col:
      df_rdv = df[
          df[rdv_col].notna()
          & (df[rdv_col].astype(str).str.strip() != "")
          & (df[rdv_col].astype(str).str.lower() != "nan")
      ]

    if not df_rdv.empty:
      for index, row in df_rdv.iterrows():
        lien = row.get("Lien Annonce", "#")
        btn_html = ""
        if pd.notna(lien) and str(lien).startswith("http"):
          btn_html = f"<a href='{lien}' target='_blank' style='background-color: #ef4444; color: white; padding: 8px 14px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; float: right;'>🔗 Voir l'annonce</a>"

        st.markdown(
            f"""
                <div class="rdv-card">
                    {btn_html}
                    <h3 style="margin-top:0; color: #f9fafb;">🏠 {row.get('Ville / Quartier', 'Appartement')}</h3>
                    <p style="margin: 6px 0; color: #9ca3af;"><b>💰 Loyer :</b> {row.get('Loyer', 'N/C')} | <b>📐 Surface :</b> {row.get('M²')} m² | <b>🚪 Pièces :</b> {row.get('Pièces')}</p>
                    <p style="margin: 6px 0; color: #9ca3af;"><b>🏢 Agence / Contact :</b> {row.get('Agence', 'N/C')}</p>
                    <hr style="margin: 12px 0; border: none; border-top: 1px solid #374151;">
                    <p style="margin: 6px 0; color: #4ade80; font-size: 16px;"><b>📅 RDV :</b> {row.get('RDV pris ?')}</p>
                    {"<p style='margin: 6px 0; color: #d1d5db;'><b>💬 Notes :</b> " + str(row.get('Réponse')) + "</p>" if pd.notna(row.get('Réponse')) and str(row.get('Réponse')).strip() != '' else ""}
                </div>
                """,
            unsafe_allow_html=True,
        )
    else:
      st.info("Aucun rendez-vous n'est actuellement renseigné.")

  with tab3:
    st.subheader("🗺️ Carte Interactive (Adresses précises & Villes)")

    m = folium.Map(location=[43.6767, 4.6278], zoom_level=12, control_scale=True)

    if "Ville / Quartier" in df.columns:
      for index, row in df.iterrows():
        lieu_text = str(row["Ville / Quartier"])

        lat, lon = get_lat_lon(lieu_text)

        loyer = str(row.get("Loyer", "N/C"))
        surface = str(row.get("M²", "N/C"))
        pieces = str(row.get("Pièces", "N/C"))
        agence = str(row.get("Agence", "N/C"))
        lien = str(row.get("Lien Annonce", "#"))
        if not lien.startswith("http"):
          lien = "#"

        popup_html = f"""
                <div style="font-family: sans-serif; width: 210px; color: #333;">
                    <b style="color: #111; font-size: 14px;">{lieu_text}</b><hr style="margin: 5px 0;">
                    <b>Loyer :</b> {loyer}<br>
                    <b>Surface :</b> {surface} m²<br>
                    <b>Pièces :</b> {pieces}<br>
                    <b>Agence :</b> {agence}<br><br>
                    <a href="{lien}" target="_blank" style="background-color: #ef4444; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; text-align: center;">🔗 Voir l'annonce</a>
                </div>
                """

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{loyer} - {lieu_text}",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(m)

    folium_static(m, width=1150, height=550)

else:
  st.warning("Impossible de charger les données.")