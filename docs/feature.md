**Task List – Portare AgentAichain a “Top Tier”** (superiore a OpenClaw)  
Obiettivi: integrazione AGNO al 100%, attivazione Neo4j, deployment GCP solido, security e scalabilità enterprise.

---

## 🎯 Categoria: Backend Core

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| B1 | **Tenant Scoping Automatico** – Implementare una dependency FastAPI che filtri automaticamente le query per `tenant_id` (es. `get_tenant_session`) | Alta | B2, B3 |
| B2 | **Middleware Tenant Context** – Aggiungere middleware per estrarre tenant da API key/JWT e impostare `current_tenant_id` in context var | Alta | B1 |
| B3 | **Rivedere tutti gli endpoint** – Sostituire i filtri manuali con la dependency automatica e assicurare copertura | Media | B1 |
| B4 | **Integrità referenziale Agent-AIModel** – Cambiare `Agent.model` (string) in FK `aimodel_id` con cascade o proteggere cancellazioni | Alta | B5, migrazione DB |
| B5 | **Migrazione Alembic** – Generare migration per alterare colonna `agents.model` → `aimodel_id` e popolare con join | Alta | B4 |
| B6 | **Rimuovere dipendenza Neo4j inutilizzata** – Eliminare `neo4j` da requirements.txt se non usata (o implementare) | Bassa | – |
| B7 | **Audit Logging strutturato** – Log di tutte le azioni (creazione, modifica, run) con tenant/user/timestamp in JSON a fini di conformità | Alta | B2 |
| B8 | **Rate Limiting per tenant** – Implementare limiting per API key/IP (es. 1000 req/min per tenant) con Redis storage | Alta | B2 |
| B9 | **API Versioning** – Introdurre prefisso `/api/v1/` e piano per v2, con deprecation headers | Media | – |
| B10 | **Request ID tracing** – Aggiungere `X-Request-ID` in middleware per correlare log through services (API → Celery) | Media | B2 |

---

## 🤖 Categoria: AGNO Integration (100%)

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| A1 | **Client AGNO ufficiale** – Sostituire chiamate HTTP raw con client Python `agno` (se disponibile) per type safety e retry | Alta | A2 |
| A2 | **Configurazione multi-provider** – Supportare non solo AGNO ma anche OpenAI, Anthropic, Google, Ollama via `AIModel.provider` + adapter pattern | Alta | B4 |
| A3 | **Retry & Circuit Breaker** – Implementare retry con backoff e circuit breaker per chiamate AGNO (o provider) | Alta | A1 |
| A4 | **Streaming risposte** – Aggiungere endpoint streaming SSE per run in tempo reale (per evitare polling) | Media | A1 |
| A5 | **Cost & Token tracking** – Calcolo precise dei token e costo per provider (usando `tiktoken` o equivalente) e salvataggio in `Run` | Alta | A2 |
| A6 | **Tool calling standardizzato** – Definire interface per tool (input schema, exec) e wrapper per tool esterni (Eurotrust QES, etc.) | Alta | A2 |
| A7 | **Agent template system** – Permettere template di agent riutilizzabili con placeholders e versioning | Media | A2 |
| A8 | **Test di carico AGNO** – Simulare carico con mock provider e verificare scaling workers Celery | Media | A1 |

---

## 🕸️ Categoria: Neo4j (Graph Database)

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| N1 | **Integrazione Neo4j** – Aggiungere driver `neo4j` (rimuovere commento) e connection pooling | Alta | N2, B2 |
| N2 | **Modelli Graph** – Definire schema: Tenant Node, Agent Node, Relationship `BELONGS_TO`, `USES_TOOL`, `RUNS` | Alta | N1 |
| N3 | **Synch DB relazionale → Graph** – Su create/update agent/team, aggiornare graph (async task) | Media | N2 |
| N4 | **Query grafo per recommendation** – Esempio: “trova agenti con tool simili” o “path tra agenti e tool” | Bassa | N2 |
| N5 | **Migrazione dati iniziale** – Script per popolare graph da DB esistente | Media | N2 |
| N6 | **Index e constraint** – Creare indici su `tenant_id` e proprietà per performance | Media | N2 |

