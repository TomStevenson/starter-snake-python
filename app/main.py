import json
import os
import random
import bottle
from cheroot import wsgi

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
    snakeCoords = []

     # perimeter coordinates just outside the board
    for x in range(width):
        bad = (x, -1)
        badCoords.append(bad)
        bad = (x, height)
        badCoords.append(bad)

        bad = (x, -2)
        badCoords.append(bad)
        bad = (x, height + 1)
        badCoords.append(bad)

    for y in range(width):
        bad = (-1, y)
        badCoords.append(bad)
        bad = (width, y)
        badCoords.append(bad)

        bad = (-2, y)
        badCoords.append(bad)
        bad = (width + 1, y)
        badCoords.append(bad)

    snake_heads = []
    snake_tails = []
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
            snakeSize = len(snake["body"])
            temp = (snake["body"][snakeSize - 1]["x"], snake["body"][snakeSize - 1]["y"])
            snake_tails.append(temp)
        for xycoord in snake["body"]:
            bad = (xycoord["x"], xycoord["y"])
            snakeCoords.append(bad)
        if (snake != data["you"] and (len(snake["body"]) < shortest_length)):
            print("DEBUG: Found a shorter snake")
            shortest_snake = snake
            shortest_length = len(snake["body"])
        elif (snake != data["you"] and (len(snake["body"]) >= longest_length - 6)):
            print("DEBUG: Found a longer snake")
            longest_snake = snake
            longest_length = len(snake["body"])
            longer_snake = True

    myHead1 = data["you"]["body"][0]   

    sorted_list = get_food_list(myHead1, data)
    amountOfFood = len(sorted_list)
    first_food = sorted_list[0]
    # print("DEBUG: first food={}".format(first_food))
    
    mySize = len(data["you"]["body"])
    myTail = data["you"]["body"][mySize-1]

    # get coordinates of our snake head
    myHealth = data["you"]["health"]

    myHead = myHead1
    
    healthThreshold = 20
    if (amountOfFood < 10):
        healthThreshold = 30
    elif (amountOfFood < 5):
        healthThreshold = 50

    attack = 0
    if ((myHealth < healthThreshold) or (longer_snake == True)) :
        print("DEBUG: Go get food")
    elif (shortest_length < len(data["you"]["body"])):
        print("DEBUG: Chase shortest snake")
        first_food["x"] = shortest_snake["body"][0]["x"]
        first_food["y"] = shortest_snake["body"][0]["y"]
        attack = 1 
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
    if ((coord not in badCoords) and (coord not in snakeCoords)):
        possibleMoves.append("left")
    # right
    coord = (myHead["x"]+1, myHead["y"])
    if (coord not in badCoords) and (coord not in snakeCoords):
        possibleMoves.append("right") 
    # up
    coord = (myHead["x"], myHead["y"]-1)
    if (coord not in badCoords) and (coord not in snakeCoords):
        possibleMoves.append("up")
    # down
    coord = (myHead["x"], myHead["y"]+1)
    if (coord not in badCoords) and (coord not in snakeCoords):
        possibleMoves.append("down")

    print("DEBUG: PossibleMoves={}".format(possibleMoves))
    
    riskyMoves = []
    myTailCoord = (myTail["x"], myTail["y"])
    snakes = data["board"]["snakes"]

    print("RISK UP")
    riskUp = check_risk(myHead["y"] - 3, myHead["y"], myHead["x"] - 3, myHead["x"] + 3, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 0)
    print("RiskUp 1 = {}".format(riskUp))
    #check this
    riskUp1 = count_empty(0, myHead["y"], myHead["x"], myHead["y"], snakeCoords, myTailCoord, snake_tails, snake_heads, 1)
    print("RiskUp 2 = {}".format(riskUp1))

    riskUp2 = 0
    if (myHead["y"] <= 2):
        riskUp2 += 0.1

    tup = ('up', riskUp + riskUp1 + riskUp2)
    riskyMoves.append(tup)
    
    print("RISK DOWN")
    riskDown = check_risk((myHead["y"]) + 1, myHead["y"] + 4, myHead["x"] - 3, myHead["x"] + 3, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 0)
    print("RiskDown 1 = {}".format(riskDown))
    riskDown1 = count_empty(myHead["y"] + 1, height, myHead["x"], height - myHead["y"] - 1, snakeCoords, myTailCoord, snake_tails, snake_heads, 1)
    print("RiskDown 2 = {}".format(riskDown1))

    riskDown2 = 0
    if (myHead["y"] > height - 3):
        riskDown2 += 0.1

    tup = ('down', riskDown + riskDown1 + riskDown2)
    riskyMoves.append(tup)
    
    print("RISK LEFT")
    riskLeft = check_risk(myHead["x"] - 4, myHead["x"] - 1, myHead["y"]-3, myHead["y"]+3, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 1)
    print("RiskLeft 1 = {}".format(riskLeft))
    riskLeft1 = count_empty(0, myHead["x"], myHead["y"], myHead["x"], snakeCoords, myTailCoord, snake_tails, snake_heads, 0) 
    print("RiskLeft 2 = {}".format(riskLeft1))

    riskLeft2 = 0
    if (myHead["x"] <= 2):
        riskLeft2 += 0.1

    tup = ('left', riskLeft + riskLeft1 + riskLeft2)
    riskyMoves.append(tup)
    
    print("RISK RIGHT")
    riskRight = check_risk(myHead["x"] + 1, myHead["x"] + 4, myHead["y"]-3, myHead["y"]+3, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 1)
    print("RiskRight 1 = {}".format(riskRight))
    riskRight1 = count_empty(myHead["x"] + 1, width, myHead["y"], width - myHead["x"] - 1, snakeCoords, myTailCoord, snake_tails, snake_heads, 0)
    print("RiskRight 2 = {}".format(riskRight1))

    riskRight2 = 0
    if (myHead["x"] > width - 3):
        riskRight2 += 0.1

    tup = ('right', riskRight + riskRight1 + riskRight2)
    riskyMoves.append(tup)
    
    riskyMoves.sort(key=lambda x: x[1])
   
    print("DEBUG: Risky Moves: {}".format(riskyMoves))

    # final decision
    direction = None
    
    # preferredMove
    preferredDirection = None
    for pm in preferredMoves:
        if pm in possibleMoves:
            preferredDirection = pm
            print("DEBUG: Preferred direction = {}".format(preferredDirection))
            break

    # least risk           
    leastRisk = None
    for lrm in riskyMoves:
        if lrm[0] in possibleMoves:
            leastRisk = lrm[0]
            leastRiskScore = lrm[1]
            print("DEBUG: least risk move: {}".format(leastRisk))
            break

    pms = -1
    direction = leastRisk
    if (preferredDirection != None):
        for rrr in riskyMoves:
            if (rrr[0] == preferredDirection):
                pms = rrr[1]
                break
            #<0.2 beats schnake so
        if ((pms != -1) and (pms < 0.25)):
            direction = preferredDirection
            print("DEBUG: choosing preferred direction: {}".format(direction))

    #if (myHealth < 20):
    #    print("Getting hungry - forcing preferred direction")
    #    direction = preferredDirection
    
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

