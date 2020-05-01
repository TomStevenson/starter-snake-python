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

    color = "#3dcd58"

    return start_response(color)

def get_food_risk(current_food_x, current_food_y, my_head, data):
    retval = 0
    snake_heads = get_snake_array(0, data)
    last_score = 999999
    for sh in snake_heads:
        if (sh != data["you"]):
            if (is_snake_longer_than_me(data, sh) == False):
                current_distance = [99, 99]
                current_distance[0] = abs(my_head["x"] - current_food_x)
                current_distance[1] = abs(my_head["y"] - current_food_y)
                current_score = current_distance[0] + current_distance[1]
                if current_score < last_score:
                    last_score = current_score
    retval = last_score
    return retval

def this_is_a_corner(x, y, data):
    retval = False
    height = data["board"]["height"]
    width = data["board"]["width"]
    if (x == 0 and y == 0):
        retval = True
    elif ((x == (width - 1)) and (y == 0)):
        retval = True
    elif ((x == (width - 1)) and (y == (height - 1))):
        retval == True
    elif ((x == 0) and (y == (height - 1))):
        retval == True
    else:
        retval = False
    return retval

def get_food_list(snake_head, data):
    closest = []
    last_score = 999999
    #food_risk = 999999
    l = []
    for current_food in data["board"]["food"]:
        current_distance = [99, 99]
        current_distance[0] = abs(snake_head["x"] - current_food["x"])
        current_distance[1] = abs(snake_head["y"] - current_food["y"])
        current_score = current_distance[0] * current_distance[1]
        if current_score < last_score:
            fr = get_food_risk(current_food["x"], current_food["y"], snake_head, data)
            print("DEBUG: Food Risk: {}".format(fr))
            if (fr >= 3):
                if (this_is_a_corner(current_food["x"], current_food["y"], data) == False):
                    closest = current_food
                    last_score = current_score
            else:
                print("DEBUG: Food identified as high risk - ignoring")
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
        test = (snake["body"][0]["x"], snake["body"][0]["y"])
        if (snake_head == test):
            if (snake != data["you"] and (len(snake["body"]) >= (len(data["you"]["body"]) - 1))):
                #print("DEBUG: Snake is longer than me !")
                longer_snake = True
                break
    return longer_snake

def which_directions_are_away_from_snake_heads(my_head, snake_heads, data, possible_moves):
    retval = []
    for sh in snake_heads:
        if (is_snake_longer_than_me(data, sh)):
            x = my_head["x"] - sh[0]
            if (x > 0):
                if ("right" not in snake_heads):
                    if ("right" in possible_moves):
                        retval.append("right")
            if (x < 0):
                if ("left" not in snake_heads):
                    if ("left" in possible_moves):
                        retval.append("left")
            y = my_head["y"] - sh[1]
            if (y > 0):
                if ("down" not in snake_heads):
                    if ("down" in possible_moves):
                        retval.append("down")
            if (y < 0):
                if ("up" not in snake_heads):
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
def populate_snake_coords(data, exclude_tails):
    snakeCoords= []
    snake_tails = get_snake_array(-1, data)
    for snake in data["board"]["snakes"]:
        for xycoord in snake["body"]:
            bad = (xycoord["x"], xycoord["y"])
            if ((exclude_tails == False) or (bad not in snake_tails)):
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
    temp = []
    test_areas = []
    test_areas.append((my_head["x"] - 1, my_head["y"]))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] - 2, my_head["y"]))
    temp = test_for_snake_head("left", test_areas, snake_heads, data)
    test_areas.clear()
    test_areas.append((my_head["x"] + 1, my_head["y"]))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 2, my_head["y"]))
    temp = temp + test_for_snake_head("right", test_areas, snake_heads, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] - 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"], my_head["y"] - 2))
    temp = temp + test_for_snake_head("up", test_areas, snake_heads, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] + 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"], my_head["y"] + 2))
    temp = temp + test_for_snake_head("down", test_areas, snake_heads, data)
    print("DEBUG: Avoid Head Moves: {}".format(temp))
    return temp

