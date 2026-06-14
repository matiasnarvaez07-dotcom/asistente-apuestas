import math

def implied_probability(decimal_odds):
    if decimal_odds is None or decimal_odds <= 0:
        return None
    return 1.0 / decimal_odds

def normalize_probs(probs):
    total = sum(probs.values())
    if total <= 0:
        n = len(probs)
        return {k: 1 / n for k in probs}
    return {k: v / total for k, v in probs.items()}

def poisson_prob(lam, k):
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

def poisson_1x2(xg_home, xg_away, max_goals=7):
    home_win = 0.0
    draw = 0.0
    away_win = 0.0

    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_prob(xg_home, h) * poisson_prob(xg_away, a)
            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p

    return normalize_probs({"home": home_win, "draw": draw, "away": away_win})

def top_scores(xg_home, xg_away, max_goals=5, top_n=5):
    scores = []
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_prob(xg_home, h) * poisson_prob(xg_away, a)
            scores.append({
                "score": f"{h}-{a}",
                "probability": round(p * 100, 2)
            })
    return sorted(scores, key=lambda x: x["probability"], reverse=True)[:top_n]

def elo_1x2(elo_home, elo_away, home_bonus=50):
    diff = (elo_home + home_bonus) - elo_away
    home_no_draw = 1 / (1 + 10 ** (-diff / 400))
    away_no_draw = 1 - home_no_draw

    abs_diff = abs(diff)
    if abs_diff <= 50:
        draw = 0.30
    elif abs_diff <= 120:
        draw = 0.26
    elif abs_diff <= 200:
        draw = 0.23
    else:
        draw = 0.18

    remaining = 1 - draw
    return normalize_probs({
        "home": home_no_draw * remaining,
        "draw": draw,
        "away": away_no_draw * remaining
    })

def form_1x2(form_home, form_away):
    home_strength = max(form_home, 1)
    away_strength = max(form_away, 1)
    diff = abs(home_strength - away_strength)

    draw = max(0.20, min(0.32, 0.32 - diff * 0.015))
    remaining = 1 - draw
    home = remaining * (home_strength / (home_strength + away_strength))
    away = remaining * (away_strength / (home_strength + away_strength))
    return normalize_probs({"home": home, "draw": draw, "away": away})

def context_1x2():
    return {"home": 0.34, "draw": 0.30, "away": 0.36}

def weighted_model(data):
    xg_home_adj = (data["xg_home"] + data["xga_away"]) / 2
    xg_away_adj = (data["xg_away"] + data["xga_home"]) / 2

    p_poisson = poisson_1x2(xg_home_adj, xg_away_adj)
    p_elo = elo_1x2(data["elo_home"], data["elo_away"])
    p_form = form_1x2(data["form_home"], data["form_away"])
    p_context = context_1x2()

    final = {}
    for outcome in ["home", "draw", "away"]:
        final[outcome] = (
            p_poisson[outcome] * 0.40 +
            p_elo[outcome] * 0.30 +
            p_form[outcome] * 0.20 +
            p_context[outcome] * 0.10
        )

    return normalize_probs(final), p_poisson, p_elo, p_form, p_context, xg_home_adj, xg_away_adj

def consensus_level(data, target_outcome):
    model_probs, p_poisson, p_elo, p_form, p_context, _, _ = weighted_model(data)
    models = [p_poisson, p_elo, p_form, p_context]

    votes = 0
    for model in models:
        best = max(model, key=model.get)
        if best == target_outcome:
            votes += 1

    if votes >= 4:
        return "Alto"
    if votes == 3:
        return "Medio"
    return "Bajo"

def igc_score(data, consensus, edge):
    data_available = 25

    sample = int(data.get("sample_size", 0))
    if sample >= 15:
        sample_score = 20
    elif sample >= 10:
        sample_score = 14
    elif sample >= 5:
        sample_score = 8
    else:
        sample_score = 2

    consensus_score = {"Alto": 20, "Medio": 14, "Bajo": 6}.get(consensus, 6)
    anomaly_score = 0 if data.get("anomaly") else 15
    history_score = 5

    if edge >= 0.10:
        edge_score = 10
    elif edge >= 0.07:
        edge_score = 7
    elif edge >= 0.03:
        edge_score = 4
    else:
        edge_score = 0

    return int(data_available + sample_score + consensus_score + anomaly_score + history_score + edge_score)

