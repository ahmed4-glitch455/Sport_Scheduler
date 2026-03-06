import requests
import os
import logging
from datetime import datetime
import json

# --- CONFIGURATION ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RapidFootballAPI:
    """Client pour l'API Football gratuite sur RapidAPI"""
    
    # Matchs prédéfinis qui fonctionnent (vous pouvez en ajouter d'autres)
    WORKING_MATCHES = [
        {"id": "12650707", "home": "Équipe A", "away": "Équipe B", "league": "Championnat"},
        # Ajoutez d'autres IDs de matchs qui fonctionnent ici
    ]
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "free-football-api-data.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': self.host
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_match_details(self, match_id):
        """Récupère les détails d'un match spécifique (le seul endpoint qui fonctionne)"""
        url = f"https://{self.host}/football-event-statistics"
        params = {"eventid": match_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Erreur {response.status_code} pour match {match_id}")
                return None
        except Exception as e:
            logging.error(f"Erreur réseau: {e}")
            return None
    
    def get_multiple_matches(self, match_ids):
        """Récupère plusieurs matchs à la fois"""
        matches = []
        for match_id in match_ids:
            data = self.get_match_details(match_id)
            if data and data.get('status') == 'success':
                matches.append(data)
        return matches
    
    def get_leagues(self):
        """Récupère la liste des ligues (fonctionne)"""
        url = f"https://{self.host}/football-leagues"
        try:
            response = self.session.get(url, timeout=10)
            return response.json() if response.status_code == 200 else None
        except:
            return None

def format_match_message(match_data, match_info):
    """Formate les données d'un match pour Telegram"""
    if not match_data or match_data.get('status') != 'success':
        return None
    
    # Informations de base
    home = match_info.get('home', '?')
    away = match_info.get('away', '?')
    league = match_info.get('league', 'Match')
    
    message = f"⚽ *{league}*\n\n"
    message += f"🏠 *{home}* vs *{away}*\n"
    message += "━" * 30 + "\n"
    
    # Extraire les statistiques si disponibles
    response = match_data.get('response', {})
    
    # Statistiques de match
    stats = response.get('statistics', {})
    if stats:
        message += "\n📊 *Statistiques:*\n"
        
        # Possession
        if 'possession' in stats:
            message += f"• Possession: {stats['possession']}\n"
        
        # Tirs
        if 'shots' in stats:
            message += f"• Tirs: {stats['shots']}\n"
        
        # Corners
        if 'corners' in stats:
            message += f"• Corners: {stats['corners']}\n"
    
    # Ajouter l'heure si disponible
    current_time = datetime.now().strftime("%H:%M")
    message += f"\n⏱️ Mis à jour à {current_time}"
    
    return message

def format_matches_list(matches_data):
    """Formate une liste de matchs"""
    if not matches_data:
        return None
    
    message = "📅 *Matchs disponibles*\n\n"
    
    for i, match_data in enumerate(matches_data[:5]):
        if i < len(RapidFootballAPI.WORKING_MATCHES):
            match_info = RapidFootballAPI.WORKING_MATCHES[i]
            home = match_info['home']
            away = match_info['away']
            league = match_info['league']
            
            message += f"🏆 {league}\n"
            message += f"⚽ {home} vs {away}\n"
            
            # Ajouter le score si disponible
            response = match_data.get('response', {})
            if response:
                score = response.get('score', {})
                if score:
                    message += f"📊 Score: {score}\n"
            
            message += "\n"
    
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
            logging.info("✅ Message Telegram envoyé")
            return True
        else:
            logging.error(f"❌ Erreur Telegram: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Erreur envoi: {e}")
        return False

def discover_working_matches(api, start_id=12650700, end_id=12650720):
    """Découvre quels IDs de matchs fonctionnent"""
    working = []
    print("\n🔍 Recherche des IDs de matchs valides...")
    
    for match_id in range(start_id, end_id):
        print(f"Test ID {match_id}...", end="")
        data = api.get_match_details(str(match_id))
        if data and data.get('status') == 'success':
            working.append(str(match_id))
            print(f" ✅")
        else:
            print(" ❌")
    
    print(f"\n✅ IDs valides trouvés: {', '.join(working)}")
    return working

def run():
    """Fonction principale"""
    print("\n" + "="*50)
    print("🚀 Démarrage du Bot Football (RapidAPI)")
    print("="*50 + "\n")
    
    # Vérification des clés
    if not all([RAPIDAPI_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logging.error("❌ Clés API manquantes")
        return
    
    # Initialisation
    api = RapidFootballAPI(RAPIDAPI_KEY)
    
    # Récupérer les matchs qui fonctionnent
    matches_data = []
    for match_info in RapidFootballAPI.WORKING_MATCHES:
        data = api.get_match_details(match_info['id'])
        if data and data.get('status') == 'success':
            matches_data.append(data)
            logging.info(f"✅ Match {match_info['home']} vs {match_info['away']} récupéré")
    
    if matches_data:
        # Si plusieurs matchs, envoyer la liste
        if len(matches_data) > 1:
            message = format_matches_list(matches_data)
        else:
            # Sinon, envoyer le détail du premier match
            message = format_match_message(matches_data[0], RapidFootballAPI.WORKING_MATCHES[0])
        
        if message:
            send_telegram_message(message)
        else:
            send_telegram_message("📭 Impossible de formater les données")
    else:
        # Fallback: message informatif
        message = """
📭 *Aucun match disponible*

L'API fonctionne mais nécessite des IDs de matchs valides.
Pour ajouter des matchs:

1. Trouvez des IDs valides avec la fonction discover_working_matches()
2. Ajoutez-les dans WORKING_MATCHES

🔍 Exemple: 12650707 fonctionne
        """
        send_telegram_message(message)
    
    print("\n" + "="*50)
    print("✅ Bot exécuté avec succès")
    print("="*50 + "\n")

# Pour découvrir plus d'IDs de matchs, décommentez:
# if __name__ == "__main__":
#     api = RapidFootballAPI(RAPIDAPI_KEY)
#     discover_working_matches(api, 12650700, 12650710)

if __name__ == "__main__":
    run()
