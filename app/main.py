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

    color = "#fff000"

    return start_response(color)

def get_snake_head_danger(snake_head, data):
    total_score = 0
    for snake in data["board"]["snakes"]:
        if (snake != data["you"]):
            current_distance = [99, 99]
            current_distance[0] = abs(snake_head["x"] - snake["body"][0]["x"])
            current_distance[1] = abs(snake_head["y"] - snake["body"][0]["y"])
            current_score = current_distance[0] * current_distance[1]
            total_score = total_score + current_score
    return total_score

def get_food_list(snake_head, data):
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

def get_common_elements(x,y):
    retval = []
    for i in x:
        if ((i in y) or (len(y) == 0)):
            retval.append(i)
    return retval

# Fetches first element from x that is common for both lists
# or return None if no such an element is found.  
def get_first_common_element(x,y):
    for i in x:
        if i in y:
            return i
    # In case no common element found, you could trigger Exception
    # Or if no common element is _valid_ and common state of your application
    # you could simply return None and test return value
    # raise Exception('No common element found')
    return None

def is_snake_longer_than_me(data, snake_head):
    longer_snake = False
    for snake in data["board"]["snakes"]:
        if (snake_head == snake["body"][0]):
            if (snake != data["you"] and (len(snake["body"]) >= (len(data["you"]["body"]) - 1))):
                print("DEBUG: Snake is longer than me !")
                longer_snake = True
                break
    return longer_snake

def which_directions_are_away_from_snake_heads(my_head, snake_heads, data, possible_moves, ignore = False):
    retval = []
    for sh in snake_heads:
        if (is_snake_longer_than_me(data, sh) or ignore):
            x = my_head["x"] - sh[0]
            if (x > 0):
                if ("right" not in retval):
                    if ("right" in possible_moves):
                        retval.append("right")
            if (x < 0):
                if ("left" not in retval):
                    if ("left" in possible_moves):
                        retval.append("left")
            y = my_head["y"] - sh[1]
            if (y > 0):
                if ("down" not in retval):
                    if ("down" in possible_moves):
                        retval.append("down")
            if (y < 0):
                if ("up" not in retval):
                    if ("up" in possible_moves):
                        retval.append("up")
    return retval

# populate_bad_coords: define perimeter coordinates just outside the board
# width: width of the board
# height: height of the board
# returns: array of all bad coords on the the board
def populate_bad_coords(width, height):
    badCoords = []
    for x in range(width):
        bad = (x, -1)
        badCoords.append(bad)
        bad = (x, height)
        badCoords.append(bad)
        # include one additional square off board
        # to easily remove from risk area calcs
        bad = (x, -2)
        badCoords.append(bad)
        bad = (x, height + 1)
        badCoords.append(bad)
    for y in range(height):
        bad = (-1, y)
        badCoords.append(bad)
        bad = (width, y)
        badCoords.append(bad)
        # include one additional square off board
        # to easily remove from risk area calcs
        bad = (-2, y)
        badCoords.append(bad)
        bad = (width + 1, y)
        badCoords.append(bad)
    return badCoords

# get_snake_array returns an array of all snake heads or snake tails
# index: 0 means return snake heads, -1 means return snake tails
# returns: array of snake heads or tails
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

# populate_snake_coords builds and returns an array of all snake coords on the board
# data: json structure provided
# returns: array of all snake coords on the board
def populate_snake_coords(data):
    snakeCoords= []
    for snake in data["board"]["snakes"]:
        for xycoord in snake["body"]:
            bad = (xycoord["x"], xycoord["y"])
            snakeCoords.append(bad)
    return snakeCoords

# get_shortest_snake returns the shortest snake object (not me) on the board
# data: json structure provided
# returns: shortest snake object
def get_shortest_snake(data):
    shortest_length = len(data["you"]["body"])
    shortest_snake = data["you"]
    for snake in data["board"]["snakes"]:
        if (snake != data["you"] and (len(snake["body"]) < shortest_length)):
            print("DEBUG: Found a shorter snake")
            shortest_snake = snake
    return shortest_snake

