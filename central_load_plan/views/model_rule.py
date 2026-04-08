"""
Functions to add url rules from database models.
"""
from central_load_plan.views.pluggable import CreateObjectView
from central_load_plan.views.pluggable import EditObjectView
from central_load_plan.views.pluggable import ListView

def add_url_rule_for_table_listing(
    blueprint,
    rule,
    **view_kwargs
):
    blueprint.add_url_rule(
        rule,
        view_func = ListView.as_view(
            'list',
            **view_kwargs
        )
    )

def add_url_rule_for_editing(
    blueprint,
    rule,
    model,
    template,
    form_class = None,
    form_class_factory = None,
    view_name = 'edit',
    extra_kwargs = None,
):
    if extra_kwargs is None:
        extra_kwargs = {}
    blueprint.add_url_rule(
        rule,
        view_func = EditObjectView.as_view(
            view_name,
            model = model,
            template = template,
            form_class = form_class,
            form_class_factory = form_class_factory,
            **extra_kwargs,
        )
    )

def add_url_rule_for_creating(
    blueprint,
    rule,
    model,
    form_class,
    template,
    view_name = 'create',
):
    blueprint.add_url_rule(
        rule,
        view_func = CreateObjectView.as_view(
            view_name,
            model = model,
            template = template,
            form_class = form_class,
        )
    )
