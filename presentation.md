# Présentation - Partie 3 : deadlocks, A* amélioré et comparaison

Ce document explique tout le projet, fichier par fichier, avec un focus sur
`search.py`, le deadlock et la complexité. Il explique aussi ce que demande
le PDF et ce que fait chaque fonction ajoutée.

---

## 1. Objectif du projet

Le projet est un solveur de Sokoban avec une interface Pygame.

Le jeu :

- le joueur se déplace d'une case à la fois ;
- il pousse les caisses, il ne peut pas les tirer ;
- une caisse ne traverse ni un mur ni une autre caisse ;
- le puzzle est résolu quand toutes les cibles sont couvertes.

Le programme transforme le jeu en graphe :

- un **état** = position du joueur + positions des caisses ;
- une **action** = un déplacement ;
- une **arête** = passage d'un état au suivant ;
- une **solution** = chemin du départ jusqu'au but.

Deux algorithmes cherchent ce chemin :

- **BFS** : exploration niveau par niveau ;
- **A*** : exploration guidée par une heuristique.

La Partie 3 ajoute :

1. la détection des deadlocks (coins et lignes) ;
2. une option dans A* pour supprimer les états condamnés ;
3. les plateaux de la Figure 7 ;
4. un benchmark sur 7 plateaux ;
5. un écran de comparaison dans l'interface ;
6. des tests automatiques.

---

## 2. Ce que dit le PDF (section D, pages 5-6)

Le PDF définit un **deadlock** comme un état du graphe de recherche à partir
duquel aucune solution n'est accessible. Il est généralement causé par une
configuration où il est impossible de pousser toutes les caisses sur les
cibles.

Si on ignore les deadlocks, on développe des sous-arbres entiers qui ne
peuvent jamais mener à une solution. L'arbre de recherche explose pour rien.

Le PDF distingue deux cas.

### 2.1 Deadlock de coin

Une caisse est bloquée sur une case qui n'est pas une cible et qui est
entourée de deux murs formant un coin : un mur sur l'axe vertical (au-dessus
ou en dessous) et un mur sur l'axe horizontal (à gauche ou à droite).

Ces cases sont les cases **rouges** de la Figure 5.

Si une caisse est poussée dans un tel coin, elle ne peut plus jamais en
sortir :

- deux directions de poussée sont bloquées par les murs ;
- pour les deux autres, le joueur devrait se placer dans un mur.

### 2.2 Deadlock de ligne

Une caisse est contre un mur et ne peut pas s'en éloigner pour rejoindre une
cible. La méthode du PDF est :

1. relier deux positions de deadlock de coin par une ligne droite
   (horizontale ou verticale) ;
2. si un côté de cette ligne est entièrement composé de murs ;
3. alors toutes les positions de la ligne sont des deadlocks.

Ces cases sont les cases **jaunes** de la Figure 6.

Pourquoi ? Une caisse sur la ligne ne peut pas être poussée
perpendiculairement : pour la pousser loin du mur, le joueur devrait se
tenir sur le mur ; pour la pousser vers le mur, la destination est un mur.
Elle ne peut donc glisser que le long de la ligne. Les deux extrémités sont
des coins morts, donc elle est bloquée partout sur la ligne.

### 2.3 Les trois tâches demandées

1. Écrire une fonction qui détermine si un état contient des caisses sur des
   positions de deadlock (coin ou ligne).
2. Utiliser cette fonction pour améliorer A* et éviter les sous-arbres
   condamnés.
3. Tester l'A* amélioré sur les deux plateaux de la Figure 7 avec
   l'heuristique 3, donner la solution et le nombre d'itérations, puis
   comparer avec les algorithmes précédents.

---

## 3. Structure du projet et rôle de chaque fichier

```
projet-RP/
|
|-- boxgame.py              modèle : état, règles, parseur, Node
|-- search.py               OPEN/CLOSED, BFS, A*, heuristiques, deadlocks
|-- levels.py               les 13 niveaux du jeu
|-- figure4_boards.py       les 5 plateaux de la Figure 4
|-- figure7_boards.py       les 2 plateaux de la Figure 7
|-- gui.py                  interface Pygame
|-- benchmark.py            lance tous les algorithmes sur tous les plateaux
|-- benchmark.csv           résultats mesurés
|-- tests.py                tests automatiques
|-- main.py                 petite démonstration console
|-- puzzle.py               ancien visualiseur simple (non utilisé)
|-- report.md               rapport écrit
|-- README.md               démarrage rapide
|-- EXPLAIN_LIKE_IM_5.md    explication courte
|-- EXPLANATION.md          explication longue, ligne par ligne
|-- SokobanFairyPuzzle.exe  jeu Windows empaqueté
|-- assets/                 images, polices, sons
|-- sfp/                    ancien dossier de build vide
```

### `boxgame.py`

Le modèle du jeu.

- `SokobanPuzzle` représente un état : joueur, caisses, murs, cibles,
  dimensions.
- `parse_board()` lit un plateau ASCII et construit un état.
- `successorFunction()` donne tous les états suivants possibles.
- `isGoal()` teste si toutes les cibles sont couvertes.
- `Node` représente un nœud de l'arbre : état, parent, action, `g`, `f`.

### `search.py`

Le cœur de la recherche.

- `Closed`, `OpenFIFO`, `OpenPriority` : les listes OPEN et CLOSED.
- `dead_cells()`, `dead_line()`, `has_deadlock()` : le détecteur de
  deadlocks.
- `bfs()` : recherche en largeur.
- `h1()`, `h2()`, `h3()` : les trois heuristiques.
- `push_distances()` : distances réelles de poussée avec les murs.
- `cheapest_assignment()` : affectation optimale caisse → cible.
- `SearchResult` : résultat + compteurs.
- `astar()` : A* avec option deadlock.

### `levels.py`

La liste des 13 niveaux :

- niveaux 1 à 6 : les niveaux originaux ;
- niveaux 7 à 11 : les plateaux de la Figure 4 ;
- niveaux 12 et 13 : les plateaux de la Figure 7.

### `figure4_boards.py` et `figure7_boards.py`

Les plateaux des figures, recopiés à la main en ASCII.
`FIGURE4_ORDER` et `FIGURE7_ORDER` fixent l'ordre.

Pour la Figure 7, exemple 2, deux cases en bas à gauche et deux cases en
haut à droite ne sont pas dessinées dans l'image. Elles sont lues comme des
murs `O`. Cela ne change pas la recherche, car le joueur ne peut pas y
aller.

### `gui.py`

L'interface Pygame.

