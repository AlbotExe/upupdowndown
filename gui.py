import customtkinter
import platform
import io
import urllib.request
import textwrap
from customtkinter import *
from PIL import Image
from setup import *
from igdbSearch import *
from manageDb import *

##Takes selected theme as a parameter, and sets it as the GUI theme, unless the "Select Theme" header was selected
def setTheme(theme):
    if theme == "Select Theme":
        pass
    else:
        theme = theme.lower()
        customtkinter.set_appearance_mode(theme)
        customtkinter.set_default_color_theme("theme.json")

##Takes selected scaling as a parameter, removes non-numerical character ("%") and converts to float, then divides by 100 to make it a decimal instead
##of a percentage
##Then sets the scaling to the float value for windows, and two times the float value for linux
def setScaling(scale):
    if scale == "Select UI Scale":
        pass
    else:
        scale = float(scale[:-1])/100
        if platform.system() == "Linux":
            customtkinter.set_widget_scaling(2*scale)
            customtkinter.set_window_scaling(2*scale)
        elif platform.system() == "Windows":
            customtkinter.set_widget_scaling(scale)
            customtkinter.set_window_scaling(scale)

##Sets theme and scaling to default on startup
setTheme("System")
setScaling("100%")

class Error(CTkToplevel):
    counter  = 0 ##counter is set to 0 at program startup
    def __init__(self, message):
        super().__init__()

        Error.counter += 1 ##counter increments each time a new error is loaded
        if Error.counter >1: ##prevents more than one error window from loading at any one time
            Error.counter -= 1
            self.destroy()

        ##Sets window title and icon, and prevents resizing or the use of the exit button
        self.title("Error")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        ##Forces the error window above the main window, and prevents any other window from being interacted with
        self.attributes("-topmost",True)
        self.grab_set()
        self.wait_visibility() ##Prevents improper sequencing when running on linux
        
        ##Defines message attribute, and creates error message and close button
        self.message = message
        self.messageLbl = CTkLabel(self, text = self.message)
        self.messageLbl.pack(padx = 10, pady = 5)

        self.closeBtn = CTkButton(self, text = "Close", command=self.close)
        self.closeBtn.pack(padx = 10, pady = 5)
    
    ##Closes the window and decreases the counter, so that the program knows how many error windows exist
    def close(self):
        Error.counter -= 1
        self.destroy()

##Borrows from ListEntryInfo, displays name and option to remove selected list. Calls relevant method of Manage object before reloading 
##tiles, and destroying the window is remove is clicked
class ListInfo(CTkToplevel):
    def __init__(self, i, master):
        super().__init__()

        self.master = master
        self.title = ("List Info")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        self.wait_visibility()
        self.grab_set()

        self.userID = master.userID
        self.listID = master.listIDs[i]
        self.db = Manage(self.userID)
        self.listTitle = master.titles[i]

        self.titleLbl = CTkLabel(self, text = self.listTitle)
        self.titleLbl.pack(padx = 10, pady = 5)
        self.removeBtn = CTkButton(self, text = "Remove", command=self.removeList, fg_color = "#ff3333", hover_color = "#ff4545")
        self.removeBtn.pack(padx = 10, pady = 5)

    def removeList(self):
        self.destroy()
        self.db.removeList(self.listID) ##This method not only deletes the list title button, but also every entry tile linked to it
        self.master.loadListTiles()

##Borrows from GameInfo, displays name and option to remove selected list entry. Calls relevant method of Manage object before reloading tiles, 
##and destroying the window if remove is clicked
class ListEntryInfo(CTkToplevel):
    def __init__(self, i, x, master):
        super().__init__()

        self.master = master
        self.title = ("List Entry Info")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        self.wait_visibility()
        self.grab_set()

        self.userID = master.userID
        self.entryID = master.entryIDs[i][x]
        self.db = Manage(self.userID)
        self.gameName = master.names[i][x]

        self.nameLbl = CTkLabel(self, text = self.gameName)
        self.nameLbl.pack(padx = 10, pady = 5)
        self.removeBtn = CTkButton(self, text = "Remove", command=self.removeEntry, fg_color = "#ff3333", hover_color = "#ff4545")
        self.removeBtn.pack(padx = 10, pady = 5)

    def removeEntry(self):
        self.destroy()
        self.db.removeListEntry(self.entryID)
        self.master.loadListTiles()

class CreateList(CTkToplevel):
    def __init__(self, master):
        super().__init__()

        self.master = master
        self.title = ("Create List")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        self.wait_visibility()
        self.grab_set()

        self.userID = master.userID
        self.db = Manage(self.userID)
        self.libraryIDs = self.db.loadUserGames("default")[1]
        self.counter = 1
        ##Creates a list of game names to be displayed in the drop down, and iteratively adds each game in the library using the loadGameName method
        ##of the Manage object
        ##An identical list, displayNames, is used for actual output to the GUI, as each time a game is selected it will be removed from the dropdown,
        ##but not the actual library
        self.gameNames = []
        self.displayNames = ["Game "+str(self.counter)]
        self.listGames = []
        self.query = Query()
        for each in range (0, len(self.libraryIDs)):
            self.name = self.db.loadGameName(self.libraryIDs[each])
            self.gameNames.append(self.name)
            self.displayNames.append(self.name)

        ##Creates and places an input field for the title of the list, the first dropdown to select a game, and the button to create the list
        self.titleEnt = CTkEntry(self, placeholder_text="List Title")
        self.titleEnt.grid(row = 0, column = 0, padx = 60, pady = (10,5), sticky = "ew")
        self.gameMenu = CTkOptionMenu(self, values = self.displayNames, dynamic_resizing = False, command = self.selectGame)
        self.gameMenu.grid(row = self.counter, column = 0, padx = 60, pady = 5, sticky = "ew")
        self.createBtn = CTkButton(self, text = "Submit", width = 30, command=self.create)
        self.createBtn.grid(row = self.counter+1, padx = 60, pady = (5,10))

    ##Called on selection of a game from the dropdown, appends the matching libraryID of the game to a list, before locking the selected dropdown menu,
    ##and creating an additonal one below to choose the next game
    def selectGame(self, choice):
        self.choice = choice
        ##Sets the libraryID to be empty if the dropdown header was incorrectly selected
        if self.choice == "Game"+str(self.counter):
            self.libraryID = ""
        else:
            ##Iterates through list of game names to find a match, so that the corresponding libraryID can be appended
            for each in range (0, len(self.gameNames)):
                if self.gameNames[each] == self.choice:
                    self.gameMenu.configure(state = "disabled") ##Locks in choice for selected game
                    self.libraryID = self.libraryIDs[each]
                    self.listGames.append(self.libraryID)
                    self.counter +=1
                    ##Revises dropdown to display the next number to be added to the list, and removes previously selected game from being chosen
                    self.displayNames[0] = "Game "+str(self.counter)
                    self.displayNames.remove(self.choice)
                    self.gameMenu = CTkOptionMenu(self, values = self.displayNames, dynamic_resizing = False, command = self.selectGame)
                    self.gameMenu.grid(row = self.counter, column = 0, padx = 60, pady = 5, sticky = "ew")
                    self.createBtn.grid_configure(row = self.counter+1)

    ##Callback method of the Create button, checks for no game selections or an empty or non-unique title, and for prompts the creation of relevant
    ##errors. If checks are passed successfully, the list and list entries are added to the database, before the window is destroyed and the list display
    ##is reloaded
    def create(self):
        self.title = self.titleEnt.get()
        if self.db.checkTitle(self.title) == True:
            Error("List already exists")
        elif self.title == "":
            Error("Please enter a list title")
        elif self.listGames == []:
            Error("Please select at least one game")
        else:
            self.db.newList(self.title, self.listGames)
            self.master.loadListTiles()
            self.destroy()
        
