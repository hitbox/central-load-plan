import click

from flask import Blueprint
from flask import render_template
from flask import url_for
from flask_login import current_user
from markupsafe import Markup

from central_load_plan.extension import db
from central_load_plan.extension import login_manager
from central_load_plan.form import EditEmailFromTemplateJobTemplateForm
from central_load_plan.form import EditSendToForm
from central_load_plan.form import EmailForm
from central_load_plan.form import EmailFromTemplateJobTemplateForm
from central_load_plan.form import FileFromTemplateJobTemplateForm
from central_load_plan.form import JSONOutputJobTemplateForm
from central_load_plan.form import JobForm
from central_load_plan.form import JobTypeForm
from central_load_plan.form import MoveFileJobTemplateForm
from central_load_plan.form import OFPConditionForm
from central_load_plan.form import OFPFileFilterForm
from central_load_plan.form import OFPFileSortForm
from central_load_plan.form import UserForm
from central_load_plan.html import Table
from central_load_plan.html import TableColumn
from central_load_plan.html import unordered_list
from central_load_plan.html import yesno
from central_load_plan.models import Email
from central_load_plan.models import EmailFromTemplateJobTemplate
from central_load_plan.models import Job
from central_load_plan.models import JobTemplate
from central_load_plan.models import JobType
from central_load_plan.models import JobTypeEnum
from central_load_plan.models import OFPCondition
from central_load_plan.models import OFPFile
from central_load_plan.models import SendToTemplate
from central_load_plan.models import User
from central_load_plan.query_form_manager import QueryFormManager

from .model_rule import add_url_rule_for_creating
from .model_rule import add_url_rule_for_editing
from .model_rule import add_url_rule_for_table_listing
from .pluggable import CreateObjectView
from .pluggable import EditObjectView
from .pluggable import ListView

admin_bp = Blueprint('admin', __name__)

def preview_ofp_condition_context(current_context):
    ofp_condition = current_context['instance']

    query = (
        db.select(OFPFile)
        .where(ofp_condition.to_expression())
        .order_by(OFPFile.archive_path)
    )
    preview_results = db.paginate(query)

    table = Table(
        columns = [
            TableColumn('Path', 'display_path'),
        ],
        row_endpoint = 'objects.ofp_file.one',
    )

    more_context = {
        'query': query,
        'ofp_condition_matches': [],
        'expression': ofp_condition.to_expression(),
        'preview_results': preview_results,
        'table': table,
    }
    return more_context

