
from django.utils import timezone as djtimezone
from django.conf import settings
import os
from datetime import datetime as dt
import dateutil.parser
import pytz
from django.conf import settings
import random
from PIL import Image


def check_dt(dt, device_timezone=None, localise=True):
    if dt is None:
        return dt

    if device_timezone is None:
        device_timezone = pytz.timezone(settings.TIME_ZONE)

    if type(dt) is str:
        dt = dateutil.parser.parse(dt, dayfirst=False, yearfirst=True)

    if dt.tzinfo is None and localise:
        mytz = device_timezone
        dt = mytz.localize(dt)

    return dt


def create_image(image_width=500, image_height=500, colors=[(255, 0, 0), (0, 0, 255), (255, 255, 0)]):
    image = Image.new('RGB', (image_width, image_height))
    for x in range(image.width):
        for y in range(image.height):
            image.putpixel((x, y), random.choice(colors))
    return image
