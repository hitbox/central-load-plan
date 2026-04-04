import sqlalchemy as sa

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.views import View

from central_load_plan.extension import db

class ListView(View):
    """
    Queryable database object view.
    """

    def __init__(
        self,
        template,
        table,
        query_form_manager,
        edit_endpoint = None,
        create_endpoint = None,
    ):
        self.template = template
        self.table = table
        self.query_form_manager = query_form_manager
        self.edit_endpoint = edit_endpoint
        self.create_endpoint = create_endpoint

    def dispatch_request(self, **kwargs):
        pagination, query = self.query_form_manager.get_pagination()
        context = {
            'table': self.table,
            'pagination': pagination,
            'query': query,
        }

        context['filter_form'] = self.query_form_manager.get_filter_form()
        context['sort_form'] = self.query_form_manager.get_sort_form()

        # Add remaining to context if is not None
        for name in ['edit_endpoint', 'create_endpoint']:
            attr = getattr(self, name, None)
            if attr is not None:
                context[name] = attr

        return render_template(self.template, **context)
