import requests
import json
import psycopg2 as pg2
from datetime import datetime

class TheOdds:   
    def __init__(self, leaguesKeys = [
            "soccer_italy_serie_a",
            "soccer_germany_bundesliga",
            "soccer_epl",
            "soccer_france_ligue_one",
            "soccer_austria_bundesliga",
            "soccer_argentina_primera_division",
            "soccer_brazil_campeonato",
            "soccer_australia_aleague",
            "soccer_italy_coppa_italia",
            "soccer_italy_serie_b",
            "soccer_netherlands_eredivisie",
            "soccer_portugal_primeira_liga",
            "soccer_saudi_arabia_pro_league",
            "soccer_spain_copa_del_rey",
            "soccer_spl",
            "soccer_sweden_allsvenskan",
            "soccer_switzerland_superleague",
            "soccer_turkey_super_league",
            "soccer_uefa_europa_conference_league",
            "soccer_usa_mls",
            "soccer_spain_segunda_division",
            "soccer_france_ligue_two",
            "soccer_germany_bundesliga2",
            "soccer_greece_super_league",
            "soccer_japan_j_league",
            "soccer_korea_kleague1",
            "soccer_mexico_ligamx"

        ]):
        self.api_url = "https://api.the-odds-api.com/v4/sports"
        self.preferredLeagues  =[]
        self.preferredLeagueKeys = leaguesKeys

    def getKeysRequests(self):
        conn = pg2.connect(
            dbname="InterBodo",
            user="postgres",
            password = "Gsmsnmms1250!",
            host="localhost"
        )
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT apiKey, requests_remaining FROM apiKeys;
            """
        )
        keys = cursor.fetchall();
        conn.commit()
        cursor.close()
        conn.close()

        return keys
        
    def retrieveKey(self):
        keys = self.getKeysRequests()
        requests_list = [];
        for key in keys:
            requests_list.append(key[1])
        return keys[requests_list.index(max(requests_list))]
    
    def getSportInfo(self):
        odds_api_key, odds_api_key_remaining_requests = self.retrieveKey()
        odds_params = {
            "apiKey" : odds_api_key,
        }
        #first api call to retrieve keys of the sports, returns a list of dicts 
        odds_sport_response = requests.get(f"{self.api_url}", odds_params)
        odds_sport_response_json = odds_sport_response.json()
        #with open("TheOdds_sport_list.json", "w", encoding="utf-8") as f:
        #   json.dump(odds_sport_response_json, f, indent=4)

        leagues_list = []
        for sport in odds_sport_response_json:
            leagues_list.append(
                {
                    "key" : sport["key"],
                    "sport" : sport["group"],
                    "title" : sport["title"],
                    "description" : sport["description"]         
                }
            )
        return leagues_list
        
    def selectLeagues(self,league_preferred = None):
        if league_preferred is None:
            league_preferred = self.preferredLeagues
        leagues_list = self.getSportInfo()
        #odds_sports = [v for v in leagues_list if any(kw in v["title"] for kw in league_preferred)]
        odds_sports = league_preferred
        #with open("odds_sports.json", "w", encoding="utf-8") as f:
        #    json.dump(odds_sports, f, indent=4)

        #retrieving keys from odds_sports
        leagues_keys = []
        for league in odds_sports:
            leagues_keys.append(league["key"])

        #Usage of keys directly
        leagues_keys = self.preferredLeagueKeys
        return leagues_keys
    
    def updateH2Hodds(self,*,chosen_bookmaker="betfair_ex_eu",request_params = {
            "regions" : "eu",
            "markets" : "h2h"
        }):
        odds_api_key, odds_api_key_remaining_requests = self.retrieveKey()   
        request_params["apiKey"] = odds_api_key
        leagues_list = self.selectLeagues()
        #call api to retrieve odds
        odds_response_list = []
        for league in leagues_list:
            odds_response = requests.get(f"{self.api_url}/{league}/odds/",request_params)
            odds_response_list.append(odds_response.json())
            remaining_request =  odds_response.headers.get("x-requests-remaining")
        #with open("odds.json", "w", encoding="utf-8") as f:
        #    json.dump(odds_response_list, f, indent=4)

        #selecting only on bookmaker
        event_list = []
        for league in odds_response_list:
            for event in league:
                quotes  = [0,0,0]
                for bookmaker in event["bookmakers"]:
                    commence_time = datetime.strptime(event["commence_time"],"%Y-%m-%dT%H:%M:%SZ")
                    last_update = datetime.strptime(bookmaker["last_update"],"%Y-%m-%dT%H:%M:%SZ")
                    if last_update < commence_time:
                        for quote in bookmaker["markets"][0]["outcomes"]:
                            if quote["name"] == event["home_team"]:
                                quotes[0] = quote["price"]
                            if quote["name"] == event["away_team"]:
                                quotes[1] = quote["price"]
                            if quote["name"] == "Draw":
                                quotes[2] = quote["price"]
                        if quotes != [0,0,0]:
                            event_ready  = {
                                "id": event["id"],
                                "sport_key": event["sport_key"],
                                "sport_title": event["sport_title"],
                                "commence_time": event["commence_time"],
                                "home_team": event["home_team"],
                                "away_team": event["away_team"],
                                "quote1" : quotes[0],
                                "quotex" : quotes[2],
                                "quote2" : quotes[1],
                                "bookmaker" : bookmaker["key"]
                            }
                            event_list.append(event_ready)
        #with open("odds_filtered.json", "w", encoding="utf-8") as f:
        #    json.dump(event_list, f, indent=4)

        #INSERTING EVENTS IN THE DATABASE
        conn = pg2.connect(
            dbname="InterBodo",
            user="postgres",
            password = "Gsmsnmms1250!",
            host="localhost"
        )
        cursor = conn.cursor()
        #Retrieving ids of leagues
        cursor.execute("SELECT name FROM leagues;")
        leagues_id_list = [name[0] for name in cursor.fetchall()]
        cursor.execute("SELECT name FROM bookmakers;")
        bookmakers_list = [name[0] for name in cursor.fetchall()]

        #code isn't optimized, each time try to insert the same event 
        for event in event_list:
            if event["sport_key"] in leagues_id_list:
                pass
            else:
                cursor.execute(
                    """
                    INSERT INTO leagues (name) VALUES (%s)
                    """,
                    (
                        event["sport_key"],
                    )
                )
                leagues_id_list.append(event["sport_key"])
            if event["bookmaker"] in bookmakers_list:
                pass
            else:
                cursor.execute(
                    """
                    INSERT INTO bookmakers (name) VALUES (%s)
                    """,
                    (
                        event["bookmaker"],
                    )
                )
                bookmakers_list.append(event["bookmaker"])
            cursor.execute(
                """
                INSERT INTO events (match_id,home_team,away_team,commence_time,league_name)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (match_id)
                DO NOTHING
                """,
                (
                    event["id"],
                    event["home_team"],
                    event["away_team"],
                    event["commence_time"],
                    event["sport_key"]
                )
            )
            cursor.execute(
                """
                INSERT INTO quotes (match_id,quote1,quote2,quotex,bookmaker)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (bookmaker,match_id)
                DO UPDATE SET
                    quote1 = EXCLUDED.quote1,
                    quotex = EXCLUDED.quotex,
                    quote2 = EXCLUDED.quote2;
                """,
                (
                    event["id"],
                    event["quote1"],
                    event["quote2"],
                    event["quotex"],
                    event["bookmaker"]
                )
            )
        cursor.execute(
            """
            UPDATE apiKeys SET requests_remaining = %s WHERE apiKey = %s;
            """,
            (
                remaining_request,
                odds_api_key
            )
        )
        conn.commit()
        cursor.close()
        conn.close()

    def updateResults(self,*,request_params = {
            "daysFrom": 3
        }):
        api_key, api_key_remaining_requests = self.retrieveKey()   
        request_params["apiKey"] = api_key
        leagues_list = self.selectLeagues()
        #call api to retrieve odds
        score_response_list = []
        for league in leagues_list:
            score_response = requests.get(f"{self.api_url}/{league}/scores/",request_params)
            score_response_list.append(score_response.json())
            remaining_request =  score_response.headers.get("x-requests-remaining")
        #with open("scores.json", "w", encoding="utf-8") as f:
        #    json.dump(score_response_list, f, indent=4)

        #INSERTING RESULTS IN THE DATABASE
        conn = pg2.connect(
            dbname="InterBodo",
            user="postgres",
            password = "Gsmsnmms1250!",
            host="localhost"
        )
        cursor = conn.cursor()
        
        for league in score_response_list:
            for score in league:
                if score["scores"] != None:
                    score_home_team  = score["scores"][0]["score"]
                    score_away_team = score["scores"][1]["score"]
                    if score_home_team > score_away_team:
                        finalScore = "1"
                    if score_away_team > score_home_team:
                        finalScore = "2"
                    if score_home_team == score_away_team:
                        finalScore = "x"

                    cursor.execute(
                        """
                        INSERT INTO results (match_id,score)
                        VALUES (%s,%s)
                        ON CONFLICT (match_id)
                        DO NOTHING
                        """,
                        (
                            score["id"],
                            finalScore
                        )
                    )
        cursor.execute(
            """
             UPDATE apiKeys SET requests_remaining = %s WHERE apiKey = %s;
             """,
              (
                  remaining_request,
                  api_key
              )
        )
        conn.commit()
        cursor.close()
        conn.close()
    

        
