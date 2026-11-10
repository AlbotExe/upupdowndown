import sqlite3
import math
import hashlib

class Manage():
    def __init__(self, userID):
        super().__init__()

        self.db = sqlite3.connect('upupdowndown.db')
        self.cursor = self.db.cursor()
        self.userID = userID

    ##Returns username linked to userID specified in the constructor method
    def getUserN(self):
        self.cursor.execute("SELECT username FROM account WHERE userID = ?", (self.userID,))
        self.db.commit
        self.userN = self.cursor.fetchone()[0]
        return self.userN

    ##Checks if an inputted List title has already been used before by the current user, returns True if so
    def checkTitle(self, title):
        self.found = False
        self.title = title ##Requested title passed in as parameter and defined as an attribute
        ##Query returns all titles of lists under specified userID
        self.cursor.execute("SELECT list.listTitle FROM list JOIN listEntry, userGame ON list.listID = listEntry.listID and listEntry.libraryID = userGame.libraryID WHERE userGame.userID = ?", (self.userID,))
        self.db.commit()
        self.fetchedTitles = self.cursor.fetchall()
        self.fetchedTitles = list(dict.fromkeys(self.fetchedTitles)) ##Converts results from a list to a dictionary and back to a list to remove
                                                                     ##repeated data (due to the nature of the JOIN clause)
        ##Iterates through fetched titles and returns true if a match is found
        for i in range (0, len(self.fetchedTitles)):
            if self.title == self.fetchedTitles[i][0]:
                self.found = True
        return self.found

    ##Takes list title and array of games as parameters, and creates a new record in list table and as many new records as required in listEntry table
    def newList(self, title, listGames):
        self.title = title
        self.listGames = listGames
        ##Executes statement to create list record
        self.cursor.execute("INSERT INTO list (listTitle) VALUES (?)", (self.title,))
        self.db.commit()
        ##Query to find PK of the record just created
        self.cursor.execute("SELECT listID FROM list ORDER BY listID DESC")
        self.db.commit()
        self.listID = self.cursor.fetchone()[0]
        ##Iteratively creates records for each of the games selected in the GUI, linking them to the PK just fetched
        for x in range (0, len(self.listGames)):
            self.cursor.execute("INSERT INTO listEntry (listID, libraryID) VALUES (?,?)", (self.listID, self.listGames[x]))
            self.db.commit()

    ##Insert the user specified game into the 'game' table, if not already present, and then the 'userGame' along with the current userID
    def newGame(self, igdbID, name, releaseDate):
        self.igdbID = str(igdbID)
        self.name = name
        self.releaseDate = releaseDate
        self.gameExists = False
        ##Checks to see if the unique identifier (igdbID) for specified game is already in 'game'
        self.cursor.execute("SELECT igdbID FROM game WHERE igdbID = ?", (self.igdbID,))
        self.db.commit()
        ##Adds details of the game to the table if not already present
        if self.cursor.fetchone() == None:
            self.cursor.execute("INSERT INTO game (igdbID, name, releaseDate) VALUES (?, ?, ?)", (self.igdbID, self.name, self.releaseDate))
            self.db.commit()
        ##Fetches PK of the record just created for the game
        self.cursor.execute("SELECT gameID FROM game WHERE igdbID = ?", (self.igdbID,))
        self.db.commit()
        self.gameID = (self.cursor.fetchone()[0]) ##Sets PK to an attribute
        
        ##Checks to if a record already exists for this specific game, under this specific user
        self.cursor.execute("SELECT userID, gameID FROM userGame WHERE userID = ? AND gameID = ?", (self.userID, self.gameID))
        self.db.commit()
        ##Adds a record of the PK from 'account' and 'game' to the table if not already present, and returns True if not
        if self.cursor.fetchone() == None:
            self.cursor.execute("INSERT INTO userGame (userID, gameID) VALUES (?, ?)", (self.userID, self.gameID))
            self.db.commit()
        else:
            self.gameExists = True
        return self.gameExists ##This allows a relevant error message to be displayed
    
    ##Creates a new record in the 'review' table for the requested game, with all the user-provided information for the review
    def newReview(self, libraryID, rating, text):
        self.reviewExists = False
        self.libraryID = libraryID
        self.rating = rating
        self.text = text
        ##Executes SELECT query to check that a review for the game doesn't already exist in this account
        self.cursor.execute("SELECT libraryID FROM review WHERE libraryID = ?", (self.libraryID,))
        self.db.commit()
        ##If the review doesn't already exist, creates the specified record using INSERT INTO with the information given by the user 
        if self.cursor.fetchone() == None:
            self.cursor.execute("INSERT INTO review (libraryID, reviewScore, reviewText) VALUES (?, ?, ?)", (self.libraryID, self.rating, self.text))
            self.db.commit()
        ##Returns True if a review already exists, so that a sufficient error can be loaded in the GUI
        else:
            self.reviewExists = True
        return self.reviewExists
    
    ##A grouping of sections of code from other load methods, but with unneeded fields removed from the SELECT statements in order to reduce
    ##execution time and the program's memory usage
    def loadHome(self):
        self.libraryIDs = []
        self.igdbIDs = []
        self.cursor.execute("SELECT userGame.libraryID, game.igdbID FROM userGame JOIN game ON userGame.gameID = game.gameID WHERE userGame.userID = ? ORDER BY userGame.libraryID DESC ", (self.userID,))
        self.db.commit()
        self.libraryData = self.cursor.fetchall()
        for x in range (0, len(self.libraryData)):
            self.libraryIDs.append(self.libraryData[x][0])
            self.igdbIDs.append(self.libraryData[x][1])
        
        self.reviewIDs = []
        self.scores = []
        self.texts = []
        self.names1 = []
        self.cursor.execute("SELECT review.reviewID, review.reviewScore, review.reviewText, game.name FROM review JOIN userGame, game ON review.libraryID = userGame.libraryID and userGame.gameID = game.gameID WHERE userGame.userID = ? ORDER BY review.reviewID DESC", (self.userID,))
        self.db.commit()
        self.reviewData = self.cursor.fetchall()
        for x in range (0, len(self.reviewData)):
            self.reviewIDs.append(self.reviewData[x][0])
            self.scores.append(self.reviewData[x][1])
            self.texts.append(self.reviewData[x][2])
            self.names1.append(self.reviewData[x][3])

        self.listIDs = []
        self.titles = []
        self.names2 = []
        self.cursor.execute("SELECT list.listID, list.listTitle, game.name FROM list JOIN listEntry, userGame, game ON list.listID = listEntry.listID and listEntry.libraryID = userGame.libraryID and userGame.gameID = game.gameID WHERE userGame.userID = ?", (self.userID,))
        self.db.commit()
        self.listData = self.cursor.fetchall()
        if self.listData != []:
            for x in range (0, len(self.listData)):
                    self.listIDs.append(self.listData[x][0])
                    self.titles.append(self.listData[x][1])
            self.listIDs = list(dict.fromkeys(self.listIDs))
            self.titles = list(dict.fromkeys(self.titles))
            for i in range (0, len(self.listIDs)):
                self.names2.append([])
                for x in range (0, len(self.listData)):
                    if self.listData[x][0] == self.listIDs[i]:
                        self.names2[i].append(self.listData[x][2])
        return (self.libraryIDs, self.igdbIDs, self.reviewIDs, self.scores, self.texts, self.names1, self.listIDs, self.titles, self.names2)

    ##Fetches information for each game linked to the specified userID, and parses them into seperate lists for specific referencing
    def loadUserGames(self, mode): ##Sort By mode passed in as a parameter
        self.mode = mode
        ##Defines lists for each field pertaining to the game
        self.libraryIDs = []
        self.igdbIDs = []
        self.names = []
        self.releaseDates = []
        ##Carries out relevant SELECT query based on the selected mode
        if self.mode == "default":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID WHERE userID = ?", (self.userID,))       
        elif self.mode == "Rating ↓":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID JOIN review ON review.libraryID = userGame.libraryID WHERE userID = ? ORDER BY review.reviewScore DESC", (self.userID,))
        elif self.mode == "Rating ↑":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID JOIN review ON review.libraryID = userGame.libraryID WHERE userID = ? ORDER BY review.reviewScore ASC", (self.userID,))
        elif self.mode == "Quick Rank ↓":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID WHERE userID = ? ORDER BY userGame.elo DESC", (self.userID,))
        elif self.mode == "Quick Rank ↑":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID WHERE userID = ? ORDER BY userGame.elo ASC", (self.userID,))
        elif self.mode == "A-Z":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID WHERE userID = ? ORDER BY game.name ASC", (self.userID,))
        elif self.mode == "Z-A":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID WHERE userID = ? ORDER BY game.name DESC", (self.userID,))
        elif self.mode == "Newest Release":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID WHERE userID = ? ORDER BY game.releaseDate DESC", (self.userID,))
        elif self.mode == "Oldest Release":
            self.cursor.execute("SELECT game.igdbID, userGame.libraryID, game.name, game.releaseDate FROM userGame JOIN game ON usergame.gameID = game.gameID WHERE userID = ? ORDER BY game.releaseDate ASC", (self.userID,))
        self.db.commit()
        self.gameData = self.cursor.fetchall()
        ##Iterates through the returned data (which is in the form of a list of tuples) and extracts each item so that 
        ##it can be appended to the relevant list, before each list is returned
        for x in range (0, len(self.gameData)):
            self.igdbIDs.append(self.gameData[x][0])
            self.libraryIDs.append(self.gameData[x][1])
            self.names.append(self.gameData[x][2])
            self.releaseDates.append(self.gameData[x][3])
        return self.igdbIDs, self.libraryIDs, self.names, self.releaseDates
    
    ##Requests the information for each of a user's reviews from the database, and parses the returned 2D list into 4 seperate lists
    def loadReviews(self):
        self.reviewIDs = []
        self.scores = []
        self.texts = []
        self.libraryIDs = []
        ##Executes a SELECT query to return necessary data, making use of a JOIN class to link it to userGame so that the correct userID is referenced
        ##Orders results by reviewID ASC so that they are displayed in order of when they are added, for user convenience
        self.cursor.execute("SELECT review.reviewID, review.reviewScore, review.reviewText, review.libraryID FROM review JOIN userGame ON review.libraryID = userGame.libraryID WHERE userGame.userID = ? ORDER BY review.reviewID ASC", (self.userID,))
        self.db.commit()
        self.temp = (self.cursor.fetchall())
        ##Iterates through the returned list of tuples, taking the data from each index of the tuple and appending it to the relevant list to be returned
        for x in range (0, len(self.temp)):
            if self.temp != []:
                self.reviewIDs.append(self.temp[x][0])
                self.scores.append(self.temp[x][1])
                self.texts.append(self.temp[x][2])
                self.libraryIDs.append(self.temp[x][3])
        return (self.reviewIDs, self.scores, self.texts, self.libraryIDs)
    
    ##Fetches information pertaining to each of a user's lists, as well as each entry in said lists, and returns them to be used in the program
    def loadLists(self):
        self.listIDs = []
        self.titles = []
        self.libraryIDs = []
        self.igdbIDs = []
        self.names = []
        self.entryIDs = []
        ##Executes a single SQL query to retrieve all list-related data across both tables that is linked to the current userID
        self.cursor.execute("SELECT list.listID, list.listTitle, listEntry.libraryID, game.igdbID, game.name, listEntry.entryID FROM list JOIN listEntry, userGame, game ON list.listID = listEntry.listID and listEntry.libraryID = userGame.libraryID and userGame.gameID = game.gameID WHERE userGame.userID = ?", (self.userID,))
        self.db.commit()
        self.temp = (self.cursor.fetchall())
        if self.temp != []: ##Prevents errors caused by a user with no lists
            ##Iteratively extracts just the listIDs and titles, and uses conversion to a dictionary from keys, and then back into a list in order to
            ##remove repeated data caused by the use of a JOIN clause
            for x in range (0, len(self.temp)):
                    self.listIDs.append(self.temp[x][0])
                    self.titles.append(self.temp[x][1])
            self.listIDs = list(dict.fromkeys(self.listIDs))
            self.titles = list(dict.fromkeys(self.titles))
            ##As in other methods, iterates through data returned by the database in the form of a 2D list, and parses the columns into their own lists
            for i in range (0, len(self.listIDs)):
                self.libraryIDs.append([])
                self.igdbIDs.append([])
                self.names.append([])
                self.entryIDs.append([])
                for x in range (0, len(self.temp)):
                    if self.temp[x][0] == self.listIDs[i]:
                        self.libraryIDs[i].append(self.temp[x][2])
                        self.igdbIDs[i].append(self.temp[x][3])
                        self.names[i].append(self.temp[x][4])
                        self.entryIDs[i].append(self.temp[x][5])
        return (self.listIDs, self.titles, self.libraryIDs, self.igdbIDs, self.names, self.entryIDs) ##Returns seperate lists of the fetched data
    
    ##Fetches and returns the string game name for a specified libraryID, based on the record from 'game' that it is linked to, before returning it
    def loadGameName(self, libraryID):
        self.libaryID = libraryID
        self.cursor.execute("SELECT game.name FROM userGame JOIN game ON userGame.gameID = game.gameID WHERE userGame.libraryID = ?", (self.libaryID,))
        self.db.commit()
        self.name = self.cursor.fetchone()[0]
        return self.name
    
    ##Removes every record using DELETE from the database that is linked to, or contains, the current userID
    ##Goes in order listEntry, list, review, userGame and account to maintain referential integrity
    def removeAcc(self):
        self.cursor.execute("DELETE FROM listEntry WHERE (SELECT userGame.libraryID FROM listEntry JOIN userGame ON listEntry.libraryID = userGame.libraryID) = ?", (self.userID,))
        self.db.commit()
        self.cursor.execute("DELETE FROM list WHERE list.listID NOT IN (SELECT list.listID FROM list JOIN listEntry ON list.listID = listEntry.listID)")
        self.db.commit()
        self.cursor.execute("DELETE FROM review WHERE review.libraryID IN (SELECT userGame.libraryID FROM userGame WHERE userGame.userID = ?)", (self.userID,))
        self.db.commit()
        self.cursor.execute("DELETE FROM userGame WHERE userID = ?", (self.userID,))
        self.db.commit()
        self.cursor.execute("DELETE FROM account WHERE userID = ?", (self.userID,))
        self.db.commit()

    ##Executes a DELETE query for the specified libraryID (PK) in userGame, which removes it from the user's account, and subsequently the GUI
    def removeUserGame(self, libraryID):
        self.libraryID = libraryID
        self.cursor.execute("DELETE FROM userGame WHERE libraryID = ?", (self.libraryID,))
        self.db.commit()

    ##Executes a DELETE query for the specified reviewID (PK) in review, which removes it from the user's account, and subsequently the GUI
    def removeReview(self, reviewID):
        self.reviewID = reviewID
        self.cursor.execute("DELETE FROM review WHERE reviewID = ?", (self.reviewID,))
        self.db.commit()
    
    ##First removes selected listEntry, as requested, before checking that the list that entry was contained is now empty, so that it can also be removed
    def removeListEntry(self, entryID):
        self.entryID = entryID
        self.cursor.execute("SELECT listID FROM listEntry WHERE entryID = ?", (self.entryID,)) ##Gets listID linked to the listEntry before it is removed
        self.db.commit()
        self.listID = self.cursor.fetchone()[0]
        self.cursor.execute("DELETE FROM listEntry WHERE entryID = ?", (self.entryID,)) ##Removes selected listEntry record
        self.db.commit()
        self.cursor.execute("SELECT entryID FROM listEntry WHERE listID = ?", (self.listID,)) ##Checks if there are any remaining entries under previously
                                                                                              ##fetched listID
        self.db.commit()
        self.listEntrys = self.cursor.fetchall()
        if self.listEntrys == []:
            self.cursor.execute ("DELETE FROM list WHERE listID = ?", (self.listID,)) ##Removes list record if it has no remaining entries
            self.db.commit()

    ##Removes each listEntry contained within the selected list, before removing the list itself
    def removeList(self, listID):
        self.listID = listID
        self.cursor.execute("DELETE FROM listEntry WHERE listID = ?", (self.listID,))
        self.db.commit()
        self.cursor.execute("DELETE FROM list WHERE listID = ?", (self.listID,))
        self.db.commit()

    ##Runs at the beginning of each new quick rank instance, resets each of the user's games to the baseline rating of 1000
    def startQR(self, libraryIDs):
        self.libraryIDs = libraryIDs
        ##Iterates through libraryIDs of the current user, make use of UPDATE statement to set the "elo" field to a float value of 1000
        for x in range (0, len(self.libraryIDs)):
            self.cursor.execute("UPDATE userGame SET elo = 1000 WHERE libraryID = ?", (self.libraryIDs[x],))
            self.db.commit()
    
    ##Performs necessary calculations based on whichever game wins (left or right) and updates ratings in the database accordingly
    def updateELO(self, leftGame, rightGame, leftWin): ##libraryID of left and right game passed in, as well as a boolean that indicates which game won
                                                       ##(i.e., left or not left/right)
        self.leftGame = leftGame
        self.rightGame = rightGame
        self.leftWin = leftWin
        ##Fetches current elo ratings of the left and right games that were just compared
        self.cursor.execute("SELECT elo FROM userGame WHERE libraryID = ?", (self.leftGame,))
        self.db.commit()
        self.leftElo = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT elo FROM userGame WHERE libraryID = ?", (self.rightGame,))
        self.db.commit()
        self.rightElo = self.cursor.fetchone()[0]

        ##Performs calculation to ascertain how many points the winner must "steal" from the loser, and updates the values in the database accordingly
        if self.leftWin == True:
            self.prob = 1.0/(1+math.pow(10, (self.rightElo-self.leftElo)/400)) ##Probability of left winning is calculated, based on the difference in
                                                                               ##points of either game before the current round of comparison
            ##Left game "steals" an amount of points from right equal to its probability of winning times 30
            self.leftElo = self.leftElo+30*(1-self.prob)
            self.rightElo = self.rightElo+30*(0-self.prob)
            ##UPDATE statements to provide new elo ratings for both games to the database, using libraryIDs of each so that the correct record is modified
            self.cursor.execute("UPDATE userGame SET elo = ? WHERE libraryID = ?", (self.leftElo, self.leftGame))
            self.db.commit()
            self.cursor.execute("UPDATE userGame SET elo = ? WHERE libraryID = ?", (self.rightElo, self.rightGame))
            self.db.commit()
        ##Identical to code above except games are switched around
        elif self.leftWin == False:
            self.prob = 1.0/(1+math.pow(10, (self.leftElo-self.rightElo)/400.0))
            self.rightElo = self.rightElo+30*(1-self.prob)
            self.leftElo = self.leftElo+30*(0-self.prob)
            self.cursor.execute("UPDATE userGame SET elo = ? WHERE libraryID = ?", (self.rightElo, self.rightGame))
            self.db.commit()
            self.cursor.execute("UPDATE userGame SET elo = ? WHERE libraryID = ?", (self.leftElo, self.leftGame))
            self.db.commit()

    ##Executes UPDATE query to find and replace the password field of the specified record
    def updatePassW(self, newPassword):
        self.newPassword = newPassword
        self.pepper = [54, 65, 120, 102, 80, 76, 106, 117]
        self.hash = hashlib.md5((self.newPassword+"".join([chr(i) for i in self.pepper])).encode())
        self.hashedPassword = self.hash.hexdigest()
        self.cursor.execute("UPDATE account SET password = ? WHERE userID = ?", (self.hashedPassword, self.userID))
        self.db.commit()

    ##Executes UPDATE query to find and replace the username field of the specified record
    def updateUserN(self, newUsername):
        self.newUsername = newUsername
        self.cursor.execute("UPDATE account SET username = ? WHERE userID = ?", (self.newUsername, self.userID))
        self.db.commit()