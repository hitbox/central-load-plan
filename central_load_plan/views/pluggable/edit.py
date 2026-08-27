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
        success_url_factory = None,
    ):
        """
        :param success_url_factory:
            callable taking (action_name, instance) where action_name is
            "delete" or "update" and instance is the database instance the
            action was performed on.
        """
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
        self._success_url_factory = success_url_factory

    @property
    def success_url_factory(self):
        if self._success_url_factory:
            success_url_factory = self._success_url_factory
        else:
            def success_url_factory(action, instance):
                return url_for(request.endpoint, **request.view_args)
        return success_url_factory

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
                url = self.success_url_factory('delete', instance)
            else:
                form.populate_obj(instance)
                flash('Object updated', 'success')
                url = self.success_url_factory('update', instance)

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
