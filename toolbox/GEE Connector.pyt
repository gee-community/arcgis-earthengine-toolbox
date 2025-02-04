# -*- coding: utf-8 -*-

import arcpy
import ee
import os
import json
import requests
import numpy as np
import xarray
import datetime

# ArcGEE version
__version__ = "0.0.1"

from google.cloud import storage
import arcgee

# import logging

# import arcgee.arctools as arctools

# logger = logging.getLogger(__name__)

""" Define functions"""


def get_reducer_list():
    """
    Get the complete list of available reducers from ee.Reducer.

    Returns:
        list: A list of all reducer names available in ee.Reducer.
    """
    reducers = [
        "ee.Reducer.allNonZero",
        "ee.Reducer.anyNonZero",
        "ee.Reducer.autoHistogram",
        "ee.Reducer.bitwiseAnd",
        "ee.Reducer.bitwiseOr",
        "ee.Reducer.centeredCovariance",
        "ee.Reducer.circularMean",
        "ee.Reducer.circularStddev",
        "ee.Reducer.circularVariance",
        "ee.Reducer.combine",
        "ee.Reducer.count",
        "ee.Reducer.countDistinct",
        "ee.Reducer.countDistinctNonNull",
        "ee.Reducer.countEvery",
        "ee.Reducer.countRuns",
        "ee.Reducer.covariance",
        "ee.Reducer.disaggregate",
        "ee.Reducer.first",
        "ee.Reducer.firstNonNull",
        "ee.Reducer.fixed2DHistogram",
        "ee.Reducer.fixedHistogram",
        "ee.Reducer.forEach",
        "ee.Reducer.forEachBand",
        "ee.Reducer.frequencyHistogram",
        "ee.Reducer.geometricMedian",
        "ee.Reducer.getOutputs",
        "ee.Reducer.group",
        "ee.Reducer.histogram",
        "ee.Reducer.intervalMean",
        "ee.Reducer.kendallsCorrelation",
        "ee.Reducer.kurtosis",
        "ee.Reducer.last",
        "ee.Reducer.lastNonNull",
        "ee.Reducer.linearFit",
        "ee.Reducer.linearRegression",
        "ee.Reducer.max",
        "ee.Reducer.mean",
        "ee.Reducer.median",
        "ee.Reducer.min",
        "ee.Reducer.minMax",
        "ee.Reducer.mode",
        "ee.Reducer.pearsonsCorrelation",
        "ee.Reducer.percentile",
        "ee.Reducer.product",
        "ee.Reducer.repeat",
        "ee.Reducer.ridgeRegression",
        "ee.Reducer.robustLinearRegression",
        "ee.Reducer.sampleStdDev",
        "ee.Reducer.sampleVariance",
        "ee.Reducer.sensSlope",
        "ee.Reducer.setOutputs",
        "ee.Reducer.skew",
        "ee.Reducer.spearmansCorrelation",
        "ee.Reducer.splitWeigths",
        "ee.Reducer.stdDev",
        "ee.Reducer.sum",
        "ee.Reducer.toCollection",
        "ee.Reducer.toList",
        "ee.Reducer.unweighted",
        "ee.Reducer.variance",
    ]
    return reducers


def get_filter_list():
    """
    Get the complete list of available filters from ee.Filter.

    Returns:
        list: A list of all filter names available in ee.Filter, including filters for:
            - Logical operations (and, or, not)
            - Temporal filtering (date, calendarRange, dayOfYear)
            - Spatial filtering (bounds, intersects, contains)
            - Value comparisons (equals, greaterThan, lessThan, etc.)
            - String operations (stringContains, stringStartsWith, etc.)
            - And more

    """
    # all filters in the ee.Filter
    filters = [
        "ee.Filter.and",  # Combines two or more filters with logical AND
        "ee.Filter.area",
        "ee.Filter.aside",
        "ee.Filter.bounds",  # Filter by geographic bounds (within a geometry)
        "ee.Filter.calendarRange",  # Filter by calendar range (e.g., specific years, months, days)
        "ee.Filter.contains",  # Checks if a collection contains a specific value
        "ee.Filter.date",  # Filter by date range
        "ee.Filter.daterangeContains",
        "ee.Filter.dayofYear",
        "ee.Filter.disjoint",
        "ee.Filter.eq",  # Equality filter (equals)
        "ee.Filter.equals",
        "ee.Filter.evaluate",
        "ee.Filter.expression",
        "ee.Filter.getInfo",
        "ee.Filter.greaterThan",
        "ee.Filter.greaterThanOrEuqals",
        "ee.Filter.gt",  # Greater than filter
        "ee.Filter.gte",  # Greater than or equal to filter
        "ee.Filter.hasType",
        "ee.Filter.inList",  # Filter by values within a list (like SQL's IN clause)
        "ee.Filter.intersects",  # Filter features that intersect a geometry
        "ee.Filter.isContained",  # Checks if a geometry is contained by another geometry
        "ee.Filter.lessThan",
        "ee.Filter.lessThanOrEquals",
        "ee.Filter.listContains",  # Filter if a list contains a specific value
        "ee.Filter.lt",  # Less than filter
        "ee.Filter.lte",  # Less than or equal to filter
        "ee.Filter.maxDifference",
        "ee.Filter.neq",  # Not equal filter
        "ee.Filter.not",  # Negates a filter
        "ee.Filter.notEuqals",
        "ee.Filter.notNull",  # Filters features where a property is not null
        "ee.Filter.or",  # Combines two or more filters with logical OR
        "ee.Filter.rangeContains",
        "ee.Filter.serialize",
        "ee.Filter.stringContains",  # Checks if a string contains a substring
        "ee.Filter.stringEndsWith",  # Checks if a string ends with a specific substring
        "ee.Filter.stringStartsWith",  # Checks if a string starts with a specific substring
        "ee.Filter.withinDistance",
    ]

    return filters


def add_date_to_gif(
    input_gif,
    output_gif,
    dates,
    font_path=None,
    font_size=40,
    position=(10, 10),
    color="white",
):
    """
    Adds a date label to each frame of a GIF.

    Args:
        input_gif (str): Path to the input GIF file.
        output_gif (str): Path to save the output GIF file.
        dates (list): List of dates to add to each frame. Must match the number of frames in the GIF.
        font_path (str): Path to a font file. Defaults to a system font.
        font_size (int): Font size for the date text.
        position (tuple): (x, y) position for the date label.
        color (str): Color of the text. Defaults to white.
    """
    from PIL import Image, ImageDraw, ImageFont, ImageSequence

    # Open the input GIF
    gif = Image.open(input_gif)

    # Load the font (use a default font if no font_path is provided)
    font = ImageFont.truetype(font_path or "arial.ttf", font_size)

    frames = []
    for i, frame in enumerate(ImageSequence.Iterator(gif)):
        # Ensure the number of dates matches the frames
        if i >= len(dates):
            break

        # Copy the frame to edit
        frame = frame.convert("RGBA")
        draw = ImageDraw.Draw(frame)

        # Add the date text
        draw.text(position, dates[i], font=font, fill=color)

        # Append the edited frame
        frames.append(frame)

    # Save the frames as a new GIF
    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        loop=gif.info.get("loop", 0),
        duration=gif.info.get("duration", 100),
    )


def validate_date(date_str, date_format="%Y-%m-%d"):
    """Validates that a date string matches the expected format.

    Args:
        date_str (str): The date string to validate
        date_format (str, optional): Expected date format. Defaults to "%Y-%m-%d".

    Raises:
        ValueError: If the date string does not match the expected format

    Examples:
        >>> validate_date("2023-01-01")  # Valid date
        >>> validate_date("01/01/2023")  # Raises ValueError
    """
    try:
        # Try to parse the date string with the expected format
        datetime.datetime.strptime(date_str, date_format)
        arcpy.AddMessage(f"Valid date: {date_str}")
    except ValueError:
        # Add error message if the format is incorrect
        arcpy.AddError(
            f"Invalid date format: '{date_str}'. Expected format: {date_format}."
        )
        raise  # Re-raise the error to stop execution


def download_ee_video(collection, video_args, out_gif, timeout=300, proxies=None):
    """Downloads a video thumbnail as a GIF image from Earth Engine.

    Args:
        collection (object): An ee.ImageCollection.
        video_args (object): Parameters for expring the video thumbnail.
        out_gif (str): File path to the output GIF.
        timeout (int, optional): The number of seconds the request will be timed out. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use. Defaults to None.
    """

    out_gif = os.path.abspath(out_gif)
    if not out_gif.endswith(".gif"):
        print("The output file must have an extension of .gif.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if "region" in video_args.keys():
        roi = video_args["region"]

        if not isinstance(roi, ee.Geometry):
            try:
                roi = roi.geometry()
            except Exception as e:
                print("Could not convert the provided roi to ee.Geometry")
                print(e)
                return

        video_args["region"] = roi
    if "dimensions" not in video_args:
        video_args["dimensions"] = 768

    try:
        print("Generating URL...")
        url = collection.getVideoThumbURL(video_args)

        print(f"Downloading GIF image from {url}\nPlease wait ...")
        r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)

        if r.status_code != 200:
            print("An error occurred while downloading.")
            print(r.json()["error"]["message"])
            return
        else:
            with open(out_gif, "wb") as fd:
                for chunk in r.iter_content(chunk_size=1024):
                    fd.write(chunk)
            print(f"The GIF image has been saved to: {out_gif}")
    except Exception as e:
        print(e)


