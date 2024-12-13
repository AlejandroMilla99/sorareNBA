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
import itertools
from addProjectionsParameters import getProj  # Import the function from app.py
import re
import copy

resultado_contender = []
resultado_champion = []

def optimize_team(players, max_cap, isContender):
    n = len(players)

    def calculate_total_projection(subset):
        return sum(player['projectionScore'] for player in subset)

    memo = {}

    def find_optimal_combination(index, remaining_cap, selected_count, excluded_player=None):
        if index == n or remaining_cap == 0 or selected_count == 5:
            return []

        memo_key = f'{index}-{remaining_cap}-{selected_count}-{isContender}-{excluded_player}'
        if memo_key in memo:
            return memo[memo_key]

        # Seleccionar al jugador con mayor projectionScore si isContender es False
        if not isContender and selected_count == 0:
            highest_projection_player = max(players, key=lambda x: x['projectionScore'])
            excluded_player = highest_projection_player

            # Ajustar remaining_cap para no considerar el actualCap del jugador seleccionado
            remaining_cap -= excluded_player['actualCap']

        # Excluir al jugador actual
        exclude_current = find_optimal_combination(index + 1, remaining_cap, selected_count, excluded_player)

        # Incluir al jugador actual si su actualCap no excede el límite y no es el jugador excluido
        include_current = []
        if remaining_cap >= players[index]['actualCap'] and players[index] != excluded_player:
            include_current = [players[index]] + find_optimal_combination(index + 1, remaining_cap - players[index]['actualCap'], selected_count + 1, excluded_player)

        # Comparar y seleccionar la combinación con la máxima suma de projectionScore
        optimal_subset = max([exclude_current, include_current], key=lambda x: calculate_total_projection(x))

        memo[memo_key] = optimal_subset
        return optimal_subset

    # Iniciar la búsqueda de la combinación óptima
    if isContender:
        return find_optimal_combination(0, max_cap, 0)
    else:
        # Añadir al jugador con la mayor projectionScore y buscar los siguientes 4 mejores
        highest_projection_player = max(players, key=lambda x: x['projectionScore'])
        return [highest_projection_player] + find_optimal_combination(0, max_cap, 1, highest_projection_player)

def optimize_both_teams(players, max_cap_contender, max_cap_non_contender):
    # Function to calculate the total projection score of a subset of players
    def calculate_total_projection(subset):
        return sum(player['projectionScore'] for player in subset)

    # Function to check if a subset of players is valid for a contender team
    def is_valid_contender(subset):
        return sum(player['actualCap'] for player in subset) <= max_cap_contender

    # Function to check if a subset of players is valid for a non-contender team
    def is_valid_non_contender(subset):
        mvp_projection = subset[0]['projectionScore']
        return sum(player['actualCap'] for player in subset[1:]) <= max_cap_non_contender

    # Generate all combinations of 5 players from the list
    all_combinations = itertools.combinations(players, 5)
    
    best_combination = None
    best_score = -1

    # Iterate over each combination for contender and non-contender teams
    for contender_team in all_combinations:
        if is_valid_contender(contender_team):
            remaining_players = [p for p in players if p not in contender_team]
            non_contender_teams = itertools.combinations(remaining_players, 5)
            for non_contender_team in non_contender_teams:
                if is_valid_non_contender(non_contender_team):
                    combined_score = calculate_total_projection(contender_team) + calculate_total_projection(non_contender_team)
    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_combination = (contender_team, non_contender_team)

                        return best_combination





