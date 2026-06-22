"""Smoke tests pour la classification FOCUS AGL / PPTX.

Couvre deux corrections :

Bug #2 — seuil captif (100 % PDM) testé sur la PDM ARRONDIE affichée :
    un client à 416/438 = 94,98 % (affiché « 95 % ») doit être classé captif,
    pas dans « autres clients ».

Bug #1 — le Top 10 « Principaux Acteurs de cette Baisse » doit être tiré du
    groupe `others_down` (autres clients en baisse, non captifs), donc cohérent
    avec le total affiché. Les clients captifs en baisse ne doivent pas y figurer.

Lancement : python test_classification_smoke.py
"""
import pandas as pd

from Insight_generation import _categorize_clients, round_half_up, series_round_half_up

CUR, PRV = 2026, 2025
CLIENT = "CLIENT"


def _row(name, agl_prv, tm_prv, agl_cur, tm_cur):
    return {
        CLIENT: name,
        f"AGL_Volume_{PRV}": agl_prv,
        f"Total_Marche_{PRV}": tm_prv,
        f"AGL_Volume_{CUR}": agl_cur,
        f"Total_Marche_{CUR}": tm_cur,
    }


def _build():
    rows = [
        # --- Bug #2 : 94,98 % arrondi 95 % -> doit être captif (hausse) ---
        _row("STE PRODUIT ALIMENT CONGELE CI", 338, 338, 416, 438),  # PDM prv 100%, cur 94.98%->95%, var +78
        # --- captif en baisse : PDM >= 95 % les deux années, AGL en baisse ---
        _row("SOLIBRA", 1000, 1000, 800, 800),                       # 100%/100%, var -200 -> captive_down
        # --- autre client en baisse (non captif) : doit alimenter le top10 ---
        _row("AUTRE BAISSE 1", 500, 700, 300, 700),                  # 71%/43%, var -200
        _row("AUTRE BAISSE 2", 400, 700, 250, 700),                  # 57%/36%, var -150
        # --- client liste noire (excluded_clients.json) en baisse : doit
        #     compter dans le total comme dans update_analyse_group (pas de
        #     filtre liste noire), sinon l'en-tête commentaire diverge du bloc. ---
        _row("ENI CI", 200, 400, 100, 400),                          # 50%/25%, var -100, blacklisté
        # --- autre client en hausse (non captif) ---
        _row("AUTRE HAUSSE", 100, 500, 300, 500),                    # 20%/60%, var +200
        # --- frontière basse : 94,4 % -> arrondi 94 % -> NON captif ---
        _row("FRONTIERE 944", 944, 1000, 944, 1000),                 # 94.4% -> 94 -> autres (var 0 -> hausse)
        # --- frontière : 94,5 % -> arrondi 95 % -> captif ---
        _row("FRONTIERE 945", 945, 1000, 945, 1000),                 # 94.5% -> 95 -> captif
        # --- 100 % concurrent (AGL=0 les deux années) : doit être exclu ---
        _row("CONCURRENT PUR", 0, 500, 0, 500),
    ]
    return pd.DataFrame(rows)


def _names(df):
    return set(df[CLIENT].tolist())


def run():
    comp = _build()
    cats = _categorize_clients(comp, CLIENT, CUR, PRV)

    captive_up = _names(cats["captive_up"])
    captive_down = _names(cats["captive_down"])
    captive = captive_up | captive_down
    hausse = _names(cats["hausse"])
    baisse = _names(cats["baisse"])

    checks = []

    def chk(cond, msg):
        checks.append((bool(cond), msg))

    # ---- Bug #2 ----
    chk("STE PRODUIT ALIMENT CONGELE CI" in captive_up,
        "STE PRODUIT (94,98%->95%, var +78) classé captive_up")
    chk("STE PRODUIT ALIMENT CONGELE CI" not in hausse,
        "STE PRODUIT n'est PAS dans 'autres en hausse'")

    # frontières d'arrondi
    chk("FRONTIERE 945" in captive,
        "94,5 % -> arrondi 95 % -> captif")
    chk("FRONTIERE 944" not in captive and "FRONTIERE 944" in hausse,
        "94,4 % -> arrondi 94 % -> NON captif (autres)")

    # ---- périmètre AGL ----
    chk("CONCURRENT PUR" not in (captive | hausse | baisse),
        "Concurrent pur (AGL=0) exclu de toutes les catégories AGL")

    # ---- captif en baisse ----
    chk("SOLIBRA" in captive_down,
        "SOLIBRA (100%/100%, var -200) classé captive_down")
    chk("SOLIBRA" not in baisse,
        "SOLIBRA n'est PAS dans 'autres en baisse'")

    # ---- Bug #1 : top10 tiré de others_down (= baisse), captifs exclus ----
    others_down = cats["baisse"]
    top10 = others_down.nsmallest(10, "Variation")
    top10_names = _names(top10)
    chk("SOLIBRA" not in top10_names,
        "Top10 baisse N'INCLUT PAS le captif SOLIBRA")
    chk({"AUTRE BAISSE 1", "AUTRE BAISSE 2"}.issubset(top10_names),
        "Top10 baisse inclut les vrais 'autres en baisse'")
    chk(top10_names.issubset(_names(others_down)),
        "Tous les clients du Top10 appartiennent au groupe 'autres en baisse'")
    # cohérence total affiché vs périmètre du top10 (inclut le client blacklisté)
    total_loss = int(others_down["Variation"].sum())
    chk(total_loss == -450,
        f"Total baisse 'autres' = somme others_down (attendu -450, obtenu {total_loss})")

    # ---- parité commentaire vs bloc d'analyse : pas de filtre liste noire ----
    # ENI CI est dans excluded_clients.json ; il DOIT compter dans la baisse,
    # comme dans update_analyse_group (sinon l'en-tête commentaire diverge).
    from Insight_generation import _is_excluded_client
    chk(_is_excluded_client("ENI CI"),
        "ENI CI est bien dans la liste noire (sanity)")
    chk("ENI CI" in baisse,
        "Client blacklisté en baisse compté dans 'autres en baisse' (parité commentaire/analyse)")

    # ---- helpers d'arrondi (half-up) ----
    chk(round_half_up(94.5) == 95 and round_half_up(2.5) == 3,
        "round_half_up: 0,5 -> arrondi supérieur (pas bancaire)")
    chk(list(series_round_half_up(pd.Series([94.4, 94.5, 94.98]))) == [94.0, 95.0, 95.0],
        "series_round_half_up vectorisé cohérent")

    ok = sum(1 for c, _ in checks if c)
    for passed, msg in checks:
        print(f"  [{'OK ' if passed else 'ECHEC'}] {msg}")
    print(f"\n{ok}/{len(checks)} vérifications passées.")
    if ok != len(checks):
        raise SystemExit(1)
    print("SMOKE TESTS OK")


if __name__ == "__main__":
    run()
