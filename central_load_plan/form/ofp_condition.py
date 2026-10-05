import sqlalchemy as sa

from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import Form
from wtforms import FormField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TimeField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError

from central_load_plan.extension import db
from central_load_plan.models import JobTemplate
from central_load_plan.models import JobType
from central_load_plan.models import JobTypeEnum
from central_load_plan.models import OFPCondition
from central_load_plan.models import OFPConditionValue
from central_load_plan.models import OFPFile
from central_load_plan.widget import DynamicListWidget
from central_load_plan.field import JSONField

def validate_values_for_operator(form, values_field):
    if form.operator.data != 'contains':
        if len(values_field.data) > 1:
            raise ValidationError(f'Only only value for {form.operator.data} allowed')

class OFPConditionValueFieldForm(Form):

    value = StringField(validators=[DataRequired()])


def ofp_key_select_field(**kwargs):
    kwargs.setdefault('choices', OFPCondition.valid_ofp_key_values())
    return SelectField(**kwargs)

def operator_select_field(**kwargs):
    default_choices = [(key, val.title()) for key, val in OFPCondition.__operators_choices__]
    kwargs.setdefault('choices', default_choices)
    validators = kwargs.setdefault('validators', [DataRequired()])
    return SelectField(**kwargs)

def values_field_list(**kwargs):
    kwargs.setdefault('unbound_field', FormField(OFPConditionValueFieldForm))
    kwargs.setdefault('min_entries', 1)
    kwargs.setdefault('widget', DynamicListWidget())
    validators = kwargs.setdefault('validators', [validate_values_for_operator])
    return FieldList(**kwargs)

class OFPConditionForm(Form):

    name = StringField()

    blurb = StringField()

    ofp_key = ofp_key_select_field()

    operator = operator_select_field()

    values = values_field_list()

    submit = SubmitField('Update')

    delete = SubmitField('Delete')

    def populate_obj(self, obj):
        # populate from normal fields
        for field_name in ['name', 'ofp_key', 'operator']:
            if hasattr(self, field_name):
                setattr(obj, field_name, getattr(self, field_name).data)

        # nested FieldList -> OFPConditionValue
        if hasattr(self, 'values'):
            # Clear existing related objects
            obj.values.clear()

            for i, value_form in enumerate(self.values):
                # Either update existing object if editing or create new
                val_obj = OFPConditionValue(value=value_form.value.data, position=i)
                obj.values.append(val_obj)


def ofp_condition_name_is_unique(form, field):
    if not form.delete.data:
        query = (
            db.select(OFPCondition)
            .where(OFPCondition.name == field.data)
        )
        exists = db.session.scalars(query).one_or_none()
        if exists:
            raise ValidationError(f'Name already exists')
