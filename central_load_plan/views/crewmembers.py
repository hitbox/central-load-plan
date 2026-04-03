import csv
import datetime
import glob
import os
import re

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
from sqlalchemy.orm import Session

from central_load_plan.constants import AIRLINE_CODES
from central_load_plan.engine import get_lsyrept_engine
from central_load_plan.extension import db
from central_load_plan.extension import login_manager
from central_load_plan.flight_plan_parser import FlightPlanParser
from central_load_plan.form import CrewmemberArgsForm
from central_load_plan.form import EFFArchiveFilterForm
from central_load_plan.models import ChainItemDaily
from central_load_plan.models import Duty
from central_load_plan.models import ItemDaily
from central_load_plan.models import LSYBase
from central_load_plan.models import NonCrewMember
from central_load_plan.models import OFPFile
from central_load_plan.models import RemarkOfEvent
from central_load_plan.models.lsyrept import crew_members_from_ofp
from central_load_plan.schema import EFFArchivePathSchema
from central_load_plan.schema import OperationalFlightPlanSchema
from central_load_plan.schema import lsyrept_model_schemas

crewmember_bp = Blueprint('crewmember', __name__)

class CriteriaDict:

    def __init__(self, dict_):
        self.dict_ = dict_

    def __call__(self, data):
        return all(data[key] == value for key, value in self.dict_.items() if key in data)


@crewmember_bp.before_request
def require_login():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()


@crewmember_bp.route('/')
def index():
    return redirect(url_for('.query'))


@crewmember_bp.route('/from-ofp-file/<uuid:id>')
def from_ofp_file(id):
    ofp_file = db.session.get(OFPFile, id)
    if ofp_file is None:
        abort(404)

    ofp_schema = OperationalFlightPlanSchema()
    flight_plan_parser = FlightPlanParser()

    ofp_strings = flight_plan_parser.parse_path(ofp_file.archive_path)

    ofp_file = ofp_schema.load(ofp_strings)

    # Add crewmembers
    engine = get_lsyrept_engine(ofp_file.airline_iata_code)
    with Session(engine) as session:
        crewmembers_result = crew_members_from_ofp(session, ofp_file)
        ofp_strings['crewmembers'] = crewmembers_result['crew_members']
    ofp_data = ofp_schema.load(ofp_strings)
    result = {
        'ofp_data': ofp_schema.dump(ofp_data),
    }
    return jsonify(result)

@crewmember_bp.route('/query', methods=['GET', 'POST'])
def query():
    """
    Query database for crew members, jump seats and dead heads.
    """
    result = None
    form = CrewmemberArgsForm(formdata = request.form or request.args)

    eff_archive_form = EFFArchiveFilterForm(request.args)

    if request.method == 'POST' and form.validate():
        # there doesn't seem to be support for html datetime field, it just
        # comes out as a text input
        # so we combine them here
        flight_data = dict(
            airline_iata_code = form.airline_iata_code.data,
            flight_origin_date = form.flight_origin_date.data,
            flight_number = form.flight_number.data,
            origin_iata = form.origin_iata.data,
            scheduled_departure_time = datetime.datetime.combine(
                form.scheduled_departure_date.data,
                form.scheduled_departure_time.data,
            ),
        )
        return jsonify(flight_data)

    eff_archive = current_app.config.get('EFF_ARCHIVE')
    eff_path_parser = current_app.config.get('EFF_PATH_PARSER')
    eff_archive_path_schema = EFFArchivePathSchema()

    substitutions = {
        'airline_code': eff_archive_form.airline_iata_code.data,
        'date': eff_archive_form.archive_date.data,
    }
    eff_paths = list(eff_archive.iter_files(substitutions))
    #eff_paths = map(os.path.normpath, eff_paths)
    #eff_paths = (eff_data for eff_data in map(eff_path_parser, eff_paths) if eff_data)
    #eff_paths = [eff_archive_path_schema.load(eff_data) for eff_data in eff_paths]

    interesting_data = current_app.config.get('CREWMEMBERS_INTERESTING_DATA', [])
    context = {
        'form': form,
        'interesting_data': interesting_data,
        'result': result,
        'eff_archive_form': eff_archive_form,
        'eff_paths': eff_paths,
        'substitutions': substitutions,
    }
    return render_template('crewmember/query.html', **context)

