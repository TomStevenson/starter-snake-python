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

    color = "#f00000"

    return start_response(color)

# get_food_list: scans the food array and finds the closest food to my snake head
# my_head: coordinates of my snake head to be used as the reference point to food
# data: generic game data to get the food list from
# returns: coordinates of the closest food
def get_food_list(my_head, data):
    closest = []
    last_score = 999999
    l = []
    for current_food in data["board"]["food"]:
        current_distance = [99, 99]
        current_distance[0] = abs(my_head["x"] - current_food["x"])
        current_distance[1] = abs(my_head["y"] - current_food["y"])
        current_score = current_distance[0] * current_distance[1]
        if current_score < last_score:
            closest = current_food
            last_score = current_score 
    l.append(closest)
    return l

# get_food_list: fetches first element from x that is common for both lists
# x,y: lists to search for common element in
# returns: common element if found, None otherwise
def get_first_common_element(x,y):
    for i in x:
        if i in y:
            return i
    return None

# is_snake_longer_than_me: helper function that determines if the supplied snake is longer
# data: game data to obtain snakes, my snake information from
# snake_head: the snake_head to test if longer than me
# returns: True if snake_head snake is longer than me, False otherwise
def is_snake_longer_than_me(data, snake_head):
    longer_snake = False
    for snake in data["board"]["snakes"]:
        if (snake_head == snake["body"][0]):
            if (snake != data["you"] and (len(snake["body"]) >= (len(data["you"]["body"]) - 1))):
                print("DEBUG: Snake is longer than me !")
                longer_snake = True
                break
    return longer_snake

# which_directions_are_away_from_snake_heads: helper function that determines directions away from bigger snakes
# my_head: coordinates of my snake head
# data: game data to obtain snakes, my snake information from
# possible_moves: list of the possible moves the snake can make
# returns: True if snake_head snake is longer than me, False otherwise
def which_directions_are_away_from_snake_heads(my_head, data, possible_moves):
    retval = []
    snake_heads = get_snake_array(0, data)
    for sh in snake_heads:
        if (is_snake_longer_than_me(data, sh)):
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
    for y in range(height):
        bad = (-1, y)
        badCoords.append(bad)
        bad = (width, y)
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
    # remove my tail from snake coords
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
# data: json structure provided
# returns: returns an array of bad directions that will encounter snake heads
def test_for_snake_head(direction, coords_to_test, data):
    snake_heads = get_snake_array(0, data)
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
                        #print("DEBUG: Avoid snake head!")
    return heads_to_avoid

# get_snake_heads_to_avoid: checks for other snake headsin all directions
# my_head: coordinates of my snake head
# data: json structure provided
# returns: returns an array of bad directions that will encounter snake heads
def get_snake_heads_to_avoid(my_head, data):
    temp = []
    test_areas = []
    test_areas.append((my_head["x"] - 1, my_head["y"]))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] - 2, my_head["y"]))
    test_areas.append((my_head["x"] - 2, my_head["y"] - 1))
    test_areas.append((my_head["x"] - 2, my_head["y"] + 1))
    temp = test_for_snake_head("left", test_areas, data)
    test_areas.clear()
    test_areas.append((my_head["x"] + 1, my_head["y"]))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 2, my_head["y"]))
    test_areas.append((my_head["x"] + 2, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 2, my_head["y"] + 1))
    temp = temp + test_for_snake_head("right", test_areas, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] - 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 1))
    test_areas.append((my_head["x"], my_head["y"] - 2))
    test_areas.append((my_head["x"] - 1, my_head["y"] - 2))
    test_areas.append((my_head["x"] + 1, my_head["y"] - 2))
    temp = temp + test_for_snake_head("up", test_areas, data)
    test_areas.clear()
    test_areas.append((my_head["x"], my_head["y"] + 1))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 1))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 1))
    test_areas.append((my_head["x"], my_head["y"] + 2))
    test_areas.append((my_head["x"] - 1, my_head["y"] + 2))
    test_areas.append((my_head["x"] + 1, my_head["y"] + 2))
    temp = temp + test_for_snake_head("down", test_areas, data)
    print("DEBUG: Avoid Head Moves: {}".format(temp))
    return temp

# check_risky_business: builds a tuple of move direction and its associated risk score
# move: desired move direction to test
# snake_coords: array of all snake coordinates
# possible_moves: array of possible moves
# data: json payload from game
# width, height: dimensions of the board
# returns: tuple of move direction and risk score
def check_risky_business(move, snake_coords, possible_moves, data, width, height):
    snakes = data["board"]["snakes"]
    my_head = data["you"]["body"][0]
    tup = None

    if (move in possible_moves):
        scan = scan_matrix(build_matrix(width, height, data, snake_coords), width, height, possible_moves, data)
        # get the scan value for the supplied move
        sv = 0
        for s in scan:
            if (s[0] == move):
                sv = s[1]
                break
        
        move_to_edge = 0
        mte_factor = 0.1
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
                mid_point = round(width / 2)
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
                mid_point = round(height / 2)
                r_calc = abs(mid_point - p_to_test)
                edge_factor = r_calc / height
                edges_adjust += edge_factor
        print(" DEBUG: risky business: {}".format(move))
        print("     DEBUG: sv: {}".format(sv))
        print("     DEBUG: edges adjust: {}".format(0.1 * edges_adjust))
        print("     DEBUG: move to edge: {}".format(move_to_edge))
        tup = (move, (sv + 0.1 * edges_adjust + move_to_edge))
    return tup

# get_directions_of_my_tail: builds a list of directions to get to my tail
# my_head: coordinates of my snake head
# my_tail: coordinates of my snake tail
# possible_moves: list of possible moves my snake can make
# returns: list of possible directions to get to tail
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
    print("DEBUG: Directions of my tail: {}".format(directions))
    return directions

# build_matrix: builds a matrix populated with the whereabouts of the snakes
# width/height: size of the matrix
# snake_coords: array of all snake coords on the board
# returns: a matrix with 's' where a snake part exists, and 'e' where none exists
def build_matrix(width, height, data, snake_coords):
    matrix = [[0 for x in range(width)] for y in range(height)]
    for x in range(width):
        for y in range(height):
            testCoord = (x, y)
            if (testCoord in snake_coords):
                matrix[x][y] = 's'
            else:
                matrix[x][y] = 'e'
    return matrix

# calculate_risk_factor: helper function to sum risk factors of heads/tails/me
# test_point: coordinate to test
# snake_heads: list of snake head coords on the board
# snake_tails: list of snake tail coords on the board
# me: snake array of me
def calculate_risk_factor(test_point, snake_heads, snake_tails, me):
    retval = 0
    # scale factor initialization
    h_f = 8
    t_f = 5
    m_f = 0.4
    if (test_point in snake_heads):
        retval += h_f
    elif (test_point in snake_tails):
        retval -= t_f
    elif (test_point in me):
        retval += m_f
    else:
        retval += m_f
    return retval

# scan_matrix: builds a matrix populated with the whereabouts of the snakes
# width/height: size of the matrix
# possible_moves: list of possible moves our snake could take
# data: json payload of game data
# returns: a list of possible directions and their calculated risk
def scan_matrix(matrix, width, height, possible_moves, data):
    retval = []
    # obtain needed snake info from data
    snake_heads = get_snake_array(0, data)
    snake_tails = get_snake_array(-1, data)
    my_head = data["you"]["body"][0]
    me = data["you"]["body"]
    # initalize counter variables
    left = 0
    right = 0
    up = 0
    down = 0
    for x in range(width):
        for y in range(height):
            test = (x, y)
            if ((x <= my_head["x"]) and (matrix[x][y] == 's')):
                left += calculate_risk_factor(test, snake_heads, snake_tails, me)
            if ((y >= my_head["y"]) and (matrix[x][y] == 's')):
                down += calculate_risk_factor(test, snake_heads, snake_tails, me)
            if ((y <= my_head["y"]) and (matrix[x][y] == 's')):
                up += calculate_risk_factor(test, snake_heads, snake_tails, me)
            if ((x >= my_head["x"]) and (matrix[x][y] == 's')):
                right += calculate_risk_factor(test, snake_heads, snake_tails, me)

    scale_factor = 0.01
    if ("left" in possible_moves):
        retval.append(("left", left*scale_factor))
    if ("right" in possible_moves):
        retval.append(("right", right*scale_factor))
    if ("up" in possible_moves):
        retval.append(("up", up*scale_factor))
    if ("down" in possible_moves):
        retval.append(("down", down*scale_factor))
    
    retval.sort(key=lambda x: x[1])
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
    my_size = len(data["you"]["body"])
    retval = 0
    ff = 0
    if (test1 != test2):
        ff = floodfill_algorithm(build_matrix(width, height, data, snake_coords), x, y, 0, snake_coords)
        if (ff >= my_size + 1):
            retval = ff
        else:
            retval = 0
    return retval

