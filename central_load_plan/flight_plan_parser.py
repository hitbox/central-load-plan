import os
import argparse
import xml.etree.ElementTree as ET

from pprint import pprint

from .xml_parser import Parser
from .xml_parser import XMLField

flight_plan_namespaces = {
    'ns': 'http://aeec.aviation-ia.net/633',
    'lsya': 'http://www.lido.net/lsya' ,
}

class FlightPlanXMLField(XMLField):
    """
    XMLField with the default namespaces for xpaths in and OFP XML file.
    """

    def __init__(self, xpath, **kwargs):
        kwargs.setdefault('namespaces', flight_plan_namespaces)
        super().__init__(xpath, **kwargs)


class AircraftEquipmentStatusDescriptionField(FlightPlanXMLField):

    raw_text = FlightPlanXMLField(
        './ns:Title',
        raise_for_exists = False, # allow not found
    )



class AircraftEquipmentStatusField(FlightPlanXMLField):

    # expect to be rooted at the MELCDLItem node.

    item = FlightPlanXMLField(
        './ns:ReferenceId',
    )

    description_object = AircraftEquipmentStatusDescriptionField(
        xpath = './ns:Title',
        namespaces = flight_plan_namespaces,
        #raise_for_exists = False, # allow not found
        multiple = False, # only one nested object
    )

    def extract(self, elem):
        data = {}
        for name in dir(self):
            field = getattr(self, name)
            if isinstance(field, XMLField):
                data[field.name] = field.extract(elem)
        return data


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

    airline_iata_code = FlightPlanXMLField(
        './ns:M633SupplementaryHeader'
        '/ns:Flight'
        '/ns:FlightIdentification'
        '/ns:FlightNumber',
        attr = 'airlineIATACode',
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

    airline_iata_code = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Flight/ns:FlightIdentification/ns:FlightNumber',
        attr='airlineIATACode',
    )

    origin_iata = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Flight/ns:DepartureAirport/ns:AirportIATACode',
    )

    destination_iata = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Flight/ns:ArrivalAirport/ns:AirportIATACode',
    )

    aircraft_registration = FlightPlanXMLField(
        './ns:M633SupplementaryHeader/ns:Aircraft',
        attr='aircraftRegistration',
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
        xpath = './/ns:MELCDLItems',
        subfield = AircraftEquipmentStatusField(
            xpath = './ns:MELCDLItem',
            namespaces = flight_plan_namespaces,
        ),
        namespaces = flight_plan_namespaces,
        multiple = True,
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

    parser = FlightPlanParser()
    data = dict(parser.parse_path(args.path))
    pprint(data)

    if args.schema:
        ofp_schema = OperationalFlightPlanSchema()
        data = ofp_schema.load(data)
        print('schema loaded')

        # Method attributes don't seem to fire here but do in the view.

if __name__ == '__main__':
    main()
