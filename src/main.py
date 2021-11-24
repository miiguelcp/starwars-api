"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import requests
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import Favorite, db, User
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('FLASK_APP_KEY')
jwt = JWTManager(app)
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

#Replace swapi url to localhost
def swapi_to_localhost(swapi_url):
    return swapi_url.replace("https://www.swapi.tech/api/", "http://localhost:3000/")

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


#Register new user
@app.route('/signup', methods=['POST'])
def create_new_user():
    user_data = request.json
    user = User.create(user_data)
    if user is not None:
        print(user)
        return jsonify({"message":"User create correctly!"}), 201
    else:
        return jsonify({"message":"Can't create user. Try again!"}), 500


#Create token for user
@app.route('/login', methods=['POST'])
def user_login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    print(request.json)
    user = User.query.filter_by(email=email, password=password).one_or_none()
    if user is None:
        return jsonify({"msg": "Something went wrong, please try again!"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify({ "token": access_token, "user_id": user.id, "username": user.username })


#Get data about the user
@app.route('/users', methods=['GET','POST'])
def handle_users():
    if request.method == "GET":
        users = User.query.all()
        print(users)
        response = []
        for user in users:
            response.append(user.serialize())
        print(response)
        return jsonify(response), 200
    body = request.json
    object_usuario = User.create(body)
    if object_usuario is not None:
        return jsonify(object_usuario.serialize()), 201
    return jsonify({"message":"Something happen, try again!"}), 400


#Get all favorites for a user
@app.route('/favorites', methods=['GET'])
@jwt_required()
def get_user_favorites():
    user_id = get_jwt_identity()
    favorites = Favorite.query.filter_by(user_id=user_id)
    response = list(map(
        lambda favorite: favorite.serialize(),
        favorites
    ))
    return jsonify(response), 200


#Create a favorite for a user
@app.route('/favorites/<string:nature>', methods=['POST'])
@jwt_required()
def handle_users_favorite(nature):
    uid = request.json['uid']
    name = request.json['name']
    new_favorite = Favorite(
        user_id = get_jwt_identity(),
        name = name,
        url = f"https://www.swapi.tech/api/{nature}/{uid}"
    )
    db.session.add(new_favorite)
    try:
        db.session.commit()
        return jsonify(new_favorite.serialize()), 201
    except Exception as error:
        db.session.rollback()
        return jsonify(error.args), 500


#Delete a favorite
@app.route('/favorites/<int:favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    favorite = Favorite.query.filter_by(id=favorite_id).one_or_none()
    if favorite is None:
        return jsonify({"message":"not found"}), 404
    deleted = favorite.delete()
    if deleted == False:
        return jsonify({"message":"Something happen try again"}), 500
    return jsonify([]), 204


#Get all people
@app.route('/people', methods=['GET'])
def handle_people():
    limit = request.args.get("limit", 10)
    page = request.args.get("page", 1)
    response = requests.get(f"https://www.swapi.tech/api/people?page={page}&limit={limit}")
    response = response.json()
    response.update(
        previous = swapi_to_localhost(response['previous']) if response['previous'] else None,
        next = swapi_to_localhost(response['next']) if response['next'] else None
    )
    return jsonify(response), 200


#Get info about all planets
@app.route('/planets', methods=['GET'])
def handle_planets():
    response = requests.get(f"https://www.swapi.tech/api/planets?page=1&limit=1000")
    response = response.json()
    results = response['results']
    for result in results:
        result.update(
            url = swapi_to_localhost(result['url'])
        )
    return jsonify(results), 200


#Get info about all vehicles
@app.route('/vehicles', methods=['GET'])
def handle_vehicles():
    response = requests.get(f"https://www.swapi.tech/api/vehicles?page=1&limit=1000")
    response = response.json()
    results = response['results']
    for result in results:
        result.update(
            url = swapi_to_localhost(result['url'])
        )
    return jsonify(results), 200


#Get info about one planet
@app.route('/planets/<int:planet_id>', methods=['GET'])
def handle_one_planet(planet_id):
    response = requests.get(f"https://www.swapi.tech/api/planets/{planet_id}")
    body = response.json()
    if response.status_code == 200:
        planet = body['result']
        planet['properties'].update(
            url = swapi_to_localhost(planet['properties']['url'])
        )
        return jsonify(planet), 200
    else:
        return jsonify(body), response.status_code
        

#Get info about one people
@app.route('/people/<int:people_id>', methods=['GET'])
def handle_one_people(people_id):
    response = requests.get(f"https://www.swapi.tech/api/people/{people_id}")
    body = response.json()
    if response.status_code == 200:
        people = body['result']
        people['properties'].update(
            url = swapi_to_localhost(people['properties']['url'])
        )
        return jsonify(people), 200
    else:
        return jsonify(body), response.status_code


#Get info about one vehicle
@app.route('/vehicles/<int:vehicle_id>', methods=['GET'])
def handle_one_vehicle(vehicle_id):
    response = requests.get(f"https://www.swapi.tech/api/vehicles/{vehicle_id}")
    body = response.json()
    if response.status_code == 200:
        vehicle = body['result']
        vehicle['properties'].update(
            url = swapi_to_localhost(vehicle['properties']['url'])
        )
        return jsonify(vehicle), 200
    else:
        return jsonify(body), response.status_code


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)