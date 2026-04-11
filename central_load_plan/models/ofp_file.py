import os
import time
import uuid

from datetime import timedelta
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session

from .clp_base import CLPBase

from central_load_plan.engine import get_lsyrept_engine

class OFPFile(CLPBase):
    """
    OFP XML file scraped for data.
    """

    __tablename__ = 'ofp_file'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    original_path = sa.Column(sa.String, nullable=True)

    size = sa.Column(
        sa.Integer,
        nullable = False,
        comment = 'os.path.getsize value',
    )

    mtime = sa.Column(
        sa.Integer,
        nullable = False,
        comment = 'os.path.getmtime value',
    )

    @property
    def mtime_age(self):
        return time.time() - self.mtime

    archive_path = sa.Column(
        sa.String,
        nullable=True,
        info = {
            'help': 'Existing path.',
        },
    )

    @property
    def display_path(self):
        if self.archive_path is not None:
            return self.archive_path
        else:
            return self.original_path

    flight_plan_id = sa.Column(sa.String, nullable=False)

    leg_departure_date_utc = sa.Column(sa.DateTime(timezone=True), nullable=False)

    flight_origin_date = sa.Column(sa.Date)

    version_number = sa.Column(sa.String)

    flight_number = sa.Column(sa.Integer)

    flight_identifier = sa.Column(sa.String)

    airline_iata_code = sa.Column(sa.String)

    origin_iata = sa.Column(sa.String)

    destination_iata = sa.Column(sa.String)

    aircraft_registration = sa.Column(sa.String)

    estimated_block_time = sa.Column(sa.Time)

    estimated_time_enroute = sa.Column(sa.Time)

    scheduled_departure_time = sa.Column(sa.DateTime(timezone=True))

    estimated_departure_time = sa.Column(sa.DateTime(timezone=True))

    planned_payload = sa.Column(sa.Integer)

    planned_payload_unit = sa.Column(sa.String)

    ramp_fuel = sa.Column(sa.Integer)

    ramp_fuel_unit = sa.Column(sa.String)

    fuel_burn = sa.Column(sa.Integer)

    fuel_burn_unit = sa.Column(sa.String)

    taxi_fuel = sa.Column(sa.Integer)

    taxi_fuel_unit = sa.Column(sa.String)

    takeoff_fuel = sa.Column(sa.Integer)

    takeoff_fuel_unit = sa.Column(sa.String)

    landing_fuel = sa.Column(sa.Integer)

    landing_fuel_unit = sa.Column(sa.String)

    ballast_fuel = sa.Column(sa.Integer)

    ballast_fuel_unit = sa.Column(sa.String)

    mzfw = sa.Column(sa.Integer)

    mzfw_unit = sa.Column(sa.String)

    mtow = sa.Column(sa.Integer)

    mtow_unit = sa.Column(sa.String)

    mldg = sa.Column(sa.Integer)

    mldg_unit = sa.Column(sa.String)

    dow = sa.Column(sa.Integer)

    dow_unit = sa.Column(sa.String)

    aircraft_equipment_status_list = sa.orm.relationship(
        'AircraftEquipmentStatus',
        back_populates = 'ofp_files',
    )

    crewmembers = sa.orm.relationship(
        'CrewMember',
        back_populates = 'ofp_files',
        order_by = 'CrewMember.seat_order',
    )

    jobs = sa.orm.relationship(
        'Job',
        back_populates = 'ofp_file',
    )

    @property
    def flight_origin_date_mdy(self):
        return self.flight_origin_date.strftime('%d%b%y')

    @property
    def estimated_arrival_time(self):
        return self.estimated_departure_time + timedelta(
            hours = self.estimated_block_time.hour,
            minutes = self.estimated_block_time.minute,
        )

    @property
    def flight_identifier_first_three(self):
        return self.flight_identifier[:3]

    @property
    def unit_for_reporting(self):
        return f'{self.planned_payload_unit.upper()}S'

    @property
    def runtime(self):
        return datetime.now()

    __dict_keys__ = [
        'aircraft_equipment_status_list',
        'aircraft_registration',
        'airline_iata_code',
        'archive_path',
        'ballast_fuel',
        'ballast_fuel_unit',
        'crewmembers',
        'destination_iata',
        'dow',
        'dow_unit',
        'estimated_arrival_time',
        'estimated_block_time',
        'estimated_departure_time',
        'estimated_time_enroute',
        'flight_identifier',
        'flight_identifier_first_three',
        'flight_number',
        'flight_origin_date',
        'flight_plan_id',
        'fuel_burn',
        'fuel_burn_unit',
        'id',
        'runtime',
        'landing_fuel',
        'landing_fuel_unit',
        'leg_departure_date_utc',
        'mldg',
        'mldg_unit',
        'mtow',
        'mtow_unit',
        'mzfw',
        'mzfw_unit',
        'origin_iata',
        'original_path',
        'planned_payload',
        'planned_payload_unit',
        'ramp_fuel',
        'ramp_fuel_unit',
        'scheduled_departure_time',
        'takeoff_fuel',
        'takeoff_fuel_unit',
        'taxi_fuel',
        'taxi_fuel_unit',
        'unit_for_reporting',
        'version_number',
    ]

    def update_from_path(self, session, path):
        from central_load_plan.flight_plan_parser import FlightPlanParser
        from central_load_plan.schema import OperationalFlightPlanSchema

        if os.path.isfile(path) and os.path.getsize(path) > 0:
            # Is non-empty file.
            # Parse
            flight_plan_parser = FlightPlanParser()
            ofp_strings = flight_plan_parser.parse_path(path)

            # Deserialize
            ofp_schema = OperationalFlightPlanSchema()
            ofp_file = ofp_schema.load(ofp_strings, transient=True)
            ofp_file.archive_path = path

            for key in self.__dict_keys__:
                if key != 'id':
                    try:
                        setattr(self, key, getattr(ofp_file, key))
                    except AttributeError:
                        # ignore properties without setters
                        pass

    def as_dict(self):
        return {k: getattr(self, k) for k in self.__dict_keys__}

    def as_dict_with_crew(self):
        from central_load_plan.models.lsyrept import crew_members_from_ofp

        ofp_data = self.as_dict()
        engine = get_lsyrept_engine(self.airline_iata_code)
        with Session(engine) as session:
            crewmembers_result = crew_members_from_ofp(session, self)
            ofp_data['crewmembers'] = crewmembers_result['crew_members']

        return ofp_data

    @property
    def has_crew(self):
        ofp_data = self.as_dict_with_crew()
        return bool(ofp_data['crewmembers'])
