import requests
import os
import logging
import sys
from datetime import datetime, timedelta

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- DIAGNOSTIC ---
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
    print(f"  → LongeUr: {len(TELEGRAM_BOT_TOKEN)} caractères")

print(f"TELEGRAM_CHAT_ID: {'✅ Présent' if TELEGRAM_CHAT_ID else '❌ MANQUANT'}")
print("=" * 60)

# Configuration des ligues (IDs SportMonks v3)
LEAGUES = {
    "ligue1": {"id": 13, "name": "Ligue 1", "country": "France", "emoji": "🇫🇷"},
    "premier-league": {"id": 8, "name": "Premier League", "country": "Angleterre", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "laliga": {"id": 12, "name": "LaLiga", "country": "Espagne", "emoji": "🇪🇸"},
    "serie-a": {"id": 11, "name": "Serie A", "country": "Italie", "emoji": "🇮🇹"},
    "bundesliga": {"id": 9, "name": "Bundesliga", "country": "Allemagne", "emoji": "🇩🇪"},
    "champions-league": {"id": 3, "name": "Ligue des Champions", "country": "Europe", "emoji": "🏆"}
}

class SportMonksAPI:
    """Client pour l'API SportMonks v3"""
    
    # Différents endpoints à tester
    ENDPOINTS = {
        "fixtures": "/fixtures/date/{date}",
        "livescores": "/livescores",
        "leagues": "/leagues",
        "seasons": "/seasons"
    }
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.sportmonks.com/v3/football"
        self.session = requests.Session()
        print(f"✅ Client SportMonks initialisé")
    
    def test_endpoints(self):
        """Teste différents endpoints pour trouver celui qui fonctionne"""
        print("\n🔍 Test des endpoints SportMonks...")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Tester l'endpoint fixtures
        url = f"{self.base_url}/fixtures/date/{today}"
        params = {"api_token": self.api_key, "per_page": 1}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            print(f"📌 Endpoint fixtures/date: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Endpoint fixtures fonctionnel")
                return "fixtures"
        except:
            pass
        
        # Tester l'endpoint livescores
        url = f"{self.base_url}/livescores"
        params = {"api_token": self.api_key, "per_page": 1}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            print(f"📌 Endpoint livescores: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Endpoint livescores fonctionnel")
                return "livescores"
        except:
            pass
        
        print("⚠️ Aucun endpoint standard ne fonctionne")
        return None
    
    def get_todays_fixtures(self):
        """Récupère les matchs du jour avec gestion d'erreur"""
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        print(f"📅 Recherche des matchs...")
        
        # Essayer plusieurs formats de date
        for date in [today, tomorrow]:
            # Essayer différents endpoints
            endpoints = [
                f"{self.base_url}/fixtures/date/{date}",
                f"{self.base_url}/fixtures",
                f"{self.base_url}/fixtures/between/{date}/{date}"
            ]
            
            for url in endpoints:
                params = {
                    "api_token": self.api_key,
                    "include": "localTeam;visitorTeam;league;tvStations",
                    "per_page": 20
                }
                
                # Ajouter le paramètre date pour l'endpoint fixtures simple
                if "between" not in url and "date" not in url:
                    params["filters"] = f"starting_at_date:{date}"
                
                try:
                    print(f"🔄 Test: {url}")
                    response = self.session.get(url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        fixtures = data.get('data', [])
                        
                        # Vérifier si on a des résultats
                        if fixtures:
                            print(f"✅ {len(fixtures)} matchs trouvés")
                            return fixtures
                        else:
                            print(f"⚠️ 0 matchs trouvés")
                    
                except Exception as e:
                    print(f"❌ Erreur: {e}")
                    continue
        
        print("❌ Aucun match trouvé")
        return []
    
    def get_leagues(self):
        """Récupère la liste des ligues disponibles"""
        url = f"{self.base_url}/leagues"
        params = {
            "api_token": self.api_key,
            "include": "country",
            "per_page": 50
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
        except:
            pass
        return []

def format_fixtures(fixtures):
    """Formate les matchs pour Telegram"""
    if not fixtures:
        return "📭 Aucun match trouvé aujourd'hui.\n\nPeut-être qu'aucun match n'est programmé ou que l'API est en maintenance."
    
    message = "📅 *Matchs du jour*\n\n"
    
    for match in fixtures[:10]:  # Limiter à 10 matchs
        # Équipes
        home = match.get('localTeam', {}).get('data', {}).get('name', '?')
        away = match.get('visitorTeam', {}).get('data', {}).get('name', '?')
        
        # Heure du match
        starting_at = match.get('starting_at', '')
        if starting_at:
            time = starting_at[11:16] if len(starting_at) > 16 else '?'
        else:
            time = '?'
        
        # Ligue
        league = match.get('league', {}).get('data', {}).get('name', '')
        
        message += f"⏱️ {time}\n"
        if league:
            message += f"🏆 {league}\n"
        message += f"⚽ {home} vs {away}\n"
        
        # Chaînes TV
        tv = match.get('tvStations', {}).get('data', [])
        if tv:
            channels = [t.get('name', '') for t in tv[:3]]
            message += f"📺 {', '.join(channels)}\n"
        
        message += "\n"
    
    message += "#Football #Matchs #Sport"
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
        
        if response.status_code == 200:
            print("✅ Message Telegram envoyé")
            return True
        else:
            print(f"❌ Erreur Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")
        return False

def debug_api_info():
    """Affiche des infos de débogage sur l'API"""
    print("\n🔧 INFORMATIONS DE DÉBOGAGE")
    print("=" * 40)
    
    # Version de l'API
    print("📌 API Version: v3")
    
    # Clé API
    print(f"📌 Clé API: {FOOT_API[:5]}...{FOOT_API[-5:] if FOOT_API else ''}")
    
    # Date actuelle
    now = datetime.now()
    print(f"📌 Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📌 Jour de semaine: {now.strftime('%A')}")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    print("1. Vérifiez que votre clé API est active sur sportmonks.com")
    print("2. Consultez la documentation: https://docs.sportmonks.com/football")
    print("3. Essayez l'endpoint de test: curl -X GET \"https://api.sportmonks.com/v3/football/fixtures?api_token=VOTRE_CLE&per_page=1\"")
    print("=" * 40)

def run():
    """Fonction principale"""
    print("\n🚀 Démarrage du Bot Sport...\n")
    
    # Vérifications de base
    if not all([FOOT_API, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("❌ Configuration incomplète")
        return
    
    # Initialisation API
    sport_api = SportMonksAPI(FOOT_API)
    
    # Test des endpoints
    working_endpoint = sport_api.test_endpoints()
    
    if not working_endpoint:
        debug_api_info()
        send_telegram_message("⚠️ *Problème avec l'API SportMonks*\n\nImpossible de se connecter. Vérifiez votre clé API.")
        return
    
    # Récupérer les matchs
    fixtures = sport_api.get_todays_fixtures()
    
    # Formater et envoyer
    message = format_fixtures(fixtures)
    send_telegram_message(message)
    
    # Afficher un résumé
    print(f"\n📊 Résumé: {len(fixtures)} matchs trouvés")
    
    if not fixtures:
        # Suggestions pour le débogage
        print("\n💡 Suggestions:")
        print("1. Vérifiez qu'il y a des matchs aujourd'hui")
        print("2. Testez votre clé sur le site SportMonks")
        print("3. Vérifiez les IDs des ligues")
    
    print("\n✅ Bot exécuté avec succès")

if __name__ == "__main__":
    run()
