import uuid

import sqlalchemy as sa

from central_load_plan.models.clp_base import CLPBase

from ..job import SendTo

class SendToTemplate(CLPBase):

    __job_class__ = SendTo

    __tablename__ = 'send_to_template'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    # Parent EmailFromTemplateJobTemplate
    email_from_template_job_template_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('email_from_template_job_template.id'),
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
    )

    # Email to append to list if OFPCondition is met.
    email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    email = sa.orm.relationship(
        'Email',
    )

    def make_job(self):
        return self.__job_class__(email=self.email)
