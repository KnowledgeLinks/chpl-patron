""" Class for getting data mappings"""

__author__="Mike Stabile, Jeremy Nelson"
import os
import logging
import json
import requests

import elasticsearch.exceptions as es_except
from elasticsearch import Elasticsearch
from instance import config

from chplpatron import sierra


MODULE = __import__(__name__)

log = logging.getLogger("esmappings")
log.setLevel(logging.DEBUG)


class EsMappings:
    """ Class for manipulating elasticsearch mappings with the rdfframework

    attributes:

    """
    log_level = logging.INFO

    es_mapping = None
    # es_settings = None

    def __init__(self, es_url=None, **kwargs):
        if not es_url:
            es_url = config.ES_URL
        self.es_url = es_url
        self.es = Elasticsearch([es_url])
        self.mapping_url = '{0}/_mapping'.format(self.es_url)

    @classmethod
    def get_es_idx_map(cls, idx_name, idx_obj):
        """
        Returns an elasticsearch mapping for the specified index based off
        of the mapping defined by the class definition

        args:
            idx_obj: Dictionary of the index and a list of rdfclasses
                     included in the mapping
        """
        idx_name = list(idx_obj)[0]

        es_map = {
            "index": idx_name,
            "body" : {
                "mappings": {},
                "settings": {
                    # "read_only_allow_delete": False,
                    "index": {
                        # "blocks" : {
                        #     "read_only_allow_delete" : "false"
                        # },
                        "analysis": {
                            "analyzer": {
                                "keylower": {
                                    "tokenizer": "keyword",
                                    "type": "custom",
                                    "filter": "lowercase",
                                    "ignore_above" : 256
                                }
                            }
                        }
                    }
                }
            }
        }
        es_map['body']['mappings'][idx_name] = {'properties':
                                                idx_obj.es_mapping()}
        return es_map

    def send_es_mapping(self, es_map, **kwargs):
        """
        sends the mapping to elasticsearch

        args:
            es_map: dictionary of the index mapping

        kwargs:
            reset_idx: WARNING! If True the current referenced es index
                    will be deleted destroying all data in that index in
                    elasticsearch. if False an incremented index will be
                    created and data-migration will start from the old to
                    the new index
        """

        def next_es_index_version():
            """ returns the next number for a new index

                args:
                    alias_def: the dictionary returned by es for get alias
            """
            try:
                alias_def = self.es.indices.get_alias(alias)
            except es_except.NotFoundError:
                alias_def = {alias + "_v0":{}}
            old_idx = list(alias_def)[0]
            parts = old_idx.split("_v")
            try:
                parts[1] = str(int(parts[1]) + 1)
            except IndexError:
                parts = [old_idx,'1']
            return {'old': old_idx, 'new': "_v".join(parts)}

        reset_idx= kwargs.get('reset_idx', False)
        alias = es_map.pop('index')
        idx_names = next_es_index_version()

        # Delete if the index series if reset_idx was passed
        if reset_idx:
            log.warning("DELETING Elasticsearch INDEX => %s ******", alias)
            self.es.indices.delete(index=alias + "_v*", ignore=[400, 404])
            idx_names['new'] = alias + "_v1"

        # Create the new index and apply the mapping
        self.es.indices.create(index=idx_names['new'],
                               body=es_map['body'],
                               update_all_types=True)
        # if the index was not deleted transfer documents from old to the
        # new index
        if not reset_idx and self.es.indices.exists(idx_names['old']):
            map_url = os.path.join(self.es_url, '_reindex').replace('\\', '/')
            data = {"source": {"index": idx_names['old']},
                    "dest": {"index": idx_names['new']}}
            # Python elasticsearch recommends using a direct call to the
            # es 5+ _reindex URL vice using their helper.
            result = requests.post(map_url,
                                   headers={'Content-Type': 'application/json'},
                                   json=data)
            self.es.indices.delete_alias(index=idx_names['old'],
                                         name=alias,
                                         ignore=[403])
            self.es.indices.delete(index=idx_names['old'], ignore=[400, 404])
        # add the alias to the new index
        self.es.indices.put_alias(index=idx_names['new'], name=alias)

    def initialize_indices(self, **kwargs):
        """
        creates all the indicies that are defined in the rdf definitions

        kwargs:
            action: which action is to be perfomed
                    initialize: (default) tests to see if the index exisits
                                if not creates it
                    reset: deletes all of the indexes and recreate them
                    update: starts a mapping update and reindexing process
        """
        action = kwargs.get('action', 'initialize')
        if action == 'update':
            kwargs['reset_idx'] = False
        elif action == 'reset':
            kwargs['reset_idx'] = True

        idx_list = [{"patron": sierra.Patron}]
        for idx, values in idx_list.items():
            if (action == 'initialize'
                and not self.es.indices.exists(idx)) \
                    or action != 'initialize':
                self.send_es_mapping({idx: values}, **kwargs)

    def get_es_mappings(self):
        """
        Returns the mapping definitions present in elasticsearch
        """

        es_mappings = json.loads(requests.get(self.mapping_url).text)
        es_mappings = {"_".join(key.split("_")[:-1]): value['mappings'] \
                       for key, value in es_mappings.items()}
        return es_mappings

    @staticmethod
    def mapping_ref(es_mappings):
        """
        Returns a dictionary of mappings and the field names in dot notation

        args:
            mappings: es mapping definitions to parse
        """

        new_map = {}
        for key, value in es_mappings.items():
            for sub_key, sub_value in value.items():
                new_map["/".join([key, sub_key])] = \
                        mapping_fields(sub_value['properties'])
        return new_map

    @staticmethod
    def key_data_map(source, mapping, parent=[]):
        rtn_obj = {}
        if isinstance(source, dict):
            for key, value in source.items():

                new_key = parent + [key]
                new_key = ".".join(new_key)
                rtn_obj.update({new_key: {'mapping':mapping.get(new_key)}})
                if isinstance(value, list):
                    value = value[0]
                    rtn_obj.update(EsMappings.key_data_map(value,
                                                           mapping,
                                                           [new_key]))
                    if isinstance(value, dict):
                        rtn_obj[new_key]['data'] = "%s ...}" % str(value)[:60]
                elif isinstance(value, dict):
                    rtn_obj.update(EsMappings.key_data_map(value,
                                                           mapping,
                                                           [new_key]))
                    rtn_obj[new_key]['data'] = "%s ...}" % str(value)[:60]
                else:
                    rtn_obj[new_key]['data'] = value
        elif isinstance(source, list):
            rtn_obj.update(EsMappings.key_data_map(source[0],
                                                   mapping,
                                                   parent))
        else:
            rtn_obj = {"".join(parent): {
                            'data': source,
                            'mapping': mapping.get("".join(parent))}}
            # pdb.set_trace()
        return rtn_obj

    def sample_data_convert(self, data, es_index, doc_type):
        maps = self.mapping_ref(self.get_es_mappings())
        if data.get('hits'):
            new_data = data['hits']['hits'][0]['_source']
        elif data.get('_source'):
            new_data = data['_source']
        conv_data = self.key_data_map(new_data,
                                      maps["%s/%s" % (es_index, doc_type)])
        conv_data = [(key,
                      str(value['mapping']),
                      str(value['data']),)
                     for key, value in conv_data.items()]
        conv_data.sort(key=lambda tup: es_field_sort(tup[0]))
        return conv_data

    # def sample_data_map(es_url):
    #
    #     maps = mapping_ref(es_url)
    #     rtn_obj = {}
    #     for path, mapping in maps.items():
    #         url = "/".join(["{}:9200".format(es_url), path, '_search'])
    #         sample_data = json.loads(requests.get(url).text)
    #         sample_data = sample_data['hits']['hits'][0]['_source']
    #         conv_data = key_data_map(sample_data, mapping)
    #
    #         rtn_obj[path] = [(key, str(value['mapping']), str(value['data']),) \
    #                          for key, value in conv_data.items()]
    #         rtn_obj[path].sort(key=lambda tup: es_field_sort(tup[0]))
    #     return rtn_obj


