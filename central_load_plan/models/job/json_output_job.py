import os
import uuid
import json
import logging

import sqlalchemy as sa


from .job_type import JobTypeEnum
from .polybase import Job

logger = logging.getLogger(__name__)

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

    output_path = sa.Column(
        sa.String,
        nullable = False,
        comment = 'Python format string for output path.',
    )

    def do_work(self):
        from central_load_plan.schema import OperationalFlightPlanSchema
        schema = OperationalFlightPlanSchema()

        # build ofp data
        ofp_data = self.ofp_file.as_dict_with_crew()

        dumped = schema.dump(ofp_data)

        destination = self.output_path.format(**ofp_data)

        dirpath = os.path.dirname(destination)
        os.makedirs(dirpath, exist_ok=True)

        with open(destination, 'w') as outfile:
            json.dump(dumped, outfile)

        logger.info('json dumped: %s', destination)