def run_chrome_window():
    itsGeorge = True

    API_KEY = 'ec5de27c2402416037e6b5d9491728c2c0dc79907219f8204ef0574f9e700f90106d785c1f95c0f63042f2772fd16df47642ade7cea6db55ffea392f621sr128'

    headers = {
        'APIKEY': API_KEY  # Using only the API key as per Sorare's documentation
    }

    def obtener_identificador_unico():
        sistema_operativo = platform.system()
        nombre_nodo = platform.node()
        
        identificador_unico = f"{sistema_operativo}_{nombre_nodo}"
        
        return identificador_unico


    def reverseFormatMiles(cadena):
        print(float(cadena.replace(".", "").replace(",", ".")))
        return float(cadena.replace(".", "").replace(",", "."))

    def reverseFormatDecimal(cadena):
        # Establecer la configuración regional para español
        locale.setlocale(locale.LC_ALL, 'es_ES.utf-8')

        # Reemplazar el punto decimal por la coma
        cadena_con_coma = cadena.replace(".", ",")

        # Intentar convertir la cadena formateada a un número
        try:
            numero = locale.atof(cadena_con_coma)
            return numero
        except ValueError:
            # En caso de error, devolver None o lanzar una excepción según sea necesario
            return None

    def formatMiles(numero):
        return "{:,}".format(numero).replace(",", ".")

    def formatDecimal(numero):
        # Establecer la configuración regional para español
        locale.setlocale(locale.LC_ALL, 'es_ES.utf-8')
        # Formatear el número como cadena con el formato local
        numero_formateado = locale.format_string("%.2f", numero)
        return numero_formateado

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
    player_slugs = ["onyeka-okongwu-20001211", "bruno-fernando-19980815", "mouhamed-gueye-20021109", "clint-capela-19940518", "patty-mills-19880811", "jalen-johnson-20011218", "aj-griffin-20030825", "dejounte-murray-19960919", "miles-norris-20000415", "seth-lundy-20000402", "wesley-matthews-19861014", "garrison-mathews-19961024", "trae-young-19980919", "deandre-hunter-19971202", "bogdan-bogdanovic-19920818", "saddiq-bey-19990409", "kobe-bufkin-20030921", "trent-forrest-19980612", "nathan-knight-19970920", "jd-davison-20021003", "derrick-white-19940702", "jaylen-brown-19961024", "payton-pritchard-19980128", "jordan-walsh-20040303", "neemias-queta-19990713", "al-horford-19860603", "svi-mykhailiuk-19970610", "sam-hauser-19971208", "luke-kornet-19950715", "drew-peterson-19991109", "lamar-stevens-19970709", "dalano-banton-19991107", "jayson-tatum-19980303", "jrue-holiday-19900612", "kristaps-porzingis-19950802", "oshae-brissett-19980620", "harry-giles-iii-19980422", "armoni-brooks-19980605", "cameron-johnson-19960303", "dayron-sharpe-20011106", "spencer-dinwiddie-19930406", "nic-claxton-19990417", "cam-thomas-20011013", "noah-clowney-20040714", "keon-johnson-20020310", "royce-oneale-19930605", "lonnie-walker-iv-19981214", "dariq-whitehead-20040801", "dorian-finney-smith-19930504", "mikal-bridges-19960830", "ben-simmons-19960720", "jalen-wilson-20001104", "trendon-watford-20001109", "dennis-smith-jr-19971125", "lamelo-ball-20010822", "nick-richards-19971129", "nathan-mensah-19980409", "bryce-mcgowens-20021108", "jt-thor-20020826", "ish-smith-19880705", "brandon-miller-20021122", "leaky-black-19990614", "mark-williams-20011216", "miles-bridges-19980321", "nick-smith-jr-20040418", "amari-bailey-20040217", "cody-martin-19950928", "terry-rozier-19940317", "james-bouknight-20000918", "gordon-hayward-19900323", "p-j-washington-19980823", "frank-ntilikina-19980728", "nikola-vucevic-19901024", "terry-taylor-19990923", "torrey-craig-19901219", "zach-lavine-19950310", "andre-drummond-19930810", "henri-drell-20000425", "demar-derozan-19890807", "alex-caruso-19940228", "coby-white-20000216", "adama-sanogo-20020212", "patrick-williams-20010826", "lonzo-ball-19971027", "dalen-terry-20020712", "jevon-carter-19950914", "julian-phillips-20031105", "onuralp-bitim-19990331", "ayo-dosunmu-20000117", "damian-jones-19950630", "georges-niang-19930617", "caris-levert-19940825", "dean-wade-19961120", "max-strus-19960328", "donovan-mitchell-19960907", "emoni-bates-20040128", "jarrett-allen-19980421", "isaac-okoro-20010126", "evan-mobley-20010618", "tristan-thompson-19910313", "craig-porter-jr-20000226", "ty-jerome-19970708", "sam-merrill-19960515", "ricky-rubio-19901021", "isaiah-mobley-19990924", "darius-garland-20000126", "olivier-maxence-prosper-20020703", "jaden-hardy-20030705", "josh-green-20001116", "dwight-powell-19910720", "seth-curry-19900823", "a-j-lawson-20000715", "dexter-dennis-19990209", "luka-doncic-19990228", "grant-williams-19981130", "kyrie-irving-19920323", "dante-exum-19950713", "richaun-holmes-19931015", "dereck-lively-ii-20040212", "tim-hardaway-jr-19920316", "markieff-morris-19890902", "greg-brown-iii-20010901", "maxi-kleber-19920129", "derrick-jones-jr-19970215", "deandre-jordan-19880721", "aaron-gordon-19950916", "jamal-murray-19970223", "vlatko-cancar-19970410", "kentavious-caldwell-pope-19930218", "nikola-jokic-19950219", "christian-braun-20010417", "julian-strawther-20020418", "peyton-watson-20020911", "jalen-pickett-19991022", "collin-gillespie-19990625", "justin-holiday-19890405", "braxton-key-19970214", "reggie-jackson-19900416", "zeke-nnaji-20010109", "hunter-tyson-20000613", "michael-porter-jr-19980629", "jay-huff-19970825", "jared-rhoden-19990827", "monte-morris-19950627", "cade-cunningham-20010925", "isaiah-livers-19980728", "bojan-bogdanovic-19890418", "james-wiseman-20010331", "isaiah-stewart-20010522", "joe-harris-19910906", "alec-burks-19910720", "jalen-duren-20031118", "stanley-umude-19990412", "ausar-thompson-20030130", "marcus-sasser-20000921", "killian-hayes-20010727", "malcolm-cazalon-20010827", "jaden-ivey-20020213", "marvin-bagley-iii-19990314", "kevin-knox-ii-19990811", "gary-payton-ii-19921201", "draymond-green-19900304", "cory-joseph-19910820", "jonathan-kuminga-20021006", "stephen-curry-19880314", "gui-santos-20020622", "moses-moody-20020531", "dario-saric-19940408", "kevon-looney-19960206", "trayce-jackson-davis-20000222", "lester-quinones-20001116", "klay-thompson-19900208", "usman-garuba-20020309", "jerome-robinson-19970222", "andrew-wiggins-19950223", "brandin-podziemski-20030225", "chris-paul-19850506", "jock-landale-19951025", "jaesean-tate-19951028", "nate-hinton-19990608", "alperen-sengun-20020725", "jermaine-samuels-jr-19981113", "amen-thompson-20030130", "jeenathan-williams-19990212", "boban-marjanovic-19880815", "reggie-bullock-19910316", "cam-whitmore-20040708", "dillon-brooks-19960122", "aaron-holiday-19960930", "jalen-green-20020209", "tari-eason-20010510", "jabari-smith-jr-20030513", "victor-oladipo-19920504", "jeff-green-19860828", "fred-vanvleet-19940225", "jalen-smith-20000316", "bennedict-mathurin-20020619", "oscar-tshiebwe-19991127", "jordan-nwora-19980909", "bruce-brown-19960815", "james-johnson-19870220", "jarace-walker-20030904", "isaiah-wong-20010128", "kendall-brown-20030511", "t-j-mcconnell-19920325", "isaiah-jackson-20020110", "ben-sheppard-20010716", "andrew-nembhard-20000116", "myles-turner-19960324", "buddy-hield-19921217", "aaron-nesmith-19991016", "obi-toppin-19980304", "tyrese-haliburton-20000229", "terance-mann-19961018", "kawhi-leonard-19910629", "bones-hyland-20000914", "jordan-miller-20000123", "joshua-primo-20021224", "amir-coffey-19970617", "norman-powell-19930525", "james-harden-19890826", "kobe-brown-20000101", "p-j-tucker-19850505", "ivica-zubac-19970318", "daniel-theis-19920404", "xavier-moon-19950102", "mason-plumlee-19900305", "russell-westbrook-19881112", "paul-george-19900502", "moussa-diabate-20020121", "brandon-boston-jr-20011128", "lebron-james-19841230", "taurean-prince-19940322", "cam-reddish-19990901", "jaxson-hayes-20000523", "christian-wood-19950927", "austin-reaves-19980529", "colin-castleton-20000525", "anthony-davis-19930311", "gabe-vincent-19960614", "alex-fudge-20030506", "maxwell-lewis-20020727", "max-christie-20030210", "rui-hachimura-19980208", "dangelo-russell-19960223", "dmoi-hodge-19981220", "jarred-vanderbilt-19990403", "jalen-hood-schifino-20030619", "jaylen-nowell-19990709", "brandon-clarke-19960919", "desmond-bane-19980625", "jacob-gilyard-19980714", "shaquille-harrison-19931006", "ja-morant-19990810", "luke-kennard-19960624", "steven-adams-19930720", "jake-laravia-20011103", "kenneth-lofton-jr-20020814", "bismack-biyombo-19920828", "marcus-smart-19940306", "xavier-tillman-sr-19990112", "derrick-rose-19881004", "david-roddy-20010327", "jaren-jackson-jr-19990915", "vince-williams-jr-20000830", "gregory-jackson-ii-20041217", "santi-aldama-20010110", "ziaire-williams-20010912", "john-konchar-19960322", "bam-adebayo-19970718", "dru-smith-19971230", "jimmy-butler-19890914", "caleb-martin-19950928", "kevin-love-19880907", "cole-swider-19990508", "nikola-jovic-20030609", "orlando-robinson-20000710", "r-j-hampton-20010207", "thomas-bryant-19970731", "jamal-cain-19990320", "haywood-highsmith-19961209", "josh-richardson-19930915", "duncan-robinson-19940422", "jaime-jaquez-jr-20010218", "tyler-herro-20000120", "kyle-lowry-19860325", "a-j-green-19990927", "thanasis-antetokounmpo-19920718", "bobby-portis-19950210", "giannis-antetokounmpo-19941206", "pat-connaughton-19930106", "andre-jackson-jr-20011113", "lindell-wigginton-19980328", "marjon-beauchamp-20011012", "damian-lillard-19900715", "jae-crowder-19900706", "khris-middleton-19910812", "tyty-washington-20011115", "cameron-payne-19940808", "brook-lopez-19880401", "chris-livingston-20031015", "robin-lopez-19880401", "malik-beasley-19961126", "marques-bolden-19980417", "jaylen-clark-20011013", "jaden-mcdaniels-20000929", "shake-milton-19960926", "luka-garza-19981227", "daishen-nix-20020213", "jordan-mclaughlin-19960409", "anthony-edwards-20010805", "leonard-miller-20031126", "rudy-gobert-19920626", "naz-reid-19990826", "wendell-moore-jr-20010918", "kyle-anderson-19930920", "mike-conley-19871011", "troy-brown-jr-19990728", "karl-anthony-towns-19951115", "josh-minott-20021125", "nickeil-alexander-walker-19980902", "brandon-ingram-19970902", "matt-ryan-19970417", "dyson-daniels-20030317", "kira-lewis-jr-20010406", "larry-nance-jr-19930101", "jose-alvarado-19980412", "jonas-valanciunas-19920506", "herbert-jones-19981006", "trey-murphy-iii-20000618", "cj-mccollum-19910919", "jeremiah-robinson-earl-20001103", "naji-marshall-19980124", "dereon-seabron-20000526", "e-j-liddell-20001218", "cody-zeller-19921005", "zion-williamson-20000706", "jordan-hawkins-20020429", "jacob-toppin-20000508", "miles-mcbride-20000908", "ryan-arcidiacono-19940326", "taj-gibson-19850624", "quentin-grimes-20000508", "charlie-brown-jr-19970202", "immanuel-quickley-19990617", "donte-divincenzo-19970131", "mitchell-robinson-19980401", "julius-randle-19941129", "rj-barrett-20000614", "jalen-brunson-19960831", "josh-hart-19950306", "daquan-jeffries-19970830", "jericho-sims-19981020", "jaylen-martin-20040128", "isaiah-hartenstein-19980505", "evan-fournier-19921029", "isaiah-joe-19990702", "tre-mann-20010203", "keyontae-johnson-20000524", "lindy-waters-iii-19970728", "aleksej-pokusevski-20011226", "jaylin-williams-20020629", "ousmane-dieng-20030521", "chet-holmgren-20020501", "cason-wallace-20031107", "vasilije-micic-19940113", "aaron-wiggins-19990102", "jalen-williams-20010414", "luguentz-dort-19990419", "josh-giddey-20021010", "kenrich-williams-19941202", "shai-gilgeous-alexander-19980712", "davis-bertans-19921112", "olivier-sarr-19990220", "gary-harris-19940914", "kevon-harris-19970624", "admiral-schofield-19970330", "anthony-black-20040120", "goga-bitadze-19990720", "paolo-banchero-20021112", "wendell-carter-jr-19990416", "caleb-houstan-20030109", "chuma-okeke-19980818", "joe-ingles-19871002", "jett-howard-20030914", "trevelin-queen-19970225", "franz-wagner-20010827", "jonathan-isaac-19971003", "markelle-fultz-19980529", "jalen-suggs-20010603", "moritz-wagner-19970426", "cole-anthony-20000515", "javonte-smart-19990603", "deanthony-melton-19980528", "jaden-springer-20020925", "tyrese-maxey-20001104", "kj-martin-jr-20010106", "marcus-morris-sr-19890902", "mo-bamba-19980512", "joel-embiid-19940316", "robert-covington-19901214", "kelly-oubre-jr-19951209", "danuel-house-jr-19930607", "furkan-korkmaz-19970724", "tobias-harris-19920715", "paul-reed-19990614", "ricky-council-iv-20010803", "patrick-beverley-19880712", "terquavion-smith-20021231", "nicolas-batum-19881214", "devin-booker-19961030", "saben-lee-19990623", "grayson-allen-19951008", "drew-eubanks-19970201", "udoka-azubuike-19990917", "theo-maledon-20010612", "bradley-beal-19930628", "jordan-goodwin-19981023", "kevin-durant-19880929", "bol-bol-19991116", "eric-gordon-19881225", "keita-bates-diop-19960123", "chimezie-metu-19970322", "jusuf-nurkic-19940823", "nassir-little-20000211", "yuta-watanabe-19941013", "josh-okogie-19980901", "damion-lee-19921021", "deandre-ayton-19980723", "jabari-walker-20020730", "moses-brown-19991013", "duop-reath-19960626", "jerami-grant-19940312", "toumani-camara-20000508", "ish-wainright-19940912", "ibou-badji-20021013", "robert-williams-iii-19971017", "justin-minaya-19990326", "rayan-rupert-20040531", "shaedon-sharpe-20030530", "scoot-henderson-20040203", "anfernee-simons-19990608", "skylar-mays-19970905", "malcolm-brogdon-19921211", "kris-murray-20000819", "matisse-thybulle-19970304", "harrison-barnes-19920530", "jordan-ford-19980526", "domantas-sabonis-19960503", "trey-lyles-19951105", "malik-monk-19980204", "javale-mcgee-19880119", "deaaron-fox-19971220", "juan-toscano-anderson-19930410", "jalen-slawson-19991022", "keon-ellis-20000108", "kessler-edwards-20000809", "chris-duarte-19970613", "keegan-murray-20000819", "alex-len-19930616", "kevin-huerter-19980827", "davion-mitchell-19980905", "aleksandar-vezenkov-19950806", "colby-jones-20020528", "devonte-graham-19950222", "tre-jones-20000108", "david-duke-jr-19991013", "zach-collins-19971119", "charles-bassey-20001028", "charles-bediako-20020310", "dominick-barlow-20030526", "sidy-cissoko-20040402", "cedi-osman-19950408", "jeremy-sochan-20030520", "devin-vassell-20000823", "doug-mcdermott-19920103", "malaki-branham-20030512", "julian-champagnie-20010629", "keldon-johnson-19991011", "blake-wesley-20030316", "victor-wembanyama-20040104", "sandro-mamukelashvili-19990523", "markquis-nowell-19991225", "jontay-porter-19991115", "garrett-temple-19860508", "malachi-flynn-19980510", "jalen-mcdaniels-19980131", "gradey-dick-20031120", "gary-trent-jr-19990118", "otto-porter-jr-19930603", "chris-boucher-19930111", "scottie-barnes-20010801", "thaddeus-young-19880621", "pascal-siakam-19940402", "javon-freeman-liberty-19991020", "og-anunoby-19970717", "dennis-schroder-19930915", "christian-koloko-20000620", "precious-achiuwa-19990919", "jakob-poeltl-19951015", "josh-christopher-20011208", "talen-horton-tucker-20001125", "micah-potter-19980406", "kris-dunn-19940318", "walker-kessler-20010726", "keyonte-george-20031108", "jordan-clarkson-19920607", "johnny-juzang-20010317", "taylor-hendricks-20031122", "kelly-olynyk-19910419", "omer-yurtseven-19980619", "luka-samanic-20000109", "brice-sensabaugh-20031030", "john-collins-19970923", "lauri-markkanen-19970522", "collin-sexton-19990104", "ochai-agbaji-20000420", "simone-fontecchio-19951209", "jordan-poole-19990619", "eugene-omoruyi-19970214", "mike-muscala-19910701", "ryan-rollins-20020703", "anthony-gill-19921017", "daniel-gafford-19981001", "patrick-baldwin-jr-20021118", "landry-shamet-19970313", "jared-butler-20000825", "bilal-coulibaly-20040726", "delon-wright-19920426", "deni-avdija-20010103", "danilo-gallinari-19880808", "tyus-jones-19960510", "corey-kispert-19990303", "kyle-kuzma-19950724", "jules-bernard-20000121", "johnny-davis-20020227"]
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

    for player in all_player_data:
        player_info = player["data"]["nbaPlayers"][0]   
        player_id = player_info["id"]
        
        name = f"{player_info['firstName']} {player_info['lastName']}"
        
        team = player_info.get("team");
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
            "floorPrice": -1,
            "threeDaysAvgPrice": -1,
            "actualCap": actual_cap,
            "futureCap": future_cap,
            "differenceCap": future_cap - actual_cap,
            "projectionScore": -1,
            "projectedMinutes": -1,
            "minutesDifference": 0,
            "capRatio": cap_ratio,
            "projRatio": 0,
            "finalRatio": 0,
            "moneyRatio": 0,
            "finalRatioMoney": 0,
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
    with open('datos_jugadores.json', 'w') as json_file:
        json.dump(final_output_data, json_file, indent=4)  # Added indentation for better JSON formatting

    end_time = datetime.now()
    execution_time = end_time - start_time
    print(f"Script execution time: {execution_time}")
    print(f"{datetime.now()} - Data written to datos_jugadores.json")

    # Ruta al ejecutable de Chrome y parámetros
    identificador = obtener_identificador_unico()

    if identificador == "Windows_DESKTOP-12SQU36":
        itsGeorge = False

    if not itsGeorge:
        chrome_command = r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\aleja\Desktop\Proyectos\SorareNBA\SorareGit\SorareNBAweb\chromeSession"'
    else:
        chrome_command = r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\ECLIPSE\Sorare\sorareNBAweb\chromeSession"'

    # Ejecutar el comando en una nueva ventana de la consola
    subprocess.Popen(chrome_command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

    # Conectar Selenium al navegador existente utilizando el modo de depuración remota
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    # Navegar a la URL específica
    url_to_open = "https://www.soraredata.com/lineupBuilder/sections/builder/sport/sr_basketball"
    driver.get(url_to_open)

    wait = WebDriverWait(driver, 2)

    # Localizar el contenedor por la clase "bg-surface-container-high"
    container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".rounded.flex.flex-row.bg-surface-container.w-full.space-x-6.justify-between.px-4.undefined")))

    # Dentro de ese contenedor, buscar el botón por su clase específica
    toggle_button = container.find_element(By.CLASS_NAME, "cursor-pointer")
    time.sleep(1)  # Puedes ajustar el tiempo según sea necesario


    toggle_button.click()



    # Esperar un poco para que la página se actualice después de hacer clic en el botón y que empiece a scrollear

    wait = WebDriverWait(driver, 4)
    time.sleep(4)  # Puedes ajustar el tiempo según sea necesario


    # Localizar el elemento que contiene el scroll por su ID
    scroll_container = wait.until(EC.presence_of_element_located((By.ID, "table_scroll")))

    # Click on the element to give it focus
    scroll_container.click()

    #Segunda forma de automatizar por si falla
    # Perform scrolling using ActionChains
    actions = ActionChains(driver)

    scroll_duration = 42  # seconds
    start_time = time.time()

    while time.time() - start_time < scroll_duration:
        actions.send_keys(Keys.ARROW_DOWN).perform()


    getProj()

    # Esperar unos segundos (o el tiempo necesario para que Chrome se inicie)
    time.sleep(1)  # Puedes ajustar el tiempo según sea necesario



    # Cerrar la ventana de la consola actual (cmd)
    subprocess.Popen("taskkill /F /IM cmd.exe", shell=True)

    ruta_archivo = "datos_jugadores_updated.json"
    with open(ruta_archivo, "r") as archivo:
        json_jugadores_raw = json.load(archivo)
    # Crear una copia profunda del objeto sin la clave "pointsRegister"
        json_predictor = copy.deepcopy(json_jugadores_raw)
        for jugador in json_predictor['jugadores']:
            jugador.pop('pointsRegister', None)

    ruta_archivo2 = "datos_jugadores_my_players.json"
    with open(ruta_archivo2, "r") as archivo:
        json_myplayers_raw = json.load(archivo)
    # Crear una copia profunda del objeto sin la clave "pointsRegister"
        json_mypredictor = copy.deepcopy(json_myplayers_raw)
        for jugador in json_mypredictor['jugadores']:
            jugador.pop('pointsRegister', None)
            
        resultado_contender = optimize_team(json_predictor['jugadores'], 110, True)
        resultado_champion = optimize_team(json_predictor['jugadores'], 120, False)

        resultado_myContender = optimize_team(json_mypredictor['jugadores'], 110, True)
        resultado_myChampion = optimize_team(json_mypredictor['jugadores'], 120, False)
        
        resultado_contender_combined, resultado_champion_combined = optimize_both_teams(json_predictor['jugadores'], 110, 120)
        resultado_myContender_combined, resultado_myChampion_combined = optimize_both_teams(json_mypredictor['jugadores'], 110, 120)

        optimalCombined = {
            "optimalContender": resultado_contender_combined,
            "optimalChampion": resultado_champion_combined
        }
        
        myOptimalCombined = {
            "optimalContender": resultado_myContender_combined,
            "optimalChampion": resultado_myChampion_combined
        }



        # Crear un diccionario con las claves y valores
        optimal_lineups = {
            "optimalContender": resultado_contender,
            "optimalChampion": resultado_champion,
            "optimalCombined": optimalCombined,
            "myOptimalContender": resultado_myContender,
            "myOptimalChampion": resultado_myChampion,
            "myOptimalCombined": myOptimalCombined,
        }

        # Guardar el diccionario en un archivo JSON
        with open("optimal_lineups.json", "w") as json_file:
            json.dump(optimal_lineups, json_file)



    '''
    #Forma rapida scrollear solo vale con ventana maximizada
    time.sleep(3)

    # Obtiene las coordenadas del elemento
    table_scroll_location = scroll_container.location

    # Calcula las coordenadas para el extremo derecho del div
    end_x = table_scroll_location['x'] + scroll_container.size['width'] - 5

    # Calcula las coordenadas para bajar 3/4 de la ventana
    end_y = table_scroll_location['y'] + (driver.execute_script("return window.innerHeight") * 0.7)

    # Mueve el cursor a las coordenadas calculadas
    pyautogui.moveTo(end_x, end_y)

    # Haz clic mantenido durante 10 segundos
    pyautogui.mouseDown()
    time.sleep(14)
    pyautogui.mouseUp()

    '''


