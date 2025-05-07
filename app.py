import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt # Ajout de l'import

# --- Configuration de la page ---
st.set_page_config(page_title="Analyse des retards de vols", layout="wide")
st.title("✈️ Analyse des retards de vols aux USA")

# --- Chargement des données avec cache ---
@st.cache_data
def load_data(nrows=200_000):
    cols = ["MONTH","DAY","AIRLINE","ORIGIN_AIRPORT","DEPARTURE_DELAY"]
    dtypes = {
        "MONTH": "Int64",
        "DAY": "Int64",
        "AIRLINE": "string",
        "ORIGIN_AIRPORT": "string",
        "DEPARTURE_DELAY": "float64"
    }
    df = pd.read_csv(
        "flights.csv",
        usecols=cols,
        dtype=dtypes,
        parse_dates=False,
        nrows=nrows,
        low_memory=False
    )
    return df[df["DEPARTURE_DELAY"].notna()]

with st.spinner("⏳ Chargement des données…"):
    df = load_data()
st.success(f"✅ {len(df):,} lignes chargées !")

# --- Aperçu rapide ---
st.subheader("📝 Aperçu des données (5 premières lignes)")
st.dataframe(df.head(20))

# --- Filtres en sidebar ---
st.sidebar.header("Filtres")
airline = st.sidebar.selectbox("Compagnie", sorted(df["AIRLINE"].unique()))

months = sorted(df["MONTH"].unique())
# Si plusieurs mois, on peut proposer un slider, sinon un selectbox
if len(months) > 1:
    month = st.sidebar.select_slider("Mois", options=months, value=months[0])
else:
    month = st.sidebar.selectbox("Mois", options=months)

filtered = df[(df["AIRLINE"] == airline) & (df["MONTH"] == month)]

# Sous-ensemble filtré
filtered = df[(df["AIRLINE"] == airline) & (df["MONTH"] == month)]

# --- Préparations des DataFrames pour chaque graphique ---

# 1) Retard moyen par mois (tous mois confondus)
monthly = (
    df
    .groupby("MONTH", as_index=False)
    .agg(retard_moyen=("DEPARTURE_DELAY", "mean"))
)

# 2) Tendance globale par jour (pour le filtre courant)
trend = (
    filtered
    .groupby("DAY", as_index=False)
    .agg(retard_moyen=("DEPARTURE_DELAY", "mean"))
)

# 3) Top 5 aéroports par nombre de vols (sur le filtre courant)
counts = filtered["ORIGIN_AIRPORT"].value_counts().nlargest(5)
top5_airports = counts.index.tolist()
df_top5 = filtered[filtered["ORIGIN_AIRPORT"].isin(top5_airports)]

# 4) Distribution des retards (boxplot) — on réutilise df_top5

# 5) Heatmap des retards moyens par jour × aéroport (top 5)
heat = (
    df_top5
    .groupby(["ORIGIN_AIRPORT","DAY"], as_index=False)
    .agg(retard_moyen=("DEPARTURE_DELAY","mean"))
)
heat_pivot = heat.pivot(index="ORIGIN_AIRPORT", columns="DAY", values="retard_moyen")

# 6) Scatter Matrix (sur le filtre courant)
# Sélection des colonnes numériques pertinentes pour la scatter matrix
scatter_matrix_df = filtered[["DAY", "DEPARTURE_DELAY"]]

# --- Construction des onglets ---
tabs = st.tabs([
    "Moyenne par mois",
    "Tendance générale",
    "Top 5 aéroports",
    "Distribution (boxplot)",
    "Heatmap",
    "Scatter Matrix" # Ajout du 6ème onglet
])

with tabs[0]:
    st.subheader("📊 Retard moyen par mois (tous mois confondus)")
    fig = px.bar(
        monthly,
        x="MONTH", y="retard_moyen",
        labels={"MONTH":"Mois", "retard_moyen":"Retard moyen (min)"},
        title="Retard moyen par mois"
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader(f"📈 Tendance générale par jour — {airline}, mois {month}")
    fig = px.line(
        trend,
        x="DAY", y="retard_moyen",
        labels={"DAY":"Jour", "retard_moyen":"Retard moyen (min)"},
        title="Retard moyen global par jour"
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader(f"📊 Top 5 aéroports par nombre de vols — {airline}, mois {month}")
    fig = px.bar(
        x=counts.index,
        y=counts.values,
        labels={"x":"Aéroport", "y":"Nombre de vols"},
        title="Top 5 aéroports (nombre de vols)"
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader(f"📊 Distribution des retards (boxplot) — {airline}, mois {month}")
    fig = px.box(
        df_top5,
        x="ORIGIN_AIRPORT", y="DEPARTURE_DELAY",
        labels={"ORIGIN_AIRPORT":"Aéroport", "DEPARTURE_DELAY":"Retard (min)"},
        title="Variabilité des retards (Top 5 aéroports)"
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.subheader(f"🌡️ Heatmap du retard moyen — {airline}, mois {month}")
    fig = px.imshow(
        heat_pivot,
        labels=dict(x="Jour", y="Aéroport", color="Retard moyen (min)"),
        title="Heatmap retard moyen par jour et par aéroport",
        aspect="auto"
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]: # Nouveau 6ème onglet
    st.subheader(f"🔗 Scatter Matrix des retards — {airline}, mois {month}")
    if not scatter_matrix_df.empty and len(scatter_matrix_df.columns) > 1:
        fig, ax = plt.subplots()
        pd.plotting.scatter_matrix(scatter_matrix_df, ax=ax, alpha=0.5, figsize=(10, 10), diagonal='kde')
        st.pyplot(fig)
    elif scatter_matrix_df.empty:
        st.warning("Pas de données à afficher pour la sélection actuelle.")
    else:
        st.warning("Pas assez de colonnes de données pour générer une scatter matrix (besoin d'au moins 2).")
