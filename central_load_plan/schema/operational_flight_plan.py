import re

from datetime import timedelta

import marshmallow

from marshmallow import Schema
from marshmallow.fields import Date
from marshmallow.fields import DateTime
from marshmallow.fields import Float
from marshmallow.fields import Integer
from marshmallow.fields import List
from marshmallow.fields import Method
from marshmallow.fields import Nested
from marshmallow.fields import String
from marshmallow.fields import Time
from marshmallow.validate import OneOf
from marshmallow.validate import ValidationError
from marshmallow_sqlalchemy.fields import Nested
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from central_load_plan.extension import db
from central_load_plan.models import AircraftEquipmentStatus
from central_load_plan.models import CrewMember
from central_load_plan.models import AircraftEquipmentStatusDescription
from central_load_plan.models import OFPFile


# ex: PT1H30M45S
DURATION_FMT = 'PT%HH%MM%SS'

excessive_whitespace_re = re.compile(r'\s{2,}')
DATE_UTC_FORMAT = '%Y-%m-%dZ'

def compress_whitespace(string):
    return re.sub(excessive_whitespace_re, ' ', string)

class CrewSchema(Schema):
    """
    Schema for crewmembers added from external database.
    """

    first_name = String()
    last_name = String()
    employee_number = String()

    seat = String()
    seat_order = Integer()

    source = String()


class EFFArchivePathSchema(Schema):
    """
    Deserialize the path data for EFF archive files.
    """

    airline_code = String(validate=OneOf(['8C', 'GB']))
    archive_date = Date()
    origin = String()
    destination = String()
    timestamp = Time(
        format = '%H%M%S',
        metadata = {
            'help': 'The {now} timestamp when the file was moved to archive.',
        },
    )

    # RegexParser(include_string='path')
    path = String()


def raise_for_mixed_units(data, suffix='_unit', ignore_none=True):
    """
    Raise if all suffixed keys do not agree, perfectly.
    """
    units = set()
    for key, value in data.items():
        if ignore_none and value is None:
            continue
        if key.endswith(suffix):
            units.add(value)
    if len(units) != 1:
        raise ValidationError('Mixed units %r' % units)

    the_only_unit = next(iter(units))
    return the_only_unit

class AircraftEquipmentStatusDescriptionSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = AircraftEquipmentStatusDescription
        load_instance = True
        sqla_session = db.session

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # raw_text -> instance, lives for this load() call
        self._description_cache = {}

    def get_instance(self, data):
        raw_text = data.get('raw_text')
        if raw_text is None:
            return None

        # Return already-seen instance from this batch first,
        # before touching the DB at all.
        if raw_text in self._description_cache:
            instance = self._description_cache[raw_text]
            return instance

        with db.session.no_autoflush:
            instance = (
                db.session.query(AircraftEquipmentStatusDescription)
                .where(AircraftEquipmentStatusDescription.raw_text == raw_text)
                .one_or_none()
            )

        if instance is None:
            ModelClass = self.opts.model
            expiration_datetime = ModelClass.expiration_datetime_from_raw_text(raw_text, ignore_missing=True)
            instance = ModelClass(
                raw_text = raw_text, 
                expiration_datetime = expiration_datetime,
            )
            self._description_cache[raw_text] = instance

        return instance

    #def make_instance(self, data, **kwargs):
    #    instance = super().make_instance(data, **kwargs)
    #    if instance.raw_text:
    #        self._description_cache[instance.raw_text] = instance
    #    return instance


class AircraftEquipmentStatusSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = AircraftEquipmentStatus
        load_instance = True
        sqla_session = db.session

    description_object = Nested(AircraftEquipmentStatusDescriptionSchema, many=False)


class CrewMemberSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = CrewMember
        load_instance = True
        sqla_session = db.session


class OperationalFlightPlanSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = OFPFile
        load_instance = True
        sqla_session = db.session

    # Overrides
    flight_origin_date = Date(format=DATE_UTC_FORMAT)
    estimated_block_time = Time(format=DURATION_FMT)
    estimated_time_enroute = Time(format=DURATION_FMT)

    # Add relationships
    aircraft_equipment_status_list = Nested(
        AircraftEquipmentStatusSchema,
        load_default = list,
        many = True,
    )
    crewmembers = Nested(CrewMemberSchema, many=True)
