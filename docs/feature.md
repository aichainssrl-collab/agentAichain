**Task List – Portare AgentAichain a "Top Tier"** (superiore a OpenClaw)
Obiettivi: integrazione AGNO al 100%, attivazione Neo4j, deployment GCP solido, security e scalabilità enterprise.

Stato audit: 2026-04-05

---

## 🎯 Categoria: Backend Core

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| B1 | **Tenant Scoping Automatico** – Dependency FastAPI per filtrare query per `tenant_id` | Alta | **Parz.** | `TenantContext` in `tenant_context.py`, `set_current_tenant` in `auth.py`, manca `get_tenant_session` |
| B2 | **Middleware Tenant Context** – Estrarre tenant da API key/JWT | Alta | **Parz.** | Tenant estratto in auth dependency, manca middleware dedicato |
| B3 | **Rivedere tutti gli endpoint** – Sostituire filtri manuali con dependency automatica | Media | **Parz.** | Query ancora filtrate manualmente in molti endpoint |
| B4 | **Integrità referenziale Agent-AIModel** – FK `aimodel_id` con cascade | Alta | **Fatto** | `Agent.aimodel_id` FK implementata, migrazione `02322111f175` |
| B5 | **Migrazione Alembic** – Alter colonne `agents.model` → `aimodel_id` | Alta | **Fatto** | File `02322111f175_agent_aimodel_id.py` con up/down |
| B6 | **Implementare Neo4j** – Driver e connessione iniziale | Alta | **Fatto** | `core/neo4j_db.py` AsyncGraphDatabase, configured in settings e init in main.py |
| B7 | **Audit Logging strutturato** – Log azioni con tenant/user/timestamp JSON | Alta | *Non iniziato* | Solo structlog generale, nessun audit trail dedicato |
| B8 | **Rate Limiting per tenant** – Redis-based limiting | Alta | *Non iniziato* | |
| B9 | ~~**API Versioning**~~ `/api/v1/` | Alta | **Fatto** | Tutti i router con prefix `/api/v1/` in `main.py` |
| B10 | **Request ID tracing** – `X-Request-ID` middleware | Media | *Non iniziato* | |
| B11 | **Dockerfile multi-stage** – Ottimizzare per prod (non-root, distroless) | Alta | *Non iniziato* | Dockerfile single-stage: build e runtime nello stesso stage |

---

## 🤖 Categoria: AGNO Integration (100%)

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| A1 | ~~**Client AGNO ufficiale**~~ SDK Python `agno` con fallback HTTP | Alta | **Fatto** | `from agno.agent import Agent` in `agno_wrapper.py`, fallback httpx se SDK non disponibile |
| A2 | ~~**Configurazione multi-provider**~~ OpenAI, Anthropic, Google, Ollama via adapter | Alta | **Fatto** | `AIModel.provider` con 5 provider, mapping in `_get_agno_model()` |
| A3 | **Supporto Universale Modelli LLM** – Aggiunta dinamica di qualsiasi modello | Alta | **Parz.** | Fallback per provider sconosciuti (`agno_wrapper.py` righe 88-95), modelli CRUD via API |
| A4 | ~~**Streaming risposte**~~ SSE per run in tempo reale | Media | **Fatto** | `/api/v1/runs/agent/{agent_id}/stream` con `StreamingResponse`, `text/event-stream` |
| A5 | ~~**Cost & Token tracking**~~ Calcolo token/costo per provider | Alta | **Fatto** | `tokens_used` e `cost` in Run model, estrazione metriche in wrapper |
| A6 | **Tool calling standardizzato** – Interface tools + wrapper esterni | Alta | **Parz.** | Tools come lista JSON in Agent model, mapping DuckDuckGo in wrapper, manca interface formale |
| A7 | **Agent template system** – Template riutilizzabili con versioning | Media | *Non iniziato* | |
| A8 | **Test di carico AGNO** – Simulare carico con mock provider | Media | **Parz.** | `load-tests/load_test.py` presente (3000 req, 100 RPS) |

---

