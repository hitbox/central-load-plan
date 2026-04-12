import csv
import json
import logging
import os

import click
import psycopg
import sqlalchemy as sa

from flask import Blueprint
from flask import current_app
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from central_load_plan.engine import get_lsyrept_engine
from central_load_plan.extension import db
from central_load_plan.models import ChainItemDaily
from central_load_plan.models import Duty
from central_load_plan.models import ItemDaily
from central_load_plan.models import LSYBase
from central_load_plan.models import LSYCrewMember
from central_load_plan.models import NonCrewMember
from central_load_plan.models import OFPFile
from central_load_plan.models import RemarkOfEvent
from central_load_plan.models import lsyrept as lsyrept_models
from central_load_plan.utils import literal_sql

lsyrept_bp = Blueprint('lsyrept', __name__)

logging.basicConfig(level=logging.DEBUG)


@lsyrept_bp.cli.command('setup-fake-lsyrept')
@click.option('--dbname', default='fake_lsyrept')
def setup_fake_lsyrept(dbname):
    """
    Setup a fake LSYREPT database in postgresql.
    """
    logging.getLogger('psycopg').setLevel(logging.DEBUG)

    postgres_conninfo = (
        f'dbname=postgres user=postgres password={os.getenv("PGPASSWORD")}'
    )
    click.echo(postgres_conninfo)
    with psycopg.connect(postgres_conninfo, autocommit=True) as postgres_cursor:
        postgres_cursor.execute(f'DROP DATABASE IF EXISTS {dbname}')
        postgres_cursor.execute(f'CREATE DATABASE {dbname}')

    lsyrept_conninfo = (
        f'dbname={dbname} user=postgres password={os.getenv("PGPASSWORD")}'
    )
    with psycopg.connect(lsyrept_conninfo, autocommit=True) as cursor:
        for airline, credentials in current_app.config['CREDENTIALS_FOR_AIRLINE'].items():
            username = credentials['username']
            password = credentials['password']
            engine = get_lsyrept_engine(airline)
            cur = cursor.execute(
                'SELECT FROM pg_roles WHERE rolname = %s',
                (username, ),
            )
            exists = cur.fetchone() is not None
            if not exists:
                cursor.execute(
                    "CREATE ROLE %s LOGIN PASSWORD %s;",
                    (username, password, )
                )

            cursor.execute(
                f'CREATE SCHEMA IF NOT EXISTS "{username}" AUTHORIZATION "{username}";',
            )

            cursor.execute(
                f'GRANT USAGE, CREATE ON SCHEMA {username} TO {username};',
            )

            cursor.execute(
                f'ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA {username}'
                f' GRANT ALL ON TABLES TO {username};'
            )

            cursor.execute(
                f'ALTER ROLE {username} SET search_path TO {username};',
            )

@lsyrept_bp.cli.command('dump')
def dump():
    """
    Dump the LSY databases for development.
    """

    manifest = {
    }

    for airline in current_app.config['CREDENTIALS_FOR_AIRLINE'].keys():
        tables = {}
        manifest[airline] = {
            'tables': tables,
        }
        engine = get_lsyrept_engine(airline)

        with Session(engine) as session:
            for table in LSYBase.metadata.tables.values():
                query = sa.select(table)
                data_rows = session.scalars(query).all()
                output_fn = f'{airline}_{table.name}.csv'
                tables[table.name] = output_fn
                with open(output_fn, 'w', encoding='utf8') as outfile:
                    csv_writer = csv.DictWriter(outfile, fieldnames=[c.name for c in table.c])
                    csv_writer.writeheader()
                    csv_writer.writerows(data_rows)

    with open('manifest.json', 'w', encoding='utf8') as jsonfile:
        json.dump(manifest, jsonfile)

@lsyrept_bp.cli.command('create-all')
def create_all():
    """
    Create all objects for each airline schema in fake LSYREPT database.
    """
    root_engine = get_lsyrept_engine('root')
    for airline, credentials in current_app.config['CREDENTIALS_FOR_AIRLINE'].items():
        username = credentials['username']
        password = credentials['password']
        lsy_engine = get_lsyrept_engine(airline)
        # Update schema for all tables.
        for table in LSYBase.metadata.tables.values():
            table.schema = username
        click.echo(f'LSYBase.metadata.create_all({lsy_engine=})')
        LSYBase.metadata.create_all(lsy_engine)

@lsyrept_bp.cli.command('dump')
def dump():
    """
    Dump the LSY databases for development.
    """

    manifest = {}

    for airline in current_app.config['CREDENTIALS_FOR_AIRLINE'].keys():
        tables = {}
        manifest[airline] = {
            'tables': tables,
        }

        for mapper in LSYBase.registry.mappers:
            cls = mapper.class_
            table = mapper.local_table
            query = sa.select(table)
            engine = get_lsyrept_engine(airline)
            with Session(engine) as session:
                result = session.execute(query.execution_options(stream_results=True))
                data_rows = result.mappings().all()

                output_fn = f'{airline}_{table.name}.csv'
                tables[cls.__name__] = output_fn

                with open(output_fn, 'w', encoding='utf8', newline='') as outfile:
                    fieldnames = [c.name for c in table.columns]
                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)

                    writer.writeheader()
                    writer.writerows(data_rows)

    # write manifest once
    with open('manifest.json', 'w', encoding='utf8') as jsonfile:
        json.dump(manifest, jsonfile, indent=2)

@lsyrept_bp.cli.command('load')
@click.argument('manifest_path')
def load(manifest_path):
    """
    Load LSYREPT data from CSV specified by a JSON manifest file. The CSV files
    should be found next to the manifest in the same directory.
    """
    basedir = os.path.dirname(manifest_path)

    with open(manifest_path, 'r', encoding='utf8') as jsonfile:
        manifest = json.load(jsonfile)

    for airline, airline_data in manifest.items():
        tables = airline_data['tables']

        for class_name, filename in tables.items():
            class_ = getattr(lsyrept_models, class_name)
            csv_path = os.path.join(basedir, filename)

            engine = get_lsyrept_engine(airline)

            mapper = sa.inspect(class_)

            col_map = {
                col.name: mapper.get_property_by_column(col).key
                for col in mapper.columns
            }
            click.echo(f'loading {csv_path=}')

            with Session(engine) as session:
                with open(csv_path, 'r', encoding='utf8') as csv_file:
                    csv_reader = csv.DictReader(csv_file)

                    for row in csv_reader:
                        kwargs = {
                            col_map[k]: v.replace('\0', '')
                            for k, v in row.items()
                            if k in col_map
                        }

                        session.add(class_(**kwargs))

                session.commit()
