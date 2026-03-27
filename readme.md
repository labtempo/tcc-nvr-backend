# Sistema NVR IP – Backend (FastAPI + MediaMTX + PostgreSQL)

Este projeto implementa o **backend de um NVR (Network Video Recorder) IP**, focado em:

- Autenticação e autorização de usuários (JWT).
- Cadastro, gestão e controle de câmeras IP.
- Integração profunda com o **MediaMTX** (servidor de media/RTSP/HLS/WebRTC/Playback).
- Registro e listagem de **gravações** de vídeo.
- Geração de **URLs temporárias de playback** com controle de acesso.

A API é escrita em **Python 3.11**, usando **FastAPI**, **SQLModel/SQLAlchemy** e **PostgreSQL**, com orquestração via **Docker Compose**.

---

## Visão Geral da Arquitetura

### Componentes Principais

1. **API Backend (FastAPI)**  
   Container `api`, exposto em `http://localhost:8000`  
   Responsável por:
   - Autenticação JWT e **RBAC** (admin / viewer).
   - CRUD de **usuários**.
   - CRUD de **câmeras**.
   - Integração e orquestração com o **MediaMTX**.
   - Endpoints para **listagem e playback** de gravações.
   - Exposição de arquivos gravados via `/api/v1/videos` (static).

2. **Banco de Dados (PostgreSQL)**  
   Container `db` (`tcc-postgres`), exposto em `localhost:5433`.  
   Usado para armazenar:
   - Usuários e roles.
   - Câmeras cadastradas.
   - Registros de gravações (metadados).
   - Configurações de sistema (tabela `system_setting`).

3. **MediaMTX**  
   Container `mediamtx` (`tcc-mediamtx`), principal servidor de mídia:  
   - **RTSP** (porta `8554`) – ingestão de câmeras.
   - **HLS** (porta `8888`) – streaming HTTP para players HLS.
   - **WebRTC/WHEP** (porta `8889`) – baixa latência via navegador.
   - **Playback API** (porta `9996`) – leitura de arquivos gravados.
   - **API de controle v3** (porta `9997`) – criação/remoção/atualização de paths, listagem, kick de sessões, etc.
   - Tudo configurado via [`mediamtx.yml`](mediamtx.yml), com autenticação interna (`authInternalUsers`).

4. **Volumes de Gravação**
   - Pasta `./recordings` montada tanto no container da API quanto no do MediaMTX.
   - MediaMTX escreve arquivos de gravação (fmp4) nessa pasta.
   - A API expõe essa mesma pasta via `/api/v1/videos`.

---

## Funcionalidades Principais

### 1. Autenticação & Autorização (RBAC)

- Autenticação via JSON Web Token (JWT), implementada em  
  [`app/security/security.py`](app/security/security.py):
  - Funções principais:
    - [`criar_hash_senha`](app/security/security.py): hash de senha com SHA-256.
    - [`verificar_senha`](app/security/security.py): validação de senha.
    - [`gerar_token`](app/security/security.py): criação do JWT (campo `sub` = email do usuário).
    - [`pegar_usuario_atual`](app/security/security.py): dependency FastAPI que valida o token Bearer e retorna o usuário autenticado.
- Modelo de token de resposta: [`TokenResponse`](app/security/TokenContext.py).
- Papéis de usuário (RBAC):
  - Definidos em [`UserRoleEnum`](app/domain/user_role.py) (`admin`, `viewer`).
  - Persistidos em [`User_Role`](app/domain/user_role.py).
  - Seed automático em [`seed_user_roles`](app/resources/database/connection.py).

#### Permissões

- **Admin (user_role_id = 1)**:
  - Pode criar, listar e apagar usuários.
  - Pode cadastrar, atualizar e deletar câmeras.
  - Pode executar todas as operações de listagem e playback.
- **Viewer (user_role_id = 2)**:
  - Pode logar, acessar `/perfil`, listar câmeras (`GET /cameras`) e consumir playback.
  - **Não** pode criar/editar/deletar usuários.
  - **Não** pode criar/editar/deletar câmeras.

