import os
import time
import requests
import math
import csv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json

# ------------ SISTEMA DE LICENCIAS/CREDITOS (BD ENCRIPTADA) -----------
import sqlite3
import bcrypt

DB_NAME = "database_segura.db"

def get_credits(username):
    if not os.path.exists(DB_NAME): return 0
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT creditos FROM usuarios WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row: return row[0]
    return 0

def use_credit(username, cost=1):
    c = get_credits(username)
    if c >= cost:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE username=?", (cost, username))
        conn.commit()
        conn.close()
        return True
    return False

def verify_login(username, password):
    if not os.path.exists(DB_NAME): return False
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM usuarios WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8'))
    return False
# ------------------------------------------------------

# Configuración de página principal
st.set_page_config(page_title="Dark Pool Sports", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# Inyección de CSS Avanzado y Glassmorphism para Premium UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }
    
    /* Ultimate AI Terminal Theme */
    .stApp {
        background-color: #05080f;
        background-image: 
            linear-gradient(rgba(0, 242, 254, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 242, 254, 0.03) 1px, transparent 1px);
        background-size: 20px 20px;
        background-position: -1px -1px;
    }

    /* Scanline effect */
    .stApp::after {
        content: " ";
        display: block;
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
        z-index: 2;
        background-size: 100% 2px, 3px 100%;
        pointer-events: none;
    }

    /* Glitch/Neon Title */
    .premium-title {
        color: #fff;
        font-size: 4rem;
        font-weight: 700;
        text-transform: uppercase;
        text-align: center;
        margin-bottom: 0;
        padding-bottom: 0;
        letter-spacing: 2px;
        text-shadow: 
            0 0 5px #fff,
            0 0 10px #fff,
            0 0 20px #0ff,
            0 0 40px #0ff,
            0 0 80px #0ff;
        animation: pulse 2s infinite alternate;
    }
    
    @keyframes pulse {
        0% { text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 20px #0ff, 0 0 40px #0ff; }
        100% { text-shadow: 0 0 2px #fff, 0 0 5px #fff, 0 0 10px #0ff, 0 0 20px #0ff, 0 0 30px #0ff; }
    }
    
    .subtitle {
        text-align: center;
        color: #0ff;
        font-size: 1.2rem;
        font-weight: 500;
        letter-spacing: 6px;
        text-transform: uppercase;
        margin-bottom: 50px;
        position: relative;
    }

    /* Cyberpunk HUD Cards */
    .glass-card {
        background: linear-gradient(135deg, rgba(2, 6, 23, 0.8) 0%, rgba(15, 23, 42, 0.7) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(0, 242, 254, 0.2);
        border-radius: 4px; /* Angled corners look more cyberpunk */
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.05) inset, 0 4px 20px rgba(0,0,0,0.5);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    /* Decoration lines on cards */
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00f2fe, transparent);
        opacity: 0.5;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 242, 254, 0.5);
        box-shadow: 0 0 30px rgba(0, 242, 254, 0.1) inset, 0 8px 30px rgba(0, 242, 254, 0.1);
    }
    
    /* Neon Status Indicators */
    .conf-alto { border-left: 4px solid #00ffaa; box-shadow: -10px 0 20px -10px rgba(0, 255, 170, 0.4); border-top: none;}
    .conf-medio { border-left: 4px solid #ffaa00; box-shadow: -10px 0 20px -10px rgba(255, 170, 0, 0.4); border-top: none;}
    .conf-bajo { border-left: 4px solid #ff0055; box-shadow: -10px 0 20px -10px rgba(255, 0, 85, 0.4); border-top: none;}

    /* Highly advanced buttons */
    .stButton>button {
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid #00f2fe;
        color: #00f2fe;
        border-radius: 2px;
        font-weight: 600;
        font-size: 1rem;
        padding: 12px 24px;
        letter-spacing: 2px;
        text-transform: uppercase;
        width: 100%;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        z-index: 1;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 242, 254, 0.4), transparent);
        transition: all 0.4s ease;
        z-index: -1;
    }
    
    .stButton>button:hover::before {
        left: 100%;
    }
    
    .stButton>button:hover {
        background: rgba(0, 242, 254, 0.2);
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
        text-shadow: 0 0 5px #0ff;
        color: #fff;
    }
    
    /* Estilos de Métricas Holográficas */
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.8), 0 0 20px rgba(0, 242, 254, 0.4);
        display: block;
        margin-top: 10px;
        font-family: monospace; /* Numbers look better in terminal mono */
    }
    
    /* Tabs Terminal Style */
    div[data-baseweb="tab-list"] {
        gap: 5px;
        justify-content: center;
        margin-bottom: 30px;
        border-bottom: 1px solid rgba(0, 242, 254, 0.2);
        padding-bottom: 1px;
    }
    div[data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        border: 1px solid transparent;
        padding: 10px 25px;
        transition: all 0.2s;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.9rem;
    }
    div[aria-selected="true"] {
        background: rgba(0, 242, 254, 0.05);
        border: 1px solid rgba(0, 242, 254, 0.3);
        border-bottom: 2px solid #00f2fe;
        color: #00f2fe !important;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
    }
    
    /* Input Fields / Selectors Cyberpunk */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid rgba(0, 242, 254, 0.2) !important;
        color: #0ff !important;
        border-radius: 0 !important;
        font-family: monospace;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #00f2fe !important;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.2) !important;
    }
    
    /* Text Area Console */
    .stTextArea textarea {
        background-color: rgba(5, 10, 20, 0.9) !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        color: #00ffaa !important;
        border-radius: 2px;
        font-family: monospace;
        box-shadow: inset 0 0 15px rgba(0,0,0,0.8);
    }
    .stTextArea textarea:focus {
        border-color: #00ffaa !important;
        box-shadow: inset 0 0 15px rgba(0, 255, 170, 0.1) !important;
    }
    
    /* Cyber Manual Tooltips */
    details.cyber-manual {
        margin-bottom: 25px;
        margin-top: 5px;
        border-left: 2px solid rgba(0, 242, 254, 0.5);
        background: rgba(0, 242, 254, 0.03);
        padding: 12px 18px;
        color: #94a3b8;
        font-size: 0.85rem;
        border-radius: 0 4px 4px 0;
        transition: all 0.3s ease;
    }
    details.cyber-manual:hover {
        background: rgba(0, 242, 254, 0.08);
    }
    details.cyber-manual summary {
        cursor: pointer;
        color: #00f2fe;
        font-weight: 600;
        outline: none;
        list-style: none; /* remove default arrow */
        letter-spacing: 1.5px;
        font-size: 0.8rem;
    }
    details.cyber-manual summary::-webkit-details-marker {
        display: none;
    }
    details.cyber-manual summary::before {
        content: "[+] ";
        color: #0ff;
        font-family: monospace;
    }
    details.cyber-manual[open] summary::before {
        content: "[-] ";
    }
    details.cyber-manual p {
        margin-top: 12px;
        margin-bottom: 0;
        line-height: 1.6;
        border-top: 1px dashed rgba(0, 242, 254, 0.2);
        padding-top: 12px;
        color: #cbd5e1;
    }
    
    /* Responsive Mobile Design */
    @media (max-width: 768px) {
        .premium-title { font-size: 2rem !important; text-shadow: 0 0 10px #0ff; }
        .subtitle { font-size: 0.8rem !important; letter-spacing: 2px !important; margin-bottom: 25px; }
        .glass-card { padding: 15px !important; margin-bottom: 15px !important; }
        .stButton>button { padding: 10px !important; font-size: 0.9rem !important; }
        div[data-baseweb="tab-list"] { flex-wrap: wrap; gap: 2px; }
        div[data-baseweb="tab"] { flex: 1 1 45%; text-align: center; margin-bottom: 5px; font-size: 0.7rem; padding: 8px 5px; }
        .metric-value { font-size: 1.8rem !important; }
    }

    /* Ocultar elementos de Streamlit (Github, Menu, Footer) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- INICIO DE SESIÓN OBLIGATORIO ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

if not st.session_state["logged_in"]:
    st.markdown("<h1 class='premium-title' style='margin-top: 50px;'>DARK POOL SPORTS | ACCESO RESTRINGIDO</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>PORTAL DE CLIENTES VIP</p>", unsafe_allow_html=True)
    
    colA, colB, colC = st.columns([1,2,1])
    with colB:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse (Prueba)"])
        
        with tab_login:
            st.subheader("Ingreso de Clientes VIP")
            user_input = st.text_input("Usuario (ID Cliente):")
            pass_input = st.text_input("Contraseña / Llave de Acceso:", type="password")
            
            if st.button("🔌 Conectar a Servidores Centrales"):
                if verify_login(user_input, pass_input):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user_input
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas. Acceso Denegado.")
                    
        with tab_register:
            st.subheader("Solicitar Acceso Gratuito")
            st.markdown("<p style='color: #cbd5e1; font-size: 0.9rem;'>Crea tu cuenta y obtén <b>3 créditos de prueba gratuitos</b> para testear nuestra IA.<br>Para recargar, contacta al administrador.</p>", unsafe_allow_html=True)
            new_user = st.text_input("Crear Usuario Nuevo:", key="new_user")
            new_pass = st.text_input("Crear Contraseña:", type="password", key="new_pass")
            
            if st.button("🚀 Crear Cuenta de Prueba"):
                if new_user and new_pass:
                    import sqlite3
                    import bcrypt
                    
                    # Intentar obtener la IP del cliente (funciona en servidores web desplegados)
                    client_ip = "local_network"
                    try:
                        if hasattr(st, "context") and hasattr(st.context, "headers"):
                            client_ip = st.context.headers.get("X-Forwarded-For", "local_network").split(",")[0].strip()
                        else:
                            from streamlit.web.server.websocket_headers import _get_websocket_headers
                            headers = _get_websocket_headers()
                            if headers and "X-Forwarded-For" in headers:
                                client_ip = headers["X-Forwarded-For"].split(",")[0].strip()
                    except:
                        pass
                        
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    
                    # Crear tabla de usuarios si no existe
                    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                password_hash TEXT NOT NULL,
                                creditos INTEGER NOT NULL
                            )''')
                    
                    # Crear tabla de control de spam de IPs
                    cursor.execute('''CREATE TABLE IF NOT EXISTS registro_ips (
                                ip TEXT UNIQUE NOT NULL,
                                fecha_registro TEXT NOT NULL
                            )''')
                            
                    # Verificar si la IP ya existe (si no es red local en pruebas)
                    if client_ip != "local_network" and client_ip != "127.0.0.1":
                        cursor.execute("SELECT ip FROM registro_ips WHERE ip=?", (client_ip,))
                        if cursor.fetchone():
                            st.error("⛔ SISTEMA ANTI-SPAM: Ya se ha creado una cuenta recientemente desde esta red/dispositivo. No puedes crear otra.")
                            conn.close()
                            st.stop()
                    
                    salt = bcrypt.gensalt()
                    hash_pw = bcrypt.hashpw(new_pass.encode('utf-8'), salt)
                    
                    try:
                        # Registrar IP
                        if client_ip != "local_network" and client_ip != "127.0.0.1":
                            from datetime import datetime
                            cursor.execute("INSERT INTO registro_ips (ip, fecha_registro) VALUES (?, ?)", (client_ip, str(datetime.now())))
                            
                        # Crear usuario
                        cursor.execute("INSERT INTO usuarios (username, password_hash, creditos) VALUES (?, ?, ?)", 
                                       (new_user, hash_pw.decode('utf-8'), 3))
                        conn.commit()
                        st.success(f"✅ ¡Éxito! Cuenta '{new_user}' creada con 3 créditos. Ahora ve a la pestaña 'Iniciar Sesión'.")
                    except sqlite3.IntegrityError:
                        st.error(f"❌ Error: El usuario o la IP utilizada ya existen en nuestros registros.")
                    finally:
                        conn.close()
                else:
                    st.warning("⚠️ Debes completar todos los campos.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # Frena la carga de la app si no ha iniciado sesión
# ------------------------------------

# Inicializar
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not API_KEY or API_KEY == "tu_api_key_de_google_aqui":
    st.error("Error Crítico: No se encontró tu GEMINI_API_KEY en el archivo '.env'")
    st.stop()

# Cliente de IA Global
client = genai.Client(api_key=API_KEY)

# Prompts Puntuación Matrix
PROMPTS = {
    "Fútbol": """Rol: Quant de Fondo de Inversión Deportivo (Fútbol).
Regla Estricta: Entregame un Sistema de Puntuación Matrix (Radar Estadístico del 1 al 10).
Formato OBLIGATORIO:
[Motivación: X/10] - [Clima/Viaje: X/10] - [Lesiones Clave: X/10] - [Smart Money: X/10]
SCORE FINAL ORO: X.XX (Solo apuestas si > 8.00).
Debajo del radar da tu Pick exacto y 1 oración de justificación analítica. ¡Nada de saludos!""",
    
    "Básquetbol": """Rol: Analista Quant de Básquetbol de Wall Street.
Regla Estricta: Entregame un Sistema de Puntuación Matrix basado en Eficiencia (Rating) (1 al 10).
Formato OBLIGATORIO:
[Pace (Ritmo): X/10] - [Ventaja Matchup: X/10] - [Lesiones Clave: X/10] - [Smart Money: X/10]
SCORE FINAL ORO: X.XX (Solo apuestas si > 8.00).
Debajo del radar da tu Pick exacto y 1 oración de justificación analítica.""",
    
    "Jugadores (Props)": """Rol: Scout de Élite.
Regla Estricta: Entregame un Radar Predictivo de Props del 1 al 10.
Formato OBLIGATORIO:
[Minutos Estimados: X/10] - [Usage Rate: X/10] - [Emparejamiento Defensivo: X/10]
SCORE FINAL ORO: X.XX (Solo apuestas si > 8.00).
Debajo del radar da tu Pick exacto y 1 oración justificativa."""
}

def analyze_ai(match_data, prompt_text):
    with st.spinner('🤖 Inteligencia Artificial analizando bases de datos... (Puede tomar 5-10 segs)'):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{prompt_text}\n\nDato a investigar hoy (Usa el Buscador de Google incorporado):\n{match_data}",
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                    temperature=0.2
                )
            )
            return response.text
        except Exception as e:
            return f"Error en IA: {e}"

from collections import Counter
from bs4 import BeautifulSoup

def buscar_equipo_api(equipo):
    with st.spinner(f"🌍 Rastrando '{equipo}' en bolsas de apuestas internacionales..."):
        try:
            ligas = ["basketball_nba", "soccer_epl", "soccer_spain_la_liga", "soccer_uefa_champs_league", "soccer_mexico_ligamx"]
            for liga in ligas:
                res = requests.get(f"https://api.the-odds-api.com/v4/sports/{liga}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets=h2h").json()
                if isinstance(res, list):
                    for event in res:
                        if equipo.lower() in event['home_team'].lower() or equipo.lower() in event['away_team'].lower():
                            return event
        except: pass
    return None

from serpapi import GoogleSearch

def web_scraper_alineaciones(equipo):
    # Función utilizando proxy de Google News / SERP API
    with st.spinner(f"🕵️‍♂️ Extrayendo alineaciones y reportes médicos para {equipo}..."):
        serp_key = os.getenv("SERPAPI_KEY")
        if not serp_key or serp_key == "tu_serpapi_key_aqui":
            return f"⚠️ Error: No configuraste tu SERPAPI_KEY en el archivo .env\nConsigue una gratuita en serpapi.com para que el bot pueda leer Google automatizadamente."
        
        try:
            params = {
              "q": f"alineaciones probables {equipo} lesionados",
              "hl": "es",
              "gl": "es",
              "api_key": serp_key
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            
            snippets = []
            if "organic_results" in results:
                for result in results["organic_results"][:3]:
                    snippets.append(result.get("snippet", ""))
                    
            if not snippets:
                return f"No se encontró información reciente de alineaciones para {equipo} en las noticias hoy."
                
            info_cruda = " ".join(snippets)
            
            # Pasarlo a Gemini para que lo estructure bonito
            prompt_resumen = f"Lee estos recortes de noticias en Google sobre el equipo '{equipo}' y resume su alineación probable y especialmente quiénes están LESIONADOS o DUDAS. Sé directo.\n\nNoticias:\n{info_cruda}"
            respuesta_bot = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_resumen).text
            
            return respuesta_bot
            
        except Exception as e:
            return f"Error leyendo Google: {e}"

def get_allsports_info(equipo):
    if not ALLSPORTS_API_KEY or ALLSPORTS_API_KEY == "tu_allsports_api_key_aqui":
        return ""
    try:
        url = f"https://apiv2.allsportsapi.com/football/?met=Teams&teamName={equipo}&APIkey={ALLSPORTS_API_KEY}"
        res = requests.get(url, timeout=5).json()
        if res.get("result"):
            team = res["result"][0]
            return f"[AllSportsAPI] Datos {equipo}: Estadio: {team.get('team_stadium', 'N/A')}, Coach: {team.get('coaches', [{'coach_name': 'N/A'}])[0].get('coach_name', 'N/A')}."
    except:
        pass
    return ""

def get_rapidapi_info(equipo):
    if not RAPIDAPI_KEY or RAPIDAPI_KEY == "tu_rapidapi_key_aqui":
        return ""
    try:
        # Usamos API-Football, que es la más popular de deportes en RapidAPI
        url = "https://api-football-v1.p.rapidapi.com/v3/teams"
        querystring = {"search": equipo}
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        res = requests.get(url, headers=headers, params=querystring, timeout=5).json()
        if res.get("response") and len(res["response"]) > 0:
            team_info = res["response"][0]["team"]
            venue_info = res["response"][0]["venue"]
            return f"[RapidAPI] Info {team_info.get('name')}: País: {team_info.get('country')}, Fundado: {team_info.get('founded')}, Estadio: {venue_info.get('name')} (Capacidad: {venue_info.get('capacity')})."
    except:
        pass
    return ""

def recolectar_datos_extra_apis(equipo):
    extra = []
    allsports = get_allsports_info(equipo)
    if allsports: extra.append(allsports)
    rapid = get_rapidapi_info(equipo)
    if rapid: extra.append(rapid)
    return " | ".join(extra) if extra else ""



# ================== INTERFAZ GRÁFICA (UI) ==================

st.markdown("<h1 class='premium-title'>DARK POOL SPORTS</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>DETECCIÓN DE SMART MONEY & ARBITRAJE CON IA CUÁNTICA</p>", unsafe_allow_html=True)
st.markdown("---")

# Menú lateral (Sidebar) elegante
with st.sidebar:
    st.markdown("## 🤖 DARK POOL SPORTS Engine")
    st.markdown("---")
    st.markdown("### 🎛️ Panel de Control")
    st.markdown("Tu agencia personal de datos deportivos, conectada en la nube y alimentada por IA Cuántica.")
    st.markdown("---")
    
    st.markdown("💡 **Status del Sistema:**")
    st.markdown("🟢 Red Neuronal (LLM): **Online**")
    st.markdown(f"{'🟢' if ODDS_API_KEY else '🔴'} The Odds API: **{'Online' if ODDS_API_KEY else 'Offline'}**")
    st.markdown(f"{'🟢' if ALLSPORTS_API_KEY else '🔴'} AllSportsAPI: **{'Online' if ALLSPORTS_API_KEY else 'Offline'}**")
    st.markdown(f"{'🟢' if RAPIDAPI_KEY else '🔴'} RapidAPI: **{'Online' if RAPIDAPI_KEY else 'Offline'}**")
    
    st.markdown("---")
    st.markdown("### 🪫 Nivel de Energía")
    credit_placeholder = st.empty()
    
    def update_credits_ui():
        c_r = get_credits(st.session_state['username'])
        col = "#00f2fe" if c_r > 0 else "#ff0055"
        v_h = f'<div style="border: 1px dashed {col}; border-radius: 4px; padding: 15px; text-align: center; background: rgba(0,0,0,0.5);"><h1 style="color: {col}; font-family: monospace; font-size: 2rem; margin:0;">{c_r} CMD</h1><p style="color: #94a3b8; font-size: 0.8rem; margin:0;">Consultas Disponibles</p></div>'
        credit_placeholder.markdown(v_h, unsafe_allow_html=True)
        if c_r == 0:
            credit_placeholder.error("Requiere recarga de licencia.")

    update_credits_ui()
    
    st.markdown(f"**Usuario Actual:** {st.session_state['username']}")
    if st.button("Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

# Contenedor central de pestañas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🤖 Oráculo", 
    "🌐 Escáner Individual", 
    "🔥 Creador Parlays",
    "💸 Arbitraje (Surebets)",
    " Dashboard ROI"
])

# ------------- PESTAÑA 1 (Análisis Manual + POISSON) -------------
with tab1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🤖 Algoritmo de Edge y Poisson")
    st.markdown("""<details class="cyber-manual"><summary>MANUAL DE OPERACIÓN: ORÁCULO & POISSON</summary><p><b>Función:</b> Calcula la probabilidad real (Cuota Justa) mediante matemáticas asépticas (xG) y compara con datos del usuario.<br><b>Uso:</b> 1. Define los Goles Esperados (xG) para procesar matemáticas puras. 2. Pega en la caja lateral información clave u análisis del Scraper. 3. Ejecuta para que la IA cuántica unifique ambas informaciones y asigne un SCORE (1 a 10).</p></details>""", unsafe_allow_html=True)
    
    colA, colB = st.columns([1, 1.5])
    
    with colA:
        deporte = st.selectbox("🌐 Seleccionar Vector de Análisis:", ["Fútbol", "Básquetbol", "Jugadores (Props)"])
        
        poisson_data = ""
        if deporte == "Fútbol":
            st.markdown("🎯 **Motor de Probabilidades de Poisson**")
            xg_home = st.number_input("xG (Goles Esperados) Local [Deja en 0 para auto-cálculo de IA]", min_value=0.0, value=0.0, step=0.1)
            xg_away = st.number_input("xG (Goles Esperados) Visitante [Deja en 0 para auto-cálculo de IA]", min_value=0.0, value=0.0, step=0.1)
            
            if xg_home > 0 and xg_away > 0:
                # Cálculo Poisson Básico para victoria local/visitante o empate
                prob_home = 0
                prob_away = 0
                prob_draw = 0
                for g_h in range(6):
                    for g_a in range(6):
                        p = ((math.exp(-xg_home) * (xg_home**g_h)) / math.factorial(g_h)) * ((math.exp(-xg_away) * (xg_away**g_a)) / math.factorial(g_a))
                        if g_h > g_a: prob_home += p
                        elif g_a > g_h: prob_away += p
                        else: prob_draw += p
                
                p_h_pct = prob_home * 100
                p_a_pct = prob_away * 100
                p_d_pct = prob_draw * 100
                
                # Cálculo cuotas justas
                cuota_justa_h = 1/prob_home if prob_home > 0 else 0
                cuota_justa_a = 1/prob_away if prob_away > 0 else 0
                
                st.info(f"📊 **Matemática Pura:**\nLocal {p_h_pct:.1f}% (Cuota Justa: {cuota_justa_h:.2f})\nEmpate {p_d_pct:.1f}%\nVisita {p_a_pct:.1f}% (Cuota Justa: {cuota_justa_a:.2f})")
                poisson_data = f"El modelo matemático exacto de Poisson le da al Local {p_h_pct:.1f}% de ganar y al Visitante {p_a_pct:.1f}%.\n"
            else:
                st.info("🤖 **Modo Automático:** La IA buscará en la base de datos y calculará el xG y el Poisson por ti basándose en tu equipo o enlace.")
                poisson_data = "El usuario no proporcionó el xG. Debes leer el texto adjunto, inferir el poder ofensivo de ambos equipos automáticamente, y proyectar tú mismo quién ganará basándote en la data."

    with colB:
        user_input = st.text_area("📝 Datos Estructurados del Enfrentamiento:", height=200, placeholder="Pega el texto de cuotas, url del partido, o solo los nombres de los equipos...")
        
        if st.button("🚀 Ejecutar Algoritmo"):
            if not user_input:
                st.error("⚠️ Inserta el paquete de datos en el servidor primero.")
            else:
                if use_credit(st.session_state['username']):
                    update_credits_ui()
                    # Concatenar para inyectar matemática si es futbol
                    data_final = poisson_data + "\nDatos crudos para procesar: " + user_input
                    resultado = analyze_ai(data_final, PROMPTS[deporte])
                    
                    # Clasificar clase de confianza evaluando la matriz numéricamente (ej. > 8.00)
                    confianza_clase = "conf-alto" if "SCORE FINAL ORO: 8" in resultado.upper() or "SCORE FINAL ORO: 9" in resultado.upper() or "SCORE FINAL ORO: 10" in resultado.upper() else "conf-medio" if "SCORE FINAL" in resultado.upper() else "conf-bajo"
                    st.session_state['res_oraculo'] = f"### 🎯 Score Radar Matrix (1-10)\n<div class='glass-card {confianza_clase}'><pre style='white-space: pre-wrap; font-family: Inter; color: #fff; background: transparent; border: none;'>{resultado}</pre></div>"
                    
                    # Auto Tracker (Guardar en CSV)
                    try:
                        with open('historial_apuestas.csv', mode='a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f, delimiter=';')
                            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), deporte, "Análisis Bot", "Radar Matrix Guardado", "N/A", "Pendiente", "0"])
                    except Exception:
                        pass
                else:
                    st.error("❌ ENERGÍA AGOTADA. Contacte a su proveedor para recargar su licencia para este equipo.")
                    
        if 'res_oraculo' in st.session_state:
            st.markdown(st.session_state['res_oraculo'], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🕵️‍♂️ Intel Gathering & FootyStats Scraper")
    st.markdown("""<details class="cyber-manual"><summary>MANUAL DE OPERACIÓN: INTEL SCRAPER</summary><p><b>Función:</b> Rastrea noticias de internet o extrae métricas avanzadas (xG, posesión, stats) directamente de <b>FootyStats.org</b>.<br><b>Uso:</b> Pega la URL directa del partido de FootyStats. El bot bypasseará la web, extraerá toda la métrica dura disponible y te dará un resumen estadístico para pegarlo en el Oráculo superior.</p></details>""", unsafe_allow_html=True)
    col_sc1, col_sc2 = st.columns([2, 1])
    with col_sc1:
        url_scrape = st.text_input("🔗 URL de FootyStats del partido (o nombre del equipo):", placeholder="Ej. https://footystats.org/italy/ssc-napoli-vs-torino...")
    with col_sc2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("�️ Scrapear Datos Privados"):
            if url_scrape:
                if use_credit(st.session_state['username']):
                    update_credits_ui()
                    with st.spinner("Desencriptando y extrayendo Big Data..."):
                        if "http" in url_scrape and "footystats" in url_scrape:
                            import requests
                            from bs4 import BeautifulSoup
                            try:
                                heads = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                                r = requests.get(url_scrape, headers=heads, timeout=15)
                                if r.status_code == 200:
                                    soup = BeautifulSoup(r.text, 'html.parser')
                                    # Limpiamos el texto masivo para Gemini
                                    texto_limpio = ' '.join(soup.body.get_text(separator=' ', strip=True).split())
                                    # Cortamos a 3500 caracteres, que es donde suele estar lo vital (xG, H2H, forma)
                                    stat_data = "DATOS FOOTYSTATS ENCONTRADOS:\n" + texto_limpio[:3500]
                                    st.session_state['res_scraper'] = stat_data
                                else:
                                    st.error(f"⚠️ Error {r.status_code} al bypassear FootyStats. Su firewall bloqueó el bot temporariamente.")
                            except Exception as e:
                                st.error(f"⚠️ Error de Scraper: {e}")
                        else:
                            st.info("Buscando como equipo regular en la web...")
                            resultado_scrape = web_scraper_alineaciones(url_scrape)
                            extra_api_data = recolectar_datos_extra_apis(url_scrape)
                            if extra_api_data:
                                resultado_scrape += f"\n\n📊 Datos Adicionales (AllSports/RapidAPI):\n{extra_api_data}"
                            st.session_state['res_scraper'] = resultado_scrape
                else:
                    st.error("❌ ENERGÍA AGOTADA. Adquiere una recarga de la terminal.")
            else:
                st.error("Introduce una URL o equipo.")
                
        if 'res_scraper' in st.session_state:
            st.success("✅ ¡Datos extraídos con éxito! Cópialos y pégalos en la caja de 'Datos Estructurados' arriba.")
            st.code(st.session_state['res_scraper'], language=None)
    st.markdown("</div>", unsafe_allow_html=True)


# ------------- PESTAÑA 2 (Escáner API) -------------
with tab2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🌐 Radar Global Múltiple (API-Sports)")
    st.markdown("""<details class="cyber-manual"><summary>MANUAL DE OPERACIÓN: RADAR BURSÁTIL MUNDIAL</summary><p><b>Función:</b> Se conecta mediante flujos de API a diversas bolsas de apuestas para detectar desviaciones anómalas en el mercado.<br><b>Uso:</b> Fija un objetivo. El radar interceptará sus variables en tiempo real, evaluando si el mercado tiene pánico, dónde está el 'Smart Money', y devolverá el pronóstico estadístico sugerido.</p></details>""", unsafe_allow_html=True)
    
    if not ODDS_API_KEY or ODDS_API_KEY == "tu_odds_api_key_aqui":
        st.error("No tienes configurada la llave secreta en el archivo .env. Esto desactivará el escaneo mundial automático.")
    else:
        equipo_buscar = st.text_input("🔍 Fijar objetivo a rastrear en bolsas Mundiales (Ej. 'Arsenal', 'Lakers'):", placeholder="Escribe el equipo principal...")
        
        if st.button("📡 Iniciar Triangulación de Mercados"):
            if equipo_buscar:
                if use_credit(st.session_state['username']):
                    update_credits_ui()
                    match = buscar_equipo_api(equipo_buscar)
                    if match:
                        home = match['home_team']
                        away = match['away_team']
                        sport = "Básquetbol" if "basketball" in match['sport_key'] else "Fútbol"
                        
                        extra_info = ""
                        if ALLSPORTS_API_KEY or RAPIDAPI_KEY:
                            extra_info = f"\n📦 Base extra AllSports/RapidAPI:\n- {recolectar_datos_extra_apis(home)}\n- {recolectar_datos_extra_apis(away)}\n"
                        
                        input_para_ia = f"Deporte: {sport}\nEquipos: {home} (L) vs {away} (V).{extra_info}\nBusca su información actual del mercado, bajas importantes, su historial H2H reciente y dime tu predicción en tu formato."
                        resultado_api = analyze_ai(input_para_ia, PROMPTS[sport])
                        
                        confianza_clase = "conf-alto" if "Alto" in resultado_api else "conf-medio" if "Medio" in resultado_api else "conf-bajo"
                        st.session_state['res_radar'] = f"✅ Interceptado en el mercado: {home} vs {away}<br><div class='glass-card {confianza_clase}'><pre style='white-space: pre-wrap; font-family: Inter; color: #fff; background: transparent; border: none;'>{resultado_api}</pre></div>"
                    else:
                        st.session_state['res_radar'] = "⚠️ 📡 Sin resultados: El equipo no tiene líneas abiertas en Wall Street actualmente."
                else: # Solo error visual, el debito ya fallo o no paso
                    st.error("❌ ENERGÍA AGOTADA para el radar global.")
            else:
                pass
                
        if 'res_radar' in st.session_state:
            if "Sin resultados" in st.session_state['res_radar']:
                st.warning(st.session_state['res_radar'].replace("⚠️ ", ""))
            elif "Interceptado" in st.session_state['res_radar']:
                st.markdown(st.session_state['res_radar'], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ------------- PESTAÑA 3 (Parlays) -------------
with tab3:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🔥 Inteligencia Correlacional (Parlay Builder)")
    st.markdown("""<details class="cyber-manual"><summary>MANUAL DE OPERACIÓN: CORRELACIONES Y PARLAYS</summary><p><b>Función:</b> Ensambla boletas combinadas evaluando la influencia matemática en cadena (Correlación Positiva).<br><b>Uso:</b> Selecciona el mercado y el umbral de riesgo permitido. El motor triangulará hasta 3 picks algorítmicos que juntos formen un multiplicador (cuota parlay) de alto rendimiento basado en datos en vivo.</p></details>""", unsafe_allow_html=True)
    
    colP1, colP2 = st.columns([1, 1])
    with colP1:
        parlay_sport = st.selectbox("Mercado del Parlay:", ["Fútbol (Europa)", "Básquetbol (NBA)"])
        riesgo = st.radio("Perfil de Riesgo:", ["Seguro (Cuota Baja)", "Agresivo (Cuota Alta)"])
    
    with colP2:
        st.info("La IA conectará con los datos de hoy, evaluará las correlaciones lógicas (ej. 'Si Messi anota, el Barcelona probablemente gane') y te estructurará un ticket de apuesta recomendado.")
    
    if st.button("🧬 Generar Ticket Perfecto"):
        if use_credit(st.session_state['username']):
                    update_credits_ui()
            from datetime import datetime
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            
            prompt_parlay = f"""Rol: Experto en Correlaciones Deportivas.
            REGLA DE ORO INQUEBRANTABLE: Hoy es exactamente {fecha_actual}. 
            Busca en internet los partidos programados EXCLUSIVAMENTE para ESTA fecha ({fecha_actual}) o fechas futuras cercanas.
            BAJO NINGÚN MOTIVO incluyas partidos que ya se jugaron ayer o en meses pasados.
            
            Genera un Parlay (Combinada) de 3 selecciones reales para {parlay_sport} basado estrictamente en juegos a disputarse hoy o mañana. 
            Perfil: {riesgo}.
            Entrega solo el ticket en formato lista, sus cuotas estimadas, y 1 oración de por qué matemáticamente están correlacionados."""
            
            resultado_parlay = analyze_ai(f"Partidos calendario exacto hoy {fecha_actual} en {parlay_sport}", prompt_parlay)
            st.session_state['res_parlay'] = f"<div class='glass-card conf-alto'><pre style='white-space: pre-wrap; font-family: Inter; color: #fff; background: transparent; border: none;'>{resultado_parlay}</pre></div>"
            st.balloons()
        else:
            st.error("❌ ENERGÍA AGOTADA.")
            
    if 'res_parlay' in st.session_state:
        st.markdown(st.session_state['res_parlay'], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------- PESTAÑA 4 (Arbitraje / Surebets) -------------
with tab4:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("💸 Escáner de Arbitraje (Surebets)")
    st.markdown("""<details class="cyber-manual"><summary>MANUAL DE OPERACIÓN: ARBITRAJE INTERNACIONAL</summary><p><b>Función:</b> Explota desequilibrios entre los algoritmos dispersos de múltiples casinos que permiten un Beneficio del 100% libre de riesgo.<br><b>Uso:</b> Ejecuta el escáner masivo de cuotas en una liga. Si la sumatoria y dispersión es menor al 100%, alertará mediante indicador verde exacto a qué Bookies atacar para rentabilidad segura.</p></details>""", unsafe_allow_html=True)
    
    if not ODDS_API_KEY or ODDS_API_KEY == "tu_odds_api_key_aqui":
        st.warning("⚠️ Requiere tu API Key de The Odds API configurada.")
    else:
        liga_surebet = st.selectbox("Liga a escanear:", ["soccer_epl (Premier League)", "basketball_nba (NBA)", "soccer_spain_la_liga (La Liga)"])
        filtro_casas = st.text_input("Filtrar por Casas de Apuestas (Opcional, separadas por coma, Ej: Betano, Olimpo, Pinnacle). Deja vacío el cuadro para rastrear todas las casas mundiales:")
        
        if st.button("📡 Buscar Dinero Fácil (Arbitraje)"):
            if use_credit(st.session_state['username']):
                    update_credits_ui()
                with st.spinner('Comparando miles de cuotas entre Bookmakers...'):
                    try:
                        codigo_liga = liga_surebet.split()[0]
                        res = requests.get(f"https://api.the-odds-api.com/v4/sports/{codigo_liga}/odds/?apiKey={ODDS_API_KEY}&regions=eu,us,uk,au&markets=h2h").json()
                        
                        surebets_encontradas = []
                        
                        if isinstance(res, list):
                            for event in res:
                                home = event['home_team']
                                away = event['away_team']
                                
                                # Buscar las mejores cuotas de todas las casas de apuestas
                                mejor_cuota_1 = 0
                                mejor_bookie_1 = ""
                                mejor_cuota_2 = 0
                                mejor_bookie_2 = ""
                                mejor_cuota_x = 0
                                mejor_bookie_x = ""
                                
                                for bookie in event.get('bookmakers', []):
                                    if filtro_casas:
                                        casas_validas = [c.strip().lower() for c in filtro_casas.split(',')]
                                        if not any(c in bookie['title'].lower() for c in casas_validas):
                                            continue
                                            
                                    if bookie['markets']:
                                        outcomes = bookie['markets'][0]['outcomes']
                                        for o in outcomes:
                                            if o['name'] == home and o['price'] > mejor_cuota_1:
                                                mejor_cuota_1 = o['price']
                                                mejor_bookie_1 = bookie['title']
                                            elif o['name'] == away and o['price'] > mejor_cuota_2:
                                                mejor_cuota_2 = o['price']
                                                mejor_bookie_2 = bookie['title']
                                            elif o['name'] == 'Draw' and o['price'] > mejor_cuota_x:
                                                mejor_cuota_x = o['price']
                                                mejor_bookie_x = bookie['title']
                                
                                # Calcular Margen (Si es menor a 1, es surebet)
                                if mejor_cuota_1 > 0 and mejor_cuota_2 > 0:
                                    val_1 = 1 / mejor_cuota_1
                                    val_2 = 1 / mejor_cuota_2
                                    val_x = (1 / mejor_cuota_x) if mejor_cuota_x > 0 else 0
                                    
                                    margen = val_1 + val_2 + val_x
                                    
                                    if margen < 1.0 and margen > 0:
                                        beneficio = (1 - margen) * 100
                                        surebets_encontradas.append({
                                            'partido': f"{home} vs {away}",
                                            'beneficio': f"{beneficio:.2f}%",
                                            'picks': f"L: @{mejor_cuota_1} ({mejor_bookie_1}) | V: @{mejor_cuota_2} ({mejor_bookie_2})" + (f" | E: @{mejor_cuota_x} ({mejor_bookie_x})" if mejor_cuota_x > 0 else "")
                                        })
                                        
                        # Mostrar Resultados
                        html_out = ""
                        if surebets_encontradas:
                            html_out += f"<h3>🚀 ¡Encontradas {len(surebets_encontradas)} Surebets!</h3>"
                            
                            mensajes_telegram = []
                            for sb in surebets_encontradas:
                                html_out += f"""
                                <div class='glass-card conf-alto'>
                                    <h4>✅ {sb['partido']} <span style="color:#00ff00;">(Beneficio Seguro: {sb['beneficio']})</span></h4>
                                    <p style="color:#8b949e; margin-bottom: 0;">{sb['picks']}</p>
                                </div>
                                """
                                
                                # Formatear mensaje ultra-exclusivo para Telegram
                                msj = f"🚨 <b>SUREBET DETECTADA (ARBITRAJE)</b> 🚨\n\n"
                                msj += f"⚽ <b>Evento:</b> {sb['partido']}\n"
                                msj += f"💰 <b>Beneficio 100% Seguro:</b> {sb['beneficio']}\n\n"
                                msj += f"🎯 <b>Movimientos:</b>\n{sb['picks']}\n\n"
                                msj += f"<i>🤖 DARK POOL SPORTS - Alerta VIP</i>"
                                mensajes_telegram.append(msj)
                                
                            # Enviar a Telegram en background
                            try:
                                import motor_telegram
                                st.toast("Enviando alertas Push a Telegram VIP...", icon="✈️")
                                for m in mensajes_telegram:
                                    motor_telegram.enviar_mensaje_telegram(m)
                                html_out += "<p style='color:#0ff;'>✅ Alertas VIP enviadas a tu celular exitosamente.</p>"
                            except Exception as e:
                                html_out += "<p style='color:#ffaa00;'>⚠️ Surebets encontradas, pero el modulo de Telegram falló o no está configurado.</p>"
                        else:
                            html_out = "📉 No se encontró ninguna oportunidad de arbitraje del 100% en esta liga por ahora. Las casas de apuestas están alineadas."
                            
                        st.session_state['res_surebet'] = html_out
                    except Exception as e:
                        st.error(f"Error procesando cuotas: {e}")
            else:
                st.error("❌ ENERGÍA AGOTADA.")
                
        if 'res_surebet' in st.session_state:
            st.markdown(st.session_state['res_surebet'], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------- PESTAÑA 5 (Base de Datos Viva y ROI Web Tracker) -------------
with tab5:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("📈 Bankroll Data Warehouse")
    st.markdown("""<details class="cyber-manual"><summary>MANUAL DE OPERACIÓN: WAREHOUSE CONTABLE</summary><p><b>Función:</b> Almacén inmutable estadístico de tus operaciones para proyectar y diagramar tu curva fiduciaria y de rendimientos reales.<br><b>Uso:</b> Liquida la ganancia (usd) o pérdida (-usd) y el resultado en la cuadrícula y pulsa en Guardar Permanentes. El gráfico principal trazará matemáticamente tu Delta de Capital, calculando tu Win-Rate estricto y ROI global.</p></details>""", unsafe_allow_html=True)
    
    ruta_csv = 'historial_apuestas.csv'
    
    # Crear CSV si no existe
    if not os.path.exists(ruta_csv):
        pd.DataFrame(columns=["Fecha", "Deporte", "Datos Ingresados", "Pronóstico", "Nivel de Confianza", "Resultado Real", "Ganancia_y_Perdida"]).to_csv(ruta_csv, index=False, sep=";")
    
    df_bd = pd.read_csv(ruta_csv, sep=";")
    
    # Si la columna se guardo como Ganancia/Pérdida en vez de _
    if 'Ganancia/Pérdida' in df_bd.columns:
        df_bd.rename(columns={'Ganancia/Pérdida': 'Ganancia_y_Perdida'}, inplace=True)
    if 'Resultado Real (Llenar manual)' in df_bd.columns:
        df_bd.rename(columns={'Resultado Real (Llenar manual)': 'Resultado Real'}, inplace=True)
        
    df_bd['Ganancia_y_Perdida'] = pd.to_numeric(df_bd['Ganancia_y_Perdida'], errors='coerce').fillna(0)
    
    st.warning("⚠️ Haz doble clic en las columnas 'Resultado Real' y 'Ganancia_y_Perdida' en la tabla inferior para asentar tus operaciones. (Ej. Pon 50 si ganaste dólares, o -20 si perdiste)")
    
    # Editor interactivo de base de datos
    df_editado = st.data_editor(
        df_bd, 
        width="stretch", 
        num_rows="dynamic",
        column_config={
            "Ganancia_y_Perdida": st.column_config.NumberColumn(
                "Ganancia/Pérdida ($)", format="$ %d"
            ),
            "Resultado Real": st.column_config.SelectboxColumn(
                "Resultado Real", options=["En Juego", "Ganada ✅", "Perdida ❌"], required=True
            )
        }
    )
    
    colS1, colS2 = st.columns([1,4])
    with colS1:
        if st.button("💾 Guardar Cambios Permanentes"):
            df_editado.to_csv(ruta_csv, index=False, sep=";")
            st.success("Sincronizado a Disco.")
            st.rerun()

    # Calcular Datos de la Realidad
    capital_inicial = 1000 # Configurable después
    df_editado['Capital_Acumulado'] = capital_inicial + df_editado['Ganancia_y_Perdida'].cumsum()
    
    total_prof = df_editado['Ganancia_y_Perdida'].sum()
    roi_real = (total_prof / capital_inicial) * 100
    
    win_count = len(df_editado[df_editado['Ganancia_y_Perdida'] > 0])
    loss_count = len(df_editado[df_editado['Ganancia_y_Perdida'] < 0])
    total_res = win_count + loss_count
    wr_real = (win_count / total_res * 100) if total_res > 0 else 0
    
    st.markdown("---")
    
    # Métricas Top REALES
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="📊 Dinero Neto Ganado/Perdido", value=f"${total_prof:.2f}", delta=f"Caja Central Actual: ${capital_inicial + total_prof:.2f}")
    with m2:
        st.metric(label="🎯 Win-Rate Verídico", value=f"{wr_real:.1f}%", delta=f"{win_count} Ganadas / {loss_count} Perdidas")
    with m3:
        st.metric(label="🛡️ ROI Total", value=f"{roi_real:.2f}%")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráfica Plotly Premium de Vida Real
    if len(df_editado) > 0:
        fig = px.area(df_editado, x=df_editado.index, y='Capital_Acumulado', title='Curva de Crecimiento Financiero (Real)')
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            title_font=dict(size=24, color='#00C9FF'),
            xaxis=dict(showgrid=False, title='Apuestas Sucesivas N°'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Bankroll Real ($)'),
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        fig.update_traces(
            line=dict(color='#00ff00' if total_prof >= 0 else '#ff4b4b', width=3),
            fillcolor='rgba(0, 255, 0, 0.1)' if total_prof >= 0 else 'rgba(255, 0, 0, 0.1)',
            hovertemplate="Operación N° <b>%{x}</b><br>Capital Tras Impacto: <b>$%{y:.2f}</b><extra></extra>"
        )
        
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Ingresa al menos 1 resultado con Ganancia en tu tabla para observar la matriz de crecimiento.")
        
    st.markdown("</div>", unsafe_allow_html=True)







