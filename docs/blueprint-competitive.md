```markdown
# AgentAichain – Feature Blueprint & Competitive Analysis

**Obiettivo:** Costruire una piattaforma AI agent orchestration superiore a OpenClaw e competitive con Venn.ai  
**Data:** 2026-04-05  
**Versione:** 1.0

---

## 📑 Indice

1. [Panoramica](#panoramica)
2. [Feature CORE – Già implementate](#feature-core)
3. [Feature MANCANTI – Gap vs Venn.ai](#feature-mancanti)
4. [Architettura Tool System](#architettura-tool-system)
5. [Integrazioni Richieste (Connectors)](#integrazioni-richieste)
6. [Sicurezza e Controllo](#sicurezza-e-controllo)
7. [Monitoring e Observability](#monitoring-e-observability)
8. [Roadmap Prioritaria](#roadmap-prioritaria)
9. [Checklist di Complettanza](#checklist-di-complettanza)

---

## 🎯 Panoramica

AgentAichain è una piattaforma **multi-tenant** per orchestrazione di agenti AI, con:
- FastAPI backend (async)
- Celery workers per task lunghi
- PostgreSQL + Redis
- Frontend React+TypeScript
- Supporto AGNO (attualmente via HTTP wrapper)
- Deployment su GCP (Cloud Run, Cloud SQL, Memorystore)

**Visione:** Abilitare le aziende a collegare i propri agenti AI agli strumenti di lavoro (email, CRM, fogli di calcolo, git, etc.) con **controllo granulare** e **audit completo**.

---

## ✅ Feature CORE – Già implementate

| Feature | Status | Note |
|---------|--------|------|
| Multi-tenancy | ✅ | Tenant isolation via `tenant_id` in tutte le tabelle |
| Autenticazione | ✅ | API Key + JWT (OAuth2 password) |
| Agent Management | ✅ | CRUD agenti con ruoli, modelli, tool, istruzioni |
| Team Collaboration | ✅ | Gruppi di agenti, modalità coordinate |
| Async Execution | ✅ | Celery workers, task `run_agent_task`, `run_team_task` |
| Run Tracking | ✅ | Storico esecuzioni con status, output, tokens, cost |
| FastAPI REST API | ✅ | Endpoint completi, OpenAPI docs (`/docs`) |
| Docker Compose | ✅ | Postgres, Redis, API, Celery, Flower |
| React Frontend | ✅ | Dashboard, Agents, Teams, Runs, API Keys, Settings |
| GCP Terraform | ✅ | Cloud Run, Cloud SQL, Memorystore (base) |
| Alembic Migrations | ✅ | Database migrations |
| Structured Logging | ✅ | JSON logs via structlog |
| Health Check | ✅ | `/health` endpoint |
| Load Test | ✅ | 1862 RPS health, 501 RPS agents list |
| Audit DB | ✅ | Run records completi (ma manca audit logging per azioni amministrative) |

---

## ⚠️ Feature MANCANTI – Gap vs Venn.ai

| Categoria | Feature | Priorità | Motivazione |
|-----------|---------|----------|-------------|
| **Tool System** | Registry DB per tool | P0 | Serve per gestire tool Disponibili e authorization |
| | Executor sandboxed | P0 | Esecuzione sicura di codice arbitrario (PDF, Git, etc.) |
| | Permission per-tool per tenant | P0 | Controllo granulare (es. Gmail: solo read) |
| **Integrazioni** | Google Workspace (Gmail, Calendar, Drive, Docs, Sheets) | P1 | Core per produttività |
| | Slack | P1 | Comunicazione team |
| | Notion | P1 | Documentazione/conoscenza |
| | Salesforce/HubSpot | P1 | CRM |
| | QuickBooks/Xero | P1 | Fatturazione |
| | GitHub/GitLab | P1 | Code management |
| | Asana/Jira | P1 | Project tracking |
| | Dropbox/OneDrive | P2 | File storage |
| | Shopify/Stripe | P2 | E-commerce |
| | Zoom | P2 | Meeting |
| **Document Processing** | PDF Reader (testo + OCR) | P0 | Input comune |
| | Excel (.xlsx) Reader | P0 | Fogli di calcolo |
| | CSV Parser | P0 | Dati tabellari |
| | Audio Transcription (Whisper) | P1 | Voce → testo |
| | Text-to-Speech | P2 | Accessibility/automazione |
| | Web Scraper (BS4) | P1 | Estrazione dati web |
| | Dynamic Scraper (Playwright) | P2 | Siti JS-heavy |
| **Version Control** | Git Operations (clone, commit, push, diff) | P1 | Automazione sviluppo |
| | Repository Search | P2 | Cerca codice in repo |
| **Data Transformation** | JSON ↔ CSV/Excel converter | P1 | Integrazione dati |
| | Data validator (JSON Schema) | P2 | Qualità dati |
| | Aggregator (groupby, sum) | P2 | Analisi rapida |
| **File System** | Local file reader (sandboxed) | P0 | Accesso file uploadati |
| | Cloud Storage (GCS, S3) | P1 | File remoti |
| **Security** | OAuth2 connectors (Google, Slack, etc.) | P1 | Auth sicura per integrazioni |
| | Secrets management per tenant | P1 | Credenziali archiviate in Secret Manager |
| | Rate limiting per tenant/tool | P0 | Prevenire abuse |
| | GDPR: data export/delete | P1 | Compliance |
| **Monitoring** | Activity logs per tool call | P0 | Audit trail |
| | Prometheus metrics per tool usage | P1 | Osservabilità |
| | Alerting per errori tool | P2 | Produttività |
| **User Experience** | Universal URL (come Venn) | P1 | Collegamento AI facile |
| | Real-time updates (SSE/WebSocket) | P1 | Stato run in tempo reale |
| | Cost analytics dashboard | P2 | Visibilità costo AI |
| | Dark mode, i18n | P2 | UX |

---

## 🧩 Architettura Tool System

### 1. Tool Registry (DB Model)

```python
class Tool(Base):
    __tablename__ = "tools"

    id: int (PK)
    name: str (unique)  # e.g. "pdf_reader", "gmail_send"
    description: str  # per LLM (cosa fa)
    module_path: str  # Python path, e.g. "agent_aichain.tools.pdf.read"
    function_name: str  # funzione da chiamare
    parameters_schema: JSON  # JSON Schema per validazione input
    tenant_id: int (FK, nullable=True)  # null = global tool
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    # Relationships
    tenant = relationship("Tenant", back_populates="tools")
    agents = relationship("Agent", secondary=agent_tools, back_populates="tools")
