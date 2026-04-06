import os
import uuid

import sqlalchemy as sa

from .polybase import Job
from .job_type import JobTypeEnum

from central_load_plan import rendering

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

    template_name = sa.Column(sa.String, nullable=False)

    output_path = sa.Column(sa.String, nullable=False)

    def do_work(self):

        # build ofp data
        ofp_data = self.ofp_file.as_dict_with_crew()

        content = rendering.render(self.template_name, ofp_data)

        destination = self.output_path.format(**ofp_data)

        dirpath = os.path.dirname(destination)
        os.makedirs(dirpath, exist_ok=True)

        with open(destination, 'w') as outfile:
            outfile.write(content)
