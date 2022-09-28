from wsgiref import validate
from flask import render_template, redirect, session, request, flash
from flask_app import app
from flask_app.models.user import User
from flask_app.models.trainer import Trainer

@app.route('/trainer')
def create_trainer():

    return render_template("trainer.html")#, user_in_db=user_in_db)

@app.route('/trainer/submit', methods=['POST'])
def submit_new_with_trainer():
    if "user_id" not in session:
        return redirect('/login')
    data = {
        "first_name": request.form["first_name"],
        "last_name": request.form["last_name"],
        "plans": request.form["plans"],
        "date": request.form["date"],
        "comment": request.form["comment"],
        "users_id": session["user_id"]       
    }

    if not Trainer.validate_trainer(data):
        return redirect("/trainer/new")

    Trainer.save(data)
    return redirect('/')


@app.route('/show/trainer/<int:id>')
def show_trianer(id):
    data = {
        "id": session['user_id']
    }
    user_in_db = User.get_one_by_id(data)

    one_trainer = Trainer.get_one_trainer({"id":id})
    all_trainers = Trainer.get_all()

    user_data = {
        "id": one_trainer.users_id   
    }

    user = User.get_one_by_id(user_data)
    return render_template("show.html", user_in_db=user_in_db, all_trainers=all_trainers, one_trainer=one_trainer, user=user)


@app.route('/delete/<int:id>')
def delete_trainer(id):
    # print(f"****** delete  {id} *******")

    data = {
        "id":id
    }
    Trainer.delete_trianer(data)
    return redirect("/main")       # <<---- show page NEW NAMING ACCOUNT

@app.route('/edit/trianer/<int:id>')
def edit_trainer(id):
    one_trainer = Trainer.get_one_trainer({"id":id})

    data = {
        "id": session['user_id']
    }
    user_in_db = User.get_one_by_id(data)
    return render_template("edit.html", one_trainer=one_trainer, user_in_db=user_in_db)



