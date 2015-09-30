# -*- coding: utf-8 -*-
from connect import security
import json

class TestFilteredKeys():
    def test_encrypt_and_decrypt_return_same_value(self):
        master_key = "00000000000000000000000000000000"
        filter_definition = {
            'filters': {
                'type': 'cycling'
            },
            'canQuery': True,
            'canPush': True
        }
        
        encrypted = security.encrypt_filtered_key(filter_definition,master_key)
        decrypted = security.decrypt_filtered_key(encrypted,master_key)

        expected_value = bytearray(json.dumps(filter_definition),"ascii")
        assert decrypted == expected_value