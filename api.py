#import the necessary modules and libraries
from flask import Blueprint, jsonify, request, session, redirect, url_for, send_file
from app.models.users import Users
from app.models.address import Address
from app.models.orders import Orders
from app.models.tickets import Tickets
from werkzeug.utils import secure_filename
from app import db
import os

api = Blueprint('api', __name__, url_prefix="/api")

#create a variable that stores the path for the attachments to be uploaded 
UPLOAD_FOLDER = os.path.abspath("app/static/attachments")

@api.route('/login', methods=['POST'])
#create the login page that asks the user to add their email and their password
def login():
    try:
        email = request.json.get('email')
        password = request.json.get('password')
        query = f"(select * from users where email='{email}' and password='{password}');"
        if not all((email, password)):
            return jsonify({
                    'status': 'error',
                    'message': 'Both email and password are required!'
            }), 400
        user = db.engine.execute(query).first()
        if user:
            session["email"] = email
            session["user_id"] = user[0]
            return jsonify({
                "status": "success",
                "id": user[0]
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Not sure"
            }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@api.route("/logout", methods=["POST"])
#create a function for the person/user to be able to log out
def logout():
    try:
        session["email"] = None
        session["user_id"] = None
        return jsonify(
            {
                "status": "success",
            }, 200
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@api.route("/add-address", methods=["POST"])
#funtion for the person to add their address such as their house number, city, country etc
def add_address():
    try:
        house_number = request.json.get("house_number")
        city = request.json.get("city")
        state = request.json.get("state")
        country = request.json.get("country")
        pin_code = request.json.get("pin_code")
        user_email = session.get("email")
        user_query = f"select * from users where email='{user_email}';"
        user = db.engine.execute(user_query).first()
        Address.create(user["id"], house_number, city, state, country, pin_code)
        return jsonify(
            {
                "status": "success",
            }, 201
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@api.route("/create-order", methods=["POST"])
#create a funtion that takes in user emails and gets them their order with the product name, the address
#and the amount

def create_order():
    try:
        user_email = session.get("email")
        user_query = f"select * from users where email='{user_email}';"
        user = db.engine.execute(user_query).first()
        product_id = request.json.get("product_id")
        address_id = request.json.get("address_id")
        amount = request.json.get("amount")
        Orders.create(user["id"], product_id, 1, address_id, amount)
        return jsonify(
            {
                "status": "success",
            }, 201
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@api.route("/submit-help", methods=["POST"])
#create the help funtion for the user to appeal for help
#the function allows the user to add a title, a description and add an attachment
#Due to no restriction as to what file type the attachment should be the hackers can install viruses into other computers

def submit_help():
    title = request.form.get("title")
    description = request.form.get("description")
    attachment = request.files.get("attachment")
    if attachment:
        filename = secure_filename(attachment.filename)
        attachment.save(os.path.join(UPLOAD_FOLDER, filename))
    user_email = session.get("email")
    user_query = f"select * from users where email='{user_email}';"
    user = db.engine.execute(user_query).first()
    Tickets.create(user["id"], title, description, filename)
    return jsonify(
            {
                "status": "success",
            }, 201
        )

@api.route("/download/<path:filename>")
#create the download funtion which joins the uploaded folder and filename and downloards them into the folder
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

@api.route("/search-order")
#create a funtion that searches for the persons order with their email 
def search_order():
    order_id = request.args.get("order_id")
    user_email = session.get("email")
    user_query = f"select * from users where email='{user_email}';"
    user = db.engine.execute(user_query).first()
    order_query = f"(select p.image, p.name, o.amount from products p right join orders o on o.user_id={user['id']} and p.id=o.product_id and o.id={order_id});"
    order = db.engine.execute(order_query).all()
    orders = []
    for order_obj in order:
        if all((order_obj[0], order_obj[1], order_obj[2])):
            orders.append([order_obj[0], order_obj[1], order_obj[2]])
    return jsonify({
        "status": "success",
        "orders": orders
    }), 200

@api.route("/execute", methods=["POST"])
#funtion that executes the query 
def execute():
    try:
        code = request.json.get("code")
        result = db.engine.execute(code).all()
        if len(result) == 0:
            return jsonify({
                "status": "no_result"
            }), 200
        else:
            keys, values = result[0].keys()._keys, []
            for result_obj in result:
                temp_values = []
                for result_value in result_obj:
                    temp_values.append(result_value)
                values.append(temp_values)
            return jsonify({
                "status": "success",
                "keys": keys,
                "values": values
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
