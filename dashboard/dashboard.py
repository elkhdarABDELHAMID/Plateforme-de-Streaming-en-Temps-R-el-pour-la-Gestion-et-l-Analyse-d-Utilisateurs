import streamlit as st
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Dashboard de Streaming en Temps Réel",
    page_icon="📊",
    layout="wide"
)

# Fonctions de connexion à la base de données
@st.cache_resource
def get_cassandra_connection():
    try:
        cluster = Cluster(['cassandra'], port=9042)
        session = cluster.connect()
        
        # Créer le keyspace et les tables si elles n'existent pas
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS random_user_keyspace 
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
        """)
        
        session.execute("""
            USE random_user_keyspace
        """)
        
        # Table pour les utilisateurs individuels
        session.execute("""
            CREATE TABLE IF NOT EXISTS random_user_table (
                user_id TEXT,
                gender TEXT,
                full_name TEXT,
                country TEXT,
                age INT,
                email TEXT,
                ingestion_time TIMESTAMP,
                PRIMARY KEY (user_id, ingestion_time)
            )
        """)
        
        # Table pour les statistiques par pays
        session.execute("""
            CREATE TABLE IF NOT EXISTS country_stats (
                country TEXT PRIMARY KEY,
                count_users INT,
                avg_age DOUBLE,
                last_update TIMESTAMP
            )
        """)
        
        return session
    except Exception as e:
        st.error(f"Erreur de connexion à Cassandra: {e}")
        return None

# Fonction pour récupérer les derniers utilisateurs
def get_latest_users(session, limit=10):
    try:
        rows = session.execute("SELECT * FROM random_user_keyspace.random_user_table LIMIT %s", [limit])
        return pd.DataFrame(list(rows))
    except Exception as e:
        st.error(f"Erreur lors de la récupération des derniers utilisateurs: {e}")
        return pd.DataFrame()

# Fonction pour récupérer les statistiques par pays
def get_country_stats(session):
    try:
        rows = session.execute("SELECT * FROM random_user_keyspace.country_stats")
        return pd.DataFrame(list(rows))
    except Exception as e:
        st.error(f"Erreur lors de la récupération des statistiques par pays: {e}")
        return pd.DataFrame()

# Fonction pour récupérer le nombre total d'utilisateurs
def get_user_count(session):
    try:
        row = session.execute("SELECT COUNT(*) as count FROM random_user_keyspace.random_user_table").one()
        if row:
            return row.count
        return 0
    except Exception as e:
        st.error(f"Erreur lors de la récupération du nombre d'utilisateurs: {e}")
        return 0

# Fonction pour récupérer la répartition par genre
def get_gender_distribution(session):
    try:
        rows = session.execute("SELECT gender, COUNT(*) as count FROM random_user_keyspace.random_user_table GROUP BY gender ALLOW FILTERING")
        return pd.DataFrame(list(rows))
    except Exception as e:
        st.error(f"Erreur lors de la récupération de la répartition par genre: {e}")
        return pd.DataFrame()

# Fonction principale
def main():
    # Titre
    st.title("📊 Dashboard de Streaming en Temps Réel")
    st.markdown("### Analyse des Données d'Utilisateurs Random")
    
    # Connexion à Cassandra
    session = get_cassandra_connection()
    
    if not session:
        st.error("Impossible de se connecter à Cassandra. Vérifiez que le service est en cours d'exécution.")
        return
    
    # Créer une barre latérale pour les contrôles
    with st.sidebar:
        st.header("Contrôles")
        refresh_rate = st.slider("Taux de rafraîchissement (secondes)", 5, 60, 10)
        user_limit = st.slider("Nombre d'utilisateurs à afficher", 5, 50, 10)
        
        # Information sur la dernière mise à jour
        st.write("---")
        last_update = st.empty()
    
    # Créer un layout en deux colonnes pour les métriques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_users_metric = st.empty()
    
    with col2:
        total_countries_metric = st.empty()
    
    with col3:
        avg_age_metric = st.empty()
    
    # Créer un layout pour les graphiques et tableaux
    st.write("---")
    tab1, tab2 = st.tabs(["📈 Statistiques", "👥 Utilisateurs"])
    
    # Boucle principale
    while True:
        try:
            # Mise à jour de l'heure
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            last_update.markdown(f"**Dernière mise à jour:** {current_time}")
            
            # Récupérer les données
            latest_users_df = get_latest_users(session, user_limit)
            country_stats_df = get_country_stats(session)
            total_users = get_user_count(session)
            gender_df = get_gender_distribution(session)
            
            # Mettre à jour les métriques
            total_users_metric.metric("Nombre total d'utilisateurs", total_users)
            
            if not country_stats_df.empty:
                total_countries_metric.metric("Nombre de pays", len(country_stats_df))
                avg_age = country_stats_df['avg_age'].mean()
                avg_age_metric.metric("Âge moyen", f"{avg_age:.1f} ans")
            
            # Onglet Statistiques
            with tab1:
                # Layout des graphiques
                stat_col1, stat_col2 = st.columns(2)
                
                with stat_col1:
                    # Graphique des utilisateurs par pays
                    if not country_stats_df.empty:
                        st.subheader("Utilisateurs par pays")
                        # Trier par nombre d'utilisateurs décroissant et prendre les 10 premiers
                        top_countries = country_stats_df.sort_values('count_users', ascending=False).head(10)
                        fig1 = px.bar(
                            top_countries,
                            x='country',
                            y='count_users',
                            color='count_users',
                            color_continuous_scale='Blues',
                            labels={'count_users': 'Nombre d\'utilisateurs', 'country': 'Pays'}
                        )
                        fig1.update_layout(xaxis_title="Pays", yaxis_title="Nombre d'utilisateurs")
                        st.plotly_chart(fig1, use_container_width=True)
                
                with stat_col2:
                    # Graphique de l'âge moyen par pays
                    if not country_stats_df.empty:
                        st.subheader("Âge moyen par pays")
                        # Trier par âge moyen et prendre les 10 premiers
                        top_age_countries = country_stats_df.sort_values('avg_age', ascending=False).head(10)
                        fig2 = px.bar(
                            top_age_countries,
                            x='country',
                            y='avg_age',
                            color='avg_age',
                            color_continuous_scale='Reds',
                            labels={'avg_age': 'Âge moyen', 'country': 'Pays'}
                        )
                        fig2.update_layout(xaxis_title="Pays", yaxis_title="Âge moyen")
                        st.plotly_chart(fig2, use_container_width=True)
                
                # Graphique de répartition par genre
                if not gender_df.empty:
                    st.subheader("Répartition par genre")
                    fig3 = px.pie(
                        gender_df,
                        values='count',
                        names='gender',
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig3, use_container_width=True)
            
            # Onglet Utilisateurs
            with tab2:
                st.subheader(f"Derniers {user_limit} utilisateurs")
                if not latest_users_df.empty:
                    # Réorganiser et formater le DataFrame pour l'affichage
                    display_df = latest_users_df[['user_id', 'full_name', 'gender', 'age', 'country', 'email', 'ingestion_time']]
                    display_df = display_df.rename(columns={
                        'user_id': 'ID',
                        'full_name': 'Nom Complet',
                        'gender': 'Genre',
                        'age': 'Âge',
                        'country': 'Pays',
                        'email': 'Email',
                        'ingestion_time': 'Date d\'ingestion'
                    })
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("Aucun utilisateur trouvé. Attendez que des données arrivent dans le système.")
            
            # Attendre avant le prochain rafraîchissement
            time.sleep(refresh_rate)
            
        except Exception as e:
            st.error(f"Une erreur s'est produite: {e}")
            time.sleep(refresh_rate)

if __name__ == "__main__":
    main()