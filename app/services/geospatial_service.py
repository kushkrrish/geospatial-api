import json
import math
import os
import shutil
import tempfile
import zipfile
import geopandas as gpd
import pandas as pd
import fiona
import shapely

# Enable KML driver support in Fiona
fiona.drvsupport.supported_drivers["KML"] = "rw"
fiona.drvsupport.supported_drivers["LIBKML"] = "rw"




class GeospatialService:

    SUPPORTED_GEOMETRIES = {
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
    }

    def extract_zip(self, zip_path: str) -> str:
        temp_dir = tempfile.mkdtemp(prefix="geospatial_")

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                for member in zip_ref.infolist():
                    member_path = os.path.abspath(
                        os.path.join(temp_dir, member.filename)
                    )

                    if not member_path.startswith(
                        os.path.abspath(temp_dir) + os.sep
                    ):
                        raise ValueError("Unsafe path detected in ZIP file")

                zip_ref.extractall(temp_dir)

            return temp_dir

        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def find_geospatial_file(self, directory: str) -> str:
        shp_files = []
        kml_files = []

        for root, _, files in os.walk(directory):
            if "__MACOSX" in root:
                continue

            for filename in files:
                if filename.startswith("._") or filename.startswith("."):
                    continue

                extension = os.path.splitext(filename)[1].lower()
                path = os.path.join(root, filename)

                if extension == ".shp":
                    shp_files.append(path)
                elif extension == ".kml":
                    kml_files.append(path)

        if shp_files:
            shp_path = shp_files[0]
            base_dir = os.path.dirname(shp_path)
            base_name = os.path.splitext(os.path.basename(shp_path))[0].lower()

            # Case-insensitive check for companion files
            dir_files = [f.lower() for f in os.listdir(base_dir)]
            has_dbf = any(f == f"{base_name}.dbf" for f in dir_files)
            has_shx = any(f == f"{base_name}.shx" for f in dir_files)

            if not (has_dbf and has_shx):
                raise ValueError(
                    f"Incomplete Shapefile in ZIP: '{os.path.basename(shp_path)}' "
                    f"is missing required companion files (.dbf or .shx)."
                )

            return shp_path

        if kml_files:
            return kml_files[0]

        raise ValueError("ZIP does not contain a valid Shapefile or KML file")

    def read_file(self, file_path: str):
        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".kml":
            return gpd.read_file(file_path, driver="KML")

        if extension == ".shp":
            return gpd.read_file(file_path)

        raise ValueError("Unsupported geospatial file")

    def load_dataset(self, file_path: str):
        extension = os.path.splitext(file_path)[1].lower()
        temp_dir = None

        try:
            if extension == ".zip":
                temp_dir = self.extract_zip(file_path)
                actual_file = self.find_geospatial_file(temp_dir)
                gdf = self.read_file(actual_file)
            else:
                gdf = self.read_file(file_path)

            return gdf

        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def get_source_crs(self, gdf) -> str:
        if gdf.crs is None:
            return "EPSG:4326"
        return gdf.crs.to_string()

    def calculate_measurement(
        self, geometry, geometry_type: str, measurement_geometry
    ):
        if geometry_type in {"Polygon", "MultiPolygon"}:
            return (measurement_geometry.area, None)

        if geometry_type in {"LineString", "MultiLineString"}:
            return (None, measurement_geometry.length)

        return (None, None)

    def extract_properties(self, row) -> dict:
        properties = {}

        for column in row.index:
            if column == "geometry":
                continue

            value = row[column]

            # Handle NaN / null values cleanly
            if pd.isna(value) or value is None:
                properties[column] = None
                continue

            try:
                json.dumps(value)
                properties[column] = value
            except (TypeError, ValueError):
                properties[column] = str(value)

        return properties

    def process(self, file_path: str):
        gdf = self.load_dataset(file_path)

        # Handle empty datasets early
        if gdf.empty:
            return {
                "source_crs": self.get_source_crs(gdf),
                "feature_count": 0,
                "features": [],
            }

        # Reset index to guarantee clean integer position indexing
        gdf = gdf.reset_index(drop=True)

        source_crs = self.get_source_crs(gdf)

        if gdf.crs is None:
            gdf = gdf.set_crs(source_crs)

        # Storage CRS (EPSG:4326 Lat/Lon)
        storage_gdf = gdf.to_crs(epsg=4326)
       

        # 2. Force geometries to 2D (strips Z dimension from KML coordinates)
        storage_gdf["geometry"] = shapely.force_2d(storage_gdf.geometry)

        # Projected Measurement CRS (UTM in meters)
        measurement_crs = storage_gdf.geometry.estimate_utm_crs()

        if measurement_crs is None:
            raise ValueError(
                "Could not determine a projected CRS for measurement"
            )

        measurement_gdf = storage_gdf.to_crs(measurement_crs)

        results = []

        for i, row in storage_gdf.iterrows():
            geometry = row.geometry

            if geometry is None or geometry.is_empty:
                continue

            geometry_type = geometry.geom_type

            if geometry_type not in self.SUPPORTED_GEOMETRIES:
                continue

            # Safe positional access using .iloc
            measurement_geometry = measurement_gdf.geometry.iloc[i]

            area, length = self.calculate_measurement(
                geometry, geometry_type, measurement_geometry
            )

            properties = self.extract_properties(row)

            results.append(
                {
                    "feature_index": i,
                    "geometry_type": geometry_type,
                    "geometry": geometry,  # GeoJSON dict format for APIs
                    "properties": properties,
                    "area": float(area) if area is not None else None,
                    "length": float(length) if length is not None else None,
                }
            )

        return {
            "source_crs": source_crs,
            "feature_count": len(results),
            "features": results,
        }