def es_field_sort(fld_name):
    """ Used with lambda to sort fields """
    parts = fld_name.split(".")
    if "_" not in parts[-1]:
        parts[-1] = "_" + parts[-1]
    return ".".join(parts)


def mapping_fields(mapping, parent=[]):
    """
    reads an elasticsearh mapping dictionary and returns a list of fields
    cojoined with a dot notation

    args:
        obj: the dictionary to parse
        parent: name for a parent key. used with a recursive call
    """
    rtn_obj = {}
    for key, value in mapping.items():
        new_key = parent + [key]
        new_key = ".".join(new_key)
        rtn_obj.update({new_key: value.get('type')})
        if value.get('properties'):
            rtn_obj.update(mapping_fields(value['properties'], [new_key]))
        elif value.get('fields'):
            rtn_obj.update(mapping_fields(value['fields'], [new_key]))
            rtn_obj[new_key] = [rtn_obj[new_key]] + \
                    list(value['fields'].keys())
    return rtn_obj


def dict_fields(obj, parent=[]):
    """
    reads a dictionary and returns a list of fields conjoined with a dot
    notation

    args:
        obj: the dictionary to parse
        parent: name for a parent key. used with a recursive call
    """
    rtn_obj = {}
    for key, value in obj.items():
        new_key = parent + [key]
        new_key = ".".join(new_key)
        if isinstance(value, list):
            if value:
                value = value[0]
        if isinstance(value, dict):
            rtn_obj.update(dict_fields(value, [new_key]))
        else:
            rtn_obj.update({new_key: value})
    return rtn_obj
