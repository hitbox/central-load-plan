import uuid
import operator as py_operator

import sqlalchemy as sa

from sqlalchemy.ext.orderinglist import ordering_list
from flask_login import UserMixin
from central_load_plan import rendering
from central_load_plan.constants import APPNAME
from lxml import etree
from passlib.hash import argon2
from sqlalchemy.ext.hybrid import hybrid_property

from .clp_base import CLPBase
from .ofp_file import OFPFile

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
        python_type = column.type.python_type
        return python_type(value)

    def to_expression(self):
        """
        Query criteria expression useful to find all matching OFPFile objects
        matching this condition.
        """
        ofp_file_mapper = sa.inspect(OFPFile)

        ofp_file_column = ofp_file_mapper.columns[self.ofp_key]

        op = self.__valid_operators__[self.operator]

        values = [self._coerce_value(ofp_file_column, value) for value in self.values]

        if self.operator == 'contains':
            return op(ofp_file_column, values)
        elif values:
            return op(ofp_file_column, values[0])

    def is_match(self, ofp_file):
        """
        OFPCondition matches data scraped from OFP stored in OFPFile object.
        """
        ofp_file_mapper = sa.inspect(OFPFile)

        op = self.__valid_operators__[self.operator]

        #ofp_file_column = ofp_file_mapper.columns[self.ofp_key]
        ofp_file_column = getattr(ofp_file, self.ofp_key)

        values = [ofp_value.value for ofp_value in self.values]

        ofp_file_key_value = getattr(ofp_file, self.ofp_key)

        if self.operator == 'contains':
            # same as `b in a`
            return ofp_file_key_value in values
        else:
            return op(ofp_file_key_value, values[0])

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
