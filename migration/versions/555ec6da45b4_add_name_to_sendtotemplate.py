"""Add name to SendToTemplate

Revision ID: 555ec6da45b4
Revises: 8ddbe8f9ab13
Create Date: 2026-08-30 17:00:41.767209

"""
import uuid

from enum import Enum

import sqlalchemy as sa

from alembic import op
from sqlalchemy.ext.orderinglist import ordering_list

# revision identifiers, used by Alembic.
revision= '555ec6da45b4'
down_revision = '8ddbe8f9ab13'
branch_labels = None
depends_on = None

class Base(sa.orm.DeclarativeBase):
    pass


class JobTypeEnum(Enum):
    """
    Some type of work to do with OFP data scraped from XML files.
    """

    EMAIL_FROM_TEMPLATE = 'email_from_template'

    FILE_FROM_TEMPLATE = 'file_from_template'

    JSON_FILE = 'json_file'

    MOVE_FILE = 'move_file'


class JobTemplate(Base):
    __tablename__ = 'job_template'

    __mapper_args__ = {
        'polymorphic_on': 'job_type_name',
    }

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False, unique=True)

    ofp_condition_id = sa.Column(
        sa.ForeignKey('ofp_condition.id'),
        nullable = False,
    )

    ofp_condition = sa.orm.relationship(
        'OFPCondition',
    )

    job_type_name = sa.Column(
        sa.String,
        comment = 'polymorphic job type identifier',
    )

    jobs = sa.orm.relationship(
        'Job',
        back_populates = 'job_template',
    )

    min_size = sa.Column(
        sa.Integer,
        comment = 'minimum file size to process this job',
    )

    execution_position = sa.Column(
        sa.Integer,
        comment = 'execution ordering among matching jobs',
    )


class SendToTemplate(Base):
    __tablename__ = 'send_to_template'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String)

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
    )

    # Email to append to list if OFPCondition is met.
    email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    email = sa.orm.relationship(
        'Email',
        #back_populates = 'send_to_templates',
    )


class OFPCondition(Base):
    """
    Conditional expression to test against parsed and deserialized OFP XML file data.
    """

    __tablename__ = 'ofp_condition'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, unique=True, nullable=False)

    blurb = sa.Column(
        sa.String,
        nullable = True,
        info = {
            'help': 'Short description of the purpose of this condition.',
        },
    )

    ofp_key = sa.Column(sa.String, nullable=False)

    operator = sa.Column(sa.String)

    values = sa.orm.relationship(
        'OFPConditionValue',
        back_populates = 'ofp_conditions',
        cascade = 'all, delete-orphan',
        order_by = 'OFPConditionValue.position',
        collection_class = ordering_list('position')
    )


class Job(Base):
    __tablename__ = 'job'

    __mapper_args__ = {
        'polymorphic_on': 'job_type_name',
    }

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    job_type_name = sa.Column(
        sa.String,
        comment = 'polymorphic job type identifier.',
    )

    job_template_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template.id'),
        nullable = False,
        comment = 'FK to the job template that created this job',
    )

    job_template = sa.orm.relationship(
        'JobTemplate',
        back_populates = 'jobs',
    )

class OFPConditionValue(Base):

    __tablename__ = 'ofp_condition_value'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    value = sa.Column(sa.String, nullable=False)

    ofp_condition_id = sa.Column(sa.ForeignKey('ofp_condition.id'))

    ofp_conditions = sa.orm.relationship(
        'OFPCondition',
        back_populates = 'values'
    )

    position = sa.Column(sa.Integer, default=0)


class Email(Base):

    __tablename__ = 'email'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    address = sa.Column(sa.String, unique=True, nullable=False)

    display_name = sa.Column(sa.String, nullable=True)


class EmailFromTemplateJobTemplate(JobTemplate):

    __tablename__ = 'job_template_email_from_template'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.EMAIL_FROM_TEMPLATE.name,
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    send_tos = sa.orm.relationship(
        'SendToTemplate',
        back_populates = 'email_from_template_job_template',
        cascade = 'all, delete-orphan',
    )

    from_email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    from_email = sa.orm.relationship('Email')

    template_name = sa.Column(sa.String, nullable=False)

    subject = sa.Column(
        sa.String,
        nullable=False,
        comment = 'Format string given scraped OFP data for email subject',
    )

def upgrade():
    """Upgrade schema."""
    op.drop_column('job_template', 'min_age')
    op.add_column('send_to_template', sa.Column('name', sa.String(), nullable=True))

    session = sa.orm.Session(bind=op.get_bind())

    for send_to_template in session.scalars(sa.select(SendToTemplate)):
        if send_to_template.ofp_condition:
            send_to_template.name = send_to_template.ofp_condition.name
        elif send_to_template.email_from_template_job_template:
            send_to_template.name = send_to_template.email_from_template_job_template.name

    session.commit()
    
    op.alter_column(
        'send_to_template',
        'name',
        existing_type=sa.String(),
        nullable=False,
    )
    op.create_unique_constraint(None, 'send_to_template', ['name'])

def downgrade():
    """Downgrade schema."""
    op.drop_constraint(None, 'send_to_template', type_='unique')
    op.drop_column('send_to_template', 'name')
    op.add_column('job_template', sa.Column('min_age', sa.INTEGER(), autoincrement=False, nullable=True, comment='minimum file age in seconds to process this job'))
