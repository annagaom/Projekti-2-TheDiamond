import random
import mysql.connector
import rule
from geopy import distance
from prettytable import PrettyTable

from flask import Flask, request, Response, jsonify

app = Flask(__name__)

def connect_db():
    return mysql.connector.connect(
         host='127.0.0.1',
         port= 3306,
         database='lentopeli',
         user='user1',
         password='sala1',
         autocommit=True
    )


connection = connect_db()

#FUNCTIONS
#valitse peliin Suomen keskisuuret ja suuret lentokentät (yhteensä 31)
def get_airports():
    query = """SELECT ident, airport.name, latitude_deg, longitude_deg, country.name as country_name
FROM airport, country
WHERE airport.iso_country = country.iso_country
AND country.iso_country = 'FI' AND (type = 'large_airport'
OR type = 'medium_airport');"""
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchall()
    return result


#saada tehtävät tietokannasta
def get_tasks():
    query = "SELECT * FROM task ORDER BY RAND();"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def get_screen_names():
    sql = f"select screen_name from game"
    cursor = connection.cursor()
    cursor.execute(sql)
    list = cursor.fetchall()
    names = []
    for n in list:
        names.append(n[0])
    return names

def create_new_player(name):
    query = f"INSERT INTO game (screen_name) VALUES('{name}');"
    cursor = connection.cursor()
    cursor.execute(query)
    player_id = cursor.lastrowid
    return player_id

def get_existing_game_id(name):
    query = f"SELECT id FROM game WHERE screen_name = '{name}';"
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    id = result[0]
    return id


#päivittää game taulu(location käytetään icao-koodilla)
def update_game(game_id, p_range, p_flight=None, loca=None, goal_loca=None):
    if p_flight is None and loca is None and goal_loca is None:
        query = f"UPDATE game SET player_range = {p_range} WHERE id = {game_id};"
    elif goal_loca is None:
        query = f"UPDATE game SET location = '{loca}', player_range = {p_range}, player_flight = {p_flight} WHERE id = {game_id};"
    else:
        query = f"UPDATE game SET player_range = {p_range}, player_flight = {p_flight}, location = '{loca}', " \
                f"goal_id = 1, goal_location = '{goal_loca}' WHERE id = {game_id};"
    cursor = connection.cursor()
    cursor.execute(query)

#luo uusi peli: insert current airport, player range, player flight, goal airport --> game taulu
def create_game(airports, p_range, p_flight, p_id):
    # peli arpoo aloituslentokenttä ja lentokenttä, joka timantti sijaitsee
    start = random.choice(airports)
    diamond = random.choice(airports)
    while start == diamond:
        start = random.choice(airports)
        diamond = random.choice(airports)
    start_icao = start['ident']
    diamond_icao = diamond['ident']
    update_game(p_id, p_range, p_flight, start_icao, diamond_icao)
    return (start, diamond)

#get airport info
def get_airport_info(icao_code):
    query = f"SELECT ident, airport.name, latitude_deg, longitude_deg, country.name as country_name " \
            f"FROM airport, country WHERE airport.iso_country = country.iso_country AND ident = '{icao_code}';"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchone()
    return result

#laskea etäiisyys kahden lentokentä valillä
def calc_distance(icao_1, icao_2):
    airport1 = get_airport_info(icao_1)
    airport2 = get_airport_info(icao_2)
    airport1_coord = (airport1['latitude_deg'], airport1['longitude_deg'])
    airport2_coord = (airport2['latitude_deg'],airport2['longitude_deg'])
    distance_km = distance.distance(airport1_coord, airport2_coord).km
    dist_rounded = round(distance_km)
    return dist_rounded

#saada lentokentät, joille pelaaja voi lentää
# metrimäärällään
def get_airports_in_range1(airports, cur_airport, p_range):
    airports_in_range = []
    for airport in airports:
        distance_km = calc_distance(cur_airport['ident'], airport['ident'])
        if distance_km <= p_range and distance_km != 0:
            airports_in_range.append(airport)
    return airports_in_range

