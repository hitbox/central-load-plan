import click

from flask import Blueprint
from flask import render_template
from flask import url_for
from flask_login import current_user
from markupsafe import Markup

from central_load_plan.extension import db
from central_load_plan.extension import login_manager
from central_load_plan.form import EditEmailFromTemplateJobTemplateForm
from central_load_plan.form import EditOFPConditionForm
from central_load_plan.form import EmailForm
from central_load_plan.form import EmailFromTemplateJobTemplateForm
from central_load_plan.form import FileFromTemplateJobTemplateForm
from central_load_plan.form import JSONOutputJobTemplateForm
from central_load_plan.form import JobTemplateForm
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
        model = OFPFile,
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

add_url_rule_for_table_listing(
    user_admin_blueprint,
    rule = '/users',
    query_form_manager = QueryFormManager(model=User),
    #pagination_factory = lambda: db.paginate(db.select(User)),
    template = 'admin/table.html',
    table = Table(
        model = User,
        columns = [
            TableColumn('Username', 'username'),
            TableColumn('Active?', 'is_active', cast=yesno),
            TableColumn('Admin?', 'is_admin', cast=yesno),
        ],
    ),
)

add_url_rule_for_editing(
    user_admin_blueprint,
    rule = '/users/<uuid:id>',
    model = User,
    form_class = UserForm,
    template = 'admin/form.html',
)

add_url_rule_for_creating(
    user_admin_blueprint,
    rule = '/users/new',
    model = User,
    form_class = UserForm,
    template = 'admin/form.html',
)

# Email objects admin

email_admin_blueprint = Blueprint('emails', __name__)
admin_bp.register_blueprint(email_admin_blueprint)

# emails.list
add_url_rule_for_table_listing(
    email_admin_blueprint,
    rule = '/emails',
    query_form_manager = QueryFormManager(
        model = Email,
    ),
    edit_endpoint = '.edit',
    template = 'admin/table.html',
    table = Table(
        model = Email,
        columns = [
            TableColumn('Address', 'address'),
            TableColumn('Display', 'display_name'),
        ],
    ),
)

# emails.create
add_url_rule_for_creating(
    email_admin_blueprint,
    rule = '/emails/new',
    model = Email,
    form_class = EmailForm,
    template = 'admin/form.html',
)

# emails.edit
add_url_rule_for_editing(
    email_admin_blueprint,
    rule = '/emails/<uuid:id>',
    model = Email,
    form_class = EmailForm,
    template = 'admin/form.html',
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
        #pagination_factory = lambda: db.paginate(db.select(OFPCondition)),
        query_form_manager = QueryFormManager(
            model = OFPCondition,
        ),
        template = 'admin/table.html',
        table = Table(
            model = Email,
            columns = [
                TableColumn('Name', 'name'),
                TableColumn('Blurb', 'blurb'),
                TableColumn('Expression', 'condition_as_html'),
            ],
        ),
    ),
)