# is_there_a_longer_snake is a helper function to see if there is a longer snake on the board
# data: json structure provided
# returns: True if there is a longer snake than me on the board, False otherwise
def is_there_a_longer_snake(data):
    longer_snake = None
    for snake in data["board"]["snakes"]:
        if (snake != data["you"] and (len(snake["body"]) >= (len(data["you"]["body"]) - 1))):
            print("DEBUG: Found a longer snake")
            longer_snake = snake
            break
    return longer_snake

# get_possible_moves: build an array of all possible moves for the snake
# my_head: coords of my snake head
# bad_coords: array of bad coordinates
# snake_coords: array of all snake parts
# returns: array of all possible moves
def get_possible_moves(my_head, my_tail, bad_coords, snake_coords):
    possible_moves = []
    tail = (my_tail["x"], my_tail["y"])
    snake_coords.remove(tail)
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

# get_preferred_moves: build an array of all preferred moves to get to target
# my_head: coords of my snake head
# target: target coords - food or smaller snake
# possible_moves: array of all possible moves
# returns: array of all preferred moves
def get_preferred_moves(my_head, target, possible_moves):
    preferred_moves = []
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

# test_for_snake_head: checks for other snake heads nearby
# direction: direction to test (left, right, up, down)
# coords_to_test: array of coordinates to test for snake heads
# snake_heads: array of all the snake heads on the board
# data: json structure provided
# returns: returns an array of bad directions that will encounter snake heads
def test_for_snake_head(direction, coords_to_test, snake_heads, data):
    my_size = len(data["you"]["body"])
    heads_to_avoid = []
    for test in coords_to_test:
        if test in snake_heads:
            for snake in data["board"]["snakes"]:
                temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                if (temp == test):
                    other_snake_size = len(snake["body"])
                    if (my_size <= other_snake_size):
                        heads_to_avoid.append(direction)
                        print("DEBUG: Avoid snake head!")
    return heads_to_avoid

# get_snake_heads_to_avoid: checks for other snake headsin all directions
# my_head: coordinates of my snake head
# snake_heads: array of all the snake heads on the board
# data: json structure provided
# returns: returns an array of bad directions that will encounter snake heads
def get_snake_heads_to_avoid(my_head, snake_heads, data):
    my_size = len(data["you"]["body"])
    temp = []
    test_areas = []
    test_areas.append((my_head["x"] - 1, my_head["y"]))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] - 2, my_head["y"]))
    test_areas.append((my_head["x"] - 2, my_head["y"] - 1))
    test_areas.append((my_head["x"] - 2, my_head["y"] + 1))
    temp = test_for_snake_head("left", test_areas, snake_heads, data)
    test_areas.clear()
    test_areas.append((my_head["x"] + 1, my_head["y"]))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 2, my_head["y"]))
    test_areas.append((my_head["x"] + 2, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 2, my_head["y"] + 1))
    temp = temp + test_for_snake_head("right", test_areas, snake_heads, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] - 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"], my_head["y"] - 2))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 2))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 2))
    temp = temp + test_for_snake_head("up", test_areas, snake_heads, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] + 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"], my_head["y"] + 2))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 2))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 2))
    temp = temp + test_for_snake_head("down", test_areas, snake_heads, data)
    print("DEBUG: Avoid Head Moves: {}".format(temp))
    return temp

