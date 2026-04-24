import uuid

import sqlalchemy as sa

from sqlalchemy.ext.associationproxy import association_proxy

from .clp_base import CLPBase

class AircraftEquipmentStatus(CLPBase):

    __tablename__ = 'aircraft_equipment_status'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    item = sa.Column(sa.String)

    description_object_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('aircraft_equipment_status_description.id'),
    )

    description_object = sa.orm.relationship(
        'AircraftEquipmentStatusDescription',
        back_populates = 'aircraft_equipment_status'
    )

    description = association_proxy(
        'description_object',
        'raw_text',
    )

    ofp_file_id = sa.Column(sa.ForeignKey('ofp_file.id'))

    ofp_files = sa.orm.relationship(
        'OFPFile',
        back_populates = 'aircraft_equipment_status_list',
    )


class AircraftEquipmentStatusDescription(CLPBase):

    __tablename__ = 'aircraft_equipment_status_description'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    raw_text = sa.Column(sa.String)

    aircraft_equipment_status = sa.orm.relationship(
        'AircraftEquipmentStatus',
        back_populates = 'description_object',
    )
