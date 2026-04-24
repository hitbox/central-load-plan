import glob
import logging
import os

from pprint import pprint

import click

from flask import Blueprint
from flask import current_app

from central_load_plan.extension import db
from central_load_plan.flight_plan_parser import FlightPlanParser
from central_load_plan.models import OFPFile
from central_load_plan.schema import OperationalFlightPlanSchema

ofp_file_bp = Blueprint('ofp_file', __name__)

ofp_file_bp.cli.help = 'Command line utility to load OFPFile objects from archive.'

@ofp_file_bp.cli.command('load-from-archive')
@click.option('--config-var', help='Name of config var of iterable object to get archive OFP paths.')
def load_from_archive(config_var):
    """
    Load OFPFile objects from configured glob pattern.
    """
    logger = logging.getLogger(f'{__name__}.load_from_archive')

    file_walker = current_app.config.get(config_var)

    if file_walker is None:
        raise ValueError(f'No config var {config_var}')

    logger.info(f'Searching {file_walker=}')

    existing = set(db.session.scalars(db.select(OFPFile.archive_path)).all())

    ofp_schema = OperationalFlightPlanSchema()

    flight_plan_parser = FlightPlanParser()
    for path_data in file_walker:
        path = os.path.normpath(path_data['full'])
        # Size check because we're not using the conditions on Job objects.
        if path not in existing and os.path.isfile(path) and os.path.getsize(path) > 0:
            # Parse XML for strings
            ofp_strings = flight_plan_parser.parse_path(path)
            ofp_strings['archive_path'] = path

            # Create database object.
            ofp_file = ofp_schema.load(ofp_strings, session=db.session)
            # No original path because this is the archive
            ofp_file.archive_path = path

            db.session.add(ofp_file)
            logger.info('loaded %s', path)

    db.session.commit()
