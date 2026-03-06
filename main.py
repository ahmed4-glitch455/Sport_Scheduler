import requests
import os
import logging
from datetime import datetime
import json

# --- CONFIGURATION ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "aae4f48e19msh089011944c89f58p11391cjsne9ade8487bd1")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RapidFootballAPI:
    """Client pour l'API Football gratuite sur RapidAPI"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "free-football-api-data.p.rapidapi.com"
        self.base_url = f"https://{self.host}"
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': self.host
        }
    
    def get_live_matches(self):
        """Récupère les matchs en direct"""
        url = f"{self.base_url}/football-live-scores"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erreur live matches: {e}")
            return None
    
    def get_todays_matches(self, date=None):
        """Récupère les matchs du jour"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Note: L'endpoint exact dépend de l'API
        # Essayez différents endpoints selon la documentation
        endpoints = [
            f"/football-today-matches?date={date}",
            f"/football-fixtures?date={date}",
            f"/football-schedule?date={date}"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                logging.info(f"Tentative: {endpoint}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data and data.get('data') or data.get('matches'):
                        return data
            except:
                continue
        
        return None
    
    def get_match_details(self, match_id):
        """Récupère les détails d'un match spécifique"""
        url = f"{self.base_url}/football-event-statistics"
        params = {"eventid": match_id}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erreur match details {match_id}: {e}")
            return None
    
    def search_matches(self, query):
        """Recherche des matchs par équipe/ligue"""
        url = f"{self.base_url}/football-search"
        params = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            return response.json()
        except:
            return None
    
    def get_leagues(self):
        """Récupère la liste des ligues disponibles"""
        url = f"{self.base_url}/football-leagues"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.json()
        except:
            return None

def format_match_message(match_data):
    """Formate les données d'un match pour Telegram"""
    if not match_data:
        return "📭 Aucune donnée disponible"
    
    message = "⚽ *Match Info*\n\n"
    
    # Adapter selon la structure de votre API
    if isinstance(match_data, dict):
        # Exemple de formatage
        home = match_data.get('homeTeam', {}).get('name', '?')
        away = match_data.get('awayTeam', {}).get('name', '?')
        score = match_data.get('score', '? - ?')
        status = match_data.get('status', '?')
        time = match_data.get('time', '?')
        
        message += f"🏆 {home} vs {away}\n"
        message += f"⚽ Score: {score}\n"
        message += f"⏱️ Status: {status} {time}\n"
        
        # Chaînes TV (si disponibles)
        tv = match_data.get('tvStations', [])
        if tv:
            message += f"📺 {', '.join(tv)}\n"
    
    return message

def format_matches_list(matches):
    """Formate une liste de matchs"""
    if not matches or not isinstance(matches, list):
        return "📭 Aucun match trouvé"
    
    message = "📅 *Matchs du jour*\n\n"
    
    for match in matches[:10]:  # Limiter à 10
        home = match.get('homeTeam', {}).get('name', '?')
        away = match.get('awayTeam', {}).get('name', '?')
        time = match.get('time', '?')
        league = match.get('league', {}).get('name', '')
        
        if league:
            message += f"🏆 {league}\n"
        message += f"⏱️ {time} - {home} vs {away}\n\n"
    
    return message

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
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Erreur Telegram: {e}")
        return False

def test_rapidapi_connection(api):
    """Teste la connexion à RapidAPI"""
    print("\n🔍 Test de connexion RapidAPI...")
    
    # Test 1: Récupérer les ligues
    leagues = api.get_leagues()
    if leagues:
        print("✅ Endpoint /leagues fonctionne")
    else:
        print("❌ Endpoint /leagues échoué")
    
    # Test 2: Récupérer les matchs du jour
    today_matches = api.get_todays_matches()
    if today_matches:
        print("✅ Endpoint /matches fonctionne")
    else:
        print("❌ Endpoint /matches échoué")
    
    # Test 3: Votre endpoint spécifique
    match_details = api.get_match_details("12650707")
    if match_details:
        print("✅ Endpoint /event-statistics fonctionne")
        print(f"📊 Données reçues: {json.dumps(match_details, indent=2)[:200]}...")
    else:
        print("❌ Endpoint /event-statistics échoué")

def run():
    """Fonction principale"""
    print("\n🚀 Démarrage du Bot Football (RapidAPI)...\n")
    
    # Initialisation
    api = RapidFootballAPI(RAPIDAPI_KEY)
    
    # Test de connexion
    test_rapidapi_connection(api)
    
    # Récupérer les matchs du jour
    print("\n📅 Recherche des matchs du jour...")
    matches = api.get_todays_matches()
    
    if matches:
        message = format_matches_list(matches.get('data', []))
    else:
        # Fallback: utiliser votre endpoint spécifique
        print("⚠️ Utilisation de l'endpoint de fallback...")
        match = api.get_match_details("12650707")
        if match:
            message = format_match_message(match)
        else:
            message = "📭 Aucun match trouvé"
    
    # Envoyer sur Telegram
    if send_telegram_message(message):
        print("✅ Message envoyé!")
    else:
        print("❌ Échec envoi")

if __name__ == "__main__":
    run()
