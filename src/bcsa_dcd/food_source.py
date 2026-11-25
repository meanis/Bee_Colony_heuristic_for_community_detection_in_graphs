class FoodSource:
    def __init__(self, initial_solution, initial_cost):

        self.trials = 0

        self.solution = initial_solution
        self.cost = initial_cost

    def increment_trials(self):
        self.trials += 1

    def __repr__(self):

        return f'<FoodSource s:{self.solution} f:{self.cost} />'
