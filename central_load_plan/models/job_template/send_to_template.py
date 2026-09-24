import uuid
import warnings

import sqlalchemy as sa

from markupsafe import Markup
from sqlalchemy.ext.associationproxy import association_proxy

from central_load_plan.extension import db

from ..job import SendTo

class SendToTemplate(db.Model):
    """
    A template describing the email to send to and an optional condition
    against OFP data. This class is how we get extra, finer per-email control
    over what emails go out for an OFP condition against, say,
    EmailFromTemplateJobTemplate objects.
    """

    __tablename__ = 'send_to_template'

    __ui_description__ = Markup("""
    <h3>SendToTemplate</h3>
    <p>Defines an email recipient and, optionally, a condition that controls when
    that recipient receives the email.</p>

    <p>The email template determines when an email is sent. This setting provides
    additional control over who receives it.</p>

    <p>Without a condition, the recipient always receives the email. With a
    condition, the recipient receives it only when the condition matches the
    flight plan.</p>
    """)

    __job_class__ = SendTo

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, unique=True, nullable=False)

    # Parent EmailFromTemplateJobTemplate
    email_from_template_job_template_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template_email_from_template.id'),
    )

    email_from_template_job_template = sa.orm.relationship(
        'EmailFromTemplateJobTemplate',
    )

    # OFP Condition to add related email to final send to list.
    ofp_condition_id = sa.Column(
        sa.ForeignKey('ofp_condition.id'),
    )

    ofp_condition = sa.orm.relationship(
        'OFPCondition',
        back_populates = 'send_to_templates',
    )

    ofp_condition_name = association_proxy(
        'ofp_condition',
        'name',
    )

    # Email to append to list if OFPCondition is met.
    email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    email = sa.orm.relationship(
        'Email',
        back_populates = 'send_to_templates',
    )

    @property
    def ofp_condition_as_html(self):
        if self.ofp_condition is None:
            return 'No condition--always send'
        else:
            return self.ofp_condition.condition_as_html

    @property
    def address_html_with_condtion(self):
        """
        Produce an HTML, short brief of what emails get sent under what
        conditions.
        """
        html = []

        if self.ofp_condition:
            html.append(
                f'Send to <address>{self.email.address}</address> when'
                f' {self.ofp_condition.condition_as_string}')
        else:
            html.append(f'Always send to <address>{self.email.address}</address>')

        return Markup(''.join(html))

    def make_job(self):
        warnings.warn(
            f'{self}.make_job is unexpectedly being called.',
            RunTimeWarning,
            stacklevel = 2,
        )
        return self.__job_class__(
            email = self.email,
            ofp_condition = self.ofp_condition,
        )
