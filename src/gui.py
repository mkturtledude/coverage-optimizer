import sys
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox
import tkinter.simpledialog
import aggregator
import interface
import threading
import multiprocessing
import time

JSON_FILE_PATH = ""
INVENTORY_FILE_PATH = ""
COURSES_FILE_PATH = ""

ALL_INPUT_JSON = ""

COURSES = []
ITEMS = []



def stringToItemType(string):
    if string == "Drivers":
        return "D"
    elif string == "Karts":
        return "K"
    else:
        assert(string == "Gliders")
        return "G"


def updateCoursesItems():
    global COURSES
    global ITEMS
    COURSES = aggregator.collectCourses(JSON_FILE_PATH)
    ITEMS = aggregator.collectItems(JSON_FILE_PATH, COURSES, stringToItemType(itemTypeVar.get()))


def updateListboxes():
    for box in [enforcedHighEndsListbox, enforcedSupersListbox, excludedHighEndsListbox, excludedSupersListbox]:
        box.delete(0, tk.END)
    for item in ITEMS:
        if item.rarity == "High-End":
            enforcedHighEndsListbox.insert(tk.END, item.name)
            excludedHighEndsListbox.insert(tk.END, item.name)
        else:
            enforcedSupersListbox.insert(tk.END, item.name)
            excludedSupersListbox.insert(tk.END, item.name)

def updateAll(blah): # Crashes if there's no argument here
    if not JSON_FILE_PATH:
        return
    updateCoursesItems()
    updateListboxes()


def selectJson():
    filename = fd.askopenfilename(title='Select the *_alldata_multilang.json file',
                                  filetypes=(('JSON files', '*.json'),))
    if filename:
        global JSON_FILE_PATH
        JSON_FILE_PATH = filename
        updateAll(0)
        selectedJsonFileLabel.config(text=filename)

def showSelection():
    enforcedItems = [enforcedHighEndsListbox.get(i) for i in enforcedHighEndsListbox.curselection()] \
                    + [enforcedSupersListbox.get(i) for i in enforcedSupersListbox.curselection()]
    excludedItems = [excludedHighEndsListbox.get(i) for i in excludedHighEndsListbox.curselection()] \
                    + [excludedSupersListbox.get(i) for i in excludedSupersListbox.curselection()]
    outputText = "Enforced items:\n"
    for item in enforcedItems:
        outputText += "\t" + item + "\n"
    outputText += "\nExcluded items:\n"
    for item in excludedItems:
        outputText += "\t" + item + "\n"
    tk.messagebox.showinfo("Enforced and excluded items", outputText)


def saveSelection():
    enforcedItems = [enforcedHighEndsListbox.get(i) for i in enforcedHighEndsListbox.curselection()] \
                                  + [enforcedSupersListbox.get(i) for i in enforcedSupersListbox.curselection()]
    excludedItems = [excludedHighEndsListbox.get(i) for i in excludedHighEndsListbox.curselection()] \
                                    + [excludedSupersListbox.get(i) for i in excludedSupersListbox.curselection()]
    fileName = itemTypeVar.get() + ".txt"
    f = open(fileName, "w")
    f.write("#Enforced\n")
    for item in enforcedItems:
        f.write(item)
        f.write("\n")
    f.write("#Excluded\n")
    for item in excludedItems:
        f.write(item)
        f.write("\n")
    f.close()
    tk.messagebox.showinfo("Selection saved", "Saved selection of enforced and excluded items to " + fileName + ".")

def loadSelection():
    fileName = itemTypeVar.get() + ".txt"
    numEnforced = 0
    numExcluded = 0
    try:
        file = open(fileName, "r")
        lines = file.read().splitlines()
        readingEnforced = True
        if lines[0] != "#Enforced":
            tk.messagebox.showerror("Error", "File with selection has incorrect formatting, please generate it again")
            return
        for line in lines:
            if line == "#Enforced":
                continue
            elif line == "#Excluded":
                readingEnforced = False
            else:
                boxes = [enforcedHighEndsListbox, enforcedSupersListbox]
                if not readingEnforced:
                    boxes = [excludedHighEndsListbox, excludedSupersListbox]
                success = False
                for box in boxes:
                    for index, value in enumerate(box.get(0, tk.END)):
                        if value == line:
                            box.selection_set(index)
                            box.event_generate("<<ListboxSelect>>")
                            success = True
                if not success:
                    tk.messagebox.showwarning("Warning", "Couldn't identify object " + line
                                              + ". Please re-generate the file with the selection.")
                    return
                if readingEnforced:
                    numEnforced += 1
                else:
                    numExcluded +=1
    except:
        tk.messagebox.showwarning("Warning", "Couldn't find or read file " + fileName + ".")
        return
    tk.messagebox.showinfo("Loading successful",
                           "Added {} items to the enforced list and {} to the excluded list, on top of what was "
                           "already selected.".format(numEnforced, numExcluded))

