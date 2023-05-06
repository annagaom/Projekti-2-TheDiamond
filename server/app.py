import random
import json
from flask import Flask, request, Response
import mysql.connector
from flask_cors import CORS
import game
import config

app = Flask(__name__)
# lisätty cors
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def connect_db():
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        database='lentopeli',
        user='user1',
        password='sala1',
        autocommit=True
    )
connection = connect_db()


# http://127.0.0.1:5000/newgame?player=Martti
@app.route('/newgame')
def newgame():
    try:
        args = request.args
        player = args.get("player")
        player_id = game.create_new_player(player)
        player_range = config.player_range
        flight_limit = config.player_flight
        player_flight = flight_limit
        airports = game.get_airports()
        (starting, diamond_airport) = game.create_game(airports, player_range, player_flight, player_id)
        current = starting
        current_to_diamond = game.calc_distance(current['ident'], diamond_airport['ident'])
        in_range = game.get_airports_in_range(airports, current['ident'], player_range)
        range_to_fly = True
        if len(in_range) == 0:
            range_to_fly = False

        #in_range = game.get_airports_in_range(airports, current, player_range)
        # add distance to every airport, add status active to current airport
        for a in airports:
            distance = game.calc_distance(current['ident'], a['ident'])
            a.update({'distance': distance})

            if (current['ident'] == a['ident']):
                a.update({'active': True})
            else:
                a.update({'active': False})

            if (distance <= player_range):
                a.update({'in_range': True})
            else:
                a.update({'in_range': False})
        tasks = game.get_tasks()
        task = random.choice(tasks)
        res = {
            "game" : {
                "id" : player_id,
                "name": player,
                "range": player_range,
                "flight": player_flight,
                "range_to_flight": range_to_fly,
                "player_loc" : current,
                "diamond": {
                    "location": diamond_airport['ident'],
                    "airport_name": diamond_airport['name'],
                    "country": diamond_airport['country_name']
                },
                "distance_to_goal": current_to_diamond,
                "previous_loc" : ""
            },
            "airports" : airports,
            "task": task
        }
        status_code = 200
        res_json = json.dumps(res)
        return Response(response=res_json, status=status_code, mimetype="application/json")
    except ValueError:
        status_code = 400
        res = {"message": "not found"}
        res_json = json.dumps(res)
        return Response(response=res_json, status=status_code, mimetype="application/json")

# http://127.0.0.1:5000/flyto?game=30&dest=EFPO&range=700&flight=14
@app.route('/flyto')
def fly_to():
    try:
        args = request.args
        player_id = args.get("game")
        dest_code = args.get("dest")
        player_range = args.get("range")
        player_flight = args.get("flight")

        #hakea pelaajan sijainti ja päivitä uusi sijainti game taulussa
        previous_code = game.get_player_loc(player_id)

        game.update_game(player_id, player_range, player_flight, dest_code)

        game_data = game.get_game_info(player_id)
        print(f"data {game_data}")
        current = game.get_airport_info(dest_code)

        distance = game.calc_distance(current['ident'], dest_code)

        diamond_airport_icao = game_data['goal_location']
        diamond_airport = game.get_airport_info(diamond_airport_icao);
        current_to_diamond = game.calc_distance(current['ident'], diamond_airport_icao)
        print(current_to_diamond)
        airports = game.get_airports()
        in_range = game.get_airports_in_range(airports, current['ident'], game_data['player_range'])
        print(len(in_range))
        range_to_fly = True
        if len(in_range) == 0:
            range_to_fly = False
        # add distance to every airport, add status active to current airport
        for a in airports:
            distance = game.calc_distance(current['ident'], a['ident'])
            a.update({'distance': distance})
            if (current['ident'] == a['ident']):
                a.update({'active': True})
            else:
                a.update({'active': False})

            if (distance <= game_data['player_range']):
                a.update({'in_range': True})
            else:
                a.update({'in_range': False})
        print(airports)
        tasks = game.get_tasks()
        task = random.choice(tasks)
        res = {
            "game": {
                "id": player_id,
                "name": game_data['screen_name'],
                "range": game_data['player_range'],
                "flight": game_data['player_flight'],
                "range_to_flight": range_to_fly,
                "player_loc": current,
                "diamond": {
                    "location": diamond_airport_icao,
                    "airport_name": diamond_airport['name'],
                    "country": diamond_airport['country_name']
                },
                "distance_to_goal": current_to_diamond,
                "previous_loc": previous_code
            },
            "airports": airports,
            "task": task
        }
        status_code = 200
        res_json = json.dumps(res)
        return Response(response=res_json, status=status_code, mimetype="application/json")


    except ValueError:
        status_code = 400
        res = {"message": "airport not found"}
        res_json = json.dumps(res)
    return Response(response=res_json, status=status_code, mimetype="application/json")
@app.errorhandler(404)
def page_not_found(error):
    res = {"message": "Page not found"}
    res_json = json.dumps(res)
    return Response(response=res_json, status=404, mimetype="application/json")

if __name__ == '__main__':
    app.run(use_reloader=True, host="127.0.0.1", port=5002)

#
# class Airport:
#     def __init__(self, ident, name, ):


class Game:
    def __init__(self, id, goal_location, name):
        self.id = id
        self.name = name
        self.goal_location = goal_location
        self.status = {}
        self.airports = {}

        if id == 0:
            player_id = game.create_new_player(name)
            airports = game.get_airports()
            (starting, diamond_airport) = game.create_game(airports, config.player_range, config.player_flight, player_id)
            current = starting
            current_to_diamond = game.calc_distance(current['ident'], diamond_airport['ident'])
            in_range = game.get_airports_in_range(airports, current['ident'], config.player_range)
            range_to_fly = True
            if len(in_range) == 0:
                range_to_fly = False
            for a in airports:
                distance = game.calc_distance(current['ident'], a['ident'])
                a.update({'distance': distance})

                if (current['ident'] == a['ident']):
                    a.update({'active': True})
                else:
                    a.update({'active': False})

                if (distance <= config.player_range):
                    a.update({'in_range': True})
                else:
                    a.update({'in_range': False})
