import requests
import json
import json
from datetime import datetime
import sys
import requests
import json



class BetfairClient:

    class LoginError(Exception):
        pass

    def __init__(self, username, password, app_key,app_name,
                 cert_file="betfair_auth_files/client-2048.crt",
                 key_file="betfair_auth_files/client-2048.key"):

        self.username = username
        self.password = password
        self.app_key = app_key
        self.cert = (cert_file, key_file)
        self.app_name = app_name
        self.eventTypeDict = {
            "soccer" : 1,
            "tennis" : 2,
            "basketball" : 7522,
            "rugby" : 5
        }

        self.sessionToken = self.login()

    def login(self):

        url = "https://identitysso-cert.betfair.it/api/certlogin"

        headers = {
            "X-Application": self.app_name,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "username": self.username,
            "password": self.password
        }

        response = requests.post(
            url,
            headers=headers,
            data=data,
            cert=self.cert
        )

        if response.status_code == 200:
            res = response.json()
            self.sessionToken = res["sessionToken"]
            return self.sessionToken

        raise BetfairClient.LoginError(response.text)

    def callAping(self, jsonrpc_req):

        if not self.sessionToken:
            self.login()

        url = "https://api.betfair.com/exchange/betting/json-rpc/v1"

        headers = {
            "X-Application": self.app_key,
            "X-Authentication": self.sessionToken
        }

        try:

            response = requests.post(
                url,
                json=jsonrpc_req,
                headers=headers
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print("Connection error:", e)
            return None

    def getEventTypes(self):

        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listEventTypes",
            "params": {"filter": {}},
            "id": 1
        }

        response = self.callAping(req)

        if response and "result" in response:
            return response["result"]

        print("API error:", response)
        return None
    def getMarketTypes(self):

        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketTypes",
            "params": {"filter": {}},
            "id": 1
        }

        response = self.callAping(req)

        if response and "result" in response:
            return response["result"]

        print("API error:", response)
        return None

    def getEventTypeIDForEventTypeName(self, eventTypesResult, name):

        for event in eventTypesResult:
            if event["eventType"]["name"] == name:
                return event["eventType"]["id"]

        return None
    
    def getEventIds(self, eventTypeIDS = None, competitionIds = None):
        filter = { }
        if eventTypeIDS is not None:
            filter["eventTypeIds"] = eventTypeIDS
        if competitionIds is not None:
            filter["competitionIds"] = competitionIds
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listEvents",
            "params": {
                "filter": filter,
                "maxResults": "200"
            },
            "id": 1
        }

        response = self.callAping(req)

        if response and "result" in response:
            ids_list = []
            for event in response["result"]:
                ids_list.append(event["event"]["id"])
            return ids_list

        print("API error:", response)
        return None

    def getEvent(self, eventTypeIDS = None, competitionIds = None, eventIds = None):
        filter = { }
        if eventTypeIDS is not None:
            filter["eventTypeIds"] = eventTypeIDS
        if competitionIds is not None:
            filter["competitionIds"] = competitionIds
        if eventIds is not None:
            filter["eventIds"] = eventIds
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listEvents",
            "params": {
                "filter": filter,
                "maxResults": "200"
            },
            "id": 1
        }

        response = self.callAping(req)

        if response and "result" in response:
            return response

        print("API error:", response)
        return None

    def getCompetitions(self, eventTypeID):

        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listCompetitions",
            "params": {
                "filter": {"eventTypeIds": [str(eventTypeID)]},
                "maxResults": "50"
            },
            "id": 1
        }

        response = self.callAping(req)
        if response and "result" in response:
            return response["result"]

        print("API error:", response)
        return None

    def getMarketCatalogue(self, marketTypeCodes=None, eventTypeIDS = None, competitionIds = None, eventIds = None):
        filter = { }
        if eventTypeIDS is not None:
            filter["eventTypeIds"] = eventTypeIDS
        if competitionIds is not None:
            filter["competitionIds"] = competitionIds
        if eventIds is not None:
            filter["eventIds"] = eventIds
        if marketTypeCodes is not None:
            filter["marketTypeCodes"] = marketTypeCodes

        #markerProjection serve to rettrieve more data from the market as runner's names
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketCatalogue",
            "params": {
                "filter": filter,
                "marketProjection": [
                    "RUNNER_DESCRIPTION",
                    "MARKET_DESCRIPTION",
                    "COMPETITION",
                    "EVENT",
                    "MARKET_START_TIME",
                    "RUNNER_METADATA"
                ],
                "maxResults": "50"
            },
            "id": 1
        }

        response = self.callAping(req)
        if response and "result" in response:
            return response["result"]

        print("API error:", response)
        return None

    def getMarketBook(self, marketId):

        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listMarketBook",
            "params": {
                "marketIds": marketId,
                "priceProjection": {
                    "priceData": ["EX_BEST_OFFERS"]
                }
            },
            "id": 1
        }
        
        response = self.callAping(req)
        if response and "result" in response:
            return response["result"]

        print("API error:", response)
        return None

    def findGoodOdds(self, markets,price=9,size = 2):
        marketsIds = []
        for market in markets:
            marketsIds.append(market["marketId"])
        markets_odds = self.getMarketBook(marketsIds)
        #Sort to re allign array
        markets_odds.sort(key = lambda x: x["marketId"])
        markets.sort(key = lambda x: x["marketId"])
        interestingSelection = []
        for market,marketDetail in zip(markets_odds,markets):
            if market["marketId"] != marketDetail["marketId"]:
                print("FAIL")
            dt = datetime.strptime(marketDetail["event"]["openDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if dt < datetime.now():
                continue
            startDict = {
                            "eventId" : marketDetail["event"]["id"],
                            "eventName" : marketDetail["event"]["name"],
                            "openDate" :  marketDetail["event"]["openDate"],
                            "competitionId" : marketDetail["competition"]["id"],
                            "competitionName" : marketDetail["competition"]["name"],
                            "marketId" : marketDetail["marketId"],
                            "marketName" : marketDetail["marketName"],
                            "marketType" : marketDetail["description"]["marketType"],
                            "runners" : []
            }                  
            for runner,runnerDetail in zip(market["runners"],marketDetail["runners"]):
                if runner["ex"]["availableToBack"]:
                    SelectionPrice = runner["ex"]["availableToBack"][0]["price"]
                    if  (SelectionPrice > price) & (runner["ex"]["availableToBack"][0]["size"] > size):
                        runners_list = startDict["runners"]
                        runners_list.append({
                            "selectionId" : runner["selectionId"],
                            "runnerName" : runnerDetail["runnerName"],
                            "handicap" : runnerDetail["handicap"],
                            "status" : runner["status"],
                            "ex" : runner["ex"]
                        })
                        startDict["runners"] = runners_list
            if startDict["runners"]:
                interestingSelection.append(startDict)
                

        return interestingSelection

    def getRunner(self,selectionId,marketId):
        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/listRunnerBook",
            "params": {
                "marketId": marketId,
                "selectionId": selectionId
            },
            "id": 1
        }    
        response = self.callAping(req)
        if response and "result" in response:
            return response["result"]

        print("API error:", response)
        return None


    def genInstruction(self, selectionId, handicap, side, orderType, size, price, persistenceType):

        return {
            "selectionId": selectionId,
            "handicap": handicap,
            "side": side.upper(),
            "orderType": orderType.upper(),
            "limitOrder": {
                "size": size,
                "price": price,
                "persistenceType": persistenceType.upper()
            }
        }

    def placeOrder(self, marketId, instructions):

        req = {
            "jsonrpc": "2.0",
            "method": "SportsAPING/v1.0/placeOrders",
            "params": {
                "marketId": marketId,
                "instructions": instructions,
                "customerRef": "test123"
            },
            "id": 1
        }

        response = self.callAping(req)

        if response:
            print(response)

    def selectCompetitions(self, marketCount=None, names=None, countries=None,eventTypes=None):
        competitions = []
        if eventTypes is not None:
            for eventType in eventTypes:
                competitions.extend(self.getCompetitions(self.eventTypeDict[eventType]))
        else:
            for eventType in self.eventTypeDict.values():
                competitions.extend(self.getCompetitions(eventType))


        selectedComp = []
        for comp in competitions:
            if marketCount is not None and comp.get('marketCount') < marketCount:
                continue
            if names is not None and comp["competition"]["name"] not in names:
                continue
            if countries is not None and comp.get('competitionRegion') not in countries:
                continue

            selectedComp.append(comp)
        
        result_ids = []
        for comp in selectedComp:
            result_ids.append(comp["competition"]["id"])

        return result_ids
            


def printJson(fileName, content):
    with open(fileName,"w") as f:
        json.dump(content,f, indent=4)

