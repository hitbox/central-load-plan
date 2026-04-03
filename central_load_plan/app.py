from flask import Flask
from flask import redirect
from flask import render_template
from flask import url_for

from . import converter
from . import extension
from . import views

CONFIG_PREFIX = 'CENTRAL_LOAD_PLAN'

def create_app():
    """
    Demo web apps for central_load_plan.
    """
    app = Flask(__name__)
    app.config.from_envvar(f'{CONFIG_PREFIX}_CONFIG')

    extension.init_app(app)
    converter.init_app(app)
    views.init_app(app)

    @app.route('/')
    def index():
        """
        Redirect to admin root for app root.
        """
        return redirect(url_for('admin.root'))

    @app.cli.command('create-db')
    def create_db():
        """
        Create database schema from SQLAlchemy ORM.
        """
        extension.db.create_all()

    return app