def classify(edge, igc, consensus, anomaly):
    if edge < 0.03:
        return "Sin ventaja", "Analizable", "Diferencia menor a 3%; se considera ruido estadístico."

    if anomaly:
        return "Valor bajo", "Analizable con reservas", "Existe evento anómalo; se reduce confianza."

    if consensus == "Bajo":
        return "Valor bajo", "Analizable con reservas", "Existe diferencia positiva, pero el consenso entre modelos es bajo."

    if edge >= 0.12 and igc > 70:
        return "Valor alto", "Analizable", "Diferencia positiva con validación suficiente del modelo."

    if edge >= 0.07 and igc > 60:
        return "Valor medio", "Analizable", "Diferencia positiva moderada con validación aceptable."

    return "Valor bajo", "Analizable con reservas", "Diferencia positiva, pero calidad o consenso limitados."

def confidence(data, igc, consensus):
    if int(data.get("sample_size", 0)) < 10:
        return "Baja"
    if igc >= 81 and consensus in ["Alto", "Medio"]:
        return "Muy Alta"
    if igc >= 70:
        return "Alta"
    if igc >= 50:
        return "Media"
    return "Baja"

def analyze(data):
    model_probs, p_poisson, p_elo, p_form, p_context, xg_home_adj, xg_away_adj = weighted_model(data)
    odds = {
        "home": data["cuota_home"],
        "draw": data["cuota_draw"],
        "away": data["cuota_away"]
    }

    outcomes_label = {
        "home": data["home_team"],
        "draw": "Empate",
        "away": data["away_team"]
    }

    analyses = []
    for outcome, price in odds.items():
        if not price or price <= 0:
            analyses.append({
                "outcome": outcome,
                "outcome_label": outcomes_label[outcome],
                "price": price,
                "model_probability": round(model_probs[outcome] * 100, 2),
                "market_probability": None,
                "edge": None,
                "value_label": "Información insuficiente",
                "classification": "No clasificable",
                "risk": "Alto",
                "confidence": "Muy Baja",
                "igc": 0,
                "consensus": "Bajo",
                "reason": "Cuota no disponible."
            })
            continue

        market_prob = implied_probability(price)
        edge = model_probs[outcome] - market_prob
        consensus = consensus_level(data, outcome)
        igc = igc_score(data, consensus, edge)
        value_label, classification, reason = classify(edge, igc, consensus, data.get("anomaly", False))
        risk = "Alto" if data.get("anomaly") else "Medio"

        analyses.append({
            "outcome": outcome,
            "outcome_label": outcomes_label[outcome],
            "price": round(price, 2),
            "model_probability": round(model_probs[outcome] * 100, 2),
            "market_probability": round(market_prob * 100, 2),
            "edge": round(edge * 100, 2),
            "value_label": value_label,
            "classification": classification,
            "risk": risk,
            "confidence": confidence(data, igc, consensus),
            "igc": igc,
            "consensus": consensus,
            "reason": reason
        })

    best = sorted(
        analyses,
        key=lambda x: (
            x["classification"] == "Analizable",
            x["edge"] if x["edge"] is not None else -999,
            x["igc"]
        ),
        reverse=True
    )[0]

    return {
        "match": f'{data["home_team"]} vs {data["away_team"]}',
        "league": data["league"],
        "bookmaker": data["bookmaker"],
        "xg_adjusted": {
            "home": round(xg_home_adj, 2),
            "away": round(xg_away_adj, 2)
        },
        "top_scores": top_scores(xg_home_adj, xg_away_adj),
        "component_models": {
            "poisson": {k: round(v * 100, 2) for k, v in p_poisson.items()},
            "elo": {k: round(v * 100, 2) for k, v in p_elo.items()},
            "form": {k: round(v * 100, 2) for k, v in p_form.items()},
            "context": {k: round(v * 100, 2) for k, v in p_context.items()}
        },
        "analyses": analyses,
        "best": best
    }