def edge_check(move, width, height, data):
    retval = 0
    factor = 5
    snake_heads = get_snake_array(0, data)
    my_head = data["you"]["body"][0]

    if (move == "up"):
        reference = 0
        if (my_head["x"] == 0):
            reference = 1
            for y in range(my_head["y"] - 4, my_head["y"] + 1):
                if (y >= 0):
                    test_point = (reference, y)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
        
        reference = width - 2
        if (my_head["x"] == (width - 1)):
            for y in range(my_head["y"] - 4, my_head["y"] + 1):
                if (y >= 0):
                    test_point = (reference, y)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
    
    if (move == "down"):
        reference = 0
        if (my_head["x"] == 0):
            reference = 1
            for y in range(my_head["y"] - 1, my_head["y"] + 4):
                if (y <= height - 1):
                    test_point = (reference, y)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
        
        reference = width - 2
        if (my_head["x"] == (width - 1)):
            for y in range(my_head["y"] - 1, my_head["y"] + 4):
                if (y <= height - 1):
                    test_point = (reference, y)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
    
    if (move == "left"):
        reference = 0
        if (my_head["y"] == 0):
            reference = 1
            for x in range(my_head["x"] - 4, my_head["x"] + 1):
                if (x >= 0):
                    test_point = (x, reference)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
        
        reference = height - 2
        if (my_head["y"] == (height - 1)):
            for x in range(my_head["x"] - 4, my_head["x"] + 1):
                if (x <= width - 1):
                    test_point = (x, reference)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
    
    if (move == "right"):
        reference = 0
        if (my_head["y"] == 0):
            reference = 1
            for x in range(my_head["x"] - 1, my_head["x"] + 4):
                if (x >= 0):
                    test_point = (x, reference)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
        
        reference = height - 2
        if (my_head["y"] == (height - 1)):
            for x in range(my_head["x"] - 1, my_head["x"] + 4):
                if (x <= width - 1):
                    test_point = (x, reference)
                    if (test_point in snake_heads):
                        retval = factor
                        print(" DEBUG: FAILED EDGE CHECK !  BAD DIRECTION !: {}".format(move))
                        break
    
    print(" DEBUG: Edge check: {}".format(retval))
    return retval

def move_to_edge(move, width, height, data):
    retval = 0
    factor = 0.2
    my_head = data["you"]["body"][0]
    if (move == "left"):
        if ((my_head["x"] - 1) == 0):
            retval = factor
    if (move == "right"):
        if ((my_head["x"] + 1) == width - 1):
            retval = factor
    if (move == "up"):
        if ((my_head["y"] - 1) == 0):
            retval = factor
    if (move == "down"):
        if ((my_head["y"] + 1) == height - 1):
            retval = factor
    print(" DEBUG: Move to Edge: {}".format(retval))
    return retval

# check_risky_business: builds a tuple of move direction and its associated risk score
# a1, a2, b1, b2: x and y to and from coordinates to scan
# snake_coords: array of all snake coordinates
# possible_moves: array of possible moves
# data: json payload from game
# width, height: dimensions of the board
# returns: tuple of move direction and risk score
def check_risky_business(move, a1, a2, b1, b2, snake_coords, possible_moves, data, width, height):
    #snakes = data["board"]["snakes"]
    tup = None
    if (move in possible_moves):
        print("DEBUG: Checking risk in direction: {}".format(move))
        risk_area = 0
        scan = scan_matrix(build_matrix(width, height, snake_coords, data), width, height, possible_moves, get_snake_array(0, data), get_snake_array(-1, data), data)
        ec = edge_check(move, width, height, data)
        mte = move_to_edge(move, width, height, data)
        sv = 0
        for s in scan:
            if (s[0] == move):
                sv = s[1]
                break
        tup = (move, risk_area + sv + ec + mte)
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
def build_matrix(width, height, snake_coords, data):
    snake_tails = get_snake_array(-1, data)
    matrix = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            if ((testCoord in snake_coords) and (testCoord not in snake_tails)):
                matrix[x][y] = 's'
            else:
                matrix[x][y] = 'e'
    return matrix

