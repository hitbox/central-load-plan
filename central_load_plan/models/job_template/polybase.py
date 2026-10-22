import logging
import uuid

from operator import attrgetter

import sqlalchemy as sa

from markupsafe import Markup

from central_load_plan.extension import db

logger = logging.getLogger(__name__)

class JobTemplate(db.Model):
    """
    Named template for work to do when a condition is met against an OFPFile object.
    """

    __ui_description__ = Markup("""
    <h3>JobTemplate</h3>
    <p>Object holds the conditions for creating a Job object to do work.</p>
    """)

    __tablename__ = 'job_template'

    __mapper_args__ = {
        'polymorphic_on': 'job_type_name',
    }

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False, unique=True)

    is_enabled = sa.Column(sa.Boolean, nullable=False)

    ofp_condition_id = sa.Column(
        sa.ForeignKey('ofp_condition.id'),
        nullable = False,
    )

    ofp_condition = sa.orm.relationship(
        'OFPCondition',
    )

    job_type_name = sa.Column(
        sa.String,
        sa.ForeignKey('job_type.name'),
        comment = 'polymorphic job type identifier',
    )

    jobs = db.orm.relationship(
        'Job',
        back_populates = 'job_template',
    )

    min_size = sa.Column(
        sa.Integer,
        comment = 'minimum file size to process this job',
    )

    # NOTE: not using a min_age because the file system we're dealing with have
    # mtimes that return negative with regard to current time.

    execution_position = sa.Column(
        sa.Integer,
        comment = 'execution ordering among matching jobs',
    )

    def __init__(self, **kwargs):
        if hasattr(self, '__python_defaults__'):
            for key, value in self.__python_defaults__.items():
                kwargs.setdefault(key, value)
        super().__init__(**kwargs)

    def is_match(self, ofp_file):
        return self.ofp_condition.is_match(ofp_file)

    def make_job(self, ofp_file):
        # Create the job object that actually does work [do_work()].
        raise NotImplementedError()

    @classmethod
    def select_factory(cls):
        """
        JobTemplate objects sorted by execution position.
        """
        query = db.select(cls).order_by(cls.execution_position)
        return query

    @classmethod
    def _matches_for_ofp_file(cls, session, ofp_file):
        """
        Yield all JobTemplate objects whose related OFPCondition conditions
        match against OFPFile ofp_file.

        This is a positive style condition. All conditions must match. Unlike
        the related OFPCondition condition objects for SendToTemplate for which
        an empty condition (None) is taken as a match.
        """
        for job_template in session.scalars(sa.select(cls)):
            if (
                job_template.ofp_condition.is_match(ofp_file)
                and ofp_file.size >= job_template.min_size
            ):
                logger.info('JobTemplate %s matched ofp_file=%s', cls, ofp_file)
                yield job_template

    @classmethod
    def all_matches_sorted_for_execution(cls, session, ofp_file):
        key = attrgetter('execution_position')
        return sorted(cls._matches_for_ofp_file(session, ofp_file), key=key)
