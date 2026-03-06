import requests
import os
import logging
from datetime import datetime, timedelta
import sys

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TheSportsDBAPI:
    """Client pour TheSportsDB API (totalement gratuit, pas de clé requise)"""
    
    BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"
    
    def __init__(self):
        self.session = requests.Session()
        logging.info("✅ Client TheSportsDB initialisé")
    
    def get_events_by_date(self, date=None):
        """
        Récupère les événements (matchs) pour une date spécifique
        Format date: YYYY-MM-DD
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{self.BASE_URL}/eventsday.php"
        params = {'d': date}
        
        logging.info(f"📅 Récupération des matchs du {date}...")
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            events = data.get('events', [])
            if events:
                logging.info(f"✅ {len(events)} matchs trouvés")
            else:
                logging.info(f"ℹ️ Aucun match trouvé pour le {date}")
            
            return events
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Erreur réseau: {e}")
            return None
        except Exception as e:
            logging.error(f"❌ Erreur inattendue: {e}")
            return None
    
    def get_events_by_league(self, league_id, date=None):
        """
        Récupère les événements pour une ligue spécifique
        Utile pour filtrer par championnat
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{self.BASE_URL}/eventsday.php"
        params = {'d': date, 'l': league_id}
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        except:
            return []
    
    def get_next_events(self, team_id=None, league_id=None, days=5):
        """
        Récupère les prochains événements sur plusieurs jours
        """
        all_events = []
        today = datetime.now()
        
        for i in range(days):
            date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            events = self.get_events_by_date(date)
            
            if events:
                # Filtrer par équipe ou ligue si spécifié
                if team_id:
                    events = [e for e in events if 
                             e.get('idHomeTeam') == team_id or 
                             e.get('idAwayTeam') == team_id]
                if league_id:
                    events = [e for e in events if e.get('idLeague') == league_id]
                
                all_events.extend(events)
        
        return all_events
    
    def get_team_info(self, team_id):
        """Récupère les informations d'une équipe"""
        url = f"{self.BASE_URL}/lookupteam.php"
        params = {'id': team_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            teams = data.get('teams', [])
            return teams[0] if teams else None
        except:
            return None
    
    def get_league_info(self, league_id):
        """Récupère les informations d'une ligue"""
        url = f"{self.BASE_URL}/lookupleague.php"
        params = {'id': league_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            leagues = data.get('leagues', [])
            return leagues[0] if leagues else None
        except:
            return None
    
    def search_teams(self, team_name):
        """Recherche une équipe par nom"""
        url = f"{self.BASE_URL}/searchteams.php"
        params = {'t': team_name}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            return data.get('teams', [])
        except:
            return []


def format_events_for_telegram(events):
    """
    Formate les événements pour un message Telegram
    """
    if not events:
        return "📭 *Aucun match trouvé aujourd'hui*\n\nVérifiez plus tard ou explorez d'autres dates."
    
    # Trier les événements par date et heure
    try:
        events.sort(key=lambda x: (x.get('dateEvent', ''), x.get('strTime', '')))
    except:
        pass
    
    # Grouper par sport/ligue pour une meilleure lisibilité
    grouped_events = {}
    for event in events:
        sport = event.get('strSport', 'Football')
        league = event.get('strLeague', 'Ligue inconnue')
        key = f"{sport} - {league}"
        
        if key not in grouped_events:
            grouped_events[key] = []
        grouped_events[key].append(event)
    
    # Construction du message
    total_events = len(events)
    message = f"📅 *MATCHS DU JOUR* ({total_events} événements)\n\n"
    
    for category, category_events in grouped_events.items():
        message += f"🏆 *{category}*\n"
        message += "━" * 30 + "\n"
        
        for event in category_events:
            # Informations de base
            home_team = event.get('strHomeTeam', '?')
            away_team = event.get('strAwayTeam', '?')
            
            # Heure du match
            event_time = event.get('strTime', 'Horaire inconnu')
            if event_time and event_time != 'Horaire inconnu':
                # Formater l'heure (enlever les secondes si présentes)
                if len(event_time) > 5:
                    event_time = event_time[:5]
            
            # Date (au cas où on ait plusieurs dates)
            event_date = event.get('dateEvent', '')
            date_display = f" ({event_date})" if event_date else ""
            
            # Score ou état du match
            status = event.get('strStatus', '')
            if status and status.lower() not in ['not started', '']:
                home_score = event.get('intHomeScore', '')
                away_score = event.get('intAwayScore', '')
                if home_score and away_score:
                    message += f"⚽ *{home_team} {home_score} - {away_score} {away_team}*\n"
                    message += f"📌 {status}\n"
                else:
                    message += f"⚽ {home_team} vs {away_team}\n"
                    message += f"📌 {status}\n"
            else:
                message += f"⏱️ {event_time}\n"
                message += f"⚽ {home_team} vs {away_team}\n"
            
            # Informations supplémentaires (optionnelles)
            round_info = event.get('intRound', '')
            if round_info:
                message += f"📋 Journée {round_info}\n"
            
            # Stade (si disponible)
            stadium = event.get('strStadium', '')
            if stadium and stadium != '?':
                message += f"🏟️ {stadium}\n"
            
            message += "\n"
        
        message += "\n"
    
    # Ajouter un résumé et des hashtags
    message += "━" * 35 + "\n"
    message += f"📊 *Résumé* : {total_events} matchs programmés\n"
    message += "📌 *Légende* : ⏱️ Heure | ⚽ Match | 🏟️ Stade\n\n"
    message += "#Football #TheSportsDB #MatchsDuJour"
    
    return message


def format_events_simple(events):
    """
    Version ultra-simple pour les SMS ou notifications courtes
    """
    if not events:
        return "Aucun match aujourd'hui"
    
    lines = ["📅 Matchs du jour:"]
    for event in events[:5]:  # Max 5 matchs
        home = event.get('strHomeTeam', '?')
        away = event.get('strAwayTeam', '?')
        time = event.get('strTime', '?')[:5]
        lines.append(f"• {time} - {home} vs {away}")
    
    if len(events) > 5:
        lines.append(f"... et {len(events)-5} autres")
    
    return "\n".join(lines)


def send_telegram_message(message):
    """
    Envoie un message sur Telegram
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("❌ Configuration Telegram manquante")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Vérifier la longueur du message (limite 4096)
    if len(message) > 4000:
        # Envoyer en plusieurs parties
        parts = []
        current_part = ""
        
        for line in message.split('\n'):
            if len(current_part) + len(line) + 1 < 4000:
                current_part += line + '\n'
            else:
                parts.append(current_part)
                current_part = line + '\n'
        
        if current_part:
            parts.append(current_part)
        
        success = True
        for i, part in enumerate(parts):
            part_num = i + 1
            part_header = f"*Partie {part_num}/{len(parts)}*\n\n"
            if not _send_single_message(part_header + part):
                success = False
        
        return success
    else:
        return _send_single_message(message)


def _send_single_message(text):
    """
    Envoie un seul message Telegram
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        response = requests.post(
            url,
            data={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            logging.error(f"❌ Erreur Telegram: {response.status_code}")
            logging.error(f"Réponse: {response.text}")
            
            # Tentative sans Markdown
            clean_text = text.replace('*', '').replace('_', '').replace('`', '')
            response2 = requests.post(
                url,
                data={
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': clean_text,
                    'disable_web_page_preview': True
                },
                timeout=10
            )
            return response2.status_code == 200
            
    except Exception as e:
        logging.error(f"❌ Erreur envoi: {e}")
        return False


def test_connection():
    """
    Teste la connexion à TheSportsDB
    """
    try:
        response = requests.get(
            f"{TheSportsDBAPI.BASE_URL}/eventsday.php",
            params={'d': datetime.now().strftime("%Y-%m-%d")},
            timeout=10
        )
        if response.status_code == 200:
            logging.info("✅ Connexion TheSportsDB réussie")
            return True
        else:
            logging.error(f"❌ Erreur TheSportsDB: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Erreur connexion: {e}")
        return False


def run():
    """
    Fonction principale
    """
    print("\n" + "="*60)
    print("🚀 BOT MATCHS DU JOUR - TheSportsDB")
    print("="*60 + "\n")
    
    # Vérification configuration
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("❌ Clés Telegram manquantes")
        print("\nConfiguration requise:")
        print("  TELEGRAM_BOT_TOKEN: votre_token")
        print("  TELEGRAM_CHAT_ID: votre_chat_id")
        return
    
    logging.info("✅ Configuration Telegram validée")
    
    # Test connexion API
    if not test_connection():
        logging.error("❌ Impossible de se connecter à TheSportsDB")
        return
    
    # Initialisation API
    api = TheSportsDBAPI()
    
    # Récupérer les matchs du jour
    today = datetime.now().strftime("%Y-%m-%d")
    events = api.get_events_by_date(today)
    
    # Si pas de matchs aujourd'hui, chercher dans les prochains jours
    if not events:
        logging.info("🔍 Aucun match aujourd'hui, recherche dans les 5 prochains jours...")
        events = api.get_next_events(days=5)
        
        if events:
            message = "📅 *PROCHAINS MATCHS*\n\n"
            message += format_events_for_telegram(events)
        else:
            message = "📭 *Aucun match trouvé dans les 5 prochains jours*"
    else:
        message = format_events_for_telegram(events)
    
    # Afficher un aperçu
    print("\n" + "="*40)
    print("📝 APERÇU DU MESSAGE")
    print("="*40)
    print(message[:500] + "..." if len(message) > 500 else message)
    
    # Envoyer sur Telegram
    print("\n📤 ENVOI SUR TELEGRAM...")
    if send_telegram_message(message):
        logging.info("✅ Message envoyé avec succès!")
    else:
        logging.error("❌ Échec de l'envoi")
    
    print("\n" + "="*60)
    print("✅ BOT TERMINÉ")
    print("="*60 + "\n")


if __name__ == "__main__":
    run()
