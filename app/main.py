import logging

from flask import Flask
from .config.settings import (
    PRODUCTION_SERVER_PORT,
    DEV_SERVER_PORT,
    REQUEST_TIMEOUT,
    STAGE
)

# For background tasks, if needed
# from apscheduler.schedulers.background import BackgroundScheduler

def create_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

    # Load config from settings.py
    app.config.from_pyfile('config/settings.py')

    # Register routes
    register_routes(app)

    # Potentially start any schedulers/background tasks
    # start_scheduler(app)

    try:
        # start_background_task()

        # Start server
        if STAGE == 'prod':
            # Set up the scheduler for prod env
            # app.logger.info("Start scheduler to refresh server in background")
            # scheduler.start()

            app.logger.info('Start production server')
            from waitress import serve
            serve(app, host = "0.0.0.0", port = PRODUCTION_SERVER_PORT, channel_timeout=REQUEST_TIMEOUT)
        else:
            app.logger.info('Start development server')
            app.run(debug = True, port = DEV_SERVER_PORT)
    except (KeyboardInterrupt, SystemExit) as e:
        # scheduler.shutdown()
        app.logger.error(f'Error while running server: {str(e)}')

    return app

def register_routes(app):
    """
    Imports and registers all route blueprints.
    """
    from .routes.chat_routes import chat_bp
    from .routes.start_routes import start_bp
    from .routes.end_routes import end_bp
    from .routes.general_routes import general_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(start_bp)
    app.register_blueprint(end_bp)
    app.register_blueprint(general_bp)

# If you use a background scheduler
# def start_scheduler(app):
#     scheduler = BackgroundScheduler()
#     # Add your jobs here...
#     scheduler.start()
