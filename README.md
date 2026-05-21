# fiap-hackathon-upload-service

Responsável por receber arquivos de diagramas de arquitetura, validá-los, armazená-los no MinIO e enfileirá-los no RabbitMQ para processamento assíncrono.

## Responsabilidade

- Validar tipo de arquivo por magic bytes (não confia no Content-Type declarado pelo cliente)
- Rejeitar arquivos acima do limite configurado
- Salvar o arquivo no MinIO com nome baseado em UUID (sem expor nome original)
- Registrar a análise no banco de dados com status `RECEBIDO`
- Publicar mensagem no RabbitMQ para o processing-service consumir
- Expor endpoint para consulta de status e atualização interna de status

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/uploads` | Recebe e valida o arquivo, inicia o fluxo de análise |
| `GET` | `/uploads/{analysis_id}` | Consulta status de uma análise |
| `PATCH` | `/uploads/{analysis_id}/status` | Atualiza status (chamado pelo processing-service) |
| `GET` | `/health` | Health check |

## Formatos aceitos

`PDF`, `PNG`, `JPG`, `JPEG` — validados por magic bytes via biblioteca `filetype`.

## Diagrama

```mermaid
flowchart TD
    A([POST /uploads]) --> B{Magic bytes<br>válidos?}
    B -- não --> C([400 Bad Request])
    B -- sim --> D{Tamanho<br>≤ MAX_FILE_SIZE_MB?}
    D -- não --> E([413 Payload Too Large])
    D -- sim --> F[Salvar no MinIO<br>nome = UUID]
    F --> G[Registrar no PostgreSQL<br>status = RECEBIDO]
    G --> H[Publicar no RabbitMQ<br>exchange: arch_analyzer]
    H --> I([202 Accepted · analysis_id])
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_URL` | `postgresql+asyncpg://upload_user:upload_pass@localhost:5432/upload_db` | Banco de dados PostgreSQL |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | URL de conexão RabbitMQ |
| `MINIO_ENDPOINT` | `localhost:9000` | Endpoint do MinIO |
| `MINIO_ACCESS_KEY` | `minioadmin` | Access key do MinIO |
| `MINIO_SECRET_KEY` | `minioadmin` | Secret key do MinIO |
| `MINIO_BUCKET` | `diagrams` | Bucket para armazenar diagramas |
| `MINIO_SECURE` | `false` | Usar TLS na conexão com MinIO |
| `MAX_FILE_SIZE_MB` | `10` | Tamanho máximo do arquivo em MB |
| `RABBITMQ_EXCHANGE` | `arch_analyzer` | Nome do exchange RabbitMQ |
| `RABBITMQ_QUEUE` | `analysis.process` | Nome da fila RabbitMQ |
| `RABBITMQ_ROUTING_KEY` | `analysis.process` | Routing key RabbitMQ |
| `SERVICE_NAME` | `upload-service` | Nome do serviço (usado em logs) |
| `LOG_LEVEL` | `INFO` | Nível de log |

## Como rodar localmente (sem Docker)

```bash
# Pré-requisito: PostgreSQL, RabbitMQ e MinIO em execução

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Ajuste DATABASE_URL, RABBITMQ_URL e MINIO_ENDPOINT

uvicorn app.main:app --port 8001 --reload
```

## Como rodar com Docker (standalone)

```bash
docker build -t fiap-hackathon/upload-service .
docker run --rm -p 8001:8001 \
  -e DATABASE_URL=postgresql+asyncpg://upload_user:upload_pass@host.docker.internal:5432/upload_db \
  -e RABBITMQ_URL=amqp://guest:guest@host.docker.internal:5672/ \
  -e MINIO_ENDPOINT=host.docker.internal:9000 \
  fiap-hackathon/upload-service
```

## Como rodar os testes

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

## Arquitetura completa e orquestração

Para rodar o sistema completo (todos os serviços + infraestrutura), consulte o repositório de documentação:

**[fiap-hackathon-docs](../fiap-hackathon-docs)** — contém `docker-compose.yml`, `.env.example` e instruções de setup do ambiente completo.
