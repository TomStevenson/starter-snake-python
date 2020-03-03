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

    color = "#64F83C"

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
        current_score = current_distance[0] * current_distance[1]
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

# perimeter coordinates just outside the board
def populate_bad_coords(width, height):
    badCoords = []
    for x in range(width):
        bad = (x, -1)
        badCoords.append(bad)
        bad = (x, height)
        badCoords.append(bad)

        bad = (x, -2)
        badCoords.append(bad)
        bad = (x, height + 1)
        badCoords.append(bad)

    for y in range(height):
        bad = (-1, y)
        badCoords.append(bad)
        bad = (width, y)
        badCoords.append(bad)

        bad = (-2, y)
        badCoords.append(bad)
        bad = (width + 1, y)
        badCoords.append(bad)
    return badCoords

def get_snake_array(index, data):
    snake_array = []
    for snake in data["board"]["snakes"]:
        if snake != data["you"]:
            snakeSize = len(snake["body"])
            if (index == 0):
                temp = (snake["body"][index]["x"], snake["body"][index]["y"])
            else:
                temp = (snake["body"][snakeSize + index]["x"], snake["body"][snakeSize + index]["y"])
            snake_array.append(temp)
    return snake_array

def populate_snake_coords(data):
    snakeCoords= []
    for snake in data["board"]["snakes"]:
        for xycoord in snake["body"]:
            bad = (xycoord["x"], xycoord["y"])
            #my_size = len(data["you"]["body"])
            #my_tail = data["you"]["body"][my_size-1]
            #mt = (my_tail["x"], my_tail["y"])
            #if (bad != mt):
            snakeCoords.append(bad)
    return snakeCoords

def get_shortest_snake(data):
    shortest_length = len(data["you"]["body"])
    shortest_snake = data["you"]
    for snake in data["board"]["snakes"]:
        if (snake != data["you"] and (len(snake["body"]) < shortest_length)):
            print("DEBUG: Found a shorter snake")
            shortest_snake = snake
    return shortest_snake

def is_there_a_longer_snake(data):
    longer_snake = False
    for snake in data["board"]["snakes"]:
        if (snake != data["you"] and (len(snake["body"]) >= (len(data["you"]["body"]) - 1))):
            print("DEBUG: Found a longer snake")
            longer_snake = True
            break
    return longer_snake

def get_possible_moves(my_head, bad_coords, snake_coords):
    possible_moves = []
    # left
    coord = (my_head["x"] -1 , my_head["y"])
    if ((coord not in bad_coords) and (coord not in snake_coords)):
        possible_moves.append("left")
    # right
    coord = (my_head["x"] + 1, my_head["y"])
    if (coord not in bad_coords) and (coord not in snake_coords):
        possible_moves.append("right") 
    # up
    coord = (my_head["x"], my_head["y"] - 1)
    if (coord not in bad_coords) and (coord not in snake_coords):
        possible_moves.append("up")
    # down
    coord = (my_head["x"], my_head["y"] + 1)
    if (coord not in bad_coords) and (coord not in snake_coords):
        possible_moves.append("down")
    return possible_moves

def get_preferred_moves(my_head, target, possible_moves):
    preferred_moves = []
    coord = (my_head["x"], my_head["y"])
    if target["x"] < my_head["x"]:
        if ("left" in possible_moves):
            preferred_moves.append("left")
    elif target["x"] > my_head["x"]:
        if ("right" in possible_moves):
            preferred_moves.append("right")
    if target["y"] < my_head["y"]:
        if ("up" in possible_moves):
            preferred_moves.append("up")
    elif target["y"] > my_head["y"]:
        if ("down" in possible_moves):
            preferred_moves.append("down")
    print("DEBUG: Preferred moves to get us to target: {}".format(preferred_moves))
    return preferred_moves

