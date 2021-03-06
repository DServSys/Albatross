import json
import copy
import rdflib as rdf
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import subprocess
from jinja2 import Environment,  FileSystemLoader
from bokeh.models import Button, Paragraph, Div
from bokeh.layouts import column, widgetbox,  row
from bokeh.models.sources import ColumnDataSource
from bokeh.models.widgets.tables import TableColumn, DataTable
from bokeh.models.widgets.inputs import TextInput

class Layout():
    _menu = None
    
    def __init__(self,  menu):
       self._menu = menu
       
    def set_layout(self, doc):
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('frameing.html')
        doc.template = template;
        
        user_str = doc.session_context.id
        layout = row([Div(), Div(), Div()], width=1700)
        # menu
        doc.template_variables["menu"] = self._menu
        print(self._menu)
        doc.add_root(layout)
        return layout
   
    def sourceToRDF(self,  doc):
        layout = self.set_layout(doc)
        dp = DataProcessing(layout)
        dp.sourceToRDFFunction()
    
    def rdf_to_geojson(self,  doc):
        layout = self.set_layout(doc)
        dp = DataProcessing(layout)
        dp.rdf_to_geojson()
        
    def endpoint_to_geojson(self,  doc):
        layout = self.set_layout(doc)
        dp = DataProcessing(layout)
        dp.endpoint_to_geojson()
        
