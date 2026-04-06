"""
Command line utilities for processing files with Job objects.
"""
import glob
import os

import click
import sqlalchemy as sa

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy.orm import Session

from central_load_plan.extension import db
from central_load_plan.extension import login_manager
from central_load_plan.flight_plan_parser import FlightPlanParser
from central_load_plan.models import JobTemplate
from central_load_plan.models import OFPFile
from central_load_plan.schema import OperationalFlightPlanSchema

job_bp = Blueprint('job', __name__)

@job_bp.cli.command('load')
@click.option('--glob_pattern')
@click.option('--config-var')
@click.option('--recursive/--no-recursive')
def load(glob_pattern, config_var, recursive):
    """
    Load OFPFile objects from glob pattern and process jobs.
    """
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
                'size': os.path.getsize(path),
                'mtime': os.path.getmtime(path),
                'original_path': path,
            })

            ofp_file = flight_plan_schema.load(ofp_strings)

            job_templates = JobTemplate.all_matches_sorted_for_execution(
                db.session,
                ofp_file,
            )
            jobs = []
            for job_template in job_templates:
                job = job_template.make_job(ofp_file)
                db.session.add(job)
                job.do_work()
            db.session.commit()
