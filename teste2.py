from coda_integration import CodaIntegration

coda = CodaIntegration()
endpoint = f'docs/{coda.doc_id}/tables/{coda.table_id}/rows'
params = {'useColumnNames': True, 'limit': 10}
response = coda._make_request('GET', endpoint, params=params)
print(response)
