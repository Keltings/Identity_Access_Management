import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

####################### ROUTES #############################
'''
    GET /drinks endpoint 
        is a public endpoint
        that contains only the drink.short() data representation and
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks')
def get_drinks():
    
    drinks_queried = Drink.query.order_by(Drink.id).all()

    drinks = [drink.short() for drink in drinks_queried]

    if not drinks_queried:
        abort(404)
    else:
        print(drinks)

        return jsonify({
        'success': True,
        'drinks': drinks,
        })


'''
GET /drinks-detail endpoint
    requires the 'get:drinks-detail' permission,
    contains the drink.long() data representation and 
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    get_details = Drink.query.order_by(Drink.id).all()
    drinks = [drink.long() for drink in get_details]

    if not get_details:
        abort(404)

    #print(payload)
    return jsonify({

        'success': True,
        'drinks': drinks,
    })


'''
POST /drinks
    creates a new row in the drinks table
    requires the 'post:drinks' permission
    contains the drink.long() data representation and
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    data = request.get_json()
    
    if 'title' and 'recipe' not in data:
        abort(422)
    
    new_drink = Drink(title=data['title'], recipe=json.dumps(data['recipe']))
    drink = [new_drink.long()]

    try:
        new_drink.insert()
    
        return jsonify({
            'success': True,
            'drinks': drink,
            })

    except:
        abort(422)

'''
PATCH /drinks/<id> endpoint:
    where <id> is the existing model id
    responds with a 404 error if <id> is not found
    updates the corresponding row for <id>
    requires the 'patch:drinks' permission
    contains the drink.long() data representation and
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload,drink_id):

    get_drink = Drink.query.get(drink_id)
    drink = [get_drink.long()]

    try:
        if get_drink is None:
            abort(404)
        data =  request.get_json()

        if 'title' in data:
            get_drink.title = data['title']
        if 'recipe' in data:
            get_drink.recipe = json.dumps(data['recipe'])

        get_drink.update()

        return jsonify({
            'success': True,
            'drinks': drink,
        })
    except:
        abort(422)


'''
DELETE /drinks/<id> endpoint:
    where <id> is the existing model id
    responds with a 404 error if <id> is not found
    deletes the corresponding row for <id>
    requires the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record and
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload,drink_id):
    try:
        get_drink = Drink.query.get(drink_id)

        if get_drink is None:
            abort(404)

        get_drink.delete()

        return jsonify({
            'success': True,
            'deleted': get_drink.id,
        })
    except:
        abort(422)

############################ Error Handling #####################################
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
implement error handlers using the @app.errorhandler(error) decorator
    each error handler returns (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
  

# implement error handler for 404
@app.errorhandler(404)
def unauthorized(error):
  return jsonify({
    'success': False,
    'error': 404,
    'message':'resource not found'
  }), 404

 # implement error handler for AuthError
@app.errorhandler(AuthError)
def authError(error):
    return (
        jsonify({
            'success': False,
            'error': error.status_code,
            'message': error.error['description']
        }), error.status_code
    )