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
    #print(food_list)
    closest = []
    last_score = 999999
    l = []
    for current_food in data["board"]["food"]:
        current_distance = [99, 99]
        current_distance[0] = abs(snake_head["x"] - current_food["x"])
        current_distance[1] = abs(snake_head["y"] - current_food["y"])
        #current_distance[0] = current_distance[0] * current_distance[0]
        #current_distance[1] = current_distance[1] * current_distance[1]
        current_score = current_distance[0] * current_distance[1]
        #current_score = current_distance[0] + current_distance[1]
        if current_score < last_score:
            closest = current_food
            last_score = current_score
            #print("Closest food = {}".format(closest))
            #print("Score = {}".format(last_score))
    l.append(closest)
    #print(closest) 
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
    

    healthThreshold = 50
    goGetFood = 0

    if ((myHealth < healthThreshold) or (longer_snake == True)) :
        print("DEBUG: Go get food")
        if (myHealth < healthThreshold):
            goGetFood = 1
    elif (shortest_length < len(data["you"]["body"])):
        print("DEBUG: Chase shortest snake")
        first_food["x"] = shortest_snake["body"][0]["x"]
        first_food["y"] = shortest_snake["body"][0]["y"]
        attack = 1 
    elif (myHead == myTail):
        print("DEBUG: starting conditions - get food")
        goGetFood = 1
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
    
    #left
    avoidHeadMoves = []
    testAreas = []
    testAreas.append((myHead["x"]-1, myHead["y"]))
    testAreas.append((myHead["x"]-1, myHead["y"] - 1))
    testAreas.append((myHead["x"]-1, myHead["y"] + 1))
    testAreas.append((myHead["x"] - 2, myHead["y"]))
    testAreas.append((myHead["x"] - 2, myHead["y"] - 1))
    testAreas.append((myHead["x"] - 2, myHead["y"] + 1))
    for test in testAreas:
        if test in snake_heads:
            for snake in data["board"]["snakes"]:
                temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                if (temp == test):
                    otherSnakeSize = len(snake["body"])
                    if (mySize < otherSnakeSize):
                        avoidHeadMoves.append("left")
                        print("DEBUG: Avoid snake head!")

    testAreas.clear()

    # right
    testAreas.append((myHead["x"] + 1, myHead["y"]))
    testAreas.append((myHead["x"] + 1, myHead["y"] - 1))
    testAreas.append((myHead["x"] + 1, myHead["y"] + 1))
    testAreas.append((myHead["x"] + 2, myHead["y"]))
    testAreas.append((myHead["x"] + 2, myHead["y"] - 1))
    testAreas.append((myHead["x"] + 2, myHead["y"] + 1))
    for test in testAreas:
        if test in snake_heads:
            for snake in data["board"]["snakes"]:
                temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                if (temp == test):
                    otherSnakeSize = len(snake["body"])
                    if (mySize < otherSnakeSize):
                        avoidHeadMoves.append("right")
                        print("DEBUG: Avoid snake head!")

    testAreas.clear()

    # up
    testAreas.append((myHead["x"], myHead["y"] - 1))
    testAreas.append((myHead["x"] - 1, myHead["y"] - 1))
    testAreas.append((myHead["x"] + 1, myHead["y"] - 1))
    testAreas.append((myHead["x"], myHead["y"] - 2))
    testAreas.append((myHead["x"] - 1, myHead["y"] - 2))
    testAreas.append((myHead["x"] + 1, myHead["y"] - 2))
    for test in testAreas:
        if test in snake_heads:
            for snake in data["board"]["snakes"]:
                temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                if (temp == test):
                    otherSnakeSize = len(snake["body"])
                    if (mySize < otherSnakeSize):
                        avoidHeadMoves.append("up")
                        

    testAreas.clear()

