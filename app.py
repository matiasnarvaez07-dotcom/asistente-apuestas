from flask import Flask, render_template, request
from analysis_engine import analyze
from database import save_analysis, get_history, init_db

app = Flask(__name__)

def parse_float(name, default=0.0):
    value = request.form.get(name, "")
    try:
        return float(value)
    except ValueError:
        return default

def parse_int(name, default=0):
    value = request.form.get(name, "")
    try:
        return int(float(value))
    except ValueError:
        return default

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    form_data = {
        "league": "Chile Primera",
        "bookmaker": "Betsson",
        "home_team": "Colo Colo",
        "away_team": "Universidad de Chile",
        "cuota_home": "2.10",
        "cuota_draw": "3.30",
        "cuota_away": "3.50",
        "xg_home": "1.75",
        "xga_home": "1.10",
        "xg_away": "1.25",
        "xga_away": "1.40",
        "elo_home": "1680",
        "elo_away": "1620",
        "form_home": "10",
        "form_away": "8",
        "sample_size": "10",
        "anomaly": ""
    }

    if request.method == "POST":
        form_data.update(request.form.to_dict())

        data = {
            "league": request.form.get("league", "Sin liga"),
            "bookmaker": request.form.get("bookmaker", "Betsson"),
            "home_team": request.form.get("home_team", "Local"),
            "away_team": request.form.get("away_team", "Visitante"),
            "cuota_home": parse_float("cuota_home"),
            "cuota_draw": parse_float("cuota_draw"),
            "cuota_away": parse_float("cuota_away"),
            "xg_home": parse_float("xg_home"),
            "xga_home": parse_float("xga_home"),
            "xg_away": parse_float("xg_away"),
            "xga_away": parse_float("xga_away"),
            "elo_home": parse_int("elo_home"),
            "elo_away": parse_int("elo_away"),
            "form_home": parse_int("form_home"),
            "form_away": parse_int("form_away"),
            "sample_size": parse_int("sample_size"),
            "anomaly": request.form.get("anomaly") == "on"
        }

        result = analyze(data)
        save_analysis(data, result)

    return render_template("index.html", result=result, form_data=form_data)

@app.route("/history")
def history():
    rows = get_history(150)
    return render_template("history.html", rows=rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
