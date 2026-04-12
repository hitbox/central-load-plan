import logging
import sqlalchemy as sa

from flask import current_app

logger = logging.getLogger(__name__)

def get_lsyrept_engine(airline_code):
    """
    Get an engine for a given airline iata code.
    """
    credentials = current_app.config.get('CREDENTIALS_FOR_AIRLINE', {})
    # get to allow none
    airline_data = credentials.get(airline_code, {})
    keys = [
        'LSYREPT_PRODUCTION_DATABASE_URI',
        'LSYREPT_FALLBACK_DATABASE_URI',
    ]
    for name in keys:
        uri = current_app.config.get(name)

        # Create new URI with credentials for airline
        creds = {k:v for k, v in airline_data.items() if k in ('username', 'password')}
        uri = uri.set(**creds)

        connect_args = airline_data.get('connect_args', {})
        engine = sa.create_engine(uri, connect_args=connect_args)
        try:
            with engine.connect() as conn:
                pass
        except:
            raise
        else:
            logger.info(engine)
            return engine
