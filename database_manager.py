import os
import sqlite3
import pandas as pd
import bcrypt
import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Se recomienda usar st.secrets en Streamlit Cloud para estas variables
SUPABASE_URL = st.secrets.get("SUPABASE_URL") if "SUPABASE_URL" in st.secrets else os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") if "SUPABASE_KEY" in st.secrets else os.getenv("SUPABASE_KEY")

LOCAL_DB = "database_segura.db"
LOCAL_CSV = "historial_apuestas.csv"

# ¿Estamos en modo nube?
USING_SUPABASE = SUPABASE_URL is not None and SUPABASE_KEY is not None

def get_supabase_client() -> Client:
    if USING_SUPABASE:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

# --- MÉTRICAS GLOBALES ---

def get_global_metrics():
    """Calcula métricas globales para mostrar públicamente antes del login"""
    if USING_SUPABASE:
        try:
            supabase = get_supabase_client()
            res = supabase.table('historial_apuestas').select('resultado_real').neq('resultado_real', 'En Juego').execute()
            df = pd.DataFrame(res.data)
        except:
            return 0, 0
    else:
        if os.path.exists(LOCAL_CSV):
            df = pd.read_csv(LOCAL_CSV, sep=";")
            df = df[df['resultado_real'] != 'En Juego']
        else:
            return 0, 0
    
    if df.empty:
        return 0, 0
        
    win_count = len(df[df['resultado_real'].str.contains("Ganada ✅", na=False)])
    total = len(df)
    wr = (win_count / total * 100) if total > 0 else 0
    return round(wr, 1), total

# --- GESTIÓN DE CRÉDITOS Y USUARIOS ---