- `Assets` charge les images et les polices.
- `Audio` charge et joue les sons et la musique.
- `SolutionPlayer` rejoue une solution pas à pas.
- les fonctions `draw_*` dessinent le plateau, le panneau, le splash et
  l'écran de comparaison.
- `run_all_algorithms()` lance les cinq algorithmes une seule fois.
- `make_player()` construit la lecture pour un algorithme donné.
- `load_level()` prépare un niveau et ses résultats.
- `main()` contient la boucle d'événements, les touches et les boutons.

### `benchmark.py`

Lance les algorithmes sur les 7 plateaux :

- BFS ;
- A* h1 ;
- A* h2 ;
- A* h3 ;
- A* h3+deadlock.

Il lance aussi A* h1+deadlock et A* h2+deadlock pour montrer l'effet du
filtre sur les heuristiques faibles.

Il imprime des tableaux et écrit `benchmark.csv`.

### `benchmark.csv`

Une ligne par plateau et par méthode. Les colonnes sont :

`board`, `method`, `cost`, `expanded`, `generated`, `closed`, `open_end`,
`max_open`, `heuristic_calls`, `deadlock_checks`, `status`, `actions`.

### `tests.py`

Les tests automatiques. Ils tournent sans fenêtre
(`SDL_VIDEODRIVER=dummy` est mis automatiquement) et affichent PASS ou FAIL.

### `main.py`

Petite démonstration console : résout le plateau par défaut avec BFS et
affiche la solution, le coût, les nœuds développés et générés, OPEN et
CLOSED.

### `puzzle.py`

Le premier visualiseur, très simple. Le jeu final est `gui.py` ; `puzzle.py`
n'est plus utilisé.

### `report.md`, `README.md`, `EXPLAIN_LIKE_IM_5.md`, `EXPLANATION.md`

- `report.md` : rapport complet avec tableaux et conclusion ;
- `README.md` : installation, commandes, touches, lecture des nombres ;
- `EXPLAIN_LIKE_IM_5.md` : explication très courte ;
- `EXPLANATION.md` : explication longue, ligne par ligne.

### `assets/` et `SokobanFairyPuzzle.exe`

`assets/` contient les images, les polices et les sons.
`SokobanFairyPuzzle.exe` est le jeu Windows empaqueté avec PyInstaller.

---

## 4. Le modèle : `boxgame.py`

### 4.1 Les symboles

| Symbole | Sens |
|---|---|
| `O` | mur |
| `R` | joueur |
| `B` | caisse |
| `S` | cible |
| `.` | joueur sur une cible |
| `*` | caisse sur une cible |
| espace | sol vide |

### 4.2 Un état

```python
class SokobanPuzzle:

    def __init__(self, targets, walls, boxes, player, height, width):
        self.targets = frozenset(targets)   # les cibles ne bougent jamais
        self.walls = frozenset(walls)       # les murs ne bougent jamais
        self.boxes = frozenset(boxes)       # les caisses de cet état
        self.player = player                # (ligne, colonne)
        self.height = height
        self.width = width
```

Un état est **immuable** : les ensembles sont des `frozenset`. Chaque
déplacement crée un nouvel état. On peut donc garder le même état dans OPEN,
dans CLOSED et dans un chemin sans risque de le modifier plus tard.

### 4.3 Les règles

```python
def successorFunction(self):
    successors = []
    for action, (dr, dc) in self.DIRECTIONS.items():   # 4 directions
        nxt = (self.player[0] + dr, self.player[1] + dc)

        if not self.isInside(nxt) or nxt in self.walls:
            continue                                   # mur ou hors grille

        new_boxes = set(self.boxes)
        if nxt in self.boxes:                          # poussée
            dest = (nxt[0] + dr, nxt[1] + dc)
            if (not self.isInside(dest) or dest in self.walls
                    or dest in self.boxes):
                continue                               # caisse bloquée
            new_boxes.remove(nxt)
            new_boxes.add(dest)

        successors.append((action, SokobanPuzzle(
            self.targets, self.walls, new_boxes, nxt,
            self.height, self.width)))
    return successors
```

Pour chaque direction :

1. on calcule la case devant le joueur ;
2. si c'est un mur ou hors grille, le mouvement est interdit ;
3. si c'est une caisse, on regarde la case derrière ;
4. si la case derrière est libre, on déplace la caisse ;
5. on crée un nouvel état avec la nouvelle position.

Il n'y a ni tir, ni saut. Le joueur ne marche jamais sur une caisse : dans
une poussée, il prend la place que la caisse vient de quitter.

### 4.4 Le but

```python
def isGoal(self):
    return self.targets <= self.boxes   # toutes les cibles ont une caisse
```

Le parseur garantit autant de caisses que de cibles. Donc si toutes les
cibles sont couvertes, toutes les caisses sont sur une cible.

### 4.5 La clé d'état

```python
def stateKey(self):
    return (self.player, tuple(sorted(self.boxes)))
```

C'est le nom unique de l'état. Le tri des caisses est important : deux états
avec les mêmes caisses dans un ordre différent doivent avoir la même clé.

### 4.6 Le parseur

```python
def parse_board(board):
    walls, targets, boxes, player = set(), set(), set(), None
    height, width = len(board), len(board[0])

    for row in board:
        if len(row) != width:
            raise ValueError("All rows must have the same length.")

    for r in range(height):
        for c in range(width):
            s, pos = board[r][c], (r, c)
            if s == "O":
                walls.add(pos)
            elif s == "S":
                targets.add(pos)
            elif s in ("R", "."):
                if player is not None:
                    raise ValueError("There must be only one player.")
                player = pos
                if s == ".":
                    targets.add(pos)
            elif s in ("B", "*"):
                boxes.add(pos)
                if s == "*":
                    targets.add(pos)
            elif s != " ":
                raise ValueError(f"Unknown symbol: {s!r}")

    if player is None:
        raise ValueError("The board must contain a player.")
    if len(boxes) != len(targets):
        raise ValueError("The number of boxes and targets must be equal.")

    return SokobanPuzzle(targets, walls, boxes, player, height, width)
```

Le parseur vérifie :

- toutes les lignes ont la même longueur ;
- il y a exactement un joueur ;
- le nombre de caisses est égal au nombre de cibles ;
- les symboles sont connus.

### 4.7 `Node`

```python
class Node:
    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state        # l'état
        self.parent = parent      # le nœud précédent
        self.action = action      # l'action qui a produit ce nœud
        self.g = g                # coût depuis le départ
        self.f = g                # f = g + h, calculé plus tard

    def setF(self, heuristic):
        self.f = self.g + heuristic(self.state)
        return self.f

    def getPath(self):
        path, cur = [], self
        while cur is not None:
            path.append(cur.state)
            cur = cur.parent
        return path[::-1]

    def getSolution(self):
        actions, cur = [], self
        while cur.parent is not None:
            actions.append(cur.action)
            cur = cur.parent
        return actions[::-1]
```