As checagens estão implementadas principalmente em:

- [`app/controller/usersController.py`](app/controller/usersController.py)
- [`app/controller/cameraController.py`](app/controller/cameraController.py)

---

### 2. Modelo de Dados

Principais entidades (em [`app/domain`](app/domain)):

1. [`User`](app/domain/user.py)
   - `id`, `email`, `password_hash`, `full_name`
   - `user_role_id` (FK para [`User_Role`](app/domain/user_role.py))
   - `is_active`, `created_at`, `updated_at`

2. [`User_Role`](app/domain/user_role.py)
   - `id`, `role_name` (`admin` ou `viewer`), `description`

3. [`Camera`](app/domain/camera.py)
   - `id`, `name`, `rtsp_url`, `is_recording`
   - `created_by_user_id` (FK para `User`)
   - `path_id` (ex: `live/cam1`) – path principal no MediaMTX.
   - `path_id_low` (ex: `live/cam1_low`) – path de baixa resolução.
   - `created_at`, `updated_at`

4. [`Record`](app/domain/record.py)
   - `id`, `camera_id` (FK)
   - `nome_arquivo`, `url_acesso`
   - `duracao_segundos`
   - `data_criacao`, `data_inicio_segmento`, `data_fim_segmento`

5. [`System_Setting`](app/domain/system_settings.py)
   - Configurações de sistema (key/value).

---

### 3. Endpoints da API

A API é inicializada em [`app/main.py`](app/main.py) e registra os routers:

- [`usersController`](app/controller/usersController.py) – prefixo `/api/v1`
- [`cameraController`](app/controller/cameraController.py) – prefixo `/api/v1`
- [`recordController`](app/controller/recordController.py) – prefixo `/api/v1`, tag `records`
- [`videoController`](app/controller/videoController.py) – static `/api/v1/videos`
- [`playbackController`](app/controller/playbackController.py) – prefixo `/api/v1`

#### 3.1. Autenticação & Usuários

Controller: [`usersController.py`](app/controller/usersController.py)

- **POST** `/api/v1/login`
  - Body: [`LoginData`](app/dtos/login.py) `{ email, password }`
  - Retorna [`TokenResponse`](app/security/TokenContext.py): `access_token`, `token_type`, `user_id`, `role`.
  - Implementa fluxo de autenticação via [`authenticate_user`](app/service/user_services.py).

- **POST** `/api/v1/usuarios` (Admin)
  - Cria novo usuário com role `viewer`.
  - Body: [`NovoUsuario`](app/dtos/login.py) `{ email, password, full_name }`.
  - Verifica se o `usuario_atual.user_role_id == 1`.

- **GET** `/api/v1/usuarios` (Admin)
  - Lista todos os usuários, retorna [`UserData`](app/dtos/login.py) com `role` textual (`admin`/`viewer`).

- **GET** `/api/v1/perfil`
  - Retorna os dados do usuário autenticado (`UserData`).

- **GET** `/api/v1/area-restrita`
  - Endpoint simples para testar proteção via token.

- **DELETE** `/api/v1/usuarios/{user_id}` (Admin)
  - Admin pode deletar outros usuários (não pode deletar a si mesmo).

---

#### 3.2. Câmeras

Controller: [`cameraController.py`](app/controller/cameraController.py)  
Serviço: [`camera_services.py`](app/service/camera_services.py)  
Repositório: [`camera_repository.py`](app/repository/camera_repository.py)

- **POST** `/api/v1/camera` (Admin)
  - Body: [`CamCreate`](app/dtos/camera.py) `{ name, rtsp_url, is_recording }`
  - Passos:
    1. Verifica permissão (apenas admin).
    2. Gera `path_id = "live/{nome_normalizado}"`.
    3. Chama [`media_mtx_service.create_and_verify_camera_path`](app/service/mediaMtx_services.py) para configurar o path no MediaMTX.
    4. Cria entrada na tabela `camera`.
    5. Retorna [`CamData`](app/dtos/camera.py) com URLs HLS/WebRTC baseadas em [`settings`](app/resources/settings/config.py):
       - `visualisation_url_hls`
       - `visualisation_url_hls_low`
       - `visualisation_url_webrtc`

