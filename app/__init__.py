# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

# Chỉ khởi tạo các extension ở đây
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Di chuyển các cấu hình vào bên trong hàm create_app
def create_app(config_class=Config):
    """Hàm factory để tạo ứng dụng Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Gắn các extension vào app instance
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # --- Cấu hình cho LoginManager ---
    # Đặt các cấu hình này sau khi login_manager đã được init_app
    login_manager.login_view = 'main.login' # type: ignore
    login_manager.login_message = "Vui lòng đăng nhập để truy cập trang này."
    login_manager.login_message_category = 'info'
    # -----------------------------------

    # Import và đăng ký blueprint sau khi mọi thứ đã sẵn sàng
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # THÊM CÁC HÀM XỬ LÝ LỖI
    from flask import render_template
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403 # Bạn tự tạo file 403.html tương tự 404.html

    # Quan trọng: Đảm bảo models được import để user_loader hoạt động
    with app.app_context():
        from . import models

    return app