def get_credits(username):
    if USING_SUPABASE:
        try:
            supabase = get_supabase_client()
            res = supabase.table("usuarios").select("creditos").eq("username", username).execute()
            if res.data:
                return res.data[0]["creditos"]
        except Exception as e:
            st.error(f"Error Supabase (Credits): {e}")
    
    # Fallback a SQLite
    if not os.path.exists(LOCAL_DB): return 0
    conn = sqlite3.connect(LOCAL_DB)
    c = conn.cursor()
    c.execute("SELECT creditos FROM usuarios WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def use_credit(username, cost=1):
    if USING_SUPABASE:
        try:
            current = get_credits(username)
            if current >= cost:
                supabase = get_supabase_client()
                supabase.table("usuarios").update({"creditos": current - cost}).eq("username", username).execute()
                return True
        except Exception as e:
            st.error(f"Error Supabase (Use Credit): {e}")
            return False
            
    # Fallback a SQLite
    c_r = get_credits(username)
    if c_r >= cost:
        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET creditos = creditos - ? WHERE username=?", (cost, username))
        conn.commit()
        conn.close()
        return True
    return False

def verify_login(username, password):
    if USING_SUPABASE:
        try:
            supabase = get_supabase_client()
            res = supabase.table("usuarios").select("password_hash").eq("username", username).execute()
            if res.data:
                return bcrypt.checkpw(password.encode('utf-8'), res.data[0]["password_hash"].encode('utf-8'))
        except Exception as e:
            st.error(f"Error Supabase (Login): {e}")
            
    # Fallback a SQLite
    if not os.path.exists(LOCAL_DB): return False
    conn = sqlite3.connect(LOCAL_DB)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM usuarios WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8'))
    return False

def register_user(username, password, client_ip):
    salt = bcrypt.gensalt()
    hash_pw = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    if USING_SUPABASE:
        try:
            supabase = get_supabase_client()
            # Sistema Anti-Spam por IP en Supabase
            if client_ip not in ["local_network", "127.0.0.1"]:
                check_ip = supabase.table("registro_ips").select("ip").eq("ip", client_ip).execute()
                if check_ip.data:
                    return False, "IP_EXISTS"
            
            # Registrar IP
            if client_ip not in ["local_network", "127.0.0.1"]:
                supabase.table("registro_ips").insert({"ip": client_ip, "fecha_registro": datetime.now().isoformat()}).execute()
            
            # Crear Usuario
            supabase.table("usuarios").insert({
                "username": username,
                "password_hash": hash_pw,
                "creditos": 3
            }).execute()
            return True, "SUCCESS"
        except Exception as e:
            if "duplicate key" in str(e).lower(): return False, "USER_EXISTS"
            return False, str(e)

    # Fallback a SQLite
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, creditos INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS registro_ips (ip TEXT UNIQUE, fecha_registro TEXT)''')
    
    if client_ip not in ["local_network", "127.0.0.1"]:
        cursor.execute("SELECT ip FROM registro_ips WHERE ip=?", (client_ip,))
        if cursor.fetchone():
            conn.close()
            return False, "IP_EXISTS"
    
    try:
        if client_ip not in ["local_network", "127.0.0.1"]:
            cursor.execute("INSERT INTO registro_ips (ip, fecha_registro) VALUES (?, ?)", (client_ip, str(datetime.now())))
        cursor.execute("INSERT INTO usuarios (username, password_hash, creditos) VALUES (?, ?, ?)", (username, hash_pw, 3))
        conn.commit()
        return True, "SUCCESS"
    except sqlite3.IntegrityError:
        return False, "USER_EXISTS"
    finally:
        conn.close()
    def get_all_users(self):
        """Obtiene la lista de todos los usuarios (solo para admin)"""
        if self.USING_SUPABASE:
            res = self.supabase.table('usuarios').select('username, creditos').execute()
            return pd.DataFrame(res.data)
        else:
            if os.path.exists('usuarios.csv'):
                return pd.read_csv('usuarios.csv')
            return pd.DataFrame(columns=['username', 'creditos'])

    def admin_update_credits(self, username, new_credits):
        """Actualiza créditos de cualquier usuario (solo para admin)"""
        if self.USING_SUPABASE:
            self.supabase.table('usuarios').update({'creditos': new_credits}).eq('username', username).execute()
        else:
            if os.path.exists('usuarios.csv'):
                df = pd.read_csv('usuarios.csv')
                df.loc[df['username'] == username, 'creditos'] = new_credits
                df.to_csv('usuarios.csv', index=False)
        return True
# --- GESTIÓN DE HISTORIAL ---

def save_prediction(username, deporte, datos_ingresados, pronostico, nivel_confianza):
    if USING_SUPABASE:
        try:
            supabase = get_supabase_client()
            supabase.table("historial_apuestas").insert({
                "username": username,
                "deporte": deporte,
                "datos_ingresados": datos_ingresados[:500],
                "pronostico": pronostico[:1000],
                "nivel_confianza": nivel_confianza,
                "resultado_real": "Pendiente",
                "ganancia_y_perdida": 0
            }).execute()
            return True
        except Exception as e:
            print(f"Error Supabase (Save Prediction): {e}")

    # Fallback a CSV
    try:
        import csv
        with open(LOCAL_CSV, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), deporte, datos_ingresados[:200], pronostico[:500], nivel_confianza, "Pendiente", "0"])
        return True
    except:
        return False

def get_full_history(username=None):
    if USING_SUPABASE:
        try:
            supabase = get_supabase_client()
            query = supabase.table("historial_apuestas").select("*").order("fecha", desc=True)
            if username:
                query = query.eq("username", username)
            res = query.execute()
            return pd.DataFrame(res.data)
        except Exception as e:
            st.error(f"Error Supabase (Get History): {e}")

    # Fallback a CSV
    if not os.path.exists(LOCAL_CSV):
        return pd.DataFrame(columns=["Fecha", "Deporte", "Datos Ingresados", "Pronóstico", "Nivel de Confianza", "Resultado Real", "Ganancia_y_Perdida"])
    
    df = pd.read_csv(LOCAL_CSV, sep=";")
    return df
