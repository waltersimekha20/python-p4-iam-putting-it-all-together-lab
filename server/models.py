from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    serialize_rules=('-_password_hash', '-created_at', '-updated_at', '-recipes')

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    recipes = db.relationship('Recipe', backref='user', cascade='all, delete-orphan')

    @validates('username', _password_hash)
    def validate(self, key, value):
        if (len(value) < 1) or (value in db.session.query(User.username).all()):
            raise ValueError('Username expected')
        return value
    
    
    
    @hybrid_property
    def password_hash(self):
        raise AttributeError("Can't access password")
    
    @password_hash.setter
    def password_hash(self, password):
        before_hash = bcrypt.generate_password_hash(
            password.encode('utf-8')
        )
        self._password_hash = before_hash

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))
    
class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    serialize_rules = ('-created_at', '-updated_at', '-user.recipes')

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable = False)
    instructions = db.Column(db.String)
    minutes_to_complete= db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @validates('title', 'instructions')
    def validate(self, key, value):
        if key == 'title':
            if len(value) < 1:
                raise ValueError('Title must be present')
            return value
        
        if key == 'instructions':
            if len(value) <= 50:
                raise ValueError('Instruction should be 50 characters or more')
            return value