import os
import json
import requests 
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

LEAGUE_ID = os.getenv("LEAGUE_ID")
SWID = os.getenv("SWID")
ESPN_2 = os.getenv("ESPN_2")
YEAR=2023


def getData(option="viewLeagueTeams"):
  # Set up the base url and parameters needed to make any request for updating various datasets
  base_url = f"https://fantasy.espn.com/apis/v3/games/flb/seasons/{str(YEAR)}/segments/0/leagues/{str(LEAGUE_ID)}"
  paramOptions = {
  "viewLiveDraftTrends": "?view=kona_player_info",
  "viewLeagueTeams": "?view=mTeam",
  "viewSchedule": "?view=mMatchupScore",
  "viewRoster": "?view=mRoster",
  }
  cookies = {
    "swid": str(SWID),
    "espn_s2": str(ESPN_2)
  }

  match option: # type: ignore

    case "mlbTeams":
      r = requests.get(base_url + "?view=kona_player_info", cookies=cookies)
      data = r.json()
      teams = data['teams']
      result = []
      for team in teams:
        details = {
          "id": team['id'],
          "location": team['location'],
          "nickname": team['nickname'],
          "abbreviation": team['abbreviation']
        }
        result.append(details)
      with open("data/mlb-teams.json", "w") as outfile:
        json.dump(result, outfile)
      return "Updated mlb teams in data/mlb-teams.json"
    

    case "leagueOwners":
      r = requests.get(base_url + "?view=mTeam", cookies=cookies)
      data = r.json()
      teams = data['teams']
      result = []
      for team in teams:
        details = {
          "id": team['id'],
          "location": team['location'],
          "nickname": team['nickname'],
          "abbreviation": team['abbreviation'],
          "owner": team['owners'][0]['displayName']
        }
        result.append(details)
      with open("data/league-owners.json", "w") as outfile:
        json.dump(result, outfile)
      return "Updated league owners in data/league-owners.json"
    


    case "draftOrder":
      headers = {
        "x-fantasy-filter": json.dumps({
          "players": {
            "filterSlotIds": {
              "value": [
                0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19, 21, 22, 23
              ]
            },
            "limit": 500,
            "sortAdp": { "sortAsc": "true", "sortPriority": 1 },
            "sortDraftRanks": {
              "sortPriority": 100,
              "sortAsc": "true",
              "value": "STANDARD"
            },
            "filterRanksForScoringPeriodIds": { "value": [1] },
            "filterRanksForRankTypes": { "value": ["STANDARD"] },
            "filterStatsForTopScoringPeriodIds": {
              "value": 5,
              "additionalValue": [
                "102023"
              ]
            }
          }
        }),
        "x-fantasy-platform": "kona-PROD-a7efc944bb49ab8bac8a9fa8de3b5b8ecf42e618",
        "x-fantasy-source": "kona"
      }
      r = requests.get(base_url + paramOptions[option], cookies=cookies, headers=headers)
      data = r.json()

      result = []
      for player in data['players']:
        try:
          projPoints = next((stat for stat in player['player']['stats'] if stat['id'] == '102023'), 0)
              
          details = {
            "draftRank": player['player']['draftRanksByRankType']['STANDARD']['rank'],
            "eligibleSlots": player['player']['eligibleSlots'],
            "playerId": player['player']['id'],
            "name": player['player']['firstName'] + " " + player['player']['lastName'],
            "projPoints": projPoints['appliedTotal'] if projPoints else 0 #type: ignore
          }
          result.append(details)
        except:
          print("error with player", player)
          continue

      result = sorted(result, key=lambda k: k['draftRank'])
      df = pd.DataFrame(result)
      df.to_csv("data/player-draft-rankings.csv", index=False)

      return "Updated player draft rankings in data/player-draft-rankings.csv"