def get_airports_in_range(airports, cur_icao, p_range):
    airports_in_range = []
    for airport in airports:
        distance_km = calc_distance(cur_icao, airport['ident'])
        if distance_km <= p_range and distance_km != 0:
            airports_in_range.append(airport)
    return airports_in_range

# hakea pelaajan tiedot
def get_game_info(game_id):
    query = f"SELECT player_range, player_flight, location, screen_name, goal_location " \
          f"FROM game WHERE id = {game_id};"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchone()
    return result

# find player location
def get_player_loc(game_id):
    query = f"SELECT location FROM game WHERE id = {game_id};"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchone()
    return result


#
# #PELI ALKAA
# #kysy tarvitseko näyttää pelin sääntö
# show_rules = input("Haluatko lukea pelin sääntöjä? Yes/No: ")
# if show_rules.lower() == "yes":
#     rule.play_rules()
# input("Jatkamaan painamalla Enter-näppäintä...")
# print("1. Olet uusi pelaaja.")
# print("2. Olet pelannut aikaisemmin.")
#
# choose = input("Anna toiminnan numero (1 tai 2): ")
# while choose not in ['1', '2']:
#     choose = input("Anna toiminnan numero (1 tai 2): ")
# choose = int(choose)
# player_names = get_screen_names()
# names_upper = []
# for name in player_names:
#     names_upper.append(name.upper())
# #print(names_upper)
# if choose == 1:
#     name = input("Luo Pelinimi: ")
#     while name.upper() in names_upper or name == "":
#         if name.upper() in names_upper:
#             print(f"{name} nimi on jo käytössä. Anna uusi nimi.")
#         elif name == "":
#             print(f"Et syötetty nimeä. Anna uusi nimi.")
#         name = input("Luo pelinimi: ")
#     player_id = create_new_player(name)
# elif choose == 2:
#     print("Tervetuloa etsimään timanttia!")
#     name = input("Anna nimesi: ")
#     while name.upper() not in names_upper:
#         print(f"Nimi: {name} ei löytyy listasta.")
#         name = input("Anna nimesi: ")
#     player_id = get_existing_game_id(name)
#
# player_range = 1000
# flight_limit = 15
# player_flight = flight_limit
#
# #pelin lentokentät
# all_airports = get_airports()
# #print(all_airports)
# #luo peli pelaajalle, palauta pelaajan aloitus lentokenttä, pelin lentokentä, jossa timantti
# (starting, diamond_airport) = create_game(all_airports, player_range, player_flight, player_id)
#
# #print(f"diamond: {diamond_airport}")
#
# current = starting
# #print(f"starting: {starting}")
#
# #pelin kaikki tehtävät
# tasks = get_tasks()
# #print(tasks)
#
# #Boolean kun timantti on löytynyt
# game_win = False
# game_lose = False
#
# moved = []
# moved.append(starting['ident'])
# #pelin loopi
# while game_win == False:
#     #näyttää kenttien tiedot, etäiisyys ja pelaajan oma kmmäärä sekä lentokertaa jäljellä pelaajalle
#     current_name = get_airport_info(current['ident'])['name']
#     current_to_diamond = calc_distance(current['ident'], diamond_airport['ident'])
#     print(f"\033[34m{name}, olet nyt {current_name} lentokentällä.\033[0m")
#
#     print(f"\033[34mSinulla on nyt {player_range} km ja {player_flight} lentokertaa jäljellä.\033[0m")
#
#     if current_to_diamond <= 300:
#         print("\033[32mEtäisyys timanttiin on noin 0 - 300 km.\033[0m")
#     elif 300 < current_to_diamond <= 600:
#         print("\033[32mEtäisyys timanttiin on noin yli 300 - 600 km.\033[0m")
#     elif current_to_diamond > 600:
#         print("\033[32mEtäisyys timanttiin on noin yli 600 km.\033[0m")
#     input("Jatkamaan painamalla Enter-näppäintä...")
#
#     # tehtävä suoritaminen
#     # kysy jos pelaaja halua lisätä kmmäärä tekemällä tehtävä
#     question = input("\033[34mHaluatko voittaa lisä kilometrimäärä tai jatka matka? "
#                      "yes = Haluan, Enter-näppäin: Ohita \033[0m ")
#     if question.lower() == "yes":
#         print(("Tervetuloa tehtäviin!"))
#         task = random.choice(tasks)
#         print(f"Laskea: {task['name']}")
#         ans = input("Anna vaustaus: ")
#         while not ans.isdigit():
#             print("Anna vastaus numeroina.")
#             ans = input("Anna vastaus: ")
#         if task['answer'] == int(ans):
#             print("Vastauksesi on oikein, voitat 500 km!")
#             player_range += 500
#             #print(player_range)
#         else:
#             print("Vastauksesi on väärä, vähenee 50 km!")
#             player_range -= 50
#         update_game(player_id, player_range)
#         print(f"\033[34mSinulla on nyt {player_range} km ja {player_flight} lentokertaa jäljellä.\033[0m")
#
#     #laskea etäisyys ja näyttää lentokentät, joihin pelaaja on mahdollista lentää
#     in_range = get_airports_in_range(all_airports, current, player_range)
#     if len(in_range) == 0:
#         print("Peli loppui! Sinun kilometrimäärä ei riittää lentämiseksi. ")
#         game_lose = True
#         break
#     print(f"Mihin haluat lentää? On {len(in_range)} lentokenttää, mihin voit lentää kilometrimäärälläsi.")
#     input("Jatkamaan painamalla Enter-näppäintä...")
#     print("Lentokentät:...")
#     in_range_icao_list = []
#     im_range_distance_added = []
#     # laskea etäisyys, lisää ICAO koodit eri listalle, lisää etäisyys tietoa in_range_distance_added listalle
#     for airport in in_range:
#         in_range_icao_list.append(airport['ident'])
#         distance_km = calc_distance(current['ident'], airport['ident'])
#         airport.update({'distance': distance_km})
#         im_range_distance_added.append(airport)
#
#     #tulosta taulu etäisyyden mukaan
#     list_sorted = sorted(im_range_distance_added, key=lambda a: a['distance'])
#     table = PrettyTable()
#     table.align["Lentokenttä"] = "r"
#     Y = "\033[93m"  # yellow
#     B = "\033[1m"  # Bold
#     R = "\033[0m"  # reset
#     table.field_names = [B + "Lentokenttä" + R, B + "ICAO-koodi" + R, B + "Etäisyys" + R]
#
#     for a in list_sorted:
#         if a['ident'] not in moved:
#             table.add_row([a['name'], a['ident'], a['distance']])
#         else:
#             table.add_row([Y + a['name'] + R, Y + a['ident'] + R, Y + str(a['distance']) + R])
#     print(table)
#
#     #kysy
#
#     icao = input("Mihin haluat jatkaa matkaa? Lentokentän ICAO-koodi: ").upper()
#     #Pyytä uudelleen ICAO-koodi, jos se ei ole yllä olevassa luettelossa
#     while icao not in in_range_icao_list:
#         icao = input("Väärä ICAO-koodi. Kijoita uudestaan: ").upper()
#     moved.append(icao)
#
#     #laskea etäisyys ja päivitä tietoja game-taululle
#     distance_between = calc_distance(current['ident'], icao)
#     player_range = player_range - distance_between
#     current = get_airport_info(icao)
#     player_flight = player_flight - 1
#     #print(player_flight)
#     update_game(player_id, player_range, player_flight, icao)
#
#     if current['ident'] == diamond_airport['ident']:
#         print(B + "Wau! Löysit timantin! Olet hyvä etsijä!" + R)
#         game_win = True
#
#     if player_flight == 0:
#         print(B + f"Peli loppui! Olet lentänyt {flight_limit} kertaa." + R)
#         game_lose = True
#         break
#
#
# print(B + "ONNEA! VOITIT PELIN! " + R if game_win else "")
# print(B + f"Hävisit! \n Timantin sijaitsee {diamond_airport['name']} lentokentällä."
#       f" \n Sinulla on  {player_range} km ja {player_flight} lentokertaa jäljellä." + R if game_lose else "")
#
#

