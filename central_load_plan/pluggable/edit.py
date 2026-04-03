import sqlalchemy as sa

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.views import View

from central_load_plan.www.extension import db

class EditObjectView(View):
    """
    Create or edit instances of a model class.
    """
    methods = ['GET', 'POST']

    def __init__(self, form_class, model, template, extra_context=None):
        self.form_class = form_class
        self.model = model
        self.template = template
        self.extra_context = extra_context

    def dispatch_request(self, **ident):
        instance = db.session.get(self.model, ident)

        if instance is None:
            abort(404)

        if request.form:
            form = self.form_class(data=request.form)
        else:
            form = self.form_class(obj=instance)

        if request.method == 'POST' and form.validate():
            if 'delete' in request.form:
                db.session.delete(instance)
                flash('Object deleted', 'success')
                url = url_for('.list')
            else:
                form.populate_obj(instance)
                flash('Object updated', 'success')
                url = url_for(request.endpoint, **request.view_args)

            db.session.commit()
            return redirect(url)

        context = {
            'instance': instance,
            'form': form,
            'model': self.model,
        }
        if self.extra_context:
            context.update(self.extra_context(context))

        return render_template(self.template, **context)
