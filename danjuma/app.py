from flask import Flask, render_template
from flask_cors import CORS
from models.database import init_db
from routes.api import api_bp
from scheduler import start_scheduler
from config import Config
import os

def create_app():
    # Set up static folder path
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
    app.config.from_object(Config)
    CORS(app)

    # Initialize DB
    init_db()

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Start the background scheduler
    start_scheduler()

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

app = create_app()

if __name__ == '__main__':
    import sys
    # Force unbuffered output for better logging on Render
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
