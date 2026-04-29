from wtforms import DateField
from wtforms import Form
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import SubmitField

from central_load_plan.extension import db
from central_load_plan.models import Airline
from central_load_plan.models import Airport
from central_load_plan.models import OFPFile

class QueryFormMixin:

    sorting_choices = ['', 'asc', 'desc']

    @property
    def request_args(self):
        return {field.name: field.data for field in self}


class OFPFileSortForm(QueryFormMixin, Form):

    airline_iata_code = SelectField()

    flight_origin_date = SelectField()

    origin_iata = SelectField()

    destination_iata = SelectField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self:
            field.choices = self.sorting_choices


class OFPFileFilterForm(QueryFormMixin, Form):

    airline_iata_code = SelectField()

    flight_origin_date = DateField()

    flight_number = IntegerField()

    origin_iata = SelectField()

    destination_iata = SelectField()

    filter = SubmitField('Update filter and sorting')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # select all Airlines for choices
        query = db.select(Airline.iata_code)
        airlines = db.session.scalars(query).all()
        airlines.insert(0, '')
        self.airline_iata_code.choices = airlines

        iata_stations = (
            db.session.scalars(
                db.select(Airport.iata_code)
                .order_by('iata_code')
            )
            .all()
        )
        iata_stations.insert(0, '')

        self.origin_iata.choices = iata_stations

        self.destination_iata.choices = iata_stations

        min_origin_date = db.session.scalars(db.select(db.func.min(OFPFile.flight_origin_date))).one()
        max_origin_date = db.session.scalars(db.select(db.func.max(OFPFile.flight_origin_date))).one()
        self.flight_origin_date.render_kw = {
            'min': min_origin_date,
            'max': max_origin_date,
        }
