from flask import Flask, render_template, send_from_directory, redirect, url_for
from flask_login import LoginManager, login_required
from shiny import App as ShinyApp
from elite_ops_dashboard import app as shiny_app
from models import User
from config import Config
from auth import auth
from pathlib import Path
import threading

static_dir = Path(__file__).parent / "static"

print(f"Static directory path: {static_dir}")
print(f"Does static directory exist? {static_dir.exists()}")
print(f"Does styles.css exist? {(static_dir / 'styles.css').exists()}")

app = Flask(__name__, static_folder=str(static_dir))
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect('http://localhost:8000')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

def run_shiny():
    shiny_app.run(port=8000)

if __name__ == '__main__':
    print("Starting Shiny app...")
    shiny_thread = threading.Thread(target=run_shiny)
    shiny_thread.start()
    
    print("Starting Flask app...")
    app.run(debug=True, use_reloader=False)
    