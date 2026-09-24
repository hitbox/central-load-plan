"""Rename job tables for clarity. Combine existing P-station OFPCondition
objects into one that matches any of the stations.

Revision ID: cefbec432f72
Revises: 31433e9a25f9
Create Date: 2026-08-17 14:05:55.570024

"""
import logging
import uuid

from enum import Enum

import sqlalchemy as sa

from alembic import op
from sqlalchemy.ext.orderinglist import ordering_list

# revision identifiers, used by Alembic.
revision= 'cefbec432f72'
down_revision = '31433e9a25f9'
branch_labels = None
depends_on = None

logger = logging.getLogger('alembic')

# Basically put job_ in front so that tables group together logically.

# Job subclasses tablenames.
renames = [
    # <old/original>, <new>
    ('email_from_template_job', 'job_email_from_template'),
    ('file_output_from_template_job', 'job_file_output_from_template'),
    ('json_output_job', 'job_json_output'),
    # Fixed originally misnamed ("template" should not have been in this:
    ('move_file_job_template', 'job_move_file'),
]

# JobTemplate subclassess tablenames.
renames.extend([
    # the template class's table name is wrong too
    ('email_from_template_job_template', 'job_template_email_from_template'),
    ('file_output_from_template_job_template', 'job_template_file_output_from_template'),
    ('move_file_job', 'job_template_move_file'),
    ('json_output_template_job_template', 'job_template_json_output'),
])

class Base(sa.orm.DeclarativeBase):
    pass


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

    min_age = sa.Column(
        sa.Integer,
        default = 5, # seconds
        comment = 'minimum file age in seconds to process this job',
    )

    execution_position = sa.Column(
        sa.Integer,
        comment = 'execution ordering among matching jobs',
    )


class JobTypeEnum(Enum):
    """
    Some type of work to do with OFP data scraped from XML files.
    """

    EMAIL_FROM_TEMPLATE = 'email_from_template'

    FILE_FROM_TEMPLATE = 'file_from_template'

    JSON_FILE = 'json_file'

    MOVE_FILE = 'move_file'


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


class SendToTemplate(Base):
    __tablename__ = 'send_to_template'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

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


class JobType(Base):
    __tablename__ = 'job_type'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False, unique=True)


class Email(Base):

    __tablename__ = 'email'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    address = sa.Column(sa.String, unique=True, nullable=False)

    display_name = sa.Column(sa.String, nullable=True)


def replace_p_prefix_email_and_conditions():
    # Delete OFPCondition objects what contain string 'Equal' in their names.
    # These are the conditions for the P-prefix stations/emails.

    # Manually cascade delete referenced OFPConditionValue objects

    name_like = 'OFP origin IATA Equals %'
    logger.info('DELETE ofp_condition_value ILIKE %s', name_like)
    params = {'name_like': name_like}
    # These should be:
    # OFP origin IATA Equals ANC,
    # OFP origin IATA Equals HKO,
    # OFP origin IATA Equals HLI,
    # OFP origin IATA Equals HNL,
    # OFP origin IATA Equals HOG,
    stmt = sa.text("""
        DELETE FROM ofp_condition_value
        WHERE ofp_condition_id IN (
            SELECT id
            FROM ofp_condition
            WHERE name ILIKE :name_like
        )
        """).bindparams(**params)
    op.execute(stmt)

    # Delete SendToTemplate
    logger.info('DELETE send_to_template ILIKE %s', name_like)
    stmt = sa.text("""
        DELETE FROM send_to_template
        WHERE ofp_condition_id IN (
            SELECT id
            FROM ofp_condition
            WHERE name ILIKE :name_like
        )
        """).bindparams(**params)
    op.execute(stmt)

    # Delete the OFPCondition objects that were pointing to those conditions.
    logger.info('DELETE ofp_condition ILIKE %s', name_like)
    stmt = (
        sa.text('DELETE FROM ofp_condition WHERE name ILIKE :name_like')
        .bindparams(**params)
    )
    op.execute(stmt)

    session = sa.orm.Session(bind=op.get_bind())

    ofp_condition = OFPCondition(
        id = uuid.uuid4(),
        name = 'P-prefix stations',
        blurb =
            'Match IATA origin stations that need a P prefix and send to P{origin_iata}-clp@airtransport.cc email address.',
        ofp_key = 'origin_iata',
        operator = 'contains',
        values = [
            OFPConditionValue(
                value = 'ANC',
            ),
            OFPConditionValue(
                value = 'HKO',
            ),
            OFPConditionValue(
                value = 'HLI',
            ),
            OFPConditionValue(
                value = 'HNL',
            ),
            OFPConditionValue(
                value = 'HOG',
            ),
        ]
    )
    session.add(ofp_condition)

    session.flush()

    session.add(
        SendToTemplate(
            ofp_condition = ofp_condition,
            email = Email(
                address = 'P{origin_iata}-clp@airtransport.cc',
            ),
        )
    )

    query = (
        sa.select(OFPCondition)
        .where(OFPCondition.name == 'Send OFP origin IATA to K-prefixed generated email address from OFP iata codes that do not have a K prefix.')
    )
    ofp_condition = session.scalars(query).one()

    ofp_condition.name = 'K-prefixed stations'

    session.commit()

def upgrade():
    """Upgrade schema."""
    for oldname, newname in renames:
        op.rename_table(oldname, newname)

    replace_p_prefix_email_and_conditions()


def downgrade():
    """Downgrade schema."""
    for oldname, newname in renames:
        op.rename_table(newname, oldname)
