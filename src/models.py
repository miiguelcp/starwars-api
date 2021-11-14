from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    favorites = db.relationship('Favorite', backref='user', uselist = True)


    def serialize(self):
        return {
            "username": self.username,
            "id": self.id

        }


    @classmethod
    def create(cls, users):
        try:
            new_user = cls(**users)
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except Exception as error:
            db.session.rollback()
            return None



class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    url = db.Column(db.String(125), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint(
        'user_id',
        'url',
        name='unique_favorite_for_user'
    ),)


    def serialize(self):
        return{
            "user_id": self.user_id,
            "swapi_url": self.url,
            "url": "/detail/" + self.url.replace("https://www.swapi.tech/api/", ""),
            "id": self.id,
            "favoriteName": self.name
        }

    def new(self):
        db.session.add(self)
        try:
            db.session.commit()
            return True
        except Exception as error:
            db.session.rollback()
            return False



    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
            return True
        except Exception as error:
            db.session.rollback()
            return False



class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False, unique=True)
    birth_day = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    gender= db.Column(db.String(30), nullable=False)
    color_skin = db.Column(db.String(40), nullable=False)