- **GET** `/api/v1/cameras`
  - Lista **todas** as câmeras (admin e viewer podem consumir).
  - Retorna lista de [`CamData`](app/dtos/camera.py).

- **GET** `/api/v1/camera/{camera_id}`
  - Retorna detalhes de uma câmera específica.

- **GET** `/api/v1/camera/user/{user_id}`
  - Lista câmeras criadas por um determinado usuário.

- **PUT** `/api/v1/camera/{camera_id}` (Admin)
  - Atualiza nome/URL/flag de gravação.
  - Se `rtsp_url` ou `is_recording` mudarem, chama  
    [`media_mtx_service.create_camera_path`](app/service/mediaMtx_services.py) para reconfigurar o path no MediaMTX.

- **DELETE** `/api/v1/camera/{camera_id}` (Admin)
  - Fluxo:
    1. Checa permissão de admin.
    2. Busca a câmera.
    3. Chama [`media_mtx_service.delete_camera_path`](app/service/mediaMtx_services.py) para remover a configuração no MediaMTX.
    4. Remove a entrada da câmera do banco.

---

#### 3.3. Gravações

Controller: [`recordController.py`](app/controller/recordController.py)  
DTOs: [`RecordCreate`, `RecordData`](app/dtos/record.py)

- **POST** `/api/v1/record`
  - Usado principalmente como **endpoint interno/webhook** para registrar metadados de gravações.
  - Cria um [`Record`](app/domain/record.py) com:
    - `camera_id`
    - `nome_arquivo`
    - `url_acesso` (montado como `/recordings/{nome_arquivo}`)
    - `duracao_segundos`
    - `data_inicio_segmento`, `data_fim_segmento`
  - Requer usuário autenticado.

Embora exista o DTO [`MediaMTXWebhookPayload`](app/dtos/webhook.py) e um serviço inicial [`WebhookService`](app/service/webhook_services.py) (pensado para processar webhooks do MediaMTX), o fluxo principal de gravação hoje é baseado no próprio MediaMTX gravando em disco e a API consultando via **Playback API**.

---

#### 3.4. Playback (Reprodução de Vídeo Gravado)

Controller: [`playbackController.py`](app/controller/playbackController.py)  
Segurança: funções de playback em [`security.py`](app/security/security.py)

##### a) Listagem de segmentos gravados

- **GET** `/api/v1/camera/{camera_id}/recordings`

Fluxo:

1. Busca a câmera (`Camera`) e obtém `path_id`.
2. Monta chamada para MediaMTX Playback API:
   - URL: `settings.media_mtx_playback_url + "/list"`  
     (por padrão: `http://mediamtx:9996/list`)
   - Autenticação: `MEDIAMTX_API_USER` / `MEDIAMTX_API_PASS`.
   - Query params:
     - `path` = `camera.path_id`
     - `start` (opcional)
     - `end` (opcional)
3. Faz `GET` via `httpx.AsyncClient`.
4. Retorna JSON vindo do MediaMTX ou `[]` em alguns casos de erro 404.

##### b) Geração de URL Temporária de Playback

- **GET** `/api/v1/camera/{camera_id}/playback-url`

Fluxo:

1. Usuário autenticado solicita playback para uma câmera específica.
2. API gera um **token de playback temporário**:
   - Função: [`create_temp_playback_token`](app/security/security.py)
   - Payload inclui:
     - `sub` = `user_id`
     - `path` = `camera.path_id`
     - `start`
     - `duration`
   - Expira em `PLAYBACK_TOKEN_EXPIRE_SECONDS` (padrão 600s).
3. API retorna JSON:
   - `{"playbackUrl": "/api/v1/playback/video?token=<TOKEN>"}`

##### c) Endpoint de Stream de Playback

- **GET** `/api/v1/playback/video?token=...`

Fluxo:

1. Decodifica o token com [`decode_temp_playback_token`](app/security/security.py).
2. Extrai `path`, `start`, `duration`.
3. Chama MediaMTX Playback API `/get`:
   - URL base: `settings.media_mtx_playback_url + "/get"`
   - Autenticação via `MEDIAMTX_API_USER / MEDIAMTX_API_PASS`.
   - Query params: `path`, `start`, `duration`, `format=mp4`.
4. Abre um stream HTTP (`stream=True` via `httpx`) e retransmite para o cliente como `video/mp4` usando `StreamingResponse`.
5. Fecha conexões no final usando `BackgroundTask`.

Este fluxo garante:

- Controle de acesso (apenas usuários com token válido).
- Tokens com vida curta, mais seguros.
- Consumo simples via front-end (basta usar a URL retornada).

---

### 4. Integração com MediaMTX (Controle de Paths e Sessões)

Toda a lógica de integração com MediaMTX está concentrada em  
[`app/service/mediaMtx_services.py`](app/service/mediaMtx_services.py), através da classe `MediaMtxService`.

#### 4.1. Configuração de Clientes HTTP

- `self.command_client` – `httpx.AsyncClient` com timeout de 10s.
- `self.polling_client` – `httpx.AsyncClient` com timeout de 30s.
- Ambos autenticam via `BasicAuth(MEDIAMTX_API_USER, MEDIAMTX_API_PASS)`.
- Base URL: `settings.media_mtx_control_api_url` (ex: `http://mediamtx:9997`).

#### 4.2. Criação/Verificação de Path de Câmera

Método principal:  
[`MediaMtxService.create_and_verify_camera_path`](app/service/mediaMtx_services.py)

**Objetivo:**  
Criar ou assumir um path no MediaMTX (v3 API) e garantir que ele está pronto para receber/entregar stream.

Passos principais:

1. **Normalização e encoding do path**
   - O `path_name` (ex: `live/cam1`) é URL-encoded para evitar problemas com `/` e caracteres especiais.
   - Endpoints montados:
     - `/v3/config/paths/add/{encoded_path}`
     - `/v3/config/paths/patch/{encoded_path}`
     - `/v3/config/paths/delete/{encoded_path}`
     - `/v3/paths/get/{encoded_path}`

2. **Montagem do payload**
   - Se `rtsp_url` começa com `"publisher"`:
     - `source = "publisher"` (MediaMTX espera publisher externo conectando no path).
   - Senão:
     - `source = rtsp_url` (MediaMTX faz pull do RTSP remoto).
   - Opções de gravação (`record`) se `record=True`:
     - `recordPath = "/recordings/%path/%Y-%m-%d_%H-%M-%S-%f"`
     - `recordFormat = "fmp4"`
     - `recordSegmentDuration = "10s"`
     - `recordDeleteAfter = "24h"`

3. **Tentativa de PATCH (Upsert)**
   - Primeiro tenta `PATCH /v3/config/paths/patch/{path}`:
     - Se `200 OK`: path atualizado/assumido => parte para verificação de prontidão.
     - Se `404`: path não existe, irá tentar `ADD`.
     - Outros códigos: segue para a estratégia de `ADD`.

4. **Loop de ADD com Retry e Kick**
   - Antes de criar, faz um **blind delete** de configs antigas:
     - `POST /v3/config/paths/delete/{path}` (ignorando erros).
   - Tenta até 20 vezes:
     - `POST /v3/config/paths/add/{path}`.
     - Se sucesso, prossegue.
     - Se `400 Bad Request` (conflito):
       - Interpreta como possível conflito de path/sessão.
       - Chama `/v3/paths/list` para inspecionar path em runtime.
       - Se encontrar item com `name == path_name`, aplica **kick**:

#### 4.3. Lógica de Kick (desconexão de clientes)

Função auxiliar:  
[`_get_kick_endpoint`](app/service/mediaMtx_services.py)

- Recebe `session_type` e `session_id`.
- Mapeia para endpoints padrão do MediaMTX v3:
  - `rtspSession` → `/v3/rtspsessions/kick/{id}`
  - `rtmpSession` → `/v3/rtmpsessions/kick/{id}`
  - `hlsSession` → `/v3/hlssessions/kick/{id}`
  - `webrtcSession` → `/v3/webrtcsessions/kick/{id}`
  - Fallback: `/v3/sessions/kick/{id}`.

