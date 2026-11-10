import requests
from datetime import datetime

class Query():
    def __init__(self):
        super().__init__()

    def cover(self, gameID): ##IGDB gameID passed in as a parameter
        self.gameID = str(gameID)
        ##All gameIDs and imageIDs linked to specified gameID are requested from the IGDB
        self.coverResponse = (requests.post('https://api.igdb.com/v4/covers', 
                                            **{'headers': 
                                               {'Client-ID': 'j6uq2tdmclc6yqhmy9pyzkxmmiagai', 
                                                'Authorization': 'Bearer u1ly6f68082kvg2s4xqc8d78j62obp'},
                                                'data': 'fields game, image_id; where game = '+self.gameID+';'})).json()
        self.coverIDs = []
        self.coverURLs = []
        ##Returned json is iterated through and parsed into two arrays, one for each field
        for each in self.coverResponse:
            temp1 = each["game"]
            ##Image URL is created in 1080p using imageID
            temp2 = "https://images.igdb.com/igdb/image/upload/t_1080p/"+str(each["image_id"])+".jpg"
            self.coverIDs.append(temp1)
            self.coverURLs.append(temp2)

    def game(self, searchedGame): ##Game name inputted by the user is passed in as a parameter
        self.searchedGame = searchedGame
        ##All gameIDs, game names and release dates similar to the inputted string are requested from the IGDB
        self.gameResponse = (requests.post('https://api.igdb.com/v4/games', 
                                           **{'headers': 
                                              {'Client-ID': 'j6uq2tdmclc6yqhmy9pyzkxmmiagai', 
                                               'Authorization': 'Bearer wdth1x317eebcljhds08iqk7092mex'},
                                               'data': 'search "'+self.searchedGame+'"; fields id, name, first_release_date;'})).json()
        self.resultIDs = []
        self.resultNames = []
        self.resultReleases = []
        print (self.gameResponse)
        ##Returned json is iterated through and parsed into three arrays, one for each field
        for each in self.gameResponse:
            temp1 = each["id"]
            temp2 = str(each["name"])
            ##Errors caused by null values are avoided using try and except
            try:
                temp3 = datetime.fromtimestamp(each["first_release_date"])
            except KeyError:
                temp3 = None
            self.resultIDs.append(temp1)
            self.resultNames.append(temp2)
            self.resultReleases.append(temp3)