from wtforms import Form
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms_sqlalchemy.orm import model_form

class LoginForm(Form):

    username = StringField(validators=[DataRequired()])

    password = PasswordField(validators=[DataRequired()])

    submit = SubmitField('Login')