# check_risk_area: calculates a risk factor based on coordinates provided
# a1, a2, b1, b2: x and y to and from coordinates to scan
# snake_coords: array of all snake coordinates
# me: array of my snake
# snakes: array of all snakes on the board
# mode: boolean toggle for interpreting x and y dimensions
# width, height: dimensions of the board
# returns: calculated risk area
def check_risk_area(a1, a2, b1, b2, snake_coords, me, snakes, mode, width, height):
    risk = 0
    fake_area = 0
    test_coord = None
    risk_factor = 0
    for first_loop in range(b1, b2 + 1):
        if (first_loop < 0):
            continue
        if (mode > 0):
            if (first_loop > height - 1):
                continue
        else:   
            if (first_loop > width - 1):
                continue
        for second_loop in range(a1, a2 + 1):
            if (second_loop < 0):
                continue
            if (mode > 0):
                if (second_loop > height - 1):
                    continue
            else:
                if (second_loop > width - 1):
                    continue
            fake_area += 1
            if (mode > 0):
                test_coord = (first_loop, second_loop)
            else:
                test_coord = (second_loop, first_loop)
            
            if (test_coord in snake_coords):
                risk += 1
                for snake in snakes:
                    temp = (snake["body"][0]["x"], snake["body"][0]["y"])
                    if (temp == test_coord):
                        otherSnakeSize = len(snake["body"])
                        if (len(me) < otherSnakeSize):
                            risk += 5
                            print("DEBUG: +5 to risk - bigger snake head !")
    #print("DEBUG: risk: {}".format(risk))
    #print("DEBUG: fake_area: {}".format(fake_area))
    if (risk > 0):
        risk_factor = risk / fake_area
    else:
        risk_factor = 0
    return risk_factor

# check_risky_business: builds a tuple of move direction and its associated risk score
# a1, a2, b1, b2: x and y to and from coordinates to scan
# snake_coords: array of all snake coordinates
# possible_moves: array of possible moves
# data: json payload from game
# width, height: dimensions of the board
# returns: tuple of move direction and risk score
def check_risky_business(move, a1, a2, b1, b2, snake_coords, possible_moves, data, width, height):
    snakes = data["board"]["snakes"]
    tup = None
    my_head = data["you"]["body"][0]
    if (move in possible_moves):
        mode = 1
        if ((move == "left") or move == "right"): 
            mode = 0
        #print("DEBUG: Risk direction being tested: {}".format(move))
        risk_area = check_risk_area(a1, a2, b1, b2, snake_coords, data["you"]["body"], snakes, mode, width, height)
        scan = scan_matrix(build_matrix(width, height, data, snake_coords), width, height, possible_moves, get_snake_array(0, data), get_snake_array(-1, data), my_head)
        sv = 0
        for s in scan:
            if (s[0] == move):
                sv = s[1]
                break
        
        move_to_edge = 0
        mte_factor = 0
        if (move == "left" and (my_head["x"] == 1)):
            move_to_edge += mte_factor
        elif (move == "right" and (my_head["x"] == width - 2)):
            move_to_edge += mte_factor
        elif (move == "up" and (my_head["y"] == 1)):
            move_to_edge += mte_factor
        elif (move == "down" and (my_head["y"] == height - 2)):
            move_to_edge += mte_factor
        else:
            move_to_edge += 0
  
        edges_adjust = 0
        if ((move == "up") or (move == "down")):
            if ((my_head["x"] == 0) or (my_head["x"] == width - 1)):
                p_to_test = 0
                if (move == "down"):
                    p_to_test = (my_head["y"] + 2)
                else:
                    p_to_test = (my_head["y"])
                mid_point = width / 2
                r_calc = abs(mid_point - p_to_test)
                edge_factor = r_calc / width
                edges_adjust += edge_factor
        if ((move == "right") or (move == "left")):
            if ((my_head["y"] == 0) or (my_head["y"] == height - 1)):
                p_to_test = 0
                if (move == "right"):
                    p_to_test = (my_head["y"] + 2)
                else:
                    p_to_test = (my_head["y"])
                mid_point = height / 2
                r_calc = abs(mid_point - p_to_test)
                edge_factor = r_calc / height
                edges_adjust += edge_factor

        tup = (move, risk_area + sv + edges_adjust*0.6 + move_to_edge)
    return tup

def get_directions_of_my_tail(my_head, my_tail, possible_moves):
    directions = []
    x = my_head["x"] - my_tail["x"]
    y = my_head["y"] - my_tail["y"]
    if (x > 0):
        if ("left" in possible_moves):
            directions.append("left")
    if (x < 0):
        if ("right" in possible_moves):
            directions.append("right")
    if (y > 0):
        if ("up" in possible_moves):
            directions.append("up")
    if (y < 0):
        if ("down" in possible_moves):
            directions.append("down")
    print("DEBUG: directions of my tail: {}".format(directions))
    return directions

