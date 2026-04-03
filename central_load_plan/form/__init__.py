import json
from datetime import date

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
from central_load_plan.models import JobTemplate
from central_load_plan.models import JobType
from central_load_plan.models import JobTypeEnum
from central_load_plan.models import OFPCondition
from central_load_plan.models import OFPConditionValue
from central_load_plan.models import OFPFile
from central_load_plan.singlepage import DynamicListWidget
from central_load_plan.widget import NestedFormWidget

from central_load_plan.field import JSONField

from .job_template import JobTemplateForm
from .ofp_file import OFPFileFilterForm

JobTypeForm = model_form(JobType, db_session=db.session)

class LoginForm(Form):

    username = StringField()

    password = PasswordField()

    submit = SubmitField('Login')


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


class UserForm(Form):
    """
    Edit User database object.
    """

    username = StringField()

    password = PasswordField()

    update = SubmitField()
    delete = SubmitField()


class EmailForm(Form):

    address = StringField()

    display_name = StringField()

    update = SubmitField()
    delete = SubmitField()


class OFPConditionValueFormField(Form):

    value = StringField(validators=[DataRequired()])


def ofp_condition_name_is_unique(form, field):
    if not form.delete.data:
        query = (
            db.select(OFPCondition)
            .where(OFPCondition.name == field.data)
        )
        exists = db.session.scalars(query).one_or_none()
        if exists:
            raise ValidationError(f'Name already exists')

def validate_values_for_operator(form, values_field):
    if form.operator.data != 'contains':
        if len(values_field.data) > 1:
            raise ValidationError(f'Only only value for {form.operator.data} allowed')

class OFPConditionForm(Form):

    name = StringField()

    def is_ofp_key(form, field):
        """
        Validate ofp_key is an attribute of OFPFile for submit/update.
        """
        if not form.delete.data:
            mapper = sa.inspect(OFPFile)
            if field.data not in mapper.columns.keys():
                raise ValidationError(f'{field.data} is not a column of OFPFile')

    ofp_key = SelectField()

    __human_operator__ = {
        'eq': 'Equals',
        'ne': 'Not Equal',
        'lt': 'Less Than',
        'le': 'Less Than or Equal',
        'gt': 'Greater Than',
        'ge': 'Greater Than or Equal',
        'contains': 'One Of',
        'ilike': 'Case Insensitive Search',
    }

    operator = SelectField(validators=[DataRequired()])

    values = FieldList(
        FormField(
            OFPConditionValueFormField
        ),
        min_entries=1,
        widget = DynamicListWidget(),
        validators = [validate_values_for_operator],
    )

    submit = SubmitField('Update')

    delete = SubmitField('Delete')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'obj' in kwargs:
            # Editing existing obj
            obj = kwargs['obj']
        else:
            # Require unique name for new
            validators = list(self.name.validators)
            validators.append(ofp_condition_name_is_unique)
            self.name.validators = tuple(validators)

        # Dynamic choices
        self.operator.choices = [
            (key, self.__human_operator__[key])
            for key in OFPCondition.__valid_operators__
        ]
        mapper = sa.inspect(OFPFile)
        self.ofp_key.choices = [(c.name, c.name) for c in mapper.columns]

    def populate_obj(self, obj):
        # normal fields
        for field_name in ['name', 'ofp_key', 'operator']:
            if hasattr(self, field_name):
                setattr(obj, field_name, getattr(self, field_name).data)

        # nested FieldList -> OFPConditionValue
        if hasattr(self, 'values'):
            # Clear existing related objects
            obj.values[:] = []

            for i, value_form in enumerate(self.values):
                # Either update existing object if editing or create new
                val_obj = OFPConditionValue(value=value_form.value.data, position=i)
                obj.values.append(val_obj)
