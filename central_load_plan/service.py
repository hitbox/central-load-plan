"""
Service layer for processing OFP files and executing jobs.
"""
import os
import logging

import sqlalchemy as sa

from central_load_plan.models import OFPFile
from central_load_plan.models import JobTemplate

logger = logging.getLogger(__name__)

def build_jobs(db_session, path, flight_plan_parser, flight_plan_schema):
    """
    Parse a single file path and build Job objects.
    Pure-ish function: no DB commits, only constructs jobs.
    """
    if not os.path.isfile(path):
        return []

    path = os.path.normpath(path)

    ofp_strings = flight_plan_parser.parse_path(path)
    ofp_strings["original_path"] = path

    ofp_file = flight_plan_schema.load(ofp_strings)

    job_templates = JobTemplate.all_matches_sorted_for_execution(
        db_session,
        ofp_file,
    )

    jobs = []
    for job_template in job_templates:
        jobs.append(job_template.make_job(ofp_file))

    return jobs

def run_jobs(db_session, jobs):
    """
    Execute a list of jobs with DB transaction handling.
    Owns side effects (job execution + commit/rollback).
    """
    for job in jobs:
        db_session.add(job)

        try:
            job.do_work()
            db_session.commit()

        except KeyboardInterrupt:
            raise

        except Exception:
            db_session.rollback()
            logger.exception("Exception occurred during job execution: %s", job)

def get_ofp_file(db_session, path):
    query = sa.select(OFPFile).where(OFPFile.original_path == path)
    return db_session.scalars(query).one_or_none()

def process_path(db_session, path, flight_plan_parser, flight_plan_schema):
    """
    High-level convenience function to run jobs against a new path.
    """
    # incoming paths are named simply and can often be duplicated later.
    jobs = build_jobs(
        db_session = db_session,
        path = path,
        flight_plan_parser = flight_plan_parser,
        flight_plan_schema = flight_plan_schema,
    )

    run_jobs(db_session, jobs)