# build_matrix: builds a matrix populated with the whereabouts of the snakes
# width/height: size of the matrix
# snake_coords: array of all snake coords on the board
# returns: a matrix with 's' where a snake part exists, and 'e' where none exists
def build_matrix(width, height, data, snake_coords):
    #my_size = len(data["you"]["body"])
    #my_tail = data["you"]["body"][my_size-1]
    snake_tails = get_snake_array(-1, data)
    matrix = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            #tail = (my_tail["x"], my_tail["y"])
            if ((testCoord in snake_coords) and (testCoord != snake_tails)):
                matrix[x][y] = 's'
            else:
                matrix[x][y] = 'e'
    return matrix

def scan_matrix(matrix, width, height, possible_moves, snake_heads, snake_tails, my_head):
    left = 0
    right = 0
    up = 0
    down = 0
    for x in range(width):
        for y in range(height):
            test = (x, y)
            if ((x <= my_head["x"]) and (matrix[x][y] == 's')):
                if (test in snake_heads):
                    left += 8
                elif (test in snake_tails):
                    left -= 5
                else:
                    left += 1
            if ((y > my_head["y"]) and (matrix[x][y] == 's')):
                if (test in snake_heads):
                    down += 8
                elif (test in snake_tails):
                    down -= 5
                else:
                    down += 1
            if ((y <= my_head["y"]) and (matrix[x][y] == 's')):
                if (test in snake_heads):
                    up += 8
                elif (test in snake_tails):
                    up -= 5
                else:
                    up += 1
            if ((x > my_head["x"]) and (matrix[x][y] == 's')):
                if (test in snake_heads):
                    right += 8
                elif (test in snake_tails):
                    right -= 5
                else:
                    right += 1
    retval = []
    if ("left" in possible_moves):
        #print("SCAN LEFT: {}".format(left / (my_head["x"] + 1) * (height - 1)))
        retval.append(("left", left*0.01))
    if ("right" in possible_moves):
        #print("SCAN RIGHT: {}".format(right / ((width - my_head["x"]) * (height - 1))))
        retval.append(("right", right*0.01))
    if ("up" in possible_moves):
        #print("SCAN UP: {}".format(up / ((width - 1) * (my_head["y"] + 1))))
        retval.append(("up", up*0.01))
    if ("down" in possible_moves):
        #print("SCAN DOWN: {}".format(down / ((height - my_head["y"]) * (width - 1))))
        retval.append(("down", down*0.01))
    
    retval.sort(key=lambda x: x[1])
    print("DEBUG: scan matrix: {}".format(retval))
    return retval

# floodfill_algorithm: recusive function to floodfill the provided matrix
# matrix: matrix representing board with snake coordinates on it
# x,y: coordinates to test
# count: variable to count the number of empty squares on flood fill
# snake_coords: array of all snake part locations
# returns: count of all empty squares on flood fill
def floodfill_algorithm(matrix, x, y, count, snake_coords):
    if matrix[x][y] == 'e':  
        matrix[x][y] = ' '
        count += 1
        if x > 0:
            count = floodfill_algorithm(matrix, x-1, y, count, snake_coords)
        if x < len(matrix[y]) - 1:
            count = floodfill_algorithm(matrix, x+1, y, count, snake_coords)
        if y > 0:
            count = floodfill_algorithm(matrix, x, y-1, count, snake_coords)
        if y < len(matrix) - 1:
            count = floodfill_algorithm(matrix, x, y+1, count, snake_coords)
    return count

# build_floodfill_move: helper function to call floodfill algorithm
def build_floodfill_move(width, height, snake_coords, data, x, y, test1, test2):
    ff = 0
    if (test1 != test2):
        ff = floodfill_algorithm(build_matrix(width, height, data, snake_coords), x, y, 0, snake_coords)
    return ff

