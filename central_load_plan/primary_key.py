import sqlalchemy as sa

def get_pk_dict(instance):
    """
    Return a dict of {primary_key_column_name: value} for a model instance.
    """
    mapper = sa.inspect(instance).mapper
    # list of Column objects
    pk_cols = mapper.primary_key
    # tuple of PK values
    identity = sa.inspect(instance).identity
    if identity is None:
        return None  # instance not persisted yet
    return {col.name: val for col, val in zip(pk_cols, identity)}
