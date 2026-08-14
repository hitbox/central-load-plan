from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import FormField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField

from .job_template import SendToTemplateAddressForm
from .job_template import render_field_list
from .ofp_condition import EditOFPConditionForm

class EditEmailFromTemplateJobTemplateForm(FlaskForm):
    """
    Edit EmailFromTemplateJobTemplate object.
    """

    name = StringField()

    ofp_condition = FormField(
        EditOFPConditionForm,
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
