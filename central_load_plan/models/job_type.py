import uuid

from enum import Enum

import sqlalchemy as sa

from .clp_base import CLPBase

class JobTypeEnum(Enum):
    """
    Some type of work to do with OFP data scraped from XML files.
    """

    EMAIL_FROM_TEMPLATE = 'email_from_template'

    FILE_FROM_TEMPLATE = 'file_from_template'

    JSON_FILE = 'json_file'

    def instance(self):
        from central_load_plan.www.extension import db

        query = db.select(JobType).where(JobType.name == self.name)
        return db.session.scalars(query).one()


class JobType(CLPBase):
    """
    Type of Job to conditionally perform on OFP files.
    """

    __tablename__ = 'job_type'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False, unique=True)
