from flask import Blueprint
from flask import current_app
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from markupsafe import Markup
from sqlalchemy.orm import Session

from urllib.parse import urljoin
from urllib.parse import urlparse

import sqlalchemy as sa
import click

from sqlalchemy.exc import NoResultFound

from central_load_plan.extension import db
from central_load_plan.extension import login_manager
from central_load_plan.form import LoginForm
from central_load_plan.models import User

user_bp = Blueprint('user', __name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc

@user_bp.route('/', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)

    if request.method == 'POST':
        if login_form.validate():

            user_query = db.select(User).where(User.username == login_form.username.data)
            try:
                user = db.session.scalars(user_query).one()
            except NoResultFound:
                pass
            else:
                if user.verify_password(login_form.password.data):
                    login_user(user)
                    flash(f'{user.username} logged in', 'success')

                    next_url = request.args.get('next')
                    if not next_url or not is_safe_url(next_url):
                        next_url = url_for('index')
                    return redirect(next_url)

        flash('Login failed', 'danger')

    context = {
        'login_form': login_form,
    }
    return render_template('login.html', **context)

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out')
    return redirect(url_for('user.login'))

@user_bp.cli.command('list')
def list():
    """
    List user objects in database.
    """
    for user in db.session.scalars(db.select(User).order_by(User.username)):
        click.echo(f'{user.username}')

@user_bp.cli.command('create')
@click.argument('username')
@click.password_option()
@click.option('--admin', is_flag=True)
def create(username, password, admin):
    user = User(
        username = username,
        password = password,
        is_admin = admin,
        is_active = True,
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f'{username} created')
