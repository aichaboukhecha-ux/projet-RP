
Level =[
    "OOOOO",
    "ORBSO",
    "O   O",
    "OOOOO",
] 
class boxgame:
    def __init__( self, goal, walls, boxes, agent ,height ,width):
        
        self.goal =set(goal)
        self.walls=set(walls)
        self.boxes=set(boxes)
        self.agent=agent
        self.height=height
        self.width=width
        self.directions={
            "up":(-1,0),
            "down":(1,0),
            "left":(0,-1),
            "right":(0,1),
        }
    
    def inside(self,position):
        row,col=position
        return(
        0<=row<self.height and 0<=col<self.width
        )    
    
    def isgoal(self):
        return self.boxes == self.goal    
    
    def stateKey(self):
        return (self.player, tuple(sorted(self.boxes)))
def successorFunction(self):
        successors = []

        for action, move in self.directions.items():

            
            next_position = (
                self.player[0] + move[0],
                self.player[1] + move[1]
            )

            
            if not self.isInside(next_position):
                continue

            if next_position in self.walls:
                continue

            
            new_boxes = set(self.boxes)

            
            if next_position in self.boxes:

                box_destination = (
                    next_position[0] + move[0],
                    next_position[1] + move[1]
                )

                
                if not self.isInside(box_destination):
                    continue

                if box_destination in self.walls:
                    continue

                if box_destination in self.boxes:
                    continue

               
                new_boxes.remove(next_position)
                new_boxes.add(box_destination)

            
            new_player = next_position

            
            new_state = boxgame(
                self.walls,
                self.targets,
                new_player,
                new_boxes,
                self.height,
                self.width
            )

            successors.append((action, new_state))

        return successors


def parse_board(board):
    walls = set()
    targets = set()
    boxes = set()
    player = None

    height = len(board)
    width = len(board[0])

    
    for row in board:
        if len(row) != width:
            raise ValueError("All rows must have the same length.")

    
    for row in range(height):
        for col in range(width):

            symbol = board[row][col]
            position = (row, col)

            if symbol == "O":
                walls.add(position)

            elif symbol == "S":
                targets.add(position)

            elif symbol == "R":
                if player is not None:
                    raise ValueError("There must be only one player.")

                player = position

            elif symbol == "B":
                boxes.add(position)

            elif symbol == ".":
                if player is not None:
                    raise ValueError("There must be only one player.")

                player = position
                targets.add(position)

            elif symbol == "*":
                boxes.add(position)
                targets.add(position)

            elif symbol == " ":
                pass

            else:
                raise ValueError(f"Unknown symbol: {symbol}")

    if player is None:
        raise ValueError("The board must contain a player.")

    if len(boxes) != len(targets):
        raise ValueError("The number of boxes and targets must be equal.")

    return boxgame(
        walls, targets, player, boxes, height, width
    )


class Node:

    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.g = g

    def getPath(self):
        path = []
        current = self

        while current is not None:
            path.append(current.state)
            current = current.parent

        path.reverse()
        return path

    def getSolution(self):
        actions = []
        current = self

        while current.parent is not None:
            actions.append(current.action)
            current = current.parent

        actions.reverse()
        return actions


