import json
import os
import random
import bottle

from .api import ping_response, start_response, move_response, end_response

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

@bottle.post('/start')
def start():
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    print(json.dumps(data))

    color = "#4f7942"

    return start_response(color)


def get_food_list(snake_head, data):
    food_list = data.get('food')
    closest = []
    last_score = 999999
    l = []
    for current_food in data["board"]["food"]:
        current_distance = [99, 99]
        current_distance[0] = snake_head["x"] - current_food["x"]
        current_distance[1] = snake_head["y"] - current_food["y"]
        current_distance[0] = current_distance[0] * current_distance[0]
        current_distance[1] = current_distance[1] * current_distance[1]
        current_score = current_distance[0] + current_distance[1]
        if current_score < last_score:
            closest = current_food
            last_score = current_score   
    l.append(closest) 
    return l

def get_first_common_element(x,y):
    ''' Fetches first element from x that is common for both lists
        or return None if no such an element is found.
    '''
    for i in x:
        if i in y:
            return i

    # In case no common element found, you could trigger Exception
    # Or if no common element is _valid_ and common state of your application
    # you could simply return None and test return value
    # raise Exception('No common element found')
    return None

@bottle.post('/move')
def move():
    data = bottle.request.json

    """
    TODO: Using the data from the endpoint request object, your
            snake AI must choose a direction to move in.
    """
    print(json.dumps(data))

   # Make a list of all the bad coordinates and try to avoid them
    height = data["board"]["height"]
    width = data["board"]["width"]
    badCoords = []

     # perimeter coordinates just outside the board
    for x in range(width):
        bad = (x, -1)
        badCoords.append(bad)
        bad = (x, height)
        badCoords.append(bad)

    for y in range(width):
        bad = (-1, y)
        badCoords.append(bad)
        bad = (width, y)
        badCoords.append(bad)

    snake_heads = []
    # snake bodies
    shortest_length = len(data["you"]["body"])
    shortest_snake = data["you"]
    longest_length = len(data["you"]["body"])
    longest_snake = data["you"]
    longer_snake = False
    for snake in data["board"]["snakes"]:
        if snake != data["you"]:
            temp = (snake["body"][0]["x"], snake["body"][0]["y"])
            snake_heads.append(temp)
            print(snake["body"][0])
        for xycoord in snake["body"]:
            bad = (xycoord["x"], xycoord["y"])
            badCoords.append(bad)
        if (len(snake["body"]) < shortest_length):
            print("DEBUG: Found a shorter snake")
            shortest_snake = snake
            shortest_length = len(snake["body"])
        elif (len(snake["body"]) >= longest_length):
            print("DEBUG: Found a longer snake")
            longest_snake = snake
            longest_length = len(snake["body"])
            longer_snake = True

    myHead1 = data["you"]["body"][0]   

    sorted_list = get_food_list(myHead1, data)
    first_food = sorted_list[0]
    # print("DEBUG: first food={}".format(first_food))
    
    mySize = len(data["you"]["body"])
    myTail = data["you"]["body"][mySize-1]

    # get coordinates of our snake head
    myHealth = data["you"]["health"]

    myHead = myHead1
    if ((myHealth < 20) or (longer_snake == True)) :
    #if (myHealth < 10):
        print("DEBUG: Go get food")
    elif (shortest_length < len(data["you"]["body"])):
        print("DEBUG: Chase shortest snake")
        first_food["x"] = shortest_snake["body"][0]["x"]
        first_food["y"] = shortest_snake["body"][0]["y"]       
    elif (myHead == myTail):
        print("DEBUG: starting conditions - get food")
    else:
        print("DEBUG: Chase my tail")
        first_food["x"] = myTail["x"]
        first_food["y"] = myTail["y"]

    # find smaller snake
    # NEED TO DO BAD SNAKE HEAD DETECTION

    preferredMoves = []
    coord = (myHead["x"], myHead["y"])
    if first_food["x"] < myHead["x"]:
        preferredMoves.append("left")
    elif first_food["x"] > myHead["x"]:
        preferredMoves.append("right")
    if first_food["y"] < myHead["y"]:
        preferredMoves.append("up")
    elif first_food["y"] > myHead["y"]:
        preferredMoves.append("down")
    print("DEBUG: Directions to get us to target={}".format(preferredMoves))

    possibleMoves = []
    # left
    coord = (myHead["x"]-1, myHead["y"])
    if coord not in badCoords:
        coord = (myHead["x"]-1, myHead["y"]-1)
        if coord not in snake_heads:
            coord = (myHead["x"]-1, myHead["y"]+1)
            if coord not in snake_heads:
                possibleMoves.append("left")
    # right
    coord = (myHead["x"]+1, myHead["y"])
    if coord not in badCoords:
        coord = (myHead["x"]+1, myHead["y"]-1)
        if coord not in snake_heads:
            coord = (myHead["x"]+1, myHead["y"]+1)
            if coord not in snake_heads:
                possibleMoves.append("right")
            
    # up
    coord = (myHead["x"], myHead["y"]-1)
    if coord not in badCoords:
        coord = (myHead["x"]-1, myHead["y"]-1)
        if coord not in snake_heads:
            coord = (myHead["x"]+1, myHead["y"]-1)
            if coord not in snake_heads:
                possibleMoves.append("up")
    # down
    coord = (myHead["x"], myHead["y"]+1)
    if coord not in badCoords:
        coord = (myHead["x"]+1, myHead["y"]+1)
        if coord not in snake_heads:
            coord = (myHead["x"]-1, myHead["y"]+1)
            if coord not in snake_heads:
                possibleMoves.append("down")

    print("DEBUG: PossibleMoves={}".format(possibleMoves))
    
    riskUp = 0
    riskDown = 0
    riskLeft = 0
    riskRight = 0
    # if preferred move is left, check from x coord to x = 0 for other snakes.  If other snake, mark left as risky
    for a in range(0, int(myHead["x"]) - 1):
        testCoord = (a, myHead["y"])
        if testCoord in badCoords:
            riskLeft += 1

    # if preferred move is right, check from x coord to x = max board size for other snakes.  If other snake, mark right as risky
    for b in range(int(myHead["x"]) + 1, width - 1):
        testCoord = (b, myHead["y"])
        if testCoord in badCoords:
            riskRight += 1

    # if preferred move is up, check from y coord to y = 0 for other snakes.  If other snake, mark up as risky
    for c in range(0, int(myHead["y"]) - 1):
        testCoord = (myHead["x"], c)
        if testCoord in badCoords:
            riskUp += 1
        
    # if preferred move is down, check from y coord to y = max for other snakes.  If other snake, mark down as risk
    for d in range(int(myHead["y"]) + 1, height -1):
        testCoord = (myHead["x"], d)
        if testCoord in badCoords:
            riskDown += 1
    
    riskyMoves = []
    
    if riskLeft > 0:
        if "left" in possibleMoves:
            riskyMoves.append("left")
            print("Risk Left: {}".format(riskLeft))
        
    if riskRight > 0:
        if "right" in possibleMoves:
            riskyMoves.append("right")
            print("Risk Right: {}".format(riskRight))
    
    if riskUp > 0:
        if "up" in possibleMoves:
            riskyMoves.append("up")
            print("Risk Up: {}".format(riskUp))

    if riskDown > 0:
        if "down" in possibleMoves:
            riskyMoves.append("down")
            print("Risk Down: {}".format(riskDown))
    
    print("DEBUG: Risky Moves={}".format(riskyMoves))

    
    # final decision
    direction = None
    for pm in preferredMoves:
        if pm not in riskyMoves:
            if pm in possibleMoves:
                direction = pm
                print("DEBUG: We have a preferred move !")
                break
    if direction == None:
        print("DEBUG: Choosing lowest risk option in possible moves")
        for pm in possibleMoves:
            if pm not in riskyMoves:
                direction = pm
    if direction == None:
        if len(possibleMoves):
            print("DEBUG: Choosing the first available possible move")
            direction = possibleMoves[0]

    if direction == None:
        print("DEBUG: No options left - choose RANDOM direction")
        direction = random.choice(["left", "right", "up", "down"])

    print("DEBUG: Direction={}".format(direction))

    return move_response(direction)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

    return end_response()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

def main():
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )

if __name__ == '__main__':
    main()