ofp_condition_admin_blueprint.add_url_rule(
    rule = '/ofp-condition/<uuid:id>',
    view_func = EditObjectView.as_view(
        name = 'edit',
        model = OFPCondition,
        # Special template and context for displaying the results of the
        # OFPCondition query.
        template = 'admin/form_ofp_condition.html',
        form_class = EditOFPConditionForm,
        extra_context = preview_ofp_condition_context,
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

def job_template_form_for_instance(job_template):
    # Select proper form for job_type name.
    if job_template.job_type_name in job_template_forms:
        return job_template_forms[job_template.job_type_name]

add_url_rule_for_table_listing(
    job_template_admin_blueprint,
    rule = '/job-template',
    query_form_manager = QueryFormManager(model=JobTemplate),
    template = 'admin/table.html',
    edit_endpoint = '.edit',
    table = Table(
        model = JobTemplate,
        columns = [
            TableColumn('Name', 'name'),
            TableColumn('Job Type', 'job_type_name'),
            TableColumn('OFP Condition', 'ofp_condition.blurb'),
            TableColumn('Position', 'execution_position'),
        ],
    ),
)

add_url_rule_for_creating(
    job_template_admin_blueprint,
    rule = '/job-template/new',
    model = JobTemplate,
    form_class = EmailFromTemplateJobTemplateForm,
    template = 'admin/form.html',
)

add_url_rule_for_editing(
    job_template_admin_blueprint,
    rule = '/job-template/<uuid:id>',
    form_class_factory = job_template_form_for_instance,
    model = JobTemplate,
    template = 'admin/form.html',
)

job_admin_blueprint = Blueprint('job', __name__)

add_url_rule_for_table_listing(
    job_admin_blueprint,
    rule = '/job',
    #pagination_factory = lambda: db.paginate(db.select(Job)),
    query_form_manager = QueryFormManager(model=Job),
    template = 'admin/table.html',
    table = Table(
        model = Job,
        columns = [
            TableColumn('Name', 'name'),
            TableColumn('Type', 'job_type.name'),
            TableColumn('OFP Condition', 'ofp_condition.blurb'),
        ],
    ),
)

add_url_rule_for_creating(
    job_admin_blueprint,
    rule = '/job/new',
    model = Job,
    form_class = JobTemplateForm,
    template = 'admin/form.html',
)

add_url_rule_for_editing(
    job_admin_blueprint,
    rule = '/job/<uuid:id>',
    form_class = JobTemplateForm,
    model = Job,
    template = 'admin/form.html',
)

ofp_file_admin_blueprint = Blueprint('ofp_file', __name__)
admin_bp.register_blueprint(ofp_file_admin_blueprint)

ofp_files_query_form_manager = QueryFormManager(
    model = OFPFile,
    filter_form_class = OFPFileFilterForm,
    sort_form_class = OFPFileSortForm,
)

def mdy_format(flight_origin_date):
    return flight_origin_date.strftime('%d%b%y')

add_url_rule_for_table_listing(
    ofp_file_admin_blueprint,
    '/ofp-file',
    template = 'admin/table_with_filter.html',
    query_form_manager = ofp_files_query_form_manager,
    edit_endpoint = 'job_template.list_matching_job_templates',
    table = Table(
        model = OFPFile,
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

add_url_rule_for_editing(
    ofp_file_admin_blueprint,
    rule = '/ofp-file/<uuid:id>',
    form_class = JobTemplateForm,
    model = Job,
    template = 'admin/form.html',
)

job_type_blueprint = Blueprint('job_type', __name__)
admin_bp.register_blueprint(job_type_blueprint)

add_url_rule_for_table_listing(
    job_type_blueprint,
    rule = '/job-types',
    template = 'admin/table.html',
    #pagination_factory = lambda: db.paginate(db.select(JobType)),
    query_form_manager = QueryFormManager(model=JobType),
    table = Table(
        model = JobType,
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
            model = EmailFromTemplateJobTemplate,
            columns = [
                TableColumn('Name', 'name'),
                TableColumn('OFP Condition', 'ofp_condition'),
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

@admin_bp.context_processor
def add_links_to_context():
    links = [
        ('admin.users.list', 'Users',),
        ('admin.emails.list', 'Emails',),
        (
            'admin.email_from_template_job_template.list',
            Markup('Email From Template Job Template'),
        ),
        ('admin.ofp_condition.list', 'OFPCondition',),
        ('admin.job_type.list', 'JobType',),
        ('admin.job_template.list', 'JobTemplate',),
        ('admin.ofp_file.list', 'OFPFile',),
    ]
    return {
        'links': links,
    }

@admin_bp.route('/')
def root():
    """
    List of links to database objects' admin pages.
    """
    return render_template('admin/base.html')

# Map models to forms
MODEL_FORM_MAP = {
    User: UserForm,
    Email: EmailForm,
    OFPCondition: OFPConditionForm,
}

MODELNAME_CLASS_MAP = {
    'User': User,
    'Email': Email,
    'OFPCondition': OFPCondition,
}

def prompt_for_form(form_class, formdata=None):
    """
    Prompt user for each field in a WTForms form, returning a populated form.
    """
    if formdata is None:
        formdata = {}
    form = form_class()
    for name, field in form._fields.items():
        # skip submit/delete buttons
        if field.type in ('SubmitField',):
            continue

        # Skip already given keys
        if name in formdata:
            continue

        # prompt textually
        prompt_text = f"{name} ({field.label.text})"
        default = getattr(field, 'default', None)

        if field.type.endswith('List'):
            value = []
            while True:
                item = click.prompt(prompt_text, default='', show_default=False)
                if not item:
                    break
                value.append(item)
        else:
            value = click.prompt(prompt_text, default=default, show_default=True)
        formdata[name] = value

    # create form instance with the collected data
    return form_class(data=formdata)


@admin_bp.cli.command('create')
@click.argument(
    'model_name',
    type = click.Choice(key.__name__ for key in MODEL_FORM_MAP),
)
@click.option(
    '--field',
    '-f',
    multiple = True,
    nargs = 2,
    type = str,
)
def create_object(model_name, field):
    """
    Create an object of MODEL_NAME using its form.
    Example: flask seed create User
    """
    # find model + form
    model = MODELNAME_CLASS_MAP[model_name]
    form_class = MODEL_FORM_MAP[model]

    data = dict(field)

    # prompt user for values
    form = prompt_for_form(form_class, data)

    # validate
    if not form.validate():
        click.echo("Validation failed!")
        for field, errors in form.errors.items():
            for e in errors:
                click.echo(f"  {field}: {e}")
        return

    # create instance
    instance = model()
    form.populate_obj(instance)

    # add and commit
    db.session.add(instance)
    db.session.commit()
    click.echo(f"{model_name} created with id={instance.id}")