class ReviewInfo(CTkToplevel):
    def __init__(self, i, master): ##Passes in 'i' as a parameter so that it knows at what stage the for loop is being broken out of
        super().__init__()

        ##Defines specifications of the window, and sets the master to an attribute for use in class methods
        self.master = master
        self.title = ("Review Info")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        self.wait_visibility()
        self.grab_set()

        ##Pulls all the relevant user info, and review info to be displayed, ensuring the format the long string of text in the same way as the review
        ##frame
        self.userID = master.userID
        self.db = Manage(self.userID)
        self.userN = self.db.getUserN()
        self.reviewID = master.reviewIDs[i]
        self.name = master.names[i]
        self.score = master.scores[i]
        self.textWrp = textwrap.wrap(master.texts[i], width = 50, max_lines = None)
        self.text = ""
        for x in range (0, len(self.textWrp)):
            self.text = self.text+self.textWrp[x]+"\n"

        ##Creates and places label to contain the review text, as well as share and remove buttons
        self.nameLbl = CTkLabel(self, text = self.text)
        self.nameLbl.pack(padx = 10, pady = 5)
        self.shareBtn = CTkButton(self, text = "Share", command=self.shareReview)
        self.shareBtn.pack(padx = 10, pady = 5)
        self.removeBtn = CTkButton(self, text = "Remove", command=self.removeReview, fg_color = "#ff3333", hover_color = "#ff4545")
        self.removeBtn.pack(padx = 10, pady = 5)

    ##Creates external .txt file containing game name, score out of 5, and wrapped text for easier readability
    def shareReview(self):
        try:
            with open("exports/"+self.name+" "+str(self.score)+" "+self.userN+".txt", "x") as temp:
                temp.write(self.name+" "+str(self.score)+"/5\n\n"+self.text)
        except FileExistsError:
            self.userN += " (1)"
            self.shareReview()
    
    ##Calls relevant method of the Manage object, ensuring to pass in the review ID in question so that the correct record is removed, before destroying
    ##the window and refreshing the tiles so that the changes are reflected in the GUI
    def removeReview(self):
        self.destroy()
        self.db.removeReview(self.reviewID)
        self.master.loadReviewTiles()

class WriteReview(CTkToplevel):
    def __init__(self, master): ##Passes in master frame's attributes and methods
        super().__init__() ##Inherits parents attributes and methods

        ##Sets up the windows characteristics (title, icon, etc.)
        self.master = master
        self.title = ("Write Review")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        self.wait_visibility()
        self.grab_set()

        self.userID = master.userID
        self.db = Manage(self.userID)
        self.libraryIDs = self.db.loadUserGames("default")[1]
        ##Iteratively appends all of the user's games to a list for use in the dropdown, with "Select Game" as a header
        self.gameNames = ["Select Game"]
        self.query = Query()
        for each in range (0, len(self.libraryIDs)):
            self.name = self.db.loadGameName(self.libraryIDs[each])
            self.gameNames.append(self.name)
        
        ##Establishes attributes for the contents of the review, and allows the program to check if they're empty later
        self.libraryID = ""
        self.rating = ""
        self.text = ""

        #Creates and places the dropdown to select the game, selector for the rating, text box for the actual review, and submit to add it to the database
        self.gameMenu = CTkOptionMenu(self, values = self.gameNames, dynamic_resizing = False, command = self.getGame)
        self.gameMenu.pack(padx = 10, pady = (10,5))
        self.ratingLbl = CTkLabel(self, text = "Rating")
        self.ratingLbl.pack(padx = 10, pady = 2)
        self.ratingBtn = CTkSegmentedButton(self, values = ["0", "1", "2", "3", "4", "5"], width = 100, command = self.getRating)
        self.ratingBtn.pack(padx = 10, pady = 5)
        self.reviewBox = CTkTextbox(self, width = 300, wrap = "word")
        self.reviewBox.pack(padx = 10, pady = 5)
        self.submitBtn = CTkButton(self, text = "Submit", command=self.submit)
        self.submitBtn.pack(padx = 10, pady = (5,10))

    ##Grabs the game selected from the dropdown, and matches it to one in the list of game names, which is then used to determine the libraryID
    def getGame(self, choice):
        self.choice = choice
        if self.choice == "Select Game":
            self.libraryID = ""
        else:
            for each in range (0, len(self.gameNames)):
                if self.gameNames[each] == self.choice:
                    self.libraryID = self.libraryIDs[each-1]

    ##Sets rating to the number clicked in the selector
    def getRating(self, value):
        self.rating = value

    ##Fetches the from the textbox, and checks for any empty inputs, generating an error if any are found. Relevant method from the Manage object
    ##is then called, which attempts to add the review, and prompts an error if the specified game already has a review under the user's account
    def submit(self):
        self.text = self.reviewBox.get("0.0", "end")
        if self.libraryID == "" or self.rating == "" or self.text == "":
            Error("Missing field required")
        else:
            if self.db.newReview(self.libraryID, self.rating, self.text) == True:
                Error("Game already added")
            ##Once successfully added, the window is closed and the tiles are refreshed
            else:
                self.destroy()
                self.master.loadReviewTiles()

class GameInfo(CTkToplevel):
    def __init__(self, i, master): ##Passes in 'i' as a parameter so that it knows at what stage the for loop is being broken out of
        super().__init__()

        ##Sets master parameter as an attribute, and defines the specifications of the window (e.g., title, icon, non-resizable)
        self.master = master
        self.title = ("Game Info")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        ##Freezes all other windows
        self.wait_visibility()
        self.grab_set()

        self.userID = master.userID
        ##Fetches libraryID, and string of game name, that corresponds to the selected tile
        self.libraryID = master.libraryIDs[i]
        self.db = Manage(self.userID) ##Creates db management object, so that the game name can be retrieved, and 
                                      ##the relevant records can be deleted if necessary
        self.gameName = self.db.loadGameName(self.libraryID)

        ##Creates and places a label to contain the game name, and a button for removing the selected game
        self.nameLbl = CTkLabel(self, text = self.gameName)
        self.nameLbl.pack(padx = 10, pady = 5)
        self.removeBtn = CTkButton(self, text = "Remove", command=self.removeGame, fg_color = "#ff3333", hover_color = "#ff4545")
        self.removeBtn.pack(padx = 10, pady = 5)

    ##Destroys the window, removes the selected game from the userGame table, and updates the tile display to reflect the new state of the table
    def removeGame(self):
        self.destroy()
        self.db.removeUserGame(self.libraryID)
        self.master.loadGameTiles()

