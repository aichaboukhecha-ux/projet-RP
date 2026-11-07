# Les 2 plateaux de la Figure 7 (sujet Part 3, page 7).
# O mur, R joueur, B caisse, S cible, . joueur sur cible, * caisse sur cible

FIGURE7 = {
    "exemple1": [
        "OOOOOOO",
        "OS O RO",
        "O  OB O",
        "OS  B O",
        "O  OB O",
        "OS O  O",
        "OOOOOOO",
    ],
    "exemple2": [
        "OOOOOOOO",
        "OSSS OOO",
        "O S B  O",
        "O  BBB O",
        "OOOO  RO",
        "OOOOOOOO",
    ],
}

FIGURE7_ORDER = ["exemple1", "exemple2"]


def boards():
    for name in FIGURE7_ORDER:
        yield name, FIGURE7[name]
