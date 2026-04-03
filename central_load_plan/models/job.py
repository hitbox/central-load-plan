import uuid

from enum import Enum

import sqlalchemy as sa

from .clp_base import CLPBase
from .job_type import JobTypeEnum

class Job(CLPBase):
    """
    Some work to do with OFP data.
    """

    __tablename__ = 'job'

    __mapper_args__ = {
        'polymorphic_on': 'job_type_id',
    }

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False, unique=True)

    job_type_id = sa.Column(sa.ForeignKey('job_type.id'))

    ofp_file_id = sa.Column(sa.ForeignKey('ofp_file.id'))

    ofp_condition_id = sa.Column(sa.ForeignKey('ofp_condition.id'))

    ofp_condition = sa.orm.relationship(
        'OFPCondition',
    )

    ofp_file = sa.orm.relationship(
        'OFPFile',
        back_populates = 'jobs',
    )


class SendTo(CLPBase):

    __tablename__ = 'send_to'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    send_email_job_id = sa.Column(sa.Uuid, sa.ForeignKey('email_from_template_job.id'))

    email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    email = sa.orm.relationship(
        'Email',
        back_populates = 'send_tos',
    )


class EmailFromTemplateJob(Job):

    __tablename__ = 'email_from_template_job'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.EMAIL_FROM_TEMPLATE,
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job.id'),
        primary_key = True,
        default = uuid.uuid4,
    )


class FileOutputFromTemplateJob(Job):

    __tablename__ = 'file_output_from_template_job'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.FILE_FROM_TEMPLATE.name,
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job.id'),
        primary_key = True,
        default = uuid.uuid4,
    )


class JSONOutputJob(Job):

    __tablename__ = 'json_output_job'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.JSON_FILE.name,
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    output_path = sa.Column(sa.String, nullable=False)
