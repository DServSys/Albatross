from SPARQLWrapper import SPARQLWrapper, JSON
import xml.etree.ElementTree
import os

e = xml.etree.ElementTree.parse(os.path.join(os.path.dirname(__file__), 'config.xml')).getroot()

#TODO improve xml query
'''
TODO: <unit>amount_unit</unit> implement crop_type etc...
'''
def buildqueryselect():
    # read xml file
    # first only selects without using them as properties for geojson
    for atype in e.findall('sparql'):
        select = atype.findall('select')
        selectstring = '';
        for t in select:
            selectstring = selectstring + ' ?' + t.text
    # here add to select the properties including geodata and date as special sets
    for prop in e.findall('properties'):
        for p in prop.findall('property'):
            selectstring = selectstring + ' ?' + p.find('sparql').find('select').text
            selectstring = selectstring + ' ?' + p.find('sparql').find('unit').text
        selectstring = selectstring + ' ?' + prop.find('date').text
        selectstring = selectstring + ' ?' + prop.find('geo').text
    
    return selectstring

def buildquerywhere():
    for atype in e.findall('sparql'):
        wherestring = atype.find('where').text
    return wherestring;

def buildqueryfrom():
    for atype in e.findall('sparql'):
        fromstring = '<' + atype.find('from').text + '>'
    return fromstring;

def buildqueryendpoint():
    for atype in e.findall('sparql'):
        endstring = atype.find('endpoint').text
    return endstring;


def buildqueryprefix():
    prestring = '';
    for a in e.findall('sparql'):
        for atype in a.findall('prefixes'):
            for pre in atype.findall('prefix'):
                prestring = prestring + """PREFIX """ + pre.get('short') + """: <""" + pre.text + """>
                """
    return prestring

    
def query():
    sparql = SPARQLWrapper(buildqueryendpoint())
    sparql.setQuery(
        buildqueryprefix() +
        """
        
        select """ + buildqueryselect() + """
        from """ + buildqueryfrom() + """
        where 
        {
            """ + buildquerywhere() + """
        }
        
    
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    return results;
    #for result in results["results"]["bindings"]:
     #   print(result["geosc"]["value"])