## 🕸️ Categoria: Neo4j (Graph Database)

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| N1 | ~~**Integrazione Neo4j**~~ Driver e connection pooling | Alta | **Fatto** | `neo4j_db.py` con AsyncGraphDatabase |
| N2 | ~~**Modelli Graph**~~ Tenant, Agent, Team nodes e relationships | Alta | **Fatto** | Sync functions per Tenant, Agent, Team |
| N3 | ~~**Synch DB relazionale → Graph**~~ Update async su create/update | Media | **Fatto** | Background tasks in `agents.py` righe 56-58 |
| N4 | ~~**Query grafo per recommendation**~~ "agenti con tool simili" | Bassa | **Fatto** | `get_similar_agents()` implementato |
| N5 | ~~**Migrazione dati iniziale**~~ Script popolare graph da DB | Media | **Fatto** | Schema init e constraints in `neo4j_db.py` righe 8-33 |
| N6 | ~~**Index e constraint**~~ Indici su `tenant_id` | Media | **Fatto** | Implementati in schema init |

---

## ☁️ Categoria: GCP Deployment (Terraform)

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| G1 | **Cloud Run per Celery workers** – Servizi separati per worker | Alta | *Parz.* | `terraform/gcp/` esiste ma manca Cloud Run specifico worker |
| G2 | **Container image multi-stage** – Ottimizzare Dockerfile | Alta | *Non iniziato* | Vedi B11 |
| G3 | **Cloud SQL vs Socket** – Cloud SQL Auth proxy | Alta | *Non iniziato* | |
| G4 | **Memorystore (Redis)** – Redis con password e network privata | Alta | *Non iniziato* | |
| G5 | **Secret Manager** – Spostare secrets in Secret Manager | Alta | *Non iniziato* | |
| G6 | **Cloud Build triggers** – CI/CD su push main | Media | *Non iniziato* | |
| G7 | **Cloud Monitoring & Alerting** – Dashboard metrics | Alta | *Non iniziato* | |
| G8 | **Cloud Scheduler** – Task periodici cleanup/stats | Media | *Non iniziato* | |
| G9 | **IAM Service Account least privilege** | Alta | *Non iniziato* | |
| G10 | **Budget e billing alerts** | Media | *Non iniziato* | |
| G11 | **Multi-region (futuro)** | Bassa | *Non iniziato* | |

---

## 🔒 Categoria: Security & Compliance

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| S1 | **Security headers** – CSP, HSTS via middleware | Media | *Non iniziato* | Solo CORS middleware attivo |
| S2 | **Threat Model** – `THREAT_MODEL.md` con STRIDE | Bassa | *Non iniziato* | |
| S3 | **Penetration test** – OWASP ZAP + fixes | Alta | *Non iniziato* | |
| S4 | **GDPR compliance** – Data export/delete per tenant | Alta | *Non iniziato* | |
| S5 | **Secrets scanning** – `detect-secrets` in CI | Alta | *Non iniziato* | |
| S6 | **Enforce HTTPS** – Redirect HTTP→HTTPS + HSTS | Alta | *Non iniziato* | |
| S7 | **API key rotation** – Rotazione con coesistenza | Media | **Parz.** | `expires_at` e `is_expired()` in ApiKey model, manca flusso rotazione |

---

## 📈 Categoria: Monitoring & Observability

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| O1 | ~~**Structured logging centralizzato**~~ JSON logs con tenant/user | Alta | **Fatto** | `structlog` configurato in `main.py`, JSON renderer |
| O2 | **Metrics Prometheus** – `/metrics` endpoint | Alta | *Non iniziato* | `prometheus-client` in requirements ma nessun endpoint |
| O3 | **Distributed Tracing** – OpenTelemetry | Media | *Non iniziato* | |
| O4 | **Alerting** – Error rate, latency, worker queue | Alta | *Non iniziato* | |
| O5 | **Dashboard Grafana (facoltativo)** | Bassa | *Non iniziato* | |

---

## 🧪 Categoria: Testing & Quality

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| T1 | **Increase test coverage** – ≥80% | Alta | **Parz.** | 8 file test (4 unit, 4 integration), coverage configurato in pyproject.toml, ma `test_agno_wrapper` fallisce senza `agno` installato |
| T2 | **Property-based testing** – `hypothesis` | Media | *Non iniziato* | |
| T3 | **Contract testing** – OpenAPI retrocompatibilità | Media | *Non iniziato* | |
| T4 | **Load testing** – 1000 tenant con Locust/k6 | Alta | **Parz.** | `load-tests/load_test.py` con 3000 req / 100 RPS |
| T5 | **Chaos engineering** | Bassa | *Non iniziato* | |
| T6 | **Frontend E2E** – Cypress/Playwright | Media | *Non iniziato* | |

---

