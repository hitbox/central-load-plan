import uuid

import sqlalchemy as sa

from central_load_plan.models.clp_base import CLPBase

class Job(CLPBase):
    """
    Some work to do with OFP data.
    """

    __tablename__ = 'job'

    __mapper_args__ = {
        'polymorphic_on': 'job_type_name',
    }

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False)

    job_type_name = sa.Column(
        sa.String,
        comment = 'polymorphic job type identifier.',
    )

    ofp_file_id = sa.Column(sa.ForeignKey('ofp_file.id'))

    ofp_condition_id = sa.Column(sa.ForeignKey('ofp_condition.id'))

    ofp_condition = sa.orm.relationship(
        'OFPCondition',
    )

    ofp_file = sa.orm.relationship(
        'OFPFile',
        back_populates = 'jobs',
    )

    def do_work(self):
        raise NotImplementedError(str(self))
