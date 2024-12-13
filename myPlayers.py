import requests
import json
import time
from datetime import datetime, timedelta
import locale
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import pyautogui
import platform
from addProjectionsParameters import getProj  # Import the function from app.py
import re
import copy

resultado_contender = []
resultado_champion = []

# def optimize_team(players, max_cap, isContender):
#     n = len(players)
#
#     def calculate_total_projection(subset):
#         return sum(player['projectionScore'] for player in subset)
#
#     memo = {}
#
#     def find_optimal_combination(index, remaining_cap, selected_count):
#         # Check if we have selected exactly 5 players
#         if index == n or remaining_cap < 0 or selected_count > 5:
#             return [] if selected_count != 5 else []
#
#         memo_key = f'{index}-{remaining_cap}-{selected_count}-{isContender}'
#         if memo_key in memo:
#             return memo[memo_key]
#
#         # Select the player with the highest projectionScore first if isContender is False
#         if not isContender and selected_count == 0:
#             contender_player = max(players, key=lambda x: x['projectionScore'])
#             remaining_cap_contender = remaining_cap - contender_player['actualCap']
#             if remaining_cap_contender >= 0:
#                 include_contender = [contender_player] + find_optimal_combination(index + 1, remaining_cap_contender, selected_count + 1)
#                 optimal_subset = max([[], include_contender], key=lambda x: calculate_total_projection(x))
#                 memo[memo_key] = optimal_subset
#                 return optimal_subset
#
#         # Exclude the current player
#         exclude_current = find_optimal_combination(index + 1, remaining_cap, selected_count)
#
#         # Include the current player if their actualCap does not exceed the limit
#         include_current = (
#             [players[index]] + find_optimal_combination(index + 1, remaining_cap - players[index]['actualCap'], selected_count + 1)
#         ) if remaining_cap >= players[index]['actualCap'] else []
#
#         # Compare and select the combination with the maximum sum of projectionScore
#         optimal_subset = max([exclude_current, include_current], key=lambda x: calculate_total_projection(x))
#
#         memo[memo_key] = optimal_subset
#         return optimal_subset
#
#     return find_optimal_combination(0, max_cap, 0)