def get_lsyrept_schema(model):
    for schema_class in lsyrept_schemas:
        if schema_class.Meta.model == model:
            return schema_class

crewmember_bp.cli.help = (
    'Command-line commands for examining queries related to finding crew'
    ' members for given OFPs.'
)

@crewmember_bp.cli.command('dump')
@click.option('--print-only', is_flag=True)
def dump(print_only):
    """
    Dump external database tables for all airlines.
    """
    for airlinecode in AIRLINE_CODES:
        for model in LSYBase.__subclasses__():
            filename = f'{airlinecode}_{model.__name__}.csv'
            schema_class = lsyrept_model_schemas[model]
            schema = schema_class()
            query = sa.select(model)
            fieldnames = [c.name for c in query.selected_columns]
            try:
                engine = get_lsyrept_engine(airlinecode)
            except:
                continue
            with Session(engine) as session:
                rows = session.execute(query).mappings()
                if print_only:
                    print(filename)
                    for row in rows:
                        print(row)
                else:
                    with open(filename, 'w', newline='') as output_file:
                        writer = csv.DictWriter(output_file, fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)

@crewmember_bp.cli.command('load')
@click.argument('dump_path')
@click.option('--filename-parser', default=r'(?P<airline_code>8C|GB)_(?P<model_name>ChainItemDaily|CrewMember|Duty|ItemDaily|NonCrewMember|RemarkOfEvent)\.csv')
def load(dump_path, filename_parser):
    filename_parser = re.compile(filename_parser)
    for csv_fn in os.listdir(dump_path):
        match = filename_parser.match(csv_fn)
        if not match:
            raise ValueError(f'{csv_fn} did not match regex')
        fn_data = match.groupdict()
        airline_code = fn_data['airline_code']
        engine = get_lsyrept_engine(airline_code)
        LSYBase.metadata.create_all(engine)
        print(engine)
        with Session(engine) as session:
            model_name = fn_data['model_name']
            model = eval(model_name)
            print(model)
            schema_class = lsyrept_model_schemas[model]
            schema = schema_class(session=session)
            schema.context = {'session': session}
            csv_path = os.path.join(dump_path, csv_fn)
            print(csv_path)
            with open(csv_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file, fieldnames=schema.fields.keys())
                for row in reader:
                    instance = schema.load(row)
                    session.add(instance)
            session.commit()

@crewmember_bp.cli.command('from_path')
@click.argument('airline_code')
@click.argument('archive_date', type=click.DateTime(formats=['%Y-%m-%d']))
@click.argument('origin')
@click.argument('destination')
@click.argument('filename_time', type=click.DateTime(formats=['%H:%M:%S']))
def from_path(airline_code, archive_date, origin, destination, filename_time):
    # Keep only the datetime parts we need.
    archive_date = archive_date.date()
    filename_time = filename_time.time()

    criteria = {
        'airline_code': airline_code,
        'archive_date': archive_date,
        'origin': origin,
        'destination': destination,
        'time': filename_time,
    }
    print(f'{criteria=}')
    matcher = CriteriaDict(criteria)

    eff_archive_path_schema = EFFArchivePathSchema()
    substitutions = {
        'airline_code': airline_code,
        'date': archive_date,
    }
    eff_path_parser = current_app.config.get('EFF_PATH_PARSER')

    ofp_schema = OperationalFlightPlanSchema()
    for path in eff_archive_paths.paths(substitutions=substitutions):
        eff_data = eff_path_parser(path)
        eff_data = eff_archive_path_schema.load(eff_data)
        # all the criteria keys from arguments that match path data
        if matcher(eff_data):
            print(f'MATCH: {path=}')
            ofp_data = ofp_schema.load(ofp_strings)

            engine = get_lsyrept_engine(airline_code)
            with Session(engine) as session:
                print(list(crew_members_from_ofp(session, ofp_data)))
