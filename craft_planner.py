import json
from heapq import heappop, heappush
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        if 'Consumes' in rule:
            for item, value in rule['Consumes'].items():
                if value > state[item]:
                    return False

        if 'Requires' in rule:
            for tool in rule['Requires']:
                if state[tool] == 0:
                    return False

        return True

    return check


def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        next_state = state.copy()   # Has to be state.copy(). Using just state
                                    
        if 'Consumes' in rule:
            for item in rule['Consumes']:
                next_state[item] = next_state[item] - rule['Consumes'][item]

        for created in rule['Produces']:
            next_state[created] = next_state[created] + rule['Produces'][created]

        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for goal in Crafting['Goal']:
            if Crafting['Goal'][goal] > state[goal]:
                return False

        return True

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)


def heuristic(state):
    # Implement your heuristic here!
    tools = ['bench', 'furnace', 'wooden_pickaxe', 'stone_pickaxe',
             'iron_pickaxe', 'wooden_axe', 'stone_axe', 'iron_axe']

    for tool in tools:
        if state[tool] > 1:
            return float("inf")

    return 0

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()

    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state
    queue = [(0, state, None)]
    times = {}
    times[state] = 0
    backpointers = {}
    backpointers[state] = None
    previous_actions = {}
    previous_actions[state] = None
    path = []

    while queue or time() - start_time < limit:
        current_time, current_state, previous_action = heappop(queue)
        if is_goal(current_state):
            path.append((current_state, previous_action))
            previous_state = backpointers[current_state]
            while previous_state != None:
                if previous_state != state:
                    path.append((previous_state, previous_actions[current_state]))
                else:
                    path.append((state, None))
                current_state = previous_state
                previous_state = backpointers[previous_state]
            return path[::-1]   # path.reverse() does not return a value.
                                # Used an iterator instead.

        state_graph = graph(current_state)
        #print(current_state)
        for next_move in state_graph:
            #print(current_state)
            #print(next_move)
            current_action = next_move[0]
            test_state = next_move[1]
            test_cost = next_move[2]
            pathcost = current_time + test_cost + heuristic(test_state)
            if test_state not in times or pathcost < times[test_state]:
                times[test_state] = pathcost
                backpointers[test_state] = current_state
                previous_actions[test_state] = current_action
                heappush(queue, (pathcost, test_state, current_action))

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    # # List of items that can be in your inventory:
    # print('All items:', Crafting['Items'])
    #
    # # List of items in your initial inventory with amounts:
    # print('Initial inventory:', Crafting['Initial'])
    #
    # # List of items needed to be in your inventory at the end of the plan:
    #print('Goal:',Crafting['Goal'])
    #
    # # Dict of crafting recipes (each is a dict):
    # print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic)
    #print(resulting_plan)

    if resulting_plan:
        # Print resulting plan
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
