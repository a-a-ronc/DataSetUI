from flask import Flask, render_template, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_required, current_user
from elite_ops_dashboard import create_app as create_shiny_app
from models import User
from config import Config
from auth import auth
from pathlib import Path
from shiny import App
import threading

import pandas as pd

static_dir = Path(__file__).parent / "static"
print(f"Static directory path: {static_dir}")
print(f"Does static directory exist? {static_dir.exists()}")
print(f"Does styles.css exist? {(static_dir / 'styles.css').exists()}")
#######################################################################################
static_dir = Path(__file__).parent / "static"
print(f"Static directory path: {static_dir}")
print(f"Does static directory exist? {static_dir.exists()}")
print(f"Does styles.css exist? {(static_dir / 'styles.css').exists()}")

# Add debugging for CSV file
csv_path = Path(__file__).parent / 'transaction_data.csv'
print(f"CSV file path: {csv_path}")
print(f"Does CSV file exist? {csv_path.exists()}")

if csv_path.exists():
    df = pd.read_csv(csv_path, nrows=1)  # Read just the first row to get column names
    print("Columns in the CSV file:")
    print(df.columns.tolist())
######################################################################################
app = Flask(__name__, static_folder=str(static_dir))
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

shiny_app = None
shiny_thread = None

def run_shiny(username):
    global shiny_app
    shiny_app = create_shiny_app(username, str(static_dir))
    shiny_app.run(port=8000)

@app.route('/')
@login_required
def index():
    global shiny_thread
    if shiny_thread is None or not shiny_thread.is_alive():
        username = current_user.username if current_user.is_authenticated else "Guest"
        shiny_thread = threading.Thread(target=run_shiny, args=(username,), daemon=True)
        shiny_thread.start()
    return redirect('http://localhost:8000')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, use_reloader=False)