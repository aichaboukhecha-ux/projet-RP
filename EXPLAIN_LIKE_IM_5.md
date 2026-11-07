# The code explained like you are 5

## The game

You are a little worker in a room. There are boxes on the floor and some
special squares (the targets). You must push every box onto a target.

- You can only **push**, never pull.
- You can push only **one box** at a time.
- A box cannot go through a wall or another box.

That is all. The code is just a way to teach a computer to play this game
and to find the answer by itself.

---

## `boxgame.py` - the rules of the game

**The board** is a list of text lines. Each letter is a thing:

| Letter | What it is |
|---|---|
| `O` | wall |
| `R` | the player |
| `B` | a box |
| `S` | a target |
| `.` | the player standing on a target |
| `*` | a box already on a target |
| (space) | empty floor |

`parse_board` reads these lines and builds the game.

**`SokobanPuzzle`** is one photo of the game at one moment: where the player is
and where the boxes are. The walls and targets never move, so they are the
same in every photo.

It knows three things:

- `isGoal()` - "are all targets covered by a box?"
- `successorFunction()` - "what are all the moves I can do now?" For each of
  the 4 directions it checks the rules (wall? box behind the box?) and, if the
  move is allowed, gives back the new photo.
- `stateKey()` - a name for the photo, so the computer can say "I already saw
  this one".

**`Node`** is a step on a path. It remembers the photo, the step before it
(`parent`), the move that made it (`action`), how many moves it took (`g`) and
a score (`f`). With the parents you can walk backwards and get the whole
solution: `getPath()` gives the photos, `getSolution()` gives the moves.

---

## `search.py` - the robots that look for the answer

The computer does not "see" the solution. It tries moves, then tries moves
after moves, until the boxes are on the targets. The robots differ in *how
they choose what to try next*.

### BFS - the careful robot

It tries everything close first, then a little further, then further...
like the rings made by a stone in water. It always finds the shortest answer,
but it looks at a LOT of photos.

### A* - the robot with a compass

Before choosing, it gives each photo a score: `f = g + h`

- `g` = moves already done
- `h` = a guess of how many moves are still needed (the "compass")

It always tries the photo with the smallest score. A good compass means fewer
photos to look at. There are three compasses:

- **h1**: count the boxes that are not on a target. Simple, but weak.
- **h2** (the teacher's): count the misplaced boxes twice, and add the distance
  from each box to its closest target "as a bird flies".
- **h3** (ours): we compute the *real* number of pushes a box needs, with the
  walls in the way (a bird can fly over a wall, a box cannot). We give every
  box its own target, in the cheapest way, and we add the walk from the player
  to the nearest box that is not done.

### Deadlocks - the box that is stuck forever

If a box is pushed into a corner, nobody can ever move it again. The game is
lost, but a lazy robot would keep trying for nothing.

- **Corner**: a floor square with a wall above/below AND a wall left/right.
- **Line**: two corners on the same wall, with nothing but wall on one side.
  A box on that line can only slide along the wall, never away from it.

`dead_cells()` finds all those bad squares once. `has_deadlock()` says "a box
is on a bad square". When `use_deadlock=True`, A* throws those photos away
immediately.

### The counters

Instead of using a stopwatch, the code counts:

- **expanded** = how many photos the robot opened and explored
- **generated** = how many new photos it created

Fewer means a smarter robot.

---

## Other files

- **`levels.py`** - the list of 13 rooms (6 of ours, 5 from Figure 4, 2 from Figure 7).
- **`figure4_boards.py`, `figure7_boards.py`** - the rooms copied from the
  teacher's pictures, letter by letter.
- **`gui.py`** - the window you play with. It runs the chosen robot, then
  replays its answer move by move. `A` changes the robot, `C` shows the
  comparison table and bars.
- **`benchmark.py`** - makes all 5 robots solve all 7 rooms and writes the
  scores in `benchmark.csv`.
- **`tests.py`** - a checker. It tries many small situations and says PASS or
  FAIL, so we know nothing is broken.
- **`report.md`** - the written report with the tables.
- **`main.py`** - the tiniest demo: solve one room and print the moves.

---

## The result in one sentence

All robots find the same shortest answer, but BFS and h1 look at tens of
thousands of photos on the hardest room, while A* with h3 (and the stuck-box
check) looks at about nine times fewer in total.