def clearSelection():
    boxes = [enforcedHighEndsListbox, enforcedSupersListbox, excludedHighEndsListbox, excludedSupersListbox]
    for box in boxes:
        box.selection_clear(0, tk.END)


def selectInventory():
    filename = fd.askopenfilename(title='Select the inventory file', filetypes=(('CSV files', '*.csv'),))
    if filename:
        global INVENTORY_FILE_PATH
        INVENTORY_FILE_PATH = filename
        selectedInventoryFileLabel.config(text=filename)


def selectCourses():
    filename = fd.askopenfilename(title='Select the courses file', filetypes=(('CSV files', '*.csv'),))
    if filename:
        global COURSES_FILE_PATH
        COURSES_FILE_PATH = filename
        selectedCoursesFileLabel.config(text=filename)


def printAbout():
    aboutTitle = "About"
    title = "** Coverage Optimizer **\n\n"
    developer = "Developed by aturtledude\n\n"
    version = "Version: 0.9\n\n"
    text = "To support the Coverage Optimizer, please subscribe to Kevin Garrett's YouTube channel:\n" \
           "https://www.youtube.com/c/kevingarrettgaming\n" \
           "The Discord server of the channel (link in each video) is the official home of the Coverage Optimizer.\n" \
           "There, you can find tutorials, examples, technical support and advice for using this tool. "
    aboutText = title + developer + version + text
    CustomDialog(inputFrame, title=aboutTitle, text=aboutText)

def readAllowedCourses():
    result = []
    if not COURSES_FILE_PATH:
        return result
    with open(COURSES_FILE_PATH) as f:
        return f.read().splitlines()


def generateReport():
    originalMaxItems = maxItemsEntry.get()
    originalMaxNewItems = maxNewItemsEntry.get()
    enforcedItems = [enforcedHighEndsListbox.get(i) for i in enforcedHighEndsListbox.curselection()] + \
                    [enforcedSupersListbox.get(i) for i in enforcedSupersListbox.curselection()]
    REPORT_MAX_ADDITIONAL_ITEMS = 3
    maxItemsEntry.delete(0, tk.END)
    maxItemsEntry.insert(0, str(len(enforcedItems) + REPORT_MAX_ADDITIONAL_ITEMS))
    outputBox.insert(tk.END, "\n\n\n\n**** Analysis for {} *****\n".format(itemTypeVar.get()))
    # print("\n\n\n\n**** Analysis for {} *****\n".format(itemTypeVar.get()))
    outputBox.insert(tk.END, "There are {} enforced items:\n".format(len(enforcedItems)))
    # print("There are {} enforced items:".format(len(enforcedItems)))
    for i in enforcedItems:
        outputBox.insert(tk.END, "\t{}\n".format(i))
        # print("\t{}".format(i))
    outputBox.insert(tk.END, "\n")
    # print("")
    for i in range(REPORT_MAX_ADDITIONAL_ITEMS + 1):
        maxNewItemsEntry.delete(0, tk.END)
        maxNewItemsEntry.insert(0, str(i))
        outputBox.insert(tk.END, "Optimal coverage with {} additional items, {} of which are allowed to be unowned:\n"
              .format(REPORT_MAX_ADDITIONAL_ITEMS, maxNewItemsEntry.get()))
        # print("Optimal coverage with {} additional items, {} of which are allowed to be unowned:"
        #                  .format(REPORT_MAX_ADDITIONAL_ITEMS, maxNewItemsEntry.get()))
        generateJson()
        optimizationProcess.join()

    maxItemsEntry.delete(0, tk.END)
    maxItemsEntry.insert(0, originalMaxItems)
    maxNewItemsEntry.delete(0, tk.END)
    maxNewItemsEntry.insert(0, originalMaxNewItems)

def clearResults():
    outputBox.delete("1.0", tk.END)
    outputBox.update()

def getShowCoursesSetting():
    value = shownCoursesVar.get()
    if value == 1:
        return "noCourses"
    elif value == 2:
        return "simpleCourses"
    else:
        assert(value==3)
        return "extendedCourses"

