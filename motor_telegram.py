import os
import requests
from dotenv import load_dotenv

# Reemplaza con el Token de BotFather que me pasaste
TELEGRAM_BOT_TOKEN = "8704107870:AAHte5AvmJ0lckZ2DRAXuTXr-EFPhrceIVs" 
# Reemplaza con tu Chat ID (Te enseñaré cómo conseguirlo)
TELEGRAM_CHAT_ID = "793948199"

def enviar_mensaje_telegram(mensaje):
    """Función para enviar un mensaje pasivo directo por Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML" # Para poder enviar texto en negrita, cursiva, etc.
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("🟢 ¡Mensaje de Telegram enviado al Grupo VIP/Privado exitosamente!")
            return True
        else:
            print(f"🔴 Error enviando a Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"🔴 Error de conexión a Telegram: {e}")
        return False

# Prueba manual
if __name__ == "__main__":
    print("Probando el motor de notificaciones de Telegram...")
    mensaje_prueba = "🤖 <b>H AI SYSTEM ONLINE</b>\n✅ Conexión establecida.\n📡 <i>Escaneando Betano, Apuesta Total y Olimpo en el background...</i>"
    enviar_mensaje_telegram(mensaje_prueba)