@admin_bp.before_request
def require_login_and_admin():
    """
    Must be logged in as admin to access.
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return login_manager.unauthorized()

## Sub-blueprints for namespacing

# admin.users.list view listing inside a table
user_admin_blueprint = Blueprint('users', __name__)
admin_bp.register_blueprint(user_admin_blueprint)

user_admin_blueprint.add_url_rule(
    rule = '/users',
    view_func = ListView.as_view(
        name = 'list',
        edit_endpoint = '.edit',
        query_form_manager = QueryFormManager(
            model = User,
        ),
        template = 'admin/table.html',
        table = Table(
            columns = [
                TableColumn('Username', 'username'),
                TableColumn('Active?', 'is_active', cast=yesno),
                TableColumn('Admin?', 'is_admin', cast=yesno),
            ],
        ),
    ),
)

user_admin_blueprint.add_url_rule(
    rule = '/users/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        model = User,
        form_class = UserForm,
        template = 'admin/form.html',
    ),
)

user_admin_blueprint.add_url_rule(
    rule = '/users/new',
    view_func = CreateObjectView.as_view(
        name = 'create',
        model = User,
        template = 'admin/form.html',
        form_class = UserForm,
    ),
)

# Email objects admin

email_admin_blueprint = Blueprint('emails', __name__)
admin_bp.register_blueprint(email_admin_blueprint)

# emails.list
email_admin_blueprint.add_url_rule(
    rule = '/emails',
    view_func = ListView.as_view(
        name = 'list',
        edit_endpoint = '.edit',
        query_form_manager = QueryFormManager(
            model = Email,
        ),
        template = 'admin/table.html',
        table = Table(
            columns = [
                TableColumn('Delete?'),
                TableColumn('Address', 'address'),
                TableColumn('Display', 'display_name'),
            ],
        ),
    ),
)

# emails.create
email_admin_blueprint.add_url_rule(
    rule = '/emails/new',
    view_func = CreateObjectView.as_view(
        name = 'create',
        model = Email,
        template = 'admin/form.html',
        form_class = EmailForm,
    ),
)

# emails.edit
email_admin_blueprint.add_url_rule(
    rule = '/emails/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        model = Email,
        form_class = EmailForm,
        template = 'admin/form.html',
    )
)

def symbol_for_operator(ofp_condition):
    return ofp_condition.__symbols__[ofp_condition.operator]

def values_for_html(ofp_condition):
    val_list = [v.value for v in ofp_condition.values]
    if ofp_condition.operator == 'contains':
        return str(val_list)
    elif val_list:
        return str(val_list[0])

# OFPCondition objects admin
ofp_condition_admin_blueprint = Blueprint('ofp_condition', __name__)
admin_bp.register_blueprint(ofp_condition_admin_blueprint)

ofp_condition_admin_blueprint.add_url_rule(
    rule = '/ofp-condition',
    view_func = ListView.as_view(
        name = 'list',
        edit_endpoint = '.edit',
        query_form_manager = QueryFormManager(
            model = OFPCondition,
        ),
        template = 'admin/table.html',
        description =
            'OFPCondition objects are stand-alone objects that can be used for'
            ' JobTemplate and SendToTemplate objects.',
        table = Table(
            columns = [
                TableColumn('Name', 'name'),
                TableColumn('Blurb', 'blurb'),
                TableColumn('Expression', 'condition_as_html'),
            ],
        ),
    ),
)

def url_for_ofp_condition_after_success(action, instance):
    return url_for('.list', _anchor=str(instance.id))

ofp_condition_admin_blueprint.add_url_rule(
    rule = '/ofp-condition/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        model = OFPCondition,
        # Special template and context for displaying the results of the
        # OFPCondition query.
        template = 'admin/form.html',
        form_class = OFPConditionForm,
        extra_context = preview_ofp_condition_context,
        success_url_factory = url_for_ofp_condition_after_success,
    ),
)

# JobTemplate database objects administration
job_template_admin_blueprint = Blueprint('job_template', __name__)
admin_bp.register_blueprint(job_template_admin_blueprint)

job_template_forms = {
    JobTypeEnum.EMAIL_FROM_TEMPLATE.name: EmailFromTemplateJobTemplateForm,
    JobTypeEnum.FILE_FROM_TEMPLATE.name: FileFromTemplateJobTemplateForm,
    JobTypeEnum.JSON_FILE.name: JSONOutputJobTemplateForm,
    JobTypeEnum.MOVE_FILE.name: MoveFileJobTemplateForm,
}

job_template_admin_blueprint.add_url_rule(
    rule = '/job-template',
    view_func = ListView.as_view(
        name = 'list',
        query_form_manager = QueryFormManager(model=JobTemplate),
        template = 'admin/table.html',
        edit_endpoint = '.edit',
        description = JobTemplate.__ui_description__,
        table = Table(
            columns = [
                TableColumn('Name', 'name'),
                TableColumn('Job Type', 'job_type_name'),
                TableColumn('OFP Condition', 'ofp_condition.blurb'),
                TableColumn('Position', 'execution_position'),
            ],
        ),
    ),
)

job_template_admin_blueprint.add_url_rule(
    rule = '/job-template/new',
    view_func = CreateObjectView.as_view(
        name = 'create',
        rule = '/job-template/new',
        model = JobTemplate,
        form_class = EmailFromTemplateJobTemplateForm,
        template = 'admin/form.html',
    )
)

def job_template_form_for_instance(job_template):
    # Select proper form for job_type name.
    if job_template.job_type_name in job_template_forms:
        return job_template_forms[job_template.job_type_name]

job_template_admin_blueprint.add_url_rule(
    rule = '/job-template/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        model = JobTemplate,
        form_class_factory = job_template_form_for_instance,
        template = 'admin/form.html',
    )
)

job_admin_blueprint = Blueprint('job', __name__)
admin_bp.register_blueprint(job_admin_blueprint)

job_admin_blueprint.add_url_rule(
    rule = '/job',
    view_func = ListView.as_view(
        'list',
        query_form_manager = QueryFormManager(
            model = Job,
        ),
        template = 'admin/table.html',
        table = Table(
            columns = [
                TableColumn('Type', 'job_template.job_type'),
                TableColumn('OFP Condition', 'job_template.ofp_condition.blurb'),
            ],
        ),
    ),
)

job_admin_blueprint.add_url_rule(
    rule = '/job/new',
    view_func = CreateObjectView.as_view(
        'create',
        job_admin_blueprint,
        model = Job,
        form_class = JobForm,
        template = 'admin/form.html',
    )
)

job_admin_blueprint.add_url_rule(
    rule = '/job/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        form_class = JobForm,
        model = Job,
        template = 'admin/form.html',
    )
)

ofp_file_admin_blueprint = Blueprint('ofp_file', __name__)
admin_bp.register_blueprint(ofp_file_admin_blueprint)

def mdy_format(flight_origin_date):
    return flight_origin_date.strftime('%d%b%y')

ofp_files_query_form_manager = QueryFormManager(
    model = OFPFile,
    filter_form_class = OFPFileFilterForm,
    sort_form_class = OFPFileSortForm,
)

ofp_file_admin_blueprint.add_url_rule(
    rule = '/ofp-file',
    view_func = ListView.as_view(
        name = 'list',
        template = 'admin/table_with_filter.html',
        query_form_manager = ofp_files_query_form_manager,
        # views/job_template.py:list_matching_job_templates
        edit_endpoint = 'job_template.list_matching_job_templates',
        table = Table(
            columns = [
                # Showing the same fields we can filter by.
                TableColumn('Airline', 'airline_iata_code'),
                TableColumn('Flight', 'flight_number'),
                TableColumn('Date', 'flight_origin_date', cast=mdy_format),
                TableColumn('Orig.', 'origin_iata'),
                TableColumn('Dest.', 'destination_iata'),
                TableColumn('Path', 'display_path'),
            ],
        ),
    )
)

ofp_file_admin_blueprint.add_url_rule(
    rule = '/ofp-file/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        form_class = JobForm, # TODO: need a form?
        model = Job,
        template = 'admin/form.html',
    )
)

job_type_blueprint = Blueprint('job_type', __name__)
admin_bp.register_blueprint(job_type_blueprint)

add_url_rule_for_table_listing(
    job_type_blueprint,
    rule = '/job-types',
    template = 'admin/table.html',
    query_form_manager = QueryFormManager(model=JobType),
    table = Table(
        columns = [
            TableColumn('Name', 'name'),
        ],
    ),
)

add_url_rule_for_editing(
    job_type_blueprint,
    rule = '/job-types/<uuid:id>',
    model = JobType,
    form_class = JobTypeForm,
    template = 'admin/form.html',
)

add_url_rule_for_creating(
    job_type_blueprint,
    rule = '/job-types/new',
    model = JobType,
    form_class = JobTypeForm,
    template = 'admin/form.html',
)

send_to_template_blueprint = Blueprint('send_to_template', __name__)
admin_bp.register_blueprint(send_to_template_blueprint)

send_to_template_blueprint.add_url_rule(
    rule = '/send-to',
    view_func = ListView.as_view(
        name = 'list',
        query_form_manager = QueryFormManager(
            model = SendToTemplate,
        ),
        description = SendToTemplate.__ui_description__,
        edit_endpoint = 'admin.send_to_template.edit',
        create_endpoint = 'admin.send_to_template.create',
        template = 'admin/table.html',
        table = Table(
            columns = [
                TableColumn('OFP Condition', 'ofp_condition_as_html'),
                TableColumn('Email', 'email.address'),
            ],
        ),
    ),
)

send_to_template_blueprint.add_url_rule(
    rule = '/send-to/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        form_class = EditSendToForm,
        model = SendToTemplate,
        template = 'admin/form.html',
    ),
)

send_to_template_blueprint.add_url_rule(
    rule = '/send-to/new',
    view_func = CreateObjectView.as_view(
        name = 'create',
        form_class = EditSendToForm,
        template = 'admin/form.html',
    )
)

email_from_template_job_template_blueprint = Blueprint('email_from_template_job_template', __name__)
admin_bp.register_blueprint(email_from_template_job_template_blueprint)

email_from_template_job_template_blueprint.add_url_rule(
    rule = '/email-from-template-job-template',
    view_func = ListView.as_view(
        name = 'list',
        edit_endpoint = 'admin.email_from_template_job_template.edit',
        query_form_manager = QueryFormManager(
            model = EmailFromTemplateJobTemplate,
        ),
        template = 'admin/table.html',
        table = Table(
            columns = [
                TableColumn('Name', 'name'),
                TableColumn('OFP Condition', 'ofp_condition.condition_as_html'),
                TableColumn('Recipients', 'send_tos_html_list'),
            ],
        ),
    ),
)

email_from_template_job_template_blueprint.add_url_rule(
    rule = '/email-from-template-job-template/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        form_class = EditEmailFromTemplateJobTemplateForm,
        model = EmailFromTemplateJobTemplate,
        template = 'admin/form.html',
    ),
)

links = [
    {
        'endpoint': 'admin.users.list',
        'text': 'Users',
        'current_for': set([
            'admin.users.list',
            'admin.users.edit',
            'admin.users.new',
        ]),
    },
    # Job objects are a poor admin objects. These are basically the work that
    # was done.
    #{
    #    'endpoint': 'admin.job.list',
    #    'text': 'Job',
    #    'current_for': set([
    #        'admin.job.list',
    #        'admin.job.edit',
    #        'admin.job.new',
    #    ]),
    #},
    {
        'endpoint': 'admin.job_template.list',
        'text': 'Job Template',
        'current_for': set([
            'admin.job_template.list',
            'admin.job_template.edit',
            'admin.job_template.new',
        ]),
    },
    {
        'endpoint': 'admin.emails.list',
        'text': 'Emails',
        'current_for': set([
            'admin.emails.list',
            'admin.emails.edit',
            'admin.emails.new',
        ]),
    },
    {
        'endpoint': 'admin.email_from_template_job_template.list',
        'text': Markup('Email From Template Job Template'),
        'current_for': set([
            'admin.email_from_template_job_template.list',
            'admin.email_from_template_job_template.edit',
            'admin.email_from_template_job_template.new',
        ]),
    },
    {
        'endpoint': 'admin.send_to_template.list',
        'text': 'Send To Template',
        'current_for': set([
            'admin.send_to_template.list',
            'admin.send_to_template.edit',
            'admin.send_to_template.new',
        ]),
    },
    {
        'endpoint': 'admin.ofp_condition.list',
        'text': 'OFPCondition',
        'current_for': set([
            'admin.ofp_condition.list',
            'admin.ofp_condition.edit',
            'admin.ofp_condition.new',
        ]),
    },
    {
        'endpoint': 'admin.job_type.list',
        'text': 'JobType',
        'current_for': set([
            'admin.job_type.list',
            'admin.job_type.edit',
            'admin.job_type.new',
        ])
    },
    {
        'endpoint': 'admin.job_template.list',
        'text': 'JobTemplate',
        'current_for': set([
            'admin.job_template.list',
            'admin.job_template.edit',
            'admin.job_template.new',
        ]),
    },
    {
        'endpoint': 'admin.ofp_file.list',
        'text': 'OFPFile',
        'current_for': set([
            'admin.ofp_file.list',
            'admin.ofp_file.edit',
            'admin.ofp_file.new',
        ]),
    },
]

@admin_bp.context_processor
def add_links_to_context():
    # Add links to all admin endpoints
    return {
        'links': links,
    }

@admin_bp.route('/')
def root():
    """
    List of links to database objects' admin pages.
    """
    return render_template('admin/base.html')
