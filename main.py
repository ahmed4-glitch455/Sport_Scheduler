import http.client
import json
import os
import logging
from datetime import datetime, timedelta

# --- CONFIGURATION ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "aae4f48e19msh089011944c89f58p11391cjsne9ade8487bd1")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FreeFootballAPI:
    """Client pour free-football-api-data.p.rapidapi.com"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.host = "free-football-api-data.p.rapidapi.com"
    
    def get_scheduled_events(self, date=None):
        """Récupère les matchs programmés pour une date"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conn = http.client.HTTPSConnection(self.host)
        headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': self.host
        }
        
        endpoint = f"/football-scheduled-events?date={date}"
        logging.info(f"📅 Récupération des matchs du {date}...")
        
        try:
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                logging.error(f"Erreur {res.status}: {data.decode('utf-8')}")
                return None
        except Exception as e:
            logging.error(f"Erreur connexion: {e}")
            return None
        finally:
            conn.close()
    
    def get_multiple_dates(self, days=7):
        """Récupère les matchs pour plusieurs jours"""
        all_matches = []
        today = datetime.now()
        
        for i in range(days):
            date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            events = self.get_scheduled_events(date)
            
            if events and events.get('events'):
                all_matches.extend(events['events'])
                logging.info(f"✅ {date}: {len(events['events'])} matchs")
            else:
                logging.info(f"ℹ️ {date}: 0 match")
        
        return all_matches

def format_events(events):
    """Formate les matchs pour Telegram"""
    if not events:
        return "📭 Aucun match programmé aujourd'hui."
    
    # Grouper par ligue
    leagues = {}
    for event in events:
        league = event.get('league', 'Ligue inconnue')
        if league not in leagues:
            leagues[league] = []
        leagues[league].append(event)
    
    message = "📅 *MATCHS PROGRAMMÉS*\n\n"
    
    for league_name, matches in leagues.items():
        message += f"🏆 *{league_name}*\n"
        message += "━" * 25 + "\n"
        
        for match in matches[:10]:  # Max 10 par ligue
            home = match.get('homeTeam', '?')
            away = match.get('awayTeam', '?')
            time = match.get('time', '?')
            date = match.get('date', '')
            
            # Format de l'heure
            if time and time != '?':
                time_display = time
            else:
                time_display = 'Horaire inconnu'
            
            message += f"⏱️ {time_display}\n"
            message += f"⚽ {home} vs {away}\n\n"
        
        message += "\n"
    
    # Ajouter un résumé
    total = len(events)
    message += f"━━━━━━━━━━━━━━━━━━\n"
    message += f"📊 Total: {total} matchs programmés\n"
    message += "#Football #MatchsProgrammés"
    
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
    except Exception as e:
        logging.error(f"Erreur Telegram: {e}")
        return False

def test_endpoint():
    """Test simple de l'endpoint"""
    print("\n🔍 TEST DE L'ENDPOINT")
    print("="*40)
    
    api = FreeFootballAPI(RAPIDAPI_KEY)
    
    # Test avec aujourd'hui
    today = datetime.now().strftime("%Y-%m-%d")
    data = api.get_scheduled_events(today)
    
    if data:
        print(f"✅ Connexion réussie!")
        print(f"📊 Données reçues: {json.dumps(data, indent=2)[:500]}...")
        return True
    else:
        print("❌ Échec connexion")
        return False

def run():
    """Fonction principale"""
    print("\n" + "="*50)
    print("⚽ BOT MATCHS PROGRAMMÉS")
    print("="*50 + "\n")
    
    # Test de connexion
    if not test_endpoint():
        print("\n❌ Arrêt du bot - API inaccessible")
        return
    
    # Initialisation
    api = FreeFootballAPI(RAPIDAPI_KEY)
    
    # Récupérer les matchs du jour
    today = datetime.now().strftime("%Y-%m-%d")
    events_data = api.get_scheduled_events(today)
    
    if events_data and events_data.get('events'):
        events = events_data['events']
        message = format_events(events)
        print(f"\n✅ {len(events)} matchs trouvés")
    else:
        # Si pas de matchs aujourd'hui, chercher dans les prochains jours
        print("\n🔍 Aucun match aujourd'hui, recherche dans les prochains jours...")
        all_events = api.get_multiple_dates(days=5)
        
        if all_events:
            message = format_events(all_events)
            message = "📅 *PROCHAINS MATCHS*\n\n" + message
            print(f"\n✅ {len(all_events)} matchs trouvés dans les 5 prochains jours")
        else:
            message = "📭 Aucun match programmé dans les 5 prochains jours."
            print("\n❌ Aucun match trouvé")
    
    # Envoyer sur Telegram
    if send_telegram_message(message):
        print("\n✅ Message envoyé sur Telegram")
    else:
        print("\n❌ Erreur envoi Telegram")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    # Nécessaire pour les requêtes HTTP
    import requests
    run()
