from wtforms import Form
from wtforms import SubmitField
from wtforms import DateField
from wtforms import SelectField

from central_load_plan.extension import db
from central_load_plan.models import OFPFile

class OFPFileFilterForm(Form):

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