#riskUp = check_risk(0, int(myHead["y"]) - 1, myHead["x"] - 2, myHead["x"] + 2, badCoords, snakeCoords)
#riskLeft = check_risk1(0, int(myHead["x"] - 1), int(myHead["y"]-2), int(myHead["y"]+2), badCoords, snakeCoords)
#count_empty(int(myHead["y"]), 0, myHead["x"], height, snakeCoords)
#UP count_empty(int(myHead["y"]), 0, myHead["x"], height, snakeCoords, myTailCoord, 1)
def count_empty(aFrom, aTo, b, total, snakeCoords, myTail, snake_tails, snake_heads, mode):
    emptyCount = 0
    #print("DEBUG RISK 1")
    #print("aFrom={}".format(aFrom))
    #print("aTo={}".format(aTo))
    #print("b={}".format(b))
    loopCounter = 0

    for x in range(aFrom, aTo):
        loopCounter += 1
        if (mode > 0):
            testCoord = (b, x)
            #print ("testCoord1:{}".format(testCoord))
        else:
            testCoord = (x, b)
            #print ("testCoord2:{}".format(testCoord))
        
        if (testCoord not in snakeCoords):
            emptyCount += 1
        else:
            #print("DEBUG: we have encountered a snake part - stop counting")
            total = loopCounter
            break
    
    ratio = 0
    if (emptyCount == 0):
        #print("EmptyCount = 0 !")
        ratio
    else:
        ratio = total / emptyCount

    if (ratio >= 0.8) and (ratio <= 1.2):
        #print("ratio = 0.8-1.2, so set to zero - no risk")
        ratio = 0

    ratio = ratio

    #print ("EmptyCount:{}".format(emptyCount))
    #print ("Total:{}".format(total))
    #print ("Ratio:{}".format(ratio))

    return ratio


def check_risk(a1, a2, b1, b2, badCoords, snakeCoords, me, sh, snakes, mode):
    risk = 0
    heads = 0
    area = abs(a2 - a1) * abs(b2 - b1)
    print ("Desired Area = {}".format(area))
    for first_loop in range(b1, b2):
        for second_loop in range(a1, a2):
            if (mode > 0):
                testCoord = (second_loop, first_loop)
            else:
                testCoord = (first_loop, second_loop)
            if (testCoord in snakeCoords):
                    risk += 1
                    #print("DEBUG: +1 to risk - other snake")
    if (risk > 0):
        riskFactor = risk / area
        riskFactor = riskFactor + heads
        #if (riskFactor < 0.1):
            #riskFactor = 0
    else:
        riskFactor = 0
    return riskFactor

class CherryPyServer(bottle.ServerAdapter):
    def run(self, handler):
        server = wsgi.Server((self.host, self.port), handler)
        try:
            server.start()
        finally:
            server.stop()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

def main():
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True),
        server=CherryPyServer
    )

if __name__ == '__main__':
    main()