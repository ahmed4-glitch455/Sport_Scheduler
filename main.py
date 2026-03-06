import requests
import os
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# --- CONFIGURATION AVEC DÉBOGAGE ---
print("=" * 60)
print("🔍 DIAGNOSTIC DES VARIABLES D'ENVIRONNEMENT")
print("=" * 60)

FOOT_API = os.getenv("FOOT_API")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"FOOT_API: {'✅ Présente' if FOOT_API else '❌ MANQUANTE'}")
if FOOT_API:
    print(f"  → Longueur: {len(FOOT_API)} caractères")
    print(f"  → Début: {FOOT_API[:5]}...")

print(f"TELEGRAM_BOT_TOKEN: {'✅ Présent' if TELEGRAM_BOT_TOKEN else '❌ MANQUANT'}")
if TELEGRAM_BOT_TOKEN:
    print(f"  → Longueur: {len(TELEGRAM_BOT_TOKEN)} caractères")

print(f"TELEGRAM_CHAT_ID: {'✅ Présent' if TELEGRAM_CHAT_ID else '❌ MANQUANT'}")
if TELEGRAM_CHAT_ID:
    print(f"  → Valeur: {TELEGRAM_CHAT_ID}")

print("=" * 60)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Vérification immédiate
if not all([FOOT_API, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("\n❌ ERREUR: Clés API manquantes!")
    print("Vérifiez que les secrets GitHub sont configurés:")
    print("1. Allez dans Settings > Secrets and variables > Actions")
    print("2. Vérifiez que ces secrets existent:")
    print("   - FOOT_API")
    print("   - TELEGRAM_BOT_TOKEN")
    print("   - TELEGRAM_CHAT_ID")
    print("3. Si vous êtes en local, créez un fichier .env")
    sys.exit(1)

# IDs des ligues
LEAGUES = {
    "ligue1": {"id": 13, "name": "Ligue 1", "emoji": "🇫🇷"},
    "premier-league": {"id": 8, "name": "Premier League", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "laliga": {"id": 12, "name": "LaLiga", "emoji": "🇪🇸"},
    "serie-a": {"id": 11, "name": "Serie A", "emoji": "🇮🇹"},
    "bundesliga": {"id": 9, "name": "Bundesliga", "emoji": "🇩🇪"},
    "champions-league": {"id": 3, "name": "Ligue des Champions", "emoji": "🏆"}
}

class SportMonksAPI:
    """Client pour l'API SportMonks"""
    
    BASE_URL = "https://api.sportmonks.com/v3/football"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        print(f"✅ Client SportMonks initialisé")
    
    def test_connection(self):
        """Test simple de connexion"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/fixtures/date/{datetime.now().strftime('%Y-%m-%d')}",
                params={"api_token": self.api_key, "per_page": 1},
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Connexion API SportMonks réussie")
                return True
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    def get_todays_fixtures(self):
        """Récupère les matchs du jour"""
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Récupération des matchs du {today}...")
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/fixtures/date/{today}",
                params={
                    "api_token": self.api_key,
                    "include": "localTeam;visitorTeam;league;tvStations",
                    "per_page": 50
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('data', [])
                print(f"✅ {len(fixtures)} matchs trouvés")
                return fixtures
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []

def send_telegram_message(message):
    """Envoie un message Telegram"""
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
        if response.status_code == 200:
            print("✅ Message Telegram envoyé")
            return True
        else:
            print(f"❌ Erreur Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")
        return False

def format_fixtures(fixtures):
    """Formate les matchs pour Telegram"""
    if not fixtures:
        return "📭 Aucun match trouvé aujourd'hui."
    
    message = "📅 *Matchs du jour*\n\n"
    
    for match in fixtures[:10]:  # Limiter à 10 matchs
        local = match.get('localTeam', {}).get('data', {}).get('name', '?')
        visitor = match.get('visitorTeam', {}).get('data', {}).get('name', '?')
        time = match.get('starting_at', '?')[11:16] if match.get('starting_at') else '?'
        
        message += f"⏱️ {time}\n"
        message += f"⚽ {local} vs {visitor}\n"
        
        # Chaînes TV
        tv = match.get('tvStations', {}).get('data', [])
        if tv:
            channels = [t.get('name', '') for t in tv[:2]]
            message += f"📺 {', '.join(channels)}\n"
        
        message += "\n"
    
    message += "#Football #Matchs"
    return message

def run():
    """Fonction principale"""
    print("\n🚀 Démarrage du Bot Sport...\n")
    
    # Initialiser API
    sport_api = SportMonksAPI(FOOT_API)
    
    # Tester connexion
    if not sport_api.test_connection():
        print("❌ Arrêt du bot - API non disponible")
        return
    
    # Récupérer les matchs
    fixtures = sport_api.get_todays_fixtures()
    
    # Formater et envoyer
    if fixtures:
        message = format_fixtures(fixtures)
        send_telegram_message(message)
    else:
        send_telegram_message("📭 Aucun match programmé aujourd'hui.")
    
    print("\n✅ Bot exécuté avec succès")

if __name__ == "__main__":
    run()
