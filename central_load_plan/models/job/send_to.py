import uuid

import sqlalchemy as sa

from central_load_plan.models.clp_base import CLPBase

class SendTo(CLPBase):
    """
    Association object linking EmailFromTemplateJob to Email objects.
    """

    __tablename__ = 'send_to'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email_from_template_job_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('email_from_template_job.id'),
    )

    email_from_template_job = sa.orm.relationship(
        'EmailFromTemplateJob',
    )

    email_id = sa.Column(sa.Uuid(as_uuid=True), sa.ForeignKey('email.id'))

    email = sa.orm.relationship(
        'Email',
    )
