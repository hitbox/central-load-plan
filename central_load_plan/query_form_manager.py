from flask import request

from central_load_plan.extension import db

class QueryFormManager:
    """
    Coordinate filtering and sorting forms for a model, generating queries from
    request arguments.
    This helps with (de)serializing data from the frontend as we need to
    partition it by filtering and sorting.
    """

    def __init__(
        self,
        model,
        filter_form_class = None,
        sort_form_class = None,
        filter_prefix = 'filter',
        sort_prefix = 'sort',
    ):
        self.model = model
        self.filter_form_class = filter_form_class
        self.sort_form_class = sort_form_class
        self.filter_prefix = filter_prefix
        self.sort_prefix = sort_prefix

    def get_filter_form(self):
        if callable(self.filter_form_class):
            return self.filter_form_class(request.args, prefix=self.filter_prefix)

    def get_sort_form(self):
        if callable(self.sort_form_class):
            return self.sort_form_class(request.args, prefix=self.sort_prefix)

    def apply_forms_to_query(self, query):
        # Apply filters from form
        filter_form = self.get_filter_form()
        if filter_form is not None:
            for field in filter_form:
                if hasattr(self.model, field.short_name) and field.data:
                    model_field = getattr(self.model, field.short_name)
                    query = query.where(
                        model_field == field.data,
                    )

        # Apply sort from form
        sort_form = self.get_sort_form()
        if sort_form is not None:
            for field in sort_form:
                if hasattr(self.model, field.short_name) and field.data:
                    model_field = getattr(self.model, field.short_name)
                    if field.data == 'desc':
                        model_field = model_field.desc()
                    query = query.order_by(model_field)

        return query

    def get_pagination(self):
        query = db.select(self.model)
        query = self.apply_forms_to_query(query)
        return db.paginate(query), query
