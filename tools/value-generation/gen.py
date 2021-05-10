import yaml
import copy
from emitter import CommentedMapping, CommentedDumper
import sys

# format properties for helm chart
def format_properties(properties, values, comments, sub_keys, depth):
  for key, value in properties.items():

    if 'description' not in value:
      value['description'] = ""

    
    description = value['description']

    if 'items' in value:
      if 'properties' in value['items']:
        value = value['items']

    # check for sub properties 
    if 'properties' in value:
      values[key] = {}

      # place comment key at whatever depth we are in
      subs = copy.deepcopy(sub_keys)
      subs.append(key)
      comments[tuple(subs)] = description
      format_properties(value['properties'], values[key], comments, subs, depth + 1)

    else:
      comment_key = key 
      if len(sub_keys):
        subs = copy.deepcopy(sub_keys)
        subs.append(key)
        comment_key = tuple(subs)

      # populate description and default value
      # comment keys are tuple
      comments[comment_key] = description

      # Now set the default value
      values[key] = None 
      if 'default' in value:
        values[key] = value['default']
      else:
        # boolean without default is False
        if 'type' in value:
          if value['type'] == 'boolean':
            values[key] = False
          # Other supported types are string, integer, array and object

# Set up a lookup table mapping CRD name to Helm chart YAML key
crd_mapping = {}
crd_mapping['CouchbaseCluster']='cluster'

# read in crd properties from stdin
input_crd = sys.stdin.read()

for data in yaml.load_all(input_crd, Loader=yaml.Loader) :
  crd_name=data['spec']['names']['kind']
  if crd_name in crd_mapping :
    crd_value=crd_mapping[crd_name]
    
    crd_properties = data['spec']['versions'][0]['schema']['openAPIV3Schema']['properties']['spec']['properties']

    # pass properties into formatter
    value_map = {}
    value_map[crd_value] ={}
    comment_map = {}
    comment_map[crd_value] = 'Controls the generation of the ' + crd_name + ' CRD'
    format_properties(crd_properties, value_map[crd_value], comment_map, [crd_value], 0)

    # reorganize
    # TODO

    # convert to documented map
    helm_values = CommentedMapping(value_map, comments=comment_map)

    # dump to stdout
    print(yaml.dump(helm_values, Dumper=CommentedDumper))