# get_ff_size: helper function to get risk score for provided direction
# direction: desired direction
# ff_moves: array of flood fill information
# returns: size of specified flood fill
def get_ff_size(direction, ff_moves, data):
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
def check_ff_size(direction, ff_moves, data):
    my_size = len(data["you"]["body"])
    new_direction = None
    ff_size = get_ff_size(direction, ff_moves, data)
    if ((ff_size) >= my_size):
        new_direction = direction
        print("DEBUG: choosing supplied direction: {}".format(new_direction))
    else:
        print("DEBUG: Floodfill size in preferred direction too small: {}".format(direction))
        new_direction = None
    return new_direction

# get_weight: helper function to return the weight for the supplied vote
def get_weight(weight, vote):
    retval = 0.0
    for x in weight:
        if (x[0] == vote):
            retval = x[1] * 1.0
            break
    return retval

# get_risk: helper function to return the risk value for the supplied move
def get_risk(move, risk_moves):
    retval = 0.0
    if (move != None):
        for rm in risk_moves:
            if (rm[0] == move):
                retval = rm[1] * 1.0
                break
    return retval

# vote: function to tally votes in the supplied list
# votes_table: dictionary of existing votes
# votes: new votes to tally and add to votes_table
# weight: scaling factor to apply to votes
# returns: updated votes_table
def vote(votes_table, votes, weight = 1.0):
    for vote in votes:
        if vote in votes_table:
            votes_table[vote] += weight
        else:
            votes_table[vote] = weight
    return votes_table

# vote_with_weights: function to tally votes in the supplied list with weights supplied in dictionary
# votes_table: dictionary of existing votes
# votes: new votes to tally and add to votes_table
# weights: dictionary of weights to apply
# returns: updated votes_table
def vote_with_weights(votes_table, votes, weights):
    for vote in votes:
        w = get_weight(weights, vote)
        if vote in votes_table:
            votes_table[vote] += w
        else:
            votes_table[vote] = w
    return votes_table

# vote_with_risk_weights: function to tally votes in the supplied list ordered by risk
# votes_table: dictionary of existing votes
# votes: new votes to tally and add to votes_table
# weights: dictionary of weights to apply
# returns: updated votes_table
def vote_with_risk_weights(votes_table, votes, weights):
    i = len(votes_table)
    for vote in votes:
        if vote in votes_table:
            votes_table[vote] += i
        else:
            votes_table[vote] = i
        i -= 1
    return votes_table

# helper function to return a list of first elements in a dictionary
def extract_1(lst): 
    return [item[0] for item in lst] 