def test_for_snake_head(direction, coords_to_test, snake_heads, my_size, data):
    heads_to_avoid = []
    for test in coords_to_test:
        if test in snake_heads:
            for snake in data["board"]["snakes"]:
                temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                if (temp == test):
                    other_snake_size = len(snake["body"])
                    if (my_size < other_snake_size):
                        heads_to_avoid.append(direction)
                        print("DEBUG: Avoid snake head!")
    return heads_to_avoid

def get_snake_heads_to_avoid(my_head, snake_heads, my_size, data):
    temp = []
    test_areas = []
    test_areas.append((my_head["x"]-1, my_head["y"]))
    test_areas.append((my_head["x"]-1, my_head["y"] - 1))
    test_areas.append((my_head["x"]-1, my_head["y"] + 1))
    test_areas.append((my_head["x"] - 2, my_head["y"]))
    test_areas.append((my_head["x"] - 2, my_head["y"] - 1))
    test_areas.append((my_head["x"] - 2, my_head["y"] + 1))
    temp = test_for_snake_head("left", test_areas, snake_heads, my_size, data)
    test_areas.clear()
    test_areas.append((my_head["x"] + 1, my_head["y"]))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 2, my_head["y"]))
    test_areas.append((my_head["x"] + 2, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 2, my_head["y"] + 1))
    temp = temp + test_for_snake_head("right", test_areas, snake_heads, my_size, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] - 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"], my_head["y"] - 2))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 2))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 2))
    temp = temp + test_for_snake_head("up", test_areas, snake_heads, my_size, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] + 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"], my_head["y"] + 2))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 2))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 2))
    temp = temp + test_for_snake_head("down", test_areas, snake_heads, my_size, data)
    print("DEBUG: Avoid Head Moves: {}".format(temp))
    return temp

  #  0, my_head["x"] - 1, my_head["y"], my_head["x"] - 1, snake_coords, possible_moves, data, (my_head["x"] <= 2), width, height)      

def check_risk_straight_line(a_from, a_to, b, total, snake_coords, mode):
    empty_count = 0
    for x in range(a_from, a_to): #0 - 7
        test_coord = None
        if (mode > 0):
            test_coord = (b, x) #2 0 / 2 1 / 2 2 / 2 3 
        else:
            test_coord = (x, b) #(0 0) (1 0 ) (2 0 ) (3 0) 4 0
        
        if (test_coord not in snake_coords):
            #print("DEBUG:     empty_count + 1: {}".format(test_coord))
            empty_count += 1
        else:
            #print("DEBUG:     not in snake coords - break: {}".format(snake_coords))
            break
    ratio = 0
    if (empty_count == 0):
        empty_count = 0.5
    #print("DEBUG:     total: {}".format(total))
    ratio = total / empty_count
    #print("DEBUG:     ratio: {}".format(total))
    return ratio

#tup = check_risky_business("left", my_head["x"] - 4, my_head["x"] - 1, my_head["y"] - 2, my_head["y"] + 2,
def check_risk_area(a1, a2, b1, b2, snake_coords, me, snakes, mode, width, height):
    risk = 0
    fake_area = 0
    test_coord = None
    risk_factor = 0
    #print("b1: {}".format(b1)) #8
    #print("b2: {}".format(b2)) #12
    #print("a1: {}".format(a1)) #8
    #print("a2: {}".format(a2)) #5
    for first_loop in range(b1, b2 + 1): # left 8 - 12
        if (first_loop < 0):
            #print("TOM FIRST LOOP (1): {}".format(first_loop))
            continue
        if (mode > 0):
            if (first_loop > height - 1):
                #print("TOM FIRST LOOP (2): {}".format(first_loop))
                continue
        else:   
            if (first_loop > width - 1):
                #print("TOM FIRST LOOP (3): {}".format(first_loop))
                continue
        for second_loop in range(a1, a2 + 1): #8 - 5
            if (second_loop < 0):
                #print("TOM SECOND LOOP (4): {}".format(second_loop))
                continue
            if (mode > 0):
                if (second_loop > height - 1):
                    #print("TOM SECOND LOOP (5): {}".format(second_loop))
                    continue
            else:
                if (second_loop > width - 1):
                    #print("TOM SECOND LOOP (6): {}".format(second_loop))
                    continue
            fake_area += 1
            if (mode > 0):
                test_coord = (first_loop, second_loop)
                #print ("TOM mode 1: {}".format(test_coord))
            else:
                test_coord = (second_loop, first_loop)
                #print ("TOM mode 2: {}".format(test_coord))
            if (test_coord in snake_coords):
                if (test_coord in me):
                    risk += 0.5
                else:
                    risk += 1
                    #print("RISK + 1")
                for snake in snakes:
                    temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                    #print (temp)
                    if (temp == test_coord):
                        otherSnakeSize = len(snake["body"])
                        if (len(me) < otherSnakeSize):
                            risk += 5
                            print("DEBUG: +5 to risk - bigger snake head !")
    if (risk > 0):
        risk_factor = risk / fake_area
    else:
        risk_factor = 0

    #print("DEBUG:     risk: {}".format(risk))
    #print("DEBUG:     fake_area: {}".format(fake_area))
    #print("DEBUG:     risk_factor: {}".format(risk_factor))
    return risk_factor

    #tup = check_risky_business("left", my_head["x"] - 4, my_head["x"] - 1, my_head["y"] - 2, my_head["y"] + 2,
    # 
    #  0, my_head["x"] - 1, my_head["y"], my_head["x"] - 1, snake_coords, possible_moves, data, (my_head["x"] <= 2), width, height)    
    
def check_risky_business(move, a1, a2, a3, a4, b1, b2, b3, b4, snake_coords, possible_moves, data, test_result, width, height):
    risk_for_proximity_to_walls = 0.1
    snakes = data["board"]["snakes"]
    tup = None
    if (move in possible_moves):
        #print("DEBUG: Risk: {}".format(move))
        mode = 1
        if ((move == "left") or move == "right"): 
            mode = 0
        risk_area = check_risk_area(a1, a2, a3, a4, snake_coords, data["you"]["body"], snakes, mode, width, height)
        
        # check right for this !!!!!!!!!!!!!
        #risk_straight_line = check_risk_straight_line(b1, b2, b3, b4, snake_coords, 1)
        risk_wall_proximity = 0
        if (test_result):
            risk_wall_proximity += risk_for_proximity_to_walls
        #tup = (move, risk_area + risk_straight_line + risk_wall_proximity)
        tup = (move, risk_area + risk_wall_proximity)
        #print("DEBUG:   Area: {}".format(risk_area))
        #print("DEBUG:   Straight Line: {}".format(risk_straight_line))
        #print("DEBUG:   Wall Proximity: {}".format(risk_wall_proximity))
    return tup

def build_matrix(width, height, snake_coords):
    matrix = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            if (testCoord in snake_coords):
                matrix[x][y] = 's'
            else:
                matrix[x][y] = 'e'
    return matrix

def floodfill_algorithm(matrix, x, y, count, snakeCoords):
    if matrix[x][y] == 'e':  
        matrix[x][y] = ' '
        count += 1
        if x > 0:
            count = floodfill_algorithm(matrix, x-1, y, count, snakeCoords)
        if x < len(matrix[y]) - 1:
            count = floodfill_algorithm(matrix, x+1, y, count, snakeCoords)
        if y > 0:
            count = floodfill_algorithm(matrix, x, y-1, count, snakeCoords)
        if y < len(matrix) - 1:
            count = floodfill_algorithm(matrix, x, y+1, count, snakeCoords)
    return count

def build_floodfill_move(width, height, snake_coords, x, y, test1, test2):
    ff = 0
    if (test1 != test2):
        ff = floodfill_algorithm(build_matrix(width, height, snake_coords), x, y, 0, snake_coords)
    return ff

