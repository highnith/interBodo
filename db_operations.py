import psycopg2 as pg2

class db_connection:
    def __init__(self, dbname, user, password, host):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
    
    def sendQueries(self,queries):
        conn = pg2.connect(
            dbname=self.dbname,
            user=self.user,
            password = self.password,
            host=self.host
        )
        cursor = conn.cursor()
        response_list =[]
        for query in queries:
            cursor.execute(query[0],query[1])
        conn.commit()
        cursor.close()
        conn.close()
        return response_list
    def sendQueriesSelection(self,queries):
        conn = pg2.connect(
            dbname=self.dbname,
            user=self.user,
            password = self.password,
            host=self.host
        )
        cursor = conn.cursor()
        response_list =[]
        for query in queries:
            cursor.execute(query[0],query[1])
            result = cursor.fetchall()
            if result:
                 response_list.append(result)
        conn.commit()
        cursor.close()
        conn.close()
        return response_list

    def load_odds(self,marketOdds):
        queries = []
        for event in marketOdds:
            if event and event[0]["marketType"] != "WINNER": #winner of a league, I exclude it because it gives problems, may I'll implement it later
                elem = event[0]
                home, away = elem["eventName"].split(" v ")
                event_query = ("""INSERT INTO events (eventId,competitionId,home_team,away_team,openDate) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (
                            elem["eventId"],
                            elem["competitionId"],
                            home,
                            away,
                            elem["openDate"]
                        )     
                )
                queries.append(event_query)
                for market in event:
                    market_query = ("""INSERT INTO markets (marketId,marketType,marketName,eventId) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (
                            market["marketId"],
                            market["marketType"],
                            market["marketName"],
                            market["eventId"]
                        )     
                    )
                    queries.append(market_query)
                    for runner in market["runners"]:
                        if not runner["ex"]["availableToLay"]:
                            runner["ex"]["availableToLay"] = [{
                                "price" : 0,
                                "size" : 0
                            }]
                        runner_query = ("""INSERT INTO runners (selectionId,marketId,runnerName,handicap,back,lay,back_size,lay_size) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                            (
                                runner["selectionId"],
                                market["marketId"],
                                runner["runnerName"],
                                runner["handicap"],
                                runner["ex"]["availableToBack"][0]["price"],
                                runner["ex"]["availableToLay"][0]["price"],
                                runner["ex"]["availableToBack"][0]["size"],
                                runner["ex"]["availableToLay"][0]["size"]
                            )     
                        )
                        queries.append(runner_query)
        self.sendQueries(queries)

    def update_competitions(self,client):
        for comp in client.getCompetitions(1):
            query = ("""INSERT INTO competitions (competitionId,competitionName,competitionRegion) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""",
                    (
                        comp["competition"]["id"],
                        comp["competition"]["name"],
                        comp["competitionRegion"]
                    )
            )
            self.sendQueries([query])
    
    def pair_competition_league(self,competitionId,leagueId):
        self.sendQueries([
            (
                "UPDATE competitions SET leagueId = %s WHERE competitionId = %s",
                (
                    leagueId,
                    competitionId
                )
            )
        ])
    def loadFixtures(self, fixtures):
        queries = []
        for fixture in fixtures:
            query = (
                "INSERT INTO fixtures (fixtureId,eventId,home_goal_ft,away_goal_ft,home_goal_ht,away_goal_ht) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (
                    fixture["fixtureId"],
                    fixture["eventId"],
                    fixture["home_goal_ft"],
                    fixture["away_goal_ft"],
                    fixture["home_goal_ht"],
                    fixture["away_goal_ht"]
                )
            )
            print("ok")
            queries.append(query)
        self.sendQueries(queries)