def updateOutputBox(otherThread, q, outputBox):
    while otherThread.is_alive():
        try:
            newOutput = q.get(timeout=0.1)
            outputBox.insert(tk.END, newOutput)
            outputBox.yview_moveto(1)
            outputBox.update()
        except:
            pass
        time.sleep(0.01)
    while not q.empty():
        newOutput = q.get(timeout=0.1)
        outputBox.insert(tk.END, newOutput)
    outputBox.yview_moveto(1)
    outputBox.update()

def generateJson():
    outputBox.mark_set(tk.INSERT, tk.END) # Place cursor at the end to print output in the right place
    if not JSON_FILE_PATH:
        messagebox.showerror("Error", "You need to select a JSON file with the coverage data.")
        return
    userSettings = dict()
    userSettings["itemType"] = stringToItemType(itemTypeVar.get())
    userSettings["maxItemsAllowed"] = maxItemsEntry.get()
    userSettings["maxNewItems"] = maxNewItemsEntry.get()
    userSettings["simulatedLevel"] = simulatedLevelVar.get()
    userSettings["considerCities"] = bool(considerCitiesVar.get())
    userSettings["considerNinjaHideawayMerryMountain"] = bool(considerNinjaMerryVar.get())
    userSettings["showCoveredCourses"] = getShowCoursesSetting()
    userSettings["forcedItems"] = [enforcedHighEndsListbox.get(i) for i in enforcedHighEndsListbox.curselection()] \
                                  + [enforcedSupersListbox.get(i) for i in enforcedSupersListbox.curselection()]
    userSettings["excludedItems"] = [excludedHighEndsListbox.get(i) for i in excludedHighEndsListbox.curselection()] \
                                    + [excludedSupersListbox.get(i) for i in excludedSupersListbox.curselection()]
    userSettings["consideredCourses"] = readAllowedCourses()
    # global ALL_INPUT_JSON
    # if exportInputVar.get():
    #     ALL_INPUT_JSON = "all_input.json"
    json = aggregator.createJson(JSON_FILE_PATH, INVENTORY_FILE_PATH, userSettings)
    q = multiprocessing.Queue()
    global optimizationProcess
    if optimizationProcess.is_alive():
        messagebox.showerror("Error", "There is an ongoing calculation, wait for it to finish or press Stop in order to start a new one.")
        return
    optimizationProcess = multiprocessing.Process(target=interface.optimize, args=(json, q))
    optimizationProcess.start()
    updateProcess = threading.Thread(target=updateOutputBox, args=(optimizationProcess, q, outputBox))
    updateProcess.start()
    # interface.optimize(json, outputBox)

def redirector(inputStr):
    outputBox.insert(tk.INSERT, inputStr)
    outputBox.update()


def stopCalculation():
    global optimizationProcess
    if optimizationProcess.is_alive():
        optimizationProcess.terminate()
        outputBox.insert(tk.END, "\n\nCalculation terminated by the user!\n\n")
    # else:
    #     print("Process is dead, can't terminate it")


class CustomDialog(tk.simpledialog.Dialog):

    def __init__(self, parent, title=None, text=None):
        self.data = text
        tk.simpledialog.Dialog.__init__(self, parent, title=title)

    def body(self, parent):

        self.text = tk.Text(self, width=110, height=10)
        self.text.pack(fill="both", expand=True)
        self.text.insert("1.0", self.data)
        return self.text

    def ok_pressed(self):
        # print("ok")
        self.destroy()

    def buttonbox(self):
        self.ok_button = tk.Button(self, text='OK', width=5, command=self.ok_pressed)
        self.ok_button.pack()
        self.bind("<Return>", lambda event: self.ok_pressed())

