from wsgiref import validate
from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash
from flask_app.models.user import User

DATABASE = "pokegym"

class Trainer: 
    def __init__(self, data):
        self.id = data["id"]
        self.first_name = data["first_name"]
        self.lastname = data["last_name"]
        self.plans = data["plans"]
        self.date = data["date"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.comment = data["comment"]
        self.poster = None
    

    # The validate on the form
    @staticmethod
    def validate_trainer(trainer_form): 
        is_valid = True # ! assume this is true

        if len(trainer_form['first_name']) < 2:
            flash("Must input first name.")
            is_valid = False
        if len(trainer_form['email']) < 2:
            flash("Must input last name.")
            is_valid = False
        if len(trainer_form['date']) < 2: 
            flash("Must schedule a date.")
            is_valid = False
        return is_valid


    @classmethod    
    def get_all(cls):
        query = "SELECT * FROM trainers  JOIN users ON users_id = trainers.users_id"    ####<----pain
        results = connectToMySQL(DATABASE).query_db(query)


        all_trainers = []     

        for trainer in results:         
            single_trainer = cls(trainer)  

            user_data = {
                "id": trainer["users.id"],
                "first_name": trainer["first_name"],
                "last_name": trainer["last_name"],
                "email": trainer["email"],
                "password": trainer["password"],
                "created_at": trainer["users.created_at"],
                "updated_at": trainer["users.updated_at"]
            }
            single_trainer.poster = User(user_data)
            all_trainers.append(single_trainer)
        return all_trainers


    #CRUD
    @classmethod
    def save(cls, data):
        query = "INSERT INTO trainers (first_name,last_name,plans,date,created_at,updated_at,users_id) VALUES(%(first_name)s,%(last_name)s, %(plans)s,%(date)s,NOW(),NOW(),%(comment)s,%(users_id)s)"

        return connectToMySQL(DATABASE).query_db(query, data)

    @classmethod
    def get_one_trainer(cls, data):
        query = "SELECT * FROM trainers  WHERE id=%(id)s"
        results = connectToMySQL(DATABASE).query_db(query, data)
        
        one_trianer = cls(results[0])
        return one_trianer
    
    @classmethod
    def edit_trainer(cls, data):
        query = "UPDATE trainers SET first_name=%(first_name)s, last_name=%(last_name)s, plans=%(plans)s, date=%(date)s, updated_at=NOW() WHERE id=%(id)s"

        return connectToMySQL(DATABASE).query_db(query, data)
    
    @classmethod
    def delete_trainer(cls, data):
        query = "DELETE FROM trainers WHERE id=%(id)s"

        return connectToMySQL(DATABASE).query_db(query, data)
    

