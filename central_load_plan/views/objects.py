from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from markupsafe import Markup

from central_load_plan.models import JobType
from central_load_plan.models import OFPCondition
from central_load_plan.models import OFPFile
from central_load_plan.extension import db
from central_load_plan.views.pluggable import InstanceView

objects_bp = Blueprint('objects', __name__)

@objects_bp.route('/')
def index():
    html = ['<ul>']

    links = [
        ''
    ]

    html.append('</ul>')
    return Markup(''.join(html))

ofp_condition_bp = Blueprint('ofp_condition', __name__)

ofp_condition_bp.add_url_rule(
    'ofp-condition/<uuid:id>',
    view_func = InstanceView.as_view(
        'one',
        model = OFPCondition,
        template = 'instance.html',
    ),
)

ofp_file_bp = Blueprint('ofp_file', __name__)

ofp_file_bp.add_url_rule(
    'ofp-file/<uuid:id>',
    view_func = InstanceView.as_view(
        'one',
        model = OFPFile,
        template = 'instance.html',
    ),
)

job_type_bp = Blueprint('job_type', __name__)

job_type_bp.add_url_rule(
    'job-type/<uuid:id>',
    view_func = InstanceView.as_view(
        'one',
        model = JobType,
        template = 'instance.html',
    ),
)

objects_bp.register_blueprint(ofp_condition_bp, url_prefix='/ofp-condition')
objects_bp.register_blueprint(ofp_file_bp, url_prefix='/ofp-file')
objects_bp.register_blueprint(job_type_bp, url_prefix='/job-type')