def scan_matrix(matrix, width, height, possible_moves, snake_heads, snake_tails, data):
    left = 0
    right = 0
    up = 0
    down = 0
    my_head = data["you"]["body"][0]
    for x in range(width):
        for y in range(height):
            test = (x, y)
            me = (my_head["x"], my_head["y"])
            if (test != me):
                if ((x <= (width / 2)) and (matrix[x][y] == 's')):
                    if (test in snake_heads):
                        left += 20
                    else:
                        left += 0
                if ((y > (height / 2)) and (matrix[x][y] == 's')):
                    if (test in snake_heads):
                        down += 20
                    else:
                        down += 0
                if ((y <= (height / 2)) and (matrix[x][y] == 's')):
                    if (test in snake_heads):
                        up += 20
                    else:
                        up += 0
                if ((x > (width / 2)) and (matrix[x][y] == 's')):
                    if (test in snake_heads):
                        right += 20
                    else:
                        right += 0
    retval = []
    area = (round(width / 2) * round(height / 2))
    if ("left" in possible_moves):
        retval.append(("left", left / area))
    if ("right" in possible_moves):
        retval.append(("right", right / area))
    if ("up" in possible_moves):
        retval.append(("up", up / area))
    if ("down" in possible_moves):
        retval.append(("down", down / area))
    retval.sort(key=lambda x: x[1])
    print(" DEBUG: scan matrix: {}".format(retval))
    return retval

# floodfill_algorithm: recusive function to floodfill the provided matrix
# matrix: matrix representing board with snake coordinates on it
# x,y: coordinates to test
# count: variable to count the number of empty squares on flood fill
# snake_coords: array of all snake part locations
# returns: count of all empty squares on flood fill
def floodfill_algorithm(matrix, x, y, count):
    if matrix[x][y] == 'e':  
        matrix[x][y] = ' '
        count += 1
        if x > 0:
            count = floodfill_algorithm(matrix, x-1, y, count)
        if x < len(matrix[y]) - 1:
            count = floodfill_algorithm(matrix, x+1, y, count)
        if y > 0:
            count = floodfill_algorithm(matrix, x, y-1, count)
        if y < len(matrix[x]) - 1:
            count = floodfill_algorithm(matrix, x, y+1, count)
    return count

# build_floodfill_move: helper function to call floodfill algorithm
def build_floodfill_move(width, height, snake_coords, data, x, y, test1, test2):
    ff = 0
    if (test1 != test2):
        ff = floodfill_algorithm(build_matrix(width, height, snake_coords, data), x, y, 0)
    return ff

def check_for_clear_path(matrix, direction, x, y, my_tail):
    x_factor = 0
    y_factor = 0
    if (direction == "left"):
        x_factor = -1
    if (direction == "right"):
        x_factor = 1
    if (direction == "up"):
        y_factor = -1
    if (direction == "down"):
        y_factor = 1
    retval = clear_path_to_my_tail(matrix, x + x_factor, y + y_factor, my_tail)
    return retval

def clear_path_to_my_tail(matrix, x, y, my_tail):
    retval = False
    if matrix[x][y] == 'e':  
        test = (x, y)
        #print(test)
        tail_point = (my_tail["x"], my_tail["y"])
        #print(tail_point)
        if test == tail_point:
            return True
        matrix[x][y] = ' '
        if x > 0:
            r = clear_path_to_my_tail(matrix, x - 1, y, my_tail)
            if (r == True):
                return True
        if x < len(matrix[y]) - 1:
            r = clear_path_to_my_tail(matrix, x + 1, y, my_tail)
            if (r == True):
                return True
        if y > 0:
            r = clear_path_to_my_tail(matrix, x, y - 1, my_tail)
            if (r == True):
                return True
        if y < len(matrix[x]) - 1:
            r = clear_path_to_my_tail(matrix, x, y + 1, my_tail)
            if (r == True):
                return True
    return retval

