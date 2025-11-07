"""Flask application factory."""
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from config.settings import config
from app.models.base import db
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize SocketIO globally
socketio = SocketIO()

def create_app(config_name='development'):
    """
    Application factory pattern.
    
    Args:
        config_name: Configuration to use (development/production)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": app.config['SOCKETIO_CORS_ALLOWED_ORIGINS']}})
    
    # Initialize database
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        from app.models import Base
        Base.metadata.create_all(bind=db.session.get_bind())
    
    # Initialize SocketIO
    socketio.init_app(
        app,
        cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE'],
        logger=True,
        engineio_logger=True
    )
    
    # Register blueprints
    from app.routes import api_bp, socketio_events
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize LangSmith tracking
    if app.config['LANGSMITH_TRACING']:
        os.environ['LANGSMITH_TRACING_V2'] = 'true'
        os.environ['LANGSMITH_API_KEY'] = app.config['LANGSMITH_API_KEY']
        os.environ['LANGSMITH_PROJECT'] = app.config['LANGSMITH_PROJECT']
        os.environ['LANGSMITH_ENDPOINT'] = app.config['LANGSMITH_ENDPOINT']
        logging.info(f"LangSmith tracking enabled for project: {app.config['LANGSMITH_PROJECT']}")
    
    # Health check endpoint
    @app.route('/health')
    def health():
        from datetime import datetime
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    
    logging.info(f"Application initialized in {config_name} mode")
    return app
