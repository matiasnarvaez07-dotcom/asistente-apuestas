from flask import Flask, render_template, request
from analysis_engine import analyze
from database import save_analysis, get_history, init_db
from football_api import build_automatic_match_data

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    form_data = {
        "league": "Mundial FIFA",
        "bookmaker": "Betsson",
        "home_team": "",
        "away_team": ""
    }

    if request.method == "POST":
        league = request.form.get("league", "Mundial FIFA")
        bookmaker = request.form.get("bookmaker", "Betsson")
        home_team = request.form.get("home_team", "")
        away_team = request.form.get("away_team", "")

        form_data = {
            "league": league,
            "bookmaker": bookmaker,
            "home_team": home_team,
            "away_team": away_team
        }

        if not home_team or not away_team:
            error = "Debes ingresar equipo local y equipo visitante."
        else:
            data, error = build_automatic_match_data(
                league=league,
                home_team=home_team,
                away_team=away_team,
                bookmaker=bookmaker
            )

            if data and not error:
                result = analyze(data)
                save_analysis(data, result)

    return render_template(
        "index.html",
        result=result,
        error=error,
        form_data=form_data
    )


@app.route("/history")
def history():
    rows = get_history(150)
    return render_template("history.html", rows=rows)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