## 🎨 Categoria: Frontend (già buono, migliorie)

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| F1 | **Real-time updates** – WebSocket/SSE per run status | Alta | *Parz.* | SSE endpoint esiste (A4), WebSocket da valutare |
| F2 | **Dark mode** | Bassa | *Non iniziato* | |
| F3 | **Internationalization** – i18n EN/IT | Media | *Non iniziato* | |
| F4 | **Offline indicator** | Bassa | *Non iniziato* | |
| F5 | **Cost analytics dashboard** | Media | *Non iniziato* | |
| F6 | **Bulk operations** | Bassa | *Non iniziato* | |

---

## 🚀 Categoria: DevOps & Automation

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| D1 | **pre-commit hooks** – black, ruff, mypy, detect-secrets | Alta | *Non iniziato* | |
| D2 | **Dependabot** – Auto-update dipendenze | Media | *Non iniziato* | |
| D3 | **Container scanning** – Snyk/Trivy in CI | Alta | *Non iniziato* | |
| D4 | **Blue-green deployment** – Zero-downtime deploy | Media | *Non iniziato* | |
| D5 | **Backup自动化** – Cloud SQL snapshot giornalieri | Alta | *Non iniziato* | |
| D6 | **Scalatura automatica** – Min/max instances | Alta | *Non iniziato* | |

---

## 📦 Categoria: AGNO & Tooling Specific

| ID | Task | Priorità | Stato | Note |
|----|------|----------|-------|------|
| T1 | **Document ingestion pipeline** – PDF/DOC, chunk, embed, Neo4j | Alta | *Non iniziato* | |
| T2 | **RAG retrieval tool** – Vector + graph search | Alta | *Non iniziato* | |
| T3 | **Multi-provider fallback** – Fallback a OpenAI se AGNO fallisce | Media | *Non iniziato* | |
| T4 | **Agent marketplace** – Catalogo agenti predefiniti | Bassa | *Non iniziato* | |

---

## 📋 Ordine di esecuzione suggerito

1. Blocco **Backend Core** (B1-B10, B11) – Fondamentali per stabilità e sicurezza
2. Blocco **AGNO Integration** (A1-A8) – Per usare AGNO al 100% con cost tracking e streaming
3. Blocco **Neo4j** (N1-N6) – Attendere che AIModel e agenti siano solidi
4. Blocco **GCP Deployment** (G1-G11) – Solo dopo che i test Docker passano
5. Blocco **Security & Monitoring** (S1-S7, O1-O5) – In parallelo con GCP
6. Blocco **Frontend + DevOps** – Per completare l'esperienza utente e CI/CD

---

## 📊 Riepilogo complessivo

| Stato | Count | % |
|-------|-------|---|
| **Fatto** | 14 | ~32% |
| **Parzialmente fatto** | 9 | ~21% |
| **Non iniziato** | 21 | ~48% |

**Totale task: 44**

### Categorie per maturità

| Categoria | % Fatto |
|-----------|---------|
| Neo4j | **100%** ✅ |
| AGNO Integration | **~65%** 🟡 |
| Backend Core | **~40%** 🟡 |
| Testing | **~20%** 🔴 |
| Security | **~5%** 🔴 |
| Monitoring | **~15%** 🔴 |
| GCP Deployment | **~5%** 🔴 |
| DevOps | **0%** 🔴 |
| Frontend | **~5%** 🔴 |

---

## ✅ Checklist pre-GCP (aggiornata)

- [ ] Tutti i test unit + integration passano (fix `test_agno_wrapper` senza `agno` locale)
- [ ] Copertura ≥80% (attualmente <50%)
- [x] Dipendenza Neo4j installata e configurata
- [ ] Tenant scoping automatico completo (attualmente parziale)
- [x] AGNO wrapper funzionante con SDK Python
- [x] Neo4j connesso e schema inizializzato
- [ ] Dockerfile multi-stage
- [x] Terraform boilerplate presente (`terraform/gcp/`)
- [ ] Cloud Run, Cloud SQL, Memorystore, Secret Manager Terraform
- [ ] Monitoring (Metrics, Alerting)
- [x] Structured logging JSON
- [ ] Rate limiting
- [ ] Audit log

Legenda update:
- ~~testi barrati~~ = task completati e rimossi dalla lista prioritaria
- **Fatto** = implementato e verificato
- **Parz.** = implementazione parziale con dettagli nelle note
- *Non iniziato* = da implementare