class GameSearch(CTkToplevel):
    def __init__(self, master):
        super().__init__()

        ##Sets master parameter as an attribute, and defines the specifications of the window (e.g., title, icon, non-resizable)
        self.master = master
        self.userID = master.userID ##Makes userID directly accessible as a class-specific attribute, for ease of writing
        self.title("Game Search")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        ##Freezes all other windows
        self.wait_visibility()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: self.close()) ##Binds the built in 'close' button to a prewritten exit method, that causes the 
                                                                ##tiles to be reloaded
        ##Creates and places components of the search GUI, including entry field and 'search' button
        self.searchEnt = CTkEntry(self, placeholder_text="Enter a game")
        self.searchEnt.grid(row = 0, column = 0, padx = (60,5), pady = 10, sticky = "ew")

        self.searchCounter = 0
        self.searchBtn = CTkButton(self, text = "Search", width = 50, command = self.loadResults)
        self.bind("<Return>", self.loadResults) ##Binds the functionality of the search button to the enter key for user convenience
        self.searchBtn.grid(row = 0, column = 1, padx = (5,60), pady = 10, sticky = "ew")

    ##Performs the standard function of closing the current window, as well as calling the master class's tile reload method
    def close(self):
        self.destroy()
        self.master.loadGameTiles()
    
    ##Expands the game title display to show the full text when clicked
    def fullResult(self, i):
        ##Ensures the correct button is being accessed when the for loop is broken out of
        self.resultID = self.query.resultIDs[i]
        self.resultName = self.query.resultNames[i]
        self.checkLength() ##Checks current status of the button so it knows what to toggle it to
        if self.full == False:
            self.resultText = (self.resultName)
            self.full = True
        elif self.full == True:
            self.checkLength()
            self.full = False
        self.resultBtns[self.resultID].configure(text = self.resultText) ##Updates the appearance of the button based on the output of the subroutine call

    ##Adds the selected game to the userGame table of the local database, and links it to the current userID
    def addGame(self, i):
        ##Ensures the correct button is being accessed when the for loop is broken out of
        self.resultID = self.query.resultIDs[i]
        self.resultName = self.query.resultNames[i]
        self.resultRelease = self.query.resultReleases[i]
        ##Creates the database management object, and assigns it to the current user
        self.db = Manage(self.userID)
        ##Displays the relevant error if the game is already in the database, and adds it if not
        if self.db.newGame(self.resultID, self.resultName, self.resultRelease) == True:
            Error("Game already added")

    ##Refreshes the display of game results based on an updated search query    
    def loadResults(self, event = None):
        ##Checks to see if there are already results in the tkinter grid, and removes them if True
        self.searchCounter += 1
        if self.searchCounter == 2:
            for x in self.resultBtns:
                self.resultBtns[x].destroy()
            for x in self.addResultBtns:
                self.addResultBtns[x].destroy()
            self.searchCounter -= 1
        ##Establishes dictionaries to contain the buttons for result text (that can be expanded), and for adding the games
        self.resultBtns = {}
        self.addResultBtns = {}
        self.searchedGame = str(self.searchEnt.get()) ##Fetches and sanitises the search query from the entry field
        ##Establishes the IGDB query object, and passes in the query to return the names and IGDB IDs of the all matching games
        self.query = Query()
        self.query.game(self.searchedGame)
        ##Iteratively calls the createResultBtns method to create and place a button for each item in the list of returned IGDB IDs
        for i in range(0, len(self.query.resultIDs)):
            self.createResultBtns(i)

    ##Creates and places a button for the game relating to the IGDB ID passed in as a parameter
    def createResultBtns(self, i):
        ##Sets the ID as an attribute, and as well as the corresponding name based on matching index postions from two lists
        self.resultID = self.query.resultIDs[i]
        self.resultName = self.query.resultNames[i]
        self.checkLength() ##Calls method to truncate the result name if it is too long
        self.full = False
        ##Creates two buttons; one to contain the name and elongate it if necessary, and another to add it to the database
        ##Each button is added to a relevant dictionary so that it can be individually addressed by breaking out of the for loop
        self.resultBtn = CTkButton(self, text = self.resultText, anchor = "w", fg_color = "transparent", hover = False, 
                                   command = lambda: self.fullResult(i))
        self.resultBtns[self.resultID] = self.resultBtn
        self.resultBtn.grid(row = i+1, column = 0, padx = (10,5), pady = 10, sticky = "ew")
        self.addResultBtn = CTkButton(self, text = "Add", width = 30, fg_color = ("#919191", "#474747"), border_color = ("#848484","#404040"), 
                                      border_width = 2, hover_color = ("#808080","#363636"), command = lambda: self.addGame(i))
        self.addResultBtns[self.resultID] = self.addResultBtn
        self.addResultBtn.grid(row = i+1, column = 1, padx = (5,10), pady = 10, sticky = "ew")

    ##Defines a new variable for the text to be displayed, that is identical to the result name if it is already a suitable length, or
    ##limited to 25 characters, with a "[...]" included to prompt expansion, if not
    def checkLength(self):
        if self.resultName == self.resultName[:25]:
            self.resultText = self.resultName
        else:
            self.resultText = (self.resultName[:25]+"[...]")

class WelcomeWin(CTk):
    def __init__(self):
        super().__init__()

        ##Sets title and icon of window and prevents it from being resized
        self.title("upupdowndown")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)

        ##Creates the logo image and the label containing it, and places it within the GUI
        self.logoImg = CTkImage(light_image = Image.open("images/logo_dark.png"), 
                                dark_image = Image.open("images/logo_light.png"), size = (330,42))
        self.titleLbl = CTkLabel(self, text = "", image = self.logoImg, width = 300, height = 38)
        self.titleLbl.grid(row = 0, column = 0, columnspan = 8, padx = 30, pady = (100,50))

        ##Creates and places the entry boxes for the username and password, as well as the login and create account buttons
        self.passWChar = "•" ##sets the visiblity of the password box to a variable so that it can be toggled
        self.userNEnt = CTkEntry(self, placeholder_text="Username", width = 300, height = 50, 
                                 corner_radius = 11, font = ("Segoe UI", 20))
        self.userNEnt.grid(row = 1, column = 0, columnspan = 8, padx = 30, pady = 5, sticky = "ew")
        self.passWEnt = CTkEntry(self, show = self.passWChar, placeholder_text = "Password", width = 300, height = 50,
                                  corner_radius = 11, font = ("Segoe UI", 20))
        self.passWEnt.grid(row = 2, column = 0, columnspan = 7, padx = (30,5), pady = 5, sticky = "ew")

        self.showIcon = CTkImage(light_image = Image.open("icons/show.png"), 
                                 dark_image = Image.open("icons/show.png"), size = (30,30))
        self.hideIcon = CTkImage(light_image = Image.open("icons/hide.png"), 
                                 dark_image = Image.open("icons/hide.png"), size = (30,30))
        self.showHideBtn = CTkButton(self, text = "", image = self.showIcon , 
                                     width = 50, height = 50, corner_radius = 11, command = self.showHide)
        self.showHideBtn.grid(row = 2, column = 7, padx = (5,30), pady = 5, sticky = "ew")

        self.loginBtn = CTkButton(self, text = "Login", height = 50, corner_radius = 11, 
                                  fg_color = ("#919191", "#474747"), border_color = ("#848484","#404040"), 
                                  border_width = 3, hover_color = ("#808080","#363636"), font = ("Segoe UI Semibold", 20), 
                                  command=self.retUser)
        self.bind("<Return>", self.retUser) ##binds login to the enter key
        self.loginBtn.grid(row = 3, column = 0, columnspan = 4, padx = (30,5), pady = (5,100), sticky = "ew")
        self.createAccBtn = CTkButton(self, text = "Create Account", height = 50, corner_radius = 11, 
                                      font = ("Segoe UI Semibold", 20), command=self.newUser)
        self.createAccBtn.grid(row = 3, column = 4, columnspan = 4, padx = (5,30), pady = (5,100), sticky = "ew")

    ##Called by pressing the show/hide button
    ##Toggles the visibility of the password when entered, as well as the icon contained within the show/hide button
    def showHide(self):
        if self.passWChar == "•":
            self.passWChar = ""
            self.showHideBtn.configure(image = self.hideIcon)
        elif self.passWChar == "":
            self.passWChar = "•"
            self.showHideBtn.configure(image = self.showIcon)
        self.passWEnt.configure(show = self.passWChar)

    ##Called by pressing login (i.e., when a returning user wants to load the program)
    ##Calls another method to fetch the credentials, before passing them to an authentication method and loading the main window if it succeeds, 
    ##or prompting an error upon failure
    def retUser(self, event = None):
        self.getCredentials()
        if self.auth.checkAcc() == True:
            self.userID = self.auth.getUserID()
            self.destroy()
            mainInstance = MainWin(self.userID)
            mainInstance.mainloop()
        else:
            Error("Account not found")

    ##Called by pressing create account
    ##Calls a method to fetch the credentials, and passes them to the auth method for checking that the username is unique
    ##Creates the account if the credentials are valid; otherwise prompts an error
    def newUser(self):
        self.getCredentials()
        if self.auth.checkUserN() == False:
            self.auth.createAcc()
        else:
            Error("Username taken")
    
    ##Fetches the credentials and sanitises them to a string to prevent SQL injection, then checks for empty fields and loads the relevant error
    ##Creates the object for the authentication methods and passes in the fetched credentials
    def getCredentials(self):
        self.username = str(self.userNEnt.get())
        self.password = str(self.passWEnt.get())
        if self.username == "" or self.password == "":
            Error("Please enter both a username and password")
        else:
            self.auth = Auth(self.username, self.password)

