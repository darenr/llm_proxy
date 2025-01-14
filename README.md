# llm_proxy
Route LLM traffic between model endpoints, provide payload based routing and telemetry

```shell

curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"field1": "value1", "other_data": "some_value"}' \
  http://localhost:8080/api/endpoint
```