import requests
import os
import logging
from datetime import datetime, timedelta
import json

# --- CONFIGURATION ---
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FootballDataAPI:
    """Client pour football-data.org API v4"""
    
    BASE_URL = "https://api.football-data.org/v4"
    
    # Mapping des compétitions majeures avec leurs codes
    COMPETITIONS = {
        'PL': 'Premier League',
        'PD': 'LaLiga',
        'SA': 'Serie A',
        'BL1': 'Bundesliga',
        'FL1': 'Ligue 1',
        'DED': 'Eredivisie',
        'PPL': 'Primeira Liga',
        'CL': 'Champions League',
        'EL': 'Europa League',
        'EC': 'Euro Championship'
    }
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'X-Auth-Token': api_key}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        logging.info("✅ Client football-data.org initialisé")
    
    def get_today_matches(self, date=None):
        """
        Récupère les matchs du jour
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{self.BASE_URL}/matches"
        params = {
            'date': date,
            'status': 'SCHEDULED'  # Uniquement les matchs programmés
        }
        
        logging.info(f"📅 Récupération des matchs du {date}...")
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # Vérifier le quota
            remaining = response.headers.get('X-Requests-Available-Minute', '?')
            logging.info(f"📊 Requêtes restantes: {remaining}")
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                logging.info(f"✅ {len(matches)} matchs trouvés")
                return matches
            elif response.status_code == 429:
                logging.error("❌ Quota dépassé pour cette minute")
                return []
            else:
                logging.error(f"❌ Erreur {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"❌ Erreur: {e}")
            return []
    
    def get_matches_by_competition(self, competition_code, date_from=None, date_to=None):
        """
        Récupère les matchs d'une compétition spécifique
        """
        url = f"{self.BASE_URL}/competitions/{competition_code}/matches"
        params = {}
        
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('matches', [])
            return []
        except:
            return []
    
    def get_live_matches(self):
        """
        Récupère les matchs en direct
        """
        url = f"{self.BASE_URL}/matches"
        params = {'status': 'LIVE'}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('matches', [])
            return []
        except:
            return []
    
    def check_quota(self):
        """
        Vérifie le quota restant
        """
        url = f"{self.BASE_URL}/matches"
        try:
            response = self.session.get(url, params={'date': datetime.now().strftime("%Y-%m-%d")}, timeout=5)
            remaining = response.headers.get('X-Requests-Available-Minute', 'Inconnu')
            return remaining
        except:
            return "Inconnu"


def format_matches_for_telegram(matches):
    """
    Formate les matchs pour Telegram
    """
    if not matches:
        return "📭 *Aucun match programmé aujourd'hui*\n\nLes championnats européens sont peut-être en pause."
    
    # Grouper par compétition
    competitions = {}
    for match in matches:
        comp_name = match['competition']['name']
        if comp_name not in competitions:
            competitions[comp_name] = []
        competitions[comp_name].append(match)
    
    # Construire le message
    total_matches = len(matches)
    today = datetime.now().strftime("%d/%m/%Y")
    
    message = f"📅 *MATCHS DU {today}* ({total_matches} matchs)\n\n"
    
    for comp_name, comp_matches in competitions.items():
        # Emoji pour la compétition
        if 'Champions League' in comp_name:
            emoji = "🏆"
        elif 'Premier League' in comp_name:
            emoji = "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
        elif 'Ligue 1' in comp_name:
            emoji = "🇫🇷"
        elif 'LaLiga' in comp_name:
            emoji = "🇪🇸"
        elif 'Serie A' in comp_name:
            emoji = "🇮🇹"
        elif 'Bundesliga' in comp_name:
            emoji = "🇩🇪"
        else:
            emoji = "⚽"
        
        message += f"{emoji} *{comp_name}*\n"
        message += "━" * 25 + "\n"
        
        for match in comp_matches:
            # Équipes
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            
            # Heure du match (format UTC)
            date_str = match['utcDate']
            match_time = date_str[11:16]  # HH:MM
            
            # Score si disponible
            score_home = match['score']['fullTime']['home']
            score_away = match['score']['fullTime']['away']
            
            status = match['status']
            
            if status == 'FINISHED':
                message += f"✅ *TERMINÉ*\n"
                message += f"⚽ {home} {score_home} - {score_away} {away}\n"
            elif status == 'IN_PLAY':
                message += f"⚡ *EN DIRECT*\n"
                message += f"⚽ {home} {score_home or 0} - {score_away or 0} {away}\n"
            elif status == 'PAUSED':
                message += f"⏸️ *MI-TEMPS*\n"
                message += f"⚽ {home} {score_home or 0} - {score_away or 0} {away}\n"
            else:
                message += f"⏱️ {match_time}\n"
                message += f"⚽ {home} vs {away}\n"
            
            # Journée (optionnel)
            matchday = match.get('matchday', '')
            if matchday:
                message += f"📋 Journée {matchday}\n"
            
            message += "\n"
        
        message += "\n"
    
    # Ajouter le statut du quota en fin de message (optionnel)
    message += "━" * 35 + "\n"
    message += "#Football #MatchsDuJour #football-data"
    
    return message


def format_matches_simple(matches):
    """
    Version ultra-simple (si le message est trop long)
    """
    if not matches:
        return "📭 Aucun match aujourd'hui"
    
    lines = ["📅 Matchs du jour:"]
    for match in matches[:10]:
        home = match['homeTeam']['name'][:15]
        away = match['awayTeam']['name'][:15]
        time = match['utcDate'][11:16]
        lines.append(f"• {time} - {home} vs {away}")
    
    return "\n".join(lines)


def send_telegram_message(message):
    """
    Envoie un message Telegram
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        response = requests.post(
            url,
            data={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logging.info("✅ Message envoyé sur Telegram")
            return True
        else:
            logging.error(f"❌ Erreur Telegram: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Erreur envoi: {e}")
        return False


def test_api_connection(api):
    """
    Teste la connexion à l'API
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        matches = api.get_today_matches(today)
        
        if matches is not None:
            quota = api.check_quota()
            logging.info(f"✅ Connexion réussie! Quota restant: {quota}")
            return True
    except:
        pass
    
    logging.error("❌ Échec connexion API")
    return False


def run():
    """
    Fonction principale
    """
    print("\n" + "="*60)
    print("⚽ BOT FOOTBALL - football-data.org")
    print("="*60 + "\n")
    
    # Vérification des clés
    if not FOOTBALL_DATA_API_KEY:
        logging.error("❌ Clé football-data.org manquante")
        print("\nObtenez votre clé sur: https://www.football-data.org/client/register")
        return
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("❌ Configuration Telegram manquante")
        return
    
    logging.info("✅ Configuration validée")
    
    # Initialisation API
    api = FootballDataAPI(FOOTBALL_DATA_API_KEY)
    
    # Test connexion
    if not test_api_connection(api):
        logging.error("❌ Impossible de se connecter à l'API")
        return
    
    # Récupérer les matchs du jour
    today = datetime.now().strftime("%Y-%m-%d")
    matches = api.get_today_matches(today)
    
    # Formater le message
    if matches:
        message = format_matches_for_telegram(matches)
        logging.info(f"✅ {len(matches)} matchs trouvés")
    else:
        # Chercher les prochains jours
        logging.info("🔍 Aucun match aujourd'hui, recherche dans les 3 prochains jours...")
        
        next_matches = []
        for i in range(1, 4):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            day_matches = api.get_today_matches(date)
            if day_matches:
                next_matches.extend(day_matches)
        
        if next_matches:
            message = f"📅 *PROCHAINS MATCHS*\n\n"
            message += format_matches_for_telegram(next_matches)
        else:
            message = "📭 *Aucun match programmé dans les 3 prochains jours*\n\n"
            message += "Les championnats européens sont peut-être en trêve.\n\n"
            message += "📆 Revenez dans quelques jours !\n\n"
            message += "#Football #Pause"
    
    # Envoyer sur Telegram
    if send_telegram_message(message):
        logging.info("✅ Bot exécuté avec succès")
    else:
        logging.error("❌ Échec de l'envoi")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    run()
