import sqlalchemy as sa

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.views import View

from central_load_plan.extension import db

class InstanceView(View):
    """
    View database object instance from identity.
    """

    def __init__(self, model, template):
        self.model = model
        self.template = template

    def dispatch_request(self, **ident):
        instance = db.session.get(self.model, ident)
        context = {
            'model': self.model,
            'instance': instance,
        }
        return render_template(self.template, **context)
