from django.http import Http404
from django.utils.translation import get_language
from pytz import timezone
from datetime import datetime

import calendar
import django.utils
import pytz

LOCAL = timezone('Europe/Stockholm')
UTC = pytz.utc

# Global constants
MAX_RESERVATION_LENGTH = 1  # in hours


def get_object_or_404(object_type, key):
    language = get_language()
    if language not in ['en', 'sv']:
        language = 'en'

    obj = object_type.objects.language(language).get(pk=key)
    if obj is None:
        raise Http404
    return obj


def to_timestamp(datetime):
    """
    Takes a datetime and converts it into a POSIX timestamp in UTC timezone.
    """
    return calendar.timegm(as_utc_time(datetime).timetuple())


def from_timestamp(timestamp):
    """
    Takes a timestamp, assumed to be in UTC timezone, and returns
    a datetime in UTC timezone.
    """
    return UTC.localize(datetime.utcfromtimestamp(timestamp))


def as_local_time(time):
    return LOCAL.normalize(time.astimezone(LOCAL))


def as_utc_time(time):
    return UTC.normalize(time.astimezone(UTC))


def utc_now():
    return django.utils.timezone.now()
    # now = datetime.datetime.utcnow().replace(tzinfo=UTC)
    # return now
