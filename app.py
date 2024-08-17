# app.py
from flask import Flask
from extensions import db, migrate
import logging
from logging.handlers import RotatingFileHandler
import os
import secrets

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///people_counting.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = secrets.token_hex(16)

    db.init_app(app)
    migrate.init_app(app, db)

    from blueprints.dashboard import dashboard_bp
    from blueprints.camera import camera_bp
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(camera_bp)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/people_counting.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('People Counting startup')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)