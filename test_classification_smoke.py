"""Smoke tests pour la classification FOCUS AGL / commentaires PPTX.

Couvre trois comportements :

Bug #2 — seuil captif (100 % PDM) testé sur la PDM ARRONDIE affichée :
    un client à 416/438 = 94,98 % (affiché « 95 % ») doit être classé captif,
    pas dans « autres clients ».

En-tête commentaire — « Nous notons que les Volumes d'AGL sont en baisse (X) » :
    X = somme de TOUTES les baisses « autres » (others_down), SANS filtre liste
    noire (identique au bloc d'analyse update_analyse_group). Donc les clients
    blacklistés (mines, ministères) COMPTENT dans ce total.

Top 10 « Principaux Acteurs de cette Baisse » (comportement historique) :
    clients en baisse chez AGL ALORS QUE leur marché progresse
    (Variation < 0 ET Var_Marche > 0). Pas de filtre liste noire : les clients
    hors périmètre (mines…) ont un marché en baisse et sortent via Var_Marche>0.

Lancement : python test_classification_smoke.py
"""
import pandas as pd

from Insight_generation import (_categorize_clients, _is_excluded_client,
                                 round_half_up, series_round_half_up)

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
        # --- frontières d'arrondi ---
        _row("FRONTIERE 944", 944, 1000, 944, 1000),                 # 94.4% -> 94 -> autres
        _row("FRONTIERE 945", 945, 1000, 945, 1000),                 # 94.5% -> 95 -> captif

        # --- captif en baisse : PDM >= 95 % les deux années ---
        _row("CAPTIF BAISSE", 1000, 1000, 950, 1000),                # 100%/95%, var -50 -> captive_down

        # --- décliners AGL dont LE MARCHÉ PROGRESSE -> doivent peupler le top10 ---
        _row("SOLIBRA", 1000, 1000, 800, 1300),                      # var -200, Var_Marche +300, 61% cur -> non captif
        _row("AUTRE BAISSE MARCHE UP", 500, 600, 300, 900),          # var -200, Var_Marche +300, non captif

        # --- décliners AGL dont LE MARCHÉ BAISSE -> hors top10 (Var_Marche<0) ---
        # mine blacklistée : compte dans l'en-tête (pas de filtre liste noire)
        # mais sort du top10 via Var_Marche < 0.
        _row("STE DES MINES D'ITY", 200, 400, 100, 300),             # var -100, Var_Marche -100, blacklisté
        _row("ENI CI", 100, 200, 50, 150),                           # var -50, Var_Marche -50, blacklisté

        # --- 100 % concurrent (AGL=0 les deux années) : exclu du périmètre AGL ---
        _row("CONCURRENT PUR", 0, 500, 0, 500),
    ]
    return pd.DataFrame(rows)


def _names(df):
    return set(df[CLIENT].tolist())


def _replicate_top10(comp):
    """Réplique la logique du top10 de update_comments_text (Insight_generation)."""
    c = comp.copy()
    c['Variation'] = c[f"AGL_Volume_{CUR}"] - c[f"AGL_Volume_{PRV}"]
    c['Var_Marche'] = c[f"Total_Marche_{CUR}"] - c[f"Total_Marche_{PRV}"]
    return c[(c['Variation'] < 0) & (c['Var_Marche'] > 0)].nsmallest(10, 'Variation')


def run():
    comp = _build()
    cats = _categorize_clients(comp, CLIENT, CUR, PRV)

    captive_up = _names(cats["captive_up"])
    captive_down = _names(cats["captive_down"])
    captive = captive_up | captive_down
    hausse = _names(cats["hausse"])
    baisse = _names(cats["baisse"])  # = others_down (non captifs en baisse, sans liste noire)

    checks = []

    def chk(cond, msg):
        checks.append((bool(cond), msg))

    # ---- Bug #2 : classement captif sur PDM arrondie ----
    chk("STE PRODUIT ALIMENT CONGELE CI" in captive_up,
        "STE PRODUIT (94,98%->95%, var +78) classé captive_up")
    chk("STE PRODUIT ALIMENT CONGELE CI" not in hausse,
        "STE PRODUIT n'est PAS dans 'autres en hausse'")
    chk("FRONTIERE 945" in captive,
        "94,5 % -> arrondi 95 % -> captif")
    chk("FRONTIERE 944" not in captive and "FRONTIERE 944" in hausse,
        "94,4 % -> arrondi 94 % -> NON captif (autres)")
    chk("CAPTIF BAISSE" in captive_down and "CAPTIF BAISSE" not in baisse,
        "Captif en baisse classé captive_down, pas dans 'autres en baisse'")
    chk("CONCURRENT PUR" not in (captive | hausse | baisse),
        "Concurrent pur (AGL=0) exclu de toutes les catégories AGL")

    # ---- En-tête commentaire : total des baisses 'autres' SANS liste noire ----
    # others_down = SOLIBRA(-200) + AUTRE BAISSE MARCHE UP(-200)
    #             + STE DES MINES D'ITY(-100) + ENI CI(-50) = -550
    total_loss = int(cats["baisse"]["Variation"].sum())
    chk(total_loss == -550,
        f"En-tête = somme others_down sans liste noire (attendu -550, obtenu {total_loss})")
    chk(_is_excluded_client("ENI CI") and _is_excluded_client("STE DES MINES D'ITY"),
        "ENI CI et STE DES MINES D'ITY sont bien blacklistés (sanity)")
    chk({"ENI CI", "STE DES MINES D'ITY"}.issubset(baisse),
        "Clients blacklistés comptés dans l'en-tête (pas de filtre liste noire)")

    # ---- Top 10 : décliners AGL à marché en hausse, comportement historique ----
    top10 = _replicate_top10(comp)
    top10_names = _names(top10)
    chk((top10["Var_Marche"] > 0).all() and (top10["Variation"] < 0).all(),
        "Top10 : tous Variation<0 ET Var_Marche>0")
    chk({"SOLIBRA", "AUTRE BAISSE MARCHE UP"}.issubset(top10_names),
        "Top10 inclut les décliners dont le marché progresse")
    chk("STE DES MINES D'ITY" not in top10_names and "ENI CI" not in top10_names,
        "Top10 EXCLUT les clients à marché en baisse (mines/blacklist) via Var_Marche>0")
    chk("CAPTIF BAISSE" not in top10_names,
        "Top10 exclut le captif en baisse (Var_Marche non > 0)")

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
