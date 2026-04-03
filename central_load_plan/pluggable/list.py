import sqlalchemy as sa

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.views import View

from central_load_plan.www.extension import db

class ListView(View):
    """
    Queryable database object view.
    """

    def __init__(
        self,
        pagination_factory,
        template,
        table,
        filter_form = None,
        edit_endpoint = None,
        create_endpoint = None,
    ):
        self.pagination_factory = pagination_factory
        self.template = template
        self.table = table
        self.filter_form = filter_form
        self.edit_endpoint = edit_endpoint
        self.create_endpoint = create_endpoint

    def dispatch_request(self, **kwargs):
        pagination = self.pagination_factory()
        context = {
            'table': self.table,
            'pagination': pagination,
        }

        if self.filter_form:
            filter_form = self.filter_form(request.args)
            context['filter_form'] = filter_form

        # Add remaining to context if is not None
        for name in ['edit_endpoint', 'create_endpoint']:
            attr = getattr(self, name, None)
            if attr is not None:
                context[name] = attr

        return render_template(self.template, **context)