Fluxo de kick dentro do retry:

1. Chama `/v3/paths/list`.
2. Para o path conflitado:
   - Se `source` tiver `id`:
     - Monta endpoint via `_get_kick_endpoint(type, id)`.
     - Tenta desconectar o **publisher**.
   - Para cada `reader`:
     - Mesmo processo, chutando leitores ativos.
3. Reforça a deleção da conf antiga:
   - `POST /v3/config/paths/delete/{path}`.
4. Aguarda:
   - `0.5s` se encontrou publisher.
   - `1.0s` se não encontrou.
5. Tenta `ADD` novamente.

#### 4.4. Verificação de Prontidão

Após sucesso no `PATCH` ou no `ADD`, o serviço faz polling:

- Até 10 tentativas.
- Exponencial backoff (0.5s → até 5s).
- Chama `/v3/paths/get/{path}`.
- Se `200 OK`, considera o path pronto (`True`).

Se não ficar pronto a tempo, lança `TimeoutError`.

#### 4.5. Atualização Simples de Path

Método:  
[`MediaMtxService.create_camera_path`](app/service/mediaMtx_services.py)

- Versão simplificada usada ao **atualizar** uma câmera (PUT).
- Mesma ideia de `PATCH` + fallback para `ADD` com retry e kick.

#### 4.6. Deleção de Path

Método:  
[`MediaMtxService.delete_camera_path`](app/service/mediaMtx_services.py)

- `POST /v3/config/paths/delete/{path_name}`
- Se `404`, apenas loga que o path já não existe.
- Qualquer outro erro gera exceção.

---

### 5. Scripts Auxiliares

Pasta [`scripts`](scripts):

- Criar/atualizar admin e usuários de teste:
  - [`seed_admin.py`](seed_admin.py): cria `admin@sistema.com` (senha `admin123`) se não existir.
  - [`create_test_user.py`](scripts/create_test_user.py): cria/atualiza `tester@test.com` (senha `test`).
  - [`list_users.py`](scripts/list_users.py): lista usuários do banco.

- Auxílio para MediaMTX:
  - [`simulate_camera.sh`](scripts/simulate_camera.sh) / [`simulate_camera.ps1`](scripts/simulate_camera.ps1): simulam câmeras com FFMPEG dentro de container Docker, publicando em `rtsp://host.docker.internal:8554/live/<nome>`.
  - Vários scripts de debug/testes (`debug_*`, `verify_*`, `stress_test_api.py`, etc.) foram usados para:
    - Reproduzir cenários de conflito de path.
    - Validar lógica de kick.
    - Verificar endpoints da API v3 do MediaMTX.

Esses scripts são especialmente úteis para **relatar no TCC** o processo de teste e validação da integração com MediaMTX.

---

## Configuração de Ambiente

### Variáveis de Ambiente (Settings)

Gerenciadas em [`app/resources/settings/config.py`](app/resources/settings/config.py) via `pydantic-settings`.

Campos principais:

- `DATABASE_URL`
- `MEDIA_MTX_HOST` (ex: `http://mediamtx`)
- `CONTROL_API_PORT` (ex: `9997`)
- `HLS_PORT` (ex: `8888`)
- `WEBRTC_PORT` (ex: `8889`)
- `MEDIAMTX_API_USER`, `MEDIAMTX_API_PASS`
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

Campos adicionais (fixos ou default):

- `MEDIA_MTX_PLAYBACK_PORT = 9996`
- `PLAYBACK_TOKEN_SECRET_KEY`
- `PLAYBACK_TOKEN_ALGORITHM`
- `PLAYBACK_TOKEN_EXPIRE_SECONDS = 600`

### .env de Exemplo (Desenvolvimento Local sem Docker Compose)

