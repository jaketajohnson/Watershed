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
import os
import traceback
import sys
sys.path.insert(0, "Y:/Scripts")
import Logging


# Environments
arcpy.env.overwriteOutput = True

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


@Logging.insert("Merge All")
def merge_all(input_dataset, output_merged):
    """Take input and merge into output"""
    Logging.logger.info(f"{input_dataset} Start")
    arcpy.env.workspace = input_dataset
    features_to_merge = arcpy.ListFeatureClasses()
    merged_to_remove = os.path.basename(output_merged)
    features_to_merge.remove(merged_to_remove)
    arcpy.Merge_management(features_to_merge, output_merged)
    Logging.logger.info(f"{output_merged} Complete")


if __name__ == "__main__":
    traceback_info = traceback.format_exc()
    try:
        Logging.logger.info("Script Execution Started")
        merge_all(contours_lines_final, contours_lines_merged)
        merge_all(streams_final, streams_merged)
        merge_all(contours_polygons_final, contours_polygons_merged)
        Logging.logger.info("Script Execution Finished")
    except (IOError, NameError, KeyError, IndexError, TypeError, UnboundLocalError, ValueError):
        Logging.logger.info(traceback_info)
    except NameError:
        print(traceback_info)
    except arcpy.ExecuteError:
        Logging.logger.error(arcpy.GetMessages(2))
    except:
        Logging.logger.info("An unspecified exception occurred")