Un `Node` est une liste chaînée :

- `parent` permet de remonter jusqu'au départ ;
- `g` est le nombre d'actions déjà faites ;
- `f = g + h` est le score A* ;
- `getPath()` renvoie les états du départ au but ;
- `getSolution()` renvoie les actions du départ au but.

Comme chaque action coûte 1, `goal.g` est aussi la longueur de la solution.

---

## 5. OPEN et CLOSED

Le cours utilise deux listes :

- **OPEN** : les nœuds générés mais pas encore développés (la frontière) ;
- **CLOSED** : les nœuds déjà développés.

Algorithme général :

```
OPEN   <- [racine]
CLOSED <- {}

tant que OPEN n'est pas vide :
    n <- prendre un nœud dans OPEN
    si n est un but : retourner n
    mettre n dans CLOSED
    pour chaque successeur c de n :
        si c est nouveau : mettre c dans OPEN
```

La différence entre BFS et A* est **le nœud choisi dans OPEN** :

- BFS : le plus ancien (file FIFO) ;
- A* : celui avec le plus petit `f` (file de priorité).

### 5.1 `Closed`

```python
class Closed:
    def __init__(self):
        self.nodes = {}

    def add(self, node):
        self.nodes[node.state.stateKey()] = node

    def get(self, state):
        return self.nodes.get(state.stateKey())

    def remove(self, state):
        del self.nodes[state.stateKey()]

    def contains(self, state):
        return state.stateKey() in self.nodes
```

CLOSED est un dictionnaire :

- clé = clé d'état ;
- valeur = le nœud développé.

`remove()` sert à A* quand une meilleure route vers un état déjà fermé est
trouvée : on rouvre l'état.

### 5.2 `OpenFIFO` (BFS)

```python
class OpenFIFO:
    def __init__(self):
        self.queue = deque()
        self.keys = set()

    def push(self, node):
        self.queue.append(node)
        self.keys.add(node.state.stateKey())

    def pop(self):
        node = self.queue.popleft()
        self.keys.discard(node.state.stateKey())
        return node

    def contains(self, state):
        return state.stateKey() in self.keys
```

`deque` permet d'ajouter à droite et de retirer à gauche en O(1).
`keys` permet de savoir rapidement si un état est déjà dans OPEN.

FIFO = premier entré, premier sorti. C'est ce qui donne l'exploration niveau
par niveau.

### 5.3 `OpenPriority` (A*)

```python
class OpenPriority:
    def __init__(self):
        self.heap = []
        self.live = {}
        self.tie = count()

    def push(self, node):
        self.live[node.state.stateKey()] = node
        heappush(self.heap, (node.f, next(self.tie), node))

    def pop(self):
        while self.heap:
            _, _, node = heappop(self.heap)
            key = node.state.stateKey()
            if self.live.get(key) is node:      # ignorer les vieilles entrées
                del self.live[key]
                return node
        return None
```

- `heap` est un tas min sur `f`.
- `live` garde le seul nœud valide pour chaque état.
- `tie` est un compteur unique pour départager deux `f` égaux.
- Quand une meilleure route est trouvée, on pousse un nouveau nœud ; l'ancien
  reste dans le tas mais est ignoré grâce à `live.get(key) is node`.

Complexité : `push` et `pop` en O(log N), `get` et `contains` en O(1)
moyen.

---

## 6. Deadlock : les fonctions ajoutées

### 6.1 `dead_cells(state)` : trouver toutes les cases mortes

```python
def dead_cells(state):
    walls, targets = state.walls, state.targets
    corners = set()
    for row in range(state.height):
        for col in range(state.width):
            pos = (row, col)
            if pos in walls or pos in targets:
                continue                    # une cible n'est jamais morte
            vertical = (row - 1, col) in walls or (row + 1, col) in walls
            horizontal = (row, col - 1) in walls or (row, col + 1) in walls
            if vertical and horizontal:
                corners.add(pos)            # un mur sur chaque axe = coin

    dead = set(corners)
    for a in corners:
        for b in corners:
            if a < b:                       # chaque paire une seule fois
                dead |= dead_line(a, b, walls, targets)
    return frozenset(dead)
```

Étapes :

1. parcourir toutes les cases ;
2. ignorer les murs et les cibles ;
3. ajouter les coins ;
4. initialiser `dead` avec les coins ;
5. tester chaque paire de coins avec `dead_line` ;
6. renvoyer un `frozenset` réutilisable.

Cette fonction ne dépend pas du joueur ni des caisses. Elle est calculée
**une seule fois par niveau**, puis passée à tous les appels.

### 6.2 `dead_line(a, b, walls, targets)` : tester une ligne

```python
def dead_line(a, b, walls, targets):
    if a[0] == b[0]:                        # même ligne
        cells = [(a[0], col) for col in range(a[1], b[1] + 1)]
        sides = [(-1, 0), (1, 0)]           # au-dessus et en dessous
    elif a[1] == b[1]:                      # même colonne
        cells = [(row, a[1]) for row in range(a[0], b[0] + 1)]
        sides = [(0, -1), (0, 1)]           # à gauche et à droite
    else:
        return set()                        # coins non alignés

    if len(cells) < 3:
        return set()                        # il faut au moins une case entre
    if any(p in walls or p in targets for p in cells):
        return set()                        # un mur ou une cible coupe la ligne
    for dr, dc in sides:
        if all((r + dr, c + dc) in walls for r, c in cells):
            return set(cells)               # un côté entièrement mur
    return set()
```

Conditions :

- les deux coins sont sur la même ligne ou la même colonne ;
- il y a au moins une case entre eux (`len(cells) >= 3`) ;
- aucun mur et aucune cible sur la ligne ;
- un des deux côtés parallèles est entièrement mur.

Si tout est vrai, toutes les cases de la ligne sont mortes.

### 6.3 `has_deadlock(state, dead=None)` : tester un état

```python
def has_deadlock(state, dead=None):
    if dead is None:
        dead = dead_cells(state)            # calcul si non fourni
    return any(box in dead and box not in state.targets
               for box in state.boxes)      # une caisse sur cible est OK
```

La fonction renvoie `True` si au moins une caisse est sur une case morte
**et** que cette case n'est pas une cible.

Le paramètre `dead` permet de réutiliser l'ensemble calculé une fois. A*
l'utilise ainsi :

