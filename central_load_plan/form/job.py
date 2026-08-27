import json
import uuid

from datetime import date
from operator import attrgetter

import sqlalchemy as sa

from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import DateField
from wtforms import FieldList
from wtforms import Form
from wtforms import FormField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import RadioField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import TimeField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms_sqlalchemy.orm import model_form

from central_load_plan.extension import db
from central_load_plan.field import JSONField
from central_load_plan.models import JobTemplate
from central_load_plan.models import JobType
from central_load_plan.models import JobTypeEnum
from central_load_plan.models import OFPCondition
from central_load_plan.models import OFPFile

from .email import EmailAddressForm
from .email import EmailForm
from .widget import render_field_list

class JobForm(FlaskForm):

    name = StringField(
        validators = [
            DataRequired(),
        ],
    )

    job_type_name = SelectField('JOB Type')

    template_name = StringField()

    submit = SubmitField('Update')

    delete = SubmitField('Delete')
