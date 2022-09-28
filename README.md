# Flask Checklist

- [ ] create a separate directory for each app.
- [ ] inside the directory for the app, run:

```bash
pipenv install flask=='2.0.3' pymysql flask-bcrypt werkzeug==2.0.3
```

- [ ] add [server.py](server.py) with the following content:
- - Flask instance (app), all controllers

```py
from flask_app import app
from flask_app.controllers import models

if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] add [flask_app](./flask_app/__init__.py) with the `__init__.py` file that contains the following:
- - Uncomment secret key and add random generated key:
- - Sites to generate password:
- - - https://www.lastpass.com/features/password-generator
- - - https://1password.com/password-generator/
```py
from flask_bcrypt import Bcrypt
from flask import Flask, flash, session
import re

app = Flask(__name__)

# app.secret_key = "" # INSERT GENERATED KEY FROM SITE
```

- [ ] add [mysqlconnection.py](./flask_app/config/mysqlconnection.py) to the `config` directory inside the `flask_app` package. It should contain the following:

```py
import pymysql.cursors

class MySQLConnection:
    def __init__(self, db):
        # ! If on mac, change password to 'rootroot'
        connection = pymysql.connect(host = 'localhost',
                                    user = 'root', 
                                    password = 'root',
                                    db = db,
                                    charset = 'utf8mb4',
                                    cursorclass = pymysql.cursors.DictCursor,
                                    autocommit = True)

        self.connection = connection
    def query_db(self, query:dict, data=None):
        with self.connection.cursor() as cursor:
            try:
                query = cursor.mogrify(query, data)
                print("Running Query:", query)
                executable = cursor.execute(query, data)
                if query.lower().find("insert") >= 0:
                    self.connection.commit()
                    return cursor.lastrowid
                elif query.lower().find("select") >= 0:
                    result = cursor.fetchall()
                    return result
                elif query.lower().find("update") >= 0:
                    result = data['id']
                    return result
                else:
                    self.connection.commit()
            except Exception as e:
                print("Something went wrong", e)
                return False
            finally:
                self.connection.close() 

def connectToMySQL(db):
    return MySQLConnection(db)
```

- [ ] add the models for the application inside the `models` directory. Each non-relational table in the database should have a [model](flask_app/models/model.py). A generic model should look like this:
- - Set `DATABASE` to filename of the database (usually something_schmea)
- - Set `PRIMARY_TABLE` to the name of the primary table
- - If using a secondary model (such as the ninjas in dojos and ninjas), uncomment the 3rd from / import and edit `SECONDARY_MODEL` to be the correct model file name.
- - If using a one to many relationship, uncomment the `SECONDARY_TABLE` and set it to the name of the secondary table. Also ctrl+F "CHANGE THIS" and edit `model2.Model2Class` to match your secondary model.

```py
from flask import flash
from flask_app.config.mysqlconnection import connectToMySQL
# from flask_app.models import SECONDARY_MODEL # The many model
import re

DATABASE = 'database_file'
PRIMARY_TABLE = 'primary_table_name'
# SECONDARY_TABLE = 'table2_name'

## Toggle to run all debug statements to track data flow
## True = On, False = Off
debug = False

