from flask import Flask, Blueprint, render_template, request, Response
from flask_login import LoginManager, login_required, current_user
from shiny import App as ShinyApp
from elite_ops_dashboard import app_ui, server
from auth import auth
from models import User
from config import Config
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response
import shiny

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('dashboard.html')

app.register_blueprint(auth)
app.register_blueprint(main)

# Create Shiny app
shiny_app = ShinyApp(app_ui, server)

# Wrap Shiny app in a WSGI application
def shiny_wsgi(environ, start_response):
    path = environ.get('PATH_INFO', '')
    if path.startswith('/dashboard'):
        environ['PATH_INFO'] = path[len('/dashboard'):]
        return shiny_app(environ, start_response)
    return app(environ, start_response)

# Create a dispatcher middleware
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/dashboard': shiny_wsgi
})

if __name__ == '__main__':
    app.run(debug=True)