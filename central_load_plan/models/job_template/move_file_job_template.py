import uuid

import sqlalchemy as sa

from ..job import JobTypeEnum
from ..job import MoveFileJob

from .polybase import JobTemplate

class MoveFileJobTemplate(JobTemplate):

    __job_class__ = MoveFileJob

    __tablename__ = 'move_file_job'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.MOVE_FILE.name,
    }

    __python_defaults__ = {
        'execution_position': 1000,
        'min_size': 0, # always move file regardless of size.
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    destination_path = sa.Column(
        sa.String,
        comment = 'Python format string produces dest. path from OFP data.'
    )

    def make_job(self, ofp_file):
        return self.__job_class__(
            ofp_file = ofp_file,
            name = self.name,
            destination_path = self.destination_path,
        )