class Model:
    def __init__(self, data:dict) -> None:
        ## INSTANCE ATTRIBUTES SHOULD BE SAME AS TABLE COLUMNS
        self.id = data['id']
        self.col1 = data['col1']
        self.col2 = data['col2']
        self.col3 = data['col3']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.many = [] # if many to one, store many here ## Ex: Dojo and Ninjas

    # ! READ/RETRIEVE/VALIDATE
    @classmethod
    def get_all(cls) -> list:
        query = f"SELECT * FROM {PRIMARY_TABLE};"
        results = connectToMySQL(DATABASE).query_db(query)
        # Make list to return
        models_list = []
        for model in results:
            # Add instances of the class to the list
            models_list.append( cls(model) )
        # return list of instances of the class
        return models_list

    ## Provide id in dict, query by id, get back 1 user info
    @classmethod
    def get_one(cls, data:dict) -> object:
        query = f"SELECT * FROM {PRIMARY_TABLE} WHERE id = %(id)s;"
        results = connectToMySQL(DATABASE).query_db(query, data)
        return cls(results[0])

    ## Provide email in dict, query by email, get back 1 user info or False
    @classmethod
    def get_by_email(cls,data:dict) -> object or bool:
        query = f"SELECT * FROM {PRIMARY_TABLE} WHERE email = %(email)s;"
        result = connectToMySQL(DATABASE).query_db(query,data)
        # Return an instance class of User if true, else return False
        return (result ? cls(result[0]) : False)

    ## Provide column_name in dict, query by column_name, get back 1 user info or False
    @classmethod
    def get_by_col(cls, data:dict) -> object or bool:
        # Only the first key,value pair combo from dict will be checked
        query = f"SELECT * FROM {PRIMARY_TABLE} WHERE { list(data.keys())[0] } = %(email)s;"
        result = connectToMySQL(DATABASE).query_db(query,data)
        # Return an instance class of User if true, else return False
        return cls(result[0]) if result else False

    # ! Many To One, skip otherwise
    @classmethod
    def get_single_with_many( cls , data:dict ) -> object:
        query = f"SELECT * FROM {PRIMARY_TABLE} LEFT JOIN {SECONDARY_TABLE} ON {SECONDARY_TABLE}.{PRIMARY_TABLE[:-1]}_id = {PRIMARY_TABLE}.id WHERE {PRIMARY_TABLE}.id = %(id)s;"
        results = connectToMySQL(DATABASE).query_db( query , data )
        model = cls( results[0] )
        if debug:
            print(results[0])
        for row in results:
            model2_data = {
                "id" : row[f"{SECONDARY_TABLE}.id"],
                "col1" : row["col1"],
                "col2" : row["col2"],
                "col3" : row["col3"],
                f"{PRIMARY_TABLE[:-1]}_id" : row[f"{PRIMARY_TABLE[:-1]}_id"],
                "created_at" : row[f"{SECONDARY_TABLE}.created_at"],
                "updated_at" : row[f"{SECONDARY_TABLE}.updated_at"]
            }
            ### CHANGE THIS TO INCLUDE CORRECT SECONDARY MODEL 
            model.SECONDARY_TABLE.append( model2.Model2Class( model2_data ) )
            ### CHANGE THIS TO INCLUDE CORRECT SECONDARY MODEL 
        return model

    # ! CREATE
    @staticmethod
    def save(data:dict) -> int:
        query = f"INSERT INTO {PRIMARY_TABLE} ( col1, col2, col3 ) VALUES ( %(col1)s, %(col2)s, %(col3)s );"
        return connectToMySQL(DATABASE).query_db( query, data )

    # ! Validate Model/Registration
    @classmethod
    def validate_model(cls, user:dict) -> bool:
        is_valid = True
        if len(user['first_name']) < 2 or not user['first_name'].isalpha():
            if debug:
                print(f"First name: {user['first_name']}")
                print(f"First name length: {len(user['first_name'])}")
                print(f"First name isalpha: {user['first_name'].isalpha()} ")
            flash("First name must be at least 2 characters an only letters.", "register")
            is_valid = False
        if len(user['last_name']) < 2 or not user['last_name'].isalpha():
            if debug:
                print(f"Last name: {user['last_name']}")
                print(f"Last name length: {len(user['last_name'])}")
                print(f"Last name isalpha: {user['last_name'].isalpha()} ")
            flash("Last name must be at least 2 characters an only letters.", "register")
            is_valid = False
        if not cls.valid_email_format(user):
            flash("Invalid email address.", "register")
            is_valid = False
        if cls.email_in_db(user):
            flash("Email in use already.", "register")
            is_valid = False
        if not cls.valid_password(user):
            is_valid = False
        return is_valid

    # Validate email format. Ex: characters @Symbol . letters
    @staticmethod
    def valid_email_format( data:dict ) -> bool:
        # create regex pattern
        regex = r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$'
        match = re.search(regex, data['email'])
        if debug:
            print(f"Email: {data['email']}")
            print(match)
        return True if match else False

    # Validate if user exists in database by email
    @classmethod
    def email_in_db( cls, data: dict ) -> bool:
        users_emails = {user['email'] for user in cls.get_all()}
        # set comprehension, make a set (unique values) of all user emails
        # from the users in User.get_all()
        if debug:
            print(f"Users Email List: {users_emails}")
            print(f"User Email: {data['email']}")

        return True if data['email'] in users_emails else False
        # while the total number of users is small and total run time between list and set
        # isn't going to matter on this scale, it will when size gets large enough.
        # https://stackoverflow.com/a/40963434
        # https://stackoverflow.com/a/68438122

    # Validate Password on several
    @staticmethod
    def valid_password(user:dict) -> bool:
        if debug:
            print("Starting password validation.")
        # Checks matching passwords, length, contains upper, lower and digit
        is_valid = True
        if debug:
            print(f"password: {user['password']}")
            print(f"password confirm: {user['password-confirm']}")
        if user['password'] != user['password-confirm']:
            flash("Passwords do not match.", "register")
            is_valid = False
        if len(user['password']) < 8:
            flash("Password must be at least 8 characters long.", "register")
            is_valid = False
        ## If you want to check uppercase, lowercase and digit
        hasUpper = hasLower = hasDigit = False
        charInd = 0
        while (not (hasUpper and hasLower and hasDigit)) and (charInd < len(user['password'])):
            if debug:
                print("Inside password while loop.")
            # while TRUE and TRUE
            # not (A and B and C) == (not A) or (not B) or (not C)
            # True or True or True == True or False or False == True
            if user['password'][charInd].isupper(): hasUpper = True
            if user['password'][charInd].islower(): hasLower = True
            if user['password'][charInd].isdigit(): hasDigit = True
            charInd += 1
        if debug:
            print("End password while loop")
        if not (hasUpper and hasLower and hasDigit):
            flash("Password must contain at least 1 lower character, 1 upper character and a digit.", "register")
            is_valid = False
        ## Skip to here if you don't need the upper, lower, digit (comment out above)
        return is_valid

    # ! UPDATE
    @classmethod
    def update(cls,data:dict) -> int:
        query = f"UPDATE {PRIMARY_TABLE} SET col1=%(col1)s, col2=%(col2)s, col3=%(col3)s WHERE id = %(id)s;"
        return connectToMySQL(DATABASE).query_db(query,data)

    # ! DELETE
    @staticmethod
    def del_one(data: dict) -> None:
        query = f"DELETE FROM {PRIMARY_TABLE} WHERE id = %(id)s;"
        return connectToMySQL(DATABASE).query_db(query, data)
