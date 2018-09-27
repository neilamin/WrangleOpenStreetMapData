
# coding: utf-8

# # Project 4: Wrangle OpenStreetMap Data

# #### Neil Amin

# In[1]:


import xml.etree.ElementTree as ET
from collections import defaultdict
import re
import pprint
import collections


# In[2]:


def count_tags(filename):
    tags = {}
    for _,elem in ET.iterparse(filename):
        if elem.tag in tags: #if the tag already exists in the dict, add 1
            tags[elem.tag] += 1
        else: #if the tag does not exist, create a new key and value in the dic
            tags[elem.tag] = 1
    #return the result
    return tags


# In[3]:


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        key = element.attrib['k']
        if lower.search(key):
            keys['lower'] += 1
            print('lower: {}'.format(key))
        elif lower_colon.search(key):
             keys['lower_colon'] += 1
             print('lower colon: {}'.format(key))
        elif problemchars.search(key):
             keys['problemchars'] += 1
             print('problemchars: {}'.format(key))
        else:
             keys['other'] += 1
             print(key)
    
    return keys



def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys


# In[4]:


OSMFILE = "honolulu_hawaii.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

# UPDATE THIS VARIABLE
mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue", 
            "Ave.": "Avenue", 
            "Blvd": "Boulevard",
            "Dr": "Drive",
            "Dr.": "Drive",
            "Raod": "Road",
            "Rd": "Road",
            "Rd.": "Road",
            "Sq.": "Square",
            "Wy": "Way"
            }

amenity_mapping = { "public_building": "Public Building",
                    "fire_station": "Fire Station",
                    "arts_centre": "Arts Centre", 
                    "library": "Library", 
                    "Blvd": "Boulevard",
                    "hospital": "Hospital",
                    "public_building": "Public Building",
                    "prison": "Prison",
                    "theatre": "Theatre",
                    "pharmacy": "Pharmacy",
                    "restaurant": "Restaurant",
                    "cafe": "Cafe",
                    "toilets": "Toilets",
                    "post_office": "Post Office",
                    "school": "School",
                    "parking": "Parking"
                }

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osmfile, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def update_name(name, mapping):
    
    #Step 1. Identify the street type using regex pattern matching
    #Step 2. Find the "better" street type using user defined "matching" dictionary
    #Step 3. Replace old street_type with better street_type

    #Step 1
    print('name: {}'.format(name)) # Print original street name
    m = street_type_re.search(name) # Search name for regex pattern for street type
    
    if m: # Check if the refex pattern for street type was found
        street_type = m.group()
        print('m.group() output: {}'.format(street_type)) # Print street type
    
    #Step 2    
    better_type = street_type # Initialized the "better" street type variable    
    for problem_type in mapping:
        if street_type == problem_type:
            better_type = mapping[problem_type]
            
    #Step 3
    better_name = name.replace(street_type, better_type) #replace the street type with better_type
    print('better_name: {}'.format(better_name)) #print better street name
    
    return better_name

def update_amenity(node):
    if "amenity" in node and "name" in node:
        if node["name"] in amenity_mapping and node["amenity"] != amenity_mapping[node["name"]]:
            node["amenity"] = amenity_mapping[node["name"]]
    return node    

def replace_word():
    st_types = audit(OSMFILE)
    for st_type, ways in st_types.items():
        for name in ways:
            update_name(name, mapping)
            better_name = update_name(name, mapping)
            print (name, "=>", better_name)

if __name__ == '__main__':
    replace_word()


# In[5]:


#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
After auditing is complete the next step is to prepare the data to be inserted into a SQL database.
To do so you will parse the elements in the OSM XML file, transforming them from document format to
tabular format, thus making it possible to write to .csv files.  These csv files can then easily be
imported to a SQL database as tables.

The process for this transformation is as follows:
- Use iterparse to iteratively step through each top level element in the XML
- Shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the correct format
- Write each data structure to the appropriate .csv files

We've already provided the code needed to load the data, perform iterative parsing and write the
output to csv files. Your task is to complete the shape_element function that will transform each
element into the correct format. To make this process easier we've already defined a schema (see
the schema.py file in the last code tab) for the .csv files and the eventual tables. Using the 
cerberus library we can validate the output against this schema to ensure it is correct.

## Shape Element Function
The function should take as input an iterparse Element object and return a dictionary.

### If the element top level tag is "node":
The dictionary returned should have the format {"node": .., "node_tags": ...}

The "node" field should hold a dictionary of the following top level node attributes:
- id
- user
- uid
- version
- lat
- lon
- timestamp
- changeset
All other attributes can be ignored

The "node_tags" field should hold a list of dictionaries, one per secondary tag. Secondary tags are
child tags of node which have the tag name/type: "tag". Each dictionary should have the following
fields from the secondary tag attributes:
- id: the top level node id attribute value
- key: the full tag "k" attribute value if no colon is present or the characters after the colon if one is.
- value: the tag "v" attribute value
- type: either the characters before the colon in the tag "k" value or "regular" if a colon
        is not present.

Additionally,

- if the tag "k" value contains problematic characters, the tag should be ignored
- if the tag "k" value contains a ":" the characters before the ":" should be set as the tag type
  and characters after the ":" should be set as the tag key
