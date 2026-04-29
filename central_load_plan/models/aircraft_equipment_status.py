import uuid

from datetime import datetime
from datetime import timezone as timezonelib

import sqlalchemy as sa

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property

from .clp_base import CLPBase
from central_load_plan.parsers import expiration_datetime_from_raw_text

class AircraftEquipmentStatusDescription(CLPBase):

    __tablename__ = 'aircraft_equipment_status_description'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    raw_text = sa.Column(
        sa.String,
        unique = True,
    )

    expiration_datetime = sa.Column(
        sa.DateTime(timezone=True),
        nullable = True,
        comment = 'Scraped from four-space separated raw_text messages.'
    )

    @hybrid_property
    def days_to_expiration(self):
        if self.expiration_datetime is None:
            return None
        utc_now = datetime.now(timezonelib.utc)
        return (self.expiration_datetime - utc_now).days

    @days_to_expiration.expression
    def days_to_expiration(cls):
        return sa.func.date_part(
            'day',
            cls.expiration_datetime - sa.func.now()
        )

    aircraft_equipment_status = sa.orm.relationship(
        'AircraftEquipmentStatus',
        back_populates = 'description_object',
    )

    @classmethod
    def expiration_datetime_from_raw_text(cls, raw_text, text_timezone, ignore_missing=False):
        return expiration_datetime_from_raw_text(
            raw_text = raw_text,
            text_timezone = text_timezone,
            ignore_missing = ignore_missing,
        )

    @classmethod
    def make_expiration_datetime_parser(cls, ignore_missing=False, text_timezone=None):
        def f(raw_text):
            return cls.expiration_datetime_from_raw_text(raw_text, ignore_missing=ignore_missing, text_timezone=text_timezone)
        return f


class AircraftEquipmentStatus(CLPBase):

    __tablename__ = 'aircraft_equipment_status'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    # TODO
    # - separate object for duplicates
    item = sa.Column(sa.String)

    item_object_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('aircraft_equipment_status_item.id'),
        nullable = False,
    )

    item_object = sa.orm.relationship(
        'AircraftEquipmentStatusItem',
    )

    item = association_proxy(
        'item_object',
        'item_text',
    )

    description_object_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('aircraft_equipment_status_description.id'),
        nullable = True,
    )

    description_object = sa.orm.relationship(
        'AircraftEquipmentStatusDescription',
        back_populates = 'aircraft_equipment_status'
    )

    description = association_proxy(
        'description_object',
        'raw_text',
    )

    expiration_datetime = association_proxy(
        'description_object',
        'expiration_datetime',
    )

    ofp_file_id = sa.Column(
        sa.ForeignKey('ofp_file.id'),
        nullable = False,
    )

    ofp_files = sa.orm.relationship(
        'OFPFile',
        back_populates = 'aircraft_equipment_status_list',
    )


class AircraftEquipmentStatusItem(CLPBase):

    __tablename__ = 'aircraft_equipment_status_item'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    item_text = sa.Column(sa.String)
