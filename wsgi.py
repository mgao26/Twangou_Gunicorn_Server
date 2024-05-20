from main import app
from flask import Flask, request, jsonify
import sys
import logging
import sqlite3

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)


@app.route('/', methods=['GET'])
def get_request():
    return 'This is a GET request.'


# Route for handling POST requests
def addUser(username, password, cursor):
    insert_command = "INSERT INTO USERS (USERNAME, PASSWORD) VALUES('{0}', '{1}');".format(username, password)
    cursor.execute(insert_command)

    return cursor.lastrowid


def check_availability(column_name, table_name, filter_value, cursor):
    query = "SELECT {0} FROM {1} WHERE {2} = '{3}'".format(column_name, table_name, column_name, filter_value)
    cursor.execute(query)

    row = cursor.fetchone()
    if row is not None:
        # not available
        return False
    else:
        # available
        return True


def check_credentials(column_1, column_2, value_1, value_2, table_name, cursor):
    query = "SELECT {0} FROM {1} WHERE {2} = '{3}' and {4} = '{5}'".format(column_1, table_name, column_1, value_1,
                                                                           column_2, value_2)
    cursor.execute(query)

    row = cursor.fetchone()
    if row is not None:
        # correct
        return row[0]
    else:
        # incorrect
        return -1


@app.route('/AddGohu', methods=['POST'])
def receive_gohu():
    if request.method == 'POST':
        # new plan: get all non-image info of Gohu, send back Gohu ID
        # then, send images with gohu id and save them to files with id name
        # when gohu is being pulled, send back those images with the gohu id
        parts = parse_message(request.data.decode("utf-8"), '|')
        title = parts[0]
        description = parts[1]
        user_id = parts[2]

        conn = sqlite3.connect("twangou.db")
        cursor = conn.cursor()

        insert_gohu = "INSERT INTO GOHUS (TITLE, DESCRIPTION, COVERIMAGE, HOST_ID) VALUES ('{0}', '{1}',NULL, '{2}')".format(
            title, description, user_id)
        cursor.execute(insert_gohu)
        if request.data:
            gohu_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return str(gohu_id)
        else:
            return 'No data received in the POST request', 400


# remember to implement different routes to help pass in different data
@app.route('/', methods=['POST'])
def post_request():
    if request.method == 'POST':
        conn = sqlite3.connect("twangou.db")
        cursor = conn.cursor()

        create_users_table = "CREATE TABLE IF NOT EXISTS USERS(USER_ID INTEGER PRIMARY KEY AUTOINCREMENT , " \
                             "USERNAME TEXT, PASSWORD TEXT);"
        cursor.execute(create_users_table)

        create_gohus_table = "CREATE TABLE IF NOT EXISTS GOHUS(gohuID INTEGER PRIMARY KEY AUTOINCREMENT , " \
                             "title TEXT, description TEXT, coverImage BLOB, " \
                             "host_id INTEGER, FOREIGN KEY (host_id) REFERENCES users(user_id)); "
        cursor.execute(create_gohus_table)

        create_products_table = "CREATE TABLE IF NOT EXISTS PRODUCTS(PRODUCT_ID INTEGER PRIMARY KEY AUTOINCREMENT " \
                                " , name TEXT, quantity INTEGER, cost REAL, " \
                                "productImage BLOB);";
        cursor.execute(create_products_table)

        create_gohu_products_table = "CREATE TABLE IF NOT EXISTS GOHU_PRODUCTS(GOHU_PRODUCT_ID INTEGER PRIMARY KEY " \
                                     "AUTOINCREMENT , gohu_ID INTEGER, product_ID INTEGER, " \
                                     "FOREIGN KEY (gohu_id) REFERENCES gohus(gohuID), FOREIGN KEY (product_ID) REFERENCES " \
                                     "products(PRODUCT_ID));";
        cursor.execute(create_gohu_products_table)

        create_gohu_members_table = "CREATE TABLE IF NOT EXISTS GOHU_MEMBERS(GOHU_MEMBER_ID INTEGER PRIMARY KEY " \
                                    "AUTOINCREMENT NOT NULL , gohu_ID INTEGER NOT NULL, user_ID INTEGER NOT NULL, " \
                                    "FOREIGN KEY (gohu_id) REFERENCES gohus(gohuID), FOREIGN KEY (user_ID) REFERENCES " \
                                    "products(USER_ID));";
        cursor.execute(create_gohu_members_table)

        data = request.data
        # message = data.decode("utf-8")
        parts = parse_message(data.decode("utf-8"), '|')
        objective = parts[0]
        server_response = ""

        if objective == 'SignUp':
            username = parts[1]
            password = parts[2]

            if not check_availability("username", "users", username, cursor):
                server_response = "Unavailable"
                print(server_response)
            else:
                user_id = addUser(username, password, cursor)
                print(user_id)
                server_response = "Available|" + str(user_id)
                print(server_response)
        elif objective == "SignIn":
            username = parts[1]
            password = parts[2]

            user_id = check_credentials("username", "password", username, password, "users", cursor)
            if user_id != -1:
                server_response = "Correct|" + user_id
            else:
                server_response = "Incorrect"
        if data:
            conn.commit()
            conn.close()
            return server_response
        else:
            return 'No data received in the POST request', 400


def parse_message(message, delimiter):
    parts = message.strip(delimiter).split(delimiter)
    return parts


if __name__ == "__main__":
    app.run()
