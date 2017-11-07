from bokeh.plotting import figure
from bokeh.models import WMTSTileSource, ColumnDataSource
from bokeh.models.widgets import Select
from bokeh.layouts import column, row
import os
import math
import numpy as np
import geopandas as gpd
import json
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon


class Nuts:
    def __init__(self, layout):
        self.id_select = Select(title="ID Select:", value=a["Level 1"][0], options=a["Level 1"])
        self.lvl_select = Select(title="Nuts Level:", value="Level 1", options=self.lvl_select_options)
        self.lvl_select_options = ["Level 1", "Level 2", "Level 3"]
        self.layout = layout

    @staticmethod
    def get_poly_coordinates(row, geom, coord_type):
        """Returns the coordinates ('x' or 'y') of edges of a Polygon exterior"""

        # Parse the exterior of the coordinate
        exterior = row[geom].exterior

        if coord_type == 'x':
            # Get the x coordinates of the exterior
            return list(exterior.coords.xy[0])
        elif coord_type == 'y':
            # Get the y coordinates of the exterior
            return list(exterior.coords.xy[1])

    @staticmethod
    def explode(input_data):
        input_dataframe = gpd.GeoDataFrame.from_file(input_data)
        output_dataframe = gpd.GeoDataFrame(columns=input_dataframe.columns)
        for idx, row in input_dataframe.iterrows():
            if type(row.geometry) == Polygon:
                output_dataframe = output_dataframe.append(row, ignore_index=True)
            if type(row.geometry) == MultiPolygon:
                multdf = gpd.GeoDataFrame(columns=input_dataframe.columns)
                recs = len(row.geometry)
                multdf = multdf.append([row] * recs, ignore_index=True)
                for geom in range(recs):
                    multdf.loc[geom, 'geometry'] = row.geometry[geom]
                output_dataframe = output_dataframe.append(multdf, ignore_index=True)
        return output_dataframe

    @staticmethod
    def get_eurostats_geojson_list():
        """
        Generates dictionary of the eurostats geojson files and their NUTS level

        :return: Dirctionary of eurostats ID's and NUTS level that where found in data/geojson/eurostats/nuts_*
        """
        geojson_path_prefix = "data/geojson/eurostats/nuts_"
        file_list = {}
        for i in range(1, 4):
            for file in os.listdir(geojson_path_prefix + str(i)):
                geojson_name = str(os.path.basename(file).split('.')[0])
                if geojson_name in file_list:
                    file_list[geojson_name].append(i)
                else:
                    file_list[geojson_name] = [i]
        return file_list

    @staticmethod
    def produce_column_data(self, input_data):
        raw_data = self.explode(input_data)

        # Transform CRS
        raw_data.crs = {'init': 'epsg:4326'}
        raw_data = raw_data.to_crs({'init': 'epsg:3857'})

        # Get coordinates
        raw_data['x'] = raw_data.apply(self.get_poly_coordinates, geom='geometry', coord_type='x', axis=1)
        raw_data['x'] = raw_data.apply(self.get_poly_coordinates, geom='geometry', coord_type='y', axis=1)

        dataframe = raw_data.drop('geometry', axis=1).copy()
        return ColumnDataSource(dataframe)

    def show_data(self):
        # Plot map
        tools = "pan,wheel_zoom,box_zoom,reset,tap"
        bound = 20000000
        p = figure(
            width=800,
            height=600,
            title="NUTS Areas",
            tools=tools,
            x_range=(-bound, bound),
            y_range=(-bound, bound)
        )
        p.title.text_font_size = "25px"
        p.title.align = "center"
        p.toolbar.logo = None

        # Set Tiles
        tile_source = WMTSTileSource(
            url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{Y}/{X}.jpg'
        )
        p.add_tile(tile_source)
        p.axis.visible = False

        eurostats = self.get_eurostats_geojson_list()

        # collect ID by level
        a = {
            "Level 1": [k for k, v in eurostats.items() if 1 in v],
            "Level 2": [k for k, v in eurostats.items() if 2 in v],
            "Level 3": [k for k, v in eurostats.items() if 3 in v]
        }

        # ToDo remove this crap
        ################################################################
        # random plot
        rand_y_offset = np.random.rand(200)
        rand_x_offset = np.random.rand(1) * math.pi / 2
        x = np.linspace(0, 4 * math.pi, 200)
        curve = np.sin(x + rand_x_offset) * 3 + rand_y_offset
        xs = x.tolist()
        ys = curve.tolist()
        random_source = ColumnDataSource({'x': xs, 'y': ys})
        p2 = figure(width=600, height=200, title='random data 1')
        p2.line(x='x', y='y', source=random_source)
        ################################################################

        # ToDo remove this crap, aswell
        ################################################################
        # random plot
        rand_y_offset = np.random.rand(200)
        rand_x_offset = np.random.rand(1) * math.pi / 2
        x = np.linspace(0, 4 * math.pi, 200)
        curve = np.sin(x + rand_x_offset) * 3 + rand_y_offset
        xs = x.tolist()
        ys = curve.tolist()
        random_source = ColumnDataSource({'x': xs, 'y': ys})
        p3 = figure(width=600, height=200, title='random data 2')
        p3.line(x='x', y='y', source=random_source)
        ################################################################

        self.layout.children[1] = column(p, row(self.lvl_select, self.id_select))
        self.layout.children[2] = column(p2, p3)
