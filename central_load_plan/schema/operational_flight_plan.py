import re

from datetime import timedelta

from marshmallow import Schema
from marshmallow.fields import Date
from marshmallow.fields import Float
from marshmallow.fields import Integer
from marshmallow.fields import List
from marshmallow.fields import Method
from marshmallow.fields import Nested
from marshmallow.fields import String
from marshmallow.fields import Time
from marshmallow.validate import OneOf
from marshmallow.validate import ValidationError
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

class AircraftEquipmentStatusDescription(SQLAlchemyAutoSchema):

    class Meta:
        model = AircraftEquipmentStatusDescription
        load_instance = True
        sqla_session = db.session


class AircraftEquipmentStatusSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = AircraftEquipmentStatus
        load_instance = True
        sqla_session = db.session

    description_object = Nested(AircraftEquipmentStatusDescription, many=False)


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
    aircraft_equipment_status_list = Nested(AircraftEquipmentStatusSchema, many=True)
    crewmembers = Nested(CrewMemberSchema, many=True)
