import requests
import os
import logging
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FootballOnlyAPI:
    """
    Client TheSportsDB qui ne garde que le football
    """
    
    # Liste des sports à GARDER (tout le reste est ignoré)
    ALLOWED_SPORTS = [
        'Soccer',           # Football
        'Football',         # Variante
        'Soccer - France',  # Football français
        'Soccer - England', # Football anglais
        'Soccer - Spain',   # Football espagnol
        'Soccer - Italy',   # Football italien
        'Soccer - Germany', # Football allemand
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.thesportsdb.com/api/v1/json/3"
        logging.info("✅ Client FootballOnly initialisé")
    
    def get_todays_football(self):
        """
        Récupère UNIQUEMENT les matchs de football du jour
        """
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{self.base_url}/eventsday.php"
        params = {'d': today}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            all_events = data.get('events', [])
            
            # Filtrer pour ne garder que le football
            football_events = []
            for event in all_events:
                sport = event.get('strSport', '')
                
                # Vérifier si c'est du football
                if any(allowed.lower() in sport.lower() for allowed in self.ALLOWED_SPORTS):
                    football_events.append(event)
                    logging.info(f"⚽ Match trouvé: {event.get('strEvent', '?')}")
                else:
                    logging.info(f"🏈 Ignoré (pas football): {event.get('strSport', '?')} - {event.get('strEvent', '?')}")
            
            return football_events
            
        except Exception as e:
            logging.error(f"❌ Erreur: {e}")
            return []
    
    def get_next_football_days(self, days=5):
        """
        Cherche les prochains jours où il y a du football
        """
        football_days = []
        today = datetime.now()
        
        for i in range(days):
            date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            events = self.get_football_by_date(date)
            if events:
                football_days.append({
                    'date': date,
                    'count': len(events),
                    'events': events
                })
        
        return football_days
    
    def get_football_by_date(self, date):
        """
        Récupère le football pour une date spécifique
        """
        url = f"{self.base_url}/eventsday.php"
        params = {'d': date}
        
        try:
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            all_events = data.get('events', [])
            
            return [e for e in all_events 
                   if any(allowed.lower() in e.get('strSport', '').lower() 
                         for allowed in self.ALLOWED_SPORTS)]
        except:
            return []

def format_football_matches(events, date):
    """
    Formate les matchs de football pour Telegram
    """
    if not events:
        return None
    
    # Grouper par ligue
    leagues = {}
    for event in events:
        league = event.get('strLeague', 'Ligue inconnue')
        if league not in leagues:
            leagues[league] = []
        leagues[league].append(event)
    
    # Construire le message
    date_display = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    message = f"📅 *MATCHS DE FOOTBALL - {date_display}*\n\n"
    
    for league_name, league_events in leagues.items():
        message += f"🏆 *{league_name}*\n"
        message += "━" * 25 + "\n"
        
        for event in league_events:
            home = event.get('strHomeTeam', '?')
            away = event.get('strAwayTeam', '?')
            
            # Extraire l'heure
            time_str = event.get('strTime', '?')
            if time_str and time_str != '?' and len(time_str) > 5:
                time_str = time_str[:5]
            
            message += f"⏱️ {time_str}\n"
            message += f"⚽ {home} vs {away}\n\n"
        
        message += "\n"
    
    total = len(events)
    message += f"━━━━━━━━━━━━━━━━━━\n"
    message += f"📊 Total: {total} matchs de football\n"
    message += "#Football #MatchsDuJour"
    
    return message

def format_no_matches_message():
    """
    Message sympa quand il n'y a pas de football
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    return f"""
📅 *{today} - Pas de football aujourd'hui* 😴

Les championnats européens font une pause.

📆 *À venir:*
• Week-end: reprise des championnats
• Ligue des Champions: mardi/mercredi

🎯 *Prochains matchs:*
Consultez le bot demain pour le programme !

━━━━━━━━━━━━━━━━━━
🔍 *Astuce:* Les matchs NCAA (basketball US) sont ignorés automatiquement.
#Football #Repos #ProchainsMatchs
"""

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
        logging.error(f"❌ Erreur Telegram: {e}")
        return False

def run():
    """Fonction principale"""
    print("\n" + "="*60)
    print("⚽ BOT FOOTBALL - FILTRE NCAA OFF")
    print("="*60 + "\n")
    
    # Vérification configuration
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Configuration Telegram manquante")
        return
    
    # Initialisation
    api = FootballOnlyAPI()
    
    # Récupérer les matchs de football du jour
    today = datetime.now().strftime("%Y-%m-%d")
    football_matches = api.get_todays_football()
    
    if football_matches:
        # Des matchs de football aujourd'hui !
        message = format_football_matches(football_matches, today)
        print(f"✅ {len(football_matches)} matchs de football trouvés!")
    else:
        # Pas de football aujourd'hui
        print("ℹ️ Aucun match de football aujourd'hui")
        
        # Chercher les prochains jours
        print("🔍 Recherche des prochains matchs de football...")
        next_days = api.get_next_football_days(days=7)
        
        if next_days:
            # Afficher les prochains jours avec football
            schedule = "\n".join([
                f"📆 {day['date']}: {day['count']} matchs"
                for day in next_days[:3]
            ])
            
            message = f"""
📅 *Pas de football aujourd'hui*

🎯 *Prochains matchs:*
{schedule}

🔄 Revenez demain pour le programme complet !
#Football #ProchainsMatchs
"""
        else:
            # Vraiment aucun match nulle part
            message = format_no_matches_message()
    
    # Envoyer sur Telegram
    if send_telegram_message(message):
        print("✅ Message envoyé sur Telegram")
    else:
        print("❌ Échec envoi")

if __name__ == "__main__":
    run()
