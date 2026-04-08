import uuid

import sqlalchemy as sa

from .clp_base import CLPBase

class CrewMember(CLPBase):

    __tablename__ = 'crew_member'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    ofp_file_id = sa.Column(sa.ForeignKey('ofp_file.id'))

    ofp_files = sa.orm.relationship(
        'OFPFile',
        back_populates = 'crewmembers',
    )

    first_name = sa.Column(sa.String)

    last_name = sa.Column(sa.String)

    employee_number = sa.Column(sa.String)

    seat = sa.Column(sa.String)

    source = sa.Column(sa.String)

    seat_order = sa.Column(sa.Integer)