class DataProcessing():
    
    def __init__(self, layout):
        self.layout = layout
    
    def sourceToRDFFunction(self):
        
        """
        Callback generates view on RDF and Eurostats Source Files
        """
        def callback_generate_RDF():
            """
            Callback on button generates RDF from exsiting Source
            """
            directory = 'data/sandbox/eurostat/data/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            req_directory = 'data/sandbox/eurostat/raw-data/'
            if not os.path.exists(req_directory):
                os.makedirs(req_directory)
            req_directory = 'data/sandbox/eurostat/dsd/'
            if not os.path.exists(req_directory):
                os.makedirs(req_directory)
            req_directory = 'data/sandbox/eurostat/data/'
            if not os.path.exists(req_directory):
                os.makedirs(req_directory)
            req_directory = 'data/sandbox/eurostat/logs/'
            if not os.path.exists(req_directory):
                os.makedirs(req_directory)
            req_directory = 'data/sandbox/eurostat/tsv/'
            if not os.path.exists(req_directory):
                os.makedirs(req_directory)
            
            # call java
            subprocess.call(['sh', 'Main.sh', '-i', 'sdmx-code/sdmx-code.ttl'], cwd='services/eurostat/parser/')
            # move rdf
            directory = 'data/sandbox/eurostat/data/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            for filename in os.listdir(directory):
                
                if filename.endswith(".rdf"): 
                    
                    # filename = filename.split('/')[-1]
                    os.rename(os.path.join(directory, filename), os.path.join("data/rdf/eurostats/", filename))
        
        rdf_data_table = self.show_rdf_files('ID')
        
        files = self.get_eurostats_source_file_list() 
        data_table = self.generate_rdf_column_data_source(files)
        button_dl = Button(label="Convert CSV to RDF", button_type="success")
        button_dl.on_click(callback_generate_RDF)
        para = Div(text='This module uses <a href="https://github.com/linked-statistics/eurostat" target="_blank">Eurostat dataset</a> as a service.')
        #layout
        self.layout.children[1] = column([Paragraph(text="Downloaded Sources"),widgetbox(data_table), widgetbox(para), widgetbox(button_dl)], width=400)
        self.layout.children[2] = column([Paragraph(text="Existing RDF"), widgetbox(rdf_data_table)], width=400)
        
        
    
    def get_eurostats_source_file_list(self): 
        """ 
        This function generates the file names for every RDF in the "data/rdf/eurostats" subdirectory. 
     
        :return: a list of dictionaries containing the id and file names of the RDFs found. 
        """ 
        rdf_path_prefix = "data/sandbox/eurostat/tsv" 
        observation_list = []
        if not os.path.exists(rdf_path_prefix):
            os.makedirs(rdf_path_prefix)
        for file in os.listdir(rdf_path_prefix): 
            observation = {} 
            observation_name = str(os.path.basename(file).split('.')[0]) 
            observation['id'] = observation_name 
            observation['source'] = rdf_path_prefix + file 
            observation_list.append(observation) 
        return observation_list 
    
                
    def get_eurostats_file_list(s): 
        """ 
        This function generates the file names for every RDF in the "data/rdf/eurostats" subdirectory. 
     
        :return: a list of dictionaries containing the id and file names of the RDFs found. 
        """ 
        rdf_path_prefix = "data/rdf/eurostats/"
        observation_list = []
        for file in os.listdir(rdf_path_prefix):
            observation = {}
            observation_name = str(os.path.basename(file).split('.')[0])
            observation['id'] = observation_name
            observation_list.append(observation)
        return observation_list
    
    
    def get_eurostats_geojson_list(s):
        """
        Generates dictionary of the eurostats geojson files and their NUTS level
    
        :return: Dirctionary of eurostats ID's and NUTS level that where found in data/geojson/eurostats/nuts_*
        """
        geojson_path_prefix = "data/geojson/eurostats/nuts_"
        file_list = {}
        for i in range(1, 4):
            if not os.path.exists(geojson_path_prefix + str(i)):
                os.makedirs(geojson_path_prefix + str(i))
            
            for file in os.listdir(geojson_path_prefix + str(i)):
                geojson_name = str(os.path.basename(file).split('.')[0])
                if geojson_name in file_list:
                    file_list[geojson_name].append(i)
                else:
                    file_list[geojson_name]= [i]
        return file_list
    
    
    def generate_rdf_column_data_source(self, files, column_title="ID"):
        """
        Generate data table based on files list with ``id``.
    
        :param List files: List of Dictionaries that contain the key ``id``.
        :param string column_title: Title of the data table column.
        :return: Data table containing the file IDs.
        """
        ids = [tmp_id['id'] for tmp_id in files]
        data = dict(id=ids) 
        table_source = ColumnDataSource(data)
        
        columns = [TableColumn(field="id", title=column_title)]
        data_table = DataTable(source=table_source, columns=columns, width=500, height=400, selectable=True)
        return data_table
    
    
    def show_rdf_files(self, column_title="ID"):
        """ 
        Generate data table of existing RDF Files.
    
        :param string column_title: Title of the data table column.
        :return: Data table containing the file IDs.
        """ 
        files = self.get_eurostats_file_list()
        
        data_table = self.generate_rdf_column_data_source(files, column_title=column_title)
        return data_table
    
    
    def rdf_to_geojson(self): 
        """ 
        Callback that generates the list of ready-to-transform-to-GeoJSON RDF files 
        """
        converter = RDFToGeoJSON(self.layout) 
 
        convert_button = Button(label="Convert to GeoJSON", button_type="success")
        convert_button.on_click(converter.transform)

        
        self.layout.children[1] = column(widgetbox(converter.rdf_table), convert_button)
        # # s.layout.children[2] = column(converter.geojson_table)
        #
        # geojson_table_source = ColumnDataSource(data)
        # columns = [TableColumn(field='lvl', title="NUTS Level"),
        #            TableColumn(field='id', title="ID")]
        # geojson_data_table = DataTable(source=geojson_table_source, columns=columns, width=500, height=400, selectable=True)
        # #layout
        # #s.layout.children[1] = column(widgetbox(data_table), width=500)
        # self.layout.children[2] = column(widgetbox(geojson_data_table), width=500)

    def endpoint_to_geojson(self):
        converter = EndpointToGeoJSON(self.layout)

