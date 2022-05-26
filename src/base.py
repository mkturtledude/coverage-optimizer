
class Item:
    def __init__(self, name, rarity, skill, courses):
        self.name = name
        self.rarity = "Normal"
        if rarity == 1:
            self.rarity = "Super"
        if rarity == 2:
            self.rarity = "High-End"
        self.skill = skill
        self.courses = courses
    def print(self):
        print("Name: {}".format(self.name))
        print("Rarity: {}".format(self.rarity))
        print("Skill: {}".format(self.skill))
        print("Courses:")
        for course in self.courses:
            print("\t{}".format(course))
