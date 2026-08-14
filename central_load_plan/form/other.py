from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TimeField

class EFFArchiveFilterForm(FlaskForm):
    """
    Filter form for archived EFF XML files.
    """

    airline_iata_code = RadioField(
        'Airline IATA Code',
        choices=['GB', '8C'],
        default = 'GB',
    )

    archive_date = DateField(
        'Archive Date',
        default = date.today,
    )

    submit = SubmitField('Update list')


class CrewmemberArgsForm(FlaskForm):
    """
    Form for arguments like what is scraped from XML.
    """

    airline_iata_code = RadioField('Airline IATA Code', choices=['GB', '8C'])

    flight_origin_date = DateField('Flight Origin Date')

    flight_number = IntegerField('Flight Number')

    origin_iata = StringField('Origin IATA')

    scheduled_departure_date = DateField('Scheduled Departure Date')

    scheduled_departure_time = TimeField('Scheduled Departure Time')

    submit = SubmitField()
