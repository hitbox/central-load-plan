from datetime import date

from wtforms import DateField
from wtforms import Form
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TimeField
from wtforms_sqlalchemy.orm import model_form

from central_load_plan.extension import db
from central_load_plan.models import JobType

from .email import EmailForm
from .job_template import EmailFromTemplateJobTemplateForm
from .job_template import FileFromTemplateJobTemplateForm
from .job_template import JSONOutputJobTemplateForm
from .job_template import JobTemplateForm
from .job_template import MoveFileJobTemplateForm
from .login import LoginForm
from .ofp_condition import OFPConditionForm
from .ofp_file import OFPFileFilterForm
from .ofp_file import OFPFileSortForm
from .user import UserForm

JobTypeForm = model_form(JobType, db_session=db.session)

class EFFArchiveFilterForm(Form):
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


class CrewmemberArgsForm(Form):
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