- if there are additional ":" in the "k" value they and they should be ignored and kept as part of
  the tag key. For example:

  <tag k="addr:street:name" v="Lincoln"/>
  should be turned into
  {'id': 12345, 'key': 'street:name', 'value': 'Lincoln', 'type': 'addr'}

- If a node has no secondary tags then the "node_tags" field should just contain an empty list.

The final return value for a "node" element should look something like:

{'node': {'id': 757860928,
          'user': 'uboot',
          'uid': 26299,
       'version': '2',
          'lat': 41.9747374,
          'lon': -87.6920102,
          'timestamp': '2010-07-22T16:16:51Z',
      'changeset': 5288876},
 'node_tags': [{'id': 757860928,
                'key': 'amenity',
                'value': 'fast_food',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'cuisine',
                'value': 'sausage',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'name',
                'value': "Shelly's Tasty Freeze",
                'type': 'regular'}]}

### If the element top level tag is "way":
The dictionary should have the format {"way": ..., "way_tags": ..., "way_nodes": ...}

The "way" field should hold a dictionary of the following top level way attributes:
- id
-  user
- uid
- version
- timestamp
- changeset

All other attributes can be ignored

The "way_tags" field should again hold a list of dictionaries, following the exact same rules as
for "node_tags".

Additionally, the dictionary should have a field "way_nodes". "way_nodes" should hold a list of
dictionaries, one for each nd child tag.  Each dictionary should have the fields:
- id: the top level element (way) id
- node_id: the ref attribute value of the nd tag
- position: the index starting at 0 of the nd tag i.e. what order the nd tag appears within
            the way element

The final return value for a "way" element should look something like:

{'way': {'id': 209809850,
         'user': 'chicago-buildings',
         'uid': 674454,
         'version': '1',
         'timestamp': '2013-03-13T15:58:04Z',
         'changeset': 15353317},
 'way_nodes': [{'id': 209809850, 'node_id': 2199822281, 'position': 0},
               {'id': 209809850, 'node_id': 2199822390, 'position': 1},
               {'id': 209809850, 'node_id': 2199822392, 'position': 2},
               {'id': 209809850, 'node_id': 2199822369, 'position': 3},
               {'id': 209809850, 'node_id': 2199822370, 'position': 4},
               {'id': 209809850, 'node_id': 2199822284, 'position': 5},
               {'id': 209809850, 'node_id': 2199822281, 'position': 6}],
 'way_tags': [{'id': 209809850,
               'key': 'housenumber',
               'type': 'addr',
               'value': '1412'},
              {'id': 209809850,
               'key': 'street',
               'type': 'addr',
               'value': 'West Lexington St.'},
              {'id': 209809850,
               'key': 'street:name',
               'type': 'addr',
               'value': 'Lexington'},
              {'id': '209809850',
               'key': 'street:prefix',
               'type': 'addr',
               'value': 'West'},
              {'id': 209809850,
               'key': 'street:type',
               'type': 'addr',
               'value': 'Street'},
              {'id': 209809850,
               'key': 'building',
               'type': 'regular',
               'value': 'yes'},
              {'id': 209809850,
               'key': 'levels',
               'type': 'building',
               'value': '1'},
              {'id': 209809850,
               'key': 'building_id',
               'type': 'chicago',
               'value': '366409'}]}
"""

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "honolulu_hawaii.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    #Node
    if element.tag == 'node':
        for attribute in node_attr_fields:
            node_attribs[attribute] = element.attrib[attribute]
        for secondary_elem in element.findall('tag'):
            tag_append = find_tags(secondary_elem, element.attrib['id'])
            tags.append(tag_append)
        tags = update_amenity(tags)
        return {'node': node_attribs, 'node_tags': tags}
    #Way
    elif element.tag == 'way':
        for attribute in way_attr_fields: 
            way_attribs[attribute] = element.attrib[attribute]
        for secondary_elem in element.findall('tag'):
            tag_append = find_tags(secondary_elem, element.attrib['id'])
            tags.append(tag_append)
        position = 0
        for secondary_elem in element.findall('nd'):
            way_nodes_append = {'id'       : element.attrib['id'],
                                'node_id'  : secondary_elem.attrib['ref'],
                                'position' : position
                               }
            position += 1
            way_nodes.append(way_nodes_append)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))

def find_tags(elm, id_value):
    key = elm.attrib['k']
    if PROBLEMCHARS.search(key) is None:
        if ':' in key:
            key_split = key.split(':')
            type_field = key_split[0]
            key = key[len(type_field)+1:]
        else:
            type_field = 'regular'
    
    tag_append = { 'id'     : id_value,
                   'key'    : key,
                    'value' : elm.attrib['v'],
                    'type'  : type_field
                 }
    return tag_append
            


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w', encoding = 'utf8') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w', encoding = 'utf8') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w', encoding = 'utf8') as ways_file,          codecs.open(WAY_NODES_PATH, 'w', encoding = 'utf8') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w', encoding = 'utf8') as way_tags_file:

        nodes_writer = csv.DictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = csv.DictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = csv.DictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = csv.DictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = csv.DictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                #if validate is True:
                    #validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)


# In[ ]:




