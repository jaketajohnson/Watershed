"""
 SYNOPSIS

     Watershed/Extent

 DESCRIPTION

    * Processes the raw DTM from the Illinois Height Modernization Program (IHMP)
    * Splits the DTM into tiles coinciding with PLSS Quarter Sections

 REQUIREMENTS

     Python 3
     arcpy
     natsort
 """

import arcpy
import logging
import os
import sys
import traceback


def ScriptLogging():
    """Enables console and log file logging; see test script for comments on functionality"""
    current_directory = os.getcwd()
    script_filename = os.path.basename(sys.argv[0])
    log_filename = os.path.splitext(script_filename)[0]
    log_file = os.path.join(current_directory, f"{log_filename}.log")
    if not os.path.exists(log_file):
        with open(log_file, "w"):
            pass
    message_formatting = "%(asctime)s - %(levelname)s - %(message)s"
    date_formatting = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=message_formatting, datefmt=date_formatting)
    logging_output = logging.getLogger(f"{log_filename}")
    logging_output.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logging_output.addHandler(console_handler)
    logging.basicConfig(format=message_formatting, datefmt=date_formatting, filename=log_file, filemode="w", level=logging.INFO)
    return logging_output


def Extent():
    """Splits the DTM into PLSS Quarter Sections"""

    # Logging
    def logging_lines(name):
        """Use this wrapper to insert a message before and after the function for logging purposes"""
        if type(name) == str:
            def logging_decorator(function):
                def logging_wrapper():
                    logger.info(f"{name} Start")
                    function()
                    logger.info(f"{name} Complete")
                return logging_wrapper
            return logging_decorator
    logger = ScriptLogging()
    logger.info("Script Execution Start")

    # DTM Folders
    directory = r"C:\Users\jtjohnson\Documents\Python\DEM"
    dtm = os.path.join(directory, "DTM")
    dtm_split = os.path.join(directory, "DTM_Split")

    # PLSS Quarter Sections
    sde = r"C:\Users\jtjohnson\AppData\Roaming\ESRI\ArcGISPro\Favorites\OS@imSPFLD-Version.sde"
    cadastral_reference = os.path.join(sde, "imSPFLD.COSPW.CadastralReference")
    quarter_sections = os.path.join(cadastral_reference, "imSPFLD.COSPW.PLSSQuarterSection")
    arcpy.MakeFeatureLayer_management(quarter_sections, "QuarterSections", "SEWMAPOLD <> ''")

    @logging_lines("Delete")
    def RasterDelete():
        """Delete the current rasters in the output folder"""
        if len(os.listdir(dtm_split)) > 0:
            for file in os.listdir(dtm_split):
                os.remove(os.path.join(dtm_split, f"{file}"))

    @logging_lines("Split")
    def RasterSplit():
        """Split the DTM into manageable cell sizes and limit it to a certain extent rather than the entire county"""
        arcpy.SplitRaster_management(dtm, dtm_split, "dtm_split_", "POLYGON_FEATURES", overlap=1, clip_type="FEATURE_CLASS", split_polygon_feature_class="QuarterSections", template_extent="QuarterSections")

        # Log the number of cells
        arcpy.env.workspace = dtm_split
        count = len(arcpy.ListRasters())
        logger.info(f"Raster has {count} cells")

    # Try running above scripts
    try:
        RasterDelete()
        RasterSplit()
    except (IOError, KeyError, NameError, IndexError, TypeError, UnboundLocalError, ValueError):
        traceback_info = traceback.format_exc()
        try:
            logger.info(traceback_info)
        except NameError:
            print(traceback_info)
    except arcpy.ExecuteError:
        try:
            logger.error(arcpy.GetMessages(2))
        except NameError:
            print(arcpy.GetMessages(2))
    except:
        logger.exception("Picked up an exception!")
    finally:
        try:
            logger.info("Script Execution Complete")
        except NameError:
            pass


if __name__ == '__main__':
    Extent()
