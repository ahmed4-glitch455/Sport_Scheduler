import os
import requests
from datetime import datetime

def get_config():
    """Récupère les configurations depuis les variables d'environnement (GitHub Secrets)."""
    return {
        "foot_api": os.environ.get("FOOT_API"),
        "telegram_token": os.environ.get("TELEGRAM_API"),
        "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID"),
        "base_url": "https://api.sportmonks.com/v3"
    }

def fetch_today_matches(api_token, base_url):
    """Récupère les matchs de football prévus aujourd'hui."""
    today = datetime.now().strftime('%Y-%m-%d')
    # Endpoint pour les matchs par date
    url = f"{base_url}/football/fixtures/date/{today}"
    
    headers = {
        "Authorization": api_token,
        "Accept": "application/json"
    }
    
    # On ajoute 'include=league;participants' pour avoir les noms des ligues et des équipes
    params = {
        "include": "league;participants"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"❌ Erreur Sportmonks: {e}")
        return []

def send_telegram_message(token, chat_id, message):
    """Envoie un message via l'API Telegram Bot."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Message envoyé sur Telegram avec succès.")
    except Exception as e:
        print(f"❌ Erreur Telegram: {e}")

def main():
    config = get_config()
    
    # Vérification des secrets
    if not all([config["foot_api"], config["telegram_token"], config["telegram_chat_id"]]):
        print("❌ Erreur : Certains secrets GitHub sont manquants.")
        return

    print(f"🚀 Démarrage du scheduler le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    matches = fetch_today_matches(config["foot_api"], config["base_url"])
    
    if not matches:
        send_telegram_message(config["telegram_token"], config["telegram_chat_id"], "⚽ Aucun match programmé pour aujourd'hui.")
        return

    # Construction du message
    msg_lines = ["*📅 Programme Foot du Jour* \n"]
    
    # On traite les 10 premiers matchs pour éviter les messages trop longs
    for match in matches[:15]:
        league_name = match.get('league', {}).get('name', 'Ligue Inconnue')
        # Les participants sont généralement une liste
        participants = match.get('participants', [])
        home_team = "Equipe A"
        away_team = "Equipe B"
        
        for p in participants:
            if p.get('meta', {}).get('location') == 'home':
                home_team = p.get('name')
            else:
                away_team = p.get('name')
        
        starting_at = match.get('starting_at', '').split(' ')[1][:5] # Récupère HH:MM
        msg_lines.append(f"⏰ {starting_at} | *{league_name}*")
        msg_lines.append(f"🏟️ {home_team} 🆚 {away_team}\n")

    full_message = "\n".join(msg_lines)
    send_telegram_message(config["telegram_token"], config["telegram_chat_id"], full_message)

if __name__ == "__main__":
    main()
