import requests
import os
import logging
from datetime import datetime

# --- CONFIGURATION ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class APIFootball:
    """Client simple pour récupérer uniquement les matchs du jour"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "api-football-v1.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': self.host
        }
    
    def get_today_fixtures(self):
        """Récupère UNIQUEMENT les matchs du jour"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        params = {
            'date': today,
            'timezone': 'Africa/Casablanca',  # Adaptez à votre fuseau
            'status': 'NS-TBD'  # NS = Not Started, TBD = To Be Defined
        }
        
        try:
            print(f"📅 Récupération des matchs du {today}...")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get('response', [])
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def get_tv_channels(self, fixture_id):
        """Récupère les chaînes TV pour un match (si disponibles)"""
        # Note: Les infos TV peuvent nécessiter un autre endpoint
        # Pour l'instant, on simule ou on laisse vide
        return []

def format_fixtures_only(fixtures):
    """Formate UNIQUEMENT les matchs sans scores"""
    if not fixtures:
        return "📭 Aucun match programmé aujourd'hui."
    
    message = "📅 *MATCHS DU JOUR*\n\n"
    
    # Grouper par ligue
    leagues = {}
    for match in fixtures:
        league_name = match['league']['name']
        if league_name not in leagues:
            leagues[league_name] = []
        leagues[league_name].append(match)
    
    # Construire le message
    for league_name, matches in leagues.items():
        message += f"🏆 *{league_name}*\n"
        message += "━" * 25 + "\n"
        
        for match in matches:
            # Heure du match
            timestamp = match['fixture']['timestamp']
            match_time = datetime.fromtimestamp(timestamp).strftime("%H:%M")
            
            # Équipes
            home = match['teams']['home']['name']
            away = match['teams']['away']['name']
            
            message += f"⏱️ {match_time}\n"
            message += f"⚽ {home} vs {away}\n"
            
            # Statut (optionnel, pour info)
            status = match['fixture']['status']['long']
            if status != "Not Started":
                message += f"📌 {status}\n"
            
            message += "\n"
        
        message += "\n"
    
    # Ajouter un footer simple
    message += "━" * 35 + "\n"
    message += "#Football #MatchsDuJour"
    
    return message

def send_telegram_message(message):
    """Envoie le message Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        response = requests.post(
            url,
            data={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def run():
    print("\n" + "="*50)
    print("⚽ BOT MATCHS DU JOUR")
    print("="*50 + "\n")
    
    # Vérification des clés
    if not all([RAPIDAPI_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("❌ Clés API manquantes")
        return
    
    # Initialisation
    api = APIFootball(RAPIDAPI_KEY)
    
    # Récupérer les matchs du jour
    fixtures = api.get_today_fixtures()
    
    # Formatage simple (matchs uniquement)
    message = format_fixtures_only(fixtures)
    
    # Envoyer sur Telegram
    if send_telegram_message(message):
        print(f"✅ {len(fixtures)} matchs envoyés sur Telegram")
    else:
        print("❌ Échec de l'envoi")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    run()
