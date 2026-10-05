import uuid

from abc import ABC
from abc import abstractmethod

import sqlalchemy as sa

from central_load_plan.extension import db

class Job(db.Model):
    """
    Some work to do with OFP data.
    """

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
        db.ForeignKey('job_template.id'),
        nullable = False,
        comment = 'FK to the job template that created this job',
    )

    job_template = db.orm.relationship(
        'JobTemplate',
        back_populates = 'jobs',
    )

    execution_position = sa.Column(
        sa.Integer,
        nullable = False,
        comment = 'execution ordering among matching jobs',
    )

    ofp_file_id = sa.Column(sa.ForeignKey('ofp_file.id'))

    ofp_file = sa.orm.relationship(
        'OFPFile',
        back_populates = 'jobs',
    )

    completed_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable = True,
        comment = 'Job\'s work done at timestamp.',
    )

    @abstractmethod
    def do_work(self):
        """
        """
        # TODO
        # - alembic
        # - add field "do_work_at" datetime
        # - can we guess approximate it from ofp_file.mtime? should be very close.
        # - also so that we can make it not-null.
        # - web interface to re-do jobs for ofp_file objects
        raise NotImplementedError
