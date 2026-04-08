"""
Command line utilities for processing files with Job objects.
"""
import glob
import logging
import os

import click

from flask import Blueprint
from flask import current_app

from central_load_plan.extension import db
from central_load_plan.flight_plan_parser import FlightPlanParser
from central_load_plan.models import JobTemplate
from central_load_plan.models import OFPFile
from central_load_plan.schema import OperationalFlightPlanSchema

job_bp = Blueprint('job', __name__)

@job_bp.cli.command('process')
@click.option('--glob_pattern')
@click.option('--config-var')
@click.option('--recursive/--no-recursive')
def process(glob_pattern, config_var, recursive):
    """
    Load OFPFile objects from glob pattern and process jobs.
    """
    logger = logging.getLogger(f'{__name__}.process')
    if glob_pattern and config_var:
        raise click.UsageError(f'Options are mutually exclusive.')

    if config_var:
        glob_pattern = current_app.config[config_var]

    flight_plan_parser = FlightPlanParser()
    flight_plan_schema = OperationalFlightPlanSchema()

    for path in glob.iglob(glob_pattern, recursive=recursive):
        if os.path.isfile(path):
            path = os.path.normpath(path)

            ofp_strings = flight_plan_parser.parse_path(path)
            ofp_strings.update({
                'original_path': path,
            })

            ofp_file = flight_plan_schema.load(ofp_strings)

            job_templates = JobTemplate.all_matches_sorted_for_execution(
                db.session,
                ofp_file,
            )

            for job_template in job_templates:
                job = job_template.make_job(ofp_file)
                db.session.add(job)
                try:
                    job.do_work()
                    db.session.commit()
                except:
                    db.session.rollback()
                    logger.exception(f'An exception occcurred during {job_template.name} work.')

@job_bp.cli.command('process-existing')
def process_existing():
    """
    """
    logger = logging.getLogger(f'{__name__}.process_existing')

    ofp_files = db.session.scalars(db.select(OFPFile))

    for ofp_file in ofp_files:
        job_templates = JobTemplate.all_matches_sorted_for_execution(
            db.session,
            ofp_file,
        )

        for job_template in job_templates:
            job = job_template.make_job(ofp_file)
            db.session.add(job)
            try:
                job.do_work()
                db.session.commit()
            except KeyboardInterrupt:
                break
            except:
                db.session.rollback()
                logger.exception(f'An exception occcurred during {job_template.name} work.')
