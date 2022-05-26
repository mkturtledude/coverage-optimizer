# Aggregates ALL necessary input data into a single JSON file

LANGUAGE = "USen"

#51.4%
import json
import csv
import unidecode
import re

# import params
from base import *

def isCity(internalName):
    cityNames = {"Amsterdam", "Berlin", "London", "LosAngeles", "NewYork", "Paris", "Singapore", "Sydney", "Tokyo", "Vancouver"}
    for forbidden in cityNames:
        if forbidden in internalName:
            return True
    return False

def isNinjaHideaway(internalName):
    return "Ninja" in internalName

def isMerryMountain(internalName):
    return "HillClimb" in internalName

# Input: The alldata_multilang.json file
# Output: A dict mapping all internal names to the relevant course data
def collectCourses(jsonFile):
    f = open(jsonFile, encoding='utf-8')
    data = json.load(f)
    result = dict()
    for i in data["courses"]:
        courseDetails = dict()
        courseDetails["name"] = data["courses"][i]["Translations"][LANGUAGE]
        courseDetails["isCity"] = isCity(i)
        courseDetails["isNinjaHideaway"] = isNinjaHideaway(i)
        courseDetails["isMerryMountain"] = isMerryMountain(i)
        result[i] = courseDetails
    return result

def itemTypeToString(itemType):
    if itemType == 'D':
        return "drivers"
    if itemType == 'K':
        return "karts"
    if itemType == 'G':
        return "gliders"

def getItemSkill(data, itemTypeLabel, jsonItem):
    skillId = jsonItem["skill"]["Id"]
    for skillLabel in data["skills"][itemTypeLabel]:
        if data["skills"][itemTypeLabel][skillLabel]["Id"] == skillId:
            return data["skills"][itemTypeLabel][skillLabel]["Translations"][LANGUAGE]
    return "Unkown skill"

def collectItemCourses(jsonItem, courseNames):
    candidateCourses = []
    for course in jsonItem["CourseMoreGoodAtDetail"]:
        candidateCourses.append({"name" : courseNames[course]["name"], "unlockLevel" : 1 })
    for course in jsonItem["CourseGoodAtDetail"]:
        promotionLevel = course["PromotionLevel"]
        if promotionLevel > 0:
            candidateCourses.append({"name" : courseNames[course["Key"]]["name"], "unlockLevel" : promotionLevel })
    return candidateCourses

def collectItems(jsonFile, courses, itemType):
    f = open(jsonFile, encoding='utf-8')
    data = json.load(f)
    itemTypeLabel = itemTypeToString(itemType)
    result = []
    for jsonItem in data[itemTypeLabel]:
        if jsonItem["Id"] == 29: # Gold Mario
            continue
        name = unidecode.unidecode(jsonItem["Translations"][LANGUAGE]) # To get rid of accents and ^
        skill = getItemSkill(data, itemTypeLabel, jsonItem)
        itemCourses = collectItemCourses(jsonItem, courses)
        result.append(Item(name, jsonItem["Rarity"], skill, itemCourses))
    return sorted(result, key=lambda x: x.name)

def createItemsDict(items):
    itemsDict = []
    for item in items:
        internalDict = dict()
        internalDict["name"] = item.name
        internalDict["rarity"] = item.rarity
        internalDict["skill"] = item.skill
        internalDict["courses"] = item.courses
        itemsDict.append(internalDict)
    return itemsDict

def createCoursesList(courses):
    coursesList = []
    for course in courses:
        coursesList.append(courses[course])
    return coursesList


def readInventory(file, allItems, itemType):
    result = {}
    if not file:
        return result
    upperToNormal = dict()
    for item in allItems:
        # We need the unidecode to get rid of accents, as in Strawberry Cr^epe
        upperToNormal[unidecode.unidecode(item.name.upper())] = item.name
    with open(file, encoding='utf-8-sig') as csvfile:
        for line in csvfile.read().splitlines():
            if not line:
                continue
            row = re.split('[,;\t]', line)
            if row and row[2] != '0':
                assert(len(row) == 4)
                if row[1] != itemType or row[2] == 0:
                    continue
                itemDict = dict()
                itemDict["name"] = upperToNormal[unidecode.unidecode(row[0].upper())]
                itemDict["level"] = row[2]
                itemDict["uncaps"] = row[3]
                result[itemDict["name"]] = itemDict
    return result

# Returns a string. If outputPath is given, dumps to file as well
def createJson(gameDump, inventoryFile, userSettings):
    courses = collectCourses(gameDump)
    items = collectItems(gameDump, courses, userSettings["itemType"])
    inventory = readInventory(inventoryFile, items, userSettings["itemType"])

    fullDict = dict()
    fullDict["courses"] = createCoursesList(courses)
    fullDict["items"] = createItemsDict(items)
    fullDict["inventory"] = inventory
    fullDict["userSettings"] = userSettings
    # if outputPath:
    #     with open(outputPath, 'w', encoding='utf-8') as outfile:
    #         json.dump(fullDict, outfile, indent=4)
    return json.dumps(fullDict, indent=4)