```python
if use_deadlock and dead is None:
    dead = dead_cells(initial_state)    # un seul ensemble pour toute la recherche
```

### 6.4 Intégration dans A*

`astar(..., use_deadlock=False)` garde l'ancien comportement.

Avec `use_deadlock=True` :

1. on calcule `dead` une fois au départ ;
2. on teste l'état racine ;
3. on teste chaque successeur avant de le mettre dans OPEN ;
4. on jette les successeurs morts.

```python
if use_deadlock:
    deadlock_checks += 1
    if has_deadlock(child_state, dead):
        continue                # caisse sur case morte : état condamné
```

Le filtre ne retire que des états qui ne peuvent pas atteindre un but. Le
coût optimal ne change donc pas.

Le compteur `deadlock_checks` permet de mesurer le travail du filtre.

### 6.5 Les cases mortes des plateaux de la Figure 7

| Plateau | Cases rouges (coins) | Cases jaunes (lignes) |
|---|---|---|
| Figure 7 / Exemple 1 | `(1,2) (1,4) (1,5) (5,2) (5,4) (5,5)` | `(2,5) (3,5) (4,5)` |
| Figure 7 / Exemple 2 | `(1,4) (2,6) (3,1) (4,4) (4,6)` | `(3,6) (4,5)` |

Les tests vérifient :

- chaque case rouge ;
- chaque case jaune ;
- l'égalité exacte avec l'union (aucune case morte en plus) ;
- le cas négatif : une caisse sur une cible dans un coin n'est **pas** un
  deadlock.

### 6.6 Complexité du deadlock

Avec :

- `H*W` = nombre de cases ;
- `C` = nombre de coins ;
- `L` = longueur de la plus longue ligne ;
- `B` = nombre de caisses.

| Fonction | Temps | Mémoire |
|---|---|---|
| `dead_cells` | O(H*W + C² * L) | O(H*W) |
| `dead_line` | O(L) | O(L) |
| `has_deadlock` | O(B) | O(1) |

L'ensemble est construit une fois par niveau. La vérification est une
recherche par caisse.

### 6.7 Limites du détecteur

Le détecteur implémente exactement la définition du PDF : coins et lignes.
Il ne détecte pas :

- un bloc 2x2 de caisses impossible à séparer ;
- une caisse bloquée par une autre caisse sans être dans un coin ;
- un deadlock de gel avec plusieurs caisses.

Ces cas ne sont pas demandés dans la section D. Le détecteur reste sûr :
quand il dit « mort », l'état est vraiment mort ; quand il dit « pas mort »,
l'état peut quand même être mort pour une raison plus complexe, et la
recherche l'explorera simplement.

---

## 7. BFS

### 7.1 Le code

```python
def bfs(initial_state, stats=None, node_limit=DEFAULT_NODE_LIMIT):
    root = Node(initial_state)
    open_list, closed = OpenFIFO(), Closed()    # frontière + visités
    open_list.push(root)
    generated, expanded, max_open = 1, 0, 1     # la racine est générée
    limit_reached = False
    goal = None

    while len(open_list) > 0:
        if node_limit is not None and expanded >= node_limit:
            limit_reached = True                # arrêt propre
            break

        node = open_list.pop()                  # FIFO : le plus ancien
        expanded += 1

        if node.state.isGoal():                 # test du but au développement
            goal = node
            break

        closed.add(node)
        for action, child_state in node.state.successorFunction():
            if child_state in open_list or child_state in closed:
                continue                        # état déjà vu
            open_list.push(Node(child_state, node, action, node.g + 1))
            generated += 1
        max_open = max(max_open, len(open_list))

    if stats is not None:
        stats.update(generated=generated, limit_reached=limit_reached,
                     open_size=len(open_list), closed_size=len(closed),
                     max_open=max_open)
    return goal, expanded
```

### 7.2 Pourquoi BFS est optimal

Toutes les actions coûtent 1. BFS développe d'abord tous les états à
distance 0, puis ceux à distance 1, puis 2, etc. Le premier but sorti de
OPEN est donc à la distance minimale.

### 7.3 Les compteurs

- **expanded** : nœuds sortis de OPEN et traités ;
- **generated** : nœuds créés et acceptés (la racine compte pour 1) ;
- **open_size** : nœuds restant dans OPEN à la fin ;
- **closed_size** : nœuds dans CLOSED à la fin ;
- **max_open** : taille maximale de OPEN (pression mémoire).

### 7.4 Limite de nœuds

`DEFAULT_NODE_LIMIT = 400000`.

Ce n'est pas un temps : c'est un nombre de développements. Si la limite est
atteinte, la recherche s'arrête et renvoie `limit_reached = True`. Le
benchmark écrit `LIMIT`, l'interface affiche `LIMIT REACHED`.

Il n'y a aucun délai en secondes dans le solveur. Les résultats ne dépendent
donc pas de la vitesse de la machine.

---

## 8. Les heuristiques

Une heuristique `h(state)` estime le nombre d'actions restantes.
A* utilise :

```
f = g + h
```

- `g` = actions déjà faites ;
- `h` = estimation des actions restantes.

Une heuristique est **admissible** si elle ne surestime jamais le coût réel.
Avec une heuristique admissible, A* est optimal.

### 8.1 h1 : caisses mal placées

```python
def h1(state):
    return len(state.boxes - state.targets)     # caisses mal placées
```

Chaque caisse mal placée a besoin d'au moins une poussée. h1 est donc
admissible, mais faible : elle ignore la distance et la position du joueur.

### 8.2 h2 : distance + pénalité

```python
def h2(state):
    misplaced = len(state.boxes - state.targets)
    distances = 0
    for box in state.boxes:
        distances += min(abs(box[0] - t[0]) + abs(box[1] - t[1])
                         for t in state.targets)
    return 2 * misplaced + distances            # le 2x rend h2 non admissible
```

La distance de Manhattan est une borne inférieure : une caisse a besoin d'au
moins une poussée par unité de distance.

Le terme `2 * misplaced` est une pénalité supplémentaire. Il n'est pas
justifié par une borne inférieure. Sur le petit plateau

```
OOOOO
OS BR
OOOOO
```

le coût optimal est 2, mais h2 = 4. h2 est donc **non admissible**. Elle peut
accélérer certains plateaux, mais elle n'offre aucune garantie d'optimalité.

### 8.3 h3 : distances réelles de poussée + marche du joueur

h3 est l'heuristique la plus forte du projet. Elle a trois parties.

#### Partie 1 : distances réelles de poussée

L'ancienne version utilisait la distance de Manhattan. Mais une caisse ne
peut pas traverser un mur. La nouvelle version calcule le nombre réel de
poussées nécessaires pour amener une caisse à une cible, murs compris.

