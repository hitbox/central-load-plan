import code
import glob
import json
import logging
import os

from pprint import pprint

import click

from flask import Blueprint
from flask import current_app
from sqlalchemy.orm import Session

from central_load_plan.engine import get_lsyrept_engine
from central_load_plan.extension import db
from central_load_plan.flight_plan_parser import FlightPlanParser
from central_load_plan.models import OFPFile
from central_load_plan.models.archive import FolderWalk
from central_load_plan.models.lsyrept import crew_members_from_ofp
from central_load_plan.schema import OperationalFlightPlanSchema
from central_load_plan.service import build_jobs

ofp_file_bp = Blueprint('ofp_file', __name__)

ofp_file_bp.cli.help = 'Command line utility to load OFPFile objects from archive.'

@ofp_file_bp.cli.command('load-from-archive')
@click.option(
    '--commit-every',
    type = int,
)
@click.option(
    '--config-var',
    required = True,
    help = 'Name of config var of iterable object to get archive OFP paths.'
)
def load_from_archive(commit_every, config_var):
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
    for index, path_data in enumerate(file_walker):
        logger.info('examining %s', path_data)
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

            # commit every N records
            if commit_every and index % commit_every == 0:
                db.session.commit()

    db.session.commit()

@ofp_file_bp.cli.command('adhoc')
@click.option('--limit', type=int, default=10)
def adhoc(limit):
    """
    Re-send/re-do the JSON output jobs' work for some amount of recent ofp file
    database objects.
    """
    # RESEND JSON FILES
    logger = logging.getLogger(f'{__name__}.load_from_archive')
    query = (
        db.select(OFPFile)
        .where(OFPFile.archive_path.is_not(None))
        .order_by(OFPFile.mtime.desc())
        .limit(limit)
    )
    files = db.session.scalars(query).all()

    flight_plan_parser = FlightPlanParser()
    flight_plan_schema = OperationalFlightPlanSchema()

    logger.info('resending json files')

    has_crew = []
    files_and_jobs = []
    for ofp_file in files:
        jobs = build_jobs(db.session, ofp_file.archive_path, flight_plan_parser, flight_plan_schema)
        for job in jobs:
            if job.job_type_name == 'JSON_FILE':
                job.do_work()
                click.echo(ofp_file.archive_path)
