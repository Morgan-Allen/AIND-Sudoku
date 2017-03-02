
rows = 'ABCDEFGHI'
cols = '123456789'

def cross(a, b):
    return [s+t for s in a for t in b]

def diag(a, b):
    return [a[n]+b[n] for n in range(len(a))]

boxes          = cross(rows, cols)
row_units      = [cross(r   , cols) for r  in rows]
column_units   = [cross(rows, c   ) for c  in cols]
square_units   = [cross(rs  , cs  ) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')]
diagonal_units = [diag(rows, c) for c in (cols, '987654321')]
unitlist       = row_units + column_units + square_units + diagonal_units
units          = dict((s, [u for u in unitlist if s in u]) for s in boxes)
peers          = dict((s, set(sum(units[s],[]))-set([s])) for s in boxes)

assignments = []


def display(values):
    """
    Display the values as a 2-D grid.
    Input: The sudoku in dictionary form
    Output: None
    """
    width = 1+max(len(values[s]) for s in boxes)
    line = '+'.join(['-'*(width*3)]*3)
    for r in rows:
        print(''.join(values[r+c].center(width)+('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF': print(line)
    return


def assign_value(values, box, value):
    """
    Please use this function to update your values dictionary!
    Assigns a value to a given box. If it updates the board record it.
    """
    values[box] = value
    if len(value) == 1:
        assignments.append(values.copy())
    return values


def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    Args:
        grid(string) - A grid in string form.
    Returns:
        A grid in dictionary form
            Keys: The boxes, e.g., 'A1'
            Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """
    values = {}
    index = 0
    for c in grid:
        if c == '.':
            c = '123456789'
        row = rows[int(index / 9)]
        col = cols[int(index % 9)]
        assign_value(values, row+col, c)
        index += 1
    return values


def eliminate(values):
    """Eliminate possible values that belong to other solved peers.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
    Returns:
        the values dictionary with any solved box-values removed from peers.
    """
    solved_values = [box for box in values.keys() if len(values[box]) == 1]
    for box in solved_values:
        digit = values[box]
        for peer in peers[box]:
            assign_value(values, peer, values[peer].replace(digit,''))
    return values


def only_choice(values):
    """Assign a single value to a given box if it is the only box in
    a given unit which permits that value.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
    Returns:
        the values dictionary with any 'only choice' values assigned.
    """
    for unit in unitlist:
        for digit in '123456789':
            matches = [box for box in unit if digit in values[box]]
            if len(matches) == 1:
                assign_value(values, matches[0], str(digit))
    return values


#  TODO:  In principle, this could be extended to any arbitrary set of N
#  digits.

def naked_twins(values):
    """Eliminate values using the naked twins strategy.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
    Returns:
        the values dictionary with the naked twins eliminated from peers in
        the same unit.
    """
    
    #  First, we find all instances of naked twins (which we store as a list
    #  of all matches found, and the unit they were found in as the last
    #  element for reference.)
    twin_lists = []
    
    for unit in unitlist:
        unit_twins = []
        for box in unit:
            matches = [other for other in unit if values[other] == values[box]]
            if len(values[matches[0]]) == len(matches) and len(matches) == 2:
                unit_twins.extend(matches)
        if len(unit_twins) > 0:
            unit_twins.append(unit)
            twin_lists.append(unit_twins)
    
    #  Then scrub the digits found in a given twin from all other boxes in
    #  that unit.
    for unit_twins in twin_lists:
        unit = unit_twins[-1]
        twins = set(unit_twins[0:-1])
        to_scrub = [other for other in unit if not other in twins]
        for twin in twins:
            for box in to_scrub:
                for digit in values[twin]:
                    assign_value(values, box, values[box].replace(digit, ''))
    
    return values


#  TODO:  Add the sub-group exclusion rule (i.e, if the possible boxes for
#  a given digit within unit A have been narrowed to the point where they all
#  fit within another unit B, then that digit can be stripped from all other
#  boxes in unit B.)

def reduce_puzzle(values):
    """Uses a variety of simpler strategies to reduce or fix values within
    the puzzle grid.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
    Returns:
        the puzzle dictionary with as many box-values fixed or reduced
        as possible, or False if this proved ipossible.
    """
    stalled = False
    while not stalled:
        # Check how many boxes have a determined value before-
        solved_values_before = len([box for box in values.keys() if len(values[box]) == 1])

        # Use the Eliminate Strategy
        eliminate(values)

        # Use the Only Choice Strategy
        only_choice(values)
        
        # Use the Naked Twins Strategy
        naked_twins(values)

        # Check how many boxes have a determined value after-
        solved_values_after = len([box for box in values.keys() if len(values[box]) == 1])
        
        # Return if all values are solved:
        if solved_values_after == len(boxes):
            break
        
        # If no new values were added, stop the loop.
        stalled = solved_values_before == solved_values_after
        # Sanity check, return False if there is a box with zero available values:
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values


def search(values):
    """
    Reduce a puzzle using various short-term strategies, check for a
    solution, and failing that, find whichever box is closest to
    being solved, and recursively search for solutions across possible
    values.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
    Returns:
        The dictionary representation of the final sudoku grid. False if no
        solution is found.
    """
    # "Using depth-first search and propagation, create a search tree and solve the sudoku."
    # First, reduce the puzzle using the previous function
    
    result = reduce_puzzle(values)
    if result == False:
        return False
    
    num_solved = len([box for box in boxes if len(values[box]) == 1])
    if num_solved == len(boxes):
        return result
        
    # Choose one of the unfilled squares with the fewest possibilities
    
    box_picked = None
    min_values = 99
    for box in boxes:
        num_values = len(values[box])
        if num_values < min_values and num_values > 1:
            box_picked = box
            min_values = num_values
    if box_picked == None:
        return False
    
    # Now use recursion to solve each one of the resulting sudokus, and if one returns a value (not False), return that answer!
    
    for digit in values[box_picked]:
        digit_values = values.copy()
        digit_values[box_picked] = str(digit)
        search_result = search(digit_values)
        if search_result != False:
            return search_result
    
    return False


def solve(grid):
    """
    Find the solution to a Sudoku grid.
    Args:
        grid(string): a string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        The dictionary representation of the final sudoku grid. False if no solution exists.
    """
    values = grid_values(grid)
    return search(values)
    

if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(solve(diag_sudoku_grid))

    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')