```python
push_tables = {}

def push_distances(state):
    key = (state.walls, state.targets)
    if key in push_tables:
        return push_tables[key]             # même plateau : on réutilise

    tables = {}
    for target in state.targets:
        dist = {target: 0}
        queue = deque([target])             # recherche inverse : cible -> cases
        while queue:
            row, col = queue.popleft()
            for dr, dc in state.DIRECTIONS.values():
                box = (row - dr, col - dc)      # caisse avant la poussée
                player = (row - 2 * dr, col - 2 * dc)  # joueur derrière
                if box in dist or not state.isInside(player):
                    continue
                if box in state.walls or player in state.walls:
                    continue
                dist[box] = dist[(row, col)] + 1
                queue.append(box)
        tables[target] = dist
    push_tables[key] = tables
    return tables
```

Principe :

- on part de la cible avec une distance 0 ;
- si une caisse est en `(row, col)`, pour l'avoir poussée là avec la
  direction `(dr, dc)`, elle était en `(row - dr, col - dc)` et le joueur
  était en `(row - 2*dr, col - 2*dc)` ;
- si ces deux cases ne sont pas des murs, on peut reculer d'une poussée ;
- on stocke `dist[box] = dist[(row, col)] + 1`.

Le résultat ignore les autres caisses et la vraie accessibilité du joueur.
C'est donc une **borne inférieure**, ce qui est parfait pour l'admissibilité.

Le tableau est mis en cache par `(walls, targets)` : il est calculé une fois
par plateau, pas une fois par état.

#### Partie 2 : affectation caisse → cible

Chaque caisse doit finir sur une cible différente. Prendre la cible la plus
proche pour chaque caisse peut donner deux caisses sur la même cible. Le code
résout le vrai problème d'affectation par programmation dynamique.

```python
def cheapest_assignment(costs):
    size = len(costs)
    best = {0: 0}                   # masque 0 = aucune cible utilisée
    for box in range(size):
        following = {}
        for used, total in best.items():
            for target in range(size):
                if used >> target & 1:
                    continue        # cible déjà prise
                new_used = used | 1 << target
                new_total = total + costs[box][target]
                if new_total < following.get(new_used, float("inf")):
                    following[new_used] = new_total
        best = following
    return best[(1 << size) - 1]    # toutes les cibles utilisées
```

- `used` est un masque binaire : le bit `i` vaut 1 si la cible `i` est prise.
- `best[used]` est le coût minimum pour les caisses déjà traitées.
- Pour chaque nouvelle caisse, on essaie toutes les cibles libres.
- On garde le meilleur coût pour chaque nouveau masque.

C'est exact : toutes les affectations sont considérées, mais chaque
sous-problème n'est calculé qu'une fois.

#### Partie 3 : marche du joueur

```python
def h3(state):
    tables = push_distances(state)      # cache : une fois par plateau
    boxes = list(state.boxes)
    targets = list(state.targets)
    costs = [[tables[t].get(b, UNREACHABLE) for t in targets] for b in boxes]
    pushes = cheapest_assignment(costs) # chaque caisse a une cible différente

    misplaced = [b for b in boxes if b not in state.targets]
    if not misplaced:
        return pushes
    row, col = state.player
    walk = min(abs(row - b[0]) + abs(col - b[1]) for b in misplaced) - 1
    return pushes + max(walk, 0)        # poussées + marche vers la 1re caisse
```

Le joueur doit d'abord marcher jusqu'à une caisse avant de la pousser. La
distance de Manhattan du joueur à la caisse mal placée la plus proche, moins
1 (être adjacent suffit pour pousser), est une borne inférieure des
déplacements avant la première poussée. On la borne à 0.

On peut additionner les deux parties car elles comptent des actions
différentes :

- les poussées ;
- les déplacements avant la première poussée.

`UNREACHABLE = 1000` est utilisé quand une caisse ne peut pas du tout
atteindre une cible. C'est plus grand que tout coût réel sur ces plateaux,
donc cela agit comme l'infini. Sur un plateau dont la solution optimale
demande plus de 1000 poussées, cette constante pourrait surestimer et casser
l'admissibilité ; les plateaux du projet sont très loin de cette limite.

#### h3 sur les départs de la Figure 7

| Plateau | h1 | h2 | h3 | coût réel |
|---|---|---|---|---|
| Figure 7 / Exemple 1 | 3 | 17 | 16 | 41 |
| Figure 7 / Exemple 2 | 4 | 19 | 17 | 55 |

#### Complexité de h3

| Partie | Temps | Mémoire | Quand |
|---|---|---|---|
| `push_distances` | O(T * H * W) | O(T * H * W) | une fois par plateau |
| `cheapest_assignment` | O(B² * 2^B) | O(2^B) | à chaque appel de h3 |
| marche du joueur | O(B) | O(1) | à chaque appel de h3 |

Sur les plateaux du projet, `B <= 4`, donc `2^B <= 16`. Le coût est petit.

---

## 9. A*

### 9.1 Le principe

A* choisit toujours le nœud avec le plus petit `f = g + h`.

- `g` = coût déjà payé ;
- `h` = estimation du reste ;
- `f` = estimation du coût total.

Si `h` est admissible, A* trouve le chemin optimal.

### 9.2 `SearchResult`

```python
class SearchResult(tuple):
    """(goal_node, expanded) plus les autres compteurs."""

    def __new__(cls, goal_node, expanded, generated=0, limit_reached=False,
                heuristic_calls=0, deadlock_checks=0, open_size=0,
                closed_size=0, max_open=0):
        result = super().__new__(cls, (goal_node, expanded))
        result.generated = generated
        result.limit_reached = limit_reached
        result.heuristic_calls = heuristic_calls
        result.deadlock_checks = deadlock_checks
        result.open_size = open_size        # nœuds restants dans OPEN
        result.closed_size = closed_size    # nœuds dans CLOSED
        result.max_open = max_open          # plus grand OPEN
        return result
```

`SearchResult` est un tuple de deux valeurs, donc l'ancien code fonctionne
toujours :

```python
goal, expanded = astar(...)
```

Il porte aussi les compteurs :

- `generated` ;
- `limit_reached` ;
- `heuristic_calls` ;
- `deadlock_checks` ;
- `open_size` ;
- `closed_size` ;
- `max_open`.

### 9.3 Le code de `astar`

