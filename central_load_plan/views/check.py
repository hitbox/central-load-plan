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
from central_load_plan.models import EmailFromTemplateJob
from central_load_plan.models import JobTemplate
from central_load_plan.models import OFPFile
from central_load_plan.schema import OperationalFlightPlanSchema

from central_load_plan import service

check_bp = Blueprint('check', __name__)

check_bp.cli.help = 'Command line interface checking application.'

logger = logging.getLogger(__name__)

@check_bp.cli.command('templates')
def check_templates():
    """
    Check database template paths exist.
    """

    missing = []
    models = [
        EmailFromTemplateJob,
    ]
    for model_class in models:
        query = (
            db.select(model_class)
        )
        for instance in db.session.scalars(query):
            if not os.path.exists(instance.template_name):
                missing.append(instance)

    if missing:
        click.echo('Missing templates!')
        for instance in missing:
            click.echo(instance.template_name)
