import requests
from datetime import datetime
import os

# --- Configuration (à adapter avec vos variables d'environnement) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_events_for_date(target_date):
    """
    Récupère les événements (matchs) pour une date donnée via TheSportsDB.
    Args:
        target_date (str): La date au format 'YYYY-MM-DD'.
    Returns:
        list: Une liste de dictionnaires contenant les infos des matchs, ou None.
    """
    # L'endpoint pour les événements par date
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={target_date}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Lève une exception pour les codes HTTP 4xx/5xx
        data = response.json()

        # Vérifie si la clé 'events' existe et n'est pas vide
        if data and data.get('events'):
            print(f"✅ {len(data['events'])} événements trouvés pour le {target_date}")
            return data['events']
        else:
            print(f"ℹ️ Aucun événement trouvé pour le {target_date}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau ou HTTP: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return None

def format_events_for_telegram(events_list):
    """
    Formate une liste d'événements en un message prêt pour Telegram.
    """
    if not events_list:
        return "📭 Aucun match trouvé pour aujourd'hui."

    message = "📅 *Matchs du jour (TheSportsDB)*\n\n"
    # On groupe par sport ou ligue pour plus de clarté (optionnel)
    # Ici, on affiche simplement la liste
    for event in events_list:
        # Gestion robuste des clés manquantes avec .get()
        home_team = event.get('strHomeTeam', 'Inconnu')
        away_team = event.get('strAwayTeam', 'Inconnu')
        league = event.get('strLeague', 'Ligue inconnue')
        # La date est déjà dans target_date, on peut afficher l'heure si disponible
        time = event.get('strTime', 'Horaire non spécifié')

        message += f"🏆 *{league}*\n"
        message += f"⏱️ {time}\n"
        message += f"⚽ {home_team} vs {away_team}\n\n"

    message += "#Football #TheSportsDB"
    return message

def send_telegram_message(message):
    """Envoie un message Telegram (identique à vos versions précédentes)"""
    # ... (code à copier depuis vos précédents scripts fonctionnels)
    pass

# --- Exécution principale ---
if __name__ == "__main__":
    # 1. Obtenir la date d'aujourd'hui au format requis par l'API
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🔍 Recherche des matchs pour le {today_str}...")

    # 2. Récupérer les événements
    events_today = get_events_for_date(today_str)

    # 3. Formater le message
    if events_today is not None: # Vérifie que la requête a réussi (même si 0 événement)
        telegram_message = format_events_for_telegram(events_today)
    else:
        telegram_message = "⚠️ Erreur lors de la récupération des données depuis TheSportsDB."

    # 4. Envoyer sur Telegram (à décommenter quand vous aurez intégré la fonction)
    # send_telegram_message(telegram_message)
    print("\n" + "="*40)
    print("📝 Message formaté pour Telegram :")
    print("="*40)
    print(telegram_message)
