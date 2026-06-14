import os
import requests

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
print("API_FOOTBALL_KEY:", API_FOOTBALL_KEY)
print("ODDS_API_KEY:", ODDS_API_KEY)
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
ODDS_BASE = "https://api.the-odds-api.com/v4"


def api_football_headers():
    return {
        "x-apisports-key": API_FOOTBALL_KEY
    }


def search_team(team_name):
    if not API_FOOTBALL_KEY:
        return None

    url = f"{API_FOOTBALL_BASE}/teams"
    params = {"search": team_name}

    response = requests.get(
        url,
        headers=api_football_headers(),
        params=params,
        timeout=20
    )

    if response.status_code != 200:
    print("ERROR SEARCH TEAM:", team_name)
    print("STATUS:", response.status_code)
    print("RESPUESTA:", response.text)
    return None

    data = response.json()

    if not data.get("response"):
    print("SIN RESULTADOS PARA:", team_name)
    print("RESPUESTA API:", data)
    return None

    team = data["response"][0]["team"]

    return {
        "id": team.get("id"),
        "name": team.get("name"),
        "country": team.get("country")
    }


def search_fixture(home_team, away_team):
    home = search_team(home_team)
    away = search_team(away_team)

    if not home or not away:
        return None

    url = f"{API_FOOTBALL_BASE}/fixtures/headtohead"
    params = {
        "h2h": f"{home['id']}-{away['id']}",
        "last": 5
    }

    response = requests.get(
        url,
        headers=api_football_headers(),
        params=params,
        timeout=20
    )

    if response.status_code != 200:
        return None

    data = response.json()

    return {
        "home_team": home,
        "away_team": away,
        "h2h": data.get("response", [])
    }


def get_team_last_fixtures(team_id, last=5):
    if not API_FOOTBALL_KEY:
        return []

    url = f"{API_FOOTBALL_BASE}/fixtures"
    params = {
        "team": team_id,
        "last": last
    }

    response = requests.get(
        url,
        headers=api_football_headers(),
        params=params,
        timeout=20
    )

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("response", [])


def calculate_form_points(team_id, fixtures):
    points = 0

    for f in fixtures:
        teams = f.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        goals = f.get("goals", {})

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

    for f in fixtures:
        teams = f.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        goals = f.get("goals", {})

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        if home.get("id") == team_id:
            goals_for += home_goals
            goals_against += away_goals
        elif away.get("id") == team_id:
            goals_for += away_goals
            goals_against += home_goals
        else:
            continue

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
        "Uruguay", "Croatia", "Colombia", "Morocco", "Switzerland",
        "Japan", "Denmark", "Mexico", "USA", "United States"
    ]

    if team_name in elite:
        return 1800

    if team_name in strong:
        return 1680

    return 1500


def get_odds_from_the_odds_api(home_team, away_team, sport_key="soccer_fifa_world_cup"):
    if not ODDS_API_KEY:
        return None

    url = f"{ODDS_BASE}/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    response = requests.get(url, params=params, timeout=20)

    if response.status_code != 200:
        return None

    games = response.json()

    for game in games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")

        if home_team.lower() in home.lower() and away_team.lower() in away.lower():
            bookmakers = game.get("bookmakers", [])

            if not bookmakers:
                continue

            market = bookmakers[0]["markets"][0]
            outcomes = market.get("outcomes", [])

            odds = {
                "home": None,
                "draw": None,
                "away": None
            }

            for o in outcomes:
                name = o.get("name", "")
                price = o.get("price")

                if name.lower() == home.lower():
                    odds["home"] = price
                elif name.lower() == away.lower():
                    odds["away"] = price
                elif name.lower() == "draw":
                    odds["draw"] = price

            return odds

    return None


def build_automatic_match_data(league, home_team, away_team, bookmaker="Betsson"):
    fixture_data = search_fixture(home_team, away_team)

    if not fixture_data:
        return None, "No se encontraron equipos en API-Football."

    home = fixture_data["home_team"]
    away = fixture_data["away_team"]

    home_fixtures = get_team_last_fixtures(home["id"], 5)
    away_fixtures = get_team_last_fixtures(away["id"], 5)

    home_xg = estimate_xg_from_goals(home["id"], home_fixtures)
    away_xg = estimate_xg_from_goals(away["id"], away_fixtures)

    form_home = calculate_form_points(home["id"], home_fixtures)
    form_away = calculate_form_points(away["id"], away_fixtures)

    odds = get_odds_from_the_odds_api(home_team, away_team)

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
        "cuota_home": odds["home"] or 0,
        "cuota_draw": odds["draw"] or 0,
        "cuota_away": odds["away"] or 0,
        "xg_home": home_xg["xg"],
        "xga_home": home_xg["xga"],
        "xg_away": away_xg["xg"],
        "xga_away": away_xg["xga"],
        "elo_home": estimate_elo(home["name"]),
        "elo_away": estimate_elo(away["name"]),
        "form_home": form_home,
        "form_away": form_away,
        "sample_size": min(home_xg["sample_size"], away_xg["sample_size"]),
        "anomaly": False
    }

    return data, None
