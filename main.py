import requests
import os
from datetime import datetime, timedelta
import time

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class FootballAPIDiagnostic:
    """
    Diagnostic complet pour trouver POURQUOI aucun match n'est trouvé
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.thesportsdb.com/api/v1/json/3"
        
        # Base de données de secours avec des IDs vérifiés
        self.verified_leagues = {
            # France - IDs vérifiés manuellement
            "Ligue 1": 4334,
            "Ligue 2": 4335,
            "National": 4503,
            
            # Angleterre
            "Premier League": 4328,
            "Championship": 4329,
            "League One": 4330,
            "League Two": 4331,
            
            # Europe
            "Champions League": 4323,  # Ligue des Champions
            "Europa League": 4324,      # Europa League
        }
    
    def test_api_connection(self):
        """Test basique : l'API répond-elle ?"""
        print("\n📡 TEST 1: CONNEXION API")
        try:
            response = self.session.get(f"{self.base_url}/all_leagues.php", timeout=10)
            if response.status_code == 200:
                data = response.json()
                leagues = data.get('leagues', [])
                print(f"✅ API répond! {len(leagues)} ligues disponibles")
                return True
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def test_date_format(self):
        """Test différents formats de date"""
        print("\n📡 TEST 2: FORMATS DE DATE")
        today = datetime.now()
        date_formats = [
            today.strftime("%Y-%m-%d"),      # 2024-03-06
            today.strftime("%d-%m-%Y"),      # 06-03-2024
            today.strftime("%Y%m%d"),        # 20240306
        ]
        
        for date_format in date_formats:
            url = f"{self.base_url}/eventsday.php"
            params = {'d': date_format}
            
            try:
                response = self.session.get(url, params=params, timeout=5)
                data = response.json()
                events = data.get('events', [])
                print(f"📅 Format {date_format}: {len(events)} matchs")
            except:
                print(f"📅 Format {date_format}: ❌ erreur")
    
    def test_known_league(self, league_id, league_name):
        """Test une ligue spécifique"""
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{self.base_url}/eventsday.php"
        params = {'d': today, 'l': league_id}
        
        try:
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            events = data.get('events', [])
            
            if events:
                print(f"✅ {league_name}: {len(events)} matchs trouvés!")
                return events
            else:
                print(f"ℹ️ {league_name}: 0 match aujourd'hui")
                return []
        except Exception as e:
            print(f"❌ {league_name}: erreur - {e}")
            return []
    
    def search_any_event(self, days=7):
        """Recherche S'IL EXISTE AU MOINS UN MATCH dans les X prochains jours"""
        print(f"\n📡 TEST 3: RECHERCHE SUR {days} JOURS")
        
        today = datetime.now()
        found_any = False
        
        for i in range(days):
            date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{self.base_url}/eventsday.php"
            params = {'d': date}
            
            try:
                response = self.session.get(url, params=params, timeout=5)
                data = response.json()
                events = data.get('events', [])
                
                if events:
                    print(f"✅ {date}: {len(events)} matchs trouvés!")
                    found_any = True
                    # Afficher les 3 premiers
                    for event in events[:3]:
                        home = event.get('strHomeTeam', '?')
                        away = event.get('strAwayTeam', '?')
                        league = event.get('strLeague', '?')
                        print(f"   • {league}: {home} vs {away}")
                else:
                    print(f"ℹ️ {date}: 0 match")
            except:
                print(f"⚠️ {date}: erreur")
            
            time.sleep(1)  # Politesse
        
        return found_any
    
    def test_alternative_endpoints(self):
        """Test d'autres endpoints de l'API"""
        print("\n📡 TEST 4: ENDPOINTS ALTERNATIFS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Endpoint 1: next events
        url1 = f"{self.base_url}/eventsnextleague.php"
        params1 = {'id': 4328}  # Premier League
        
        try:
            response = self.session.get(url1, params=params1, timeout=5)
            data = response.json()
            events = data.get('events', [])
            print(f"📌 eventsnextleague: {len(events)} matchs à venir")
        except:
            print("📌 eventsnextleague: ❌ erreur")
        
        # Endpoint 2: last events
        url2 = f"{self.base_url}/eventslast.php"
        params2 = {'id': 4328}
        
        try:
            response = self.session.get(url2, params=params2, timeout=5)
            data = response.json()
            events = data.get('results', [])
            print(f"📌 eventslast: {len(events)} derniers matchs")
        except:
            print("📌 eventslast: ❌ erreur")

def send_diagnostic_report(message):
    """Envoie le rapport de diagnostic sur Telegram"""
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
    except:
        return False

def run_diagnostic():
    """Exécute le diagnostic complet"""
    print("\n" + "="*70)
    print("🔧 DIAGNOSTIC COMPLET - POURQUOI AUCUN MATCH ?")
    print("="*70 + "\n")
    
    diag = FootballAPIDiagnostic()
    
    # 1. Test connexion API
    if not diag.test_api_connection():
        print("\n❌ L'API elle-même ne répond pas!")
        message = "⚠️ *Problème API TheSportsDB*\n\nL'API ne répond pas. Vérifiez plus tard."
        send_diagnostic_report(message)
        return
    
    # 2. Test formats de date
    diag.test_date_format()
    
    # 3. Test quelques ligues spécifiques
    print("\n📡 TEST LIGUES SPÉCIFIQUES")
    any_match_found = False
    for league_name, league_id in diag.verified_leagues.items():
        events = diag.test_known_league(league_id, league_name)
        if events:
            any_match_found = True
    
    # 4. Recherche large sur plusieurs jours
    found_in_future = diag.search_any_event(days=10)
    
    # 5. Test endpoints alternatifs
    diag.test_alternative_endpoints()
    
    # 6. Conclusion
    print("\n" + "="*70)
    print("📊 RAPPORT FINAL")
    print("="*70)
    
    if any_match_found:
        print("✅ Des matchs existent pour aujourd'hui dans certaines ligues!")
        message = "✅ *Matchs trouvés aujourd'hui!*\n\nLe bot fonctionne correctement."
    elif found_in_future:
        print("⚠️ Pas de match aujourd'hui, MAIS il y en a dans les prochains jours.")
        message = "📅 *Pas de match aujourd'hui*\n\nMais des matchs sont programmés dans les prochains jours. Le bot est opérationnel."
    else:
        print("❌ Aucun match trouvé nulle part - problème probable avec l'API")
        message = "⚠️ *Problème détecté*\n\nAucun match trouvé sur aucune période. L'API TheSportsDB a peut-être changé."
    
    print("="*70)
    
    # Envoyer le rapport sur Telegram
    if send_diagnostic_report(message):
        print("\n✅ Rapport envoyé sur Telegram")
    else:
        print("\n❌ Échec envoi rapport")

if __name__ == "__main__":
    run_diagnostic()
