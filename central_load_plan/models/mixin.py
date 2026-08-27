from central_load_plan.extension import db

class ModelMixin:

    @classmethod
    def query_factory(cls):
        raise NotImplementedError
