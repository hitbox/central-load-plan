import os
import shutil
import uuid

import sqlalchemy as sa

from .job_type import JobTypeEnum
from .polybase import Job

class MoveFileJob(Job):
    """
    Move the originally detected file job.
    """

    __tablename__ = 'move_file_job_template'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.MOVE_FILE.name,
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    destination_path = sa.Column(
        sa.String,
        nullable=False,
        comment =
            'Python format string taking OFP data to produce'
            ' the destination path.',
    )

    def do_work(self):
        ofp_data = self.ofp_file.as_dict_with_crew()

        destination = self.destination_path.format(**ofp_data)

        dirpath = os.path.dirname(destination)
        os.makedirs(dirpath, exist_ok=True)

        shutil.move(self.ofp_file.original_path, destination)

        ofp_file.archive_path = destination
