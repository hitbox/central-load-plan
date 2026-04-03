from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from central_load_plan.models.clp_base import CLPBase

db = SQLAlchemy(model_class=CLPBase)

login_manager = LoginManager()

login_manager.login_view = 'user.login'

@login_manager.user_loader
def load_user(user_id):
    from central_load_plan.models import User

    return db.session.get(User, user_id)

def init_app(app):
    db.init_app(app)
    login_manager.init_app(app)
