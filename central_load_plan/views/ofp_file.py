import glob
import logging
import os

from flask import Blueprint
from flask import current_app

from central_load_plan.extension import db
from central_load_plan.flight_plan_parser import FlightPlanParser
from central_load_plan.models import OFPFile
from central_load_plan.schema import OperationalFlightPlanSchema

ofp_file_bp = Blueprint('ofp_file', __name__)


@ofp_file_bp.cli.command('load-from-archive')
def load_from_archive():
    """
    Load OFPFile objects from configured glob pattern.
    """
    logger = logging.getLogger(f'{__name__}.load_from_archive')

    glob_pattern = current_app.config.get('ARCHIVE_GLOB_PATTERN')

    if glob_pattern is None:
        raise ValueError(f'No glob pattern configured in ARCHIVE_GLOB_PATTERN')

    existing = db.session.scalars(db.select(OFPFile.archive_path)).all()

    paths = glob.iglob(
        '/home/hitbox/repos/atsg/lido-middleware/instance/archive'
        '/atsgioccmw01/transfers$/Lufthansa/CLP/EFF/Archive_EFF'
        '/**/*.xml',
        recursive = True,
    )
    flight_plan_parser = FlightPlanParser()
    for count, path in enumerate(paths, start=1):
        if path not in existing and os.path.isfile(path):
            ofp_strings = flight_plan_parser.parse_path(path)

            ofp_schema = OperationalFlightPlanSchema()

            ofp_file = ofp_schema.load(ofp_strings, session=db.session)
            # No original path because this is the archive
            ofp_file.archive_path = path

            db.session.add(ofp_file)
            logger.info('loaded %s', path)

    db.session.commit()
