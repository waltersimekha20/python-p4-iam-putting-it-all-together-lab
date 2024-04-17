#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource, reqparse
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe



class Signup(Resource):
    def __init__(self) -> None:
        self.post_parser = reqparse.RequestParser()
        self.post_parser.add_argument(
            'username', required = True,
            help='The user\'s name'
        )
        self.post_parser.add_argument(
            'password', required=True,
            help='The user\'s password'
        )
        self.post_parser.add_argument(
            'bio', required=True,
            help='User\'s Bio'
        )
        self.post_parser.add_argument(
            'image_url', required=True,
            help='The user\'s Image Url'
        )

    def post(self):
        args = self.post_parser.parse_args()
        user = User(
            username=args.username,
            bio=args.bio,
            image_url=args.image_url,
        )
        user.password_hash = args.password

        db.session.add(user)

        try: 
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username already exists']}, 422


        if user.id:
            session['user_id'] = user.id
            response = make_response(user.to_dict(), 201)

            return response
        
        return {'errors': ['Bad Request']}, 422

class CheckSession(Resource):
    def get(self):
        if 'user_id' in session:
            user = User.query.filter_by(id=session['user_id']).first()

            if user:
                return make_response(user.to_dict(), 200)
            
        return {'errors': ['User not logged in']}, 401

class Login(Resource):
    def __init__(self) -> None:
        self.login_parser = reqparse.RequestParser()
        self.login_parser.add_argument(
            'username', required = True,
            help='The user\'s name'
        )
        self.login_parser.add_argument(
            'password', required=True,
            help='The user\'s password'
        )

    def post(self):
        args = self.login_parser.parse_args()
        user = User.query.filter_by(username=args.username).first()

        if user:
            if user.authenticate(args.password):
                session['user_id'] = user.id
                return make_response(user.to_dict(), 200)
            
        return make_response({'errors': ['Invalid username or password']}, 401)
    
class Logout(Resource):
    def delete(self):
        # print(session.get('user_id'))
        if session.get('user_id'):
            session['user_id'] = None

            return make_response({}, 204)  
        
        return {'errors': ['Log in']} , 401
    

class RecipeIndex(Resource):
    def __init__(self) -> None:
        self.recipe_parser = reqparse.RequestParser()
        self.recipe_parser.add_argument(
            'title', required=True,
            help="The Recipe's Title"
        )
        self.recipe_parser.add_argument(
            'instructions', required=True,
            help="The Recipe's Instructions"
        )
        self.recipe_parser.add_argument(
            'minutes_to_complete', required=True,
            type=int,help="The Recipe's time to read"
        )

    def get(self):
        if 'user_id' in session:
            recipes_dict = [recipe.to_dict() for recipe in Recipe.query.all()]

            return make_response(recipes_dict, 200)

        return {'errors':['User is not logged in']}, 401
    
    def post(self):
        if 'user_id' in session:
            args = self.recipe_parser.parse_args()
            recipe = Recipe(
                title=args.title,
                instructions=args.instructions,
                minutes_to_complete= args.minutes_to_complete,
            )
            recipe.user_id = session['user_id']

            db.session.add(recipe)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return {'errors': ['Missing title']}, 422
            
            return make_response(recipe.to_dict(), 201)
        
        return {'errors': ["User is not logged in"]}
        

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
     