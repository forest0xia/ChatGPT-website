from app.main import create_app

from app.config.settings import (
    PRODUCTION_SERVER_PORT,
    DEV_SERVER_PORT,
    REQUEST_TIMEOUT,
    STAGE
)

if __name__ == "__main__":
    app = create_app()
    try:
        if STAGE == 'prod':
            app.logger.info('Start production server')
            from waitress import serve
            serve(app, host = "0.0.0.0", port = PRODUCTION_SERVER_PORT, channel_timeout=REQUEST_TIMEOUT)
        else:
            app.logger.info('Start development server')
            app.run(debug = True, port = DEV_SERVER_PORT)
    except (KeyboardInterrupt, SystemExit) as e:
        app.logger.error(f'Error while running server: {str(e)}')
