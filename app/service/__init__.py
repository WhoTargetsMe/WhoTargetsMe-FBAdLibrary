from flask import Blueprint

main = Blueprint("main", __name__, template_folder="templates")

from app.service import routes  # to avoid cross-reference
