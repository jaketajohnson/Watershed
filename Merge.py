"""
 SYNOPSIS

     Watershed/Merge

 DESCRIPTION

    * Merges the final datasets into one citywide layer
        1. ContoursLines
        2. ContoursPolygons
        3. Streams
    * Merged layers names end with "Merged"

 REQUIREMENTS

     Python 3
     arcpy
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


def Merge():
    """Merges final datasets"""

    # Logging
    def logging_lines(name):
        """Use this wrapper to insert a message before and after the function for logging purposes"""
        if type(name) == str:
            def logging_decorator(function):
                def logging_wrapper(*args, **kwargs):
                    logger.info(f"{name} Start")
                    function(*args, **kwargs)
                    logger.info(f"{name} Complete")
                return logging_wrapper
            return logging_decorator
    logger = ScriptLogging()
    logger.info("Script Execution Start")

    # DTM Folder
    directory = r"C:\Users\jtjohnson\Documents\Python\DEM"

    # Final dataset paths
    watershed = os.path.join(directory, "Watershed.gdb")
    contours_lines_final = os.path.join(watershed, "ContoursLines")
    contours_lines_merged = os.path.join(contours_lines_final, "ContoursLinesMerged")
    contours_polygons_final = os.path.join(watershed, "ContoursPolygons")
    contours_polygons_merged = os.path.join(contours_polygons_final, "ContoursPolygonsMerged")
    streams_final = os.path.join(watershed, "Streams")
    streams_merged = os.path.join(streams_final, "StreamsMerged")

    # Environments
    arcpy.env.overwriteOutput = True

    @logging_lines("Merge All")
    def MergeAll(input_dataset, output_merged):
        """Take input and merge into output"""
        logger.info(f"{input_dataset} Start")
        arcpy.env.workspace = input_dataset
        features_to_merge = arcpy.ListFeatureClasses()
        merged_to_remove = os.path.basename(output_merged)
        features_to_merge.remove(merged_to_remove)
        arcpy.Merge_management(features_to_merge, output_merged)
        logger.info(f"{output_merged} Complete")

    # Try running above scripts
    try:
        MergeAll(contours_lines_final, contours_lines_merged)
        MergeAll(streams_final, streams_merged)
        MergeAll(contours_polygons_final, contours_polygons_merged)
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
    Merge()