```

### 2. Tool Executor (Worker)

```python
async def execute_tool(tool_name: str, arguments: dict, tenant_id: int, user_id: int) -> dict:
    # 1. Recupera tool dal DB (check exists, active, tenant allowed)
    tool = await get_tool(tool_name, tenant_id)
    if not tool:
        raise ToolNotFoundError()

    # 2. Validazione argomenti contro parameters_schema (jsonschema)
    validate(instance=arguments, schema=tool.parameters_schema)

    # 3. Import dinamico modulo e funzione
    module = importlib.import_module(tool.module_path)
    func = getattr(module, tool.function_name)

    # 4. Sandbox: limitare import, filesystem, rete (pool di process? docker?)
    #    Per ora, esecuzione nello stesso processo (ATTENZIONE: security!)
    #    Futuro: eseguire in worker isolato con risorse limitate.

    # 5. Esecuzione con timeout
    try:
        result = await asyncio.wait_for(func(**arguments), timeout=TOOL_TIMEOUT)
    except asyncio.TimeoutError:
        raise ToolTimeoutError()

    # 6. Audit log
    await log_audit(
        tenant_id=tenant_id,
        user_id=user_id,
        action="tool_execute",
        resource=tool_name,
        details={"arguments": arguments, "result_hash": hash(result)},
        duration_ms=...
    )

    return {"result": result, "tool": tool_name}
