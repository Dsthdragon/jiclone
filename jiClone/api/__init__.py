from flask import Blueprint

bp = Blueprint('api', __name__)

from jiClone.api import routes