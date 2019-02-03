import unittest

from chplpatron.statistics import (esmappings,
                                   elasticsearchbase as es,
                                   esutilities as ut)
import chplpatron.sierra as sierra
from chplpatron.exceptions import *
import json


@unittest.skip
class TestConvertToEs(unittest.TestCase):

    def setUp(self):
        pass

    def test_lookup_name(self):
        result = sierra.lookup_by_name("Ztestd, Jess")
        # sierra.set_email("m@m.com", result['id'])
        pprint.pprint(result)
        patron = sierra.Patron(result)
        pprint.pprint(patron.to_dict())
        print("\n----------------------------------------------\n", patron.id)
        pprint.pprint(patron.to_es())
        es.EsBase(es_index="patron").save(json.dumps(patron.to_es()), id=patron.id)

    def tearDown(self):
        pass


@unittest.skip
class TestEsSetup(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_index(self):
        # esmappings.EsMappings().send_es_mapping({"index": "patron", "body": {}})
        result = sierra.APIS.patron(headers=sierra.get_headers(),
                                    params={'limit':25,
                                            'offset': 0,
                                            'fields':
                                                sierra.lookups.PatronFlds.list_all()})
        stop = False
        offset = 0
        limit = 100
        results = []
        while not stop:
            result = sierra.APIS.patron(headers=sierra.get_headers(),
                                        params={'limit': limit,
                                                'offset': offset,
                                                'fields':
                                        sierra.lookups.PatronFlds.list_all()})
            if not result.json().get("total"):
                stop = True
            else:
                offset += limit
                results.append(result.json())
            try:
                print(result.json().get("start"),
                      " - ",
                      result.json().get("start"))
            except:
                pass
        with open("paton_data.json", "w") as fo:
            fo.write(json.dumps(results))
        pass


@unittest.skip
class TestEsRecordLoad(unittest.TestCase):

    def setUp(self):
        pass

    def test_filter_deleted(self):
        with open("paton_data.json", "r") as fo:
            data = fo.read()
        data = json.loads(data)
        filtered = []
        worker = es.EsBase(es_index="patron")
        for batch in data:
            filtered += [sierra.Patron(entry).to_es()
                         for entry in batch.get("entries")]
        action_list = worker.make_action_list(filtered)
        worker.bulk_save(action_list)
            
                         # if not entry.get("deleted")]
        # patron = sierra.Patron(filtered[0]).to_es()
        # pprint.pprint(patron)

        # action_list = worker.make_action_list([filtered])

