import os
import requests

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
ODDS_BASE = "https://api.the-odds-api.com/v4"


def api_football_headers():
    return {"x-apisports-key": API_FOOTBALL_KEY}


def search_team(team_name):
    if not API_FOOTBALL_KEY:
        return None, "API_FOOTBALL_KEY no está configurada."

    url = f"{API_FOOTBALL_BASE}/teams"
    params = {"search": team_name}

    try:
        response = requests.get(
            url,
            headers=api_football_headers(),
            params=params,
            timeout=20
        )
    except Exception as e:
        return None, f"Error conectando con API-Football: {e}"

    if response.status_code != 200:
        return None, f"API-Football respondió error {response.status_code}: {response.text}"

    data = response.json()
print("BUSCANDO:", team_name)
print("RESPUESTA API:", data)
    teams = data.get("response", [])

    if not teams:
        return None, f"No se encontró el equipo: {team_name}. Prueba con el nombre en inglés."

    team = teams[0].get("team", {})

    return {
        "id": team.get("id"),
        "name": team.get("name"),
        "country": team.get("country")
    }, None


def get_team_last_fixtures(team_id, last=5):
    url = f"{API_FOOTBALL_BASE}/fixtures"
    params = {
        "team": team_id,
        "last": last
    }

    try:
        response = requests.get(
            url,
            headers=api_football_headers(),
            params=params,
            timeout=20
        )
    except Exception:
        return []

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("response", [])


def calculate_form_points(team_id, fixtures):
    points = 0

    for fixture in fixtures:
        teams = fixture.get("teams", {})
        goals = fixture.get("goals", {})

        home = teams.get("home", {})
        away = teams.get("away", {})

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        is_home = home.get("id") == team_id

        if home_goals == away_goals:
            points += 1
        elif is_home and home_goals > away_goals:
            points += 3
        elif not is_home and away_goals > home_goals:
            points += 3

    return points


def estimate_xg_from_goals(team_id, fixtures):
    goals_for = 0
    goals_against = 0
    count = 0

    for fixture in fixtures:
        teams = fixture.get("teams", {})
        goals = fixture.get("goals", {})

        home = teams.get("home", {})
        away = teams.get("away", {})

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        if home.get("id") == team_id:
            goals_for += home_goals
            goals_against += away_goals
            count += 1

        elif away.get("id") == team_id:
            goals_for += away_goals
            goals_against += home_goals
            count += 1

    if count == 0:
        return {
            "xg": 1.20,
            "xga": 1.20,
            "sample_size": 0
        }

    return {
        "xg": round(goals_for / count, 2),
        "xga": round(goals_against / count, 2),
        "sample_size": count
    }


def estimate_elo(team_name):
    elite = [
        "Argentina", "France", "Brazil", "Spain", "England",
        "Portugal", "Germany", "Netherlands", "Belgium", "Italy"
    ]

    strong = [
        "Uruguay", "Croatia", "Colombia", "Morocco",
        "Switzerland", "Japan", "Denmark", "Mexico",
        "USA", "United States"
    ]

    if team_name in elite:
        return 1800

    if team_name in strong:
        return 1680

    return 1500


def get_odds_from_the_odds_api(home_team, away_team):
    if not ODDS_API_KEY:
        return None

    url = f"{ODDS_BASE}/sports/soccer_fifa_world_cup/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(url, params=params, timeout=20)
    except Exception:
        return None

    if response.status_code != 200:
        return None

    games = response.json()

    for game in games:
        api_home = game.get("home_team", "")
        api_away = game.get("away_team", "")

        home_match = home_team.lower() in api_home.lower()
        away_match = away_team.lower() in api_away.lower()

        if not home_match or not away_match:
            continue

        bookmakers = game.get("bookmakers", [])

        if not bookmakers:
            continue

        markets = bookmakers[0].get("markets", [])

        if not markets:
            continue

        outcomes = markets[0].get("outcomes", [])

        odds = {
            "home": 0,
            "draw": 0,
            "away": 0
        }

        for outcome in outcomes:
            name = outcome.get("name", "")
            price = outcome.get("price", 0)

            if name.lower() == api_home.lower():
                odds["home"] = price
            elif name.lower() == api_away.lower():
                odds["away"] = price
            elif name.lower() == "draw":
                odds["draw"] = price

        return odds

    return None


def build_automatic_match_data(league, home_team, away_team, bookmaker="Betsson"):
    home, home_error = search_team(home_team)

    if home_error:
        return None, home_error

    away, away_error = search_team(away_team)

    if away_error:
        return None, away_error

    home_fixtures = get_team_last_fixtures(home["id"], 5)
    away_fixtures = get_team_last_fixtures(away["id"], 5)

    home_stats = estimate_xg_from_goals(home["id"], home_fixtures)
    away_stats = estimate_xg_from_goals(away["id"], away_fixtures)

    form_home = calculate_form_points(home["id"], home_fixtures)
    form_away = calculate_form_points(away["id"], away_fixtures)

    odds = get_odds_from_the_odds_api(home["name"], away["name"])

    if not odds:
        odds = {
            "home": 0,
            "draw": 0,
            "away": 0
        }

    data = {
        "league": league,
        "bookmaker": bookmaker,
        "home_team": home["name"],
        "away_team": away["name"],
        "cuota_home": odds["home"],
        "cuota_draw": odds["draw"],
        "cuota_away": odds["away"],
        "xg_home": home_stats["xg"],
        "xga_home": home_stats["xga"],
        "xg_away": away_stats["xg"],
        "xga_away": away_stats["xga"],
        "elo_home": estimate_elo(home["name"]),
        "elo_away": estimate_elo(away["name"]),
        "form_home": form_home,
        "form_away": form_away,
        "sample_size": min(home_stats["sample_size"], away_stats["sample_size"]),
        "anomaly": False
    }

    return data, None
