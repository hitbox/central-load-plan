from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.views import View

from central_load_plan.extension import db
from central_load_plan.primary_key import get_pk_dict

class CreateObjectView(View):
    """
    Create a new instance of sqlalchemy model.
    """

    methods = ['GET', 'POST']

    def __init__(self, form_class, model, template):
        self.form_class = form_class
        self.model = model
        self.template = template

    def dispatch_request(self):
        form = self.form_class(request.form)

        if request.method == 'POST' and form.validate():
            instance = self.model()
            db.session.add(instance)
            form.populate_obj(instance)
            db.session.commit()
            flash(f'Object created', 'success')
            identity = get_pk_dict(instance)
            return redirect(url_for('.edit', **identity))

        context = {
            'form': form,
            'model': self.model,
        }
        return render_template(self.template, **context)
