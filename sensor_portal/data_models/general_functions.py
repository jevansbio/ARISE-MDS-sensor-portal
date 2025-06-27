import os
import random
from datetime import datetime
from typing import Optional, Union

import dateutil.parser
import pytz
from django.conf import settings
from django.utils import timezone as djtimezone
from PIL import Image


def check_dt(
    dt: Optional[Union[datetime, str]],
    device_timezone: Optional[pytz.timezone] = None,
    localise: bool = True
) -> Optional[datetime]:
    """
    Parse and localize a datetime object or string.

    Converts a datetime object or string to a timezone-aware datetime object,
    localized to the specified device_timezone. If no timezone is provided, the
    application's default timezone is used. Supports parsing ISO-format datetime
    strings and can localize naive datetime objects if requested.

    Args:
        dt (datetime | str | None): The datetime object or ISO-format string to process.
            Returns None if input is None.
        device_timezone (pytz.timezone, optional): The timezone to use for localization.
            Defaults to settings.TIME_ZONE if not specified.
        localise (bool, optional): If True, localizes naive datetime objects to the
            specified timezone. Defaults to True.

    Returns:
        datetime | None: A timezone-aware datetime object if parsing succeeds, or None
        if input is None.
    """
    # If the input datetime is None, return None immediately.
    if dt is None:
        return dt

    # If no device timezone is provided, use the default timezone from settings.
    if device_timezone is None:
        device_timezone = pytz.timezone(settings.TIME_ZONE)

    # If the input datetime is a string, parse it into a datetime object.
    # The parsing assumes dayfirst=False and yearfirst=True for the format.
    if isinstance(dt, str):
        dt = dateutil.parser.parse(dt, dayfirst=False, yearfirst=True)

    # If the datetime object is naive (lacks timezone info) and localization is enabled,
    # localize it to the specified device timezone.
    if dt.tzinfo is None and localise:
        mytz = device_timezone
        dt = mytz.localize(dt)

    return dt


def create_image(
    image_width: int = 500,
    image_height: int = 500,
    colors: list[tuple[int, int, int]] = [
        (255, 0, 0), (0, 0, 255), (255, 255, 0)]
) -> Image:
    """
    Generate a PIL Image with random pixel colors from a list.

    Creates a new RGB image of the specified size, with each pixel randomly
    assigned a color from the provided list of RGB tuples.

    Args:
        image_width (int, optional): Width of the image in pixels. Defaults to 500.
        image_height (int, optional): Height of the image in pixels. Defaults to 500.
        colors (list[tuple[int, int, int]], optional): List of RGB tuples to use for
            pixel colors. Defaults to [(255, 0, 0), (0, 0, 255), (255, 255, 0)].

    Returns:
        Image: A PIL Image object with randomly colored pixels.
    """

    image = Image.new('RGB', (image_width, image_height))
    for x in range(image.width):
        for y in range(image.height):
            image.putpixel((x, y), random.choice(colors))
    return image
