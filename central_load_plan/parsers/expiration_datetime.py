import re

from datetime import datetime
from datetime import timezone as timezonelib
from zoneinfo import ZoneInfo

two_or_more_whitespace = re.compile(r'\s{2,}')

def find_expiration_line(lines):
    prefix = 'Expiration Date: '
    for datetime_text in lines:
        if datetime_text.startswith(prefix):
            # remove prefix for remaining datetime string
            datetime_text = datetime_text.removeprefix(prefix)
            # strip
            datetime_text = datetime_text.strip()
            return datetime_text

def expiration_datetime_from_raw_text(
    raw_text,
    text_timezone,
    ignore_missing = False,
    ignore_no_match = False,
):
    lines = two_or_more_whitespace.split(raw_text)

    datetime_text = find_expiration_line(lines)
    if datetime_text is None:
        if ignore_missing:
            return None
        else:
            raise ValueError(f'Expiration Date line not found in {raw_text=}')

    dt = try_really_hard_to_parse_datetime(
        datetime_text = datetime_text,
        text_timezone = text_timezone,
        ignore_no_match = ignore_no_match,
    )
    return dt

def make_expiration_datetime_from_raw_text_parser(
    text_timezone,
    ignore_missing = False,
    ignore_no_match = False,
):
    if text_timezone is None:
        raise ValueError(f'source timezone info must be given.')

    if not isinstance(text_timezone, ZoneInfo):
        raise ValueError(
            f'Invalid type for text_timezone:'
            f' {type(text_timezone)}, must be zoneinfo.ZoneInfo object')

    def func(raw_text):
        return expiration_datetime_from_raw_text(
            raw_text = raw_text,
            text_timezone = text_timezone,
            ignore_missing = ignore_missing,
            ignore_no_match = ignore_no_match,
        )

    return func

def try_really_hard_to_parse_datetime(
    datetime_text,
    text_timezone,
    ignore_no_match = False,
):
    if not isinstance(datetime_text, str):
        raise ValueError(f'Invalid type {datetime_text=} ({type(datetime_text)})')

    if text_timezone is None:
        raise ValueError(f'source timezone info must be given.')

    if not isinstance(text_timezone, ZoneInfo):
        raise ValueError(
            f'Invalid type for text_timezone:'
            f' {type(text_timezone)}, must be zoneinfo.ZoneInfo object')

    if not ignore_no_match in (False, True):
        raise ValueError(
            f'Invalid type for ignore_no_match must be True or False.')

    # basically every variation encountered in the xml files.
    formats = [
        '%m/%d/%Y %I:%M:%S %p',
        '%m/%d/%Y %I:%M:%S', # without AM/PM...
        '%m/%d/%Y %I:%M', # ...no seconds
        '%m/%d/%Y %H:', # ...no minutes trailing colon
        '%m/%d/%Y %H', # ...no minutes
        '%m/%d/%Y', # no time
        '%m/%d/%y', # two-digit year
    ]

    for format_ in formats:
        try:
            dt = datetime.strptime(datetime_text, format_)
            dt = dt.replace(tzinfo=text_timezone)
            return dt.astimezone(timezonelib.utc)
        except ValueError:
            pass

    # Fell through for all datetime formats, raise if configured.
    if not ignore_no_match:
        raise ValueError(
            f'No matching datetime format for {datetime_text=!r}')
