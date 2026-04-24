"""
Command line utilities for processing files with Job objects.
"""
import glob
import logging
import os
import time

import click

from flask import Blueprint
from flask import current_app

from central_load_plan.extension import db
from central_load_plan.flight_plan_parser import FlightPlanParser
from central_load_plan.models import JobTemplate
from central_load_plan.models import OFPFile
from central_load_plan.schema import OperationalFlightPlanSchema

from central_load_plan import service

job_bp = Blueprint('job', __name__)

job_bp.cli.help = 'Command line interface for normal file processing.'

@job_bp.cli.command('process')
@click.option('--glob_pattern')
@click.option('--config-var')
@click.option('--recursive/--no-recursive')
def process(glob_pattern, config_var, recursive):
    """
    Find new files with given glob pattern or names for one from config, and
    process configured jobs for them.
    """
    if glob_pattern and config_var:
        raise click.UsageError(f'Options are mutually exclusive.')

    if config_var:
        glob_pattern = current_app.config[config_var]

    flight_plan_parser = FlightPlanParser()
    flight_plan_schema = OperationalFlightPlanSchema()

    for path in glob.iglob(glob_pattern, recursive=recursive):
        service.process_path(db.session, path, flight_plan_parser, flight_plan_schema)

@job_bp.cli.command('process-forever')
@click.option('--glob_pattern')
@click.option('--config-var')
@click.option('--recursive/--no-recursive')
def process_forver(glob_pattern, config_var, recursive):
    """
    Find new files with given glob pattern or names for one from config, and
    process configured jobs for them.
    """
    if glob_pattern and config_var:
        raise click.UsageError(f'Options are mutually exclusive.')

    if config_var:
        glob_pattern = current_app.config[config_var]

    flight_plan_parser = FlightPlanParser()
    flight_plan_schema = OperationalFlightPlanSchema()

    while True:
        for path in glob.iglob(glob_pattern, recursive=recursive):
            service.process_path(db.session, path, flight_plan_parser, flight_plan_schema)
        time.sleep(1)

@job_bp.cli.command('process-existing')
def process_existing():
    """
    Run jobs against existing files.
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
