# File: config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ban-nen-thay-the-chuoi-nay'
    
    # THAY ĐỔI DÒNG NÀY: Thêm ?charset=utf8mb4
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:ngoctuan2104@localhost/helpdesk_db?charset=utf8mb4'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # THÊM DÒNG NÀY: Định nghĩa thư mục để lưu file đính kèm
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/uploads')
    
    # THÊM DÒNG NÀY
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')