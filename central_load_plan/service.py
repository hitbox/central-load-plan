"""
Service layer for processing OFP files and executing jobs.
"""
import argparse
import configparser
import glob
import logging.config
import os
import time
import warnings

from datetime import datetime
from datetime import timezone

import sqlalchemy.orm
import sqlalchemy as sa

from central_load_plan.app import create_app
from central_load_plan.extension import db
from central_load_plan.models import Job
from central_load_plan.models import JobTemplate
from central_load_plan.models import OFPFile
from central_load_plan.parsers import FlightPlanParser
from central_load_plan.schema import OperationalFlightPlanSchema

logging_required = {'loggers', 'handlers', 'formatters'}

def build_jobs(path, flight_plan_parser, flight_plan_schema):
    """
    Parse a single file path and build Job objects.
    Pure-ish function: no DB commits, only constructs jobs.
    """
    jobs = []
    if not os.path.isfile(path):
        return jobs

    if not os.path.exists(path):
        return jobs

    path = os.path.normpath(path)

    ofp_strings = flight_plan_parser.parse_path(path)
    ofp_strings["original_path"] = path

    ofp_file = flight_plan_schema.load(ofp_strings)

    job_templates = JobTemplate.all_matches_sorted_for_execution(
        db.session,
        ofp_file,
    )

    for job_template in job_templates:
        if job_template.is_enabled:
            jobs.append(job_template.make_job(ofp_file))

    return jobs

def work(args, cp):
    """
    Run pending jobs from database forever.
    """
    work_cp = cp['work']
    sleep_seconds = work_cp.getfloat('sleep_seconds', fallback=1.0)
    logger = logging.getLogger('central_load_plan.service.work')

    logger.info('starting work loop')

    while True:
        files_with_pending_jobs_query = (
            sa.select(OFPFile)
            .where(
                OFPFile.archive_path.is_(None),
                OFPFile.jobs.any(
                    Job.completed_at.is_(None),
                )
            )
            .options(
                sa.orm.selectinload(OFPFile.jobs)
            )
        )
        #sql = files_with_pending_jobs_query.compile(
        #    db.engine,
        #    compile_kwargs = {
        #        'literal_binds': True,
        #    },
        #)

        for ofp_file in db.session.scalars(files_with_pending_jobs_query):
            for job in ofp_file.jobs:
                if job.completed_at is None:
                    job.do_work()
                    job.completed_at = datetime.now(timezone.utc)
                    db.session.commit()
                    logger.info('job %s complete', job)

        logger.info('sleeping %s seconds', sleep_seconds)
        time.sleep(sleep_seconds)

def get_mtime_utc(path):
    return datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)

def instance_from_path(path):
    path = os.path.normpath(path)
    try:
        mtime = get_mtime_utc(path)
    except FileNotFoundError:
        # the job service could have moved our file while we were looking at it
        # again because of glob.
        return None

    exists_query = (
        db.select(OFPFile)
        .where(
            OFPFile.original_path == path,
            OFPFile.mtime == mtime,
        )
    )

    instance = db.session.scalars(exists_query).one_or_none()
    return instance

def add_jobs_for_path(path, flight_plan_parser, flight_plan_schema):
    """
    High-level convenience function to run jobs against a new path.
    """
    # incoming paths are named simply and can often be duplicated later.
    logger = logging.getLogger('central_load_plan')
    ofp_file = instance_from_path(path)
    if ofp_file:
        logger.info(
            'skip adding jobs, OFPFile already exists for path=%s, mtime=%s',
            ofp_file.original_path, ofp_file.mtime)
        return

    jobs = build_jobs(
        path = path,
        flight_plan_parser = flight_plan_parser,
        flight_plan_schema = flight_plan_schema,
    )
    if jobs:
        for job in jobs:
            logger.info('created %s job for %s', job, path)
        db.session.add_all(jobs)
        db.session.commit()

def watch(args, cp):
    """
    Watch for new files in configured glob path and create new Job objects for
    `work` to process.
    """
    logger = logging.getLogger('central_load_plan.service.watch')

    watch_cp = cp['watch']
    sleep_seconds = watch_cp.getfloat('sleep_seconds', fallback=1.0)

    logger.info('sleep_seconds=%s', sleep_seconds)

    glob_pattern = watch_cp['glob_pattern']
    recursive = watch_cp.getboolean('recursive', fallback=False)

    flight_plan_parser = FlightPlanParser()
    flight_plan_schema = OperationalFlightPlanSchema()

    logger.info('starting watch')
    while True:
        for path in glob.iglob(glob_pattern, recursive=recursive):
            path = os.path.normpath(path)
            logger.info('%s', path)
            add_jobs_for_path(path, flight_plan_parser, flight_plan_schema)
        logger.info('sleeping %s seconds', sleep_seconds)
        time.sleep(sleep_seconds)

def make_argument_parser():
    parser = argparse.ArgumentParser(
        description =
            'Service runner entry point for `watch` and `work` which watches'
            ' for new files and creates jobs for `work` to do.'
    )
    # Require one or more arguments for INI config file paths.
    parser.add_argument('config', nargs='+')

    # Add subparsers for `watch` and `work`.
    subparsers = parser.add_subparsers()

    parser_watch = subparsers.add_parser(
        'watch',
        description = watch.__doc__,
        help = 'Watch files and create work jobs forever',
    )
    parser_watch.set_defaults(func=watch)

    parser_work = subparsers.add_parser(
        'work',
        description = work.__doc__,
        help = 'Execute pending work on OFP files.',
    )
    parser_work.set_defaults(func=work)

    return parser

def update_environment_from_config_for_app(cp):
    # Update environment so that flask app can find it's configuration.
    app_config_path = cp['central_load_plan']['app_config_path']
    os.environ['CENTRAL_LOAD_PLAN_CONFIG'] = os.path.normpath(app_config_path)

def main(argv=None):
    """
    Main CLI entry for running forever-tasks.
    """
    parser = make_argument_parser()
    args = parser.parse_args(argv)

    # Raise for missing paths
    for config_path in args.config:
        if not os.path.exists(config_path):
            raise FileNotFoundError(config_path)

    cp = configparser.ConfigParser()
    cp.read(args.config)

    logging_missing = logging_required - set(cp.sections())
    if logging_missing:
        warnings.warn(f'Missing logging config sections: {logging_missing}')
    else:
        # config includes all logging sections, configure logging from it.
        logging.config.fileConfig(cp)

    # Configure environment for flask app creation.
    update_environment_from_config_for_app(cp)

    logger = logging.getLogger('central_load_plan')

    # Call service function with flask application context for database.
    app = create_app()
    try:
        with app.app_context():
            args.func(args, cp)
    except:
        logger.exception('An exception occurred running service %s', args.func)
        raise

if __name__ == '__main__':
    main()
