from marshmallow import pre_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy import auto_field

from central_load_plan.models.lsyrept import ChainItemDaily
from central_load_plan.models.lsyrept import LSYCrewMember
from central_load_plan.models.lsyrept import Duty
from central_load_plan.models.lsyrept import ItemDaily
from central_load_plan.models.lsyrept import NonCrewMember
from central_load_plan.models.lsyrept import RemarkOfEvent

class PreLoadMixin:

    @pre_load
    def strip_nulls(self, data, **kwargs):
        # Fix trouble moving data from oracle to postgresql.
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = v.replace('\x00', '').strip()
        return data


class ChainItemDailySchema(PreLoadMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = ChainItemDaily
        load_instance = True


class CrewMemberSchema(PreLoadMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = LSYCrewMember
        load_instance = True


class DutySchema(PreLoadMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = Duty
        load_instance = True


class ItemDailySchema(PreLoadMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = ItemDaily
        load_instance = True


class NonCrewMemberSchema(PreLoadMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = NonCrewMember
        load_instance = True


class RemarkOfEventSchema(PreLoadMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = RemarkOfEvent
        load_instance = True


# lookup schema from model
lsyrept_model_schemas = {
    ChainItemDaily: ChainItemDailySchema,
    LSYCrewMember: CrewMemberSchema,
    Duty: DutySchema,
    ItemDaily: ItemDailySchema,
    NonCrewMember: NonCrewMemberSchema,
    RemarkOfEvent: RemarkOfEventSchema,
}