def clear_path_to_a_tail(matrix, x, y, data):
    retval = False
    snake_tails = get_snake_array(-1, data)
    for st in snake_tails:
        retval = clear_path_to_my_tail(matrix, x, y, st)
        if (retval == True):
            break
    return retval

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
    if (ff_size >= my_size - 1):
        new_direction = direction
        #print("DEBUG: choosing supplied direction: {}".format(new_direction))
        if (ff_size < 2*my_size):
            print("DEBUG: DID I GET IN TROUBLE?: {}".format(new_direction))
            direction = None
    else:
        print("DEBUG: Floodfill size in supplied direction too small: {}".format(direction))
        new_direction = None
    return new_direction

def did_snake_not_grow(snake):
    retval = False
    snake_length = len(snake["body"])
    if (snake_length >= 3):
        tail = snake["body"][snake_length - 1]
        tail_minus = snake["body"][snake_length - 2]
        if (tail != tail_minus):
            print("DEBUG: Snake DID NOT GROW")
            retval = True
        else:
            print("DEBUG: Snake ate last round so grew !")
            retval = False
    return retval

def is_move_my_tail(my_head, snakes, my_size):
    retval = []
    if (my_size >= 3):
        for snake in snakes:
            the_size = len(snake["body"]) - 1
            the_tail = (snake["body"][the_size]["x"], snake["body"][the_size]["y"])
           
            # build test points
            up = (my_head["x"], my_head["y"] - 1)
            down = (my_head["x"], my_head["y"] + 1)
            left = (my_head["x"] - 1, my_head["y"])
            right = (my_head["x"] + 1, my_head["y"])
            
            #test points
            if (up == the_tail):
                if ("up" not in retval):
                    if (did_snake_not_grow(snake)):
                        retval.append("up")
            if (down == the_tail):
                if ("down" not in retval):
                    if (did_snake_not_grow(snake)):
                        retval.append("down")
            if (left == the_tail):
                if ("left" not in retval):
                    if (did_snake_not_grow(snake)):
                        retval.append("left")
            if (right == the_tail):
                if ("right" not in retval):
                    if (did_snake_not_grow(snake)):
                        retval.append("right")
    return retval
    
def scan_empty_quadrant(matrix, width, height, possible_moves, my_head, data):
    retval = []
    # initalize counter variables
    q1 = 0
    q2 = 0
    q3 = 0
    q4 = 0
    snake_heads = get_snake_array(0, data)
    head_test = (my_head["x"], my_head["y"])
    head_q = None
    for x in range(round(width/2)):
        for y in range(round(height/2)):
            test = (x, y)
            if (test == head_test):
                head_q = "q1"
            if (matrix[x][y] == 'e'):
                q1 += 1
            if (test in snake_heads):
                q1 -= 5

    for x in range(round(width/2), width):
        for y in range(round(height/2)):
            test = (x, y)
            if (test == head_test):
                head_q = "q2"
            if (matrix[x][y] == 'e'):
                q2 += 1
            if (test in snake_heads):
                q2 -= 5

    for x in range(round(width/2)):
        for y in range(round(height/2), height):
            test = (x, y)
            if (test == head_test):
                head_q = "q3"
            if (matrix[x][y] == 'e'):
                q3 += 1
            if (test in snake_heads):
                q3 -= 5
    
    for x in range(round(width/2), width):
        for y in range(round(height/2), height):
            test = (x, y)
            if (test == head_test):
                head_q = "q4"
            if (matrix[x][y] == 'e'):
                q4 += 1
            if (test in snake_heads):
                q4 -= 5
    
    retval.append(("q1", q1))
    retval.append(("q2", q2))
    retval.append(("q3", q3))
    retval.append(("q4", q4))
     
    point = max(retval,key=lambda item:item[1])[0]
    # print("max = {}".format(point))
    tt = []
    if ((point == "q1") and (head_q != "q1")):
        if ("up" in possible_moves):
            if (my_head["y"] >= height/2):
                tt.append("up")
        if ("left" in possible_moves):
            if (my_head["x"] >= width/2):
                tt.append("left")
    if ((point == "q2") and (head_q != "q2")):
        if ("right" in possible_moves):
            if (my_head["x"] <= width/2):
                tt.append("right")
        if ("up" in possible_moves):
            if (my_head["y"] >= height/2):
                tt.append("up")
    if ((point == "q3") and (head_q != "q3")):
        if ("left" in possible_moves):
            if (my_head["x"] >= width/2):
                tt.append("left")
        if ("down" in possible_moves):
            if (my_head["y"] <= height/2):
                tt.append("down")
    if ((point == "q4") and (head_q != "q4")):
        if ("right" in possible_moves):
            if (my_head["x"] <= width/2):
                tt.append("right")
        if ("down" in possible_moves):
            if (my_head["y"] <= height/2):
                tt.append("down")
    
    return tt