# make_decision: logic to pick the desired move of the snake
# preferred_moves: array of the preffered directions to move to get to target
# last_ditch_possible_moves: array of possible moves before they have been filtered to use as last resort
# risk_moves: array of riskiest moves sorted least to most
# ff_moves: array of flood fill moves sorted best to worst
# my_size: length of my snake
# returns: final direction to move
def make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, risk_moves, ff_moves, ff_fits, data):
    # final decision
    threshold = 0.197
    #threshold = 0.179
    direction = None
    
    my_head = data["you"]["body"][0]
    my_size = len(data["you"]["body"])
    my_tail = data["you"]["body"][my_size-1]
    directions_of_my_tail = get_directions_of_my_tail(my_head, my_tail, possible_moves)
    away_from_heads = which_directions_are_away_from_snake_heads(my_head, data, possible_moves)
    
    votes_table = {}
    votes_table = vote(votes_table, away_from_heads, 1.5)
    votes_table = vote(votes_table, directions_of_my_tail, 1.1)
    votes_table = vote_with_weights(votes_table, extract_1(ff_fits), ff_fits)
    votes_table = vote_with_risk_weights(votes_table, extract_1(risk_moves), risk_moves)
    if (len(votes_table) > 0):
        print("DEBUG: Tally of Votes: {}".format(votes_table))

    # preferred direction
    preferred_direction = None
    print("DEBUG: Directions away bigger snake heads = {}".format(away_from_heads))
    preferred_direction = get_first_common_element(preferred_moves, away_from_heads)
    if (preferred_direction == None):
        for pm in preferred_moves:
             if (abs(get_risk(preferred_direction, risk_moves)) <= threshold):
                    preferred_direction = pm
                    print("DEBUG: risk threshold is low enough to go with: {}".format(preferred_direction))
                    break
    
    if (preferred_direction != None):
        lof = get_ff_size(preferred_direction, ff_moves, data)
        if (lof == None):
            direction = None
            print("DEBUG: Cancelling choice - not an FF option = {}".format(preferred_direction))
        elif (lof >= (my_size - 1.0)):
            direction = preferred_direction
            print("DEBUG: Choosing Preferred direction = {}".format(direction))
        else:
            direction = None
            print("DEBUG: Preferred direction too small for snake !! = {}".format(direction))
            print(" DEBUG: FF Size = {}".format(lof))
            print(" DEBUG: My Size = {}".format(my_size))
    
    if (direction == None):
        # Iterate over the sorted sequence
        newlist = sorted(votes_table.items(), key=lambda x: x[1], reverse=True)
        for elem in newlist:
            print("DEBUG: Next highest vote = {}".format(elem[0]))
            lof = get_ff_size(elem[0], ff_moves, data)
            if (lof == None):
                if (direction == None):
                    # only update direction if wasn't set on previous iteration
                    print("DEBUG: No flood fill size - not a good sign")
                    if (elem[0] in possible_moves):
                        direction = elem[0]
                        print("DEBUG: Move is possible - taking a chance, but still looking")
            elif (lof >= (my_size - 1.0)):
                direction = elem[0]
                print("DEBUG: Next vote fits: {}".format(direction))
                break

    # we are running out of options - get the first "possible" move from the unadulterated list
    if (direction == None):
        for lr in risk_moves:
            direction = lr[0]
            print("DEBUG: Almost last resort - pick lowest risk: {}".format(direction))
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

    # get details on the shortest snake on the board
    shortest_snake = get_shortest_snake(data)
    shortest_length = len(shortest_snake)
    # check if we have a longer snake on the board
    longer_snake = is_there_a_longer_snake(data)

    # get list of food and determine closest food to my head
    food_sorted_by_proximity = get_food_list(my_head, data)
    target = food_sorted_by_proximity[0]
    
    # specify health threshold to go get food
    health_threshold = 28
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

    avoid_heads = get_snake_heads_to_avoid(my_head, data)
    for ah in avoid_heads:
        if (ah in possible_moves):
            possible_moves.remove(ah)
    print("DEBUG: Possible Moves={}".format(possible_moves))

    # build array of preferred moves to get to target food or enemy
    preferred_moves = get_preferred_moves(my_head, target, possible_moves)

    # build array of directions sorted by risk level
    risk_moves = []
    tup = check_risky_business("up", snake_coords, possible_moves, data, width, height)    
    if (tup):
        risk_moves.append(tup)
    tup = check_risky_business("down", snake_coords, possible_moves, data, width, height)
    if (tup):
        risk_moves.append(tup)
    tup = check_risky_business("left", snake_coords, possible_moves, data, width, height)    
    if (tup):
        risk_moves.append(tup)
    tup = check_risky_business("right", snake_coords, possible_moves, data, width, height)
    if (tup):
        risk_moves.append(tup)
    if len(risk_moves) > 0:
        risk_moves.sort(key=lambda x: x[1])
    print("DEBUG: Risky Moves: {}".format(risk_moves))

    # build array of sizes of empty squares in flood fill of all four directions
    ff_moves = []
    ff_fits = []
    if ("up" in possible_moves):
        if ("up" in possible_moves):
            val = build_floodfill_move(width, height, snake_coords, data, my_head["x"], my_head["y"] - 1, my_head["y"], 0)
            if (val > 0):
                ff_moves.append(("up", val))
                ff_fits.append(("up", 1.0))
    if ("down" in possible_moves):
        if ("down" in possible_moves):
            val = build_floodfill_move(width, height, snake_coords, data, my_head["x"], my_head["y"] + 1, my_head["y"], height - 1)
            if (val > 0):
                ff_moves.append(("down", val))
                ff_fits.append(("down", 1.0))
    if ("left" in possible_moves):
        if ("left" in possible_moves):
            val = build_floodfill_move(width, height, snake_coords, data, my_head["x"] - 1, my_head["y"], my_head["x"], 0)
            if (val > 0):
                ff_moves.append(("left", val))
                ff_fits.append(("left", 1.0))
    if ("right" in possible_moves):
        if ("right" in possible_moves):
            val = build_floodfill_move(width, height, snake_coords, data, my_head["x"] + 1, my_head["y"], my_head["x"], width - 1)
            if (val > 0):
                ff_moves.append(("right", val))
                ff_fits.append(("right", 1.0))        
    ff_moves.sort(key=lambda x: x[1], reverse=True)
    print("DEBUG: FF Moves: {}".format(ff_moves))
    print("DEBUG: FF Fits: {}".format(ff_fits))

    # final decision
    #matrix = build_matrix(width, height, data, snake_coords)
    direction = make_decision(preferred_moves, possible_moves, last_ditch_possible_moves, risk_moves, ff_moves, ff_fits, data)

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