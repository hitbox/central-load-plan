from werkzeug.routing import BaseConverter
from datetime import datetime

class DateConverter(BaseConverter):

    def to_python(self, value):
        return datetime.strptime(value, '%Y-%m-%d').date()

    def to_url(self, value):
        return value.strftime('%Y-%m-%d')


class TimeConverter(BaseConverter):

    def to_python(self, value):
        return datetime.strptime(value, '%H%M%S').time()

    def to_url(self, value):
        return value.strftime('%H%M%S')


class DateTimeConverter(BaseConverter):
    regex = r'\d{4}-\d{2}-\d{2}_\d{6}'

    def to_python(self, value):
        return datetime.strptime(value, "%Y-%m-%d_%H%M%S")

    def to_url(self, value):
        return value.strftime("%Y-%m-%d_%H%M%S")


def init_app(app):
    app.url_map.converters['date'] = DateConverter
    app.url_map.converters['time'] = TimeConverter