---

## ☁️ Categoria: GCP Deployment (Terraform)

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| G1 | **Aggiungere Cloud Run per Celery workers** – Definire servizi Cloud Run separati per worker (ambiente `CELERY_WORKER=true`) | Alta | G2 |
| G2 | **Container image multi-stage** – Ottimizzare Dockerfile per prod (multi-stage, non-root, distroless) | Alta | – |
| G3 | **Cloud SQL vs Socket** – Configurare Cloud SQL Auth proxy (o IAM) per connessione sicura | Alta | G1 |
| G4 | **Memorystore (Redis)** – Provisioning Redis con password e network privata | Alta | G1 |
| G5 | **Secret Manager** – Spostare tutti i secrets (SECRET_KEY, DB_PASSWORD, AGNO_API_KEY) in Secret Manager | Alta | G1 |
| G6 | **Cloud Build triggers** – CI/CD automatico su push main (build, test, deploy) | Media | G2 |
| G7 | **Cloud Monitoring & Alerting** – Dashboard per latenza, error rate, RPS, Celery queue depth, Redis memory | Alta | G1 |
| G8 | **Cloud Scheduler per task periodici** – Per cleanup run vecchi, tenant stats, etc. | Media | G1 |
| G9 | **IAM Service Account least privilege** – Assegnare ruoli minimi (Cloud SQL Client, Secret Manager Reader) | Alta | G1 |
| G10 | **Budget e billing alerts** – Configurare budget in GCP Billing e notifiche | Media | G1 |
| G11 | **Multi-region (futuro)** – Piano per replicazione DB e Redis per enterprise tier | Bassa | G1 |

---

## 🔒 Categoria: Security & Compliance

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| S1 | **Helmet/Darkfeed** – Aggiungere security headers (CSP, HSTS) via middleware | Media | B2 |
| S2 | **Documentazione Threat Model** – Creare `THREAT_MODEL.md` con STRIDE | Bassa | – |
| S3 | **Penetration test** – Eseguire scan automatico (es. OWASP ZAP) e fixes | Alta | S1 |
| S4 | **GDPR compliance** – Implementare data export/delete per tenant (right to be forgotten) | Alta | B2 |
| S5 | **Secrets scanning** – Integrare `detect-secrets` in CI per bloccare commit con segreti | Alta | – |
| S6 | **Enforce HTTPS** – In produzione, forzare redirect HTTP→HTTPS e HSTS | Alta | G1 |
| S7 | **API key rotation** – Permettere rotazione chiavi con periodo di coesistenza | Media | B7 |

---

## 📈 Categoria: Monitoring & Observability

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| O1 | **Structured logging centralizzato** – Inviare logs a Cloud Logging con field standard (tenant_id, user_id, agent_id) | Alta | B2 |
| O2 | **Metrics Prometheus** – Esporre metriche (`/metrics`) per: request latency, celery tasks, DB pool, Redis hits | Alta | B2 |
| O3 | **Distributed Tracing** – OpenTelemetry integration per trace through API→Celery→AGNO | Media | O1 |
| O4 | **Alerting** – Configurare alert per: error rate >1%, latency >200ms, worker down, queue backlog >100 | Alta | G7 |
| O5 | **Dashboard Grafana (facoltativo)** – Se non si usa Cloud Monitoring, esportare metriche a Grafana | Bassa | O2 |

---

## 🧪 Categoria: Testing & Quality

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| T1 | **Increase test coverage** – Portare coverage a ≥80% (attualmente ~60%?) | Alta | – |
| T2 | **Property-based testing** – Usare `hypothesis` per test ai boundary conditions | Media | T1 |
| T3 | **Contract testing** – Definire contratti OpenAPI e verificare retrocompatibilità in CI | Media | B9 |
| T4 | **Load testing** – Script per simulare 1000 tenant concorrenti con Locust/k6 | Alta | A3 |
| T5 | **Chaos engineering** – Test di resilienza: kill DB, Redis, AGNO timeout | Bassa | O4 |
| T6 | **Frontend E2E** – Test con Cypress/Playwright per flusso completo | Media | – |