# down
    testAreas.append((myHead["x"], myHead["y"] + 1))
    testAreas.append((myHead["x"] - 1, myHead["y"] + 1))
    testAreas.append((myHead["x"] + 1, myHead["y"] + 1))
    testAreas.append((myHead["x"], myHead["y"] + 2))
    testAreas.append((myHead["x"] - 1, myHead["y"] + 2))
    testAreas.append((myHead["x"] + 1, myHead["y"] + 2))
    for test in testAreas:
        if test in snake_heads:
            for snake in data["board"]["snakes"]:
                temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                if (temp == test):
                    otherSnakeSize = len(snake["body"])
                    if (mySize < otherSnakeSize):
                        avoidHeadMoves.append("down")
                        
    print("DEBUG: Avoid Head Moves: {}".format(avoidHeadMoves))

    riskyMoves = []
    myTailCoord = (myTail["x"], myTail["y"])
    snakes = data["board"]["snakes"]

    #print("RISK UP")
    riskUp = check_risk(myHead["y"] - 3, myHead["y"], myHead["x"] - 2, myHead["x"] + 2, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 0)
    #print("RiskUp 1 = {}".format(riskUp))
    #check this
    riskUp1 = count_empty(0, myHead["y"], myHead["x"], myHead["y"] -1, snakeCoords, myTailCoord, snake_tails, snake_heads, 1)
    #print("RiskUp 2 = {}".format(riskUp1))

    riskUp2 = 0
    if (myHead["y"] <= 2):
        riskUp2 += 0.5

    tup = ('up', riskUp + riskUp1 + riskUp2)
    riskyMoves.append(tup)
    
    #print("RISK DOWN")
    riskDown = check_risk((myHead["y"]) + 1, myHead["y"] + 4, myHead["x"] - 2, myHead["x"] + 2, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 0)
    #print("RiskDown 1 = {}".format(riskDown))
    riskDown1 = count_empty(myHead["y"] + 1, height, myHead["x"], height - myHead["y"] - 1, snakeCoords, myTailCoord, snake_tails, snake_heads, 1)
    #print("RiskDown 2 = {}".format(riskDown1))

    riskDown2 = 0
    if (myHead["y"] > height - 3):
        riskDown2 += 0.5

    tup = ('down', riskDown + riskDown1 + riskDown2)
    riskyMoves.append(tup)
    
    #print("RISK LEFT")
    riskLeft = check_risk(myHead["x"] - 4, myHead["x"] - 1, myHead["y"]-2, myHead["y"]+2, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 1)
    #print("RiskLeft 1 = {}".format(riskLeft))
    riskLeft1 = count_empty(0, myHead["x"] - 1, myHead["y"], myHead["x"], snakeCoords, myTailCoord, snake_tails, snake_heads, 0) 
    #print("RiskLeft 2 = {}".format(riskLeft1))

    riskLeft2 = 0
    if (myHead["x"] <= 2):
        riskLeft2 += 0.5

    tup = ('left', riskLeft + riskLeft1 + riskLeft2)
    riskyMoves.append(tup)
    
    #print("RISK RIGHT")
    riskRight = check_risk(myHead["x"] + 1, myHead["x"] + 4, myHead["y"]-2, myHead["y"]+2, badCoords, snakeCoords, data["you"]["body"], snake_heads, snakes, 1)
    #print("RiskRight 1 = {}".format(riskRight))
    riskRight1 = count_empty(myHead["x"] + 1, width, myHead["y"], width - myHead["x"] - 1, snakeCoords, myTailCoord, snake_tails, snake_heads, 0)
    #print("RiskRight 2 = {}".format(riskRight1))

    riskRight2 = 0
    if (myHead["x"] > width - 3):
        riskRight2 += 0.5

    tup = ('right', riskRight + riskRight1 + riskRight2)
    riskyMoves.append(tup)
    
    riskyMoves.sort(key=lambda x: x[1])
   
    print("DEBUG: Risky Moves: {}".format(riskyMoves))

    matrixL = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            if (testCoord in snakeCoords):
                matrixL[x][y] = 's'
            else:
                matrixL[x][y] = 'e'
    
    matrixR = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            if (testCoord in snakeCoords):
                matrixR[x][y] = 's'
            else:
                matrixR[x][y] = 'e'

    matrixU = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            if (testCoord in snakeCoords):
                matrixU[x][y] = 's'
            else:
                matrixU[x][y] = 'e'

    matrixD = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            if (testCoord in snakeCoords):
                matrixD[x][y] = 's'
            else:
                matrixD[x][y] = 'e'

    #print(matrix)
    
    ffMoves = []
    upFF = 0
    if (myHead["y"] != 0):
        upFF = floodfill(matrixU, myHead["x"], myHead["y"] - 1, 0, snakeCoords)
    ffMoves.append(("up", upFF))
    
    downFF = 0
    if (myHead["y"] !=  height - 1):
        downFF = floodfill(matrixD, myHead["x"], myHead["y"] + 1, 0, snakeCoords)
    ffMoves.append(("down", downFF))
    
    leftFF = 0
    if (myHead["x"] != 0):
        leftFF = floodfill(matrixL, myHead["x"] - 1, myHead["y"], 0, snakeCoords)
    ffMoves.append(("left", leftFF))
    
    rightFF = 0
    if (myHead["x"] != width - 1):
        rightFF = floodfill(matrixR, myHead["x"] + 1, myHead["y"], 0, snakeCoords)
    ffMoves.append(("right", rightFF))
        
    ffMoves.sort(key=lambda x: x[1], reverse=True)

    print("DEBUG: FF Moves: {}".format(ffMoves))

    # final decision
    direction = None
    
    # preferredMove
    preferredDirection = None
    for pm in preferredMoves:
        if pm in possibleMoves:
            if pm not in avoidHeadMoves:
                preferredDirection = pm
                print("DEBUG: Preferred direction = {}".format(preferredDirection))
                break
    
    # least risk           
    leastRisk = None
    for lrm in riskyMoves:
        if lrm[0] in possibleMoves:
            if lrm[0] not in avoidHeadMoves:
                leastRisk = lrm[0]
                leastRiskScore = lrm[1]
                print("DEBUG: least risk move: {}".format(leastRisk))
                break

    pms = -1
    if (preferredDirection != None):
        for rrr in riskyMoves:
            if (rrr[0] == preferredDirection):
                pms = rrr[1]
                break
    
    threshold = 1
    if (goGetFood == 1):
        print("DEBUG: Getting hungry - taking more risk on preferred direction")
        threshold = 1.3

    ffDirection = None
    if ((pms != -1) and (pms <= threshold)):
        direction = preferredDirection
        print("DEBUG: choosing preferred direction: {}".format(direction))
    else:
        for ffMove in ffMoves:
            if ffMove[0] in possibleMoves:
                if ffMove[0] not in avoidHeadMoves:
                    ffDirection = ffMove[0]
                    print("DEBUG: flood fill: {}".format(ffDirection))
                    direction = ffDirection
                    break
    
    if ((pms <= threshold) and (ffDirection != None)):
        direction = leastRisk
        print("DEBUG: we have 2 options - making the hard decision of least risk")
    

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
    fakeTotal = 0
    for x in range(aFrom, aTo):
        fakeTotal += 1
        if (mode > 0):
            testCoord = (b, x)
            #print ("testCoord1:{}".format(testCoord))
        else:
            testCoord = (x, b)
            #print ("testCoord2:{}".format(testCoord))
        
        #print (snakeCoords)
        if (testCoord not in snakeCoords):
            #print("EMPTY COUNT + ! !!!!!!!!!!")
            emptyCount += 1
        else:
            break
        
    ratio = 0
    if (emptyCount == 0):
        #print("EmptyCount = 0 !")
        emptyCount = 0.5
    
    ratio = total/emptyCount

    #if (ratio >= 0.8) and (ratio <= 1.2):
        #print("ratio = 0.8-1.2, so set to zero - no risk")
        #ratio = 0

    #print ("EmptyCount:{}".format(emptyCount))
    #print ("Total:{}".format(total))
    #print ("Ratio:{}".format(ratio))

    return ratio


