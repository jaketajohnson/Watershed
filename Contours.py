"""
 SYNOPSIS

     Watershed/Contours

 DESCRIPTION

    * Contours each segment into contour lines and polygons
    * Processes each resulting contour to improve visuals
    * Merge the contours into one final raster

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
from natsort import natsorted


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


def Contouring():
    """Performs all the functions necessary to take a raw DTM and build contours from it"""

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

    # DTM Folders
    directory = r"C:\Users\jtjohnson\Documents\Python\DEM"
    dtm_split = os.path.join(directory, "DTM_Split")

    # Intermediate contours
    watershed_intermediate = os.path.join(directory, "WatershedIntermediate.gdb")
    contours_lines = os.path.join(watershed_intermediate, "ContoursLines")
    contours_lines_simplified = os.path.join(watershed_intermediate, "ContoursLinesSimplified")
    contours_lines_smoothed = os.path.join(watershed_intermediate, "ContoursLinesSmoothed")
    contours_polygons = os.path.join(watershed_intermediate, "ContoursPolygons")

    # Final contours
    watershed = os.path.join(directory, "Watershed.gdb")
    contours_lines_final = os.path.join(watershed, "ContoursLines")
    contours_polygons_final = os.path.join(watershed, "ContoursPolygons")

    # Quarter Sections
    sde = r"C:\Users\jtjohnson\AppData\Roaming\ESRI\ArcGISPro\Favorites\OS@imSPFLD-Version.sde"
    cadastral_reference = os.path.join(sde, "imSPFLD.COSPW.CadastralReference")
    quarter_sections = os.path.join(cadastral_reference, "imSPFLD.COSPW.PLSSQuarterSection")
    arcpy.MakeFeatureLayer_management(quarter_sections, "QuarterSections", "SEWMAPOLD <> ''")

    # Environments
    arcpy.env.overwriteOutput = True

    def FeatureProcessor(input_dataset, output_dataset, function_key, feature=True, start_point=0):
        """Template function for the various raster processing functions needed"""
        logger.info(f"{function_key.capitalize()} Start")

        # Check to see if the input key is correct
        allowed_folders = [dtm_split, contours_lines, contours_lines_simplified, contours_lines_smoothed, contours_polygons]
        allowed_keys = ["contours_lines", "contours_lines_simplified", "contours_lines_smoothed", "contours_polygons"]

        if (function_key in allowed_keys) and (input_dataset in allowed_folders) and (output_dataset in allowed_folders):

            # Create a list of rasters to use as an input for the process
            arcpy.env.workspace = input_dataset
            if feature:
                feature_list = natsorted(arcpy.ListFeatureClasses())[start_point:]
            elif not feature:
                feature_list = natsorted(arcpy.ListRasters(raster_type="TIF"))[start_point:]
            else:
                raise ValueError("Incorrect input format (must be feature or TIF")

            # Dictionary of each desired process containing a dictionary of the function and if it needs to be save
            function_dictionary = {
                "contours_lines": lambda feature_input, feature_output: arcpy.sa.Contour(feature_input, feature_output, 1, 564, max_vertices_per_feature=1000000),
                "contours_lines_simplified": lambda feature_input, feature_output: arcpy.SimplifyLine_cartography(feature_input, feature_output, "POINT_REMOVE", 5, "RESOLVE_ERRORS", "NO_KEEP"),
                "contours_lines_smoothed": lambda feature_input, feature_output: arcpy.SmoothLine_cartography(feature_input, feature_output, "PAEK", 5, error_option="RESOLVE_ERRORS"),
                "contours_polygons": lambda feature_input, feature_output: arcpy.sa.Contour(feature_input, feature_output, 3, 564, contour_type="CONTOUR_POLYGON", max_vertices_per_feature=1000000)
            }
            dictionary_key = function_dictionary[f"{function_key}"]

            # Run the lambda function using the given function key(s)
            for feature in feature_list:

                # Name variables based on current iterator value
                input_name = os.path.join(input_dataset, feature)
                current_filename = fr"{function_key}_{start_point:03}"
                output_name = os.path.join(output_dataset, current_filename)

                # Run the function
                while 0 <= start_point <= (len(feature_list) - 1):
                    logger.info(f"{current_filename} Start")
                    if function_key == "contours_lines_simplified":
                        selected_contours = arcpy.SelectLayerByAttribute_management(input_name, "NEW_SELECTION", "Shape_Length > 350")
                        dictionary_key(selected_contours, output_name)
                    else:
                        dictionary_key(input_name, output_name)
                start_point += 1
                logger.info(f"{current_filename} Complete")

            logger.info(f"{function_key.capitalize()} Complete")
        else:
            raise ValueError("Incorrect input parameters")

    @logging_lines("RenameMove")
    def RenameMove(input_dataset, output_dataset, function_key, start_point=0):
        """Take the final dataset and rename each feature using the parent quarter section for easy navigation"""
        logger.info(f"{function_key.capitalize()} Start")

        # Environment
        arcpy.env.workspace = input_dataset
        features_to_rename = natsorted(arcpy.ListFeatureClasses()[start_point:])

        if function_key == "contours_lines":
            name_prefix = "CL"
        elif function_key == "contours_polygons":
            name_prefix = "CP"
        else:
            raise NameError("Incorrect function key")

        # Select the intersecting quarter section
        for feature in features_to_rename:
            logger.info(f"{feature} Start")
            selected_quarter_section = arcpy.SelectLayerByLocation_management("QuarterSections", "COMPLETELY_CONTAINS", feature)

            # Assign a new name using the quarter section SEWMAP field
            with arcpy.da.SearchCursor(selected_quarter_section, "SEWMAP") as cursor:
                for row in cursor:
                    quarter_section_name = row[0].replace("-", "")
                    name = f"{name_prefix}_{quarter_section_name}"
                    input_path = os.path.join(input_dataset, feature)
                    arcpy.FeatureClassToFeatureClass_conversion(input_path, output_dataset, name, "Shape_Length > 250")
                    logger.info(f"{name} Complete")
        logger.info(f"{function_key.capitalize()} Complete")

    # Try running above scripts
    try:
        FeatureProcessor(dtm_split, contours_lines, "contours_lines", False)
        FeatureProcessor(contours_lines, contours_lines_simplified, "contours_lines_simplified")
        FeatureProcessor(contours_lines_simplified, contours_lines_smoothed, "contours_lines_smoothed")
        FeatureProcessor(dtm_split, contours_polygons, "contours_polygons", False)
        RenameMove(contours_lines_smoothed, contours_lines_final, "contours_lines")
        RenameMove(contours_polygons, contours_polygons_final, "contours_polygons")
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
    Contouring()