```

- [ ] add the controllers for the app routes inside [flask_app/controllers/models.py](flask_app/controllers/models.py):

```py
from flask import render_template, request, redirect
from flask_app import app, session, flash, Bcrypt
from flask_app.models.model import Model

## Toggle to run all debug statements to track data flow
## True = On, False = Off
debug = False

# Make instance of Bcrypt
bcrypt = Bcrypt(app)

# ! ////// READ/RETRIEVE //////
# TODO ROOT ROUTE
# TODO READ ALL
@app.route('/')
@app.route('/models')
def models():
    return render_template("models.html",models=Model.get_all())

# TODO READ ONE
@app.route('/model/show/<int:id>')
def show(id):
    data ={ 
        "id":id
    }
    return render_template("show_model.html",model=Model.get_one(data))

# TODO LOGIN
# # Login
@app.route('/login', methods=['POST'])
def login():
    data = { 'email' : request.form['email'] }
    user = User.get_by_col(data)
    if debug:
        print(f"Request Form dict: {request.form}")
        print(f"Hashed password: {user.password}")
        print(f"Entered password: {request.form['password']}")

    if not ( User.valid_email_format(data) and User.email_in_db(data) ):
        # De Morgans Law:
        # not (A and B) == (not A) or (not B)
        flash("Invalid credentials", "login")
        return redirect('/')
    elif not bcrypt.check_password_hash(user.password, request.form['password']):
        # check pw (hashed, unhashed)
        flash("Invalid credentials", "login")
        return redirect('/')
    else:
        session['user_id'] = user.id
        session['first_name'] = user.first_name
        session['logged_in'] = True
        return redirect('/success')

# ! ////// CREATE  //////
# TODO CREATE REQUIRES TWO ROUTES:
# TODO ONE TO DISPLAY THE FORM:
@app.route('/model/new')
def new():
    return render_template("new_model.html")

# TODO ONE TO HANDLE THE DATA FROM THE FORM
@app.route('/model/create',methods=['POST'])
def create():
    if debug:
        print(f"Request Form dict: {request.form}")
    Model.save(request.form)
    return redirect('/models')

# TODO REGISTER USER WITH VALIDATION
@app.route('/register/create', methods=['POST'])
def create():
    if debug:
        print(f"Request Form dict: {request.form}")
    if not Model.validate_model(request.form):
        return redirect('/')
    
    pw_hash = bcrypt.generate_password_hash(request.form['password'])
    if debug:
        print(f"Password Hash: {pw_hash}")
    # Ensure keys are correct
    data = {
        "first_name": request.form['first_name'],
        "last_name": request.form['last_name'],
        "email": request.form['email'],
        "password" : pw_hash
    }
    if debug:
        print(f"Registration data dict: {data}")
    user_id = Model.save(data)
    # Add user to session
    session['user_id'] = user_id
    session['first_name'] = data['first_name']
    session['logged_in'] = True
    # ! Auto login after registration, go to dashboard? main page?
    return redirect('/models')



