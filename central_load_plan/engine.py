import sqlalchemy as sa

from flask import current_app

def get_lsyrept_engine(airline_code):
    credentials = current_app.config.get('CREDENTIALS_FOR_AIRLINE', {})
    # get to allow none
    airline_creds = credentials.get(airline_code, {})
    keys = [
        'LSYREPT_PRODUCTION_DATABASE_URI',
        'LSYREPT_FALLBACK_DATABASE_URI',
    ]
    for name in keys:
        uri = current_app.config.get(name)
        # Create new URI with credentials for airline
        uri = uri.set(**airline_creds)
        engine = sa.create_engine(uri)
        try:
            with engine.connect() as conn:
                pass
        except:
            raise
        else:
            return engine
