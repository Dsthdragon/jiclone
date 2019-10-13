import os


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:''@localhost/jiclone'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 10
    SECRET_KEY = os.environ.get('SECRET_KEY') or "jiClone_secret_key"
    UPLOAD_FOLDER = os.path.abspath(os.path.join("jiClone", "build", "static", "upload", "images", "avatars"))
    ADS_UPLOAD_FOLDER = os.path.abspath(os.path.join("jiClone", "build", "static", "upload", "images", "services"))