class RDFToGeoJSON:
    def __init__(self, layout):
        self.__layout = layout
        self.__selected = []
        self.__file_list = self.__get_eurostats()

        self.__rdf_table_source = ColumnDataSource(dict(id=[f['id'] for f in self.__file_list]))
        self.__rdf_table_source.on_change('selected', self.__on_select)
        rdf_table_columns = [TableColumn(field='id', title='RDF ID')]
        self.rdf_table = DataTable(
            source=self.__rdf_table_source,
            columns=rdf_table_columns,
            width=300,
            height=500,
            selectable=True
        )

        geojson_data = {'id': [], 'lvl': []}
        for file in self.__file_list:
            if file['geojson']['nuts1']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(1)

            if file['geojson']['nuts2']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(2)

            if file['geojson']['nuts3']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(3)
        self.__geojson_table_source = ColumnDataSource(geojson_data)
        geojson_table_columns = [
            TableColumn(field='lvl', title='NUTS Level'),
            TableColumn(field='id',  title='ID')
        ]
        self.geojson_table = DataTable(
            source=self.__geojson_table_source,
            columns=geojson_table_columns,
            width=300,
            height=500,
            selectable=True
        )
        convert_button = Button(label="Convert to GeoJSON", button_type="success")
        convert_button.on_click(self.transform)
        # todo: creates bug - empty table
        #self.__layout.children[1] = column(widgetbox(self.rdf_table), convert_button)
        self.__layout.children[2] = column(self.geojson_table)

    def __on_select(self, attr, old, new):
        self.__selected = [self.__file_list[index] for index in new['1d']['indices']]

    def transform(self):
        print("converting")
        for f in self.__selected:
            print(".")
            f['results'] = self.__extract_observations(f['rdf'])

        print("writing")
        self.__write_geojson(self.__selected)
        print("done converting")

        self.__file_list = self.__get_eurostats()
        geojson_data = {'id': [], 'lvl': []}
        for file in self.__file_list:
            if file['geojson']['nuts1']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(1)

            if file['geojson']['nuts2']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(2)

            if file['geojson']['nuts3']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(3)
        self.__geojson_table_source = ColumnDataSource(geojson_data)
        geojson_table_columns = [
            TableColumn(field='lvl', title='NUTS Level'),
            TableColumn(field='id', title='ID')
        ]
        self.geojson_table = DataTable(
            source=self.__geojson_table_source,
            columns=geojson_table_columns,
            width=300,
            height=500,
            selectable=True
        )
        self.__layout.children[2] = column(self.geojson_table)

    def __get_eurostats(self):
        """
        This function generates the file names for every RDF in the "data/rdf/eurostats" subdirectory.

        :return: A list of dictionaries containing the id and file names of the RDFs found.
        """
        rdf_path_prefix = "data/rdf/eurostats/"
        geojson_path_prefix = "data/geojson/eurostats/"
        observation_list = []

        nuts_files = [
            [str(os.path.basename(file).split('.')[0]) for file in os.listdir(geojson_path_prefix + "nuts_1/")],
            [str(os.path.basename(file).split('.')[0]) for file in os.listdir(geojson_path_prefix + "nuts_2/")],
            [str(os.path.basename(file).split('.')[0]) for file in os.listdir(geojson_path_prefix + "nuts_3/")]
        ]

        for file in os.listdir(rdf_path_prefix):
            observation = {}
            observation_name = str(os.path.basename(file).split('.')[0])
            observation['id'] = observation_name
            observation['rdf'] = rdf_path_prefix + file
            observation['geojson'] = {
                'nuts1': {'path': geojson_path_prefix + "nuts_1/" + observation_name + ".geojson",
                          'exists': observation_name in nuts_files[0]},
                'nuts2': {'path': geojson_path_prefix + "nuts_2/" + observation_name + ".geojson",
                          'exists': observation_name in nuts_files[1]},
                'nuts3': {'path': geojson_path_prefix + "nuts_3/" + observation_name + ".geojson",
                          'exists': observation_name in nuts_files[2]},
            }
            observation_list.append(observation)
        return observation_list

    def __extract_observations(self, file):
        g = rdf.Graph()
        g.parse(file, format="xml")

        return g.query("""
            prefix obs: <http://purl.org/linked-data/sdmx/2009/measure#>
            prefix prop: <http://eurostat.linked-statistics.org/property#>
            prefix qb: <http://purl.org/linked-data/cube#>
            prefix sdmx-dimension: <http://purl.org/linked-data/sdmx/2009/dimension#>

            select distinct ?designation ?time ?value ?unit
            where {
                ?observation a qb:Observation.
                ?observation prop:geo ?designation.
                ?observation prop:unit ?unit.
                ?observation sdmx-dimension:timePeriod ?time.
                ?observation obs:obsValue ?value.
            }
        """)

    def __write_geojson(self, file_list):

        with open('data/geojson/eurostats/nuts_rg_60M_2013_lvl_3.geojson') as f:
            nuts3 = json.load(f)
        with open('data/geojson/eurostats/nuts_rg_60M_2013_lvl_2.geojson') as f:
            nuts2 = json.load(f)
        with open('data/geojson/eurostats/nuts_rg_60M_2013_lvl_1.geojson') as f:
            nuts1 = json.load(f)

        nuts = [nuts1, nuts2, nuts3]

        for file in file_list:
            geojson = copy.deepcopy(nuts)
            self.__process_file(file, geojson)

            for lvl in range(0, len(geojson)):
                with open(file['geojson']['nuts{}'.format(lvl + 1)]['path'], 'w') as outfile:
                    json.dump(geojson[lvl], fp=outfile, indent=4)

    def __process_file(self, file, nuts):
        for row in file['results']:
            # recover uncluttered information from the sparql result
            geo = row[0].split('#')[1]
            time = row[1]
            value = row[2]
            unit = row[3].split('#')[1]

            # search for the NUTS_ID (geo) in the NUTS level 1 to 3
            index = -1
            nuts_lvl = -1
            found = False
            while not found:
                index += 1
                done = []
                # prepare break condition
                for lvl in range(0, len(nuts)):
                    done.append(False)

                # check if the ID matches in any of the NUTS levels
                for lvl in range(0, len(nuts)):
                    if index < len(nuts[lvl]['features']):
                        if nuts[lvl]['features'][index]['properties']['NUTS_ID'] == geo:
                            nuts_lvl = lvl
                            found = True
                            break
                    else:
                        done[lvl] = True
                if all(done):
                    break

            if nuts_lvl != -1:
                observation = {
                    'period': time,
                    'unit': unit,
                    'value': value
                }

                # check if any of the nested elements in the JSON already exist
                if 'OBSERVATIONS' in nuts[nuts_lvl]['features'][index]['properties']:
                    if file['id'] in nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS']:
                        duplicate = False
                        for observations in nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'][file['id']]:
                            if observations['period'] == observation['period']:
                                duplicate = True
                                break
                        if not duplicate:
                            nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'][file['id']].append(
                                observation)
                    else:
                        nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'][file['id']] = [observation]
                else:
                    nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'] = {
                        file['id']: [observation]
                    }