# get_ff_size: helper function to get risk score for provided direction
# direction: desired direction
# ff_moves: array of flood fill information
# returns: size of specified flood fill
def get_ff_size(direction, ff_moves):
    retval = None
    for ff in ff_moves:
        if (ff[0] == direction):
            retval = ff[1]
            break
    return retval

# check_ff_size: checks if my snake can fit in the specified direction
# direction: specified direction to test
# ff_moves: array of flood fill information
# my_size: size of me (my snake)
# returns: validated direction of legal move
def check_ff_size(direction, ff_moves, my_size):
    new_direction = None
    ff_size = get_ff_size(direction, ff_moves)
    if (ff_size*1.25 >= my_size):
        new_direction = direction
        print("DEBUG: choosing supplied direction: {}".format(new_direction))
    else:
        print("DEBUG: Floodfill size in preferred direction too small: {}".format(direction))
        new_direction = None
    return new_direction

# make_decision: logic to pick the desired move of the snake
# preferred_moves: array of the preffered directions to move to get to target
# last_ditch_possible_moves: array of possible moves before they have been filtered to use as last resort
# risk_moves: array of riskiest moves sorted least to most
# ff_moves: array of flood fill moves sorted best to worst
# my_size: length of my snake
# returns: final direction to move
def make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, risk_moves, ff_moves, my_size, data, m, snake_heads, snake_tails):
    # final decision
    #threshold = 1.19
    threshold = 0.87

    direction = None
    
    my_head = data["you"]["body"][0]
    my_size = len(data["you"]["body"])
    my_tail = data["you"]["body"][my_size-1]
    directions_of_my_tail = get_directions_of_my_tail(my_head, my_tail, possible_moves)

    shd = get_snake_head_danger(my_head, data)
    number_of_active_snakes = len(data["board"]["snakes"])
    #print("INFO: Number of Active Snakes is = {}".format(number_of_active_snakes))
    if number_of_active_snakes == 0:
        number_of_active_snakes = 1

    preferred_direction = None    
    if (my_size > 8):
        #print("INFO: Snake Head Danger is = {}".format(shd))
        if (shd/number_of_active_snakes <= 4):    
            print("DEBUG: !!! Snake Head Danger is HIGH = {}".format(shd))
            t_away = which_directions_are_away_from_snake_heads(my_head, get_snake_array(0, data), data, possible_moves, False)
            print("DEBUG: Directions away from ALL snake heads = {}".format(t_away))
            for pm in preferred_moves:
                if (preferred_direction != None):
                    break
                for ta in t_away:
                    if (ta == pm):
                        preferred_direction = ta
                        break
            if (preferred_direction == None):
                for rm in risk_moves:
                    if (preferred_direction != None):
                        break
                    for ta in t_away:
                        if (ta == rm[0]):
                            preferred_direction = ta
                            break
                if (preferred_direction != None):
                    print("DEBUG: !!! Foregoing preferred direction and lowest risk avoiding heads: {}".format(preferred_direction))
            else:
                direction = preferred_direction
                print("DEBUG: !!! Pick preferred direction that avoids heads = {}".format(preferred_direction))
            #if (preferred_direction == None):
            #    for rm in risk_moves:
            #        preferred_direction = rm[0]
            #        print("DEBUG: !!! Pick least risk direction that avoids heads = {}".format(preferred_direction))
            #        break
    
    # preferred direction
    if (preferred_direction == None):
        for pm in preferred_moves:
            preferred_direction = pm
            print("DEBUG: Preferred direction = {}".format(preferred_direction))
            break

    # least risk direction         
    least_risk_direction = None
    for lrm in risk_moves:
        # get direction of lowest risk area score
        least_risk_direction = lrm[0]
        print("DEBUG: least risk move: {}".format(least_risk_direction))
        # test to make sure my snake can fit via flood fill in that direction
        least_risk_direction = check_ff_size(least_risk_direction, ff_moves, my_size)
        if (least_risk_direction != None):
            # snake fits - we can stop looking
            print("DEBUG: snake fits - we can stop looking: {}".format(least_risk_direction))
            direction = least_risk_direction
            break
        else:
            if least_risk_direction in directions_of_my_tail:
                direction = least_risk_direction
                print("DEBUG: move is toward tail - picking it: {}".format(least_risk_direction))

        
    #if (direction == None):
    #    directions_of_my_tail = get_directions_of_my_tail(my_head, my_tail, possible_moves)
    #    if least_risk_direction in directions_of_my_tail:
    #        direction = least_risk_direction
    #        print("DEBUG: move is toward tail - picking it: {}".format(least_risk_direction))

    height = data["board"]["height"]
    width = data["board"]["width"]
    
    # obtain the lowest risk score of the preferred move options
    lowest_risk_score = -1
    if (preferred_direction != None):        
        for rm in risk_moves:
            if (rm[0] == preferred_direction):
                lowest_risk_score = rm[1]
                break
    #else:
    #    direction = None
    #    directions_of_my_tail = get_directions_of_my_tail(my_head, my_tail, possible_moves)
    #    tom = get_common_elements(directions_of_my_tail, possible_moves)
    #    for t in tom:
    #        ttt = check_ff_size(t, ff_moves, my_size)
    #        if (ttt != None):
    #            direction = t
    #            print("DEBUG: trying a possible tail move")
    #            break
    #    if (direction == None):
    #        print("DEBUG: no preferred direction, so we want best ff option")
        
    # if the risk score is acceptably low, check that the flood fill is compatible
    if ((lowest_risk_score != -1) and (lowest_risk_score <= threshold)):
        print("DEBUG: risk score is acceptably low to choose preferred direction: {}".format(lowest_risk_score))
        temp_direction = check_ff_size(preferred_direction, ff_moves, my_size)
        if (temp_direction == preferred_direction):
            direction = temp_direction
    
    # almost last ditch - move to the area with best chance of survival
    if (direction == None):
        loop = 0
        last_score = 0
        same_count = 0

        for ffm0 in ff_moves:
            last_score = ffm0[1]
            break

        for ffm in ff_moves:
            loop += 1
            if (last_score == ffm[1]):
                same_count += 1
            last_score = ffm[1]

        first_direction = None
        for ffm2 in ff_moves:
            if (ffm2[0] in possible_moves):
                first_direction = ffm2[0]
                break

        if (loop == same_count):
            for rm in risk_moves:
                if (rm[0] in last_ditch_possible_moves):
                    if rm[0] in directions_of_my_tail:
                        direction = rm[0]
                        break
            print("DEBUG: Flood fill options all have same score.  Direction LR = {}".format(direction))
        else:
            if ((loop - same_count)/loop > 0.25):
                direction = first_direction
                print("TOMMM: {}".format((loop - same_count)/loop))
                print("DEBUG: Picking direction with highest ff - best survival chance = {}".format(direction))

    # if direction has not yet been set, take the highest empty flood fill option
    if (direction == None):
        for ffm in ff_moves:
            direction = check_ff_size(ffm[0], ff_moves, my_size)
            if (direction != None):
                print("DEBUG: selecting lowest ff = {}".format(direction))
                break
    
    # almost last ditch - move to the area with best chance of survival
    if (direction == None):
        for rm in risk_moves:
            if (rm[1] == lowest_risk_score):
                direction = rm[0]
                print("DEBUG: Picking direction with best survival chance = {}".format(direction))
                break

    # we are running out of options - get the first "possible" move from the unadulterated list

    if (direction == None):
        print("DEBUG: Last DITCH Possible Moves={}".format(last_ditch_possible_moves))
        for ldm in last_ditch_possible_moves:
            direction = ldm
            print("DEBUG: No options left - choose last ditch possible move: {}".format(direction))
            break
    
    # in trouble now - pick a random direction
    if (direction == None):
        direction = random.choice(["left", "right", "up", "down"])
        print("DEBUG: No options left - choose RANDOM direction: {}".format(direction))

    print("DEBUG: Direction={}".format(direction))
    return direction

