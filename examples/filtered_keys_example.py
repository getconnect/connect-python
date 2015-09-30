from connect import security

key_definition = {
     "filters" : {
         'type': 'cycling'
         },
    "canQuery": True,
    "canPush": True
}

print security.encrypt_filtered_key(key_definition, 
                                    "00000000000000000000000000000000")