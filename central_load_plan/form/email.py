from markupsafe import Markup
from wtforms import Form
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TimeField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms_sqlalchemy.orm import model_form

class EmailForm(Form):

    address = StringField()

    display_name = StringField()

    update = SubmitField()
    delete = SubmitField()


def render_only_the_field_input(form):
    breakpoint()
    html = ['<ul>']
    for field in field_list:
        html.append(f'{field()}')
    html.append('</ul>')
    return Markup(''.join(html))


class EmailAddressForm(Form):

    widget = render_only_the_field_input

    address = StringField()
