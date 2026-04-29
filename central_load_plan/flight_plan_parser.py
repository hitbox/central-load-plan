import argparse
import os
import xml.etree.ElementTree as ET

from pprint import pprint
from zoneinfo import ZoneInfo

from .models import AircraftEquipmentStatusDescription
from .constants import flight_plan_namespaces
from .xml_parser import NestedXMLField
from .xml_parser import Parser
from .xml_parser import XMLField
from central_load_plan.parsers.expiration_datetime import make_expiration_datetime_from_raw_text_parser

class FlightPlanXMLField(XMLField):
    """
    XMLField with the default namespaces for xpaths in and OFP XML file.
    """

    def __init__(self, xpath, **kwargs):
        kwargs.setdefault('namespaces', flight_plan_namespaces)
        super().__init__(xpath, **kwargs)

class ConstantField(XMLField):

    def __init__(self, value):
        self.value = value

    def extract(self, root):
        return self.value


class MethodField(XMLField):
    """
    Take the value as XMLField would and run a function on it and return it.
    """

    def __init__(
        self,
        func,
        xpath = '.',
        name = None,
        attr = None,
        default = None,
        cast = str,
        multiple = False,
        namespaces = None,
        raise_for_exists = True,
        subfield = None,
    ):
        super().__init__(
            xpath = xpath,
            name = name,
            attr = attr,
            default = default,
            cast = cast,
            multiple = multiple,
            namespaces = namespaces,
            raise_for_exists = raise_for_exists,
            subfield = subfield,
        )
        self.func = func

    def extract(self, root):
        value = super().extract(root)
        return self.func(value)


class NestedFlightPlanXMLField(FlightPlanXMLField, NestedXMLField):
    pass


class AircraftEquipmentStatusDescriptionField(NestedFlightPlanXMLField):
    """
    Nested XML schema rooted at a <Title> element.
    """

    raw_text = FlightPlanXMLField(
        '.',
        raise_for_exists = False, # allow not found
    )

    expiration_datetime = MethodField(
        func = make_expiration_datetime_from_raw_text_parser(
            ignore_missing = True, # some do not have expiration date strings
            text_timezone = ZoneInfo('US/Eastern'), # source text assumed local ILN time.
            ignore_no_match = True, # some date strings are just impossible
        ),
        xpath = '.',
        raise_for_exists = False, # allow not found
    )


class AircraftEquipmentStatusItemField(NestedFlightPlanXMLField):
    """
    Nested XML schema rooted at a <Title> element.
    """

    item_text = FlightPlanXMLField(
        './ns:ReferenceId',
        raise_for_exists = True,
    )


class AircraftEquipmentStatusField(NestedFlightPlanXMLField):
    """
    Nested XML schema rooted at a single <MELCDLItem> element.
    """

    item_object = AircraftEquipmentStatusItemField(
        '.',
    )

    description_object = AircraftEquipmentStatusDescriptionField(
        xpath = './ns:Title',
        raise_for_exists = False, # Title is some times missing.
        multiple = False, # only one nested object
    )


class AirportXMLField(NestedFlightPlanXMLField):

    iata_code = FlightPlanXMLField(
        './ns:AirportIATACode',
    )


class AircraftRegistrationXMLField(NestedFlightPlanXMLField):

    registration_number = FlightPlanXMLField(
        './ns:Aircraft',
        name = 'registration_number',
        attr = 'aircraftRegistration',
    )


class AirlineXMLField(NestedFlightPlanXMLField):

    iata_code = FlightPlanXMLField(
        xpath = '.',
        attr = 'airlineIATACode',
    )