```python
def astar(initial_state, heuristic=h1, node_limit=DEFAULT_NODE_LIMIT,
          use_deadlock=False, dead=None):
    if use_deadlock and dead is None:
        dead = dead_cells(initial_state)    # un seul ensemble

    root = Node(initial_state)
    root.setF(heuristic)
    heuristic_calls = 1
    deadlock_checks = 0
    open_list, closed = OpenPriority(), Closed()

    def result(goal, expanded, generated, limit):
        return SearchResult(goal, expanded, generated, limit, heuristic_calls,
                            deadlock_checks, len(open_list), len(closed),
                            max_open)

    max_open = 1
    if use_deadlock:
        deadlock_checks += 1
        if has_deadlock(root.state, dead):
            return result(None, 0, 1, False)  # départ déjà perdu

    open_list.push(root)
    expanded, generated = 0, 1

    while len(open_list) > 0:
        if node_limit is not None and expanded >= node_limit:
            return result(None, expanded, generated, True)

        node = open_list.pop()              # plus petit f
        expanded += 1

        if node.state.isGoal():             # test du but au développement
            return result(node, expanded, generated, False)

        closed.add(node)
        for action, child_state in node.state.successorFunction():
            child_g = node.g + 1

            old = open_list.get(child_state)
            if old is None:
                old = closed.get(child_state)
            if old is not None and old.g <= child_g:
                continue                    # une route au moins aussi bonne existe

            if use_deadlock:
                deadlock_checks += 1
                if has_deadlock(child_state, dead):
                    continue                # état condamné

            if closed.contains(child_state):
                closed.remove(child_state)  # rouvrir avec un meilleur g
            child = Node(child_state, node, action, child_g)
            child.setF(heuristic)
            heuristic_calls += 1
            generated += 1
            open_list.push(child)
        max_open = max(max_open, len(open_list))

    return result(None, expanded, generated, False)
```

### 9.4 Pourquoi le test `old.g <= child_g` ?

Si le même état est déjà connu avec un `g` plus petit ou égal, la nouvelle
route n'est pas meilleure : on l'ignore.

Si l'état est dans CLOSED avec un meilleur `g`, on l'ignore aussi.
Si la nouvelle route est meilleure, on met à jour OPEN ou on rouvre CLOSED.

La réouverture est nécessaire quand l'heuristique n'est pas cohérente. h2
est non admissible, donc un état peut être rouvert.

### 9.5 Le test du but

Le test du but est fait quand le nœud est **développé**, pas quand il est
généré. C'est la version classique du cours. Avec A* et une heuristique
admissible, le premier but sorti de OPEN a le coût optimal.

### 9.6 Le commutateur deadlock

`use_deadlock=False` :

- aucun ensemble mort n'est construit ;
- `deadlock_checks` reste à 0 ;
- A* se comporte comme avant.

`use_deadlock=True` :

- l'ensemble est construit une fois ;
- la racine est testée ;
- chaque enfant est testé ;
- `deadlock_checks` compte la racine et chaque enfant testé.

Le filtre est sûr : il ne retire que des états avec une caisse sur une case
morte qui n'est pas une cible. Ces états ne peuvent jamais atteindre un but.

---

## 10. Complexité

### 10.1 Notation

| Symbole | Sens |
|---|---|
| `H`, `W` | hauteur et largeur du plateau |
| `V` | nombre d'états atteignables |
| `E` | nombre de transitions |
| `b` | facteur de branchement (au plus 4) |
| `d` | profondeur de la solution |
| `B` | nombre de caisses |
| `T` | nombre de cibles |
| `C` | nombre de coins |
| `L` | longueur de la plus longue ligne |
| `N` | nombre de nœuds dans OPEN |

### 10.2 Tableau par fonction

| Fonction | Temps | Mémoire |
|---|---|---|
| `parse_board` | O(H*W) | O(H*W) |
| `successorFunction` | O(B) | O(B) par enfant |
| `stateKey` | O(B log B) | O(B) |
| `isGoal` | O(T) | O(1) |
| `Node.setF` | O(h) | O(1) |
| `getPath`, `getSolution` | O(d) | O(d) |
| `Closed.add/get/remove/contains` | O(1) moyen après la clé | O(V) |
| `OpenFIFO.push/pop` | O(1) | O(V) |
| `OpenPriority.push/pop` | O(log N) | O(N) |
| `dead_cells` | O(H*W + C² * L) | O(H*W) |
| `dead_line` | O(L) | O(L) |
| `has_deadlock` | O(B) | O(1) |
| `bfs` | O(V + E), pire O(b^d) | O(V), pire O(b^d) |
| `h1` | O(B) | O(1) |
| `h2` | O(B*T) | O(1) |
| `push_distances` | O(T*H*W) une fois | O(T*H*W) |
| `cheapest_assignment` | O(B² * 2^B) | O(2^B) |
| `h3` | O(B*T + B² * 2^B) par état | O(2^B) |
| `astar` | O(b^d) pire | O(b^d) pire |
| `run_all_algorithms` | 5 recherches par niveau | 5 résultats |

### 10.3 BFS contre A*

| | BFS | A* |
|---|---|---|
| OPEN | file FIFO | tas min sur `f` |
| Ordre | par profondeur | par coût total estimé |
| Optimal | oui, coûts unitaires | oui, si h admissible |
| Temps pire | O(b^d) | O(b^d) |
| Mémoire pire | O(b^d) | O(b^d) |
| Heuristique | non | oui |
| Effet typique | beaucoup de nœuds | moins de nœuds |

A* n'est pas automatiquement plus rapide dans le pire cas. Il est plus rapide
quand l'heuristique est informative. Sur ces plateaux, h3 est beaucoup plus
informative que h1 ou h2, et le filtre deadlock retire les états condamnés.

### 10.4 Complexité du deadlock

Construction :

```
O(H*W)        parcours des cases
+ O(C² * L)   test de chaque paire de coins
```

Vérification d'un état :

```
O(B)          une recherche par caisse
```

Mémoire :

```
O(H*W)        l'ensemble des cases mortes
```

L'ensemble est construit une fois par niveau. Le filtre est donc très bon
marché par rapport à la recherche.

---

## 11. Résultats mesurés

Les résultats viennent de `python benchmark.py`. Aucun temps en secondes :
on compte les nœuds développés et générés.

### 11.1 Nœuds développés

| Plateau | BFS | A* h1 | A* h2 | A* h3 | A* h3+deadlock |
|---|---|---|---|---|---|
| Fig. 4 Exemple 1 | 15 | 12 | 9 | **6** | **6** |
| Fig. 4 Exemple 2 | 1162 | 1106 | 749 | 196 | **196** |
| Fig. 4 Exemple 3 | 2560 | 2489 | 1443 | 353 | **353** |
| Fig. 4 Exemple 4 | 6665 | 5476 | 3098 | 878 | **878** |
| Fig. 4 Exemple 5 | 9430 | 7337 | 2128 | 716 | **716** |
| Fig. 7 Exemple 1 | 2345 | 2313 | 2242 | 1023 | **1023** |
| Fig. 7 Exemple 2 | 54841 | 54671 | 49811 | 5334 | **5334** |