def date_sequence(start, end, unit, date_format="YYYY-MM-dd", step=1):
    """Creates a date sequence.

    Args:
        start (str): The start date, e.g., '2000-01-01'.
        end (str): The end date, e.g., '2000-12-31'.
        unit (str): One of 'year', 'quarter', 'month' 'week', 'day', 'hour', 'minute', or 'second'.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.
        step (int, optional): The step size. Defaults to 1.

    Returns:
        ee.List: A list of date sequence.
    """

    def get_quarter(d):
        return str((int(d[5:7]) - 1) // 3 * 3 + 1).zfill(2)

    def get_monday(d):
        date_obj = datetime.datetime.strptime(d, "%Y-%m-%d")
        start_of_week = date_obj - datetime.timedelta(days=date_obj.weekday())
        return start_of_week.strftime("%Y-%m-%d")

    if unit == "year":
        start = start[:4] + "-01-01"
    elif unit == "month":
        start = start[:7] + "-01"
    elif unit == "quarter":
        start = start[:5] + get_quarter(start) + "-01"
    elif unit == "week":
        start = get_monday(start)

    start_date = ee.Date(start)
    end_date = ee.Date(end)

    if unit != "quarter":
        count = ee.Number(end_date.difference(start_date, unit)).toInt()
        num_seq = ee.List.sequence(0, count)
        if step > 1:
            num_seq = num_seq.slice(0, num_seq.size(), step)
        date_seq = num_seq.map(
            lambda d: start_date.advance(d, unit).format(date_format)
        )

    else:
        unit = "month"
        count = ee.Number(end_date.difference(start_date, unit)).divide(3).toInt()
        num_seq = ee.List.sequence(0, count.multiply(3), 3)
        date_seq = num_seq.map(
            lambda d: start_date.advance(d, unit).format(date_format)
        )

    return date_seq


def get_current_year():
    """Get the current year.

    Returns:
        int: The current year.
    """
    today = datetime.date.today()
    return today.year


# Generate landsat timeseries, from GEEMAP
def landsat_timeseries(
    roi=None,
    start_year=1984,
    end_year=None,
    start_date="06-10",
    end_date="09-20",
    apply_fmask=True,
    frequency="year",
    date_format=None,
    step=1,
):
    """Generates an annual Landsat ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to None, which means the current year.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        frequency (str, optional): Frequency of the timelapse: year, quarter, month. Defaults to 'year'.
        date_format (str, optional): Format of the date. Defaults to None.
        step (int, optional): The step size to use when creating the date sequence. Defaults to 1.
    Returns:
        object: Returns an ImageCollection containing annual Landsat images.
    """

    # Input and output parameters.
    import re

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )

    if end_year is None:
        end_year = get_current_year()

    if not isinstance(roi, ee.Geometry):
        try:
            roi = roi.geometry()
        except Exception as e:
            arcpy.AddMessage("Could not convert the provided roi to ee.Geometry")
            arcpy.AddError(e)

    feq_dict = {
        "year": "YYYY",
        "month": "YYYY-MM",
        "quarter": "YYYY-MM",
    }

    if date_format is None:
        date_format = feq_dict[frequency]

    if frequency not in feq_dict:
        arcpy.AddError("frequency must be year, quarter, or month.")

    # Setup vars to get dates.
    if (
        isinstance(start_year, int)
        and (start_year >= 1984)
        and (start_year < get_current_year())
    ):
        pass
    else:
        arcpy.AddError("The start year must be an integer >= 1984.")

    if (
        isinstance(end_year, int)
        and (end_year > 1984)
        and (end_year <= get_current_year())
    ):
        pass
    else:
        arcpy.AddError(f"The end year must be an integer <= {get_current_year()}.")

    if re.match(r"[0-9]{2}-[0-9]{2}", start_date) and re.match(
        r"[0-9]{2}-[0-9]{2}", end_date
    ):
        pass
    else:
        arcpy.AddError(
            "The start date and end date must be month-day, such as 06-10, 09-20"
        )

    try:
        datetime.datetime(int(start_year), int(start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        arcpy.AddMessage("The input dates are invalid.")
        arcpy.AddError(e)

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(
        str(start_year) + "-" + start_date, str(start_year) + "-" + end_date
    )
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])

    # Landsat collection preprocessingEnabled
    # Get Landsat surface reflectance collections for OLI, ETM+ and TM sensors.
    LC09col = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    LC08col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    LE07col = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    LT05col = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
    LT04col = ee.ImageCollection("LANDSAT/LT04/C02/T1_L2")

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        """Filter an image collection by region of interest and date range.

        Args:
            col (ee.ImageCollection): Input image collection
            roi (ee.Geometry): Region of interest
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format

        Returns:
            ee.ImageCollection: Filtered image collection
        """
        return col.filterBounds(roi).filterDate(start_date, end_date)

    # Function to get and rename bands of interest from OLI.
    def renameOli(img):
        """Rename bands of interest from OLI sensor.

        Args:
            img (ee.Image): Input image from OLI sensor

        Returns:
            ee.Image: Image with renamed bands
        """
        return img.select(
            ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
            ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"],
        )

    # Function to get and rename bands of interest from ETM+.
    def renameEtm(img):
        """Rename bands of interest from ETM+ sensor.

        Args:
            img (ee.Image): Input image from ETM+ sensor

        Returns:
            ee.Image: Image with renamed bands
        """
        return img.select(
            ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"],
            ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"],
        )

    def fmask(image):
        """Apply Fmask (Function of mask) for cloud and shadow masking.

        Args:
            image (ee.Image): Input Landsat image

        Returns:
            ee.Image: Masked image with scaled surface reflectance values

        Notes:
            Bit values in QA_PIXEL band:
            - Bit 0: Fill
            - Bit 1: Dilated Cloud
            - Bit 2: Cirrus
            - Bit 3: Cloud
            - Bit 4: Cloud Shadow
        """
        qaMask = image.select("QA_PIXEL").bitwiseAnd(int("11111", 2)).eq(0)
        opticalBands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
        return image.addBands(opticalBands, None, True).updateMask(qaMask)

    # Define function to prepare OLI images.
    def prepOli(img):
        """Prepare OLI sensor images by applying scaling and optional masking.

        Args:
            img (ee.Image): Input OLI sensor image

        Returns:
            ee.Image: Processed image with renamed bands and bicubic resampling
        """
        orig = img
        if apply_fmask:
            img = fmask(img)
        else:
            img = img.select("SR_B.").multiply(0.0000275).add(-0.2)
        img = renameOli(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Define function to prepare ETM+ images.
    def prepEtm(img):
        """Prepare ETM+ sensor images by applying scaling and optional masking.

        Args:
            img (ee.Image): Input ETM+ sensor image

        Returns:
            ee.Image: Processed image with renamed bands and bicubic resampling
        """
        orig = img
        if apply_fmask:
            img = fmask(img)
        else:
            img = img.select("SR_B.").multiply(0.0000275).add(-0.2)
        img = renameEtm(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Get annual median collection.
    def getAnnualComp(y):
        """Get annual median composite for a given year.

        Args:
            y (int): Year to process

        Returns:
            ee.Image: Annual median composite with metadata properties
        """
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day)
        )
        endDate = startDate.advance(ee.Number(n_days), "day")

        # Filter collections and prepare them for merging.
        LC09coly = colFilter(LC09col, roi, startDate, endDate).map(prepOli)
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC09coly.merge(LC08coly).merge(LE07coly).merge(LT05coly).merge(LT04coly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(nBands, yearImg, dummyImg))
        return yearImg.set(
            {
                "year": y,
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    # Get monthly median collection.
    def getMonthlyComp(startDate):
        """Get monthly median composite starting from a given date.

        Args:
            startDate (ee.Date): Start date for the monthly composite

        Returns:
            ee.Image: Monthly median composite with metadata properties
        """
        startDate = ee.Date(startDate)
        endDate = startDate.advance(1, "month")

        # Filter collections and prepare them for merging.
        LC09coly = colFilter(LC09col, roi, startDate, endDate).map(prepOli)
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC09coly.merge(LC08coly).merge(LE07coly).merge(LT05coly).merge(LT04coly)

        monthImg = col.median()
        nBands = monthImg.bandNames().size()
        monthImg = ee.Image(ee.Algorithms.If(nBands, monthImg, dummyImg))
        return monthImg.set(
            {
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    # Get quarterly median collection.
    def getQuarterlyComp(startDate):
        """Get quarterly (3-month) median composite starting from a given date.

        Args:
            startDate (ee.Date): Start date for the quarterly composite

        Returns:
            ee.Image: Quarterly median composite with metadata properties
        """
        startDate = ee.Date(startDate)

        endDate = startDate.advance(3, "month")

        # Filter collections and prepare them for merging.
        LC09coly = colFilter(LC09col, roi, startDate, endDate).map(prepOli)
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC09coly.merge(LC08coly).merge(LE07coly).merge(LT05coly).merge(LT04coly)

        quarter = col.median()
        nBands = quarter.bandNames().size()
        quarter = ee.Image(ee.Algorithms.If(nBands, quarter, dummyImg))
        return quarter.set(
            {
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    # Make a dummy image for missing years.
    bandNames = ee.List(["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"])
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames).selfMask().int16()

    # Make list of /quarterly/monthly image composites.

    if frequency == "year":
        years = ee.List.sequence(start_year, end_year, step)
        imgList = years.map(getAnnualComp)
    elif frequency == "quarter":
        quarters = date_sequence(
            str(start_year) + "-01-01",
            str(end_year) + "-12-31",
            "quarter",
            date_format,
            step,
        )
        imgList = quarters.map(getQuarterlyComp)
    elif frequency == "month":
        months = date_sequence(
            str(start_year) + "-01-01",
            str(end_year) + "-12-31",
            "month",
            date_format,
            step,
        )
        imgList = months.map(getMonthlyComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(
        lambda img: img.clip(roi).set({"coordinates": roi.coordinates()})
    )

    return imgCol


# Create landsat timelapse, simplified from GEEMAP
def landsat_timelapse(
    roi=None,
    out_gif=None,
    start_year=1984,
    end_year=None,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params=None,
    dimensions=768,
    frames_per_second=5,
    crs="EPSG:3857",
    apply_fmask=True,
    frequency="year",
):
    """Generates a Landsat timelapse GIF image. This function is adapted from https://emaprlab.users.earthengine.app/view/lt-gee-time-series-animator. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to None, which will use the current year.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']. Defaults to ['NIR', 'Red', 'Green'].
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        dimensions (int, optional): a number or pair of numbers (in format 'WIDTHxHEIGHT') Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 5.
        crs (str, optional): The coordinate reference system to use. Defaults to "EPSG:3857".
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        frequency (str, optional): Frequency of the timelapse: year, quarter, month. Defaults to 'year'.

    Returns:
        str: File path to the output GIF image.
    """

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )
    elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
        roi = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        pass
    else:
        arcpy.AddError("The provided roi is invalid. It must be an ee.Geometry")

    out_gif = os.path.abspath(out_gif)
    out_dir = os.path.dirname(out_gif)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if end_year is None:
        end_year = get_current_year()

    allowed_bands = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"]

    if len(bands) == 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        arcpy.AddError(
            "You can only select 3 bands from the following: {}".format(
                ", ".join(allowed_bands)
            )
        )

    try:
        if vis_params is None:
            vis_params = {}
            vis_params["bands"] = bands
            vis_params["min"] = 0
            vis_params["max"] = 0.4
            vis_params["gamma"] = [1, 1, 1]

        raw_col = landsat_timeseries(
            roi,
            start_year,
            end_year,
            start_date,
            end_date,
            apply_fmask,
            frequency,
        )

        col = raw_col.select(bands).map(
            lambda img: img.visualize(**vis_params).set(
                {
                    "system:time_start": img.get("system:time_start"),
                    "system:date": img.get("system:date"),
                }
            )
        )

        video_args = vis_params.copy()
        video_args["dimensions"] = dimensions
        video_args["region"] = roi
        video_args["framesPerSecond"] = frames_per_second
        video_args["crs"] = crs
        video_args["bands"] = ["vis-red", "vis-green", "vis-blue"]
        video_args["min"] = 0
        video_args["max"] = 255

        download_ee_video(col, video_args, out_gif)

        if os.path.exists(out_gif):
            date_list = col.aggregate_array("system:date").getInfo()
            add_date_to_gif(out_gif, out_gif, date_list)

        return out_gif

    except Exception as e:
        arcpy.AddError(e)


# List all functions in the imported module
def list_functions_from_script(module):
    """List all functions in the imported module.

    Args:
        module (module): The module from which to list functions.

    Returns:
        list: A list of function names available in the module.
    """
    import inspect

    function_list = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj):
            function_list.append(name)
    return function_list


def clean_asset_id(asset_id):
    """Clean the asset ID string by removing any whitespace, trailing slash, and quotes.

    Args:
        asset_id (str): Input asset ID string

    Returns:
        str: Cleaned asset ID string
    """
    asset_id = asset_id.strip().strip('"').strip("'")
    if asset_id.endswith("/"):
        asset_id = asset_id[:-1]
    return asset_id


def check_ee_datatype(parameter, type_str):
    """Check the Earth Engine data type of the input object."""
    asset_id = parameter.valueAsText
    asset_id = clean_asset_id(asset_id)
    # type_str = "IMAGE" or "TABLE" or "IMAGE_COLLECTION"
    if type_str == "TABLE":
        type_out = "FEATURE COLLECTION"
    else:
        type_out = type_str.replace("_", " ")

    # asset ID could be invalid
    try:
        data_type = get_ee_datatype(asset_id)
        if data_type != type_str:
            parameter.setErrorMessage(
                f"The input asset ID is not {type_out} . Please input a valid {type_out} asset ID."
            )
            return
    except Exception as e:
        parameter.setErrorMessage(
            f"Error: {str(e)}. Please input a valid {type_out} asset ID."
        )
        return


def get_ee_datatype(asset_id):
    """Get the Earth Engine data type of the input object.

    Returns:
        str: Earth Engine data type of the input object
    """
    # Get the input object
    obj = ee.data.getAsset(asset_id)
    # Get the data type of the input object
    data_type = obj["type"]
    return data_type


def init_and_set_tags(project=None, workload_tag=None):
    """Initialize Earth Engine and set user agent and workload tags.

    Args:
        project (str, optional): Google Cloud project ID. Defaults to None.
        workload_tag (str, optional): Custom workload tag. Defaults to None.
    """
    ee.Initialize(project=project)

    user_agent = f"ArcGIS_EE/{__version__}/ArcPy/{arcpy.__version__}"
    if ee.data.getUserAgent() != user_agent:
        ee.data.setUserAgent(user_agent)

    ee.data.setDefaultWorkloadTag("arcgis-ee-connector")

    if workload_tag is not None:
        ee.data.setWorkloadTag(workload_tag)

    # check initialization setup
    project_id = ee.data.getProjectConfig()["name"].split("/")[1]
    arcpy.AddMessage(f"Current project ID: {project_id}")
    arcpy.AddMessage(f"Current user agent: {ee.data.getUserAgent()}")
    arcpy.AddMessage(f"Current workload tag: {ee.data.getWorkloadTag()}")
    arcpy.AddMessage("Earth Engine is ready to use.")

    return


# Project a point to a different spatial reference
def project_to_new_sr(x, y, in_spatial_ref, out_spatial_ref):
    """Project a point from input spatial reference to output spatial reference.

    Args:
        x (float): X coordinate in input spatial reference
        y (float): Y coordinate in input spatial reference
        in_spatial_ref (SpatialReference): Input spatial reference object
        out_spatial_ref (SpatialReference): Output spatial reference object

    Returns:
        tuple: coordinates in output spatial reference
    """
    point = arcpy.Point(x, y)
    point_geom = arcpy.PointGeometry(point, in_spatial_ref)
    new_sr = arcpy.SpatialReference(out_spatial_ref)
    point_geom_wgs84 = point_geom.projectAs(new_sr)
    return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y


# Get centroid and extent coordinates of input image or feature collection
def get_object_centroid(obj, error_margin):
    """Get the centroid and extent coordinates of an Earth Engine object.

    Args:
        obj (ee.Image or ee.FeatureCollection): Earth Engine object
        error_margin (float): Error margin for geometry calculations

    Returns:
        tuple: (centroid_coords, extent_coords) where:
            - centroid_coords is [lon, lat] of centroid
            - extent_coords is list of corner coordinates defining the bounds
    """
    # get centroid geometry from input image
    centroid = obj.geometry().centroid(error_margin)
    # coordinates in list
    centroid_coords = centroid.coordinates().getInfo()
    # get image extent
    extent = obj.geometry().bounds(error_margin)
    # coordinates in list
    extent_coords = extent.coordinates().get(0).getInfo()
    return centroid_coords, extent_coords


# Zoom project map view to point
def zoom_to_point(aprx, point_coords, extent_coords):
    """Zoom the map view to a point with buffer based on extent.

    Args:
        aprx (ArcGISProject): ArcGIS Pro project object
        point_coords (list): [lon, lat] coordinates of center point
        extent_coords (list): List of corner coordinates defining the bounds
    """
    # get current project map view
    view = aprx.activeView
    # Create an extent around the centroid
    centroid_x, centroid_y = point_coords
    bottom_left = extent_coords[0]
    top_right = extent_coords[2]
    x_min = bottom_left[0]
    y_min = bottom_left[1]
    x_max = top_right[0]
    y_max = top_right[1]
    width = x_max - x_min
    height = y_max - y_min
    zoom_buffer = max(width, height) * 0.6

    extent = arcpy.Extent(
        centroid_x - zoom_buffer,  # xmin
        centroid_y - zoom_buffer,  # ymin
        centroid_x + zoom_buffer,  # xmax
        centroid_y + zoom_buffer,  # ymax
    )
    # assuming the ee object centroid and extent are always in lat/lon
    extent.spatialReference = arcpy.SpatialReference(4326)

    # Set the map view to the new extent
    view.camera.setExtent(extent)

    return


# Get map view extent
def get_map_view_extent(target_epsg=4326):
    """Get the current map view extent coordinates in WGS 84.
    Args:
        target_epsg (int): Target EPSG code for the extent coordinates
    Returns:
        tuple: (xmin, ymin, xmax, ymax) coordinates in WGS 84
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    # Get the active map view
    view = aprx.activeView
    # Get the current camera object, which includes the map view extent
    camera = view.camera

    # Extract the projection and the boundary coordinates (extent)
    spatial_ref = camera.getExtent().spatialReference
    xmin = camera.getExtent().XMin
    ymin = camera.getExtent().YMin
    xmax = camera.getExtent().XMax
    ymax = camera.getExtent().YMax
    # Check if projection code is the target EPSG code
    # projected
    poly_prj = spatial_ref.PCSCode
    if poly_prj == 0:
        # geographic
        poly_prj = spatial_ref.GCSCode
    # Always using latitude and longtiude for ee.Geometry, ee will automatically transform
    if str(poly_prj) not in "EPSG:" + str(target_epsg):
        # Convert the extent corners to target EPSG
        xmin, ymin = project_to_new_sr(xmin, ymin, spatial_ref, target_epsg)
        xmax, ymax = project_to_new_sr(xmax, ymax, spatial_ref, target_epsg)

    return xmin, ymin, xmax, ymax


# Get the coordinates from polygon feature layer
def get_polygon_coords(in_poly):
    """Extract coordinates from a polygon feature layer and convert to WGS 84.

    Args:
        in_poly (str): Input polygon feature layer path/name

    Returns:
        list: List of polygon coordinates in WGS 84
    """
    spatial_ref = arcpy.Describe(in_poly).spatialReference
    poly_prj = spatial_ref.PCSCode
    if poly_prj == 0:
        poly_prj = spatial_ref.GCSCode
    arcpy.AddMessage("Input feature layer projection CRS is " + str(poly_prj))

    # Project input feature to EPSG:4326 if needed
    target_poly = in_poly
    if str(poly_prj) not in "EPSG:4326":
        arcpy.AddMessage("Projecting input feature layer to EPSG:4326 ...")
        out_sr = arcpy.SpatialReference(4326)
        arcpy.Project_management(in_poly, "poly_temp", out_sr)
        target_poly = "poly_temp"

    # convert input feature to geojson
    arcpy.FeaturesToJSON_conversion(
        target_poly, "temp.geojson", "FORMATTED", "", "", "GEOJSON"
    )

    # Read the GeoJSON file
    upper_path = os.path.dirname(arcpy.env.workspace)
    file_geojson = os.path.join(upper_path, "temp.geojson")
    with open(file_geojson) as f:
        geojson_data = json.load(f)

    # Collect polygon object coordinates
    coords = []
    for feature in geojson_data["features"]:
        coords.append(feature["geometry"]["coordinates"])
    arcpy.AddMessage("Total number of polygon objects: " + str(len(coords)))

    # Delete temporary geojson
    if target_poly == "poly_temp":
        arcpy.management.Delete("poly_temp")
    arcpy.management.Delete(file_geojson)

    return coords


# Check whether use projection or crs code for image to xarray dataset
def whether_use_projection(ic):
    """Check whether to use projection or CRS code for image to xarray dataset.

    Args:
        ic (ee.ImageCollection): Input image collection

    Returns:
        bool: True if projection should be used, False if CRS code should be used
    """
    # Start with original projection
    prj = ic.first().select(0).projection()
    # Check crs code
    crs_code = prj.crs().getInfo()
    # Three scenarios: EPSG is unknown, EPSG is 4326, EPSG is others
    if (crs_code is None) or (crs_code == "EPSG:4326"):
        use_projection = True
        arcpy.AddMessage("Open dataset with projection")
    # ESPG is others
    # ValueError: cannot convert float NaN to integer will occur if using projection
    else:
        use_projection = False
        arcpy.AddMessage("Open dataset with CRS code")

    return use_projection


# Download GEE Image to GeoTiff
def image_to_geotiff(
    ic,
    bands,
    crs,
    scale_ds,
    roi,
    use_projection,
    out_tiff,
):
    """Download a GEE Image to GeoTiff format.

    Args:
        ic (ee.ImageCollection): Input image collection
        bands (list): List of band names to include
        crs (str): Coordinate reference system
        scale_ds (float): Scale/resolution for downloading
        roi (ee.Geometry): Region of interest geometry
        use_projection (bool): Whether to use projection or CRS code
        out_tiff (str): Output GeoTiff file path
    """
    import rasterio
    from rasterio.transform import from_origin

    prj = ic.first().select(0).projection()
    crs_code = prj.crs().getInfo()

    # When EPSG is unknown or 4326, use projection
    if use_projection:
        ds = xarray.open_dataset(
            ic,
            engine="ee",
            projection=prj,
            scale=scale_ds,
            **({"geometry": roi} if roi is not None else {}),
        )
        # Use either X/Y or lat/lon depending on the availability
        if "X" in list(ds.variables.keys()):
            arcpy.AddMessage("Use X/Y to define tranform")
            transform = from_origin(
                ds["X"].values[0], ds["Y"].values[-1], scale_ds, -scale_ds
            )
        else:
            arcpy.AddMessage("Use lat/lon to define transform")
            scale_x = abs(ds["lon"].values[0] - ds["lon"].values[1])
            scale_y = abs(ds["lat"].values[0] - ds["lat"].values[1])
            transform = from_origin(
                ds["lon"].values[0], ds["lat"].values[-1], scale_x, -scale_y
            )
    # ESPG is others, use crs code
    # ValueError: cannot convert float NaN to integer will occur if using projection
    else:
        ds = xarray.open_dataset(
            ic,
            engine="ee",
            crs=crs_code,
            scale=scale_ds,
            **({"geometry": roi} if roi is not None else {}),
        )
        if "X" in list(ds.variables.keys()):
            arcpy.AddMessage("Use X/Y to define tranform")
            transform = from_origin(
                ds["X"].values[0], ds["Y"].values[0], scale_ds, -scale_ds
            )
        else:
            arcpy.AddMessage("Use lat/lon to define transform")
            scale_x = abs(ds["lon"].values[0] - ds["lon"].values[1])
            scale_y = abs(ds["lat"].values[0] - ds["lat"].values[1])
            transform = from_origin(
                ds["lon"].values[0], ds["lat"].values[0], scale_x, -scale_y
            )
    # Display transform parameters
    arcpy.AddMessage(transform)

    meta = {
        "driver": "GTiff",
        "height": ds[bands[0]].shape[2],
        "width": ds[bands[0]].shape[1],
        "count": len(bands),  # Number of bands
        "dtype": ds[bands[0]].dtype,  # Data type of the array
        "crs": crs,  # Coordinate Reference System, change if needed
        "transform": transform,
    }

    # Store band names
    band_names = {}
    i = 1
    for iband in bands:
        band_names["band_" + str(i)] = iband
        i += 1

    # Write the array to a multiband GeoTIFF file
    arcpy.AddMessage("Save image to " + out_tiff + " ...")
    i = 1
    with rasterio.open(out_tiff, "w", **meta) as dst:
        for iband in bands:
            if use_projection:
                dst.write(np.flipud(np.transpose(ds[iband].values[0])), i)
            else:
                dst.write(np.transpose(ds[iband].values[0]), i)

            i += 1
        # write band names into output tiff
        dst.update_tags(**band_names)
    return


# Upload local file to Google Cloud Storage bucket
def upload_to_gcs_bucket(
    storage_client, bucket_name, source_file_name, destination_blob_name
):
    """Upload a local file to Google Cloud Storage bucket.

    Args:
        storage_client (google.cloud.storage.Client): Storage client instance
        bucket_name (str): Name of the GCS bucket
        source_file_name (str): Local file path to upload
        destination_blob_name (str): Destination path in GCS bucket
    """
    arcpy.AddMessage("Upload to Google Cloud Storage ...")
    # Get the bucket that the file will be uploaded to
    bucket = storage_client.bucket(bucket_name)

    # Create a new blob and upload the file's content
    blob = bucket.blob(destination_blob_name)

    # Upload the file
    blob.upload_from_filename(source_file_name)

    full_blob_name = bucket_name + "/" + destination_blob_name
    arcpy.AddMessage(f"File {source_file_name} has been uploaded to {full_blob_name}.")


# Convert Google Cloud Storage file to Earth Engine asset
def gcs_file_to_ee_asset(asset_type, asset_id, bucket_uri):
    """Convert a Google Cloud Storage file to an Earth Engine asset.

    Args:
        asset_type (str): Type of Earth Engine asset to create
        asset_id (str): ID for the new Earth Engine asset
        bucket_uri (str): URI of the file in Google Cloud Storage
    """
    import subprocess

    arcpy.AddMessage("Convert Google Cloud Storage file to Earth Engine asset ...")
    arcpy.AddMessage("Upload " + bucket_uri + " to " + asset_id)
    # Define the Earth Engine CLI command
    command = [
        "earthengine",
        "upload",
        asset_type,
        "--asset_id=" + asset_id,
        bucket_uri,
    ]

    # Run the command
    process = subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Output the result
    arcpy.AddMessage(process.stdout.decode("utf-8"))


# Create an Earth Engine image collection
def create_image_collection(asset_folder):
    """Create an Earth Engine image collection.

    Args:
        asset_folder (str): Path where the image collection will be created
    """
    import subprocess

    arcpy.AddMessage("Create an Earth Engine image collection ...")
    # Define the Earth Engine CLI command
    command = [
        "earthengine",
        "create",
        "collection",
        asset_folder,
    ]

    # Run the command
    process = subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Output the result
    arcpy.AddMessage(process.stdout.decode("utf-8"))


# Create a folder on Earth Engine
def create_ee_folder(asset_folder):
    """Create a folder on Earth Engine.

    Args:
        asset_folder (str): Path where the folder will be created
    """
    import subprocess

    arcpy.AddMessage("Create an Earth Engine folder ...")
    # Define the Earth Engine CLI command
    command = [
        "earthengine",
        "create",
        "folder",
        asset_folder,
    ]

    # Run the command
    process = subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Output the result
    arcpy.AddMessage(process.stdout.decode("utf-8"))


# Check if an Earth Engine asset already exists
def asset_exists(asset_id):
    """Check if an Earth Engine asset already exists.

    Args:
        asset_id (str): ID of the Earth Engine asset to check

    Returns:
        bool: True if asset exists, False otherwise
    """
    try:
        # Try to retrieve asset information
        ee.data.getAsset(asset_id)
        return True
    except ee.EEException:
        # Asset does not exist
        return False


# List all folders in the bucket
def list_folders_recursive(storage_client, bucket_name, prefix=""):
    """Recursively list all folders in a Google Cloud Storage bucket.

    Args:
        storage_client (google.cloud.storage.Client): Storage client instance
        bucket_name (str): Name of the GCS bucket
        prefix (str, optional): Prefix to filter folders. Defaults to "".

    Returns:
        list: Sorted list of folder paths in the bucket
    """
    # List blobs with a delimiter to group them by "folders"
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter="/")

    # Need this code to active blob prefixes, otherwise, blob.prefixes are empty
    for blob in blobs:
        blob_name = blob.name

    folder_list = []
    # Folders are stored in the prefixes attribute
    if blobs.prefixes:
        for folder in blobs.prefixes:
            folder_list.append(folder)
            # Recursively call the function to go deeper into the folder
            folder_list.extend(
                list_folders_recursive(storage_client, bucket_name, prefix=folder)
            )

    return sorted(folder_list)


# List files within a folder in the bucket
def list_files_in_folder(storage_client, bucket_name, folder_name):
    """List files within a specified folder in a Google Cloud Storage bucket.

    Args:
        storage_client (google.cloud.storage.Client): Storage client instance
        bucket_name (str): Name of the GCS bucket
        folder_name (str): Path to the folder within the bucket

    Returns:
        list: List of file paths within the specified folder
    """
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name)

    # Filter out any "folders" (items ending with a trailing slash)
    files = [blob.name for blob in blobs if not blob.name.endswith("/")]

    return files


""" Toolbox """


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        tools = []

        # authentication tools
        tools.append(GEEInit)
        tools.append(ChangeProjectID)
        tools.append(GEEAuth)

        # data exploration tools
        tools.append(AddImg2MapbyID)
        tools.append(AddImg2MapbyObj)
        tools.append(AddImgCol2MapbyID)
        tools.append(AddImgCol2MapbyObj)
        tools.append(AddFeatCol2MapbyID)
        tools.append(AddFeatCol2MapbyObj)

        # data management tools
        tools.append(DownloadImgbyID)
        tools.append(DownloadImgbyObj)
        tools.append(DownloadImgColbyID)
        tools.append(DownloadImgColbyObj)
        tools.append(DownloadFeatColbyID)
        tools.append(DownloadFeatColbyObj)
        tools.append(DownloadImgCol2Gif)
        # currently not used, because the timelapse function causes too much data usage
        # tools.append(DownloadLandsatTimelapse2Gif)
        tools.append(Upload2GCS)
        tools.append(GCSFile2Asset)
        tools.append(SaveAsset2JSON)

        # data processing tools
        tools.append(ApplyFilterbyID)
        tools.append(ApplyFilterbyObj)
        tools.append(ApplyMapFunctionbyID)
        tools.append(ApplyMapFunctionbyObj)
        tools.append(ApplyReducerbyID)
        tools.append(ApplyReducerbyObj)
        tools.append(RunPythonScript)

        self.tools = tools


""" Authentication Tools """


# Initialize Earth Engine
class GEEInit:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Initialize Earth Engine"
        self.description = ""
        self.category = "Authentication Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        from google.auth import default

        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID for Earth Engine",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        # Fetch the project ID from the default credentials
        try:
            # get project ID from earthengine credentials
            # ee.Initialize()
            # project_id = ee.data.getProjectConfig()["name"].split("/")[1]
            # get project ID from Google cloud default credentials
            credentials, env_project_id = default()
            param0.value = credentials.quota_project_id
        except:
            param0.value = "None"

        param1 = arcpy.Parameter(
            name="workload_tag",
            displayName="Specify the workload tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param1.value = "arcgis-ee-connector"

        params = [param0, param1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        project_id = parameters[0].valueAsText
        workload_tag = parameters[1].valueAsText

        init_and_set_tags(project_id, workload_tag)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Change Project ID
class ChangeProjectID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Check or Change Project ID"
        self.description = ""
        self.category = "Authentication Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="current_id",
            displayName="Current project ID is shown below",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param1 = arcpy.Parameter(
            name="current_tag",
            displayName="Current workload tag is shown below",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="new_id",
            displayName="Specify the new project ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="new_tag",
            displayName="Specify the new workload tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Fetch the project ID from the credentials
        try:
            project_id = ee.data.getProjectConfig()["name"].split("/")[1]
            parameters[0].value = project_id
        except:
            parameters[0].value = "None"

        # Fetch workload tag
        parameters[1].value = ee.data.getWorkloadTag()

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        new_id = parameters[2].valueAsText
        new_tag = parameters[3].valueAsText

        ee.Initialize(project=new_id)
        project_id = ee.data.getProjectConfig()["name"].split("/")[1]
        arcpy.AddMessage(f"Project ID is now set to {project_id}")
        if new_tag:
            ee.data.setWorkloadTag(new_tag)
            arcpy.AddMessage(f"Workload tag is now set to {ee.data.getWorkloadTag()}")
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# GEE Authentication
class GEEAuth:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Authenticate Earth Engine"
        self.description = ""
        self.category = "Authentication Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID for Earth Engine",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param1 = arcpy.Parameter(
            name="workload_tag",
            displayName="Specify the workload tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        project_id = parameters[0].valueAsText
        workload_tag = parameters[1].valueAsText

        # Define functions
        def clear_credentials():
            credentials_path = os.path.expanduser("~/.config/earthengine/credentials")
            if os.path.exists(credentials_path):
                os.remove(credentials_path)
                arcpy.AddMessage(
                    "Previous credentials are removed. Re-authenticate now ..."
                )

        def authenticate_earth_engine(project_id):
            try:
                ee.Authenticate()
                init_and_set_tags(project_id, workload_tag)
                arcpy.AddMessage("Authentication successful")
            except Exception as e:
                arcpy.AddMessage(f"Authentication failed: {e}")

        clear_credentials()
        authenticate_earth_engine(project_id)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


""" Data Exploration Tools """


# Add GEE Image to Map by Asset ID
class AddImg2MapbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image to Map by Asset ID"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the image asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="out_json",
            displayName="Save the image object to serialized JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Optional",
        )

        param6.filter.list = ["json"]

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Check band list of the selected image
        img_id = parameters[0].valueAsText

        # Update only when filter list is empty
        if img_id and not parameters[1].filter.list:
            # clean asset id string to remove whitespace, quotes, and trailing slash
            img_id = clean_asset_id(img_id)
            image = ee.Image(img_id)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[1].filter.list = band_res_list

        # Reset band filter list when asset ID changes
        if not img_id:
            parameters[1].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        img_id = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        min_val = parameters[2].valueAsText
        max_val = parameters[3].valueAsText
        gamma_str = parameters[4].valueAsText
        palette_str = parameters[5].valueAsText

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get image by label
        img_id = clean_asset_id(img_id)
        img = ee.Image(img_id)
        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_id + "--" + "--".join(bands_only)
        else:
            tsl.name = img_id

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass

        # Save image object to serialized JSON file
        if parameters[6].valueAsText:
            out_json = parameters[6].valueAsText
            if not out_json.endswith(".json"):
                out_json = out_json + ".json"

            arcgee.data.save_ee_result(img, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Image to Map by Serialized Object in JSON
class AddImg2MapbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image to Map by Serialized Object"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized image object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            image = arcgee.data.load_ee_result(json_path)
            # Update when band filter list is empty
            if not parameters[1].filter.list:
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[1].filter.list = band_res_list

        # Reset band filter list when asset id changes
        if not json_path:
            parameters[1].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        json_path = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        min_val = parameters[2].valueAsText
        max_val = parameters[3].valueAsText
        gamma_str = parameters[4].valueAsText
        palette_str = parameters[5].valueAsText

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get image by label
        img = arcgee.data.load_ee_result(json_path)
        img_id = img.get("system:id").getInfo()
        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_id + "--" + "--".join(bands_only)
        else:
            tsl.name = img_id

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Image Collection to Map by Asset ID
class AddImgCol2MapbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image Collection to Map by Asset ID"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the image collection asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
            multiValue=False,
        )
        param1.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        param1.value = [["2014-03-01", "2014-05-01"]]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="image",
            displayName="Select an image",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param5 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param8 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param9 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param10 = arcpy.Parameter(
            name="out_json",
            displayName="Save the filtered image collection to serialized JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Optional",
        )

        param10.filter.list = ["json"]

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
            param9,
            param10,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Check image list of a given collection asset
        asset_id = parameters[0].valueAsText

        # Image collection size could be huge, may take long to load without filters
        # Only retrieve the list of images, when either filter dates or filter bounds are selected
        # if asset_id and ((start_date and end_date) or (lon and lat)):
        if asset_id:
            asset_id = clean_asset_id(asset_id)
            collection = ee.ImageCollection(asset_id)
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)
            # Get image IDs from collection, limit to 50 images to avoid slow response
            image_ids = collection.limit(100).aggregate_array("system:index").getInfo()
            parameters[4].filter.list = image_ids

        # Check band list of the selected image
        img_name = parameters[4].valueAsText
        # Update only when filter list is empty
        if img_name and not parameters[5].filter.list:
            img_id = asset_id + "/" + img_name
            image = ee.Image(img_id)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[5].filter.list = band_res_list

        # Reset image and band filter list when asset ID changes
        if not asset_id:
            parameters[4].filter.list = []
            if not img_name:
                parameters[5].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_id = parameters[0].valueAsText
        # These three input parameters are only used in updateParameters above
        # filter_dates = parameters[1].valueAsText
        # filter_bounds = parameters[2].valueAsText
        # use_extent = parameters[3].valueAsText
        img_name = parameters[4].valueAsText
        band_str = parameters[5].valueAsText
        min_val = parameters[6].valueAsText
        max_val = parameters[7].valueAsText
        gamma_str = parameters[8].valueAsText
        palette_str = parameters[9].valueAsText

        asset_id = clean_asset_id(asset_id)
        # Construct asset id for selected image
        img_id = asset_id + "/" + img_name

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get image by label
        img = ee.Image(img_id)
        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_id + "--" + "--".join(bands_only)
        else:
            tsl.name = img_id

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass

        # Save filtered image collection to serialized JSON file
        if parameters[10].valueAsText:
            out_json = parameters[10].valueAsText
            if not out_json.endswith(".json"):
                out_json = out_json + ".json"

            # Get the filter dates
            if parameters[1].valueAsText:
                val_list = parameters[1].values
                start_date = val_list[0][0]
                end_date = val_list[0][1]
            else:
                start_date = None
                end_date = None

            # Get the filter bounds
            if parameters[3].value:
                # Disable input coordinates if map extent is used
                parameters[2].enabled = False
                xmin, ymin, xmax, ymax = get_map_view_extent()
                # Get the centroid of map extent
                lon = (xmin + xmax) / 2
                lat = (ymin + ymax) / 2
            else:
                parameters[2].enabled = True
                if parameters[2].valueAsText:
                    val_list = parameters[2].values
                    lon = val_list[0][0]
                    lat = val_list[0][1]
                else:
                    lon = None
                    lat = None

            collection = ee.ImageCollection(asset_id)
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)

            arcgee.data.save_ee_result(collection, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Image Collection to Map by Serialized Object in JSON
class AddImgCol2MapbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image Collection to Map by Serialized Object"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="image",
            displayName="Select image by image ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            collection = ee.ImageCollection(arcgee.data.load_ee_result(json_path))
            # Only fill the image id filter list when it is empty
            if not parameters[1].filter.list:
                # Get image IDs from collection, limit to 100 to avoid slow response
                image_names = (
                    collection.limit(100).aggregate_array("system:index").getInfo()
                )
                parameters[1].filter.list = image_names

            # Check band list of the selected image
            img_name = parameters[1].valueAsText
            # Update only when filter list is empty
            if img_name and not parameters[2].filter.list:
                # JSON object could have additional map functions, use collection
                image = collection.filter(
                    ee.Filter.eq("system:index", img_name)
                ).first()
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[2].filter.list = band_res_list

        # Reset asset id display and image filter list when json file is not selected
        if not json_path:
            parameters[1].filter.list = []
            # Reset band filter list
            if not parameters[1].valueAsText:
                parameters[2].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        json_path = parameters[0].valueAsText
        img_name = parameters[1].valueAsText
        band_str = parameters[2].valueAsText
        min_val = parameters[3].valueAsText
        max_val = parameters[4].valueAsText
        gamma_str = parameters[5].valueAsText
        palette_str = parameters[6].valueAsText

        # load collection object
        collection = arcgee.data.load_ee_result(json_path)
        # Get image id for layer name
        asset_id = collection.get("system:id").getInfo()
        img_id = asset_id + "/" + img_name
        # Get image by label
        img = ee.Image(img_id)

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_id + "--" + "--".join(bands_only)
        else:
            tsl.name = img_id

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Feature Collection to Map by Asset ID
class AddFeatCol2MapbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Feature Collection to Map by Asset ID"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """
        Define the tool parameters.

        vis_params = {
            "color": "000000",
            "pointShape": "circle",
            "pointSize": 3,
            "width": 2,
            "lineType": "solid",
            "fillColor": '00FF00',
            "opacity": 0.8,

            "colorOpacity": 1,
            "fillColorOpacity": 0.66,
        }
        """

        param0 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the feature collection asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_props",
            displayName="Filter by Properties",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param1.columns = [
            ["GPString", "Property Name"],
            ["GPString", "Operator"],
            ["GPString", "Filter Value"],
        ]
        param1.filters[1].list = ["==", "!=", ">", ">=", "<", "<="]

        param2 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        # param2.value = [['2014-03-01','2014-05-01']]

        param3 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param3.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param4 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent (point)",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent (area)",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="color",
            displayName="Specify the color for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="out_json",
            displayName="Save the filtered feature collection to serialized JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Optional",
        )

        param7.filter.list = ["json"]

        # param2 = arcpy.Parameter(
        #     name="point_shape",
        #     displayName="Specify the point shape for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param2.filter.list = ['circle','square','diamond','cross','plus','triangle']

        # param3 = arcpy.Parameter(
        #     name="point_size",
        #     displayName="Specify the point size for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param3.filter.list = [2,4,6,8,10]

        # param4 = arcpy.Parameter(
        #     name="line_width",
        #     displayName="Specify the line width for visualization ",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param4.filter.list = [1,2,3,4,5]

        # param5 = arcpy.Parameter(
        #     name="line_type",
        #     displayName="Specify the line type for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param5.filter.list = ['solid','dotted','dashed']

        # param6 = arcpy.Parameter(
        #     name="fill_color",
        #     displayName="Specify the fill color of polygons for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")

        # param7 = arcpy.Parameter(
        #     name="opacity",
        #     displayName="Specify the opacity for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # # Set the value range
        # param7.filter.type = "Range"
        # param7.filter.list = [0, 1]

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        # ,param2,param3,param4,param5,param6,param7]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        asset_id = parameters[0].valueAsText

        if asset_id and not parameters[1].filters[0].list:
            asset_id = clean_asset_id(asset_id)
            fc = ee.FeatureCollection(asset_id)
            prop_names = fc.first().propertyNames().getInfo()
            parameters[1].filters[0].list = sorted(prop_names)

        # Reset filter list when asset id is empty
        if not asset_id:
            parameters[1].filters[0].list = []

        # Disable input coordinates if map extent is used
        if parameters[4].value:
            parameters[3].enabled = False
            parameters[5].enabled = False
        else:
            parameters[3].enabled = True
            parameters[5].enabled = True

        # Disable centoer of map extent if map extent is used
        if parameters[5].value:
            # parameters[3].enabled = False
            parameters[4].enabled = False
        else:
            # parameters[3].enabled = True
            parameters[4].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        # Make sure the input datatype is feature collection
        if parameters[0].valueAsText:
            check_ee_datatype(parameters[0], "TABLE")

        # Make sure property name is only used once
        prop_list = []
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            for row in val_list:
                prop_name = row[0]
                if prop_name not in prop_list:
                    prop_list.append(prop_name)
                else:
                    parameters[1].setErrorMessage(
                        f"The property name '{prop_name}' is used more than once. Please use unique property names."
                    )
                    return

    def execute(self, parameters, messages):
        """
        The source code of the tool.
        """
        asset_id = parameters[0].valueAsText
        feat_color = parameters[6].valueAsText

        asset_id = clean_asset_id(asset_id)

        # point_shape= parameters[2].valueAsText
        # point_size = parameters[3].valueAsText
        # line_width = parameters[4].valueAsText
        # line_type  = parameters[5].valueAsText
        # fill_color = parameters[6].valueAsText
        # opacity    = parameters[7].valueAsText

        # Define visualization parameters
        vis_params = {}
        # Add color to vis_params if specified
        if feat_color:
            vis_params["color"] = feat_color
        # # Add point shape and size if specified
        # if point_shape :
        #     vis_params['pointShape'] = point_shape
        # if point_size :
        #     vis_params['pointSize'] = int(point_size)
        # # Add line width and type if specified
        # if line_width :
        #     vis_params['width'] = int(line_width)
        # if line_type :
        #     vis_params['lineType'] = line_type

        # # Add fill color and opacity if specified
        # if fill_color :
        #     vis_params['fillColor'] = fill_color
        # if opacity :
        #     vis_params['fillColorOpacity'] = float(opacity)

        # Get image by label
        fc = ee.FeatureCollection(asset_id)

        # Filter by properties
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            # Could be multiple filter properties
            for row in val_list:
                prop_name = row[0]
                # property value could be integer, float or string
                try:
                    prop_val = int(row[2])
                except ValueError:
                    try:
                        prop_val = float(row[2])
                    except ValueError:
                        prop_val = row[2]
                operator = row[1]

                # Check if prop_val is a string and format accordingly
                if isinstance(prop_val, str):
                    # If prop_val is a string, wrap it in single quotes
                    filter_condition = "{} {} '{}'".format(
                        prop_name, operator, prop_val
                    )
                else:
                    # If prop_val is an integer or float, no quotes needed
                    filter_condition = "{} {} {}".format(prop_name, operator, prop_val)

                arcpy.AddMessage("Filter by property: " + filter_condition)
                fc = fc.filter(filter_condition)

        # Filter by dates if specified
        if parameters[2].valueAsText:
            val_list = parameters[2].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
            fc = fc.filterDate(start_date, end_date)

        # Filter by bounds if specified
        if parameters[4].value or parameters[5].value:  # Use map extent
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Filter by point
            if parameters[4].value:
                # Get the centroid of map extent
                lon = (xmin + xmax) / 2
                lat = (ymin + ymax) / 2
                fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
            else:  # filter by area
                roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
                fc = fc.filterBounds(roi)

        else:  # use input coordinates
            if parameters[3].valueAsText:
                val_list = parameters[3].values
                lon = val_list[0][0]
                lat = val_list[0][1]
                fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
            else:  # no filter by bounds
                lon = None
                lat = None

        # Feature collection could contain zero record after filters
        if fc.size().getInfo() > 0:
            # Get the map ID and token
            map_id_dict = fc.getMapId(vis_params)

            # Construct the URL
            map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

            # Add map URL to the current ArcMap
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.listMaps("Map")[0]
            tsl = aprxMap.addDataFromPath(map_url)
            tsl.name = asset_id

            # Zoom to feature collection centroid if provided by dataset
            try:
                centroid_coords, bounds_coords = get_object_centroid(fc, 1)
                zoom_to_point(aprx, centroid_coords, bounds_coords)
            except:
                pass

            # Save object to serialized JSON file
            if parameters[7].valueAsText:
                out_json = parameters[7].valueAsText
                if not out_json.endswith(".json"):
                    out_json = out_json + ".json"
                arcgee.data.save_ee_result(fc, out_json)

        else:
            arcpy.AddWarning(
                "No data record returned after applying filters! Please reset the filters and try again."
            )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Feature Collection to Map by Serialized JSON Object
class AddFeatCol2MapbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Feature Collection to Map by Serialized Object"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """
        Define the tool parameters.

        vis_params = {
            "color": "000000",
            "pointShape": "circle",
            "pointSize": 3,
            "width": 2,
            "lineType": "solid",
            "fillColor": '00FF00',
            "opacity": 0.8,

            "colorOpacity": 1,
            "fillColorOpacity": 0.66,
        }
        """

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="color",
            displayName="Specify the color for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        # param2 = arcpy.Parameter(
        #     name="point_shape",
        #     displayName="Specify the point shape for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param2.filter.list = ['circle','square','diamond','cross','plus','triangle']

        # param3 = arcpy.Parameter(
        #     name="point_size",
        #     displayName="Specify the point size for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param3.filter.list = [2,4,6,8,10]

        # param4 = arcpy.Parameter(
        #     name="line_width",
        #     displayName="Specify the line width for visualization ",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param4.filter.list = [1,2,3,4,5]

        # param5 = arcpy.Parameter(
        #     name="line_type",
        #     displayName="Specify the line type for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param5.filter.list = ['solid','dotted','dashed']

        # param6 = arcpy.Parameter(
        #     name="fill_color",
        #     displayName="Specify the fill color of polygons for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")

        # param7 = arcpy.Parameter(
        #     name="opacity",
        #     displayName="Specify the opacity for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # # Set the value range
        # param7.filter.type = "Range"
        # param7.filter.list = [0, 1]

        params = [param0, param1]
        # ,param2,param3,param4,param5,param6,param7]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """
        The source code of the tool.
        """
        json_path = parameters[0].valueAsText
        feat_color = parameters[1].valueAsText

        # load collection object
        fc = arcgee.data.load_ee_result(json_path)
        asset_id = fc.get("system:id").getInfo()

        # point_shape= parameters[2].valueAsText
        # point_size = parameters[3].valueAsText
        # line_width = parameters[4].valueAsText
        # line_type  = parameters[5].valueAsText
        # fill_color = parameters[6].valueAsText
        # opacity    = parameters[7].valueAsText

        # Define visualization parameters
        vis_params = {}
        # Add color to vis_params if specified
        if feat_color:
            vis_params["color"] = feat_color

        # # Add point shape and size if specified
        # if point_shape :
        #     vis_params['pointShape'] = point_shape
        # if point_size :
        #     vis_params['pointSize'] = int(point_size)
        # # Add line width and type if specified
        # if line_width :
        #     vis_params['width'] = int(line_width)
        # if line_type :
        #     vis_params['lineType'] = line_type

        # # Add fill color and opacity if specified
        # if fill_color :
        #     vis_params['fillColor'] = fill_color
        # if opacity :
        #     vis_params['fillColorOpacity'] = float(opacity)

        # Feature collection could contain zero record after filters
        if fc.size().getInfo() > 0:
            # Get the map ID and token
            map_id_dict = fc.getMapId(vis_params)

            # Construct the URL
            map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

            # Add map URL to the current ArcMap
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.listMaps("Map")[0]
            tsl = aprxMap.addDataFromPath(map_url)
            tsl.name = asset_id

            # Zoom to feature collection centroid if provided by dataset
            try:
                centroid_coords, bounds_coords = get_object_centroid(fc, 1)
                zoom_to_point(aprx, centroid_coords, bounds_coords)
            except:
                pass

        else:
            arcpy.AddWarning(
                "No data record returned after applying filters! Please reset the filters and try again."
            )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


""" Data Management Tools """


# Download GEE Image by Asset ID (through XEE + RasterIO)
class DownloadImgbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image by Asset ID"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Image collection inputs are optional
        param0 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the image asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the output file name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param5.filter.list = ["tif"]

        param6 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        img_id = parameters[0].valueAsText

        # Update only when filter list is empty
        if img_id and not parameters[1].filter.list:
            img_id = clean_asset_id(img_id)
            image = ee.Image(img_id)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[1].filter.list = band_res_list

        # Reset band filter list when asset id changes
        if not img_id:
            parameters[1].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[1].valueAsText
        if band_str and not parameters[2].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            # use the maximum scale of the selected band by default
            parameters[2].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[4].value:  # map extent selected
            parameters[3].enabled = False
        else:
            parameters[3].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio

        """The source code of the tool."""
        # Multiple images could be selected
        asset_id = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        scale = parameters[2].valueAsText
        in_poly = parameters[3].valueAsText
        use_extent = parameters[4].valueAsText
        out_tiff = parameters[5].valueAsText
        load_tiff = parameters[6].valueAsText

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # make sure output file ends with tif
        if not out_tiff.endswith(".tif"):
            out_tiff = out_tiff + ".tif"

        # Check image projection
        asset_id = clean_asset_id(asset_id)
        image = ee.Image(asset_id)

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        elif in_poly:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
        # Not using any ROI, download entire image
        else:
            roi = None

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        # Get crs for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown. Use WKT instead.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Download image by id
        img_id = asset_id
        arcpy.AddMessage("Download image: " + img_id + " ...")
        # Must be image collection to convert to xarray
        image = ee.ImageCollection(ee.Image(img_id))
        # Filter image by selected bands
        image = image.select(bands_only)

        # check if use projection
        use_projection = whether_use_projection(image)
        # download image as geotiff
        image_to_geotiff(
            image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
        )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download GEE Image by Serialized JSON Object (through XEE + RasterIO)
class DownloadImgbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image by Serialized Object"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized image object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the output file name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param5.filter.list = ["tif"]

        param6 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            image = arcgee.data.load_ee_result(json_path)
            # Update only when band filter list is empty
            if not parameters[1].filter.list:
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[1].filter.list = band_res_list

        # Reset band filter list when asset id changes
        if not json_path:
            parameters[1].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[1].valueAsText
        if band_str and not parameters[2].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            # use the maximum scale of the selected band by default
            parameters[2].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[4].value:  # map extent selected
            parameters[3].enabled = False
        else:
            parameters[3].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio

        """The source code of the tool."""
        # Multiple images could be selected
        json_path = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        scale = parameters[2].valueAsText
        in_poly = parameters[3].valueAsText
        use_extent = parameters[4].valueAsText
        out_tiff = parameters[5].valueAsText
        load_tiff = parameters[6].valueAsText

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # Make sure output file ends with tif
        if not out_tiff.endswith(".tif"):
            out_tiff = out_tiff + ".tif"

        # Check image projection
        image = arcgee.data.load_ee_result(json_path)

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        elif in_poly:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
        # Not using any ROI, download entire image
        else:
            roi = None

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        # Get crs for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown. Use WKT instead.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Download image by id
        img_id = image.get("system:id").getInfo()
        arcpy.AddMessage("Download image: " + img_id + " ...")
        # Must be image collection to convert to xarray
        image = ee.ImageCollection(ee.Image(img_id))
        # Filter image by selected bands
        image = image.select(bands_only)

        # check if use projection
        use_projection = whether_use_projection(image)
        # download image as geotiff
        image_to_geotiff(
            image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
        )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download GEE Image Collection by Asset ID (XEE + RasterIO)
class DownloadImgColbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image Collection by Asset ID"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Image collection inputs are optional
        param0 = arcpy.Parameter(
            name="ic_id",
            displayName="Specify the image collection asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param1.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        param1.value = [["2014-03-01", "2014-05-01"]]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="img_list",
            displayName="Select images to download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param5 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param6 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param7 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param8 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param9 = arcpy.Parameter(
            name="out_folder",
            displayName="Specify the output folder",
            datatype="DEFolder",
            direction="Input",
            parameterType="Required",
        )

        param10 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
            param9,
            param10,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:  # use map extent
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:  # use input lat/lon
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Check image list of a given collection asset
        asset_id = parameters[0].valueAsText

        # Image collection size could be huge, may take long time to load image IDs without filters
        # Only retrieve the list of images, when either filter dates or filter bounds are selected
        # if asset_id and ((start_date and end_date) or (lon and lat)):
        if asset_id:
            asset_id = clean_asset_id(asset_id)
            collection = ee.ImageCollection(asset_id)
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)
            # Get image IDs from collection
            image_list = collection.limit(100).aggregate_array("system:index").getInfo()
            parameters[4].filter.list = image_list

        # Check the band list of the first selected image, assuming all selected images have the same bands
        img_names = parameters[4].valueAsText
        # Update only when filter list is empty
        if img_names and not parameters[5].filter.list:
            # Get the first select image
            img_name = img_names.split(";")[0]
            img_id = asset_id + "/" + img_name
            image = ee.Image(img_id)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[5].filter.list = band_res_list

        # Reset band filter list when asset id changes
        if (not parameters[4].valueAsText) and (not asset_id):
            parameters[5].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[5].valueAsText
        if band_str and not parameters[6].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            parameters[6].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[8].value:  # map extent selected
            parameters[7].enabled = False
        else:
            parameters[7].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio

        """The source code of the tool."""
        # Multiple images could be selected
        asset_id = parameters[0].valueAsText
        img_names = parameters[4].valueAsText
        band_str = parameters[5].valueAsText
        scale = parameters[6].valueAsText
        in_poly = parameters[7].valueAsText
        use_extent = parameters[8].valueAsText
        out_folder = parameters[9].valueAsText
        load_tiff = parameters[10].valueAsText

        img_name_list = img_names.split(";")

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        elif in_poly:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
        # Not using any ROI, download entire image
        else:
            roi = None

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        asset_id = clean_asset_id(asset_id)
        # Check first image projection
        image = ee.Image(asset_id + "/" + img_name_list[0])

        # Get crs code for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Check if use projection or crs code
        image = ee.ImageCollection(image)
        use_projection = whether_use_projection(image)

        out_tiff_list = []
        # Iterate each selected image
        for img_name in img_name_list:
            # For image collection, concatenate to get the image asset ID
            img_id = asset_id + "/" + img_name

            # Create output file name based on image IDs
            out_tiff = os.path.join(out_folder, img_name.replace("/", "_") + ".tif")
            out_tiff_list.append(out_tiff)

            arcpy.AddMessage("Download image: " + img_id + " ...")
            # Must be image collection to convert to xarray
            image = ee.ImageCollection(ee.Image(img_id))
            # Filter image by selected bands
            image = image.select(bands_only)

            # download image as geotiff
            image_to_geotiff(
                image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
            )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            for out_tiff in out_tiff_list:
                aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download GEE Image Collection by Serialized JSON Object (XEE + RasterIO)
class DownloadImgColbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image Collection by Serialized Object"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized image collection object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="img_list",
            displayName="Select images to download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param4 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="out_folder",
            displayName="Specify the output folder",
            datatype="DEFolder",
            direction="Input",
            parameterType="Required",
        )

        param7 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            collection = ee.ImageCollection(arcgee.data.load_ee_result(json_path))
            # Only fill the image id filter list when it is empty
            if not parameters[1].filter.list:
                # Get image IDs from collection
                image_list = (
                    collection.limit(100).aggregate_array("system:index").getInfo()
                )
                parameters[1].filter.list = image_list

            # Check band list of the selected image
            img_names = parameters[1].valueAsText
            # Update only when filter list is empty
            if img_names and not parameters[2].filter.list:
                # Get the first select image
                img_name = img_names.split(";")[0]
                # JSON object could have additional map functions, use collection
                image = collection.filter(
                    ee.Filter.eq("system:index", img_name)
                ).first()
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[2].filter.list = band_res_list

        # Reset image filter list
        if not json_path:
            parameters[1].filter.list = []

        # Reset band filter list when asset ID or image changes
        if (not parameters[1].valueAsText) and (not json_path):
            parameters[2].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[2].valueAsText
        if band_str and not parameters[3].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            parameters[3].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[5].value:  # map extent selected
            parameters[4].enabled = False
        else:
            parameters[4].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio

        """The source code of the tool."""
        # Multiple images could be selected
        json_path = parameters[0].valueAsText
        img_names = parameters[2].valueAsText
        band_str = parameters[3].valueAsText
        scale = parameters[4].valueAsText
        in_poly = parameters[5].valueAsText
        use_extent = parameters[6].valueAsText
        out_folder = parameters[7].valueAsText
        load_tiff = parameters[8].valueAsText

        # load collection object
        collection = arcgee.data.load_ee_result(json_path)
        # Get image collection asset id
        asset_id = collection.get("system:id").getInfo()

        img_name_list = img_names.split(";")

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        elif in_poly:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
        # Not using any ROI, download entire image
        else:
            roi = None

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        # Check first image projection
        image = ee.Image(asset_id + "/" + img_name_list[0])

        # Get crs code for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Check if use projection or crs code
        image = ee.ImageCollection(image)
        use_projection = whether_use_projection(image)

        out_tiff_list = []
        # Iterate each selected image
        for img_name in img_name_list:
            # For image collection, concatenate to get the image asset ID
            img_id = asset_id + "/" + img_name

            # Create output file name based on image IDs
            out_tiff = os.path.join(out_folder, img_name.replace("/", "_") + ".tif")
            out_tiff_list.append(out_tiff)

            arcpy.AddMessage("Download image: " + img_id + " ...")
            # Must be image collection to convert to xarray
            image = ee.ImageCollection(ee.Image(img_id))
            # Filter image by selected bands
            image = image.select(bands_only)

            # download image as geotiff
            image_to_geotiff(
                image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
            )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            for out_tiff in out_tiff_list:
                aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download Feature Collection by Asset ID
class DownloadFeatColbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Feature Collection by Asset ID"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """
        Define the tool parameters.

        """

        param0 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the feature collection asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_props",
            displayName="Filter by Properties",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param1.columns = [
            ["GPString", "Property Name"],
            ["GPString", "Operator"],
            ["GPString", "Filter Value"],
        ]
        param1.filters[1].list = ["==", "!=", ">", ">=", "<", "<="]

        param2 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        # param2.value = [['2014-03-01','2014-05-01']]

        param3 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Select the type of filter-by-location",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param3.filter.list = [
            "Coordinates (Point)",
            "Map Centroid (Point)",
            "Polygon (Area)",
            "Map Extent (Area)",
        ]

        param4 = arcpy.Parameter(
            name="use_coords",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param4.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param5 = arcpy.Parameter(
            name="use_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="select_geometry",
            displayName="Select the geometry type to download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param6.filter.list = ["Point", "Multipoint", "Polyline", "Polygon"]

        param7 = arcpy.Parameter(
            name="out_feature",
            displayName="Specify the output file name",
            datatype="DEFeatureClass",
            direction="Output",
            parameterType="Required",
        )

        param8 = arcpy.Parameter(
            name="load_feat",
            displayName="Load feature class to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
        ]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        asset_id = parameters[0].valueAsText

        if asset_id:
            asset_id = clean_asset_id(asset_id)
            fc = ee.FeatureCollection(asset_id)
            prop_names = fc.first().propertyNames().getInfo()
            # Update only when filter list is empty
            if not parameters[1].filters[0].list:
                parameters[1].filters[0].list = sorted(prop_names)
            if not parameters[6].filter.list:
                parameters[6].filter.list = sorted(prop_names)

        # Reset filter list when asset id is empty
        if not asset_id:
            parameters[1].filters[0].list = []

        # Disable input coordinates if map extent is used
        parameters[4].enabled = False
        parameters[5].enabled = False

        if parameters[3].valueAsText == "Coordinates (Point)":
            parameters[4].enabled = True
        elif parameters[3].valueAsText == "Polygon (Area)":
            parameters[5].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        # Make sure the input datatype is feature collection
        if parameters[0].valueAsText:
            check_ee_datatype(parameters[0], "TABLE")

        # Make sure property name is only used once
        prop_list = []
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            for row in val_list:
                prop_name = row[0]
                if prop_name not in prop_list:
                    prop_list.append(prop_name)
                else:
                    parameters[1].setErrorMessage(
                        f"The property name '{prop_name}' is used more than once. Please use unique property names."
                    )
                    return

    def execute(self, parameters, messages):
        """
        The source code of the tool.
        """
        asset_id = parameters[0].valueAsText
        filter_bounds = parameters[3].valueAsText
        geometry_types = parameters[6].valueAsText.split(";")
        out_filename = parameters[7].valueAsText
        load_feat = parameters[8].value

        asset_id = clean_asset_id(asset_id)

        # Get image by label
        fc = ee.FeatureCollection(asset_id)

        # Filter by properties
        if parameters[1].valueAsText:
            arcpy.AddMessage("Filter by properties ...")
            val_list = parameters[1].values
            # Could be multiple filter properties
            for row in val_list:
                prop_name = row[0]
                # property value could be integer, float or string
                try:
                    prop_val = int(row[2])
                except ValueError:
                    try:
                        prop_val = float(row[2])
                    except ValueError:
                        prop_val = row[2]
                operator = row[1]

                # Check if prop_val is a string and format accordingly
                if isinstance(prop_val, str):
                    # If prop_val is a string, wrap it in single quotes
                    filter_condition = "{} {} '{}'".format(
                        prop_name, operator, prop_val
                    )
                else:
                    # If prop_val is an integer or float, no quotes needed
                    filter_condition = "{} {} {}".format(prop_name, operator, prop_val)

                arcpy.AddMessage("Filter by property: " + filter_condition)
                fc = fc.filter(filter_condition)

        # Filter by dates
        if parameters[2].valueAsText:
            arcpy.AddMessage("Filter by dates ...")
            val_list = parameters[2].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
            fc = fc.filterDate(start_date, end_date)

        # Filter by bounds
        if filter_bounds:
            arcpy.AddMessage("Filter by bounds ...")

        if filter_bounds == "Coordinates (Point)":
            if parameters[4].valueAsText:
                val_list = parameters[4].values
                lon = val_list[0][0]
                lat = val_list[0][1]
                fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
        elif filter_bounds == "Map Centroid (Point)":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
            fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
        elif filter_bounds == "Map Extent (Area)":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
            fc = fc.filterBounds(roi)
        elif filter_bounds == "Polygon (Area)":
            if parameters[5].valueAsText:
                # Get input feature coordinates to list
                coords = get_polygon_coords(parameters[5].valueAsText)
                # Create an Earth Engine MultiPolygon from the GeoJSON
                roi = ee.Geometry.MultiPolygon(coords)
                fc = fc.filterBounds(roi)

        # Download feature collection to a temporary GeoJSON
        upper_path = os.path.dirname(arcpy.env.workspace)
        out_json = os.path.join(upper_path, "temp.geojson")

        # Prepare the download URL
        params_dict = {}
        params_dict["filetype"] = "GeoJSON"
        # params_dict["selectors"] = ["geometry"] + parameters[6].valueAsText.split(";")
        params_dict["filename"] = "temp_json"
        download_url = fc.getDownloadURL(**params_dict)

        arcpy.AddMessage("Download URL is: " + download_url)
        arcpy.AddMessage("Downloading to " + out_json + " ...")

        # Download the file to your local machine
        response = requests.get(download_url)
        with open(out_json, "wb") as file:
            file.write(response.content)

        # Convert GeoJSON to feature class
        out_feat_list = []

        for geo in geometry_types:
            out_feat = out_filename + "_" + geo
            out_feat_list.append(out_feat)
            arcpy.AddMessage(f"Converting to {geo} feature class: {out_feat} ...")
            arcpy.conversion.JSONToFeatures(out_json, out_feat, geo.upper())

        # Clean up the temp file
        os.remove(out_json)

        # Add output feature class to map layer
        if load_feat:
            arcpy.AddMessage("Load feature class to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            for out_feat in out_feat_list:
                aprxMap.addDataFromPath(out_feat)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download Feature Collection by Serialized Object in JSON
class DownloadFeatColbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Feature Collection by Serialized Object"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """
        Define the tool parameters.

        """

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="select_geometry",
            displayName="Select the geometry type to download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param1.filter.list = ["Point", "Multipoint", "Polyline", "Polygon"]

        param2 = arcpy.Parameter(
            name="out_feature",
            displayName="Specify the output file name",
            datatype="DEFeatureClass",
            direction="Output",
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="load_feat",
            displayName="Load feature class to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """
        The source code of the tool.
        """
        json_path = parameters[0].valueAsText
        geometry_types = parameters[1].valueAsText.split(";")
        out_filename = parameters[2].valueAsText
        load_feat = parameters[3].value

        # load collection object
        fc = arcgee.data.load_ee_result(json_path)

        # Download feature collection to a temporary GeoJSON
        upper_path = os.path.dirname(arcpy.env.workspace)
        out_json = os.path.join(upper_path, "temp.geojson")

        # Prepare the download URL
        params_dict = {}
        params_dict["filetype"] = "GeoJSON"
        # params_dict["selectors"] = ["geometry"] + parameters[6].valueAsText.split(";")
        params_dict["filename"] = "temp_json"
        download_url = fc.getDownloadURL(**params_dict)

        arcpy.AddMessage("Download URL is: " + download_url)
        arcpy.AddMessage("Downloading to " + out_json + " ...")

        # Download the file to your local machine
        response = requests.get(download_url)
        with open(out_json, "wb") as file:
            file.write(response.content)

        # Convert GeoJSON to feature class
        out_feat_list = []

        for geo in geometry_types:
            out_feat = out_filename + "_" + geo
            out_feat_list.append(out_feat)
            arcpy.AddMessage(f"Converting to {geo} feature class: {out_feat} ...")
            arcpy.conversion.JSONToFeatures(out_json, out_feat, geo.upper())

        # Clean up the temp file
        os.remove(out_json)

        # Add output feature class to map layer
        if load_feat:
            arcpy.AddMessage("Load feature class to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            for out_feat in out_feat_list:
                aprxMap.addDataFromPath(out_feat)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download Image Collection to GIF
class DownloadImgCol2Gif:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image Collection to GIF"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Image collection inputs are optional
        param0 = arcpy.Parameter(
            name="ic_asset_id",
            displayName="Specify the image collection asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param1.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        param1.value = [["2014-03-01", "2014-05-01"]]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="image_number",
            displayName="Specify the number of images in the gif",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param5 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands of the gif (maximum 3)",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param6 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param8 = arcpy.Parameter(
            name="dims",
            displayName="Specify the dimensions of the gif",
            datatype="GPDouble",
            direction="Input",
            parameterType="Required",
        )
        param8.value = 768

        param9 = arcpy.Parameter(
            name="fps",
            displayName="Specify the frames per second of the gif",
            datatype="GPDouble",
            direction="Input",
            parameterType="Required",
        )
        param9.value = 10

        param10 = arcpy.Parameter(
            name="crs",
            displayName="Specify the CRS of the gif",
            datatype="GPString",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param10.value = "EPSG:3857"

        param11 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param12 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param13 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param14 = arcpy.Parameter(
            name="out_gif",
            displayName="Specify the output gif file name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
            param9,
            param10,
            param11,
            param12,
            param13,
            param14,
        ]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:  # use map extent
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:  # use input lat/lon
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Check image list of a given collection asset
        asset_id = parameters[0].valueAsText

        # Get image collection
        if asset_id:
            asset_id = clean_asset_id(asset_id)
            collection = ee.ImageCollection(asset_id)
            has_filter = False
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
                has_filter = True
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)
                has_filter = True

            # Get the total number of images in the collection
            if not parameters[4].valueAsText and has_filter:
                img_num = collection.size().getInfo()
                parameters[4].value = img_num

            # Check the band list of the first selected image, assuming all selected images have the same bands
            # Update only when filter list is empty
            if not parameters[5].filter.list:
                # Get the first select image
                image = collection.first()
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res)) + "--m")
                parameters[5].filter.list = band_res_list

        # Reset band filter list when asset ID changes
        if not asset_id:
            parameters[4].value = None
            parameters[5].filter.list = []

        # Disable input feature if map extent is used
        if parameters[7].value:  # map extent selected
            parameters[6].enabled = False
        else:
            parameters[6].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Multiple images could be selected
        asset_id = parameters[0].valueAsText
        img_num = parameters[4].valueAsText
        band_str = parameters[5].valueAsText
        in_poly = parameters[6].valueAsText
        use_extent = parameters[7].valueAsText
        dims = parameters[8].valueAsText
        fps = parameters[9].valueAsText
        crs = parameters[10].valueAsText
        min_val = parameters[11].valueAsText
        max_val = parameters[12].valueAsText
        palette_str = parameters[13].valueAsText
        out_gif = parameters[14].valueAsText

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:  # use map extent
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:  # use input lat/lon
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Get image collection
        asset_id = clean_asset_id(asset_id)
        collection = ee.ImageCollection(asset_id)
        # Filter image collection as specified
        if lon is not None and lat is not None:
            collection = collection.filterBounds(
                ee.Geometry.Point((float(lon), float(lat)))
            )
        if start_date is not None and end_date is not None:
            collection = collection.filterDate(start_date, end_date)

        # Define animation function parameters
        videoArgs = {}

        # Add bands to videoArgs if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            videoArgs["bands"] = bands_only

        # Add dimensions and frames per second if specified
        if dims:
            videoArgs["dimensions"] = int(dims)
        if fps:
            videoArgs["framesPerSecond"] = int(fps)

        # Add min and max values if specified
        if min_val:
            videoArgs["min"] = float(min_val)
        if max_val:
            videoArgs["max"] = float(max_val)

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            videoArgs["palette"] = palette

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":  # use map view
            xmin, ymin, xmax, ymax = get_map_view_extent()
            bbox = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
            roi = ee.Geometry.Polygon(bbox.coordinates(), None, False)
            # Get the region of interest
            videoArgs["region"] = roi
        # Use input feature layer as ROI
        elif in_poly:
            spatial_ref = arcpy.Describe(in_poly).spatialReference
            poly_prj = spatial_ref.PCSCode
            if poly_prj == 0:
                poly_prj = spatial_ref.GCSCode
            arcpy.AddMessage("Input feature layer projection is " + str(poly_prj))

            # Project input feature to GEE image coordinate system if needed
            target_poly = in_poly
            if str(poly_prj) not in "EPSG:4326":
                arcpy.AddMessage("Projecting input feature layer to EPSG:4326 ...")
                out_sr = arcpy.SpatialReference(4326)
                arcpy.Project_management(in_poly, "poly_temp", out_sr)
                target_poly = "poly_temp"

            # convert input feature to geojson
            arcpy.FeaturesToJSON_conversion(
                target_poly, "temp.geojson", "FORMATTED", "", "", "GEOJSON"
            )

            # Read the GeoJSON file
            upper_path = os.path.dirname(arcpy.env.workspace)
            file_geojson = os.path.join(upper_path, "temp.geojson")
            with open(file_geojson) as f:
                geojson_data = json.load(f)

            # Collect polygon object coordinates
            coords = []
            for feature in geojson_data["features"]:
                coords.append(feature["geometry"]["coordinates"])
            arcpy.AddMessage("Total number of polygon objects: " + str(len(coords)))

            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords, None, False)
            # Delete temporary geojson
            arcpy.management.Delete(file_geojson)
            # Get the region of interest
            videoArgs["region"] = roi
        # Not using any ROI, download entire image
        else:
            # place holder polygon
            roi = ee.Geometry.Polygon(
                [
                    [
                        [-1e-6, -1e-6],
                        [1e-6, -1e-6],
                        [1e-6, 1e-6],
                        [-1e-6, 1e-6],
                        [-1e-6, -1e-6],
                    ]
                ]
            )

        arcpy.AddMessage(f"Region of Interest: {roi.getInfo()}")

        # Use the crs code from the first selected band if not specified
        if not crs:
            crs = collection.first().select(0).projection().getInfo()["crs"]

        arcpy.AddMessage("Image asset projection is " + crs)
        videoArgs["crs"] = crs

        # Make sure output gif file ends with .gif
        if not out_gif.endswith(".gif"):
            out_gif = out_gif + ".gif"

        # Download filtered image collection to GIF
        try:
            arcpy.AddMessage("Generating URL...")
            url = collection.limit(int(img_num)).getVideoThumbURL(videoArgs)

            arcpy.AddMessage(f"Downloading GIF image from {url}\nPlease wait ...")
            r = requests.get(url, stream=True, timeout=300)

            if r.status_code != 200:
                arcpy.AddMessage("An error occurred while downloading.")
                arcpy.AddMessage(r.json()["error"]["message"])
                return
            else:
                with open(out_gif, "wb") as fd:
                    for chunk in r.iter_content(chunk_size=1024):
                        fd.write(chunk)
                arcpy.AddMessage(f"The GIF image has been saved to: {out_gif}")
        except Exception as e:
            arcpy.AddError(e)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download Landsat Timelapse to GIF
class DownloadLandsatTimelapse2Gif:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Landsat Timelapse to GIF"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Required",
        )
        param0.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        param0.value = [["1984-01-01", "2024-12-31"]]

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands of the gif (maximum 3)",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="roi_type",
            displayName="Choose the region of interest type",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2.filter.list = ["Use a polygon", "Use the current map extent"]

        param3 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="dims",
            displayName="Specify the dimensions of the gif",
            datatype="GPDouble",
            direction="Input",
            parameterType="Required",
        )
        param4.value = 768

        param5 = arcpy.Parameter(
            name="fps",
            displayName="Specify the frames per second of the gif",
            datatype="GPDouble",
            direction="Input",
            parameterType="Required",
        )
        param5.value = 5

        param6 = arcpy.Parameter(
            name="crs",
            displayName="Specify the CRS of the gif",
            datatype="GPString",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param6.value = "EPSG:3857"

        param7 = arcpy.Parameter(
            name="out_gif",
            displayName="Specify the output gif file name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param7.filter.list = ["gif"]

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
        ]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        parameters[1].filter.list = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"]

        # Disable input feature if map extent is used
        if (
            parameters[2].valueAsText == "Use the current map extent"
        ):  # map extent selected
            parameters[3].enabled = False
        else:
            parameters[3].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        # User must select a polygon feature layer if "Use a polygon" is selected
        if parameters[2].valueAsText == "Use a polygon":
            if not parameters[3].valueAsText:
                parameters[3].setErrorMessage("Please select a polygon feature layer.")
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Multiple images could be selected
        band_str = parameters[1].valueAsText
        roi_type = parameters[2].valueAsText
        in_poly = parameters[3].valueAsText
        dims = parameters[4].valueAsText
        fps = parameters[5].valueAsText
        crs = parameters[6].valueAsText
        out_gif = parameters[7].valueAsText

        # Get the filter dates
        if parameters[0].valueAsText:
            val_list = parameters[0].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        validate_date(start_date)
        validate_date(end_date)

        # Add bands to videoArgs if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]

        arcpy.AddMessage("Bands selected: " + str(bands_only))

        # Get the region of interests
        # Use map view extent if checked
        if roi_type == "Use the current map extent":  # use map view
            xmin, ymin, xmax, ymax = get_map_view_extent()
            bbox = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
            roi = ee.Geometry.Polygon(bbox.coordinates(), None, False)
        # Use input feature layer as ROI
        else:
            spatial_ref = arcpy.Describe(in_poly).spatialReference
            poly_prj = spatial_ref.PCSCode
            if poly_prj == 0:
                poly_prj = spatial_ref.GCSCode
            arcpy.AddMessage("Input feature layer projection is " + str(poly_prj))

            # Project input feature to GEE image coordinate system if needed
            target_poly = in_poly
            if str(poly_prj) not in "EPSG:4326":
                arcpy.AddMessage("Projecting input feature layer to EPSG:4326 ...")
                out_sr = arcpy.SpatialReference(4326)
                arcpy.Project_management(in_poly, "poly_temp", out_sr)
                target_poly = "poly_temp"

            # convert input feature to geojson
            arcpy.FeaturesToJSON_conversion(
                target_poly, "temp.geojson", "FORMATTED", "", "", "GEOJSON"
            )

            # Read the GeoJSON file
            upper_path = os.path.dirname(arcpy.env.workspace)
            file_geojson = os.path.join(upper_path, "temp.geojson")
            with open(file_geojson) as f:
                geojson_data = json.load(f)

            # Collect polygon object coordinates
            coords = []
            for feature in geojson_data["features"]:
                coords.append(feature["geometry"]["coordinates"])
            arcpy.AddMessage("Total number of polygon objects: " + str(len(coords)))

            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords, None, False)
            # Delete temporary geojson
            arcpy.management.Delete(file_geojson)

        arcpy.AddMessage(f"Region of Interest: {roi.getInfo()}['coordinates']")

        arcpy.AddMessage("Image asset projection is " + crs)

        # Make sure output gif file ends with .gif
        if not out_gif.endswith(".gif"):
            out_gif = out_gif + ".gif"

        arcpy.AddMessage(f"Downloading timelapse to : {out_gif}. Please wait ...")

        landsat_timelapse(
            roi=roi,
            out_gif=out_gif,
            start_year=int(start_date[0:4]) if start_date else None,
            end_year=int(end_date[0:4]) if end_date else None,
            start_date=start_date[5:10],
            end_date=end_date[5:10],
            bands=bands_only if band_str else None,
            vis_params=None,
            dimensions=int(dims) if dims else None,
            frames_per_second=int(fps) if fps else None,
            crs=crs if crs else None,
            apply_fmask=True,
            frequency="year",
        )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Save GEE Asset to Serialized JSON File
class SaveAsset2JSON:
    def __init__(self):
        self.label = "Save Earth Engine Asset to Serialized JSON File"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            displayName="Specify the asset ID",
            name="asset_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        param1 = arcpy.Parameter(
            displayName="Select the type of the Earth Engine asset",
            name="asset_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        param1.filter.list = ["FeatureCollection", "Image", "ImageCollection"]

        param2 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param2.filter.list = ["json"]

        params = [param0, param1, param2]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_id = parameters[0].valueAsText
        data_type = parameters[1].valueAsText
        out_json = parameters[2].valueAsText

        asset_id = clean_asset_id(asset_id)

        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        # Retrieve the Earth Engine object based on the asset ID and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_id)
        elif data_type == "Image":
            ee_object = ee.Image(asset_id)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_id)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Upload Files to Google Cloud Storage and Convert to GEE Asset
class Upload2GCS:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Upload File to Cloud Storage and Convert to Earth Engine Asset"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bucket_name",
            displayName="Select the storage bucket name",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="bucket_folder",
            displayName="Select the folder within the bucket",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="files",
            displayName="Choose a local file to upload",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
            multiValue=True,
        )

        param3.filter.list = ["tif", "shp", "csv", "zip", "tfrecord"]

        param4 = arcpy.Parameter(
            name="upload_asset",
            displayName="Upload the file to Earth Engine",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="asset_type",
            displayName="Choose asset type",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param5.value = "image"
        param5.filter.list = ["image", "table"]

        param6 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )
        param6.value = "Not-in-Use"

        params = [param0, param1, param2, param3, param4, param5, param6]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Get the project ID first
        if parameters[0].valueAsText:
            project_id = parameters[0].valueAsText
            # Initialize a Cloud Storage client, for only once
            if not hasattr(self, "storage_client"):
                self.storage_client = storage.Client(project=project_id)

            # Get the list of all bucket names in this project
            buckets = self.storage_client.list_buckets()
            bucket_names = []
            for bucket in buckets:
                bucket_names.append(bucket.name)

            # Add bucket names to filter list
            parameters[1].filter.list = bucket_names

            # When bucket name is selected, list all available folders
            if parameters[1].valueAsText:
                bucket_name = parameters[1].valueAsText
                parameters[2].filter.list = list_folders_recursive(
                    self.storage_client, bucket_name
                )

        # Enable additional input when uploading to earth engine checked
        if parameters[4].value:
            parameters[5].enabled = True
            parameters[6].enabled = True
            # give a default asset ID when project ID is provided
            if parameters[0].valueAsText and not parameters[6].valueAsText:
                parameters[6].value = (
                    "projects/" + parameters[0].valueAsText + "/assets/"
                )
        else:
            parameters[5].enabled = False
            parameters[6].enabled = False

        # reset input values
        if not parameters[0].valueAsText:
            parameters[1].value = None
            parameters[2].value = None
            parameters[6].value = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        bucket_name = parameters[1].valueAsText
        bucket_folder = parameters[2].valueAsText
        files = parameters[3].valueAsText

        storage_client = storage.Client(project=parameters[0].valueAsText)

        # If user creates a new folder, make sure it ends with /
        if not bucket_folder.endswith("/"):
            bucket_folder = bucket_folder + "/"

        # Get the list of selected files
        # Remove ' in files in case users add it
        if "'" in files:
            files = files.replace("'", "")
        file_list = files.split(";")

        # Upload files to the selected bucket name
        gcs_file_list = []
        for ifile in file_list:
            file_name = os.path.basename(ifile)
            out_file = bucket_folder + file_name
            upload_to_gcs_bucket(storage_client, bucket_name, ifile, out_file)
            gcs_file_list.append(out_file)
            # check file extension
            file_extension = os.path.splitext(file_name)[1]
            # For shape file, need to upload accessary files
            if file_extension == ".shp":
                for extension in [".shx", ".dbf", ".prj", ".cpg"]:
                    upload_to_gcs_bucket(
                        storage_client,
                        bucket_name,
                        ifile.replace(".shp", extension),
                        out_file.replace(".shp", extension),
                    )

        # Upload file to earth engine
        if parameters[4].value:
            asset_type = parameters[5].valueAsText
            asset_id = parameters[6].valueAsText
            is_col = False

            # If more than one file is selected, treat as collection asset
            if len(gcs_file_list) > 1:
                is_col = True
                # use input asset id as folder path
                collection_asset_folder = asset_id
                # for image asset type, create image collection
                if asset_type == "image":
                    if not asset_exists(collection_asset_folder):
                        create_image_collection(collection_asset_folder)
                    else:
                        arcpy.AddMessage("The image collection already exists.")
                # if table, create a folder, all files will be uploaded to this folder
                else:
                    if not asset_exists(collection_asset_folder):
                        create_ee_folder(collection_asset_folder)
                    else:
                        arcpy.AddMessage("The folder already exists.")

            for ifile in gcs_file_list:
                # get file URI (file could be URI or relative path)
                bucket_uri = "gs://" + bucket_name + "/" + ifile
                # check if collection
                if is_col:
                    # upload to collection folder
                    # use file name as item id
                    file_name = os.path.splitext(os.path.basename(bucket_uri))[0]
                    item_id = f"{collection_asset_folder}/{file_name}"
                    gcs_file_to_ee_asset(asset_type, item_id, bucket_uri)
                else:
                    gcs_file_to_ee_asset(asset_type, asset_id, bucket_uri)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Convert GCS File to GEE Asset
class GCSFile2Asset:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Convert Cloud Storage File to Earth Engine Asset"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bucket_name",
            displayName="Select the storage bucket name",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="bucket_folder",
            displayName="Select the folder within the bucket",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="files",
            displayName="Select the file within the folder or specify the gsutil URI",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
            multiValue=True,
        )

        param4 = arcpy.Parameter(
            name="asset_type",
            displayName="Choose the asset type",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param4.value = "image"
        param4.filter.list = ["image", "table"]

        param5 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the asset ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        params = [param0, param1, param2, param3, param4, param5]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        project_id = parameters[0].valueAsText
        # List buckets, folders and files
        if project_id:
            # Initialize a Cloud Storage client, for only once
            if not hasattr(self, "storage_client"):
                self.storage_client = storage.Client(project=project_id)

            # Get the list of all bucket names in this project
            buckets = self.storage_client.list_buckets()
            bucket_names = []
            for bucket in buckets:
                bucket_names.append(bucket.name)
            # Add bucket names to filter list
            parameters[1].filter.list = bucket_names

            # When bucket name is selected, list all available folders
            if parameters[1].valueAsText:
                bucket_name = parameters[1].valueAsText
                parameters[2].filter.list = list_folders_recursive(
                    self.storage_client, bucket_name
                )

            # When both bucket name and folder are selected, list all files
            if parameters[1].valueAsText and parameters[2].valueAsText:
                bucket_name = parameters[1].valueAsText
                folder_name = parameters[2].valueAsText
                # only certain formats are accepted as earth engine asset
                extensions = ("tif", "shp", "csv", "zip", "tfrecord")
                file_list = list_files_in_folder(
                    self.storage_client, bucket_name, folder_name
                )
                parameters[3].filter.list = [
                    file for file in file_list if file.endswith(extensions)
                ]

            # give a default asset path when project ID is provided
            if not parameters[5].valueAsText:
                parameters[5].value = "projects/" + project_id + "/assets/"

        # reset bucket, folder and file lists and values
        if not project_id:
            parameters[1].filter.list = []
            parameters[2].filter.list = []
            parameters[3].filter.list = []
            parameters[1].value = None
            parameters[2].value = None
            parameters[3].value = None
            parameters[5].value = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        if parameters[0].valueAsText:
            if parameters[1].valueAsText:
                if not parameters[2].filter.list:
                    parameters[3].setWarningMessage("No folders found in this bucket.")
            # When both bucket name and folder are selected
            if parameters[1].valueAsText and parameters[2].valueAsText:
                if not parameters[3].filter.list:
                    parameters[3].setWarningMessage("No files found in this folder.")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        project_id = parameters[0].valueAsText
        bucket_name = parameters[1].valueAsText
        files = parameters[3].valueAsText
        asset_type = parameters[4].valueAsText
        asset_id = parameters[5].valueAsText

        # create storage client since self.storage_client can not transfer from updateParameters here
        self.storage_client = storage.Client(project=project_id)

        # Get the list of selected files
        # Remove ' in files in case users add it
        if "'" in files:
            files = files.replace("'", "")
        file_list = files.split(";")

        # If more than one file is selected, treat as collection asset
        is_col = False
        if len(file_list) > 1:
            is_col = True
            # use input asset id as folder path
            collection_asset_folder = asset_id
            # for image asset type, create image collection
            if asset_type == "image":
                if not asset_exists(collection_asset_folder):
                    create_image_collection(collection_asset_folder)
                else:
                    arcpy.AddMessage("The image collection already exists.")
            # if table, create a folder, all files will be uploaded to this folder
            else:
                if not asset_exists(collection_asset_folder):
                    create_ee_folder(collection_asset_folder)
                else:
                    arcpy.AddMessage("The folder already exists.")

        for ifile in file_list:
            # get file URI (file could be URI or relative path)
            if "gs://" not in ifile:
                bucket_uri = "gs://" + bucket_name + "/" + ifile
            else:
                bucket_uri = ifile
            # check if collection
            if is_col:
                # upload to collection folder
                # use file name as item id
                file_name = os.path.splitext(os.path.basename(bucket_uri))[0]
                item_id = f"{collection_asset_folder}/{file_name}"
                gcs_file_to_ee_asset(asset_type, item_id, bucket_uri)
            else:
                gcs_file_to_ee_asset(asset_type, asset_id, bucket_uri)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


""" Data Processing Tools """


# Apply Filters to Collection Dataset by Asset ID
class ApplyFilterbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Filters to Collection Dataset by Asset ID"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the type of the dataset to be filtered",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the asset ID of the dataset",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="filter_list",
            displayName="Specify the filters",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )
        param2.columns = [
            ["GPString", "Filters"],
            ["GPString", "Arguments"],
        ]
        filters = get_filter_list()
        param2.filters[0].list = filters

        param3 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the serialized object",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param3.filter.list = ["json"]

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        data_type = parameters[0].valueAsText
        asset_id = parameters[1].valueAsText
        filters = parameters[2].values
        out_json = parameters[3].valueAsText

        # Retrieve the Earth Engine object based on the asset id and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_id)
        elif data_type == "Image":
            ee_object = ee.Image(asset_id)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_id)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Apply the filters from the filter list to the Earth Engine object
        for filter_item in filters:
            filter_type = filter_item[0]
            filter_arg = filter_item[1]

            # Construct a command string based on the filter type
            command_string = f"{filter_type}({filter_arg})"
            arcpy.AddMessage(f"Applying filter: {command_string}")
            constructed_filter = eval(command_string)
            ee_object = ee_object.filter(constructed_filter)

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        # save to json file
        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Apply Filters to Collection Dataset by Serialized JSON Object
class ApplyFilterbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Filters to Collection Dataset by Serialized Object"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="filter_list",
            displayName="Specify the filters",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )
        param1.columns = [
            ["GPString", "Filters"],
            ["GPString", "Arguments"],
        ]
        filters = get_filter_list()
        param1.filters[0].list = filters

        param2 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the serialized object",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param2.filter.list = ["json"]

        params = [param0, param1, param2]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        json_path = parameters[0].valueAsText
        filters = parameters[1].values
        out_json = parameters[2].valueAsText

        # load collection object
        ee_object = arcgee.data.load_ee_result(json_path)

        # Apply the filters from the filter list to the Earth Engine object
        for filter_item in filters:
            filter_type = filter_item[0]
            filter_arg = filter_item[1]

            # Construct a command string based on the filter type
            command_string = f"{filter_type}({filter_arg})"
            arcpy.AddMessage(f"Applying filter: {command_string}")
            constructed_filter = eval(command_string)
            ee_object = ee_object.filter(constructed_filter)

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        # save to json
        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Apply Map Functions to Collection Dataset by ID
class ApplyMapFunctionbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Map Functions to Collection Dataset by Asset ID"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the type of the dataset to be filtered",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the asset id of the dataset",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="map_file",
            displayName="Select the Python script that contains map functions",
            datatype="DEFile",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )
        param2.filter.list = ["py"]

        param3 = arcpy.Parameter(
            name="map_functions",
            displayName="Select the map functions to apply",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param4 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the serialized object",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param4.filter.list = ["json"]

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        import importlib

        # When the map function file is selected
        if parameters[2].valueAsText:
            # get the file name of input map function file
            file_path = parameters[2].valueAsText
            map_lib = os.path.splitext(os.path.basename(file_path))[0]
            module = importlib.import_module(map_lib)

            function_list = list_functions_from_script(module)
            parameters[3].filter.list = function_list

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import importlib

        # Read input parameters
        data_type = parameters[0].valueAsText
        asset_id = parameters[1].valueAsText
        map_file = parameters[2].valueAsText
        map_functions = parameters[3].valueAsText
        out_json = parameters[4].valueAsText

        # get list of map functions
        if "'" in map_functions:
            map_functions = map_functions.replace("'", "")
        function_list = map_functions.split(";")

        # import module first
        map_lib = os.path.splitext(os.path.basename(map_file))[0]
        module = importlib.import_module(map_lib)

        # Retrieve the Earth Engine object based on the asset id and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_id)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_id)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Apply the filters from the filter list to the Earth Engine object
        for func_str in function_list:
            arcpy.AddMessage(f"Applying map function: {func_str}")
            function_to_call = getattr(module, func_str)
            ee_object = ee_object.map(function_to_call)

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        # save to json
        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Apply Map Functions to Collection Dataset by Serialized JSON Object
class ApplyMapFunctionbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Map Functions to Collection Dataset by Serialized Object"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the type of the dataset to be loaded",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param1.filter.list = ["json"]

        param2 = arcpy.Parameter(
            name="map_file",
            displayName="Select the Python script that contains map functions",
            datatype="DEFile",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )
        param2.filter.list = ["py"]

        param3 = arcpy.Parameter(
            name="map_functions",
            displayName="Select the map functions to apply",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param4 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the serialized object",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param4.filter.list = ["json"]

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        import importlib

        # When the map function file is selected
        if parameters[2].valueAsText:
            # get the file name of input map function file
            file_path = parameters[2].valueAsText
            map_lib = os.path.splitext(os.path.basename(file_path))[0]
            module = importlib.import_module(map_lib)

            function_list = list_functions_from_script(module)
            parameters[3].filter.list = function_list

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import importlib

        # Read input parameters
        data_type = parameters[0].valueAsText
        json_path = parameters[1].valueAsText
        map_file = parameters[2].valueAsText
        map_functions = parameters[3].valueAsText
        out_json = parameters[4].valueAsText

        # get list of map functions
        if "'" in map_functions:
            map_functions = map_functions.replace("'", "")
        function_list = map_functions.split(";")

        # import module first
        map_lib = os.path.splitext(os.path.basename(map_file))[0]
        module = importlib.import_module(map_lib)

        # load collection object
        ee_object = arcgee.data.load_ee_result(json_path)

        #  Re-cast the object to target data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(ee_object)
        elif data_type == "ImageCollection":

            ee_object = ee.ImageCollection(ee_object)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        asset_id = ee_object.getInfo()["id"]
        arcpy.AddMessage(f"Asset ID: {asset_id}")

        # Apply the filters from the filter list to the Earth Engine object
        for func_str in function_list:
            arcpy.AddMessage(f"Applying map function: {func_str}")
            function_to_call = getattr(module, func_str)
            ee_object = ee_object.map(function_to_call)

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        # save to json
        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Apply Reducers to GEE dataset by Asset ID
class ApplyReducerbyID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Reducers to Earth Engine Dataset by Asset ID"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the dataset type to be reduced",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "Image", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="reduction_method",
            displayName="Choose the reduction method",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="reduction_args",
            displayName="Specify the arguments of the reduction method",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify the asset ID of the dataset",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param4 = arcpy.Parameter(
            name="filter_list",
            displayName="Specify the filters",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )
        param4.columns = [
            ["GPString", "Filters"],
            ["GPString", "Arguments"],
        ]

        filters = get_filter_list()
        param4.filters[0].list = filters

        param5 = arcpy.Parameter(
            name="reducer_list",
            displayName="Specify the reducers",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )
        param5.columns = [
            ["GPString", "Reducers"],
            ["GPString", "Arguments"],
        ]

        reducers = get_reducer_list()
        param5.filters[0].list = reducers

        param6 = arcpy.Parameter(
            name="shared_inputs",
            displayName="Use the same inputs for all reducers",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the serialized object",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param7.filter.list = ["json"]

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        data_type = parameters[0].valueAsText
        if data_type == "FeatureCollection":
            parameters[1].filter.list = ["reduceColumns", "reduceToImage"]
        elif data_type == "Image":
            parameters[1].filter.list = [
                "reduce",
                "reduceConnectedComponents",
                "reduceNeighborhood",
                "reduceRegion",
                "reduceRegions",
                "reduceResolution",
                "reduceToVectors",
            ]
        elif data_type == "ImageCollection":
            parameters[1].filter.list = ["reduce", "reduceColumns", "reduceToImage"]
        else:
            parameters[1].filter.list = []

        # when multiple reducers are selected, the shared inputs parameter is enabled
        reducers = parameters[5].values
        if reducers and len(reducers) > 1:
            parameters[6].enabled = True
        else:
            parameters[6].enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        data_type = parameters[0].valueAsText
        reduction_method = parameters[1].valueAsText
        reduction_args = parameters[2].valueAsText
        asset_id = parameters[3].valueAsText
        filters = parameters[4].values
        reducers = parameters[5].values
        shared_inputs = parameters[6].value
        out_json = parameters[7].valueAsText

        asset_id = clean_asset_id(asset_id)

        # Retrieve the Earth Engine object based on the asset id and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_id)
        elif data_type == "Image":
            ee_object = ee.Image(asset_id)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_id)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Apply the filters from the filter list to the Earth Engine object
        for filter_item in filters:
            filter_type = filter_item[0]
            filter_arg = filter_item[1]

            # Construct a command string based on the filter type
            command_string = f"{filter_type}({filter_arg})"
            arcpy.AddMessage(f"Applying filter: {command_string}")
            constructed_filter = eval(command_string)
            ee_object = ee_object.filter(constructed_filter)

        # Construct all reducers first
        # Multiple reducers will be treated as combined reducer
        reducer_list = []
        for reducer_item in reducers:

            reducer_name = reducer_item[0]
            reducer_arg = reducer_item[1]

            # Construct a command string based on the reducer
            command_string = f"{reducer_name}({reducer_arg})"
            arcpy.AddMessage(f"Constructing reducer: {command_string}")
            constructed_reducer = eval(command_string)
            reducer_list.append(constructed_reducer)

        # Combine reducers if more than one
        if len(reducer_list) > 1:
            final_reducer = reducer_list[0]
            for reducer in reducer_list[1:]:
                final_reducer = final_reducer.combine(
                    reducer2=reducer, sharedInputs=shared_inputs
                )
            arcpy.AddMessage("Combined multiple reducers")
        else:

            final_reducer = reducer_list[0]

        # Apply the final reducer
        arcpy.AddMessage(f"Applying reduction method:{data_type}'.'{reduction_method}")
        ee_method = getattr(ee_object, reduction_method)
        if reduction_args:
            # Convert the string arguments into a dictionary of kwargs
            kwargs = {}
            for arg in reduction_args.split(","):
                key, value = arg.strip().split("=")
                # Convert string values to appropriate Python types
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.startswith("'") or value.startswith('"'):
                    value = value.strip("'\"")
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        # If not a number, treat as a variable name
                        value = eval(value)
                kwargs[key] = value

            # Pass reducer and parsed kwargs to the method
            ee_object = ee_method(reducer=final_reducer, **kwargs)
        else:
            ee_object = ee_method(reducer=final_reducer)

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):

            out_json = out_json + ".json"

        # save to json
        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Apply Reducers to GEE dataset by Serialized JSON Object
class ApplyReducerbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Reducers to Earth Engine Dataset by Serialized Object"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the dataset type to be reduced",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "Image", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="reduction_method",
            displayName="Choose the reduction method",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="reduction_args",
            displayName="Specify the arguments of the reduction method",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="json_path",
            displayName="Specify the path to the serialized JSON object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        param3.filter.list = ["json"]

        param4 = arcpy.Parameter(
            name="reducer_list",
            displayName="Specify the reducers",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )
        param4.columns = [
            ["GPString", "Reducers"],
            ["GPString", "Arguments"],
        ]

        reducers = get_reducer_list()
        param4.filters[0].list = reducers

        param5 = arcpy.Parameter(
            name="shared_inputs",
            displayName="Use the same inputs for all reducers",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the serialized object",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param6.filter.list = ["json"]

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        data_type = parameters[0].valueAsText
        if data_type == "FeatureCollection":
            parameters[1].filter.list = ["reduceColumns", "reduceToImage"]
        elif data_type == "Image":
            parameters[1].filter.list = [
                "reduce",
                "reduceConnectedComponents",
                "reduceNeighborhood",
                "reduceRegion",
                "reduceRegions",
                "reduceResolution",
                "reduceToVectors",
            ]
        elif data_type == "ImageCollection":
            parameters[1].filter.list = ["reduce", "reduceColumns", "reduceToImage"]
        else:
            parameters[1].filter.list = []

        # when multiple reducers are selected, the shared inputs parameter is enabled
        reducers = parameters[4].values
        if reducers and len(reducers) > 1:
            parameters[5].enabled = True
        else:
            parameters[5].enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        data_type = parameters[0].valueAsText
        reduction_method = parameters[1].valueAsText
        reduction_args = parameters[2].valueAsText
        json_path = parameters[3].valueAsText
        reducers = parameters[4].values
        shared_inputs = parameters[5].value
        out_json = parameters[6].valueAsText

        ee_object = arcgee.data.load_ee_result(json_path)

        # Retrieve the Earth Engine object based on the asset id and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(ee_object)
        elif data_type == "Image":
            ee_object = ee.Image(ee_object)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(ee_object)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Construct all reducers first
        # Multiple reducers will be treated as combined reducer
        reducer_list = []
        for reducer_item in reducers:

            reducer_name = reducer_item[0]
            reducer_arg = reducer_item[1]

            # Construct a command string based on the reducer
            command_string = f"{reducer_name}({reducer_arg})"
            arcpy.AddMessage(f"Constructing reducer: {command_string}")
            constructed_reducer = eval(command_string)
            reducer_list.append(constructed_reducer)

        # Combine reducers if more than one
        if len(reducer_list) > 1:
            final_reducer = reducer_list[0]
            for reducer in reducer_list[1:]:
                final_reducer = final_reducer.combine(
                    reducer2=reducer, sharedInputs=shared_inputs
                )
            arcpy.AddMessage("Combined multiple reducers")
        else:

            final_reducer = reducer_list[0]

        # Apply the final reducer
        arcpy.AddMessage(f"Applying reduction method:{data_type}'.'{reduction_method}")
        ee_method = getattr(ee_object, reduction_method)
        if reduction_args:
            # Convert the string arguments into a dictionary of kwargs
            kwargs = {}
            for arg in reduction_args.split(","):
                key, value = arg.strip().split("=")
                # Convert string values to appropriate Python types
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.startswith("'") or value.startswith('"'):
                    value = value.strip("'\"")
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        # If not a number, treat as a variable name
                        value = eval(value)
                kwargs[key] = value

            # Pass reducer and parsed kwargs to the method
            ee_object = ee_method(reducer=final_reducer, **kwargs)
        else:
            ee_object = ee_method(reducer=final_reducer)

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):

            out_json = out_json + ".json"

        # save to json
        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Run User-Provided Python Script
class RunPythonScript:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Run User-Provided Python Script"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="py_script",
            displayName="Choose the python script to run",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["py"]

        params = [param0]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import subprocess

        # Read input parameters
        py_script = parameters[0].valueAsText

        # Run the script as an external process
        subprocess.run(["python", py_script])

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