def get_ff_size(direction, ff_moves):
    retval = None
    for ff in ff_moves:
        if (ff[0] == direction):
            retval = ff[1]
            break
    return retval

def make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, avoid_heads, risk_moves, ff_moves, my_size, area):
    lowestFF = 0
    for ff in ff_moves:
        if (ff[1] <= my_size - 1):
            if (lowestFF != [ff[1]]):
                lowestFF = ff[1]

    threshold = 0.8
    threshold2 = my_size
    dir = None
    #aggregated_risk = []
    #for ff in ff_moves:
        #dir = ff[0]
        #agg = (area) - ff[1]
        #for rm in risk_moves:
            #if (dir == rm[0]):
                #agg = agg + rm[1]
        #ggg = (ff[0], agg)
        #aggregated_risk.append(ggg)

    #if len(aggregated_risk) > 0:
        #aggregated_risk.sort(key=lambda x: x[1])    
    #print("DEBUG: Aggregated risk: {}".format(aggregated_risk))

    # final decision
    direction = None
    
    # preferredMove
    preferredDirection = None
    for pm in preferred_moves:
        preferredDirection = pm
        print("DEBUG: Preferred direction = {}".format(preferredDirection))
        break

    # least risk           
    leastRisk = None
    leastRiskScore = None
    for lrm in risk_moves:
        leastRisk = lrm[0]
        leastRiskScore = lrm[1]
        print("DEBUG: least risk move: {}".format(leastRisk))
        direction = leastRisk
        break

    pms = -1
    if (preferredDirection != None):
        for rrr in risk_moves:
            if (rrr[0] == preferredDirection):
                pms = rrr[1]
                break
    #TOM
    #threshold = 1.3
    #threshold = 1.0
    threshold = 0.5
    #ffDirection = None
    if ((pms != -1) and (pms <= threshold)):
        ff_size = get_ff_size(preferredDirection, ff_moves)
        if (ff_size >= my_size):
            direction = preferredDirection
            print("DEBUG: choosing preferred direction: {}".format(direction))
            if (ff_size < 2*my_size):
                print("DEBUG: DID I GET IN TROUBLE?: {}".format(direction))
        else:
            print("DEBUG: Floodfill size in preferred direction too small: {}".format(direction))
            direction = None
    
    if (direction == None):
        for ffMove in ff_moves:
            ff_size = get_ff_size(ffMove[0], ff_moves)
            if (ff_size >= my_size):
                direction = ffMove[0]
                print("DEBUG: selecting lowest ff = {}".format(direction))
                break
    
    if (direction == None):
        for pm in last_ditch_possible_moves:
            direction = pm
            print("DEBUG: No options left - choose last ditch possible move: {}".format(direction))
            break

    if (direction == None):
        direction = random.choice(["left", "right", "up", "down"])
        print("DEBUG: No options left - choose RANDOM direction: {}".format(direction))

    print("DEBUG: Direction={}".format(direction))
    return direction

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

    # build list of bad coordinates
    bad_coords = populate_bad_coords(width, height)

    # build list of all snake coordinates on the board
    snakes = data["board"]["snakes"]
    snake_coords = populate_snake_coords(data)

    # obtain information about my snake
    my_size = len(data["you"]["body"])
    my_health = data["you"]["health"]
    my_head = data["you"]["body"][0]  
    my_tail = data["you"]["body"][my_size-1]

    # snake bodies
    snake_heads = get_snake_array(0, data)
    snake_tails = get_snake_array(-1, data)
    # get details on the shortest snake on the board
    shortest_snake = get_shortest_snake(data)
    shortest_length = len(shortest_snake)
    # check if we have a longer snake on the board
    longer_snake = is_there_a_longer_snake(data)

    # get list of food and determine closest food to my head
    food_sorted_by_proximity = get_food_list(my_head, data)
    amount_of_food = len(food_sorted_by_proximity)
    target = food_sorted_by_proximity[0]
    
    go_get_food = 0
    health_threshold = 25
    if ((my_head == my_tail) or (longer_snake == True) or (my_health <= health_threshold)):
        print("DEBUG: Go get food")
        goGetFood = 1
    elif (shortest_length < len(data["you"]["body"])):
        print("DEBUG: Chase shortest snake")
        target["x"] = shortest_snake["body"][0]["x"]
        target["y"] = shortest_snake["body"][0]["y"]
    else:
        print("DEBUG: Chase my tail")
        target["x"] = my_tail["x"]
        target["y"] = my_tail["y"]

    # determine possible moves - remove any entries where we need to avoid snake heads
    possible_moves = get_possible_moves(my_head, bad_coords, snake_coords)
    last_ditch_possible_moves = possible_moves
    avoid_heads = get_snake_heads_to_avoid(my_head, snake_heads, my_size, data)
    for ah in avoid_heads:
        if (ah in possible_moves):
            possible_moves.remove(ah)
    print("DEBUG: Possible Moves={}".format(possible_moves))

    preferred_moves = get_preferred_moves(my_head, target, possible_moves)

    risk_moves = []
    tup = check_risky_business("up", my_head["y"] - 3, my_head["y"], my_head["x"] - 2, my_head["x"] + 2, 0, my_head["y"], 
        my_head["x"], my_head["y"] -1, snake_coords, possible_moves, data, (my_head["y"] <= 2), width, height)    
    if (tup):
        risk_moves.append(tup)

    tup = check_risky_business("down", my_head["y"] + 1, my_head["y"] + 4, my_head["x"] - 2, my_head["x"] + 2, my_head["y"] + 1, 
        height, my_head["x"], height - my_head["y"] - 1, snake_coords, possible_moves, data, (my_head["y"] > (height - 3)), width, height)
    if (tup):
        risk_moves.append(tup)

    tup = check_risky_business("left", my_head["x"] - 4, my_head["x"] - 1, my_head["y"] - 2, my_head["y"] + 2, 0, my_head["x"] - 1, 
        my_head["y"], my_head["x"] - 1, snake_coords, possible_moves, data, (my_head["x"] <= 2), width, height)    
    if (tup):
        risk_moves.append(tup)

    tup = check_risky_business("right", my_head["x"] + 1, my_head["x"] + 4, my_head["y"]-2, my_head["y"]+2, my_head["x"] + 1, width, 
        my_head["y"], width - my_head["x"] - 1, snake_coords, possible_moves, data, (my_head["x"] > width - 3), width, height)
    if (tup):
        risk_moves.append(tup)
    
    if len(risk_moves) > 0:
        risk_moves.sort(key=lambda x: x[1])
    print("DEBUG: Risky Moves: {}".format(risk_moves))

    #snake_coords.remove((my_tail["x"], my_tail["y"]))
    
    ff_moves = []
    if ("up" in possible_moves):
        ff_moves.append(("up", build_floodfill_move(width, height, snake_coords, my_head["x"], my_head["y"] - 1, my_head["y"], 0)))
    if ("down" in possible_moves):
        ff_moves.append(("down", build_floodfill_move(width, height, snake_coords, my_head["x"], my_head["y"] + 1, my_head["y"], height - 1)))
    if ("left" in possible_moves):
        ff_moves.append(("left", build_floodfill_move(width, height, snake_coords, my_head["x"] - 1, my_head["y"], my_head["x"], 0)))
    if ("right" in possible_moves):
        ff_moves.append(("right", build_floodfill_move(width, height, snake_coords, my_head["x"] + 1, my_head["y"], my_head["x"], width - 1)))        
    ff_moves.sort(key=lambda x: x[1], reverse=True)
    print("DEBUG: FF Moves: {}".format(ff_moves))

    # final decision
    direction = make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, avoid_heads, risk_moves, ff_moves, my_size, width*height)

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