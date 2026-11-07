# Les 5 plateaux de la Figure 4 (sujet Part 3, page 5).
# O mur, R joueur, B caisse, S cible, . joueur sur cible, * caisse sur cible

FIGURE4 = {
    "exemple1": [
        "OOOOOO",
        "OS B O",
        "O OR O",
        "O    O",
        "O    O",
        "OOOOOO",
    ],
    "exemple2": [
        "OOOOOOOOO",
        "O       O",
        "O       O",
        "O  OOO  O",
        "O    O. O",
        "O     O O",
        "O  B  O O",
        "O     O O",
        "OOOOOOOOO",
    ],
    "exemple3": [
        "OOOOOOOO",
        "O   O  O",
        "O  BR  O",
        "O   OB O",
        "OOOOO SO",
        "OOOOO SO",
        "OOOOOOOO",
    ],
    "exemple4": [
        "OOOOOOO",
        "OO  OOO",
        "OO  OOO",
        "OO *  O",
        "OOBOB O",
        "O SRS O",
        "O    OO",
        "OOO  OO",
        "OOOOOOO",
    ],
    "exemple5": [
        "OOOOOOOOO",
        "OOOSO  OO",
        "O    B OO",
        "O B R  SO",
        "OOO O OOO",
        "OOOBO OOO",
        "OOO  SOOO",
        "OOOOOOOOO",
    ],
}

FIGURE4_ORDER = ["exemple1", "exemple2", "exemple3", "exemple4", "exemple5"]


def boards():
    for name in FIGURE4_ORDER:
        yield name, FIGURE4[name]
