import uuid

from enum import Enum

import sqlalchemy as sa

from central_load_plan.extension import db

class JobTypeEnum(Enum):
    """
    Some type of work to do with OFP data scraped from XML files.
    """

    EMAIL_FROM_TEMPLATE = 'email_from_template'

    FILE_FROM_TEMPLATE = 'file_from_template'

    JSON_FILE = 'json_file'

    MOVE_FILE = 'move_file'

    def instance(self):
        query = db.select(JobType).where(JobType.name == self.name)
        return db.session.scalars(query).one()


class JobType(db.Model):
    """
    Type of Job to conditionally perform on OFP files.
    """

    __tablename__ = 'job_type'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False, unique=True)

    @db.validates('name')
    def validate_name(self, key, value):
        for member in JobTypeEnum:
            if value == member.name:
                break
        else:
            raise ValueError(f'{value} must be a name of enum JobTypeEnum')

