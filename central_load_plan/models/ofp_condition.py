import uuid
import operator as py_operator

import sqlalchemy as sa

from flask_login import UserMixin
from markupsafe import Markup
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import AssociationProxy

from .clp_base import CLPBase
from .ofp_file import OFPFile

def get_column_type(model, name):
    """
    Get column type attribute from model by name. Drilling for associatonproxy
    attributes too.
    """
    mapper = sa.inspect(model)

    if name in mapper.columns:
        return mapper.columns[name].type

    attr = getattr(model, name, None)

    if isinstance(attr, AssociationProxy):
        rel = mapper.relationships[attr.target_collection]
        return rel.mapper.columns[attr.value_attr].type

    # InstrumentedAttribute/ColumnProperty
    prop = getattr(attr, 'property', None)
    if isinstance(prop, ColumnProperty):
        return prop.columns[0].type

    return None

class OFPCondition(CLPBase):
    """
    Conditional expression to test against parsed and deserialized OFP XML file data.
    """

    __tablename__ = 'ofp_condition'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, unique=True, nullable=False)

    blurb = sa.Column(
        sa.String,
        nullable = True,
        info = {
            'help': 'Short description of the purpose of this condition.',
        },
    )

    ofp_key = sa.Column(sa.String, nullable=False)

    operator = sa.Column(sa.String)

    __operators_choices__ = [
        ('eq', 'equals'),
        ('ne', 'not equals'),
        ('lt', 'less than'),
        ('le', 'less than or equal'),
        ('gt', 'greater than'),
        ('ge', 'greater than or equal'),
        ('contains', 'contains'),
        ('ilike', 'case-insensitive regex'),
    ]

    __valid_operators__ = {
        'eq': py_operator.eq,
        'ne': py_operator.ne,
        'lt': py_operator.lt,
        'le': py_operator.le,
        'gt': py_operator.gt,
        'ge': py_operator.ge,
        'contains': lambda col, val: col.contains(val),
        'ilike': lambda col, val: col.ilike(val),
    }

    __symbols__ = {
        'eq': '==',
        'ne': '!=',
        'lt': '<',
        'le': '<=',
        'gt': '>',
        'ge': '>=',
        'contains': 'in',
        'ilike': 'ilike',
    }

    values = sa.orm.relationship(
        'OFPConditionValue',
        back_populates = 'ofp_conditions',
        cascade = 'all, delete-orphan',
        order_by = 'OFPConditionValue.position',
        collection_class = ordering_list('position')
    )

    jobs = sa.orm.relationship(
        'JobTemplate',
        back_populates = 'ofp_condition',
    )

    @sa.orm.validates('ofp_key')
    def validate_ofp_key(self, key, value):
        """
        ofp_key must be an attribute name of OFPFile
        """
        mapper = sa.inspect(OFPFile)
        if value not in dir(OFPFile):
            raise ValueError(f'{value} is not an attribute of OFPFile')
        return value

    @sa.orm.validates('operator')
    def validate_operator(self, key, value):
        if value not in self.__valid_operators__:
            raise ValueError(f'{value} not in {self.__valid_operators__}')
        return value

    @classmethod
    def choices_for_select_field(cls, session, include_none=True):
        choices = [(obj.id, obj.name) for obj in session.scalars(sa.select(cls))]
        if include_none:
            item = ('', '(None)')
            choices.insert(0, item)
        return choices

    def _coerce_value(self, column, value):
        type_ = get_column_type(OFPFile, column.key)
        python_type = type_.python_type
        return python_type(value)

    def to_expression(self):
        """
        Query criteria expression useful to find all matching OFPFile objects
        matching this condition.
        """
        ofp_file_mapper = sa.inspect(OFPFile)

        op = self.__valid_operators__[self.operator]

        values = [ofp_condition_value.value for ofp_condition_value in self.values]

        if self.operator != 'contains':
            values = values[0]

        attr = getattr(OFPFile, self.ofp_key)

        return op(attr, values)

    def is_match(self, ofp_file):
        """
        OFPCondition matches data scraped from OFP stored in OFPFile object.
        """
        ofp_file_mapper = sa.inspect(OFPFile)

        op = self.__valid_operators__[self.operator]

        ofp_file_column = getattr(ofp_file, self.ofp_key)

        values = [ofp_value.value for ofp_value in self.values]

        ofp_file_key_value = getattr(ofp_file, self.ofp_key)

        if self.operator == 'contains':
            # same as `b in a`
            return ofp_file_key_value in values
        else:
            return op(ofp_file_key_value, values[0])

    @classmethod
    def get_or_create(cls, **kwargs):
        from central_load_plan.extension import db

        query = (
            db.session.scalars(cls)
            .filter_by(**kwargs)
        )
        instance = db.session.scalars(query).one_or_none()
        if instance is None:
            instance = cls(**kwargs)
            db.session.add(instance)
        return instance

    @property
    def condition_as_string(self):
        """
        Returns a human-readable string of the condition:
        e.g. "weight >= 1000" or "aircraft in [A320, B737]"
        """
        # Symbol for operator
        op_sym = self.__symbols__.get(self.operator, self.operator)

        # Get string representations of values
        value_strings = [repr(v.value) for v in self.values]

        if self.operator == "contains":
            # For multi-value "contains"
            val_str = "[" + ", ".join(value_strings) + "]"
        else:
            # Single-value operators
            if value_strings:
                val_str = value_strings[0]
            else:
                val_str = ""

        return f"{self.ofp_key} {op_sym} {val_str}"

    @property
    def condition_as_html(self):
        html = ['<span class="python-expression">']

        # OFPFile key to apply match
        html.append(f'<span class="key">{self.ofp_key}</span>')

        # Symbol for operator
        op_sym = self.__symbols__.get(self.operator, self.operator)
        html.append(f'<span class="operator">{op_sym}</span>')

        if self.values:
            if len(self.values) > 1:
                html.append('<ul>')
                for ofp_conditon_value in self.values:
                    html.append(f'<li class="literal">{ ofp_conditon_value.value }</li>')

                html.append('</ul>')
            else:
                one_value = self.values[0].value
                html.append(f'<span class="literal">{ one_value }</span>')

        return Markup(''.join(html))


class OFPConditionValue(CLPBase):

    __tablename__ = 'ofp_condition_value'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    value = sa.Column(sa.String, nullable=False)

    ofp_condition_id = sa.Column(sa.ForeignKey('ofp_condition.id'))

    ofp_conditions = sa.orm.relationship(
        'OFPCondition',
        back_populates = 'values'
    )

    position = sa.Column(sa.Integer, default=0)

    def typed_value(self, type_):
        return type_(self.value)

    def __repr__(self):
        return self.value