Le plus petit nombre de chaque ligne est en gras. h3 et h3+deadlock sont à
égalité sur les nœuds développés. Pourquoi ? Parce que h3 donne déjà un `f`
énorme aux états morts : ils restent au fond de OPEN et ne sont
généralement pas développés. Le filtre évite surtout de les **générer**.

### 11.2 Totaux sur les 7 plateaux

| Méthode | Expanded | Generated |
|---|---|---|
| BFS | 77018 | 78893 |
| A* h1 | 73404 | 75330 |
| A* h2 | 59480 | 62618 |
| A* h3 | 8506 | 10388 |
| A* h3+deadlock | **8506** | **9384** |

Les appels d'heuristique et les vérifications deadlock restent enregistrés
dans `benchmark.csv`, mais ils ne font plus partie de la comparaison
affichée.

h3 développe **89,0 % de nœuds en moins** que BFS (77018 → 8506).

Le filtre deadlock ne réduit pas le nombre de nœuds développés de h3 sur ces
plateaux, mais il réduit les nœuds générés de **9,7 %** (10388 → 9384). Il
réduit aussi la taille maximale de OPEN, donc la mémoire.

### 11.3 Effet du filtre deadlock sur les heuristiques faibles

| Heuristique | Sans filtre | Avec filtre | Réduction |
|---|---|---|---|
| h1 | 73404 | 12640 | 82,8 % |
| h2 | 59480 | 9665 | 83,8 % |
| h3 | 8506 | 8506 | 0,0 % |

C'est la preuve la plus claire que le filtre fonctionne. Avec une
heuristique faible, la recherche génère beaucoup d'états morts ; le filtre
les retire et la recherche devient beaucoup plus petite. Avec h3, qui est
déjà très forte, les états morts ne sont presque jamais développés, mais le
filtre évite encore de les générer.

### 11.4 Figure 7 en détail

#### Exemple 1 (7x7)

```
OOOOOOO
OS O RO
O  OB O
OS  B O
O  OB O
OS O  O
OOOOOOO
```

| Méthode | Coût | Expanded | Generated |
|---|---|---|---|
| BFS | 41 | 2345 | 2378 |
| A* h1 | 41 | 2313 | 2354 |
| A* h2 | 41 | 2242 | 2275 |
| A* h3 | 41 | **1023** | 1141 |
| A* h3+deadlock | 41 | **1023** | 1087 |

#### Exemple 2 (8x6)

```
OOOOOOOO
OSSS OOO
O S B  O
O  BBB O
OOOO  RO
OOOOOOOO
```

| Méthode | Coût | Expanded | Generated |
|---|---|---|---|
| BFS | 55 | 54841 | 54909 |
| A* h1 | 55 | 54671 | 54802 |
| A* h2 | 55 | 49811 | 51615 |
| A* h3 | 55 | **5334** | 6367 |
| A* h3+deadlock | 55 | **5334** | 5622 |

L'exemple 2 est le plus difficile. h3 développe 90,3 % de nœuds en moins que
BFS (54841 → 5334). Le filtre réduit les nœuds générés de 11,7 %
(6367 → 5622).

### 11.5 Expanded contre generated

- **Expanded** : le nœud est sorti de OPEN et traité. C'est le vrai travail
  de la recherche.
- **Generated** : le nœud est créé et accepté dans OPEN. Il peut être
  développé plus tard, ou rester dans OPEN quand le but est trouvé.

Un nœud est généré quand il est découvert. Il est développé quand la
recherche le regarde vraiment. `Expanded` est le nombre le plus important
pour comparer les algorithmes. `Generated` montre la pression mémoire et
l'effet de l'élagage.

### 11.6 Statuts

Les 49 exécutions du benchmark actuel ont le statut `ok`. Aucune limite n'a
été atteinte et aucune recherche n'a échoué.

Le chemin de la limite est quand même testé : les tests lancent une
recherche avec `node_limit=1` et vérifient qu'elle renvoie
`limit_reached = True` et aucune solution. L'interface affiche alors
`LIMIT REACHED`.

---

## 12. Interface graphique

### 12.1 Fonctions principales

| Partie | Rôle |
|---|---|
| `Assets` | charge les images et les polices |
| `Audio` | charge et joue les sons et la musique |
| `SolutionPlayer` | rejoue une solution pas à pas |
| `Button`, `build_buttons` | boutons du panneau |
| `draw_header` | titre et numéro de niveau |
| `draw_floor_and_walls` | fond du plateau |
| `draw_decorations` | décorations |
| `draw_targets` | cibles |
| `draw_boxes` | caisses |
| `draw_player` | joueur avec direction |
| `draw_board` | assemble le plateau |
| `draw_panel` | panneau latéral |
| `draw_status_message` | messages SOLVED, NO SOLUTION, LIMIT REACHED |
| `draw_splash` | écran « Solving with 5 algorithms ... » |
| `draw_comparison` | écran de comparaison |
| `short_label` | noms courts pour les barres |
| `run_all_algorithms` | lance les 5 algorithmes une fois |
| `make_player` | construit la lecture d'un résultat |
| `load_level` | prépare un niveau et ses résultats |
| `main` | boucle d'événements, touches, boutons, plein écran |

### 12.2 Chargement d'un niveau

1. `parse_board` lit le niveau.
2. `run_all_algorithms` lance :
   - BFS ;
   - A* h1 ;
   - A* h2 ;
   - A* h3 ;
   - A* h3+deadlock.
3. Chaque résultat est stocké avec son label, sa théorie, ses compteurs et
   son but.
4. `make_player` construit la lecture de l'algorithme sélectionné.
5. Le splash est affiché pendant les recherches, donc la fenêtre ne gèle
   pas.
6. Les résultats sont gardés en mémoire. La touche `A` ne relance pas de
   recherche : elle change seulement de résultat.

### 12.3 Panneau latéral

Le panneau affiche :

- `LEVEL` : niveau courant / 13 ;
- `ALGORITHM` : BFS, A* h1, A* h2, A* h3 ou A* h3+deadlock ;
- `STEP` : étape courante / total ;
- `SOLUTION COST` : nombre d'actions ;
- `STATUS` : READY, SOLVING, PLAYING, PAUSED, SOLVED, NO SOLUTION ou
  LIMIT REACHED ;