def showDialog():
    fromonk_text = "this is an example"
    CustomDialog(inputFrame, title="Example", text=fromonk_text)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    window = tk.Tk()
    window.title("Coverage Optimizer")
    window.geometry("930x625")

    mainFrame = tk.Frame(master=window)
    mainFrame.pack(fill=tk.BOTH,expand=1)

    my_canvas = tk.Canvas(mainFrame) # Necessary for main scrollbar, see https://stackoverflow.com/questions/19860047/python-tkinter-scrollbar-for-entire-window
    my_canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

    y_scrollbar = tk.Scrollbar(mainFrame,orient=tk.VERTICAL,command=my_canvas.yview)
    y_scrollbar.pack(side=tk.RIGHT,fill=tk.Y)

    my_canvas.configure(yscrollcommand=y_scrollbar.set)
    my_canvas.bind("<Configure>",lambda e: my_canvas.config(scrollregion= my_canvas.bbox(tk.ALL)))

    second_frame = tk.Frame(my_canvas)
    canvasFrame = my_canvas.create_window((0,0),window= second_frame, anchor="nw")

    inputFrame = tk.Frame(master=second_frame)

    upperFrame = tk.Frame(master=inputFrame)

    mandatoryFrame = tk.LabelFrame(master=upperFrame, relief=tk.GROOVE, borderwidth=5, text="Mandatory settings")

    # open button
    openJsonButton = tk.Button(mandatoryFrame, text='Select JSON file', command=selectJson)
    openJsonButton.pack(expand=True)
    selectedJsonFileLabel = tk.Label(mandatoryFrame, text='No file selected')
    selectedJsonFileLabel.pack()

    mainSettingsFrame = tk.Frame(master=mandatoryFrame)
    mainSettingsFrame.columnconfigure(3, weight=1)
    mainSettingsFrame.rowconfigure(0, weight=1)

    itemTypeFrame = tk.Frame(master=mainSettingsFrame)
    itemTypeLabel = tk.Label(master=itemTypeFrame, text="Item type")
    itemTypeLabel.pack(pady=(13,0))
    itemTypeVar = tk.StringVar(itemTypeFrame)
    itemTypeVar.set("Drivers")
    itemTypeMenu = tk.OptionMenu(itemTypeFrame, itemTypeVar, "Drivers", "Karts", "Gliders", command=updateAll)
    itemTypeMenu.pack()
    itemTypeFrame.grid(column=0, row=0)

    maxItemsFrame = tk.Frame(master=mainSettingsFrame)
    maxItemsLabel = tk.Label(master=maxItemsFrame, text="Combination size")
    maxItemsEntry = tk.Entry(master=maxItemsFrame, width=3)
    maxItemsEntry.insert(tk.END, '3')
    maxItemsLabel.pack()
    maxItemsEntry.pack()
    maxItemsFrame.grid(column=1, row=0)

    simulatedLevelFrame = tk.Frame(master=mainSettingsFrame)
    simulatedLevelLabel = tk.Label(master=simulatedLevelFrame, text="Simulated level")
    simulatedLevelLabel.pack(pady=(13,0))
    simulatedLevelVar = tk.StringVar(simulatedLevelFrame)
    simulatedLevelVar.set("6")
    simulatedLevelMenu = tk.OptionMenu(simulatedLevelFrame, simulatedLevelVar, "1", "3", "6", "8")
    simulatedLevelMenu.pack()
    simulatedLevelFrame.grid(column=2, row=0)

    mainSettingsFrame.pack()

    nitroTracksFrame = tk.Frame(master=mandatoryFrame, relief=tk.GROOVE, borderwidth=1)
    nitroTracksFrame.columnconfigure(2, weight=1)
    nitroTracksFrame.rowconfigure(0, weight=1)

    considerCitiesVar = tk.IntVar()
    considerCitiesCheckbox = tk.Checkbutton(nitroTracksFrame, text="Include cities", variable=considerCitiesVar,
                                            onvalue=1, offvalue=0)
    considerCitiesCheckbox.grid(column=0, row=0)


    considerNinjaMerryVar = tk.IntVar()
    considerNinjaMerryCheckbox = tk.Checkbutton(nitroTracksFrame, text="Include Ninja Hideaway + Merry Mountain",
                                           variable=considerNinjaMerryVar, onvalue=1, offvalue=0)
    considerNinjaMerryCheckbox.grid(column=1, row=0)
    nitroTracksFrame.pack()

    showCoursesFrame = tk.LabelFrame(master=mandatoryFrame, relief=tk.GROOVE, borderwidth=1, text="Courses Display Settings")
    shownCoursesVar = tk.IntVar()
    noCoursesButton = tk.Radiobutton(showCoursesFrame, text="No Courses", variable=shownCoursesVar, value=1)
    justCoursesButton = tk.Radiobutton(showCoursesFrame, text="Just Courses", variable=shownCoursesVar, value=2)
    coursesAndItemsButton = tk.Radiobutton(showCoursesFrame, text="Courses + Items", variable=shownCoursesVar, value=3)
    noCoursesButton.pack(anchor=tk.W)
    justCoursesButton.pack(anchor=tk.W)
    coursesAndItemsButton.pack(anchor=tk.W)
    noCoursesButton.invoke()
    showCoursesFrame.pack(pady=(10,0))

    mandatoryFrame.pack(side=tk.LEFT)


    buttonFrame = tk.Frame(master=upperFrame)
    optimizeButton = tk.Button(
        master=buttonFrame,
        text="Optimize",
        width=10,
        height=5,
        bg="green3",
        fg="black",
        command=generateJson
    )
    optimizeButton.pack()

    stopButton = tk.Button(
        master=buttonFrame,
        text="Stop",
        width=10,
        height=5,
        bg="red2",
        fg="black",
        command=stopCalculation
    )
    stopButton.pack(pady=(10,0))


    reportButton = tk.Button(
        master=buttonFrame,
        text="Generate report",
        width=12,
        height=3,
        bg="green4",
        fg="black",
        command=generateReport
    )
    # reportButton.pack(pady=(10,0))

    clearButton = tk.Button(
        master=buttonFrame,
        text="Clear results",
        bg="IndianRed3",
        command=clearResults
    )
    clearButton.pack(pady=(10,0))

    aboutButton = tk.Button(
        master=buttonFrame,
        text="About",
        # command=showDialog
        command=printAbout
    )
    aboutButton.pack(pady=(10,0))

    buttonFrame.pack(side=tk.RIGHT)
    upperFrame.pack()

    optionalFrame = tk.LabelFrame(master=inputFrame, relief=tk.GROOVE, borderwidth=5, text="Optional settings")

    optionalLeftFrame = tk.Frame(optionalFrame)

    enforcedHighEndsFrame = tk.Frame(optionalLeftFrame)
    enforcedHighEndsLabel = tk.Label(master=enforcedHighEndsFrame, text="Enforced HE items")
    enforcedHighEndsLabel.pack()
    enforcedHighEndsScrollbar = tk.Scrollbar(enforcedHighEndsFrame, orient=tk.VERTICAL)
    # exportselection=0 because otherwise selecting in a list unselects the other one
    enforcedHighEndsListbox = tk.Listbox(enforcedHighEndsFrame, height=11, selectmode='multiple', exportselection=0,
                                      yscrollcommand=enforcedHighEndsScrollbar.set)
    enforcedHighEndsScrollbar.config(command=enforcedHighEndsListbox.yview)
    enforcedHighEndsScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    enforcedHighEndsFrame.pack(side=tk.TOP)
    enforcedHighEndsListbox.pack()

    enforcedSupersFrame = tk.Frame(optionalLeftFrame)
    enforcedSupersLabel = tk.Label(master=enforcedSupersFrame, text="Enforced N/S items")
    enforcedSupersLabel.pack()
    enforcedSupersScrollbar = tk.Scrollbar(enforcedSupersFrame, orient=tk.VERTICAL)
    enforcedSupersListbox = tk.Listbox(enforcedSupersFrame, height=5, selectmode='multiple', exportselection=0,
                                         yscrollcommand=enforcedSupersScrollbar.set)
    enforcedSupersScrollbar.config(command=enforcedSupersListbox.yview)
    enforcedSupersScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    enforcedSupersFrame.pack(side=tk.BOTTOM)
    enforcedSupersListbox.pack()

    optionalLeftFrame.pack(side=tk.LEFT)


    optionalRightFrame = tk.Frame(optionalFrame)

    excludedHighEndsFrame = tk.Frame(optionalRightFrame)
    excludedHighEndsLabel = tk.Label(master=excludedHighEndsFrame, text="Excluded HE items")
    excludedHighEndsLabel.pack()
    excludedHighEndsScrollbar = tk.Scrollbar(excludedHighEndsFrame, orient=tk.VERTICAL)
    excludedHighEndsListbox = tk.Listbox(excludedHighEndsFrame, height=11, selectmode='multiple', exportselection=0,
                                      yscrollcommand=excludedHighEndsScrollbar.set)
    excludedHighEndsScrollbar.config(command=excludedHighEndsListbox.yview)
    excludedHighEndsScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    excludedHighEndsFrame.pack(side=tk.TOP)
    excludedHighEndsListbox.pack()

    excludedSupersFrame = tk.Frame(optionalRightFrame)
    excludedSupersLabel = tk.Label(master=excludedSupersFrame, text="Excluded N/S items")
    excludedSupersLabel.pack()
    excludedSupersScrollbar = tk.Scrollbar(excludedSupersFrame, orient=tk.VERTICAL)
    excludedSupersListbox = tk.Listbox(excludedSupersFrame, height=5, selectmode='multiple', exportselection=0,
                                         yscrollcommand=excludedSupersScrollbar.set)
    excludedSupersScrollbar.config(command=excludedSupersListbox.yview)
    excludedSupersScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    excludedSupersFrame.pack(side=tk.BOTTOM)
    excludedSupersListbox.pack()


    optionalRightFrame.pack(side=tk.RIGHT)
    optionalMiddleFrame = tk.Frame(optionalFrame)
    optionalMiddleFrame.columnconfigure(0, weight=1)
    optionalMiddleFrame.rowconfigure(4, weight=1)


    inventoryFrame = tk.Frame(optionalMiddleFrame)
    openInventoryButton = tk.Button(inventoryFrame, text='Select inventory file', command=selectInventory)
    openInventoryButton.pack(expand=True)
    selectedInventoryFileLabel = tk.Label(inventoryFrame, text='No file selected')
    selectedInventoryFileLabel.pack()
    # inventoryFrame.pack(side=tk.TOP)
    inventoryFrame.grid(column=0, row=0)

    maxNewItemsFrame = tk.Frame(optionalMiddleFrame)

    maxNewItemsLabel = tk.Label(master=maxNewItemsFrame, text="Maximum unowned items allowed")
    maxNewItemsEntry = tk.Entry(master=maxNewItemsFrame)
    maxNewItemsEntry.insert(tk.END, '999')
    maxNewItemsLabel.pack()
    maxNewItemsEntry.pack()

    # maxNewItemsFrame.pack()
    maxNewItemsFrame.grid(column=0, row=1, pady=(20,0))

    selectedCoursesFrame = tk.Frame(optionalMiddleFrame)
    openCoursesButton = tk.Button(selectedCoursesFrame, text='Select courses file', command=selectCourses)
    selectedCoursesFileLabel = tk.Label(selectedCoursesFrame, text='No file selected')
    openCoursesButton.pack(expand=True)
    selectedCoursesFileLabel.pack()
    selectedCoursesFrame.grid(column=0, row=2, pady=(20,0))

    saveLoadSelectionFrame = tk.Frame(optionalMiddleFrame)
    showSelectionButton = tk.Button(saveLoadSelectionFrame, text="Show selection", command=showSelection)
    showSelectionButton.pack()
    saveSelectionButton = tk.Button(saveLoadSelectionFrame, text="Save selection", command=saveSelection)
    saveSelectionButton.pack()
    loadSelectionButton = tk.Button(saveLoadSelectionFrame, text="Load selection", command=loadSelection)
    loadSelectionButton.pack()
    clearSelectionButton = tk.Button(saveLoadSelectionFrame, text="Clear selection", command=clearSelection)
    clearSelectionButton.pack()
    saveLoadSelectionFrame.grid(column=0, row=3, pady=(20,0))



    optionalMiddleFrame.pack()

    optionalFrame.pack()

    window.update_idletasks()

    lowerFrame = tk.Frame(master=inputFrame, width=optionalFrame.winfo_width())
    lowerFrame.columnconfigure(2, weight=1)
    lowerFrame.rowconfigure(0, weight=1)


    # debugFrame = tk.LabelFrame(master=lowerFrame, relief=tk.GROOVE, borderwidth=1, text="In case of problems")
    # exportInputVar = tk.IntVar()
    # exportInputCheckbox = tk.Checkbutton(debugFrame, text="Export debug file", variable=exportInputVar,
    #                                      onvalue=1, offvalue=0)
    # exportInputCheckbox.pack()
    # debugFrame.grid(column=0, row=0)


    lowerFrame.pack()
    inputFrame.pack(side=tk.LEFT)

    window.update()

    outputFrame = tk.LabelFrame(master=second_frame, height=inputFrame.winfo_height(), relief=tk.GROOVE, borderwidth=5, text="Results")
    outputScrollbar = tk.Scrollbar(outputFrame, orient=tk.VERTICAL)
    outputBox = tk.Text(master=outputFrame, width=50, yscrollcommand=outputScrollbar.set, wrap=tk.WORD)
    outputScrollbar.config(command=outputBox.yview)
    outputScrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    outputFrame.pack(side=tk.RIGHT, fill=tk.Y, expand=True)
    outputBox.pack(fill=tk.BOTH, expand=True)

    # sys.stdout.write = redirector #whenever sys.stdout.write is called, redirector is called.

    optimizationProcess = multiprocessing.Process()

    window.update()
    window.mainloop()
