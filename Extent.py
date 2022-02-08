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
import os
import traceback
import sys
sys.path.insert(0, "Y:/Scripts")
import Logging

# DTM Folders
directory = r"C:\Users\jtjohnson\Documents\Python\DEM"
dtm = os.path.join(directory, "DTM")
dtm_split = os.path.join(directory, "DTM_Split")


# PLSS Quarter Sections
sde = r"C:\Users\jtjohnson\AppData\Roaming\ESRI\ArcGISPro\Favorites\OS@imSPFLD-Version.sde"
cadastral_reference = os.path.join(sde, "imSPFLD.COSPW.CadastralReference")
quarter_sections = os.path.join(cadastral_reference, "imSPFLD.COSPW.PLSSQuarterSection")
arcpy.MakeFeatureLayer_management(quarter_sections, "QuarterSections", "SEWMAPOLD <> ''")


@Logging.insert("Delete", 1)
def raster_delete():
    """Delete the current rasters in the output folder"""
    if len(os.listdir(dtm_split)) > 0:
        for file in os.listdir(dtm_split):
            os.remove(os.path.join(dtm_split, f"{file}"))


@Logging.insert("Split", 1)
def raster_split():
    """Split the DTM into manageable cell sizes and limit it to a certain extent rather than the entire county"""
    arcpy.SplitRaster_management(dtm, dtm_split, "dtm_split_", "POLYGON_FEATURES", overlap=1, clip_type="FEATURE_CLASS", split_polygon_feature_class="QuarterSections", template_extent="QuarterSections")

    # Log the number of cells
    arcpy.env.workspace = dtm_split
    count = len(arcpy.ListRasters())
    Logging.logger.info(f"Raster has {count} cells")


if __name__ == "__main__":
    traceback_info = traceback.format_exc()
    try:
        Logging.logger.info("Script Execution Started")
        raster_delete()
        raster_split()
        Logging.logger.info("Script Execution Finished")
    except (IOError, NameError, KeyError, IndexError, TypeError, UnboundLocalError, ValueError):
        Logging.logger.info(traceback_info)
    except NameError:
        print(traceback_info)
    except arcpy.ExecuteError:
        Logging.logger.error(arcpy.GetMessages(2))
    except:
        Logging.logger.info("An unspecified exception occurred")
