import json

from datetime import date
from operator import attrgetter

import sqlalchemy as sa

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

def job_template_name_is_unique(form, field):
    if not form.delete.data:
        query = (
            db.select(JobTemplate)
            .where(JobTemplate.name == field.data)
        )
        exists = db.session.scalars(query).one_or_none()
        if exists:
            raise ValidationError(f'Name already exists')

def select_ofp_conditions():
    query = db.select(OFPCondition)
    return db.session.scalars(query).all()

def select_job_types():
    query = db.select(JobType)
    return db.session.scalars(query).all()

class RequiredJSONFields:

    def __init__(self, fieldnames):
        self.fieldnames = set(fieldnames)

    def __call__(self, form, field):
        missing_fields = self.fieldnames.difference(field.data.keys())
        if missing_fields:
            raise ValidationError(f'Missing required fields {missing_fields}')

email_required_json_fields = RequiredJSONFields(['From', 'Subject', 'To', 'template'])

write_file_required_json_fields = RequiredJSONFields(['template', 'output_format'])

def validate_job_template_parameters_for_job_type(form, field):
    if form.job_type_id.data == JobTypeEnum.SEND_EMAIL.instance().name:
        email_required_json_fields(form, field)
    elif form.job_type_id.data == JobTypeEnum.WRITE_FILE.instance().name:
        write_file_required_json_fields(form, field)

class JobTemplateForm(Form):

    name = StringField(
        validators = [
            DataRequired(),
        ],
    )

    ofp_condition_id = SelectField()

    job_type_id = SelectField()

    parameters = JSONField(
        validators = [
            DataRequired(),
            validate_job_template_parameters_for_job_type,
        ],
    )

    submit = SubmitField('Update')

    delete = SubmitField('Delete')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Because wtforms-sqlalchemy QuerySelctField does NOT WORK with UUID!
        self.ofp_condition_id.choices = [(obj.id, obj.name) for obj in select_ofp_conditions()]
        self.job_type_id.choices = [(obj.id, obj.name) for obj in select_job_types()]
