import uuid

import sqlalchemy as sa

from central_load_plan.extension import db

class SendTo(db.Model):
    """
    Association object linking EmailFromTemplateJob (render an email from
    jinja2 template) to one or more Email (address) objects.
    """

    __tablename__ = 'send_to'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email_from_template_job_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('job_email_from_template.id'),
    )

    email_from_template_job = sa.orm.relationship(
        'EmailFromTemplateJob',
    )

    email_id = sa.Column(sa.Uuid(as_uuid=True), sa.ForeignKey('email.id'))

    email = sa.orm.relationship(
        'Email',
        back_populates = 'send_tos',
    )