def my_players(players_slug_myplayers):
    
    API_KEY = 'ec5de27c2402416037e6b5d9491728c2c0dc79907219f8204ef0574f9e700f90106d785c1f95c0f63042f2772fd16df47642ade7cea6db55ffea392f621sr128'

    headers = {
        'APIKEY': API_KEY  # Using only the API key as per Sorare's documentation
    }

    def get_player_data(slug, retry_count=0, max_retries=5):
        query = """
            query getPlayerData($slug: String!) {
                nbaPlayers(slugs: [$slug]) {
                    id
                    firstName
                    lastName
                    squaredPictureUrl
                    team {
                    fullName
                    svgUrl
                    }
                    upcomingGames(next:5){
                    gameWeek
                    }
                    isActive
                    playerInjury{
                    status
                    comment
                    }
                    tenGameAverageGameStats{
                    score
                    }
                    latestFixtureStats(last: 100) {
                    fixture{
                        gameWeek
                        fixtureState
                    }
                    status {
                        isScoreFinal
                        gameStats {
                        playedInGame
                        score
                        }
                    }
                    }
                }
            }
        """


        try:
            print(f"{datetime.now()} - Sending request for slug: {slug}")
            response = requests.post(
                'https://api.sorare.com/federation/graphql', 
                json={'query': query, 'variables': {'slug': slug}}, 
                headers=headers,
                timeout=2
            )

            if response.status_code == 429:
                if retry_count < 5:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"{datetime.now()} - Rate limit exceeded for slug {slug}. Waiting for {retry_after} seconds.")
                    time.sleep(retry_after)
                    return get_player_data(slug, retry_count+1)
                else:
                    print(f"Max retries reached for {slug}")
                    return None

            response.raise_for_status()
            print(f"{datetime.now()} - Data fetched successfully for slug {slug}")
            return response.json()
        
        except requests.exceptions.ReadTimeout:
            if retry_count < max_retries:
                print(f"{datetime.now()} - Timeout for slug {slug}. Retrying ({retry_count+1}/{max_retries})")
                return get_player_data(slug, retry_count + 1)
            else:
                print(f"{datetime.now()} - Max retries reached for slug {slug}")
                return None
            
        except requests.exceptions.HTTPError as err:
            print(f"{datetime.now()} - HTTP error occurred for slug {slug}: {err}")
            print(f"Response status: {response.status_code}, Response text: {response.text}")
            return None

    # Main process
    player_slugs = players_slug_myplayers
    all_player_data = []

    start_time = datetime.now()
    # Obtén la fecha actual
    fecha_actual = datetime.now()
    fecha_ayer = fecha_actual - timedelta(days=1)

    # Formatea la fecha como "dd/mm/aaaa" y comprueba que esté disponible
    fecha_formateada = fecha_actual.strftime("%d/%m/%Y %H:%M:%S")

    try:
        for index, slug in enumerate(player_slugs):
            print(f"{datetime.now()} - Fetching data for player {index+1}/{len(player_slugs)}: {slug}")
            try:
                data = get_player_data(slug)
                if data:
                    all_player_data.append(data)
                else:
                    print(f"{datetime.now()} - No data returned for slug {slug}")
            except Exception as inner_e:
                print(f"{datetime.now()} - Error fetching data for slug {slug}: {inner_e}")
            # time.sleep(1)  # To respect rate limits
    except Exception as e:
        print(f"{datetime.now()} - Unexpected error occurred: {e}")

    # Parsing the response data
    final_output_data = {}
    output_data = []
    
    # Load the JSON data from 'datos_jugadores_updated.json'
    with open('datos_jugadores_updated.json', 'r') as file:
        json_data = json.load(file)

    # Create a dictionary for quick access to player data by ID
    player_data_by_id = {player['id']: player for player in json_data['jugadores']}
    
    for player in all_player_data:
        player_info = player["data"]["nbaPlayers"][0]   
        player_id = player_info["id"]
        
        name = f"{player_info['firstName']} {player_info['lastName']}"
        
        # Retrieve data from loaded JSON using player_id
        player_json_data = player_data_by_id.get(player_id, {})
        floor_price = player_json_data.get("floorPrice", 0)
        three_days_avg_price = player_json_data.get("threeDaysAvgPrice", 0)
        projection_score = player_json_data.get("projectionScore", 0)
        projected_minutes = player_json_data.get("projectedMinutes", 0)
        minutes_difference = player_json_data.get("minutesDifference", 0)
        proj_ratio = player_json_data.get("projRatio", 0)
        final_ratio = player_json_data.get("finalRatio", 0)
        money_ratio = player_json_data.get("moneyRatio", 0)
        final_ratio_money = player_json_data.get("finalRatioMoney", 0)
        
        team = player_info.get("team")
        
        if team and team.get("fullName"):   
            team_name = player_info["team"]["fullName"]
            team_avatar_url = player_info["team"]["svgUrl"]
        else:
            team_name = "No"
            team_avatar_url = "No"
            
        avatar_url = player_info["squaredPictureUrl"]
        
        is_active = player_info["isActive"]
        
        injury_info = player_info.get("playerInjury")
        if injury_info and injury_info.get("status"):
            injury_status = injury_info["status"]
            injury_comment = injury_info.get("comment", "")
            is_injured = f"{injury_status}, {injury_comment}"
        else:
            is_injured = "No"
            
        actual_cap = int(player_info["tenGameAverageGameStats"]["score"])

        # Initialize an empty shortApp to store valid games
        valid_games = []
        is_gw_finished = None  # Initialize to None to indicate undetermined state
        game_counter = 0  # Counter to track the number of games processed

        # Iterate over each stat in latestFixtureStats
        for stat in player_info["latestFixtureStats"]:
            fixture_state = stat["fixture"]["fixtureState"]
            game_week = stat["fixture"]["gameWeek"]
            is_score_final = stat["status"]["isScoreFinal"]
            
            # Determine gameweek and GW finished status
            if fixture_state == "started":
                if is_gw_finished is None:  # Only set this the first time a "started" fixture is found
                    is_gw_finished = is_score_final
                gameweek = game_week
                games_on_next_gw = sum(1 for game in player_info["upcomingGames"] if game["gameWeek"] == (gameweek + 1))
                games_on_current_gw = sum(1 for game in player_info["upcomingGames"] if game["gameWeek"] == gameweek)
        
            
            # Process each gameStat
            for gameStat in stat["status"]["gameStats"]:
                if gameStat["playedInGame"]:
                    valid_games.append(gameStat["score"])
                if len(valid_games) == 10:
                    break  # Stop after finding 10 valid games

            if len(valid_games) == 10:
                break  # Stop after finding 10 valid games

        # If no "started" fixture was found, use the first "opened" fixture for gameweek
        if is_gw_finished is None:
            opened_fixture = next((x for x in player_info["latestFixtureStats"] if x["fixture"]["fixtureState"] == "opened"), None)
            gameweek = opened_fixture["fixture"]["gameWeek"] if opened_fixture else None
            is_gw_finished = True  # Set to True as no "started" fixture was found
            games_on_next_gw = sum(1 for game in player_info["upcomingGames"] if game["gameWeek"] == gameweek)
            games_on_current_gw = 0
        
            
        # Calculate future cap
        num_scores = len(valid_games)
        print(f"Scores for first 10 valid games of {name}: {valid_games}")
        future_cap = round(sum(valid_games) / num_scores) if num_scores > 0 else 0

        cap_ratio = round(actual_cap / future_cap, 3) if future_cap != 0 else 0

        print(f"Current GameWeek for {player_info['firstName']} {player_info['lastName']}: {gameweek}")
        
        # Algoritmo puntuaciones

        # Renderiza la plantilla con los datos del jugador seleccionado
            # Inicializar el diccionario de registroPuntos
        pointsRegister = {}
        array_strings = [chr(i) for i in range(ord('a'), ord('z')+1)] + [f"z{chr(i)}" for i in range(ord('a'), ord('z')+1)] + [f"{chr(i)}z{chr(j)}" for i in range(ord('a'), ord('z')+1) for j in range(ord('a'), ord('z')+1)] + [f"{chr(i)}{chr(j)}z{chr(k)}" for i in range(ord('a'), ord('z')+1) for j in range(ord('a'), ord('z')+1) for k in range(ord('a'), ord('z')+1)]
        array_strings.reverse()
            
        # Iterar sobre los elementos de registerTest
        contG = 0
        # Iterar sobre los elementos de registerTest
        for registro in player_info.get("latestFixtureStats", []):
            game_week = registro.get("fixture", {}).get("gameWeek")
            game_stats = registro.get("status", {}).get("gameStats", [])
            contG = contG + 1
            # Calcular el valor para registroPuntos
            if game_week is not None:
                cont = 5
                for stat in game_stats:
                    cont = cont - 1
                    scores = stat.get("score", 0)
                    pointsRegister[f"{array_strings[contG]}GW{game_week}.{cont}"] = scores

        output_data.append({
            "id": player_id,
            "name": name,
            "avatarUrl": avatar_url,
            "team": team_name,
            "teamAvatarUrl": team_avatar_url,
            "floorPrice": floor_price,
            "threeDaysAvgPrice": three_days_avg_price,
            "actualCap": actual_cap,
            "futureCap": future_cap,
            "differenceCap": future_cap - actual_cap,
            "projectionScore": projection_score,
            "projectedMinutes": projected_minutes,
            "minutesDifference": minutes_difference,
            "capRatio": cap_ratio,
            "projRatio": proj_ratio,
            "finalRatio": final_ratio,
            "moneyRatio": money_ratio,
            "finalRatioMoney": final_ratio_money,
            "gamesOnNextGW": games_on_next_gw,
            "isInjured": is_injured,
            "isActive": is_active,
            "isGwFinished": is_gw_finished,
            "gamesLeftOnCurrentGW": games_on_current_gw,
            "pointsRegister": pointsRegister
        })
        
        final_output_data = {"date" : fecha_formateada,
                            "jugadores" : output_data
                            }
    # Writing to a JSON file
    with open('datos_jugadores_my_players.json', 'w') as json_file:
        json.dump(final_output_data, json_file, indent=4)  # Added indentation for better JSON formatting

    end_time = datetime.now()
    execution_time = end_time - start_time
    print(f"Script execution time: {execution_time}")
    print(f"{datetime.now()} - Data written to datos_jugadores.json")


def get_access_token(client_id, client_secret, code, redirect_uri):
    url = "https://api.sorare.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

def get_my_limited_cards(access_token):
    url = "https://api.sorare.com/federation/graphql"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    query = """
        query {
            currentUser {
                nbaCards(rarities:limited) {
                    nodes {
                        player {
                         slug
                        }
                    }    
                }    
            }
        }
    """
    response = requests.post(url, json={"query": query}, headers=headers)

    return response.json()

def extract_player_slugs(limited_cards):
    player_slugs = []
    try:
        cards = limited_cards['data']['currentUser']['nbaCards']['nodes']
        for card in cards:
            player = card['player']
            slug = player['slug']
            player_slugs.append(slug)
    except KeyError as e:
        print(f"Error extracting player names: {e}")
    return player_slugs