---

## 🎨 Categoria: Frontend (già buono, migliorie)

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| F1 | **Real-time updates** – WebSocket/SSE per run status instead of polling | Alta | A4 |
| F2 | **Dark mode** – Supporto tema scuro con Tailwind | Bassa | – |
| F3 | **Internationalization** – i18n per EN/IT | Media | – |
| F4 | **Offline indicator** – Mostrare status connessione e scadenza token | Bassa | – |
| F5 | **Cost analytics dashboard** – Grafici costo per tenant/agent nel tempo | Media | A5 |
| F6 | **Bulk operations** – Seleziona multipla agent/team per delete/export | Bassa | – |

---

## 🚀 Categoria: DevOps & Automation

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| D1 | **pre-commit hooks** – Installare black, ruff, mypy, secrets scan | Alta | – |
| D2 | **Dependabot** – Abilitare auto-update dipendenze su GitHub | Media | – |
| D3 | **Container scanning** – Snyk/Trivy in CI per vulnerabilities | Alta | G6 |
| D4 | **Blue-green deployment** – Zero-downtime deploy su Cloud Run (traffic splitting) | Media | G1 |
| D5 | **Backup自动化** – Snapshot giornalieri Cloud SQL e export Redis | Alta | G1 |
| D6 | **Scalatura automatica** – configurare min/max instances per API e worker in base al carico | Alta | G1 |

---

## 📦 Categoria: AGNO & Tooling Specific (per uso Aichain)

| ID | Task | Priorità | Dipendenze |
|----|------|----------|------------|
| T0 | **Eurotrust QES tool** – Implementare tool per firma digitale via API Eurotrust (wrapper) | Alta | A6 |
| T1 | **Document ingestion pipeline** – Tool per caricare PDF/DOC, chunk, embed (usando embedding model) e salvare in Neo4j | Alta | N2, A6 |
| T2 | **RAG retrieval tool** – Tool per cercare documenti simili nel graph (vector + graph) | Alta | N2, T1 |
| T3 | **Multi-provider fallback** – Se AGNO fallisce, fallback a OpenAI diretto (configurabile) | Media | A2 |
| T4 | **Agent marketplace** – Catalogo di agent predefiniti che i tenant possono istanziare | Bassa | A7 |

---

## 📋 Ordine di esecuzione suggerito

1. Blocco **Backend Core** (B1–B10) – Fondamentali per stabilità e sicurezza  
2. Blocco **AGNO Integration** (A1–A8) – Per usare AGNO al 100% con cost tracking e streaming  
3. Blocco **Neo4j** (N1–N6) – Attendere che `AIModel` e agenti siano solidi  
4. Blocco **GCP Deployment** (G1–G11) – Solo dopo che i test Docker passano (vedi `run_docker_tests.sh`)  
5. Blocco **Security & Monitoring** (S1–S7, O1–O5) – In parallelo con GCP  
6. Blocco **Frontend + DevOps** – Per completare l’esperienza utente e CI/CD  

---

## ✅ Checkpoint finale prima GCP

- [ ] Tutti i test unit + integration passano in Docker  
- [ ] Copertura ≥80%  
- [ ] Nessuna dipendenza inutilizzata (rimosso `neo4j` se non usata)  
- [ ] Tenant scoping automatico implementato e verificato  
- [ ] AGNO wrapper con retry e cost tracking funzionante  
- [ ] Neo4j connesso e dati di esempio presenti  
- [ ] Dockerfile multi-stage pronto  
- [ ] Terraform include API + worker + Redis + Cloud SQL + Secret Manager  
- [ ] Monitoring configured (Cloud Logging, Metrics, Alerting)  
- [ ] Rate limiting attivo  
- [ ] Audit log abilitato e testato  

---

Vuoi che inizi a implementare uno di questi task (es. B1 Tenant Scoping Automatico) o preferisci prima eseguire i test Docker per validare la base attuale?