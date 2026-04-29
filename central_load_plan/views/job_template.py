import click
import sqlalchemy as sa

from operator import attrgetter

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
from central_load_plan.models import JobTemplate
from central_load_plan.models import OFPFile

job_template_bp = Blueprint('job_template', __name__)

@job_template_bp.before_request
def require_login():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()


@job_template_bp.route('/')
def index():
    return redirect(url_for('.query'))


@job_template_bp.route('/job-templates-from-ofp-file/<uuid:id>')
def list_matching_job_templates(id):
    """
    Matching job templates from ofp file.
    """
    ofp_file = db.session.get(OFPFile, id)
    if ofp_file is None:
        abort(404)

    # Matching JobTemplate objects
    job_templates = sorted((jt for jt in db.session.scalars(db.select(JobTemplate)) if jt.is_match(ofp_file)), key=attrgetter('execution_position'))

    items = []
    for job_template in job_templates:
        href = url_for(
            "job_template.preview_job_template_for_file",
            job_template_id = job_template.id,
            ofp_file_id = ofp_file.id,
        )
        items.append(Markup(f'<a href="{href}">{job_template.name}</a>'))

    context = {
        'page_title': Markup(
            f'Matching jobs for file <pre class="value">{ ofp_file.archive_path }</pre>'
        ),
        'list_items': items,
    }
    return render_template('ordered_list.html', **context)

@job_template_bp.route('/preview/<uuid:job_template_id>/<uuid:ofp_file_id>')
def preview_job_template_for_file(job_template_id, ofp_file_id):
    """
    Preview work to be done by job template object.
    """
    job_template = db.session.get(JobTemplate, job_template_id)

    if job_template is None:
        abort(404)

    ofp_file = db.session.get(OFPFile, ofp_file_id)
    if ofp_file is None:
        abort(404)

    # DISABLED
    # # Scrape file and deserialize again, once more before using it on the view.
    # ofp_file.update_from_archive_path(db.session, ofp_file.archive_path)

    context = {
        'markup': job_template.html_preview(ofp_file),
    }
    return render_template('basic.html', **context)
