import sqlalchemy as sa

from flask import abort
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.views import View

from central_load_plan.extension import db

class EditObjectView(View):
    """
    Create or edit instances of a model class.
    """
    methods = ['GET', 'POST']

    def __init__(
        self,
        model,
        template,
        form_class_factory = None,
        form_class = None,
        extra_context = None,
    ):
        if not (form_class_factory or form_class):
            raise ValueError(
                'Either form_class_factory or form_class keyword'
                'argument is required.')
        if (form_class_factory and form_class):
            raise ValueError(
                'Exactly one of form_class_factory or'
                ' form_class keyword arguments is required.')

        self.model = model
        self.template = template
        self.form_class_factory = form_class_factory
        self.form_class = form_class
        self.extra_context = extra_context

    def dispatch_request(self, **ident):
        instance = db.session.get(self.model, ident)

        if instance is None:
            abort(404)

        if self.form_class_factory is not None:
            form_class = self.form_class_factory(instance)
        else:
            form_class = self.form_class

        if request.form:
            form = form_class(data=request.form)
        else:
            form = form_class(obj=instance)

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
