from coda_integration import CodaIntegration

coda = CodaIntegration()
# Tente buscar qualquer registro para ver se a conexão funciona
print(coda._make_request('GET', f'docs/{coda.doc_id}'))
