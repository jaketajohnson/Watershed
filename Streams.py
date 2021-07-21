"""
 SYNOPSIS

     Watershed/Stream

 DESCRIPTION

    * Uses the split DTMs to create a stream order collection of the City
    * Creates a lot of intermediate data

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


def Streams():

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

    # DEMs
    directory = r"C:\Users\jtjohnson\Documents\Python\DEM"
    dtm_split = os.path.join(directory, "DTM_Split")

    # Folders
    streams_folder = os.path.join(directory, "Streams")
    fill_folder = os.path.join(streams_folder, "Fill")
    direction_folder = os.path.join(streams_folder, "Direction")
    direction_merged = os.path.join(direction_folder, "direction_all.TIF")
    order_folder = os.path.join(streams_folder, "Order")
    condition_folder = os.path.join(streams_folder, "Condition")

    # Intermediate streams
    watershed_intermediate = os.path.join(directory, "WatershedIntermediate.gdb")
    streams_intermediate = os.path.join(watershed_intermediate, "Streams")

    # Final streams
    watershed = os.path.join(directory, "Watershed.gdb")
    streams_final = os.path.join(watershed, "Streams")

    # Quarter Sections
    sde = r"C:\Users\jtjohnson\AppData\Roaming\ESRI\ArcGISPro\Favorites\OS@imSPFLD-Version.sde"
    cadastral_reference = os.path.join(sde, "imSPFLD.COSPW.CadastralReference")
    quarter_sections = os.path.join(cadastral_reference, "imSPFLD.COSPW.PLSSQuarterSection")
    arcpy.MakeFeatureLayer_management(quarter_sections, "QuarterSections", "SEWMAPOLD <> ''")

    # Environments
    arcpy.env.overwriteOutput = True

    def RasterProcessor(input_folder, output_folder, function_key, raster_format="folder", start_point=0):
        """Template function for the various raster processing functions needed"""
        logger.info(f"{function_key.capitalize()} Start")

        # Check to see if the input key is correct
        allowed_folders = [dtm_split, fill_folder, direction_folder, order_folder, condition_folder, streams_intermediate, streams_final]
        allowed_keys = ["fill", "direction", "condition", "streams"]
        allowed_raster_formats = ["TIF", "folder"]

        if (function_key in allowed_keys) and (input_folder in allowed_folders) and (output_folder in allowed_folders) and (raster_format in allowed_raster_formats):

            # Create a list of rasters to use as an input for the process
            arcpy.env.workspace = input_folder
            if raster_format == "folder":
                raster_list = natsorted(arcpy.ListRasters())[start_point:]
            else:
                raster_list = natsorted(arcpy.ListRasters(raster_type=raster_format))[start_point:]

            # Dictionary of each desired process containing a dictionary of the function and if it needs to be save
            function_dictionary = {
                "fill": {"function": lambda input_raster: arcpy.sa.Fill(input_raster), "save": True},
                "direction": {"function": lambda input_raster: arcpy.sa.FlowDirection(input_raster, flow_direction_type="D8"), "save": True},
                "condition": {"function": lambda input_raster: arcpy.sa.Con(input_raster, input_raster, "", "Value >= 5"), "save": True},
                "streams": {"function": lambda input_raster, direction_raster, output_raster: arcpy.sa.StreamToFeature(input_raster, direction_merged, output_raster), "save": False}
            }
            dictionary_key = function_dictionary[f"{function_key}"]

            # Run the lambda function using the given function key(s)
            for raster in raster_list:

                # Name variables based on current iterator value
                input_name = os.path.join(input_folder, raster)
                arcpy.env.extent = input_name
                if function_key == "streams":
                    current_filename = fr"{function_key}_all"
                else:
                    current_filename = fr"{function_key}_{start_point:03}"
                direction_name = os.path.join(direction_folder, f"direction_{start_point:03}")
                output_name = os.path.join(output_folder, current_filename)

                # Run the function
                while 0 <= start_point <= (len(raster_list) - 1):
                    if dictionary_key["save"]:
                        raster_function_object = dictionary_key["function"](input_name)
                        raster_function_object.save(output_name)
                    elif not dictionary_key["save"]:
                        dictionary_key["function"](input_name, direction_name, output_name)
                    else:
                        raise ValueError("Incorrect save key")
                logger.info(f"{current_filename} Complete")
                start_point += 1

            logger.info(f"{function_key.capitalize()} Complete")
        else:
            raise ValueError("Incorrect parameters")

    @logging_lines("Order")
    def Order():
        """Merges direction rasters into one then runs Stream Order for the entire extent"""

        # Create a list of direction rasters then merge them
        arcpy.env.workspace = direction_folder
        raster_list = natsorted(arcpy.ListRasters())

        logger.info("Raster Merging Start")
        if "direction_all.tif" in raster_list:
            raster_list.remove("direction_all.tif")
        arcpy.MosaicToNewRaster_management(raster_list, direction_folder, "direction_all.tif", number_of_bands=1)
        logger.info("Raster Merging Complete")

        # Stream order
        logger.info("Stream Ordering Start")
        output_folder = os.path.join(order_folder, "order")
        direction_name = os.path.join(direction_folder, f"direction_all.tif")
        output_raster = arcpy.sa.StreamOrder(direction_name, direction_name)
        output_raster.save(output_folder)
        logger.info("Stream Ordering Complete")

    @logging_lines("SplitRename")
    def SplitRename():
        """Split the citywide streams_all feature into PLSS Quarter Sections then give it a purified name"""

        # Split the streams_all feature
        streams_all = os.path.join(streams_intermediate, "streams_all")
        arcpy.Split_analysis(streams_all, "QuarterSections", "SEWMAP", streams_final)

        # Rename the features for consistency
        arcpy.env.workspace = streams_final
        features_to_rename = arcpy.ListFeatureClasses()
        for feature in features_to_rename:
            logger.info(f"{feature} Start")
            new_name = f"{feature}".replace("_", "").replace("T", "S_")
            output_path = os.path.join(streams_final, new_name)
            arcpy.Rename_management(feature, output_path)
            logger.info(f"{new_name} Complete")

    try:
        RasterProcessor(dtm_split, fill_folder, "fill", "TIF")
        RasterProcessor(fill_folder, direction_folder, "direction")
        Order()
        RasterProcessor(order_folder, condition_folder, "condition")
        RasterProcessor(condition_folder, streams_intermediate, "streams")
        SplitRename()
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
    Streams()
