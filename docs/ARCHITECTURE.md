# Enterprise evolution architecture

The local demo is deliberately simple enough to run. A production evolution can split the modular API into:

- Spring Boot: loan/customer/workflow transactional services
- FastAPI: RAG, document intelligence, model gateway and agent services
- Node.js: notification/integration gateway
- Kafka: workflow events and service communication
- Oracle/PostgreSQL: system of record
- Redis: caching/idempotency
- OpenSearch: policy/document indexing and hybrid retrieval
- Qdrant/Chroma: vector retrieval
- Azure Document Intelligence: OCR/extraction
- Azure OpenAI / Claude / Gemini / Llama: routed model providers
- OAuth2/OIDC + MFA + RBAC: enterprise identity
- Prometheus/Grafana/OpenTelemetry: metrics and tracing
- Kubernetes/Jenkins: deployment and CI/CD

## AI safety / governance

AI output should remain advisory for regulated lending decisions. Persist source evidence, prompts/model versions, evaluation results and human decisions. Add policy constraints, PII controls, model monitoring, bias/fair-lending review and jurisdiction-specific compliance before real use.