class FlightPlanParser(Parser):

    flight_plan_id = FlightPlanXMLField('.', attr='flightPlanId')

    flight_origin_date = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Flight',
        attr = 'flightOriginDate',
    )

    version_number = FlightPlanXMLField(
        '.', # root <FlightPlan> tag.
        attr = 'flightPlanId',
    )

    flight_number = FlightPlanXMLField(
        './ns:M633SupplementaryHeader'
        '/ns:Flight'
        '/ns:FlightIdentification'
        '/ns:FlightNumber',
        attr = 'number',
    )

    # XXX: replaced below
    #airline_iata_code = FlightPlanXMLField(
    #    './ns:M633SupplementaryHeader/ns:Flight/ns:FlightIdentification/ns:FlightNumber',
    #    attr = 'airlineIATACode',
    #)

    airline_object = AirlineXMLField(
        xpath = './ns:M633SupplementaryHeader'
                '/ns:Flight'
                '/ns:FlightIdentification'
                '/ns:FlightNumber',
    )

    # NEED UNIT Field for now to avoid raising mixed
    planned_payload_unit = FlightPlanXMLField(
        './ns:WeightHeader/ns:Load/ns:EstimatedWeight/ns:Value',
        attr = 'unit',
    )
    leg_departure_date_utc = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Flight',
        attr='scheduledTimeOfDeparture',
    )

    flight_identifier = FlightPlanXMLField(
        'ns:M633SupplementaryHeader/ns:Flight/ns:FlightIdentification/ns:FlightIdentifier',
    )

    estimated_departure_time = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Flight',
        attr='scheduledTimeOfDeparture',
    )

    flight_number = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Flight/ns:FlightIdentification/ns:FlightNumber',
        attr='number',
    )

    origin_airport = AirportXMLField(
        './ns:M633SupplementaryHeader/ns:Flight/ns:DepartureAirport',
    )

    #origin_iata = FlightPlanXMLField(
    #    './ns:M633SupplementaryHeader/ns:Flight/ns:DepartureAirport',
    #)

    destination_airport = AirportXMLField(
        './ns:M633SupplementaryHeader/ns:Flight/ns:ArrivalAirport',
    )

    #destination_iata = FlightPlanXMLField(
    #    './ns:M633SupplementaryHeader/ns:Flight/ns:ArrivalAirport/ns:AirportIATACode',
    #)

    aircraft_registration = FlightPlanXMLField(
        './ns:M633SupplementaryHeader',
        subfield = FlightPlanXMLField(
            './ns:Aircraft',
            name = 'registration_number',
            attr = 'aircraftRegistration',
        ),
    )

    aircraft_registration = AircraftRegistrationXMLField(
        './ns:M633SupplementaryHeader',
    )

    estimated_block_time = FlightPlanXMLField(
        './ns:FlightPlanSummary/ns:BlockTime/ns:EstimatedTime/ns:Value',
    )

    scheduled_departure_time = FlightPlanXMLField(
        'ns:M633SupplementaryHeader/ns:Flight',
        attr = 'scheduledTimeOfDeparture',
    )

    estimated_time_enroute = FlightPlanXMLField(
        './ns:FlightPlanSummary/ns:FlightTime/ns:EstimatedTime/ns:Value',
    )

    planned_payload = FlightPlanXMLField(
        './ns:WeightHeader/ns:Load/ns:EstimatedWeight/ns:Value',
    )

    planned_payload_unit = FlightPlanXMLField(
        './ns:WeightHeader/ns:Load/ns:EstimatedWeight/ns:Value',
        attr='unit',
    )

    ramp_fuel = FlightPlanXMLField(
        './ns:FuelHeader/ns:BlockFuel/ns:EstimatedWeight/ns:Value',
    )

    ramp_fuel_unit = FlightPlanXMLField(
        './ns:FuelHeader/ns:BlockFuel/ns:EstimatedWeight/ns:Value',
        attr='unit',
    )

    # EXAMPLE:
    # <AdditionalFuels>
    # archive/GB/2025-03-05/KSCKKCVG-std.091103.xml
    # <AdditionalFuel reason="BallastFuel">
    #     <EstimatedWeight>
    #         <Value unit="lb">10000</Value>
    #     </EstimatedWeight>
    #     <Duration>
    #         <Value>PT0H0M00S</Value>
    #     </Duration>
    # </AdditionalFuel>
    ballast_fuel = FlightPlanXMLField(
        xpath = './ns:FuelHeader/ns:AdditionalFuels'
                '/ns:AdditionalFuel[@reason="BallastFuel"]'
                '/ns:EstimatedWeight/ns:Value',
        raise_for_exists = False, # Title is some times missing.
    )

    ballast_fuel_unit = FlightPlanXMLField(
        xpath = './ns:FuelHeader/ns:AdditionalFuels'
                '/ns:AdditionalFuel[@reason="BallastFuel"]'
                '/ns:EstimatedWeight/ns:Value',
        attr = 'unit',
        raise_for_exists = False, # Title is some times missing.
    )

    fuel_burn = FlightPlanXMLField(
        './ns:FuelHeader/ns:TripFuel/ns:EstimatedWeight/ns:Value',
    )

    fuel_burn_unit = FlightPlanXMLField(
        './ns:FuelHeader/ns:TripFuel/ns:EstimatedWeight/ns:Value',
        attr='unit',
    )

    taxi_fuel = FlightPlanXMLField(
        './ns:FuelHeader/ns:TaxiFuel/ns:EstimatedWeight/ns:Value',
    )

    taxi_fuel_unit = FlightPlanXMLField(
        './ns:FuelHeader/ns:TaxiFuel/ns:EstimatedWeight/ns:Value',
        attr='unit',
    )

    landing_fuel = FlightPlanXMLField(
        './ns:FuelHeader/ns:LandingFuel/ns:EstimatedWeight/ns:Value',
    )

    landing_fuel_unit = FlightPlanXMLField(
        './ns:FuelHeader/ns:LandingFuel/ns:EstimatedWeight/ns:Value',
        attr='unit',
    )

    takeoff_fuel = FlightPlanXMLField(
        './ns:FuelHeader/ns:TakeOffFuel/ns:EstimatedWeight/ns:Value',
    )

    takeoff_fuel_unit = FlightPlanXMLField(
        './ns:FuelHeader/ns:TakeOffFuel/ns:EstimatedWeight/ns:Value',
        attr='unit',
    )

    mzfw = FlightPlanXMLField(
        './ns:WeightHeader/ns:ZeroFuelWeight/ns:StructuralLimit/ns:Value',
    )

    mzfw_unit = FlightPlanXMLField(
        './ns:WeightHeader/ns:ZeroFuelWeight/ns:StructuralLimit/ns:Value',
        attr='unit',
    )

    mtow = FlightPlanXMLField(
        './ns:WeightHeader/ns:TakeoffWeight/ns:OperationalLimit/ns:Value',
    )

    mtow_unit = FlightPlanXMLField(
        './ns:WeightHeader/ns:TakeoffWeight/ns:OperationalLimit/ns:Value',
        attr='unit',
    )

    mldg = FlightPlanXMLField(
        './ns:WeightHeader/ns:LandingWeight/ns:OperationalLimit/ns:Value',
    )

    mldg_unit = FlightPlanXMLField(
        './ns:WeightHeader/ns:LandingWeight/ns:OperationalLimit/ns:Value',
        attr='unit',
    )

    dow = FlightPlanXMLField(
        './ns:WeightHeader/ns:DryOperatingWeight/ns:EstimatedWeight/ns:Value',
    )

    dow_unit = FlightPlanXMLField(
        './ns:WeightHeader/ns:DryOperatingWeight/ns:EstimatedWeight/ns:Value',
        attr='unit',
    )

    aircraft_equipment_status_list = FlightPlanXMLField(
        xpath = './/ns:MELCDLItems/ns:MELCDLItem',
        subfield = AircraftEquipmentStatusField(
            xpath = '.',
            multiple = False,
            name = 'mel_cdl_item',
        ),
        multiple = True, # many MELCDLItem elements inside the MELCDLItems element.
        default = list, # empty list if no elements. Entire MELCDLItems
                        # elements have been observed missing.
        raise_for_exists = False,
    )

    def parse_path(self, path):
        data = super().parse_path(path)
        data.update({
            'size': os.path.getsize(path),
            'mtime': os.path.getmtime(path),
        })
        return data


def main(argv=None):
    from central_load_plan.schema import OperationalFlightPlanSchema

    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--schema', action='store_true')
    args = parser.parse_args(argv)

    if not os.path.exists(args.path):
        raise FileNotFoundError(args.path)

    parser = FlightPlanParser()
    data = dict(parser.parse_path(args.path))

    if args.schema:
        # Method attributes don't seem to fire here but do in the view.
        ofp_schema = OperationalFlightPlanSchema()
        data = ofp_schema.load(data)
        print('schema loaded')
        print(data)
    else:
        pprint(data, width=1)

if __name__ == '__main__':
    main()
