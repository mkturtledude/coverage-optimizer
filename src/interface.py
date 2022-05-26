# Acts as messenger between the GUI and the optimizer

import base
import optimizer

import json
import pandas as pd
import tkinter as tk

class Input:
    def __init__(self, courses, items):
        self.courses = courses # List of course names
        self.items = items # List of items
        self.courseNameToIndexDict = {}
        for i in range(len(courses)):
            self.courseNameToIndexDict[courses[i]] = i
        self.itemNameToIndexDict = {}
        for i in range(len(items)):
            self.itemNameToIndexDict[items[i].name] = i

    def courseNameToIndex(self, name):
        return self.courseNameToIndexDict[name]

    def courseIndexToName(self, index):
        return self.courses[index]

    def itemNameToIndex(self, name):
        return self.itemNameToIndexDict[name]

    def itemIndexToName(self, index):
        return self.items[index].name

    def courseNamesToIndices(self, names):
        result = []
        for name in names:
            result.append(self.courseNameToIndex(name))
        return result


# Selects all courses that pass the filters
# allCourses is the courses list as taken from the new JSON file
def collectCourses(allCourses, considerCities, considerNinjaAndMerry, consideredCourses):
    result = []
    for course in allCourses:
        if course["isCity"] and not considerCities:
            continue
        if (course["isNinjaHideaway"] or course["isMerryMountain"]) and not considerNinjaAndMerry:
            continue
        if not consideredCourses or course["name"] in consideredCourses:
            result.append(course["name"])
    return result

def collectCoursesFromNewJson(data):
    considerCities = data["userSettings"]["considerCities"]
    considerNinjaMerry = data["userSettings"]["considerNinjaHideawayMerryMountain"]
    consideredCourses = data["userSettings"]["consideredCourses"]

    return collectCourses(data["courses"], considerCities, considerNinjaMerry, consideredCourses)

def determineItemLevel(name, data):
    level = int(data["userSettings"]["simulatedLevel"])
    if name in data["inventory"]:
        level = max(level, int(data["inventory"][name]["level"]))
    return level

def collectItemsFromNewJson(data, allowedCourses):
    result = []
    for item in data["items"]:
        name = item["name"]
        rarity = item["rarity"]
        skill = item["skill"]
        courses = []
        level = determineItemLevel(name, data)
        for course in item["courses"]:
            if int(course["unlockLevel"]) <= level and course["name"] in allowedCourses:
                courses.append(course["name"])
        result.append(base.Item(name, rarity, skill, courses))
    return result

def createCoverageVector(courseName, items):
    result = [0]*len(items)
    for i in range(len(items)):
        if courseName in items[i].courses:
            result[i] = 1
    return result

def createMatrix(courses, items):
    itemNames = []
    for item in items:
        itemNames.append(item.name)
    matrix = pd.DataFrame(columns = itemNames)
    for i in range(len(courses)):
        matrix.loc[courses[i]] = createCoverageVector(courses[i], items)
    return matrix

def collectItemIndices(jsonList, input):
    result = set()
    for name in jsonList:
        result.add(input.itemNameToIndex(name))
    return result

def collectOwnedItemsIndices(data, input):
    return collectItemIndices(data["inventory"], input)

def collectForcedItemsIndices(data, input):
    return collectItemIndices(data["userSettings"]["forcedItems"], input)

def collectExcludedItemsIndices(data, input):
    return collectItemIndices(data["userSettings"]["excludedItems"], input)

def optimize(jsonString, queue):
    data = json.loads(jsonString)
    courses = collectCoursesFromNewJson(data)
    items = collectItemsFromNewJson(data, courses)
    input = Input(courses, items)

    #Input for optimizer
    matrix = createMatrix(input.courses, input.items)
    values = [] # Will be ignored
    optMode = optimizer.OptimizationMode(2) # Only functionality for the foreseeable future
    covPercentage = 100 # Will be ignored
    combinationSize = int(data["userSettings"]["maxItemsAllowed"])
    maxNewItems = int(data["userSettings"]["maxNewItems"])
    ownedItems = collectOwnedItemsIndices(data, input)
    forcedItems = collectForcedItemsIndices(data, input)
    excludedItems = collectExcludedItemsIndices(data, input)

    foundSolutions = []
    bestValue = -1
    for i in range(1000):

        # boxContent = outputBox.get("1.0", tk.END)
        # print("\nCalculating combination of size {}...".format(combinationSize))
        queue.put("\nCalculating combination of size {}...\n".format(combinationSize))
        # outputBox.update()
        # outputBox.yview_moveto(1)
        solution, value = optimizer.optimize(matrix, values, optMode, covPercentage, combinationSize,
                                 maxNewItems, ownedItems, forcedItems, excludedItems, foundSolutions)
        # outputBox.delete("1.0", tk.END)
        # print(boxContent, end="")
        # outputBox.yview_moveto(1)
        if not solution or (i > 0 and abs(bestValue - value) > 0.001):
            # print("\nNo more combinations found!\n\n")
            queue.put("\nNo more combinations found!\n\n\n")
            return
        else:
            bestValue = value
            foundSolutions.append(solution)
            # print("Combination with coverage {}/{}:".format(int(value), len(input.courses)))
            queue.put("Combination with coverage {}/{}:\n".format(int(value), len(input.courses)))
            itemIndexToName = dict() # Maps 1,2,3...n to the names of items in the combination
            coveredCourses = dict()
            maxCourseNameSize = 0
            for i in range(len(solution)):
                if solution[i]:
                    itemIndexToName[len(itemIndexToName)+1] = input.itemIndexToName(i)
                    for course in input.items[i].courses:
                        if not course in coveredCourses:
                            coveredCourses[course] = set()
                        coveredCourses[course].add(len(itemIndexToName))
                        maxCourseNameSize = max(maxCourseNameSize, len(course))
            for k in itemIndexToName:
                # print("\t{}: {}".format(k,itemIndexToName[k]))
                queue.put("\t{}: {}\n".format(k,itemIndexToName[k]))
            shownCoursesSettings = data["userSettings"]["showCoveredCourses"]
            if shownCoursesSettings == "simpleCourses":
                # print("Covered courses:")
                queue.put("Covered courses:\n")
                for course in coveredCourses:
                    # print(course)
                    queue.put(course + "\n")
            elif shownCoursesSettings == "extendedCourses":
                # print("Covered courses:")
                queue.put("Covered courses:\n")
                for course in coveredCourses:
                    # print(f"\t{course: <{maxCourseNameSize}}\t", end="")
                    queue.put(f"\t{course: <{maxCourseNameSize}}\t")
                    for item in coveredCourses[course]:
                        # print("{} ".format(item), end="")
                        queue.put("{} ".format(item))
                    # print("")
                    queue.put("\n")