def check_risk(a1, a2, b1, b2, badCoords, snakeCoords, me, sh, snakes, mode):
    risk = 0

    area = abs(a2 - a1) * abs(b2 - b1)
    #print ("Desired Area = {}".format(area))
    fakeArea = 0
    for first_loop in range(b1, b2):
        for second_loop in range(a1, a2):
            fakeArea += 1
            if (mode > 0):
                testCoord = (second_loop, first_loop)
            else:
                testCoord = (first_loop, second_loop)
            if (testCoord in snakeCoords):
                    risk += 1
                    #print("DEBUG: +1 to risk - other snake")
    if (risk > 0):
        riskFactor = risk / fakeArea
        riskFactor = riskFactor
        #if (riskFactor < 0.1):
            #riskFactor = 0
    else:
        riskFactor = 0
    return riskFactor

#b is a snake part
# a is empty
def floodfill(matrix, x, y, count, snakeCoords):
    testc = (x,y)
    if matrix[x][y] == 'e':  
        matrix[x][y] = ' '
        #print("Filling coord ={}".format(testc))
        #recursively invoke flood fill on all surrounding cells:
        count += 1
        if x > 0:
            count = floodfill(matrix, x-1, y, count, snakeCoords)
        if x < len(matrix[y]) - 1:
            count = floodfill(matrix, x+1, y, count, snakeCoords)
        if y > 0:
            count = floodfill(matrix, x, y-1, count, snakeCoords)
        if y < len(matrix) - 1:
            count = floodfill(matrix, x, y+1, count, snakeCoords)
    #else:
        #print("Cannot floodfill as coordinate is not empty: {}".format(testc))
    return count

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