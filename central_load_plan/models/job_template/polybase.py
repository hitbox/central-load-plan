import uuid

from operator import attrgetter

import sqlalchemy as sa

from central_load_plan.models.clp_base import CLPBase

class JobTemplate(CLPBase):
    """
    Named template for work to do when a condition is met against an OFPFile object.
    """

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

    def __init__(self, **kwargs):
        if hasattr(self, '__python_defaults__'):
            for key, value in self.__python_defaults__.items():
                kwargs.setdefault(key, value)
        super().__init__(**kwargs)

    @classmethod
    def _matches_for_ofp_file(cls, session, ofp_file):
        for job_template in session.scalars(sa.select(cls)):
            if (
                job_template.ofp_condition.is_match(ofp_file)
                and ofp_file.size >= job_template.min_size
                and ofp_file.mtime_age >= job_template.min_age
            ):
                yield job_template

    @classmethod
    def all_matches_sorted_for_execution(cls, session, ofp_file):
        key = attrgetter('execution_position')
        return sorted(cls._matches_for_ofp_file(session, ofp_file), key=key)
