# Guida agli Agenti (AGNO Integration)

Questa guida documenta il funzionamento del motore degli Agenti in AgentAichain e l'integrazione nativa con la libreria **AGNO**.

## Architettura Core

Il sistema si basa su tre modelli di database principali:
1. **AIModel**: Definisce il provider LLM (es. `openrouter`, `openai`, `ollama`), l'URL di base e la chiave API.
2. **Agent**: Rappresenta un'istanza operativa. È collegato a un `AIModel` tramite `aimodel_id` e contiene le istruzioni di sistema (`instructions`) e la lista degli strumenti abilitati (`tools`).
3. **Team**: Un gruppo di più `Agent` che collaborano per risolvere task complessi (supportato nativamente da AGNO tramite `Team`).

## Integrazione AGNO (`agno_wrapper.py`)

La logica di esecuzione è centralizzata in `agent_aichain/workers/agno_wrapper.py`.
Le classi `TenantAwareAgent` e `TenantAwareTeam` estendono le funzionalità native di AGNO per garantire:
- **Isolamento Tenant**: Ogni log, traccia o metadato generato dall'agente include il `tenant_id`.
- **Esecuzione Asincrona**: Le chiamate ad AGNO (che sono bloccanti) vengono avvolte in `loop.run_in_executor` per non bloccare l'Event Loop di FastAPI.
- **Fallback Locali**: Se una chiave API non è valida o il servizio è irraggiungibile (es. errori SSL), il wrapper implementa un fallback trasparente su `Ollama` (`http://host.docker.internal:11434` con modello `qwen3.5:latest`) per permettere lo sviluppo locale senza interruzioni.

## Strumenti (Tools) Supportati

Il mapping degli strumenti dal formato stringa del DB agli oggetti nativi AGNO avviene nel metodo `_get_agno_tools()`. 

Strumenti attualmente supportati:
- `duckduckgo` / `web_search`: Ricerca web (tramite `DuckDuckGoTools`)
- `calculator`: Operazioni matematiche (`CalculatorTools`)
- `python`: Esecuzione di codice Python sandboxato (`PythonTools`)
- `file`: Operazioni su file (`FileTools`)
- `wikipedia`: Ricerca enciclopedica (`WikipediaTools` - *richiede pacchetto `wikipedia`*)
- `yfinance`: Dati finanziari (`YFinanceTools` - *richiede pacchetto `yfinance`*)

*Se un pacchetto non è installato, il sistema logga un warning senza bloccare l'avvio dell'agente.*

## Flusso di Esecuzione

1. **API Call**: Il client chiama `/api/v1/runs/agent/{agent_id}` (o `/stream` per le risposte in tempo reale via SSE).
2. **Costruzione Agente**: `build_agno_agent` recupera l'Agente e il suo AIModel dal DB, istanzia il provider corretto (es. `OpenRouter` o `OpenAI`) iniettando dinamicamente la API key (non hardcoded nel codice) e mappa i tools richiesti.
3. **Esecuzione**: `TenantAwareAgent.run()` invia il payload.
4. **Streaming (Opzionale)**: Se viene chiamato l'endpoint stream, viene utilizzato il generatore nativo di AGNO per restituire i token in tempo reale tramite Server-Sent Events (SSE).

## Aggiungere nuovi Tools

Per aggiungere un nuovo tool:
1. Assicurarsi che il tool sia supportato da AGNO o crearlo custom.
2. Aggiungere il nome del tool (es. `github`) nel blocco `if/elif` in `_get_agno_tools` dentro `agno_wrapper.py`.
3. Importare e istanziare la classe del tool corrispondente.
4. Aggiungere eventuali dipendenze a `requirements.txt`.