class MainWin(CTk):
    def __init__(self, userID): ##Takes userID as a parameter at start of program to be used throughout
        super().__init__()

        ##Declares title and icon of program window, and establishes the userID as an attribute for the first time
        self.title("upupdowndown")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.userID = userID[0][0]
        
        ##Creates separate frames to contain the tabs and sidebar, and places them in the GUI
        self.tabFrame = Home(master = self, height = 570, width = 740)
        self.tabFrame.grid(row = 0, column = 1, sticky = "nesw")
        self.sidebarFrame = Sidebar(master = self, fg_color = "transparent")
        self.sidebarFrame.grid(row = 0, column = 0, sticky = "nesw")
    
    ##Takes selected tab as a parameter, and calls necessary frame class to load it into the GUI
    def loadTab(self, chosenTab):
        self.chosenTab = chosenTab
        ##Clears the current tab for all choices other than settings (is a window, not a tab)
        if self.chosenTab != "Settings":
            self.tabFrame.destroy()
        ##Loads corresponding frame for selected tab
        if self.chosenTab == "Library":
            self.tabFrame = Library(master = self, height = 570, width = 740)
        elif self.chosenTab == "Reviews":
            self.tabFrame = Reviews(master = self, height = 570, width = 740)
        elif self.chosenTab == "Lists":
            self.tabFrame = Lists(master = self, height = 570, width = 740)
        elif self.chosenTab == "Quick Rank":
            self.tabFrame = QuickRank(master = self, height = 570, width = 740)
        ##Creates settings window if selected
        elif self.chosenTab == "Settings":
            Settings(master = self)
        ##Sets tab to Home as default, or if error occurs
        else:
            self.tabFrame = Home(master = self, height = 570, width = 740)
        self.tabFrame.grid(row = 0, column = 1, sticky = "nesw") ##Places selected frame in the GUI

    ##Destroys quick rank frame and loads placeholder frame with end message upon quick rank completion
    def endQR(self):
        self.tabFrame.destroy()
        self.tabFrame = EndScreen(master = self, height = 570, width = 740)
        self.tabFrame.grid(row = 0, column = 1, sticky = "nesw")

