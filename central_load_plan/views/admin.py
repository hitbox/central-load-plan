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

from sqlalchemy.exc import NoResultFound

from central_load_plan.extension import db
from central_load_plan.extension import login_manager
from central_load_plan.form import EmailForm
from central_load_plan.form import JobTemplateForm
from central_load_plan.form import JobTypeForm
from central_load_plan.form import OFPConditionForm
from central_load_plan.form import OFPFileFilterForm
from central_load_plan.form import UserForm
from central_load_plan.html import Table
from central_load_plan.html import TableColumn
from central_load_plan.html import yesno
from central_load_plan.models import Email
from central_load_plan.models import Job
from central_load_plan.models import JobTemplate
from central_load_plan.models import JobType
from central_load_plan.models import OFPCondition
from central_load_plan.models import OFPConditionValue
from central_load_plan.models import OFPFile
from central_load_plan.models import User

from .model_rule import add_url_rule_for_table_listing
from .model_rule import add_url_rule_for_creating
from .model_rule import add_url_rule_for_editing

admin_bp = Blueprint('admin', __name__)

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

add_url_rule_for_table_listing(
    user_admin_blueprint,
    rule = '/users',
    pagination_factory = lambda: db.paginate(db.select(User)),
    template = 'table.html',
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
    template = 'form.html',
)

add_url_rule_for_creating(
    user_admin_blueprint,
    rule = '/users/new',
    model = User,
    form_class = UserForm,
    template = 'form.html',
)

# Email objects admin

email_admin_blueprint = Blueprint('emails', __name__)

# emails.list
add_url_rule_for_table_listing(
    email_admin_blueprint,
    rule = '/emails',
    pagination_factory = lambda: db.paginate(db.select(Email)),
    template = 'table.html',
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
    template = 'form.html',
)

# emails.edit
add_url_rule_for_editing(
    email_admin_blueprint,
    rule = '/emails/<uuid:id>',
    model = Email,
    form_class = EmailForm,
    template = 'form.html',
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

add_url_rule_for_table_listing(
    ofp_condition_admin_blueprint,
    rule = '/ofp-condition',
    pagination_factory = lambda: db.paginate(db.select(OFPCondition)),
    template = 'table.html',
    table = Table(
        model = Email,
        columns = [
            TableColumn('Name', 'name'),
            TableColumn('Blurb', 'blurb'),
            TableColumn('Expression', 'condition_as_string'),
        ],
    ),
)

add_url_rule_for_creating(
    ofp_condition_admin_blueprint,
    rule = '/ofp-condition/new',
    form_class = OFPConditionForm,
    model = OFPCondition,
    template = 'form.html',
)

# JobTemplate database objects administration
job_template_admin_blueprint = Blueprint('job_template', __name__)

add_url_rule_for_table_listing(
    job_template_admin_blueprint,
    rule = '/job-template',
    pagination_factory = lambda: db.paginate(db.select(JobTemplate)),
    template = 'table.html',
    edit_endpoint = '.edit',
    table = Table(
        model = JobTemplate,
        columns = [
            TableColumn('Name', 'name'),
            TableColumn('Job Type', 'job_type_name'),
            TableColumn('OFP Condition', 'ofp_condition.blurb'),
        ],
    ),
)

add_url_rule_for_creating(
    job_template_admin_blueprint,
    rule = '/job-template/new',
    model = JobTemplate,
    form_class = JobTemplateForm,
    template = 'form.html',
)

add_url_rule_for_editing(
    job_template_admin_blueprint,
    rule = '/job-template/<uuid:id>',
    form_class = JobTemplateForm,
    model = JobTemplate,
    template = 'form.html',
)

job_admin_blueprint = Blueprint('job', __name__)

add_url_rule_for_table_listing(
    job_admin_blueprint,
    rule = '/job',
    pagination_factory = lambda: db.paginate(db.select(Job)),
    template = 'table.html',
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
    template = 'form.html',
)

add_url_rule_for_editing(
    job_admin_blueprint,
    rule = '/job/<uuid:id>',
    form_class = JobTemplateForm,
    model = Job,
    template = 'form.html',
)

ofp_file_admin_blueprint = Blueprint('ofp_file', __name__)

def ofp_files_pagination():
    query = (
        db.select(OFPFile)
        .order_by(
            OFPFile.flight_origin_date.desc(),
            OFPFile.archive_path,
        )
    )

    form = OFPFileFilterForm(request.args)

    for field in form:
        if hasattr(OFPFile, field.name):
            if field.data:
                query = query.where(
                    getattr(OFPFile, field.name) == field.data,
                )

    return db.paginate(query)

add_url_rule_for_table_listing(
    ofp_file_admin_blueprint,
    '/ofp-file',
    pagination_factory = ofp_files_pagination,
    template = 'table_with_filter.html',
    filter_form = OFPFileFilterForm,
    edit_endpoint = 'job_template.from_ofp_file',
    create_endpoint = None,
    table = Table(
        model = OFPFile,
        columns = [
            TableColumn('Path', 'display_path'),
        ],
    ),
)

add_url_rule_for_editing(
    ofp_file_admin_blueprint,
    rule = '/ofp-file/<uuid:id>',
    form_class = JobTemplateForm,
    model = Job,
    template = 'form.html',
)

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

add_url_rule_for_editing(
    ofp_condition_admin_blueprint,
    rule = '/ofp-condition/<uuid:id>',
    form_class = OFPConditionForm,
    model = OFPCondition,
    # Special template and context for displaying the results of the
    # OFPCondition query.
    template = 'form_ofp_condition.html',
    extra_kwargs = {
        'extra_context': preview_ofp_condition_context,
    }
)

job_type_blueprint = Blueprint('job_type', __name__)

add_url_rule_for_table_listing(
    job_type_blueprint,
    rule = '/job-types',
    template = 'table.html',
    pagination_factory = lambda: db.paginate(db.select(JobType)),
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
    template = 'form.html',
)

add_url_rule_for_creating(
    job_type_blueprint,
    rule = '/job-types/new',
    model = JobType,
    form_class = JobTypeForm,
    template = 'form.html',
)

# Register sub-blueprints

admin_bp.register_blueprint(email_admin_blueprint)
admin_bp.register_blueprint(job_template_admin_blueprint)
admin_bp.register_blueprint(job_type_blueprint)
admin_bp.register_blueprint(ofp_condition_admin_blueprint)
admin_bp.register_blueprint(ofp_file_admin_blueprint)
admin_bp.register_blueprint(user_admin_blueprint)

@admin_bp.route('/')
def root():
    """
    List of links to database objects' admin pages.
    """
    links = [
        ('Users', url_for('.users.list')),
        ('Emails', url_for('.emails.list')),
        ('OFPCondition', url_for('.ofp_condition.list')),
        ('JobType', url_for('.job_type.list')),
        ('JobTemplate', url_for('.job_template.list')),
        ('OFPFile', url_for('.ofp_file.list')),
    ]

    html = ['<ul>']
    for text, link in links:
        html.append(f'<li><a href="{link}">{text}</a></li>')
    html.append('</ul>')

    return render_template('basic.html', markup=Markup(''.join(html)))

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

FORM_MODEL_MAP = {v: k for k, v in MODEL_FORM_MAP.items()}

@click.group()
def seed():
    pass

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
