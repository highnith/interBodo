import requests
import db_operations
import json
from datetime import datetime, timedelta, timezone

db = db_operations.db_connection(
    dbname="InterBodo",
    user="postgres",
    password = "Gsmsnmms1250!",
    host="localhost"
)
def printJson(fileName, content):
    with open(fileName,"w") as f:
        json.dump(content,f, indent=4)

class API_football:
    def __init__(self, app_key):
        self.app_key = app_key

    def callAping(self,params,path):
        url = "https://v3.football.api-sports.io/"
        headers = {
            "x-apisports-key": self.app_key,
        }

        try:

            response = requests.get(
                f"{url}{path}",
                params=params,
                headers=headers
            )
            """
            if response:
                db.sendQueries([("UPDATE apiKeys SET remaining_requests = %s WHERE apiKey = %s",
                                (
                                    response.headers["x-ratelimit-requests-remaining"],
                                    self.app_key
                                ))])
            """

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print("Connection error:", e)
            return None
        
    def getLeagues(self):
        response = self.callAping({},"leagues")
        leagues = []
        if response:
            for league in response["response"]:
                leagues.append({
                    "leagueId":league["league"]["id"],
                    "leagueName":league["league"]["name"],
                    "leagueCountry":league["country"]["name"]
                })
        return leagues        
    
    def getFixtures(self,filter):
        response = self.callAping(filter,"fixtures")
        return response["response"]
    
    def create_fixtures(self,fixtures):
        fixtures_result = []
        if fixtures:
            open_date = datetime.fromisoformat(fixtures[0]["fixture"]["date"])
            day_after = open_date + timedelta(days=1)
            events = db.sendQueriesSelection([("SELECT * FROM events WHERE openDate > %s AND openDate < %s",
                    (
                        f"{open_date.year}-{open_date.month}-{open_date.day}",
                        f"{day_after.year}-{day_after.month}-{day_after.day}"
                    )
            )])

            if not events:
                print("There aren't events to link with fixtures in those dates")
                return -1

            for fixture in fixtures:
                for event in events[0]:
                    dt = event[4].strftime("%H:%M")
                    dt_fixture = datetime.fromisoformat(fixture["fixture"]["date"]).strftime("%H:%M")                                    
                    if dt == dt_fixture:
                        if  (event[2] == fixture["teams"]["home"]["name"] or event[3] == fixture["teams"]["away"]["name"]):
                            if fixture["fixture"]["status"]["short"] == "FT":
                                f = {
                                    "eventId" : event[1],
                                    "fixtureId" : fixture["fixture"]["id"],
                                    "home_goal_ft" : fixture["goals"]["home"],
                                    "away_goal_ft" : fixture["goals"]["away"],
                                    "home_goal_ht" : fixture["score"]["halftime"]["home"],
                                    "away_goal_ht" : fixture["score"]["halftime"]["away"]
                                }
                                fixtures_result.append(f)
                            break

        return fixtures_result


    
    