- `EXPANDED NODES` ;
- `GENERATED NODES`.

### 12.4 Écran de comparaison

Touche `C`.

Le tableau affiche :

| Colonne | Sens |
|---|---|
| ALGORITHM | nom |
| COMPLEXITY | complexité théorique en temps |
| COST | nombre d'actions de la solution |
| EXPANDED | nœuds développés |
| GENERATED | nœuds générés |

En dessous :

- un graphique en barres pour `EXPANDED` ;
- un graphique en barres pour `GENERATED`.

Chaque barre est dessinée avec `pygame.draw.rect`, mise à l'échelle de la
plus grande valeur du graphique et étiquetée avec le nombre. Toutes les
lignes et toutes les barres ont la même couleur lavande (pas de ligne
« meilleure » mise à part). Si une exécution a
atteint la limite, le texte `limit reached` remplace la barre.

### 12.5 Touches

| Touche | Action |
|---|---|
| `SPACE` | jouer / pause |
| `R` | recommencer |
| `<` / `>` | étape précédente / suivante |
| `-` / `+` | ralentir / accélérer |
| `[` / `]` | niveau précédent / suivant |
| `1` ... `9` | aller à un niveau |
| `A` | algorithme suivant |
| `C` | ouvrir / fermer la comparaison |
| `F11` ou `F` | plein écran |
| `ESC` | fermer la comparaison, ou quitter |

Les boutons du panneau font la même chose à la souris.

---

## 13. Tests

`tests.py` tourne sans fenêtre. Il met automatiquement
`SDL_VIDEODRIVER=dummy`.

Sections :

| Section | Vérifie |
|---|---|
| 1 | ordre des niveaux, 13 niveaux, chaque niveau a une solution |
| 2 | les contrôles de vitesse accélèrent vraiment |
| 3 | les sons se déclenchent sur les bonnes actions |
| 4 | les fichiers WAV se chargent |
| 5 | géométrie de la fenêtre et du plein écran |
| 6 | la frame se dessine avec le nouveau titre |
| 7 | règles des successeurs : poussées, murs, caisses, pas de tir, pas de saut |
| 8 | `isGoal` accepte toute caisse sur toute cible |
| 9 | `Node.setF`, `getPath`, `getSolution` |
| 10 | h1, h2, h3 sur un petit plateau ; h2 est non admissible |
| 11 | A* contre BFS, `SearchResult`, limites, absence de solution |
| 12 | les cases mortes correspondent aux cases rouges/jaunes des Figures 5-6 |
| 12b | tailles et coûts optimaux des plateaux de la Figure 4 |
| 13 | les plateaux de la Figure 7 sont valides et résolus |
| 14 | sélecteur d'algorithme et écran de comparaison |
| 15 | listes OPEN et CLOSED |

Résultat actuel :

```
192 PASS
0 FAIL
ALL TESTS PASSED
```

---

## 14. Comment exécuter

Installer Pygame :

```
pip install pygame
```

Jouer :

```
python gui.py
```

Lancer les tests :

```
python tests.py
```

Lancer le benchmark :

```
python benchmark.py
```

Démonstration console :

```
python main.py
```

Ancien visualiseur :

```
python puzzle.py
```

Jeu empaqueté :

```
SokobanFairyPuzzle.exe
```

---

## 15. Fonctions ajoutées ou modifiées pour la Partie 3

| Fonction / élément | Fichier | Rôle |
|---|---|---|
| `dead_cells` | `search.py` | calcule l'ensemble des cases mortes une fois par niveau |
| `dead_line` | `search.py` | teste si une ligne entre deux coins est morte |
| `has_deadlock` | `search.py` | teste si un état contient une caisse morte |
| `astar(..., use_deadlock, dead)` | `search.py` | filtre les successeurs morts |
| `SearchResult` | `search.py` | porte `generated`, `deadlock_checks`, `open_size`, `closed_size`, `max_open` |
| `bfs(..., node_limit)` | `search.py` | limite de nœuds, pas de temps |
| `Closed` | `search.py` | liste CLOSED avec `add/get/remove/contains` |
| `OpenFIFO` | `search.py` | file OPEN de BFS |
| `OpenPriority` | `search.py` | tas OPEN de A* |
| `push_distances` | `search.py` | distances réelles de poussée, murs compris |
| `cheapest_assignment` | `search.py` | affectation optimale caisse → cible |
| `h3` | `search.py` | poussées réelles + affectation + marche |
| `FIGURE7`, `FIGURE7_ORDER`, `boards` | `figure7_boards.py` | les deux plateaux de la Figure 7 |
| `LEVELS += ...` | `levels.py` | ajout des plateaux Figure 4 et Figure 7 |
| `ALGORITHMS` | `gui.py` | les cinq algorithmes du sélecteur |
| `run_all_algorithms` | `gui.py` | lance les cinq algorithmes une fois |
| `make_player` | `gui.py` | construit la lecture d'un résultat |
| `load_level` | `gui.py` | prépare le niveau et les résultats |
| `draw_comparison` | `gui.py` | écran de comparaison |
| `short_label` | `gui.py` | noms courts des algorithmes |
| `draw_panel` | `gui.py` | affiche algorithme, expanded, generated |
| `draw_status_message` | `gui.py` | affiche LIMIT REACHED |
| `choose_algorithm` | `gui.py` | change d'algorithme sans recherche |
| `switch_level` | `gui.py` | change de niveau avec splash |
| `run_one`, `benchmark`, `write_csv` | `benchmark.py` | mesure et écrit `benchmark.csv` |
| tests sections 12, 12b, 13, 14 | `tests.py` | deadlocks, Figure 4, Figure 7, GUI |

---

## 16. Conclusion

- Le détecteur de deadlock implémente exactement la définition du PDF :
  coins (rouge) et lignes (jaune).
- Les cases trouvées correspondent exactement aux Figures 5 et 6.
- A* avec `use_deadlock=True` retire les états condamnés et garde le coût
  optimal.
- h3 est la meilleure heuristique : distances réelles de poussée,
  affectation caisse → cible et marche du joueur.
- h2 est non admissible à cause du terme `2 * misplaced`.
- Sur les 7 plateaux, h3 développe 89,0 % de nœuds en moins que BFS.
- Le filtre deadlock réduit les développements de h1 de 82,8 % et de h2 de
  83,8 %.
- Avec h3, le filtre ne change pas les développements sur ces plateaux, mais
  réduit les nœuds générés de 9,7 % et la taille maximale de OPEN.
- Les 49 exécutions du benchmark sont `ok`, sans limite atteinte.
- Les 192 tests passent, 0 échec.
