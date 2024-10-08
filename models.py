from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        users = User.get_users()
        return users.get(int(user_id))

    @staticmethod
    def get_by_username(username):
        users = User.get_users()
        return next((user for user in users.values() if user.username == username), None)

    @staticmethod
    def get_users():
        return {
            1: User(1, 'user1', generate_password_hash('password1')),
            2: User(2, 'user2', generate_password_hash('password2')),
        }

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)