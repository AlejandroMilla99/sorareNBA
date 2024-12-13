from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
import re
import json

def getProj():

    # Manually provided list of complete player names and their corresponding IDs
    duplicated_players = {
        "Trae Young": "46990983393092353878222625928804297541449949761529274232261150725320970341727",
        "Thaddeus Young": "32412195530991841472146552481087436101194961872144875924393593465058669921989",
        "Donovan Mitchell": "57670796544802605102322925599546005830159332260133292591547938983514524105463",
        "Davion Mitchell": "76726632134997022870971563334280805602369559633096207693803476884784172401545",
        "Stephen Curry": "99475051630392079721863653030613771007650826225363916103059538741831983671199",
        "Seth Curry": "19013074455798567278820976664374691765431568916189545341022061774675717374546",
        "Bogdan Bogdanovic": "95844231647850895136596181296748397032545671085869965048636458784012058745830",
        "Bojan Bogdanovic": "5733757613515734312373775561633722174743825941211880849086981276337944344783",
        "Jimmy Butler": "66419300672259774809649738523201264524342385009630381974177679512105667129135",
        "Jared Butler": "55377218556237347819177219377189139250283156384613580392283630288533729278060",
        "John Butler": "109122312758380781842080605953688690379914273382166872087243524201961346830881",
        "Tyus Jones": "11582254304707765207827076959046187808751484211303170453620479469892110905291",
        "Tre Jones": "25864292691057501192229491016680810801668905626500119728872098929098008090298",
        "Miles Bridges": "73548312721675300612955992578655465028925226657729070723421901382389039149281",
        "Mikal Bridges": "2497122335508965988520031917749879590121373987356940295571790691984053362769",
        "Jabari Smith": "31929040938651554158939084991620724968459202032165626009415941083793602943416",
        "Jalen Smith": "47591888237385055789734603518982997063814031418541743030290304175005057055616",
        "Jrue Holiday": "91485148597602478025945244547837131973002798668542859430901457292684641007799",
        "Justin Holiday": "67488221544768240902339710806669481090763042887611468407151628246563911143930",
        "Jalen Williams": "79886068746921732851925426279956386731217354831885556267816989228623465378330",
        "Jaylin Williams": "28305341983201861936472101329629256690892072174287116450679316350850472277894",
        "Jalen Johnson": "1909199148710232620752878793896580386275926315139570229363995100432178993213",
        "James Johnson": "6616994259011614527506512387232827293714775556138447424256554480648575408358",
        "Keldon Johnson": "90655302154976740825342929691223304235518570555587757574492555809938770439156",
        "Keon Johnson": "115043231420946846847551853227663692619862309016386233822137698186866000883757",
        "Keyontae Johnson": "10733318265243970295220978044151429823994532827540081457735002887067497361222",
        "Caleb Martin": "16644744805056438165898291440429922531138160924506504439856546012537225205050",
        "Cody Martin": "1667966316385441077181834984640783737112694972307796778851110446911788949907",
        "Derrick Jones Jr.": "91997737985205430305482393187032741807579256998444059722240021762457818297330",
        "Damian Jones": "74526510856820751756027999036739410700079923070235039799641912112702350721848",
        "Monte Morris": "77930926378824442174861111753592415274793693051408955615607468463450586539127",
        "Marcus Morris": "63517159795235618393803260069630525811901184195921213212680905751177085703473",
        "Markieff Morris": "23681094718094307629846972230634147107364083717411981448234212882541779305250",
        "Jalen Green": "3200691611574265911474642507712666654845763220189253512875383656197110572254",
        "Josh Green": "12643381359641339963732299104679460820303332026428221979434144852244869651972",
        "Jeff Green": "72492106433381820203265522151145909536656989755124657278774273685811708313088",
        "Javonte Green": "10920215080371663868414014831519721792680411478539666901943801462007998524583",
        "JaMychal Green": "107725710615928343799956324574256978175516197895113329397291093470223047492558",
        "Draymond Green": "48425058756958616982936129698984672142234072030947113477845464020670284413493",
        "Danny Green": "101450531954091086965825487506818549421947700899705551880940687654536906714101",
        "Jaden McDaniels": "114448767915312808090529507208091328962606043387818152864552784804790195855678",
        "Jalen McDaniels": "33794419511886174416581013531606708776918771052093677030385537315503137402232",
        "Andrew Wiggins": "6216044674904641568340303812066276751108806187613436768974930144188804209511",
        "Aaron Wiggins": "19043744380735818373732040932134373078810576478299680542946036906264940999453",
        "Dennis Smith": "25218841305228312932478607833112511350383513717875566459813929235420706384270",
        "Dru Smith": "24831464636871022446362626472619932761223981052157521396444213182474953450529",
        "Ausar Thompson": "73574027624153530684087317213122173838929178019804286983284340829496532868752",
        "Amen Thompson": "6772030284339517098149728521267080678854562959412975096982018362141840370082",
        "Jabari Walker": "102156695566496431077565572824618508768357600572302721869929955503857987551401",
        "Jarace Walker": "103507397278015319924379734539551429079200836131783565886889905385463505046699",
        "Terance Mann": "71907612923743417984420702241313318865449005463346279391213894885892498849842",
        "Tre Mann": "5869213702656604047412469267910030454103198779766733282846237228547769600669",
        "Julian Champagnie": "32616586857713281799560101870521366167332800787497553819957303410037783885673",
        "Justin Champagnie": "59556049470596996912118848923566503795141023802895221077940741383327150937318",
        "Kobe Brown": "107459435110109464050112750380723139539169205065754921074794078272736298137157",
        "Kendall Brown": "28536928900718039506574810824510522283843975480808065032964836749485175752745",
        "Keegan Murray": "83777345237050021179258463144085155527355407133408813198378040979448098879861",
        "Kris Murray": "0000",
        "Lamelo Ball": "21800055025832721795375450887746150427952614630859086537034791003018754281493",
        "Lonzo Ball": "1111"
    }

    # Load the JSON file
    with open('datos_jugadores.json', 'r') as json_file:
        datos_jugadores = json.load(json_file)
        
    # Access the list of players from the "jugadores" key
    players_list = datos_jugadores.get("jugadores", [])

    def get_eth_to_eur_rate():
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=eur"
        response = requests.get(url)
        data = response.json()
        return data["ethereum"]["eur"]

    def convert_eth_to_eur(eth_amount, rate):
        return eth_amount * rate

    def parse_eth_amount(eth_string):
        # Extract the numeric part from the string
        match = re.search(r'(\d+,\d+|\d+\.?\d*) Ξ', eth_string)
        if match:
            return float(match.group(1).replace(',', '.'))
        return 0.0


    # Setup Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # Connect to the existing Chrome session
    driver = webdriver.Chrome(options=chrome_options)

    # Find the table containing the players and projections
    table_xpath = "//*[@id='table_scroll']/div/div[1]/div/table/tbody"
    print("Locating the table...")
    table = driver.find_element(By.XPATH, table_xpath)

    # Scroll to the end of the table to load all rows
    print("Scrolling through the table to load all rows...")
    scroll_pause_time = 3
    last_row = None

    while True:
        # Scroll down within the table
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", table)
        time.sleep(scroll_pause_time)

        # Check if new rows are loaded by comparing the last row
        new_last_row = table.find_elements(By.TAG_NAME, "tr")[-1]
        if new_last_row == last_row:
            print("Reached the end of the table.")
            break
        last_row = new_last_row

    # Re-identify the table to update its state
    table = driver.find_element(By.XPATH, table_xpath)

    # Initialize an empty dictionary to store player projections and a counter
    player_projections = {}
    extracted_count = 0

    # Get the current exchange rate
    eth_to_eur_rate = get_eth_to_eur_rate()

    print("Extracting data from each row...")
    for index, row in enumerate(table.find_elements(By.TAG_NAME, "tr")):
        print(f"Processing row {index + 1}...")
        try:
            player_name = row.find_element(By.XPATH, ".//td[2]/div/div/div[1]/div[1]/a/p").text
            player_link = row.find_element(By.XPATH, ".//td[2]/div/div/div[1]/div[1]/a").get_attribute('href')
            player_id = re.search(r'/player/(\d+)', player_link).group(1)
            gm_proj_value = row.find_element(By.XPATH, ".//td[5]//div//div//div//p").text
            floor_price = row.find_element(By.XPATH, ".//td[2]//div//div//div[2]//div[2]//div//p").text
            three_days_average_price = row.find_element(By.XPATH, ".//td[2]//div//div//div[2]//div[1]//div//p").text
            projected_minutes = row.find_element(By.XPATH, ".//td[14]//div//div//div[2]//p").text
            minutes_difference = row.find_element(By.XPATH, ".//td[15]//div//div//p").text

            # Extract and convert the ETH values
            floor_price_eth = parse_eth_amount(floor_price)
            three_days_avg_price_eth = parse_eth_amount(three_days_average_price)

            # Convert to EUR
            floor_price_eur = convert_eth_to_eur(floor_price_eth, eth_to_eur_rate)
            three_days_avg_price_eur = convert_eth_to_eur(three_days_avg_price_eth, eth_to_eur_rate)
            
            # Convert to integer if possible, else default to 0
            gm_proj_value_int = int(gm_proj_value) if gm_proj_value.isdigit() else 0
            projected_minutes_int = int(projected_minutes.replace("'", "")) if projected_minutes.replace("'", "").isdigit() else 0
            minutes_difference_int = int(minutes_difference) if minutes_difference.isdigit() else 0

            player_projections[player_id] = {
                "Player Name": player_name,
                "Projection Score": gm_proj_value_int,
                "Floor Price (EUR)": floor_price_eur,
                "3-Day Avg. Price (EUR)": three_days_avg_price_eur,
                "Projected Minutes": projected_minutes_int,
                "Minutes Difference": minutes_difference_int
            }
            extracted_count += 1
            print(f"Extracted: {player_name} - {gm_proj_value}, {player_id}, {floor_price}, {three_days_average_price}, {projected_minutes}, {minutes_difference}")
        except Exception as e:
            print(f"Error processing row {index + 1}: {e}")

    # Print the player projections and count
    print(f"Total players extracted: {extracted_count}")
    print("Player projections and additional details:")
    for player, details in player_projections.items():
        print(f"{player}: {details}")

    driver.quit()

    # Function to match player names and handle duplicates
    def match_player_names(json_name, script_id, script_name):
        if json_name in duplicated_players:
            # For duplicated names, match using the ID
            return duplicated_players[json_name] == script_id
        else:
            # Standard name matching for non-duplicated names
            script_first_name, script_last_name = script_name.split('.')
            json_first_name, json_last_name = json_name.split(' ')
            return script_first_name.lower() == json_first_name[0].lower() and script_last_name.lower() == json_last_name.lower()

    # Update the JSON data with new attributes
    for player in players_list:
        json_player_name = player.get("name", "")
        for script_player_id, script_player_data in player_projections.items():
            if match_player_names(json_player_name, script_player_id, script_player_data["Player Name"]):
                
                projection_score = script_player_data["Projection Score"]
                actual_cap = player.get("actualCap", 0)
                floor_price = script_player_data.get("Floor Price (EUR)", -1)  # Avoid division by zero
                cap_ratio = player.get("capRatio", 0)
                
                player["projectionScore"] = projection_score
                player["floorPrice"] = round(floor_price, 2)
                player["threeDaysAvgPrice"] = round(script_player_data["3-Day Avg. Price (EUR)"], 2)
                player["projectedMinutes"] = script_player_data["Projected Minutes"]
                player["minutesDifference"] = script_player_data["Minutes Difference"]
                
                player["projRatio"] = round(float(projection_score) / actual_cap, 2) if actual_cap else 0
                player["finalRatio"] = round((cap_ratio * 2) + (player["projRatio"] * 1.5), 2)
                player["moneyRatio"] = round(float(projection_score) / floor_price, 2) if floor_price else 0
                player["finalRatioMoney"] = round(player["finalRatio"] + (0.5 * player["moneyRatio"]), 2)
                
    # Save the updated data back to the JSON file
    with open('datos_jugadores_updated.json', 'w') as json_file:
        json.dump(datos_jugadores, json_file, indent=4)

    print("Updated data saved to datos_jugadores_updated.json")