# ! ///// UPDATE /////
# TODO UPDATE REQUIRES TWO ROUTES
# TODO ONE TO SHOW THE FORM
@app.route('/model/edit/<int:id>')
def edit(id):
    data ={ 
        "id":id
    }
    return render_template("edit_model.html",model=Model.get_one(data))

# TODO ONE TO HANDLE THE DATA FROM THE FORM
@app.route('/model/update',methods=['POST'])
def update():
    ## Redirect to all models
    # Model.update(request.form)
    # return redirect('/models')
    
    ## OR

    ## Redirect to updated model
    # UPDATE returns ID of updated model or false
    id = Model.update(request.form)
    if not id:
        flash('There was an error updating the model.')
        return redirect('/models')
    return redirect(f'/model/show/{id}')

# ! ///// DELETE //////
@app.route('/model/destroy/<int:id>')
def destroy(id):
    data ={ 'id': id }
    Model.destroy(data)
    # Redirect show all or index?
    return redirect('/models')

# ! ///// CUSTOM 404 HANDLING //////
@app.errorhandler(404)
def fourZeroFour(err):
        return "<h1 style='margin:50px auto; color:red'>Sorry!\
                No response. Try another address.</h1>"
```

- [ ] add the view of MVC:
  - [ ] add [models.html](flask_app/templates/models.html):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- CSS only -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <title>models</title>
</head>
<body>
    <h1 class="text-center">Here are our models!!!</h1>
    <table class="table table-hover">
        <thead>
            <tr>
                <th>Column One</th>
                <th>Column Two</th>
                <th>Column Three</th>
                <th>Created At</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for model in models %}
            <tr>
                <td>{{ model.column1 }}</td>
                <td>{{ model.column2 }}</td>
                <td>{{ model.column3}}</td>
                <td>{{ model.created_at.strftime("%b %d %Y") }}</td>
                <td>
                    <a href="/model/show/{{ model.id }}">Show</a> |
                    <a href="/model/edit/{{ model.id }}">Edit</a> |
                    <a href="/model/destroy/{{ model.id }}">Delete</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <a href="/model/new" class="btn btn-primary">Add a model</a>
</body>
</html>
```

  - [ ] add [new_model.html](flask_app/templates/new_model.html):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- CSS only -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <title>Create model</title>
</head>
<body>

    <form action="/model/create" method="post" class="col-6 mx-auto">
        <h2 class="text-center">Add model</h2>
        <div class="form-group">
            <label for="column1">column1:</label>
            <input type="text" name="column1"  class="form-control">
        </div>
        <div class="form-group">
            <label for="column2">column2:</label>
            <input type="text" name="column2"  class="form-control">
        </div>
        <div class="form-group">
            <label for="column3">column3:</label>
            <input type="text" name="column3"  class="form-control">
        </div>
        <input type="submit" value="Add model" class="btn btn-success">
    </form>
</body>
</html>
```

  - [ ] add [show_model.html](flask_app/templates/show_model.html):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <title>model</title>
</head>
<body>
    <h2 class="text-center">model {{model.id}}</h2>
    <p>column1 {{model.column1}}</p>
    <p>column2: {{model.column2}}</p>
    <p>column3: {{model.column3}}</p>

    <p>Created ON: {{model.created_at.strftime("%b %d %Y")}}</p>
    <p>Last Updated: {{  model.updated_at.strftime("%b %d %Y")}}</p>
</body>
</html>
```

  - [ ] add [edit_model.html](flask_app/templates/edit_model.html):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- CSS only -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <title>Edit model</title>
</head>
<body>

    <form action="/model/update" method="post" class="col-6 mx-auto">
        <h2 class="text-center">Edit {{model.id}}</h2>
        <input type="hidden" name="id" value={{model.id}}>
        <div class="form-group">
            <label for="column1">column1:</label>
            <input type="text" name="column1"  class="form-control" value="{{model.column1}}">
        </div>
        <div class="form-group">
            <label for="column2">column2:</label>
            <input type="text" name="column2" class="form-control" value="{{model.column2}}">
        </div>
        <div class="form-group">
            <label for="column3">column3:</label>
            <input type="text" name="column3"  class="form-control" value="{{model.column3}}">
        </div>
        <input type="submit" value="Update model" class="btn btn-success">
    </form>
</body>
</html>
```