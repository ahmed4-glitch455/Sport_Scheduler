import requests
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Dictionnaire complet des ligues avec leurs IDs
LEAGUES = {
    # France
    "🇫🇷 Ligue 1": 4334,
    "🇫🇷 Ligue 2": 4335,
    "🇫🇷 National": 4503,
    
    # Angleterre
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 4328,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": 4329,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League One": 4330,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 League Two": 4331,
    
    # Espagne
    "🇪🇸 LaLiga": 4332,
    "🇪🇸 LaLiga 2": 4333,
    
    # Italie
    "🇮🇹 Serie A": 4336,
    "🇮🇹 Serie B": 4337,
    
    # Allemagne
    "🇩🇪 Bundesliga": 4338,
    "🇩🇪 Bundesliga 2": 4339,
    
    # Autres championnats européens
    "🇳🇱 Eredivisie": 4341,
    "🇵🇹 Primeira Liga": 4342,
    "🇧🇪 Jupiler Pro League": 4343,
    "🇹🇷 Süper Lig": 4344,
    "🇷🇺 Premier League": 4345,
    "🇺🇦 Premier League": 4346,
}

def get_all_divisions_events(date=None):
    """
    Récupère les matchs de TOUTES les divisions configurées
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    all_events = []
    print(f"\n🔍 Recherche des matchs du {date} dans {len(LEAGUES)} ligues...")
    
    for league_name, league_id in LEAGUES.items():
        url = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"
        params = {
            'd': date,
            'l': league_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            events = data.get('events', [])
            
            if events:
                # Ajouter le nom complet de la ligue à chaque événement
                for event in events:
                    event['display_league'] = league_name
                all_events.extend(events)
                print(f"✅ {league_name}: {len(events)} matchs")
            else:
                print(f"ℹ️ {league_name}: 0 match")
                
        except Exception as e:
            print(f"❌ {league_name}: Erreur - {e}")
            continue
    
    return all_events

def format_events_by_division(events):
    """
    Formate les événements en les groupant par division
    """
    if not events:
        return "📭 Aucun match trouvé aujourd'hui."
    
    # Grouper par ligue
    grouped = {}
    for event in events:
        league = event.get('display_league', event.get('strLeague', 'Ligue inconnue'))
        if league not in grouped:
            grouped[league] = []
        grouped[league].append(event)
    
    # Construire le message
    total = len(events)
    message = f"📅 *MATCHS DU JOUR* ({total} matchs)\n\n"
    
    for league_name, league_events in grouped.items():
        message += f"🏆 *{league_name}*\n"
        message += "━" * 25 + "\n"
        
        for event in league_events:
            home = event.get('strHomeTeam', '?')
            away = event.get('strAwayTeam', '?')
            
            # Essayer d'extraire l'heure
            time_str = event.get('strTime', '?')
            if time_str and time_str != '?':
                if len(time_str) > 5:
                    time_str = time_str[:5]
            
            message += f"⏱️ {time_str}\n"
            message += f"⚽ {home} vs {away}\n\n"
        
        message += "\n"
    
    message += "━" * 35 + "\n"
    message += "#Football #ToutesDivisions"
    
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
        print(f"❌ Erreur Telegram: {e}")
        return False

def run():
    print("\n" + "="*60)
    print("⚽ BOT TOUTES DIVISIONS")
    print("="*60 + "\n")
    
    # Récupérer les matchs de toutes les divisions
    today = datetime.now().strftime("%Y-%m-%d")
    events = get_all_divisions_events(today)
    
    # Formater le message
    message = format_events_by_division(events)
    
    # Envoyer sur Telegram
    if send_telegram_message(message):
        print(f"\n✅ {len(events)} matchs envoyés sur Telegram")
    else:
        print("\n❌ Échec de l'envoi")

if __name__ == "__main__":
    run()