```env
DATABASE_URL="postgresql://tcc_usr:tcc_pwd@db:5432/tcc_db"

MEDIA_MTX_HOST="http://127.0.0.1"
CONTROL_API_PORT="9997"
HLS_PORT="8888"
WEBRTC_PORT="8889"

MEDIAMTX_API_USER="api-backend"
MEDIAMTX_API_PASS="UMA_SENHA_FORTE_E_SECRETA_AQUI"

SECRET_KEY="dev_secret_key_change_me_in_prod"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Execução com Docker (Recomendado)

Arquivo: [`docker-compose.yml`](docker-compose.yml)

### Subir os serviços

```bash
docker-compose up --build
```

Serviços disponíveis:

- API: `http://localhost:8000`
- Docs Swagger: `http://localhost:8000/docs`
- MediaMTX HLS: `http://localhost:8888`
- MediaMTX API v3: `http://localhost:9997`
- MediaMTX Playback: `http://localhost:9996`
- PostgreSQL: `localhost:5433` (para acesso local / ferramentas externas)

---

## Primeiro Usuário Admin

Após subir o ambiente pela primeira vez, crie o admin (caso não tenha seed automático):

```bash
docker exec -it tcc-postgres psql -U tcc_usr -d tcc_db \
  -c "INSERT INTO public.\"user\" (email, password_hash, full_name, user_role_id, is_active, created_at, updated_at) VALUES ('admin@sistema.com', '9bd2e6bb09a1aa991525f397da02abaaf67733b4b760ce96f287a91f5383e461', 'Administrador', 1, true, NOW(), NOW());"
```

> O hash corresponde à senha `admin123` gerada por [`criar_hash_senha`](app/security/security.py) (SHA-256).

Alternativamente, use o script [`seed_admin.py`](seed_admin.py) com as variáveis de ambiente corretas.

---

## Fluxo Completo de Uso (Login → Cadastrar Câmera → Visualizar)

### 1. Login (Obter Token JWT)

```bash
curl -X POST "http://localhost:8000/api/v1/login" \
     -H "Content-Type: application/json" \
     -d "{\"email\": \"admin@sistema.com\", \"password\": \"admin123\"}"
```

Guarde o campo `access_token` da resposta.

### 2. Cadastrar uma Câmera

Exemplo com uma câmera remota pública (instável):

```bash
curl -X POST "http://localhost:8000/api/v1/camera" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <SEU_TOKEN>" \
     -d "{
           \"name\": \"Câmera Teste\",
           \"rtsp_url\": \"rtsp://stream.strba.sk:1935/strba/VYHLAD_JAZERO.stream\",
           \"is_recording\": false
         }"
```

A resposta trará, por exemplo:

- `visualisation_url_hls`: `http://localhost:8888/live/camera_teste/index.m3u8`
- `visualisation_url_webrtc`: `http://localhost:8889/live/camera_teste`

### 3. Visualizar Vídeo (HLS)