class EndpointToGeoJSON:
    def __init__(self, layout):
        self.__layout = layout
        self.__selected = []
        self.__file_list = self.__get_eurostats()

        geojson_data = {'id': [], 'lvl': []}
        for file in self.__file_list:
            if file['geojson']['nuts1']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(1)

            if file['geojson']['nuts2']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(2)

            if file['geojson']['nuts3']['exists']:
                geojson_data['id'].append(file['id'])
                geojson_data['lvl'].append(3)
        self.__geojson_table_source = ColumnDataSource(geojson_data)
        geojson_table_columns = [
            TableColumn(field='lvl', title='NUTS Level'),
            TableColumn(field='id', title='ID')
        ]
        self.geojson_table = DataTable(
            source=self.__geojson_table_source,
            columns=geojson_table_columns,
            width=300,
            height=500,
            selectable=True
        )

        convert_button = Button(label="Convert to GeoJSON", button_type="success")
        convert_button.on_click(self.transform)
        self.__endpoint_input = TextInput(placeholder="SPARQL Endpoint")
        self.__graph_input = TextInput(placeholder="Graph")
        self.__layout.children[1] = column(self.__endpoint_input, self.__graph_input, convert_button)
        self.__layout.children[2] = column(self.geojson_table)


    def transform(self):
        if self.__graph_input.value and self.__endpoint_input.value:
            filename = self.__graph_input.value.split('/')[-1].split('.')[0]

            print("converting")
            sparql = SPARQLWrapper("https://www.foodie-cloud.org/sparql")
            query_a = """
            prefix obs: <http://purl.org/linked-data/sdmx/2009/measure#>
            prefix prop: <http://eurostat.linked-statistics.org/property#>
            prefix qb: <http://purl.org/linked-data/cube#>
            prefix sdmx-dimension: <http://purl.org/linked-data/sdmx/2009/dimension#>
            
            select distinct ?designation ?time ?value ?unit
            """

            graph = "from <{}>".format(self.__graph_input.value)

            query_b = """
            where {
                ?observation a qb:Observation.
                ?observation prop:geo ?designation.
                ?observation prop:unit ?unit.
                ?observation sdmx-dimension:timePeriod ?time.
                ?observation obs:obsValue ?value.
            }
            """

            query = "{}\n{}\n{}".format(query_a, graph, query_b)

            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print("writing")
            self.__write_geojson(results, filename)
            print("done converting")

            self.__file_list = self.__get_eurostats()
            geojson_data = {'id': [], 'lvl': []}
            for file in self.__file_list:
                if file['geojson']['nuts1']['exists']:
                    geojson_data['id'].append(file['id'])
                    geojson_data['lvl'].append(1)

                if file['geojson']['nuts2']['exists']:
                    geojson_data['id'].append(file['id'])
                    geojson_data['lvl'].append(2)

                if file['geojson']['nuts3']['exists']:
                    geojson_data['id'].append(file['id'])
                    geojson_data['lvl'].append(3)
            self.__geojson_table_source = ColumnDataSource(geojson_data)
            geojson_table_columns = [
                TableColumn(field='lvl', title='NUTS Level'),
                TableColumn(field='id', title='ID')
            ]
            self.geojson_table = DataTable(
                source=self.__geojson_table_source,
                columns=geojson_table_columns,
                width=300,
                height=500,
                selectable=True
            )
            self.__layout.children[2] = column(self.geojson_table)

    def __write_geojson(self, results, filename):

        with open('data/geojson/eurostats/nuts_rg_60M_2013_lvl_3.geojson') as f:
            nuts3 = json.load(f)
        with open('data/geojson/eurostats/nuts_rg_60M_2013_lvl_2.geojson') as f:
            nuts2 = json.load(f)
        with open('data/geojson/eurostats/nuts_rg_60M_2013_lvl_1.geojson') as f:
            nuts1 = json.load(f)

        nuts = [nuts1, nuts2, nuts3]

        geojson = copy.deepcopy(nuts)
        self.__process_file(results, geojson, filename)
        base_path = os.path.join("data", "geojson", "eurostats")

        for lvl in range(0, len(geojson)):
            path = str(os.path.join(base_path, "nuts_{}".format(lvl +1), "{}.geojson".format(filename)))
            with open(path, 'w') as outfile:
                json.dump(geojson[lvl], fp=outfile, indent=4)

    def __process_file(self, results, nuts, filename):
        for result in results["results"]["bindings"]:
            geo = result['designation']['value'].split('#')[-1]
            time = result['time']['value']
            value = result['value']['value']
            unit = result['unit']['value'].split('#')[-1]

            # search for the NUTS_ID (geo) in the NUTS level 1 to 3
            index = -1
            nuts_lvl = -1
            found = False
            while not found:
                index += 1
                done = []
                # prepare break condition
                for lvl in range(0, len(nuts)):
                    done.append(False)

                # check if the ID matches in any of the NUTS levels
                for lvl in range(0, len(nuts)):
                    if index < len(nuts[lvl]['features']):
                        if nuts[lvl]['features'][index]['properties']['NUTS_ID'] == geo:
                            nuts_lvl = lvl
                            found = True
                            break
                    else:
                        done[lvl] = True
                if all(done):
                    break

            if nuts_lvl != -1:
                observation = {
                    'period': time,
                    'unit': unit,
                    'value': value
                }
                # check if any of the nested elements in the JSON already exist
                if 'OBSERVATIONS' in nuts[nuts_lvl]['features'][index]['properties']:
                    if filename in nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS']:
                        duplicate = False
                        for observations in nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'][filename]:
                            if observations['period'] == observation['period']:
                                duplicate = True
                                break
                        if not duplicate:
                            nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'][filename].append(
                                observation)
                    else:
                        nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'][filename] = [observation]
                else:
                    nuts[nuts_lvl]['features'][index]['properties']['OBSERVATIONS'] = {
                        filename: [observation]
                    }

    def __get_eurostats(self):
        """
        This function generates the file names for every RDF in the "data/rdf/eurostats" subdirectory.

        :return: A list of dictionaries containing the id and file names of the RDFs found.
        """
        rdf_path_prefix = "data/rdf/eurostats/"
        geojson_path_prefix = "data/geojson/eurostats/"
        observation_list = []

        nuts_files = [
            [str(os.path.basename(file).split('.')[0]) for file in os.listdir(geojson_path_prefix + "nuts_1/")],
            [str(os.path.basename(file).split('.')[0]) for file in os.listdir(geojson_path_prefix + "nuts_2/")],
            [str(os.path.basename(file).split('.')[0]) for file in os.listdir(geojson_path_prefix + "nuts_3/")]
        ]

        for file in os.listdir(rdf_path_prefix):
            observation = {}
            observation_name = str(os.path.basename(file).split('.')[0])
            observation['id'] = observation_name
            observation['rdf'] = rdf_path_prefix + file
            observation['geojson'] = {
                'nuts1': {'path': geojson_path_prefix + "nuts_1/" + observation_name + ".geojson",
                          'exists': observation_name in nuts_files[0]},
                'nuts2': {'path': geojson_path_prefix + "nuts_2/" + observation_name + ".geojson",
                          'exists': observation_name in nuts_files[1]},
                'nuts3': {'path': geojson_path_prefix + "nuts_3/" + observation_name + ".geojson",
                          'exists': observation_name in nuts_files[2]},
            }
            observation_list.append(observation)
        return observation_list
