import re

from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo

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
from central_load_plan.models import AircraftEquipmentStatusDescription
from central_load_plan.models import AircraftEquipmentStatusItem
from central_load_plan.models import AircraftRegistration
from central_load_plan.models import Airline
from central_load_plan.models import Airport
from central_load_plan.models import CrewMember
from central_load_plan.models import OFPFile

# ex: PT1H30M45S
DURATION_FMT = 'PT%HH%MM%SS'

excessive_whitespace_re = re.compile(r'\s{2,}')
DATE_UTC_FORMAT = '%Y-%m-%dZ'

def compress_whitespace(string):
    return re.sub(excessive_whitespace_re, ' ', string)

class BaseSchema(SQLAlchemyAutoSchema):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = {}

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
        self._cache = {}

    def get_instance(self, data):
        raw_text = data.get('raw_text')
        if raw_text is None:
            return None

        # Return already-seen instance from this batch first,
        # before touching the DB at all.
        if raw_text in self._cache:
            instance = self._cache[raw_text]
            return instance

        with db.session.no_autoflush:
            instance = (
                db.session.query(AircraftEquipmentStatusDescription)
                .where(AircraftEquipmentStatusDescription.raw_text == raw_text)
                .one_or_none()
            )

        if instance is None:
            ModelClass = self.opts.model
            instance = ModelClass(**data)
            db.session.add(instance)
            self._cache[raw_text] = instance

        return instance


class AircraftEquipmentStatusItemSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = AircraftEquipmentStatusItem
        load_instance = True
        sqla_session = db.session

    item_text = String()

    def get_instance(self, data, *args, **kwargs):
        item_text = data.get('item_text')
        if not isinstance(item_text, str):
            breakpoint()
            return None

        cache = db.session.info.setdefault(f'{self.__class__.__name__}_cache', {})

        # Return already-seen instance from this batch first,
        # before touching the DB at all.
        if item_text in cache:
            instance = cache[item_text]
            return instance

        instance = super().get_instance(data)
        if instance is None:
            instance = self.opts.model(**data)
            cache[item_text] = instance

        return instance


class AircraftEquipmentStatusSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = AircraftEquipmentStatus
        load_instance = True
        sqla_session = db.session

    item_object = Nested(AircraftEquipmentStatusItemSchema, many=False)

    description_object = Nested(AircraftEquipmentStatusDescriptionSchema, many=False, allow_none=True)


class CrewMemberSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = CrewMember
        load_instance = True
        sqla_session = db.session


class AirportSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = Airport
        load_instance = True
        sqla_session = db.session

    def get_instance(self, data, *args, **kwargs):
        iata_code = data.get('iata_code')
        if not isinstance(iata_code, str):
            return None

        cache = db.session.info.setdefault(
            f'{self.__class__.__name__}_cache',
            {},
        )

        # Return already-seen instance from this batch first,
        # before touching the DB at all.
        if iata_code in cache:
            instance = cache[iata_code]
            return instance
        else:
            instance = super().get_instance(data)
            if instance is None:
                instance = db.session.scalars(
                    db.select(Airport)
                    .where(Airport.iata_code == iata_code)
                ).one_or_none()

        if instance is None:
            instance = self.opts.model(**data)
            cache[iata_code] = instance

        return instance


class AircraftRegistrationSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = AircraftRegistration
        load_instance = True
        sqla_session = db.session

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # raw_text -> instance, lives for this load() call
        self._cache = {}

    def get_instance(self, data):
        registration_number = data.get('registration_number')
        if registration_number is None:
            return None

        # Return already-seen instance from this batch first,
        # before touching the DB at all.
        if registration_number in self._cache:
            instance = self._cache[registration_number]
            return instance

        ModelClass = self.opts.model
        with db.session.no_autoflush:
            instance = (
                db.session.query(ModelClass)
                .where(ModelClass.registration_number == registration_number)
                .one_or_none()
            )

        if instance is None:
            instance = ModelClass(
                registration_number = registration_number
            )
            self._cache[registration_number] = instance

        return instance


class AirlineSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = Airline
        load_instance = True
        sqla_session = db.session

    icao_code = String(allow_none=True)

    def get_instance(self, data):
        """
        Lookup Airline from IATA code.
        """
        iata_code = data.get('iata_code')
        if iata_code is None:
            return None

        cache = db.session.info.setdefault(
            f'{Airline}_cache',
            {},
        )

        # Return already-seen instance from this batch first,
        # before touching the DB at all.
        if iata_code in cache:
            instance = cache[iata_code]
            return instance

        ModelClass = self.opts.model
        with db.session.no_autoflush:
            query = (
                db.select(ModelClass)
                .where(ModelClass.iata_code == iata_code)
            )
            instance = db.session.scalars(query).one()

        if instance is None:
            instance = ModelClass(
                iata_code = iata_code
            )
            cache[iata_code] = instance

        return instance



class OperationalFlightPlanSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = OFPFile
        load_instance = True
        sqla_session = db.session

    airline_object = Nested(AirlineSchema)

    # Overrides
    flight_origin_date = Date(format=DATE_UTC_FORMAT)
    estimated_block_time = Time(format=DURATION_FMT)
    estimated_time_enroute = Time(format=DURATION_FMT)

    origin_airport = Nested(AirportSchema)
    destination_airport = Nested(AirportSchema)

    aircraft_registration = Nested(AircraftRegistrationSchema)

    # Add relationships
    aircraft_equipment_status_list = Nested(
        AircraftEquipmentStatusSchema,
        load_default = list,
        many = True,
    )
    crewmembers = Nested(CrewMemberSchema, many=True)

    def get_instance(self, data):
        registration_number = data.get('registration_number')
        if registration_number is None:
            return None

        # Return already-seen instance from this batch first,
        # before touching the DB at all.
        if registration_number in self._cache:
            instance = self._cache[registration_number]
            return instance

        ModelClass = self.opts.model
        with db.session.no_autoflush:
            instance = (
                db.session.query(ModelClass)
                .where(ModelClass.registration_number == registration_number)
                .one_or_none()
            )

        if instance is None:
            instance = ModelClass(
                registration_number = registration_number
            )
            self._cache[registration_number] = instance

        return instance

