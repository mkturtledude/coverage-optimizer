# import pandas as pd # This will be needed by whoever imports this file
import pyscipopt as scip
from enum import Enum

class OptimizationMode(Enum):
    MIN_ITEMS = 1 # Classical minimization problem
    MAX_COVERAGE = 2 # Classical maximization
    MAX_VALUE = 3 # Maximizes total value subject to a fixed number of items allowed in the solution

# This is the main function
def optimize(matrix, values, optMode, covPercentage, maxTotalItemsAllowed, maxNewItemsAllowed, ownedItems, forcedItems, forbiddenItems, excludedSolutions):
    """
    Calculates the optimal solution for the given input.
    Parameters
    ----------
    matrix: pandas.DataFrame
        The columns represent items, the rows represent tracks. Is filled with 0s and 1s.
        The column indices are used as item IDs everywhere.
    values: list
        List of values used to rank the items in case MAX_VALUE is selected.
    optMode: OptimizationMode
        See description of OptimizationMode above.
    covPercentage: float
        A number between 0 and 1 representing the target coverage percentage. Relevant in case of MIN_ITEMS or MAX_VALUE.
    maxTotalItemsAllowed: int
        The maximum number of items allowed in the combination. Relevant in case of MAX_COVERAGE or MAX_VALUE.
    maxNewItemsAllowed: int
        The maximum number of items outside the user's inventory that are allowed in the combination.
    ownedItems: set
        A set of item IDs representing the user's inventory.
    forcedItems: set
        A set of item IDs that need to be part of the combination.
    forbiddenItems: set
        A set of item IDs that are not allowed to be part of the combination.
    excludedSolutions: list
        A list of solutions (each of them a list of zeroes and ones) that are already known.
        The algorithm will either find a solution different to all these, or return without solution.

    Returns
    -------
    list
        Solution as a list of zeros and ones, showing which items were selected.
        If the list is empty, that means no solution was found.
    float
        Objective value of the best solution found
    """
    model, x = createBasicModel(matrix, maxNewItemsAllowed, ownedItems, forcedItems, forbiddenItems, excludedSolutions)

    if optMode == OptimizationMode.MIN_ITEMS:
        coverFractionOfTracks(matrix, model, x, covPercentage)
        minimizeItems(matrix, model, x)
    elif optMode == OptimizationMode.MAX_VALUE:
        coverFractionOfTracks(matrix, model, x, covPercentage)
        setNumberOfItems(matrix, model, x, maxTotalItemsAllowed)
        maximizeValue(matrix, values, model, x)
    elif optMode == OptimizationMode.MAX_COVERAGE:
        setNumberOfItems(matrix, model, x, maxTotalItemsAllowed)
        maximizeTracks(matrix, model, x)


    # Used for debugging
    # model.writeProblem("mkt.lp")

    model.optimize()

    objVal = -1

    if model.getSols():
        objVal = model.getObjVal()

    return createSolution(matrix, model, x), objVal

def createBasicModel(matrix, maxNewItemsAllowed, ownedItems, forcedItems, forbiddenItems, excludedSolutions):
    model = scip.Model()
    model.hideOutput()
    x = defineItemVariables(matrix, model)
    limitNewItems(matrix, model, x, ownedItems, maxNewItemsAllowed)
    fixVariables(forcedItems, forbiddenItems, model, x)
    excludeSolutions(model, x, excludedSolutions)

    return model, x

def verifySolution(solution, matrix):
    for i in range(matrix.shape[0]):
        for j in range(len(solution)):
            if solution[j] == 1 and matrix.iloc[i,j] == 1:
                print("Track {0} is covered by driver {1}".format(i,j))
                break

# Store the solution in a list.
def createSolution(matrix, model, x):
    solution = []
    if len(model.getSols()) == 0:
        # print("\n\nNo solution found :(")
        return solution
    # print("The optimal value is {}".format(model.getObjVal()))
    for j in range(len(matrix.columns)):
        if (model.getVal(x[j]) > 0.99): # They should be 0 or 1, but they are saved as floats
            solution.append(1)
        else:
            solution.append(0)
    # verifySolution(solution, matrix)
    return solution

def defineItemVariables(df, model):
    # Define variables (one for each driver)
    x = {}
    for j in range(len(df.columns)):
        x[j] = model.addVar(vtype="B", name="x%s"%j)
    return x

def fixVariables(mandatory, forbidden, model, x):
    """
    Fixes all mandatory variables to 1 and all forbidden to 0
    """
    for j in mandatory:
        model.addCons(x[j] == 1, "Force%s"%j)
    for j in forbidden:
        model.addCons(x[j] == 0, "Forbid%s"%j)


def minimizeItems(df, model, x):
    # Define objective function as minimizing the sum of all variables
    model.setObjective(scip.quicksum(x[j] for j in range(len(df.columns))), "minimize")

def maximizeValue(df, values, model, x):
    model.setObjective(scip.quicksum(x[j]*values[j] for j in range(len(df.columns))), "maximize")

def maximizeTracks(df, model, x):
    y = defineTrackVariables(df, model, x)
    model.setObjective(scip.quicksum(y[i] for i in range(df.shape[0])), "maximize")

def defineTrackVariables(df, model, x):
    y = {} # y[i] is 1 if track i is covered
    for i in range(df.shape[0]):
        y[i] = model.addVar(vtype="B", name="y%s"%i)
        model.addCons(scip.quicksum(x[j]*df.iloc[i,j] for j in range(len(df.columns))) >= y[i], "CoverTrack%s"%i)
    return y

# fraction in [0,1]: 1 means cover all tracks
def coverFractionOfTracks(df, model, x, percentage):
    y = defineTrackVariables(df, model, x)
    model.addCons(scip.quicksum(y[i] for i in range(df.shape[0])) >= percentage * df.shape[0], "CoverTracks")

def setNumberOfItems(df, model, x, n):
    model.addCons(scip.quicksum(x[j] for j in range(len(df.columns))) == n, "FixedNumberItems")

def limitNewItems(df, model, x, ownedItems, newItemsAllowed):
    coefficients = [1]*len(df.columns)
    for j in ownedItems:
        coefficients[j] = 0
    model.addCons(scip.quicksum(coefficients[j]*x[j] for j in range(len(df.columns))) <= newItemsAllowed, "LimitNewItems")

def excludeSolutions(model, x, excludedSolutions):
    for i in range(len(excludedSolutions)):
        solution = excludedSolutions[i]
        model.addCons(scip.quicksum(solution[j]*x[j] for j in range(len(solution))) <= scip.quicksum(solution[j] for j in range(len(solution))) - 1, "ExcludeSolution%s"%i)
