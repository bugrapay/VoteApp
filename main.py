from flask import Flask, request, jsonify, redirect, url_for, render_template, current_app
from flask_jwt_extended import create_access_token, JWTManager, create_refresh_token, jwt_required
from flask_sqlalchemy import SQLAlchemy
from email.message import EmailMessage
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3, ssl, smtplib, jwt, datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/bugra/Desktop/Coding/VoteApp/database.db'
db = SQLAlchemy(app)
app.config['JWT_SECRET_KEY'] = 'alttab'
jwt = JWTManager(app)


# Kullanıcı Veritabanı işleme
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    followers = db.relationship('Followers', backref='user', lazy=True)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=True)

    # Relationships
    followers = db.relationship('Followers', foreign_keys='Followers.followed_id', backref='followed', lazy='dynamic')
    following = db.relationship('Followers', foreign_keys='Followers.follower_id', backref='follower', lazy='dynamic')


#takip ağı
class Followers(db.Model):
    __tablename__ = 'followers'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime, nullable=False)


# Giriş sayfası
@app.route('/login', methods=['POST'])
def login():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()

    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username:
        return jsonify({"msg": "Kullanıcı Adı giriniz"}), 400
    if not password:
        return jsonify({"msg": "Parola giriniz"}), 400

    # kullanıcı kimlik kontrolü
    for row in rows:
        if row[1] == username and row[5] == password:

            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
            return jsonify({"msg": "Giriş Başarılı!"}), 200
            break
        refresh_token = create_refresh_token({"username": username})
        return {
            "access_token": access_token.decode(),
            "refresh_token": refresh_token.decode(),
        }

    conn.close()

    # erişim tokeni oluşturma

    # return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Kullanıcı adı veya parola hatalı!"}), 400


# Kullanıcı listesi
@app.route("/users")
def user_list():
    users = db.session.execute(
        db.select(Users).order_by(Users.username)).scalars()
    # return render_template("user/list.html", users=users)
    return jsonify(users=users)


# Kullanıcı Oluşturma
@app.route("/users/create", methods=["GET", "POST"])
def user_create():
    if request.method == "POST":
        user = Users(
            name=request.form["name"],
            surname=request.form["surname"],
            username=request.form["username"],
            email=request.form["email"],
            password=request.form["password"],
            location=request.form["location"]

        )
        db.session.add(user)
        db.session.commit()
        # return redirect(url_for("user_detail", id=user.id))

    # return render_template("user/create.html")
    # return redirect(url_for("user_detail", id=user.id))
    return jsonify({"msg": "Kayıt Başarılı!"}), 200



# Kullanıcı bilgileri
@app.route("/user/<int:id>")
@jwt_required()
def user_detail(id):
    user = db.get_or_404(Users, id)
    # return render_template("user/detail.html", user=user)
    return jsonify(user=user)


# Kullanıcı silme
@app.route("/user/<int:id>/delete", methods=["GET", "POST"])
@jwt_required()
def user_delete(id):
    user = db.get_or_404(Users, id)

    if request.method == "POST":
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for("user_list"))

    return render_template("user/delete.html", user=user)


# Kullanıcı güncelleme
@app.route("/update/<int:id>", methods=["GET", "POST"])
@jwt_required()
def update_user(id):
    user_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        user_to_update.name = request.form["name"]
        user_to_update.surname = request.form["surname"]
        user_to_update.email = request.form["email"]
        user_to_update.location = request.form["location"]
        user_to_update.password = request.form["password"]
        try:
            db.session.commit()
            return jsonify("Kullanıcı bilgileri başarıyla güncellendi")
        except:
            return "Kullanıcı bilgileri güncellenirken sorun oluştu..."

    return


#takip etme
@app.route('/users/<int:user_id>/follow', methods=['POST'])
def follow_user(user_id):
    # get the user who is following (e.g. from the authentication token)
    follower = get_current_user()
    
    # get the user who is being followed
    followed = Users.query.get(user_id)
    
    # create a new relationship in the database
    follower.followed.append(followed)
    db.session.commit()
    
    # return a response indicating success
    return jsonify({'message': f'You are now following {followed.username}!'})


#takipten çıkma
@app.route('/users/<int:user_id>/follow', methods=['DELETE'])
def unfollow_user(user_id):
    # get the user who is following (e.g. from the authentication token)
    follower = get_current_user()
    
    # get the user who is being unfollowed
    followed = Users.query.get(user_id)
    
    # remove the relationship from the database
    follower.followed.remove(followed)
    db.session.commit()
    
    # return a response indicating success
    return jsonify({'message': f'You have unfollowed {followed.username}.'})



def get_current_user():
    # Get the JWT token from the request header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    token = auth_header.split(' ')[1]

    # Decode the JWT token to get the user ID
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
    except jwt.InvalidTokenError:
        return None

    # Retrieve the user from the database using the user ID
    user = Users.query.get(user_id)
    return user




if __name__ == '__main__':
    app.run(debug=True)
