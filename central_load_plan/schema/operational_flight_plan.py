import re

from datetime import timedelta

from marshmallow import Schema
from marshmallow import post_load
from marshmallow.fields import Date
from marshmallow.fields import AwareDateTime
from marshmallow.fields import Integer
from marshmallow.fields import List
from marshmallow.fields import Method
from marshmallow.fields import Nested
from marshmallow.fields import String
from marshmallow.fields import Time
from marshmallow.validate import OneOf
from marshmallow.validate import ValidationError

# ex: PT1H30M45S
DURATION_FMT = 'PT%HH%MM%SS'

excessive_whitespace_re = re.compile(r'\s{2,}')

DATE_UTC_FORMAT = '%Y-%m-%dZ'

def compress_whitespace(string):
    return re.sub(excessive_whitespace_re, ' ', string)

class MELCDLItemSchema(Schema):

    item = String()
    description = String(allow_none=True)

    fak_status = Method('fak_status_from_item')

    description_lines = Method('split_description_on_excessive_whitespace')

    def fak_status_from_item(self, data):
        item = data['item']
        if item.endswith('00-30-FAK'):
            fak_status = 0
        elif item.endswith('FAK'):
            fak_status = 1
        else:
            fak_status = 99
        return fak_status

    def split_description_on_excessive_whitespace(self, data):
        return excessive_whitespace_re.split(data['description'])


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


class OperationalFlightPlanSchema(Schema):
    """
    Marshal the Operational Flight Plan XML data.
    """

    datetime_format = '%Y-%m-%dT%H:%M:%SZ'
    # TODO
    # - change to a mapping for the _for_reporting strings
    units = ['kg', 'lb']

    flight_plan_id = String()
    leg_departure_date_utc = AwareDateTime(format=datetime_format, default_timezone="utc")
    flight_origin_date = Date(format=DATE_UTC_FORMAT)
    version_number = String()
    flight_number = Integer() # most lsyrept datasebase tables need integer for crew members
    flight_identifier = String()

    airline_iata_code = String()
    origin_iata = String()
    destination_iata = String()
    aircraft_registration = String()

    estimated_block_time = Time(format=DURATION_FMT)
    estimated_time_enroute = Time(format=DURATION_FMT)

    scheduled_departure_time = AwareDateTime(format=datetime_format, default_timezone="utc")
    estimated_departure_time = AwareDateTime(format=datetime_format, default_timezone="utc")

    planned_payload = Integer()
    planned_payload_unit = String(validate=OneOf(units))

    ramp_fuel = Integer()
    ramp_fuel_unit = String(validate=OneOf(units))

    fuel_burn = Integer()
    fuel_burn_unit = String(validate=OneOf(units))

    taxi_fuel = Integer()
    taxi_fuel_unit = String(validate=OneOf(units))

    takeoff_fuel = Integer()
    takeoff_fuel_unit = String(validate=OneOf(units))

    landing_fuel = Integer()
    landing_fuel_unit = String(validate=OneOf(units))

    ballast_fuel = Integer(allow_none=True)
    ballast_fuel_unit = String(allow_none=True, validate=OneOf(units))

    mzfw = Integer()
    mzfw_unit = String(validate=OneOf(units))

    mtow = Integer()
    mtow_unit = String(validate=OneOf(units))

    mldg = Integer()
    mldg_unit = String(validate=OneOf(units))

    dow = Integer()
    dow_unit = String(validate=OneOf(units))

    aircraft_equipment_status_list = List(Nested(MELCDLItemSchema))
    crewmembers = List(Nested(CrewSchema))

    flight_identifier_first_three = Method('add_flight_identifier_first_three')

    estimated_block_datetime = Method('add_estimated_block_datetime')

    unit_for_reporting = Method('add_unit_for_reporting')

    max_payload = Method('add_max_payload')

    def add_flight_identifier_first_three(self, data):
        return data['flight_identifier'][:3]

    def add_estimated_block_datetime(self, data):
        """
        Calculate and add estimated arrival time as datetime.
        """
        etd = data['estimated_departure_time']
        ste = data['estimated_block_time']
        return etd + timedelta(hours=ste.hour, minutes=ste.minute)

    def add_unit_for_reporting(self, data):
        return data['unit'].upper() + 'S'

    def add_max_payload(self, data):
        calcs = [
            data['mtow'] - data['takeoff_fuel'] - data['dow'],
            data['mldg'] - data['landing_fuel'] - data['dow'],
            data['mzfw'] - data['dow'],
        ]
        return min(calcs)

    @post_load
    def post_load(self, data, **kwargs):
        # Ensure that the scraped unit reporting is consistent, and add it to
        # the data.
        data['unit'] = raise_for_mixed_units(data)
        return data


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

from marshmallow import pre_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy import auto_field

from central_load_plan.extension import db
from central_load_plan.models import AircraftEquipmentStatus
from central_load_plan.models import CrewMember
from central_load_plan.models import OFPFile

class AircraftEquipmentStatusSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AircraftEquipmentStatus
        load_instance = True
        sqla_session = db.session


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


