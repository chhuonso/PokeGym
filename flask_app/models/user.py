from flask_app.config.mysqlconnection import connectToMySQL
from flask_app import flash, re


DATABASE = "pokegym"
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 


class User:
    def __init__(self, data):
        self.id = data['id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']

    #CHECKS and Validate REGISTER INFO
    @staticmethod
    def validate_user(user): 
        is_valid = True # ! assume this is true
        if len(user['first_name']) < 2:
            flash("Name must be at least 2 characters.")
            is_valid = False
        if len(user['last_name']) < 2:
            flash("Name must be at least 2 characters.")
            is_valid = False
        if not EMAIL_REGEX.match(user['email']): 
            flash("Invalid email address!")
            is_valid = False
        if user['password'] != user['confirm_password']:
            flash("Passwords do not match")
            is_valid = False
        return is_valid

    # ADD users to the database
    @classmethod
    def save(cls, data):
        query = "INSERT INTO users (first_name, last_name, email, password,created_at, updated_at) VALUES (%(first_name)s,%(last_name)s,%(email)s,%(password)s,NOW(),NOW());"
        return connectToMySQL(DATABASE).query_db(query,data)

    #Find the users by email
    @classmethod
    def get_one_by_email(cls,data):
        query = "SELECT * FROM users WHERE email = %(email)s;"
        results = connectToMySQL(DATABASE).query_db(query,data)  
        if len(results) < 1:
            return False
        return cls(results[0])   

    #Find the users by id
    @classmethod
    def get_one_by_id(cls,data):
        query = "SELECT * FROM users WHERE id = %(id)s;"
        results = connectToMySQL(DATABASE).query_db(query,data)
        return cls(results[0])