from flask import Flask
from config import Config
from extension import login_manager
from models.user import User
from main.routes import main_bp, user_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    from auth.routes import auth_bp
    from main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)


    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
