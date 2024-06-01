from main import app
from flask import Flask, request, jsonify
import sys
import logging
import sqlite3
import os

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)


@app.route('/FetchNumberOfGohus', methods=['GET'])
def get_num_of_gohus():
    user_id = request.args.get('user-id')
    conn = sqlite3.connect("twangou.db")
    cursor = conn.cursor()

    get_gohus = "SELECT * FROM GOHUS WHERE HOST_ID = {0}".format(user_id)
    cursor.execute(get_gohus)
    rows = cursor.fetchall()

    return str(len(rows))


@app.route('/FetchGohu', methods=['GET'])
def get_gohu():
    user_id = request.args.get('user-id')
    order = request.args.get('order')
    conn = sqlite3.connect("twangou.db")
    cursor = conn.cursor()

    get_gohus = "SELECT gohu_id, title, description, cover_image, num_of_products FROM GOHUS WHERE HOST_ID = {0}".format(
        user_id)
    cursor.execute(get_gohus)

    rows = cursor.fetchall()
    print(rows[0])
    return str(rows[int(order)])


@app.route('/FetchImage', methods=['GET'])
def get_image():
    file_name = request.args.get('file-name')
    with open(file_name, 'rb') as file:
        cover_image = file.read()

    return cover_image


@app.route('/FetchProduct', methods=['GET'])
def get_product():
    gohu_id = request.args.get('gohu-id')
    order = request.args.get('order')
    conn = sqlite3.connect("twangou.db")
    cursor = conn.cursor()

    get_product = "SELECT name, quantity, cost, product_image FROM PRODUCTS WHERE gohu_id = {0} AND product_order = {1};".format(
        gohu_id, order)
    cursor.execute(get_product)
    row = cursor.fetchone()

    return str(row)


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
    query = "SELECT USER_ID FROM {0} WHERE {1} = '{2}' and {3} = '{4}'".format(table_name, column_1, value_1,
                                                                               column_2, value_2)
    cursor.execute(query)

    row = cursor.fetchone()
    if row is not None:
        # correct
        print(row)
        return row[0]
    else:
        # incorrect
        return -1


@app.route('/AddGohu/AddProductImage', methods=['POST'])
def receive_product_image():
    if request.method == 'POST':
        # new plan: get all non-image info of Gohu, send back Gohu ID
        # then, send images with gohu id and save them to files with id name
        # when gohu is being pulled, send back those images with the gohu id
        # each user has own image folder with id as title

        user_id = request.headers.get('User-Id')
        gohu_id = request.headers.get('Gohu-Id')
        order_number = request.headers.get('Order-Number')
        image = request.data

        file_name = "Gohu{0}Product{1}Image.bin".format(gohu_id, order_number)
        with open(file_name, 'wb') as file:
            file.write(image)

        conn = sqlite3.connect("twangou.db")
        cursor = conn.cursor()
        cursor.execute('''UPDATE PRODUCTS SET PRODUCT_IMAGE = ? WHERE product_order = ? and gohu_id = ?''',
                       (file_name, order_number, gohu_id))
        conn.commit()

        '''user_folder_name = 'User' + str(user_id)
        gohu_folder_name = 'Gohu' + str(gohu_id)
        path_name = user_folder_name + '/' + gohu_folder_name
        with open((path_name + "/Product'{0}'.bin").format(order_number), 'wb') as file:
            file.write(image) '''

        if request.data:
            return "Received Product Image"
        else:
            return 'No data received in the POST request', 400


@app.route('/AddGohu/AddProduct', methods=['POST'])
def receive_product():
    if request.method == 'POST':
        # new plan: get all non-image info of Gohu, send back Gohu ID
        # then, send images with gohu id and save them to files with id name
        # when gohu is being pulled, send back those images with the gohu id
        parts = parse_message(request.data.decode("utf-8"), '|')
        name = parts[0]
        cost = parts[1]
        quantity = parts[2]
        order = parts[3]
        gohu_id = parts[4]
        conn = sqlite3.connect("twangou.db")
        cursor = conn.cursor()

        insert_product = "INSERT INTO PRODUCTS (name, quantity, cost, product_image, product_order, gohu_id) VALUES ('{0}', '{1}', " \
                         "'{2}', " \
                         "'{3}', '{4}', '{5}')".format(name, quantity, cost, '', order, gohu_id)
        cursor.execute(insert_product)
        if request.data:
            gohu_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return str(gohu_id)
        else:
            return 'No data received in the POST request', 400


