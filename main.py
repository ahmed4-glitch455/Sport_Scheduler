import requests
import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import time

# --- CONFIGURATION ---
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sport_bot.log'),
        logging.StreamHandler()
    ]
)

# IDs des ligues populaires (vous pouvez ajouter/modifier selon vos besoins)
LEAGUES = {
    "ligue1": {
        "id": 13,
        "name": "Ligue 1",
        "country": "France",
        "emoji": "🇫🇷"
    },
    "premier-league": {
        "id": 8,
        "name": "Premier League",
        "country": "Angleterre",
        "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    },
    "laliga": {
        "id": 12,
        "name": "LaLiga",
        "country": "Espagne",
        "emoji": "🇪🇸"
    },
    "serie-a": {
        "id": 11,
        "name": "Serie A",
        "country": "Italie",
        "emoji": "🇮🇹"
    },
    "bundesliga": {
        "id": 9,
        "name": "Bundesliga",
        "country": "Allemagne",
        "emoji": "🇩🇪"
    },
    "champions-league": {
        "id": 3,
        "name": "Ligue des Champions",
        "country": "Europe",
        "emoji": "🏆"
    }
}


class SportMonksAPI:
    """Client pour l'API SportMonks v3"""
    
    BASE_URL = "https://api.sportmonks.com/v3/football"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.cache_dir = Path("sport_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
    
    def _make_request(self, endpoint, params=None):
        """Effectue une requête à l'API SportMonks"""
        if params is None:
            params = {}
        
        # Ajouter la clé API à tous les paramètres
        params["api_token"] = self.api_key
        
        # Construire l'URL complète
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur API SportMonks: {e}")
            return None
    
    def get_todays_fixtures(self, league_id=None):
        """Récupère les matchs du jour"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Endpoint: fixtures/date/{date}
        endpoint = f"fixtures/date/{today}"
        
        # Inclure les données des chaînes TV et des équipes
        params = {
            "include": "tvStations;localTeam;visitorTeam;league",
            "per_page": 50
        }
        
        if league_id:
            params["filters"] = f"league_id:{league_id}"
        
        data = self._make_request(endpoint, params)
        return data.get('data', []) if data else []
    
    def get_fixtures_by_date(self, date, league_id=None):
        """Récupère les matchs pour une date spécifique"""
        endpoint = f"fixtures/date/{date}"
        
        params = {
            "include": "tvStations;localTeam;visitorTeam;league",
            "per_page": 50
        }
        
        if league_id:
            params["filters"] = f"league_id:{league_id}"
        
        data = self._make_request(endpoint, params)
        return data.get('data', []) if data else []
    
    def get_live_scores(self):
        """Récupère les scores en direct"""
        endpoint = "livescores"
        params = {
            "include": "localTeam;visitorTeam;league;tvStations",
            "per_page": 50
        }
        
        data = self._make_request(endpoint, params)
        return data.get('data', []) if data else []
    
    def get_league_standings(self, league_id, season_id=None):
        """Récupère le classement d'une ligue"""
        if not season_id:
            # Utiliser la saison en cours (2026)
            season_id = 22569  # ID de la saison 2026 (à vérifier)
        
        endpoint = f"standings/seasons/{season_id}"
        params = {
            "include": "participant",
            "filters": f"league_id:{league_id}"
        }
        
        data = self._make_request(endpoint, params)
        return data.get('data', []) if data else []
    
    def search_tv_stations(self, fixture_id):
        """Recherche les chaînes TV pour un match spécifique"""
        endpoint = f"fixtures/{fixture_id}"
        params = {"include": "tvStations"}
        
        data = self._make_request(endpoint, params)
        if data and data.get('data'):
            return data['data'].get('tvStations', {}).get('data', [])
        return []


def format_fixtures_message(fixtures, title="📅 Matchs du jour"):
    """Formate les matchs pour Telegram"""
    if not fixtures:
        return "📭 Aucun match trouvé pour cette période."
    
    message = f"{title}\n\n"
    
    # Grouper par ligue
    matches_by_league = {}
    for match in fixtures:
        league = match.get('league', {}).get('data', {})
        league_name = league.get('name', 'Ligue inconnue')
        
        if league_name not in matches_by_league:
            matches_by_league[league_name] = []
        matches_by_league[league_name].append(match)
    
    # Construire le message
    for league_name, matches in matches_by_league.items():
        message += f"🏆 *{league_name}*\n"
        message += "━" * 30 + "\n"
        
        for match in matches:
            # Équipes
            local = match.get('localTeam', {}).get('data', {}).get('name', '?')
            visitor = match.get('visitorTeam', {}).get('data', {}).get('name', '?')
            
            # Score
            scores = match.get('scores', {})
            local_score = scores.get('localteam_score', '?')
            visitor_score = scores.get('visitorteam_score', '?')
            
            # Statut du match
            status = match.get('time', {}).get('status', 'NS')
            minute = match.get('time', {}).get('minute', '')
            
            if status == 'LIVE':
                time_info = f"⚡ {minute}'"
                score_display = f"{local} {local_score} - {visitor_score} {visitor}"
            elif status == 'FT':
                time_info = "✅ Terminé"
                score_display = f"{local} {local_score} - {visitor_score} {visitor}"
            elif status == 'NS':
                time_info = match.get('starting_at', '?')[11:16] if match.get('starting_at') else '?'
                score_display = f"{local} vs {visitor}"
            else:
                time_info = status
                score_display = f"{local} vs {visitor}"
            
            message += f"⏱️ {time_info}\n"
            message += f"⚽ {score_display}\n"
            
            # Chaînes TV
            tv_stations = match.get('tvStations', {}).get('data', [])
            if tv_stations:
                channels = [tv.get('name', '') for tv in tv_stations[:3]]
                message += f"📺 {', '.join(channels)}\n"
            
            message += "\n"
        
        message += "\n"
    
    return message


def format_live_matches_message(matches):
    """Formate les matchs en direct"""
    return format_fixtures_message(matches, "⚡ *Matchs en direct*")


def format_standings_message(standings, league_name):
    """Formate le classement d'une ligue"""
    if not standings:
        return f"📊 Classement {league_name} non disponible"
    
    message = f"📊 *Classement {league_name}*\n\n"
    message += "```\n"
    message += "Pos Équipe                    Pts\n"
    message += "━" * 40 + "\n"
    
    for idx, standing in enumerate(standings[:10], 1):  # Top 10
        participant = standing.get('participant', {}).get('data', {})
        team_name = participant.get('name', '?')[:20]
        points = standing.get('points', '?')
        
        # Formatage sur 2 chiffres pour le classement
        pos = f"{idx:2d}"
        message += f"{pos}  {team_name:<20} {points:>3}\n"
    
    message += "```"
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
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        logging.error(f"❌ Erreur envoi Telegram: {e}")
        return False


def send_daily_summary(sport_api):
    """Envoie un résumé quotidien des matchs"""
    logging.info("📅 Génération du résumé quotidien...")
    
    # Matchs du jour toutes ligues confondues
    fixtures = sport_api.get_todays_fixtures()
    
    if not fixtures:
        message = "📭 Aucun match programmé aujourd'hui."
    else:
        message = format_fixtures_message(fixtures)
    
    # Envoyer le message
    if send_telegram_message(message):
        logging.info("✅ Résumé quotidien envoyé")
    else:
        logging.error("❌ Échec envoi résumé quotidien")


def send_live_updates(sport_api):
    """Envoie les mises à jour des matchs en direct"""
    logging.info("⚡ Vérification des matchs en direct...")
    
    live_matches = sport_api.get_live_scores()
    
    if live_matches:
        message = format_live_matches_message(live_matches)
        if send_telegram_message(message):
            logging.info(f"✅ {len(live_matches)} matchs en direct signalés")
    else:
        logging.info("ℹ️ Aucun match en direct")


def send_league_standings(sport_api, league_key="ligue1"):
    """Envoie le classement d'une ligue spécifique"""
    if league_key not in LEAGUES:
        logging.error(f"Ligue inconnue: {league_key}")
        return
    
    league = LEAGUES[league_key]
    logging.info(f"📊 Récupération classement {league['name']}...")
    
    standings = sport_api.get_league_standings(league["id"])
    
    if standings:
        message = format_standings_message(standings, league['name'])
        if send_telegram_message(message):
            logging.info(f"✅ Classement {league['name']} envoyé")
    else:
        logging.warning(f"⚠️ Classement {league['name']} non disponible")


def send_weekend_preview(sport_api):
    """Envoie un aperçu des matchs du week-end"""
    # Obtenir les matchs pour les 2 prochains jours
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = datetime.now() + timedelta(days=2)
    
    all_fixtures = []
    for date in [tomorrow, day_after]:
        fixtures = sport_api.get_fixtures_by_date(date.strftime("%Y-%m-%d"))
        all_fixtures.extend(fixtures)
    
    if all_fixtures:
        message = format_fixtures_message(
            all_fixtures, 
            "📅 *Programme du week-end*"
        )
        if send_telegram_message(message):
            logging.info("✅ Aperçu week-end envoyé")
    else:
        logging.info("ℹ️ Aucun match ce week-end")


def send_top_matches_by_tv(sport_api, min_channels=2):
    """Envoie les matchs diffusés sur plusieurs chaînes"""
    fixtures = sport_api.get_todays_fixtures()
    
    top_matches = []
    for match in fixtures:
        tv_stations = match.get('tvStations', {}).get('data', [])
        if len(tv_stations) >= min_channels:
            top_matches.append(match)
    
    if top_matches:
        message = format_fixtures_message(
            top_matches,
            f"📺 *Matchs du jour diffusés ({min_channels}+ chaînes)*"
        )
        if send_telegram_message(message):
            logging.info("✅ Top matchs TV envoyés")


def test_api_connection(sport_api):
    """Teste la connexion à l'API SportMonks"""
    try:
        fixtures = sport_api.get_todays_fixtures()
        if fixtures is not None:
            logging.info(f"✅ API SportMonks connectée. {len(fixtures)} matchs trouvés")
            return True
    except Exception as e:
        logging.error(f"❌ Échec connexion API: {e}")
    return False


def run():
    """Fonction principale"""
    logging.info("=" * 50)
    logging.info("🚀 Démarrage du Bot Sport avec SportMonks")
    logging.info("=" * 50)
    
    # Vérifications
    if not all([SPORTMONKS_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logging.error("❌ Clés API manquantes")
        return
    
    logging.info("✅ Configuration validée")
    
    # Initialisation API
    sport_api = SportMonksAPI(SPORTMONKS_API_KEY)
    
    # Test connexion
    if not test_api_connection(sport_api):
        logging.error("❌ Impossible de se connecter à l'API")
        return
    
    # Menu des actions disponibles
    logging.info("📋 Actions disponibles:")
    logging.info("1. Envoyer résumé quotidien")
    logging.info("2. Envoyer matchs en direct")
    logging.info("3. Envoyer classement Ligue 1")
    logging.info("4. Envoyer classement Premier League")
    logging.info("5. Envoyer classement LaLiga")
    logging.info("6. Envoyer aperçu week-end")
    logging.info("7. Envoyer top matchs TV")
    logging.info("8. Tout envoyer")
    
    # Par défaut, envoyer le résumé quotidien
    choice = os.getenv("ACTION", "1")  # On peut passer ACTION en variable d'env
    
    if choice == "1" or choice == "8":
        send_daily_summary(sport_api)
        time.sleep(2)
    
    if choice == "2" or choice == "8":
        send_live_updates(sport_api)
        time.sleep(2)
    
    if choice == "3" or choice == "8":
        send_league_standings(sport_api, "ligue1")
        time.sleep(2)
    
    if choice == "4" or choice == "8":
        send_league_standings(sport_api, "premier-league")
        time.sleep(2)
    
    if choice == "5" or choice == "8":
        send_league_standings(sport_api, "laliga")
        time.sleep(2)
    
    if choice == "6" or choice == "8":
        send_weekend_preview(sport_api)
        time.sleep(2)
    
    if choice == "7" or choice == "8":
        send_top_matches_by_tv(sport_api)
        time.sleep(2)
    
    logging.info("=" * 50)


if __name__ == "__main__":
    run()