```

### 3. Registrazione Tool al Agent

Quando crei un Agent, selezioni i tool disponibili dalla registry (globali + tenant-specific). Questi tool names vengono passati ad AGNO (o al tuo wrapper) perché li renda disponibili per function calling.

---

## 🔌 Integrazioni Richieste (Connectors)

Ogni connector è un **tool** (o set di tools) che interagisce con un servizio esterno via REST API/OAuth.

### Pattern comune:

1. **OAuth2 flow** – L’utente (tenant admin) autorizza Venn-style: una volta sola, ottieni refresh token, memorizzato in Secret Manager (per tenant).
2. **Tool functions** – Un modulo Python con funzioni: `gmail_list_drafts()`, `gmail_send_draft()`, `slack_post_message()`, ecc.
3. **Parameters schema** – JSON Schema che descrive input (es. `to`, `subject`, `body` per email).
4. **Rate limiting** – Rispettare API limits (usare Redis counters).
5. **Error handling** – Trasformare API errors in messaggi chiari.

### Lista connectors (priorità)

| Connector | Tools principali | Auth | Priorità |
|-----------|------------------|------|----------|
| Google Workspace | gmail_list, gmail_send, gdrive_upload, gsheets_update, gcalendar_create | OAuth2 | P1 |
| Slack | slack_post_message, slack_search, slack_list_channels | Bot token | P1 |
| Notion | notion_query_db, notion_create_page, notion_update | OAuth2 | P1 |
| GitHub | git_clone, git_commit, git_push, git_create_pr | OAuth2/App | P1 |
| GitLab |Simile a GitHub | OAuth2 | P1 |
| Jira | jira_create_issue, jira_search, jira_transition | OAuth2 | P1 |
| Asana | asana_create_task, asana_update | OAuth2 | P1 |
| Salesforce | sf_query, sf_create_record, sf_update | OAuth2 | P1 |
| QuickBooks | qb_invoice_list, qb_create_invoice | OAuth2 | P1 |
| HubSpot | hs_create_contact, hs_log_activity | OAuth2 | P1 |
| Shopify | shopify_order_list, shopify_product_update | Private app | P2 |
| Stripe | stripe_create_payment_intent, stripe_refund | API key | P2 |
| Dropbox | dropbox_upload, dropbox_list_folder | OAuth2 | P2 |
| Zoom | zoom_create_meeting, zoom_list_participants | OAuth2/JWT | P2 |

---

## 🔐 Sicurezza e Controllo

### 1. Permission System per-Tool

- Ogni tenant ha una **policy** che elenca quali tool sono abilitati e con quali vincoli.
- Esempio policy (JSON):

```json
{
  "tools": {
    "gmail_send": {
      "allowed": true,
      "max_recipients": 10,
      "allowed_domains": ["@aichain.solutions"]
    },
    "github_push": {
      "allowed": false
    }
  }
}
```

- Il Tool Executor deve verificare la policy prima di eseguire.

### 2. Secrets Management

- Credenziali OAuth (refresh token, access token) salvate in **GCP Secret Manager** (o HashiCorp Vault) **per tenant**.
- Accesso ai secret solo dal worker (service account con ruolo `Secret Manager Secret Accessor`).
- Rotazione automatica access token (refresh).

### 3. Rate Limiting

- Redis sliding window per `(tenant_id, tool_name)`.
- Configurabile via policy (max calls per minute).

### 4. Sandboxing

- Esecuzione tool in **container Docker separati** per tenant? (overhead)
- Almeno, usare `multiprocessing` con `resource.setrlimit` per limitare CPU/memory.
- Block access a file system al di fuori di `/data/tenant_{id}/`.

### 5. Audit Logging strutturato

```json
{
  "timestamp": "2026-04-05T14:19:00Z",
  "tenant_id": 42,
  "user_id": 123,
  "action": "tool_execute",
  "tool": "gmail_send",
  "input": {"to": "client@example.com", "subject": "Hello"},
  "output_status": "success",
  "duration_ms": 450,
  "error": null,
  "request_id": "req-abc123"
}
```

Loggare in **Cloud Logging** con etichette (`tenant_id`, `tool`) per filtra.

---

## 📊 Monitoring e Observability

| Metric | Recommended | Why |
|--------|-------------|-----|
| `tool_calls_total` | Counter (labels: tenant_id, tool, status) | Track usage |
| `tool_duration_seconds` | Histogram (labels: tool) | Performance |
| `celery_queue_depth` | Gauge (queue name) | Worker health |
| `api_request_duration_seconds` | Histogram (endpoint, method, status) | API latency |
| `api_requests_total` | Counter (endpoint, status) | Throughput |
| `rate_limit_rejections_total` | Counter (tenant_id, tool) | Abuse detection |
| `audit_log_entries_total` | Counter (action) | Compliance |

**Alerting:**
- Tool error rate >5% in 5 min
- Celery queue backlog >100
- Worker process down
- API 5xx error rate >1%

---

## 🗺️ Roadmap Prioritaria (8 settimane)

### Settimana 1–2: Tool Framework Foundation

- [ ] Design Tool Registry DB (alembic migration)
- [ ] Implement Tool Executor (basic, no sandbox yet)
- [ ] Validazione input con JSON Schema
- [ ] Audit logging per tool calls
- [ ] Rate limiting Redis (sliding window)
- [ ] Test: PDF Reader tool (`pymupdf`)
- [ ] Test: CSV Reader tool (`pandas`)
- [ ] Test: HTTP Client tool (`httpx`)

### Settimana 3–4: Integrazioni Core + Auth

- [ ] OAuth2 framework per connectors (Google, Slack, GitHub)
- [ ] Google Workspace connector: Gmail (list, send), Drive (upload), Sheets (update)
- [ ] Slack connector: post_message, search
- [ ] GitHub connector: clone, commit, push, create PR
- [ ] Frontend: UI per grant OAuth permissions (tenant settings)
- [ ] Tool permission policy (per tenant) CRUD
- [
...(truncated)...