import csv
import json

import sqlalchemy as sa
import click

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
from central_load_plan.models import OFPFile
from central_load_plan.models import RemarkOfEvent
from central_load_plan.utils import literal_sql

lsyrept_bp = Blueprint('lsyrept', __name__)

@lsyrept_bp.cli.command('crewmembers')
@click.argument('ofp_file_uuid')
@click.option('--echo/--no-echo')
def query_crewmembers(ofp_file_uuid, echo):
    ofp_file = db.session.get(OFPFile, ofp_file_uuid)

    if ofp_file is None:
        click.echo('OFPFile not found')
        return

    ofp_file.update_from_path(db.session, ofp_file.archive_path)
    click.echo(f'{ofp_file.archive_path=}')
    click.echo(f'{ofp_file.crewmembers=}')

    if False:
        for key in ofp_file.__dict_keys__:
            attr = getattr(ofp_file, key)
            click.echo(f'{key}={attr}')

    lsy_engine = get_lsyrept_engine(ofp_file.airline_iata_code)
    if echo:
        lsy_engine.echo = True
    click.echo(lsy_engine)

    crew_query = LSYCrewMember.crew_query_from_ofp_file(ofp_file)

    click.echo(literal_sql(crew_query, lsy_engine.dialect))

    crewmembers = []
    with Session(lsy_engine) as lsy_session:
        more_crew = lsy_session.execute(crew_query).all()
        click.echo(more_crew)
        if not more_crew:
            raise NoResultFound(f'No results for query.')
        crewmembers.extend(more_crew)
        click.echo(f'{len(more_crew)}')

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
            print(cls.__name__)
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
