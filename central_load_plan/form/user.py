from wtforms import Form
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField

class UserForm(Form):
    """
    Edit User database object.
    """

    username = StringField()

    password = PasswordField()

    update = SubmitField()
    delete = SubmitField()
