import sqlite3
import hashlib

class Auth():
    def __init__(self, username, password):
        super().__init__()

        ##Connects to the sqlite database file, establishes a cursor and defines class attributes from the passed in credentials
        self.db = sqlite3.connect('upupdowndown.db')
        self.cursor = self.db.cursor()
        self.username = username
        self.password = password

        self.pepper = [54, 65, 120, 102, 80, 76, 106, 117]
        self.hash = hashlib.md5((self.password+"".join([chr(i) for i in self.pepper])).encode())
        self.hashedPassword = self.hash.hexdigest()
    
    ##Fetches userID that corresponds to the username and password inputted in the GUI
    def getUserID(self):
        self.cursor.execute("SELECT userID FROM account WHERE username = ? AND password = ?", (self.username, self.hashedPassword))
        self.db.commit()
        fetchedID = self.cursor.fetchall()
        return fetchedID

    ##Returns True if a record is found containing both the username and password
    def checkAcc(self):
        self.cursor.execute("SELECT username, password FROM account WHERE username = ? AND password = ?", (self.username, self.hashedPassword))
        self.db.commit()
        fetchedAcc = str(self.cursor.fetchall())
        if (fetchedAcc) == ("[('"+self.username+"', '"+self.hashedPassword+"')]"):
            return True
        else:
            return False

    ##Returns True if the desired username is already taken
    def checkUserN(self):
        self.cursor.execute("SELECT username FROM account WHERE username = ?", (self.username,))
        self.db.commit()
        self.fetchedUserN = str(self.cursor.fetchall())
        if self.fetchedUserN == ("[('"+self.username+"',)]"):
            return True
        else:
            return False

    ##Creates a new record in the account table containing the inputted credentials
    def createAcc(self):
        self.cursor.execute("INSERT INTO account (username, password) VALUES (?, ?)", (self.username, self.hashedPassword))
        self.db.commit()