1. Abra um player HLS (ex.: [https://hls-js.netlify.app/demo/](https://hls-js.netlify.app/demo/)).
2. Cole a URL `visualisation_url_hls`.
3. Clique em **Play**.

### 4. WebRTC (Baixa Latência)

- Use a URL retornada em `visualisation_url_webrtc` (ex.: `http://localhost:8889/live/camera_teste`).
- Em produção, recomenda-se HTTPS e configuração adequada de STUN/TURN.

---

## Simulação de Câmeras (Sem Hardware Físico)

### Script `simulate_camera.sh` (Linux/Mac)

```bash
./scripts/simulate_camera.sh cam1
```

- Gera um sinal de teste por FFMPEG.
- Publica via RTSP em: `rtsp://host.docker.internal:8554/live/cam1`.
- O próprio script tenta **auto-registrar** a câmera na API usando o admin padrão.

### Script `simulate_camera.ps1` (Windows/PowerShell)

```powershell
.\scripts\simulate_camera.ps1 -CameraName cam1
```

- Mesmo conceito, mas adaptado para Windows.
- Usa a mesma credencial admin.

---

## Estrutura do Projeto (Resumo)

```txt
app/
  ├── main.py                      # Inicialização da API e routers
  ├── controller/
  │     ├── usersController.py     # Login, usuários, perfil
  │     ├── cameraController.py    # Câmeras, listing, playback-url
  │     ├── recordController.py    # Registro de gravações
  │     ├── playbackController.py  # Endpoint de streaming playback
  │     └── videoController.py     # Exposição da pasta recordings
  ├── domain/
  │     ├── user.py
  │     ├── user_role.py
  │     ├── camera.py
  │     ├── record.py
  │     └── system_settings.py
  ├── dtos/
  │     ├── login.py
  │     ├── camera.py
  │     ├── record.py
  │     └── webhook.py
  ├── repository/
  │     ├── user_repository.py
  │     ├── login_repository.py
  │     └── camera_repository.py
  ├── resources/
  │     ├── database/
  │     │     └── connection.py    # engine, create_db_and_tables, seed_user_roles, get_session
  │     └── settings/
  │           └── config.py        # Settings (env vars) + URLs MediaMTX
  ├── security/
  │     ├── security.py            # JWT, hash, token de playback
  │     └── TokenContext.py        # TokenResponse
  └── service/
        ├── user_services.py
        ├── camera_services.py
        ├── mediaMtx_services.py   # Integração robusta com MediaMTX
        └── webhook_services.py    # Base para processamento de webhooks
```

---

## Problemas Comuns

### "Token inválido"

- O token JWT pode ter expirado (padrão: 8 horas para login, 10 minutos para playback).
- Verifique se foi copiado sem quebras de linha.
- Faça login novamente.

### "Email ou senha errados"

- Confirme `admin@sistema.com` / `admin123` ou usuários de teste criados via scripts.

### "Você não tem permissão"

- Apenas **admin** pode:
  - Criar/editar/deletar usuários.
  - Criar/editar/deletar câmeras.
- Faça login com conta admin.

### Erros ao criar câmera (503 / 504)

- Podem estar relacionados a:
  - MediaMTX não estar rodando ou inacessível pela API.
  - Conflitos de path resolvidos por meio da lógica de **kick** e **retry**.
- Verifique os logs do container `mediamtx` e da API.

---

## Pontos Relevantes para o TCC

Ao descrever este sistema em um trabalho acadêmico, alguns tópicos técnicos importantes:

1. **Arquitetura em Microsserviços/Containers**
   - Separação clara entre API, DB e servidor de mídia.
   - Orquestração com Docker Compose.

2. **Persistência e Modelo de Dados**
   - Uso de SQLModel (integração Pydantic + SQLAlchemy).
   - Modelagem de `User`, `Camera`, `Record` e `User_Role`.

3. **Segurança**
   - Uso de JWT para autenticação stateless.
   - RBAC com roles `admin` e `viewer`.
   - Tokens temporários de playback.

4. **Integração com MediaMTX**
   - Uso das APIs v3 (`/v3/config/paths`, `/v3/paths`, `/v3/*sessions/kick`).
   - Estratégia de **PATCH / ADD + Retry + Kick** para garantir consistência em cenários de conflito.
   - Mecanismo de playback via HTTP e controle de sessões.

5. **Gravação e Playback**
   - Gravação no nível do MediaMTX com fmp4 segmentado.
   - API de Playback da MediaMTX (`/list` e `/get`).
   - Tokenização de acesso e re-streaming do vídeo via FastAPI.

6. **Ferramentas de Simulação e Testes**
   - Uso de FFMPEG para simulação de câmeras.
   - Scripts de stress test e debug para validar a robustez do sistema.

---

## Instalação Local (sem Docker)

> Recomendado apenas para ambiente de desenvolvimento.

1. Criar venv e instalar dependências:

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

2. Configurar `.env` conforme seção anterior.
3. Subir PostgreSQL e MediaMTX manualmente (ou usar o `docker-compose` apenas para eles).
4. Rodar a API:

```bash
uvicorn app.main:app --reload
```

---

Este `README` busca documentar o máximo possível do fluxo interno da aplicação, suas responsabilidades e a integração detalhada com o MediaMTX, servindo como base para descrição técnica no TCC.