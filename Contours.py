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
import os
import traceback
from natsort import natsorted
import sys
sys.path.insert(0, "Y:/Scripts")
import Logging


# Environments
arcpy.env.overwriteOutput = True

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


def feature_processor(input_dataset, output_dataset, function_key, feature=True, start_point=0):
    """Template function for the various raster processing functions needed"""
    Logging.logger.info(f"{function_key.capitalize()} Start")

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
            "contours_lines": lambda feature_input, feature_output: arcpy.sa.Contour(feature_input, feature_output, 1, 500, max_vertices_per_feature=1000000),
            "contours_lines_simplified": lambda feature_input, feature_output: arcpy.SimplifyLine_cartography(feature_input, feature_output, "POINT_REMOVE", 1, "RESOLVE_ERRORS", "NO_KEEP"),
            "contours_lines_smoothed": lambda feature_input, feature_output: arcpy.SmoothLine_cartography(feature_input, feature_output, "PAEK", 1, error_option="RESOLVE_ERRORS"),
            "contours_polygons": lambda feature_input, feature_output: arcpy.sa.Contour(feature_input, feature_output, 1, 500, contour_type="CONTOUR_POLYGON", max_vertices_per_feature=1000000)
        }
        dictionary_key = function_dictionary[f"{function_key}"]

        # Run the lambda function using the given function key(s)
        while 0 <= start_point <= (len(feature_list) - 1):
            for feature in feature_list:

                # Name variables based on current iterator value
                input_name = os.path.join(input_dataset, feature)
                current_filename = fr"{function_key}_{start_point:03}"
                output_name = os.path.join(output_dataset, current_filename)
                Logging.logger.info(f"{current_filename} Start")
                if function_key == "contours_lines_simplified":
                    selected_contours = arcpy.SelectLayerByAttribute_management(input_name, "NEW_SELECTION", "Shape_Length >= 60")
                    dictionary_key(selected_contours, output_name)
                else:
                    dictionary_key(input_name, output_name)
                start_point += 1
                Logging.logger.info(f"{current_filename} Complete")
        Logging.logger.info(f"{function_key.capitalize()} Complete")
    else:
        raise ValueError("Incorrect input parameters")


@Logging.insert("RenameMove", 1)
def rename_move(input_dataset, output_dataset, function_key, start_point=0):
    """Take the final dataset and rename each feature using the parent quarter section for easy navigation"""
    Logging.logger.info(f"------START {function_key.capitalize()}")

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
        Logging.logger.info(f"------START {feature}")
        selected_quarter_section = arcpy.SelectLayerByLocation_management("QuarterSections", "COMPLETELY_CONTAINS", feature)

        # Assign a new name using the quarter section SEWMAP field
        with arcpy.da.SearchCursor(selected_quarter_section, "SEWMAP") as cursor:
            for row in cursor:
                quarter_section_name = row[0].replace("-", "")
                name = f"{name_prefix}_{quarter_section_name}"
                input_path = os.path.join(input_dataset, feature)
                arcpy.FeatureClassToFeatureClass_conversion(input_path, output_dataset, name)
                Logging.logger.info(f"{name} Complete")
    Logging.logger.info(f"------FINISH {function_key.capitalize()}")


if __name__ == "__main__":
    traceback_info = traceback.format_exc()
    try:
        Logging.logger.info("Script Execution Started")
        # feature_processor(dtm_split, contours_lines, "contours_lines", False)
        feature_processor(contours_lines, contours_lines_simplified, "contours_lines_simplified")
        feature_processor(contours_lines_simplified, contours_lines_smoothed, "contours_lines_smoothed")
        feature_processor(dtm_split, contours_polygons, "contours_polygons", False)
        rename_move(contours_lines_smoothed, contours_lines_final, "contours_lines")
        rename_move(contours_polygons, contours_polygons_final, "contours_polygons")
        Logging.logger.info("Script Execution Finished")
    except (IOError, NameError, KeyError, IndexError, TypeError, UnboundLocalError, ValueError):
        Logging.logger.info(traceback_info)
    except NameError:
        print(traceback_info)
    except arcpy.ExecuteError:
        Logging.logger.error(arcpy.GetMessages(2))
    except:
        Logging.logger.info("An unspecified exception occurred")