@app.route('/AddGohu/AddCoverImage', methods=['POST'])
def receive_cover_image():
    if request.method == 'POST':
        # new plan: get all non-image info of Gohu, send back Gohu ID
        # then, send images with gohu id and save them to files with id name
        # when gohu is being pulled, send back those images with the gohu id
        # each user has own image folder with id as title

        gohu_id = request.headers.get('Gohu-Id')
        image = request.data

        file_name = "Gohu{0}Image.bin".format(gohu_id)
        with open(file_name, 'wb') as file:
            file.write(image)

        conn = sqlite3.connect("twangou.db")
        cursor = conn.cursor()
        cursor.execute('''UPDATE GOHUS SET COVER_IMAGE = ? WHERE gohu_id = ?''',
                       (file_name, gohu_id))
        conn.commit()
        '''user_folder_name = 'User' + str(user_id)
        gohu_folder_name = 'Gohu' + str(gohu_id)
        path_name = user_folder_name + '/' + gohu_folder_name

        os.mkdir(path_name)
        with open(path_name + '/CoverImage.bin', 'wb') as file:
            file.write(image) '''

        if request.data:
            return "Received Image"
        else:
            return 'No data received in the POST request', 400


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
        num_of_products = parts[3]

        conn = sqlite3.connect("twangou.db")
        create_gohus_table = "CREATE TABLE IF NOT EXISTS GOHUS(gohu_ID INTEGER PRIMARY KEY AUTOINCREMENT , " \
                             "title TEXT, description TEXT, cover_image TEXT, num_of_products INTEGER," \
                             "host_id INTEGER, FOREIGN KEY (host_id) REFERENCES users(user_id)); "
        cursor = conn.cursor()

        insert_gohu = "INSERT INTO GOHUS (TITLE, DESCRIPTION, COVER_IMAGE, HOST_ID, NUM_OF_PRODUCTS) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(
            title, description, '', user_id, num_of_products)
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

        # cursor.execute("DROP TABLE USERS;")
        # cursor.execute("DROP TABLE GOHUS;")
        # cursor.execute("DROP TABLE PRODUCTS;")
        # cursor.execute("DROP TABLE GOHU_PRODUCTS;")

        create_users_table = "CREATE TABLE IF NOT EXISTS USERS(USER_ID INTEGER PRIMARY KEY AUTOINCREMENT , " \
                             "USERNAME TEXT, PASSWORD TEXT);"
        cursor.execute(create_users_table)

        create_gohus_table = "CREATE TABLE IF NOT EXISTS GOHUS(gohu_ID INTEGER PRIMARY KEY AUTOINCREMENT , " \
                             "title TEXT, description TEXT, cover_image TEXT, num_of_products INTEGER," \
                             "host_id INTEGER, FOREIGN KEY (host_id) REFERENCES users(user_id)); "
        cursor.execute(create_gohus_table)

        create_products_table = "CREATE TABLE IF NOT EXISTS PRODUCTS(" \
                                "name TEXT, quantity INTEGER, cost REAL, product_image TEXT, product_order INTEGER, " \
                                "gohu_id INTEGER, FOREIGN KEY (gohu_id) REFERENCES gohus(gohu_id)); "
        cursor.execute(create_products_table)

        '''create_gohu_products_table = "CREATE TABLE IF NOT EXISTS GOHU_PRODUCTS(GOHU_PRODUCT_ID INTEGER PRIMARY KEY " \
                                     "AUTOINCREMENT , gohu_ID INTEGER, product_ID INTEGER, " \
                                     "FOREIGN KEY (gohu_id) REFERENCES gohus(gohuID), FOREIGN KEY (product_ID) REFERENCES " \
                                     "products(PRODUCT_ID));"; 
        cursor.execute(create_gohu_products_table) '''

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
                '''folder_name = 'User' + str(user_id)

                try:
                    os.mkdir(folder_name)
                except FileExistsError:
                    print(f"Directory '{folder_name}' already exists.") '''

                server_response = "Available|" + str(user_id)
                print(server_response)
        elif objective == "SignIn":
            username = parts[1]
            password = parts[2]

            user_id = check_credentials("username", "password", username, password, "users", cursor)

            if user_id != -1:
                server_response = str(user_id)
            else:
                server_response = "-1"
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
