import uuid

import sqlalchemy as sa

from .clp_base import CLPBase

class Airline(CLPBase):
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
