# llm_proxy
Route LLM traffic between model endpoints, provide payload based routing and telemetry

UNDER CONSTRUCTION

Still very much a work in progress, but the idea is to be able to route LLM traffic very efficiently based on 
a variety of ways, headers, payload, url.

```bash

curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"field1": "value1", "other_data": "some_value"}' \
  http://localhost:8080/api/endpoint
```