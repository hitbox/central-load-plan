import uuid

import sqlalchemy as sa

from central_load_plan.extension import db

class Airline(db.Model):
    """
    OFP XML file scraped for data.
    """

    __tablename__ = 'airline'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    iata_code = sa.Column(
        sa.String,
        nullable = False,
        unique = True,
    )

    icao_code = sa.Column(
        sa.String,
        nullable = False,
        unique = True,
    )