# helper function to return a list of first elements in a dictionary
def extract_1(lst): 
    return [item[0] for item in lst] 

def snake_head_test(data, a, b):
    retval = False
    snake_heads = get_snake_array(0, data)
    test = (a, b)
    if (test in snake_heads):
        retval = True
    return retval

def get_kill_moves(possible_moves, data):
    preferred_moves_modified = []
    my_head = data["you"]["body"][0]
    height = data["board"]["height"]
    width = data["board"]["width"]
    if ("left" in possible_moves):
        if (my_head["y"] == 1):
            if (snake_head_test(data, my_head["x"] + 1,  my_head["y"] - 1)):
                preferred_moves_modified.append("left")   
        if (my_head["y"] == (height - 2)):
            if (snake_head_test(data, my_head["x"] + 1,  my_head["y"] + 1)):
                preferred_moves_modified.append("left")   
    if ("right" in possible_moves):
        if (my_head["y"] == 1):
            if (snake_head_test(data, my_head["x"] - 1,  my_head["y"] - 1)):
                preferred_moves_modified.append("right")   
        if (my_head["y"] == (height - 2)):
            if (snake_head_test(data, my_head["x"] - 1,  my_head["y"] + 1)):
                preferred_moves_modified.append("right")  
    if ("up" in possible_moves):
        if (my_head["x"] == 1):
            if (snake_head_test(data, my_head["y"] + 1,  my_head["x"] - 1)):
                preferred_moves_modified.append("up")   
        if (my_head["x"] == (width - 2)):
            if (snake_head_test(data, my_head["y"] + 1,  my_head["x"] + 1)):
                preferred_moves_modified.append("up")   
    if ("down" in possible_moves):
        if (my_head["x"] == 1):
            if (snake_head_test(data, my_head["y"] - 1,  my_head["x"] - 1)):
                preferred_moves_modified.append("down")   
        if (my_head["x"] == (width - 2)):
            if (snake_head_test(data, my_head["y"] - 1,  my_head["x"] + 1)):
                preferred_moves_modified.append("down") 
        
    if (len(preferred_moves_modified) > 0):
        print("DEBUG: Attempting straight line kill of snake: {}".format(preferred_moves_modified))
    return preferred_moves_modified    

def modify_preferred_moves(preferred_moves, possible_moves, data, hungry):
    preferred_moves_modified = []
    my_head = data["you"]["body"][0]
    height = data["board"]["height"]
    width = data["board"]["width"]
    for pm in preferred_moves:
        if pm == "up":
            if (((my_head["y"] - 1) != 0) or (my_head["x"] != 0) or (my_head["x"] != (width - 1)) or (hungry == True)):
                if ("up" not in preferred_moves_modified):
                    preferred_moves_modified.append("up")
        if pm == "down":
            if (((my_head["y"] + 1) != (height - 1)) or (my_head["x"] != 0) or (my_head["x"] != (width - 1)) or (hungry == True)):
                if ("down" not in preferred_moves_modified):
                    preferred_moves_modified.append("down")
        if pm == "left":
            if (((my_head["x"] - 1) != 0) or (my_head["y"] != 0) or (my_head["y"] != (height - 1)) or (hungry == True)):
                if ("left" not in preferred_moves_modified):
                    preferred_moves_modified.append("left")
        if pm == "right":
            if (((my_head["x"] - 1) != (width - 1)) or (my_head["y"] != 0) or (my_head["y"] != (height - 1)) or (hungry == True)):
                if ("right" not in preferred_moves_modified):
                    preferred_moves_modified.append("right")
    return preferred_moves_modified


