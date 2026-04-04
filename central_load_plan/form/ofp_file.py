from wtforms import Form
from wtforms import SubmitField
from wtforms import DateField
from wtforms import SelectField

from central_load_plan.extension import db
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

    origin_iata = SelectField()

    destination_iata = SelectField()

    filter = SubmitField('Filter')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        airlines = db.session.scalars(db.select(OFPFile.airline_iata_code).distinct()).all()
        airlines.insert(0, '')
        self.airline_iata_code.choices = airlines

        iata_stations = (
            db.session.scalars(
                db.select(OFPFile.origin_iata.label('station'))
                .union(
                    db.select(OFPFile.destination_iata.label('station'))
                )
                .order_by('station')
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
