from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import FormField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms_sqlalchemy.fields import QuerySelectField

from central_load_plan.models import OFPCondition
from central_load_plan.extension import db

from .job_template import SendToTemplateAddressForm
from .job_template import render_field_list
from .ofp_condition import OFPConditionForm

def ofp_conditions():
    return db.session.scalars(db.select(OFPCondition)).all()

class EditEmailFromTemplateJobTemplateForm(FlaskForm):
    """
    Edit EmailFromTemplateJobTemplate object.
    """

    name = StringField()

    ofp_condition = FormField(
        OFPConditionForm,
    )

    ofp_condition = QuerySelectField(
        query_factory = ofp_conditions,
        get_label = 'name',
    )

    # TODO
    # - add/remove buttons for each
    send_tos = FieldList(
        FormField(
            SendToTemplateAddressForm,
            widget = render_field_list,
        ),
        widget = render_field_list,
    )
