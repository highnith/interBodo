import betfairAPI
import db_operations
import API_football
from datetime import datetime, timedelta
import json

def printJson(fileName, content):
    with open(fileName,"w") as f:
        json.dump(content,f, indent=4)

betfairClient = betfairAPI.BetfairClient(
    username="giorgiosisti12@gmail.com",
    password="Gsmsnmms1250!",
    app_key="H0Um0XPdSjDLu1T6",
    app_name="InterBodo"
)

api_footballClient = API_football.API_football(
    "9e0e825f6a094061904a7c1a2fa68ba9"
)

db = db_operations.db_connection(
    dbname="InterBodo",
    user="postgres",
    password = "Gsmsnmms1250!",
    host="localhost"
)

interestingMarkets = [
    "WINNER",
    "OVER_UNDER_05",
    "OVER_UNDER_65",
    "OVER_UNDER_55",
    #"CORRECT_SCORE",
    "OVER_UNDER_45",
    "FIRST_HALF_GOALS_25",
    "TO_QUALIFY",
    "TEAM_A_1",
    "TEAM_B_1",
    "OVER_UNDER_75",
    "MATCH_ODDS",
    "HALF_TIME",
    "WINNER",
    "HALF_TIME_SCORE",
    "HALF_TIME_FULL_TIME",
    "DOUBLE_CHANCE"
]
competitions = [
    "Italian Serie A",
    "Italian Serie B",
    "Italian Coppa Italia"
]


def findOdds(interestingMarkets=interestingMarkets,competitions = competitions):
    
    #getEventIds ACCEPTED_ARGUMENT=([eventTypeIDS], [competitionIds])
    #selectCompetitions ACCEPTED_ARGUMENT=(marketCount, names: [competitionNames], countries: [countries es ITA], eventType : [eventTypes])
    chosen_events_ids = betfairClient.getEventIds(competitionIds=betfairClient.selectCompetitions(names=competitions))
    market_opp = []

    for event_id in chosen_events_ids:

        #marketTypeCodes serve as a filter for getMarketCatalogue
        market_selection = betfairClient.getMarketCatalogue(marketTypeCodes=interestingMarkets,eventIds=[event_id])

        #findGoodOdds ACCEPTED_ARGUMENT=(price : the minimum price for the selections, size  : the minimum size for the selections
        market_odds = betfairClient.findGoodOdds(market_selection)
        market_opp.append(market_odds)
    
    return market_opp


def updateFixtures():
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    
    today_raw_fixtures = api_footballClient.getFixtures(
        {
            "date" : today_str
        }
    )
    today_fixtures = api_footballClient.create_fixtures(today_raw_fixtures)
    if today_fixtures == -1:
        return -1
    db.loadFixtures(today_fixtures)

    yesterday_raw_fixtures = api_footballClient.getFixtures(
        {
            "date" : yesterday_str
        }
    )
    yesterday_fixtures = api_footballClient.create_fixtures(yesterday_raw_fixtures)
    db.loadFixtures(yesterday_fixtures)
    return "SUCCESS"


db.load_odds(findOdds())
updateFixtures()







