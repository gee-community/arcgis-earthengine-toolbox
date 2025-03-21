# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import ee
import ujson
import arcpy
import google.auth
import xarray
import datetime
import os
import requests
import numpy as np
import json

# Import version from parent package
# from arcgee import __version__

__version__ = "0.1.1"


def get_version_info():
    """
    Returns version information about the GEE Connector.

    Returns:
        str: A formatted string with version information
    """
    return f"GEE Connector v{__version__}"


def auth(project=None):
    credentials, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/earthengine",
        ]
    )
    ee.Initialize(
        credentials.with_quota_project(None),
        project=project,
    )

    return


def save_ee_result(ee_object, path):

    serialized_obj = ee_object.serialize()

    with open(path, "w") as f:
        ujson.dump(serialized_obj, f)

    return


def load_ee_result(path):
    """
    Loads a serialized Earth Engine object from a JSON file and deserializes it.

    Args:
        path (str): The file path to the JSON file.

    Returns:
        ee.ComputedObject: The deserialized Earth Engine object.

    Raises:
        RuntimeError: If deserialization fails.
    """
    try:
        with open(path, "r") as f:
            ee_object = ujson.load(f)

        # Attempt to deserialize the Earth Engine object
        return ee.deserializer.fromJSON(ee_object)

    except Exception as e:
        # Log an error message and raise a RuntimeError
        error_message = (
            f"Failed to deserialize the Earth Engine object from {path}: {str(e)}"
        )
        raise RuntimeError(error_message) from e


def get_reducer_list():
    """
    Get the complete list of available reducers from ee.Reducer.

    Returns:
        list: A list of all reducer names available in ee.Reducer, including reducers for:
            - Statistical operations (mean, median, mode, etc.)
            - Counting operations (count, countDistinct, etc.)
            - Correlation measures (pearsonsCorrelation, spearmansCorrelation, etc.)
            - Distribution analysis (histogram, kurtosis, etc.)
            - And more

    Notes:
        This reducer list contains all reducers from ee.Reducer that can be used to
        reduce collections and compute statistics on Earth Engine data.
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


# convert coordinates to bounding box values
def convert_coords_to_bbox(coords):
    """Convert coordinates to bounding box values.

    Args:
        coords (list): List of coordinates

    Returns:
        tuple: (x_min, y_min, x_max, y_max)
    """
    bottom_left = coords[0]
    top_right = coords[2]
    x_min = bottom_left[0]
    y_min = bottom_left[1]
    x_max = top_right[0]
    y_max = top_right[1]

    return x_min, y_min, x_max, y_max


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