@bottle.post('/move')
def move():
    data = bottle.request.json
    print(json.dumps(data))

    # Make a list of all the bad coordinates and try to avoid them
    height = data["board"]["height"]
    width = data["board"]["width"]

    # build list of bad coordinates
    bad_coords = populate_bad_coords(width, height)

    # build list of all snake coordinates on the board
    snakes = data["board"]["snakes"]
    snake_coords = populate_snake_coords(data)
    num_snakes = len(snakes)

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
    target = food_sorted_by_proximity[0]
    
    # specify health threshold to go get food
    health_threshold = 30
    if ((my_head == my_tail) or (my_health <= health_threshold) or (longer_snake != None)):
        print("DEBUG: Go get food")
    elif (shortest_length < len(data["you"]["body"])):
        print("DEBUG: Chase shortest snake")
        target["x"] = shortest_snake["body"][0]["x"]
        target["y"] = shortest_snake["body"][0]["y"]
    else:
        print("DEBUG: Chase my tail")
        target["x"] = my_tail["x"]
        target["y"] = my_tail["y"]

    # determine possible moves - remove any entries where we need to avoid snake heads
    possible_moves = get_possible_moves(my_head, my_tail, bad_coords, snake_coords)
    
    last_ditch_possible_moves = []
    for pm in possible_moves:
        last_ditch_possible_moves.append(pm)
    print("DEBUG: Last Ditch Possible Moves={}".format(last_ditch_possible_moves))

    avoid_heads = get_snake_heads_to_avoid(my_head, snake_heads, data)
    for ah in avoid_heads:
        if (ah in possible_moves):
            possible_moves.remove(ah)
    print("DEBUG: Possible Moves={}".format(possible_moves))

    # build array of preferred moves to get to target food or enemy
    preferred_moves = get_preferred_moves(my_head, target, possible_moves)

    # build array of directions sorted by risk level
    risk_moves = []
    tup = check_risky_business("up", my_head["y"] - 3, my_head["y"], my_head["x"] - 2, my_head["x"] + 2, snake_coords, possible_moves, data, width, height)    
    if (tup):
        risk_moves.append(tup)
    tup = check_risky_business("down", my_head["y"] + 1, my_head["y"] + 4, my_head["x"] - 2, my_head["x"] + 2, snake_coords, possible_moves, data, width, height)
    if (tup):
        risk_moves.append(tup)
    tup = check_risky_business("left", my_head["x"] - 4, my_head["x"] - 1, my_head["y"] - 2, my_head["y"] + 2, snake_coords, possible_moves, data, width, height)    
    if (tup):
        risk_moves.append(tup)
    tup = check_risky_business("right", my_head["x"] + 1, my_head["x"] + 4, my_head["y"]-2, my_head["y"]+2, snake_coords, possible_moves, data, width, height)
    if (tup):
        risk_moves.append(tup)
    if len(risk_moves) > 0:
        risk_moves.sort(key=lambda x: x[1])
    print("DEBUG: Risky Moves: {}".format(risk_moves))

    # build array of sizes of empty squares in flood fill of all four directions
    ff_moves = []
    if ("up" in last_ditch_possible_moves):
        ff_moves.append(("up", build_floodfill_move(width, height, snake_coords, data, my_head["x"], my_head["y"] - 1, my_head["y"], 0)))
    if ("down" in last_ditch_possible_moves):
        ff_moves.append(("down", build_floodfill_move(width, height, snake_coords, data, my_head["x"], my_head["y"] + 1, my_head["y"], height - 1)))
    if ("left" in last_ditch_possible_moves):
        ff_moves.append(("left", build_floodfill_move(width, height, snake_coords, data, my_head["x"] - 1, my_head["y"], my_head["x"], 0)))
    if ("right" in last_ditch_possible_moves):
        ff_moves.append(("right", build_floodfill_move(width, height, snake_coords, data, my_head["x"] + 1, my_head["y"], my_head["x"], width - 1)))        
    ff_moves.sort(key=lambda x: x[1], reverse=True)
    print("DEBUG: FF Moves: {}".format(ff_moves))

    # final decision
    m = build_matrix(width, height, data, snake_coords)
    direction = make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, risk_moves, ff_moves, my_size, data, m, snake_heads, snake_tails)

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