def validate_move(move, risk_moves, ff_moves, my_size, m, x, y, my_tail, data):
    retval = False
    if (check_ff_size(move, ff_moves, my_size)):
        retval = True
        print("DEBUG: validate_move: floodfill size ok {}".format(move))
    else:
        cp = clear_path_to_a_tail(m, x, y, data)
        if (cp == True):
            retval = True
            print("DEBUG: We have a clear path to tail: {}".format(move))
        else:
            print("DEBUG: No clear path to a tail: {}".format(move))
    
    if (len(risk_moves) > 1):
        for lrm in risk_moves:
            if (lrm[0] == move):
                if (lrm[1] >= 5.0):
                    retval = False
                break
    print("DEBUG: Validated Move! :{}".format(move))
    return retval

# make_decision: logic to pick the desired move of the snake
# preferred_moves: array of the preffered directions to move to get to target
# last_ditch_possible_moves: array of possible moves before they have been filtered to use as last resort
# risk_moves: array of riskiest moves sorted least to most
# ff_moves: array of flood fill moves sorted best to worst
# my_size: length of my snake
# returns: final direction to move
def make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, risk_moves, ff_moves, ff_moves_no_tails, my_size, data, m, snake_heads, snake_tails, hungry):
    # final decision
    direction = None
    
    my_head = data["you"]["body"][0]
    my_size = len(data["you"]["body"])
    my_tail = data["you"]["body"][my_size-1]
    height = data["board"]["height"]
    width = data["board"]["width"]
    
    preferred_moves_modified = modify_preferred_moves(preferred_moves, possible_moves, data, hungry)
    print("DEBUG: Modified Preferred Moves: {}".format(preferred_moves_modified))

    tail_moves = is_move_my_tail(my_head, data["board"]["snakes"], my_size)
    if (my_size > 3):
        for tm in tail_moves:
            if tm not in possible_moves:
                possible_moves.append(tm)
            if tm not in extract_1(risk_moves):
                risk_moves.append((tm, 0.0))
            if tm not in extract_1(ff_moves):
                ff_moves.append((tm, 999999))
    print("DEBUG: Tail Moves!: {}".format(tail_moves))

    away_from_heads = which_directions_are_away_from_snake_heads(my_head, get_snake_array(0, data), data, possible_moves)
    print("DEBUG: Directions away snake heads = {}".format(away_from_heads))
    
    # kill
    preferred_direction = None
    for kill in get_kill_moves(possible_moves, data):
        preferred_direction = kill
        print("DEBUG: Kill move = {}".format(preferred_direction))
        if (validate_move(preferred_direction, risk_moves, ff_moves, my_size, m, my_head["x"], my_head["y"], my_tail, data) == True):
            direction = preferred_direction
            break

    # preferred direction
    preferred_direction = None
    if (direction == None):
        for pd in get_common_elements(extract_1(risk_moves),preferred_moves_modified):
            preferred_direction = pd
            print("DEBUG: Preferred direction modified = {}".format(preferred_direction))
            if (validate_move(preferred_direction, risk_moves, ff_moves, my_size, m, my_head["x"], my_head["y"], my_tail, data) == True):
                direction = preferred_direction
                break
    
    if (direction == None):
        for pd in get_common_elements(extract_1(risk_moves),preferred_moves):
            preferred_direction = pd
            print("DEBUG: Preferred direction = {}".format(preferred_direction))
            if (validate_move(preferred_direction, risk_moves, ff_moves, my_size, m, my_head["x"], my_head["y"], my_tail, data) == True):
                direction = preferred_direction
                break

    if (direction == None):
        for pm in possible_moves:
            possible_direction = pm
            print("DEBUG: Possible direction = {}".format(possible_direction))
            if (validate_move(possible_direction, risk_moves, ff_moves, my_size, m, my_head["x"], my_head["y"], my_tail, data) == True):
                direction = possible_direction
                break

        #snake_coords = populate_snake_coords(data, False)
        #matrix = build_matrix(width, height, snake_coords, data)
        #affinity_moves = scan_empty_quadrant(matrix, width, height, possible_moves, my_head, data)
        #for am in affinity_moves:
        #    temp_direction = am
        #    break

    if (direction == None):
        for rm in risk_moves:
            if (clear_path_to_a_tail(m, my_head["x"], my_head["y"], data)):
                print("DEBUG: Lowest risk with clear path to a tail={}".format(rm[0]))
                direction = rm[0]
                break
            
    # we are running out of options - get the first "possible" move from the unadulterated list
    if (direction == None):
        print("DEBUG: Last Ditch Possible Moves={}".format(last_ditch_possible_moves))
        for ldm in last_ditch_possible_moves:
            if (clear_path_to_my_tail(m, my_head["x"], my_head["y"], my_tail)):
                direction = ldm
                print("DEBUG: No options left - choose clear path to tail: {}".format(direction))
                break
            if (check_ff_size(ldm, ff_moves, my_size) == True):
                direction = ldm
                print("DEBUG: No options left - choose floodfill size: {}".format(direction))
                break
    
    if (direction == None):
        print("DEBUG: Last Ditch Possible Moves={}".format(last_ditch_possible_moves))
        for ldm in last_ditch_possible_moves:
            direction = ldm
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
    snake_coords = populate_snake_coords(data, False)
    snake_coords_no_tails = populate_snake_coords(data, True)
    #num_snakes = len(snakes)

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
    target = {}
    target["x"] = my_tail["x"]
    target["y"] = my_tail["y"]
    first = food_sorted_by_proximity.pop(0)
    if (len(first) > 0):
        target = first
    else:
        print("DEBUG: No suitable food !")
    print("DEBUG: Initial Target: {}".format(target))
    
    # specify health threshold to go get food
    health_threshold = 30
    hungry = False
    if (my_health <= health_threshold):
        print("DEBUG: I am hungry")
        hungry = True

    if ((my_head == my_tail) or (hungry == True) or (longer_snake != None)):
        print("DEBUG: Go get food")
        hungry = True
    elif (shortest_length < len(data["you"]["body"])):
        print("DEBUG: Chase shortest snake")
        target["x"] = shortest_snake["body"][0]["x"]
        target["y"] = shortest_snake["body"][0]["y"]
    else:
        print("DEBUG: Chase my tail")
        target["x"] = my_tail["x"]
        target["y"] = my_tail["y"]
    
    print("DEBUG: Updated Target: {}".format(target))

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

    ff_moves_no_tails = []
    if ("up" in last_ditch_possible_moves):
        ff_moves_no_tails.append(("up", build_floodfill_move(width, height, snake_coords_no_tails, data, my_head["x"], my_head["y"] - 1, my_head["y"], 0)))
    if ("down" in last_ditch_possible_moves):
        ff_moves_no_tails.append(("down", build_floodfill_move(width, height, snake_coords_no_tails, data, my_head["x"], my_head["y"] + 1, my_head["y"], height - 1)))
    if ("left" in last_ditch_possible_moves):
        ff_moves_no_tails.append(("left", build_floodfill_move(width, height, snake_coords_no_tails, data, my_head["x"] - 1, my_head["y"], my_head["x"], 0)))
    if ("right" in last_ditch_possible_moves):
        ff_moves_no_tails.append(("right", build_floodfill_move(width, height, snake_coords_no_tails, data, my_head["x"] + 1, my_head["y"], my_head["x"], width - 1)))        
    ff_moves_no_tails.sort(key=lambda x: x[1], reverse=True)
    print("DEBUG: FF Moves No Tails: {}".format(ff_moves_no_tails))


    # final decision
    m = build_matrix(width, height, snake_coords, data)
    direction = make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, risk_moves, ff_moves, ff_moves_no_tails, my_size, data, m, snake_heads, snake_tails, hungry)

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