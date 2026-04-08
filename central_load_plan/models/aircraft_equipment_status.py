import uuid

import sqlalchemy as sa

from .clp_base import CLPBase

class AircraftEquipmentStatus(CLPBase):

    __tablename__ = 'aircraft_equipment_status'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    item = sa.Column(sa.String)

    description = sa.Column(sa.String)

    ofp_file_id = sa.Column(sa.ForeignKey('ofp_file.id'))

    ofp_files = sa.orm.relationship(
        'OFPFile',
        back_populates = 'aircraft_equipment_status_list',
    )