class Home(CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.userID = self.master.userID
        ##Creates IGDB query and database management objects
        self.db = Manage(self.userID)
        self.query = Query()

        ##Loads arrays of all relevant data to be displayed
        self.libraryIDs = self.db.loadHome()[0]
        self.igdbIDs = self.db.loadHome()[1]
        self.reviewIDs = self.db.loadHome()[2]
        self.scores = self.db.loadHome()[3]
        self.texts = self.db.loadHome()[4]
        self.reviewNames = self.db.loadHome()[5]
        self.listIDs = self.db.loadHome()[6]
        self.titles = self.db.loadHome()[7]
        self.listNames = self.db.loadHome()[8]

        ##Checks that the user has games to prevent an error, and allow the frame to load even if empty
        if self.igdbIDs != []:
            ##Creates and places title label for the row of games
            self.recentGameLbl = CTkLabel(self, text = "Recent Games", font = ("Segoe UI Semibold", 20))
            self.recentGameLbl.grid(row = 0, column = 0, columnspan = 4, padx = 5, pady = 5, sticky = "w")
            ##Iterates through 4 most recent games, and pulls cover image from URL, before creating and placing a label with the image
            if len(self.igdbIDs) >= 4:
                self.temp = 4
            else:
                ##Prevents error if number of games <4
                self.temp = len(self.igdbIDs)
            for i in range (0,self.temp):
                ##Queries IGDB for cover URL
                self.query.cover(self.igdbIDs[i])
                ##Creates image object from URL
                if self.query.coverURLs != []:
                    with urllib.request.urlopen(self.query.coverURLs[0]) as cover:
                        self.coverData = cover.read()
                        self.coverImg = CTkImage(light_image = Image.open(io.BytesIO(self.coverData)), size = (135,180))
                    ##Creates and places button, using additional padding for the start and end tiles of the row
                    self.tileLbl = CTkLabel(self, text = "", image = self.coverImg, anchor = "center", height = 184, width = 139)
                else:
                    self.gameName = self.db.loadGameName(self.libraryIDs[i])
                    if len(self.gameName) > 15:
                        self.gameName = self.gameName[:15]+"[...]"
                    self.tileLbl = CTkLabel(self, text = self.gameName, anchor = "center", height = 180, width = 135, fg_color = ("#919191", "#474747"), 
                    corner_radius = 0)
                if i == 0:
                    self.x = (5,2)
                elif i == 4:
                    self.x = (2,5)
                else:
                    self.x = 2
                self.tileLbl.grid(row = 1, column = i, padx = self.x, pady = 2)
        
        ##Checks that the user has reviews
        if self.texts != []:
            ##Creates and places title label for the row of reviews
            self.recentReviewLbl = CTkLabel(self, text = "Recent Reviews", font = ("Segoe UI Semibold", 20))
            self.recentReviewLbl.grid(row = 2, column = 0, columnspan = 4, padx = 5, pady = 5, sticky = "w")
            ##Iterates through 2 most recent reviews, wrapping review text and loading necessary star rating image to display in a label
            if len(self.texts) >= 2:
                self.temp = 2
            else:
                ##Prevents error if number of reviews <2
                self.temp = len(self.texts)
            for i in range (0,self.temp):
                ##Uses same text wrapping code as Reviews class
                self.text = ""
                self.textWrp = textwrap.wrap(self.texts[i], width = 50, max_lines = 5, placeholder = "[...]")
                for x in range (0, len(self.textWrp)):
                    self.text = self.text+self.textWrp[x]+"\n"
                ##Creates and places review labels using wrapped text and the image that relates to the score, ensuring to add extra padding for start
                ##and end tiles of the row
                self.tileImg = CTkImage(light_image = Image.open("icons/"+str(self.scores[i])+"_dark.png"), 
                                        dark_image = Image.open("icons/"+str(self.scores[i])+"_light.png"), size = (120, 24))
                self.tileLbl = CTkLabel(self, text = self.reviewNames[i]+"\n\n"+self.text, image = self.tileImg, compound = "top", height = 180, 
                                        width = 350, fg_color = ("#919191", "#474747"), corner_radius = 0)
                if i == 0:
                    self.x = (5,2)
                elif i == 4:
                    self.x = (2,5)
                else:
                    self.x = 2
                self.tileLbl.grid(row = 3, column = i*2, columnspan = 2, padx = self.x, pady = 2)

        ##Checks that the user has lists
        if self.listNames != []:
            ##Creates and places title label for the row of lists
            self.recentListLbl = CTkLabel(self, text = "Recent Lists", font = ("Segoe UI Semibold", 20))
            self.recentListLbl.grid(row = 4, column = 0, columnspan = 4, padx = 5, pady = 5, sticky = "w")
            ##Iterates through 4 most recent lists, placing list title and an array of truncated game names within a label
            if len(self.listNames) >= 4:
                self.temp = 4
            else:
                ##Prevents error if number of lists <4
                self.temp = len(self.listNames)
            for i in range (0,self.temp):
                self.listString = ""
                ##Iterates through game names, reducing them to 15 characters, and adding them to a new line in a string of names to display
                for x in range (0, len(self.listNames[i])):
                    self.listString = self.listString+self.listNames[i][x][:15]+"[...]\n"
                ##Creates label with title of the list, and each truncated game name on seperate lines
                self.tileLbl = CTkLabel(self, text = self.titles[i]+"\n\n"+self.listString, compound = "top", fg_color = ("#919191", "#474747"), 
                                        corner_radius = 0, height = 184, width = 139)
                ##Places each label with extra padding for the first and last tiles in each row
                if i == 0:
                    self.x = (5,2)
                elif i == 4:
                    self.x = (2,5)
                else:
                    self.x = 2
                self.tileLbl.grid(row = 5, column = i, sticky = "new", padx = self.x, pady = 2)

class Library(CTkScrollableFrame):
    ##Master object (main window) is passed in as a parameter
    def __init__(self, master, **kwargs):
        ##Inherits methods and attributes of parent class
        super().__init__(master, **kwargs)

        self.userID = master.userID ##Pulls current userID from master
        ##Creates "Sort By" dropdown, as well as "Add Game" button, and places them in the GUI
        self.sortMenu = CTkOptionMenu(self, values = ["Sort by", "Rating ↓", "Rating ↑", "Quick Rank ↓", "Quick Rank ↑", "A-Z", "Z-A", 
                                                      "Newest Release", "Oldest Release"], fg_color = ("#919191", "#474747"), 
                                                      button_color = ("#919191", "#474747"), button_hover_color = ("#808080","#363636"), 
                                                      command = self.getSort)
        self.sortMenu.grid(row = 0, column = 0, padx = 5, pady = 5)
        self.addIcon = CTkImage(light_image=  Image.open("icons/add.png"), dark_image = Image.open("icons/add.png"), size = (75,75))
        self.addGameBtn = CTkButton(self, text = "Add Game", image = self.addIcon, compound = "top", height = 180, width = 135, corner_radius = 0, 
                                    font = ("Segoe UI Semibold", 20), command = lambda: GameSearch(master = self))
        self.addGameBtn.grid(row = 1, column = 0, padx = (5,2), pady = 2)
        ##Sets sorting mode to default and calls method to load game tiles
        self.sort = "default"
        self.loadCounter = 0
        self.loadGameTiles()

    def getSort(self, choice):
        ##Sets sorting method by getting the selected item in the dropdown, then reloads the tiles with the new sort in place
        self.sort = choice
        if choice == "Sort by": ##Accounts for user selecting the dropdown title as an option
            self.sort = "default"
        else:
            self.sort = choice
        self.loadGameTiles()

    def loadGameTiles(self):
        ##Removes prior tiles, if they exist, before loading the new ones
        self.loadCounter += 1
        if self.loadCounter == 2:
            for x in self.tiles:
                self.tiles[x].destroy()
            self.loadCounter -= 1
        ##Creates database management object, and uses it to get the igdbIDs and local libraryIDs of the current user
        self.db = Manage(self.userID)
        self.igdbIDs = self.db.loadUserGames(self.sort)[0]
        self.libraryIDs = self.db.loadUserGames(self.sort)[1]
        self.query = Query() ##Creates IGDB query object
        ##Creates a dictionary to contain the tiles, then iteratively creates the tiles from the fetched lists above, and adds them to the dictionary
        self.tiles = {}
        for i in range (0, len(self.igdbIDs)):
            self.query.cover(self.igdbIDs[i])
            ##URL of required cover image is received from the IGDB API, then urllib is used to pull the image from that URL, before it is 
            #converted it to a PIL image object
            if self.query.coverURLs != []:
                with urllib.request.urlopen(self.query.coverURLs[0]) as cover:
                    self.coverData = cover.read()
                    self.coverImg = CTkImage(light_image = Image.open(io.BytesIO(self.coverData)), size = (135,180))
                self.tileBtn = CTkButton(self, text = "", image = self.coverImg, anchor = "center", height = 184, width = 139, fg_color = "transparent", 
                corner_radius = 0, hover_color = ("#848484","#404040"), command = lambda i=i: GameInfo(i, master = self))
            else:
                self.gameName = self.db.loadGameName(self.libraryIDs[i])
                if len(self.gameName) > 15:
                        self.gameName = self.gameName[:15]+"[...]"
                self.tileBtn = CTkButton(self, text = self.gameName, anchor = "center", height = 180, width = 135, fg_color = ("#919191", "#474747"), 
                corner_radius = 0, hover_color = ("#848484","#404040"), command = lambda i=i: GameInfo(i, master = self))
            self.tiles[self.libraryIDs[i]] = self.tileBtn
        
        ##Defines counters that control the placement of tiles, and the tile currently being placed, as the tiles are iterated through and
        ##assigned to a grid position in the GUI
        self.tileCounter = 0
        self.rowCounter = 1
        self.columnCounter = 1
        ##Tiles are iterated through and gridded, starting with the second column of the first row, as the first column is already taken up by
        ##the add game button
        while self.tileCounter <= (len(self.libraryIDs)-1):
            ##Moves to the next row once the current one is full (limit of 5 per row)
            if (self.tileCounter+1) >= 5*(self.rowCounter):
                    self.rowCounter += 1
                    self.columnCounter = 0
            ##Changes the padding of the end tiles on each row to 5 instead of 2
            if self.columnCounter == 0:
                self.x = (5,2)
            elif self.columnCounter == 4:
                self.x = (2,5)
            else:
                self.x = 2
            ##Tiles are placed, and the tile and column counters are incremented for the next iteration
            self.tiles[self.libraryIDs[self.tileCounter]].grid(row = self.rowCounter, column = self.columnCounter, padx = self.x, pady = 2)
            self.tileCounter += 1
            self.columnCounter += 1
            
class Reviews(CTkScrollableFrame):
    def __init__(self, master, **kwargs): ##Master frame passed in as a parameter
        super().__init__(master, **kwargs)##Initiates inheritance of parent class attributes and methods
        
        self.userID = master.userID
        self.addIcon = CTkImage(light_image=  Image.open("icons/add.png"), dark_image = Image.open("icons/add.png"), size = (75,75))
        ##Creates and places button for adding review, which fills half a row as a precedent for the other tiles
        self.addReviewBtn = CTkButton(self, text = "Add Review", image = self.addIcon, compound = "top", height = 180, width = 350, 
                                      corner_radius = 0, font = ("Segoe UI Semibold", 20), command = lambda: WriteReview(master = self))
        self.addReviewBtn.grid(row = 0, column = 0, padx = (5,2), pady = 2)
        self.loadCounter = 0
        self.loadReviewTiles()

    ##Iteratively loads tiles for each review in a user's library, and clears and pre-existing tiles
    def loadReviewTiles(self):
        ##Code reused from the check system in Library
        self.loadCounter += 1
        if self.loadCounter == 2:
            for x in self.tiles:
                self.tiles[x].destroy()
            self.loadCounter -= 1
        ##Manage object is declared, and used to fetch the review IDs, scores (/5) and review text for each review
        self.db = Manage(self.userID)
        self.reviewIDs = self.db.loadReviews()[0]
        self.scores = self.db.loadReviews()[1]
        self.texts = self.db.loadReviews()[2]
        self.igdbIDs = []
        self.names = []
        
        ##Gets the IGDB IDs of each game that has a review, by iterating through a list of 
        ##libraryIDs and appending the corresponding IGDB ID if a match is found
        self.temp1 = self.db.loadUserGames("default")[1]
        self.temp2 = self.db.loadUserGames("default")[0]
        self.libraryIDs = self.db.loadReviews()[3]
        for x in range (0, len(self.libraryIDs)):
            for i in range (0, len(self.temp1)):
                if self.libraryIDs[x] == self.temp1[i]:
                    self.igdbIDs.append(self.temp2[i])
        self.query = Query()
        ##Iteratively fetches the name of each of the games with a review and appends it to a list
        for x in range (0, len(self.igdbIDs)):
            self.names.append(self.db.loadGameName(self.libraryIDs[x]))
        self.tiles = {}
        ##Uses largely the same system as Library to iteratively create the buttons, and save them in a dictionary
        for i in range (0, len(self.reviewIDs)):
            ##Text wrap library converts the long string of text into a list of equally sized strings, which can then be iteratively reassembled into
            ##a single string, with a new line character placed between each
            self.text = ""
            self.textWrp = textwrap.wrap(self.texts[i], width = 50, max_lines = 5, placeholder = "[...]")
            for x in range (0, len(self.textWrp)):
                self.text = self.text+self.textWrp[x]+"\n"
            ##Matches the score of the review to a corresponding image with the right amount of stars
            self.tileImg = CTkImage(light_image = Image.open("icons/"+str(self.scores[i])+"_dark.png"), 
                                    dark_image = Image.open("icons/"+str(self.scores[i])+"_light.png"), size = (120, 24))
            self.tileBtn = CTkButton(self, text = self.names[i]+"\n\n"+self.text, image = self.tileImg, 
                                     compound = "top", height = 180, width = 350, fg_color = ("#919191", "#474747"), corner_radius = 0, 
                                     hover_color = ("#808080","#363636"), command = lambda i=i: ReviewInfo(i, master = self))
            self.tiles[self.db.reviewIDs[i]] = self.tileBtn

        ##Code reused from the placement system in Library, but altered to account for the wider tiles (2 per row)
        self.tileCounter = 0
        self.rowCounter = 0
        self.columnCounter = 1
        while self.tileCounter <= (len(self.db.reviewIDs)-1):
            if (self.tileCounter+1) >= 2*(self.rowCounter+1):
                    self.rowCounter += 1
                    self.columnCounter = 0
            if self.columnCounter == 0:
                self.x = (5,2)
            elif self.columnCounter == 1:
                self.x = (2,5)
            else:
                self.x = 2
            self.tiles[self.db.reviewIDs[self.tileCounter]].grid(row = self.rowCounter, column = self.columnCounter, padx = self.x, pady = 2)
            self.tileCounter += 1
            self.columnCounter += 1

class Lists(CTkScrollableFrame):
    def __init__(self, master, **kwargs): ##Master parameter enables access to attributes and methods of the frame containing Lists
        super().__init__(master, **kwargs) ##Inherits from parent class

        self.master = master
        self.userID = master.userID
        ##Creates a button in the GUI identical to the one in Reviews, with the text changed to "Add List"
        self.addIcon = CTkImage(light_image=  Image.open("icons/add.png"), dark_image = Image.open("icons/add.png"), size = (75,75))
        self.addListBtn = CTkButton(self, text = "Add List", image = self.addIcon, compound = "top", height = 180, width = 730, corner_radius = 0, 
                                    font = ("Segoe UI Semibold", 20), command = lambda: CreateList(master = self))
        self.addListBtn.grid(row = 0, column = 0, columnspan = 5, padx = (5,2), pady = 2)
        self.loadCounter = 0
        self.loadListTiles()

    ##Iteratively creates a header button for each list, and a series of tiles for each entry in each list, before employing a for loop to them 
    ##grid them in the GUI
    def loadListTiles(self):
        ##Code borrowed from Library, destroys any pre-existing list headers and tiles so that new ones can be loaded
        self.loadCounter += 1
        if self.loadCounter == 2:
            for x in range (0, len(self.allTiles)):
                for i in self.allTiles[x]:
                    self.allTiles[x][i].destroy()
            for x in self.listBtns:
                self.listBtns[x].destroy()
            self.loadCounter -= 1
        ##Calls loadLists method of Manage object to pull arrays for each field in list and listEntry tables
        self.db = Manage(self.userID)
        self.listIDs = self.db.loadLists()[0]
        self.titles = self.db.loadLists()[1]
        self.libraryIDs = self.db.loadLists()[2]
        self.igdbIDs = self.db.loadLists()[3]
        self.names = self.db.loadLists()[4]
        self.entryIDs = self.db.loadLists()[5]
        self.query = Query()
        self.allTiles = []
        ##Iteratively creates list entry tiles, and places them in a dictionary of entries from that list. Each dictionary is then added to an array
        ##containing each list
        for i in range (0, len(self.listIDs)):
            self.listTiles = {}
            for x in range (0, len(self.igdbIDs[i])):
                self.query.cover(self.igdbIDs[i][x])
                if self.query.coverURLs != []:
                    with urllib.request.urlopen(self.query.coverURLs[0]) as cover:
                        self.coverData = cover.read()
                        self.coverImg = CTkImage(light_image = Image.open(io.BytesIO(self.coverData)), size = (135,180))
                    self.tileBtn = CTkButton(self, text = "", image = self.coverImg, anchor = "center", height = 184, width = 139, 
                    fg_color = "transparent", corner_radius = 0, hover_color = ("#848484","#404040"), 
                    command = lambda i=i, x=x: ListEntryInfo(i, x, master = self))
                else:
                    self.gameName = self.db.loadGameName(self.libraryIDs[i][x])
                    if len(self.gameName) > 15:
                            self.gameName = self.gameName[:15]+"[...]"
                    self.tileBtn = CTkButton(self, text = self.gameName, anchor = "center", height = 180, width = 135, fg_color = ("#919191", "#474747"), 
                    corner_radius = 0, hover_color = ("#848484","#404040"), command = lambda i=i, x=x: ListEntryInfo(i, x, master = self))
                self.listTiles[self.libraryIDs[i][x]] = self.tileBtn
            self.allTiles.append(self.listTiles)
        
        ##Iteratively creates and places a header button for each list, and places the entry tiles for that list under the header
        self.listBtns = {}
        self.rowCounter = 0
        ##Iterates through the 2D list of libraryIDs, where each index represents one list, and the indexes of that index represent the entries
        for i in range (0, len(self.libraryIDs)):
            ##Increments row for each new list, and resets column to 0
            self.rowCounter += 1
            self.columnCounter = 0
            ##Creates and places header button for the list, and adds it to a dictionary
            self.titleBtn = CTkButton(self, text = self.titles[i], font = ("Segoe UI Semibold", 20), fg_color = "transparent", anchor = "w", 
                                      command = lambda i=i: ListInfo(i, master = self))
            self.listBtns[self.listIDs[i]] = self.titleBtn
            self.titleBtn.grid(row = self.rowCounter, column = self.columnCounter, columnspan = 5, padx = 5, pady = (30,2), sticky = "w")
            self.rowCounter += 1 ##Row increments to display list games below the releveant header
            ##Iterates through the current index of the 2D list, placing the matching button from the "allTiles" dictionary
            for x in range (0, len(self.libraryIDs[i])):
                ##Increases padding for the first and last tile in a row
                if self.columnCounter == 0:
                    self.x = (5,2)
                elif self.columnCounter == 4:
                    self.x = (2,5)
                else:
                    self.x = 2
                self.allTiles[i][self.libraryIDs[i][x]].grid(row = self.rowCounter, column = self.columnCounter, padx = self.x, pady = 2)
                ##Moves to next column, starting a new row and resetting to first column if the last column has been reached
                self.columnCounter += 1
                if self.columnCounter == 5:
                    self.columnCounter = 0
                    self.rowCounter += 1

class QuickRank(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.userID = master.userID
        ##Creates and places start button in an otherwise empty window, which prompts the user to begin the quick rank process
        self.startBtn = CTkButton(self, text = "Start Quick Rank", height = 50, corner_radius = 11, font = ("Segoe UI Semibold", 20), command=self.start)
        self.startBtn.pack(padx = 20, pady = 20)
        self.loadCounter = 0

    ##Called when start button clicked, creates GUI constants (up/down icons, "VS" label) and fetches from/amends the database as necessary before
    ##starting comparisons with the user's first two games
    def start(self):
        ##Removes start button, and creates up and down icons and "VS" label (places this too)
        self.startBtn.destroy()
        self.vsLbl = CTkLabel(self, text = "VS", font = ("Segoe UI Bold", 50))
        self.vsLbl.grid(row = 0, column = 2, padx = 2, pady = 2)
        self.upIcon = CTkImage(light_image = Image.open("icons/up.png"), size = (40,40))
        self.downIcon = CTkImage(light_image = Image.open("icons/down.png"), size = (40,40))

        ##Fetches IGDB and library IDs from database, resets all elo values to baseline (1000) and starts comparison with the first two items
        ##of the libraryIDs array
        self.db = Manage(self.userID)
        self.igdbIDs = self.db.loadUserGames("default")[0]
        self.libraryIDs = self.db.loadUserGames("default")[1]
        self.db.startQR(self.libraryIDs)
        self.query = Query()
        self.compare(0,1)

    ##Creates all GUI elements for current comparison, including left and right game images, as well as up and down buttons
    def compare(self, leftPtr, rightPtr): ##Passes in current index positions being compared
        self.leftPtr = leftPtr
        self.rightPtr = rightPtr
        ##If pointers exceed the number of games, then quick rank is complete, and the end screen can be loaded into the GUI
        if self.leftPtr > (len(self.libraryIDs)-1) or self.rightPtr > (len(self.libraryIDs)-1):
            self.master.endQR()
        else:
            ##Utilises same counter system to remove and replace GUI elements if there was a previous comparison
            self.loadCounter += 1
            if self.loadCounter == 2:
                self.leftLbl.destroy()
                self.rightLbl.destroy()
                self.upBtn.destroy()
                self.downBtn.destroy()
            ##Gets libraryIDs of games to be compared
            self.leftGame = self.libraryIDs[self.leftPtr]
            self.rightGame = self.libraryIDs[self.rightPtr]
            self.query.cover(self.igdbIDs[self.leftPtr])
            ##Creates and places cover images of games to be compared
            if self.query.coverURLs != []:
                with urllib.request.urlopen(self.query.coverURLs[0]) as cover:
                    self.coverData = cover.read()
                    self.coverImg = CTkImage(light_image = Image.open(io.BytesIO(self.coverData)), size = (324,432))
                self.leftLbl = CTkLabel(self, text = "", image = self.coverImg, anchor = "center", height = 432, width = 324, fg_color = "transparent", 
                                        corner_radius = 0)
            else:
                self.gameName = self.db.loadGameName(self.libraryIDs[self.leftPtr])
                if len(self.gameName) > 15:
                        self.gameName = self.gameName[:15]+"[...]"
                self.leftLbl = CTkLabel(self, text = self.gameName, anchor = "center", height = 432, width = 324, fg_color = "transparent", 
                                        corner_radius = 0)
            self.leftLbl.grid(row = 0, column = 0, columnspan = 2, padx = 10, pady = 10)
            self.query.cover(self.igdbIDs[self.rightPtr])
            if self.query.coverURLs != []:
                with urllib.request.urlopen(self.query.coverURLs[0]) as cover:
                    self.coverData = cover.read()
                    self.coverImg = CTkImage(light_image = Image.open(io.BytesIO(self.coverData)), size = (324,432))
                self.rightLbl = CTkLabel(self, text = "", image = self.coverImg, anchor = "center", height = 432, width = 324, fg_color = "transparent", 
                                        corner_radius = 0)
            else:
                self.gameName = self.db.loadGameName(self.libraryIDs[self.rightPtr])
                if len(self.gameName) > 15:
                        self.gameName = self.gameName[:15]+"[...]"
                self.rightLbl = CTkLabel(self, text = self.gameName, anchor = "center", height = 432, width = 324, fg_color = "transparent", 
                                        corner_radius = 0)
            self.rightLbl.grid(row = 0, column = 3, padx = 10, pady = 10)

            ##Creates and places up and down buttons
            self.upBtn = CTkButton(self, text = "", image = self.upIcon, fg_color = "#09db64", hover_color = "#1df078", width = 50, height = 50, 
                                   corner_radius = 11, command = self.up)
            self.upBtn.grid(row = 1, column = 0, padx = (10,5), pady = 5, sticky = "e")
            self.downBtn = CTkButton(self, text = "", image = self.downIcon, width = 50, height = 50, corner_radius = 11, command = self.down)
            self.downBtn.grid(row = 1, column = 1, padx = (5,10), pady = 5, sticky = "w")
    
    ##Runs if left game wins, calls relevant Manage method to update elo ratings before incrementing the right game
    def up(self):
        self.leftWin = True
        self.db.updateELO(self.leftGame, self.rightGame, self.leftWin)
        ##Pointer that designates the index position of the right game in "libraryIDs" is incremented
        self.rightPtr += 1
        ##Ensures right game moves past current game on the left in the array, to prevent a comparison of identical games
        if self.rightPtr == self.leftPtr:
            self.rightPtr += 1
        self.compare(self.leftPtr, self.rightPtr) ##Recalls comparison method to initiate the next quick rank round

    ##Runs if right game wins, performs the same functions as above, only in reference to the other game
    def down(self):
        self.leftWin = False
        self.db.updateELO(self.leftGame, self.rightGame, self.leftWin)
        self.leftPtr += 1
        if self.leftPtr == self.rightPtr:
            self.leftPtr += 1
        self.compare(self.leftPtr, self.rightPtr)

##Loaded as a placeholder upon quick rank finishing, displays completion message to the user so that they switch tabs
class EndScreen(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.endLbl = CTkLabel(self, text = "Quick Rank Complete", font = ("Segoe UI Semibold", 20))
        self.endLbl.pack(padx = 20, pady = 20)

class Settings(CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.userID = self.master.userID
        self.title("Settings")
        self.iconbitmap("icons/logo.ico")
        self.resizable(False,False)
        self.attributes("-topmost",True)
        self.wait_visibility()
        self.grab_set()
        self.db = Manage(self.userID)

        ##Creates and places username and password entry boxes, as well as corresponding "Update" buttons, option menus for the theme and scale, 
        ##and log out and delete account buttons
        self.newUserNEnt = CTkEntry(self, placeholder_text="New Username", font = ("Segoe UI", 13))
        self.newUserNEnt.grid(row = 0, column = 0, columnspan = 5, padx = (10,5), pady = (10,5), sticky = "ew")
        self.updateBtn1 = CTkButton(self, text = "Update", width = 20, fg_color = ("#919191", "#474747"), border_color = ("#848484","#404040"), 
        border_width = 2, hover_color = ("#808080","#363636"), command = self.updateUserN)
        self.updateBtn1.grid(row = 0, column = 5, padx = (5,10), pady = (10,5), sticky = "ew")
        self.newPassWEnt = CTkEntry(self, placeholder_text="New Password", font = ("Segoe UI", 13))
        self.newPassWEnt.grid(row = 1, column = 0, columnspan = 5, padx = (10,5), pady = 5, sticky = "ew")
        self.updateBtn2 = CTkButton(self, text = "Update", width = 20, fg_color = ("#919191", "#474747"), border_color = ("#848484","#404040"), 
        border_width = 2, hover_color = ("#808080","#363636"), command = self.updatePassW)
        self.updateBtn2.grid(row = 1, column = 5, padx = (5,10), pady = 5, sticky = "ew")

        self.scaleMenu = CTkOptionMenu(self, values = ["Select UI Scale", "25%", "50%", "75%", "100%", "125%", "150%", "200%"], 
        fg_color = ("#919191", "#474747"), button_color = ("#919191", "#474747"), button_hover_color = ("#808080","#363636"), command = setScaling)
        self.scaleMenu.grid(row = 2, column = 0, columnspan = 3, padx = (10,5), pady = 5, sticky = "ew")
        self.themeMenu = CTkOptionMenu(self, values = ["Select Theme", "System", "Light", "Dark"], fg_color = ("#919191", "#474747"), 
        button_color = ("#919191", "#474747"), button_hover_color = ("#808080","#363636"), command = setTheme)
        self.themeMenu.grid(row = 2, column = 3, columnspan = 3, padx = (5,10), pady = 5, sticky = "ew")

        self.logOutBtn = CTkButton(self, text = "Log Out", fg_color = ("#919191", "#474747"), border_color = ("#848484","#404040"), border_width = 2, 
        hover_color = ("#808080","#363636"), command = self.logOut)
        self.logOutBtn.grid(row = 3, column = 2, columnspan = 3, padx = 5, pady = (5,10), sticky = "ew")
        self.deleteAccBtn = CTkButton(self, text = "Delete Account", fg_color = "#ff3333", hover_color = "#ff4545", command = self.deleteAcc)
        self.deleteAccBtn.grid(row = 4, column = 2, columnspan = 3, padx = 5, pady = (5,10), sticky = "ew")

    ##Checks that username entry isn't empty, before creating Auth object and calling its relevant method to update the database
    def updateUserN(self):
        self.username = str(self.newUserNEnt.get())
        if self.username == "":
            Error("Please enter a username")
        else:
            self.auth = Auth(self.username, None)
            if self.auth.checkUserN() == False:
                self.db.updateUserN(self.username)
            else: ##Outputs error if Auth method returns True (username taken)
                Error("Username taken")

    ##Checks that password entry isn't empty, before creating Auth object and calling its relevant method to update the database
    def updatePassW(self):
        self.password = str(self.newPassWEnt.get())
        if self.password == "":
            Error("Please enter both a password")
        else:
            self.db.updatePassW(self.password)

    ##Destroys current window, as well as the master frame and window its contained in, before creating and calling login window
    def logOut(self):
        self.destroy()
        self.master.destroy()
        welcomeInstance = WelcomeWin()
        welcomeInstance.mainloop()
    
    ##Calls method of Manage to remove all records linked to the current userID, before performing the same actions as "logOut"
    def deleteAcc(self):
        self.db.removeAcc()
        self.destroy()
        self.master.destroy()
        welcomeInstance = WelcomeWin()
        welcomeInstance.mainloop()

class Sidebar(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        self.userID = master.userID

        ##Declares names for each of the tabs in an iterable array
        self.tabNames = ["Home", "Library", "Reviews", "Lists", "Quick Rank", "Settings"]
        self.tabBtns = {} ##Creates dictionary to store each tab button

        ##Iterates through array of tab names and repeatedly calls method to create button for each tab
        for i in range (0, len(self.tabNames)):
            self.createBtns(i)

        ##Creates and places "Menu" button, as it has different behaviour to the other buttons (collapsing the entire frame, alternate colour)
        self.btnTxt = "Menu"
        self.menuIcon = CTkImage(light_image = Image.open("icons/menu.png"), dark_image = Image.open("icons/menu.png"), size = (25,25))
        self.menuBtn = CTkButton(self, width = 150, text = self.btnTxt, font = ("Segoe UI Semibold", 16), image = self.menuIcon, anchor = "center", 
                                 command = self.collapse, corner_radius = 0, fg_color = ("#919191", "#474747"), hover_color = ("#808080","#363636"))
        self.menuBtn.grid(row = 0, column = 0)

    ##Called iteratively to create the buttons, place them one after the other in the sidebar, and add them to the dictionary
    def createBtns(self, i):
        ##Creates image object from file name that corresponds to the current item of the array
        self.tempIcon = CTkImage(light_image = Image.open("icons/"+self.tabNames[i].lower()+"_dark.png"), 
                                 dark_image = Image.open("icons/"+self.tabNames[i].lower()+"_light.png"), size = (20,20))
        ##Callback function passes in name of the button
        self.tempBtn = CTkButton(self, width = 150, text = self.tabNames[i], text_color = ("#313336","#DCE4EE"), image = self.tempIcon, anchor = "w", 
                                 command = lambda: self.master.loadTab(self.tabNames[i]), corner_radius = 0, fg_color = "transparent")
        ##Places the buttons, using the iterator variable to determine the row
        ##Increases spacing for settings so that it appears at the bottom
        if self.tabNames[i] == "Settings":
            self.tempBtn.grid(row = i+1, column = 0, sticky = "ew", pady = (380,0))
        else:
            self.tempBtn.grid(row = i+1, column = 0, sticky = "ew")
        self.tabBtns[self.tabNames[i]] = self.tempBtn

    ##Toggles the width of the sidebar (collapses/uncollapses) based on the contents of "btnTxt"
    def collapse(self):
        ##Checks if "btnTxt" is empty, and increases the width if it is. If it contains "Menu" then the width is decreased
        if self.btnTxt == "Menu":
            ##Changes "btnTxt" for when the button is next clicked
            self.btnTxt = ""
            ##Iterates through dictionary of tab buttons to reduce their width
            for i in range (0, len(self.tabBtns)):
                self.tabBtns[self.tabNames[i]].configure(text = "", width = 20, anchor = "center")
            ##Reduces width of menu button, and updates text
            self.menuBtn.configure(text = self.btnTxt, width = 20)
        ##Performs the same actions as above, instead increasing width to 150
        elif self.btnTxt == "":
            self.btnTxt = "Menu"
            for i in range (0, len(self.tabBtns)):
                self.tabBtns[self.tabNames[i]].configure(text = self.tabNames[i], width = 150, anchor = "w")
            self.menuBtn.configure(text = self.btnTxt, width = 150)

##Runs at program startup to open the login window, and prevent this file from being called by any other
if __name__ == "__main__":
    welcomeInstance = WelcomeWin()
    welcomeInstance.mainloop()
    # mainInstance = MainWin()
    # mainInstance.mainloop() ##Used for testing just the main window