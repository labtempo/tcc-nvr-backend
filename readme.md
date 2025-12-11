# API Sistema - Documentação

## Sobre o Sistema

API para controle de acesso com autenticação JWT. Feita com FastAPI para gerenciar usuários e permissões.
Python versão 3.11
Até o momento, para rodar localmente é necessário criar um arquivo .env com os seguintes parâmetros

DATABASE_URL="postgresql://tcc_usr:tcc_pwd@db:5432/tcc_db"

MEDIA_MTX_HOST="http://127.0.0.1:"
CONTROL_API_PORT="9997"
HLS_PORT="8888"
WEBRTC_PORT="8889"

## Instalação

```bash
pip install -r requirements.txt
```

## Rodando com Docker (Recomendado)

O projeto já está configurado com `docker-compose` para rodar a API, o Banco de Dados (PostgreSQL) e o MediaMTX (Servidor de Streaming) juntos.

1.  **Iniciar os serviços:**
    ```bash
    docker-compose up --build
    ```
    Aguarde até ver os logs da API na porta 8000.

    - **API**: http://localhost:8000
    - **Docs**: http://localhost:8000/docs
    - **MediaMTX**: http://localhost:8888 (API de controle na porta 9997)

## Simulando Câmeras (Sem Hardware)

Para testar o sistema sem ter câmeras reais, você pode simular streams RTSP usando **Docker e FFMPEG**. Isso cria um "sinal de teste" infinito que o sistema processa como se fosse uma câmera real.

### Opção 1: Gerar Sinal de Teste (Recomendado)
Este comando cria uma câmera falsa transmitindo um relógio e barras de cores. Use o script auxiliar para facilitar.

```bash
# Execute em um novo terminal:
./scripts/simulate_camera.sh cam1
```

Para criar múltiplas câmeras, basta passar nomes diferentes:
```bash
./scripts/simulate_camera.sh cam2
```

**Como Cadastrar essa Câmera:**
Use a URL RTSP: `rtsp://localhost:8554/cam1` (Sim, use `localhost` na hora de cadastrar na API, pois o MediaMTX vai ler de si mesmo/rede local).

### Opção 2: Links Públicos (Instáveis)
Você pode tentar usar links públicos, mas eles ficam offline com frequência.
- `rtsp://stream.strba.sk:1935/strba/VYHLAD_JAZERO.stream`
- `rtsp://rtsp.stream/pattern` (Requer cadastro as vezes)

## Primeiro Usuário Admin

Após rodar a aplicação pela primeira vez, o banco estará vazio. Você deve criar o usuário administrador para conseguir logar.

Execute o comando abaixo em um **novo terminal** para inserir o usuário `admin@sistema.com` (senha `admin123`) diretamente no banco dockerizado:

```bash
docker exec -it tcc-postgres psql -U tcc_usr -d tcc_db -c "INSERT INTO public.\"user\" (email, password_hash, full_name, user_role_id, is_active, created_at, updated_at) VALUES ('admin@sistema.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'Administrador', 1, true, NOW(), NOW());"
```

## User Roles

Os tipos de usuário (`admin`, `usuario`) são criados automaticamente no banco ao iniciar a API.

## Como Testar (Fluxo Completo)

Para testar, simularemos o fluxo completo: Login -> Adicionar Câmera -> Visualizar.
Você precisará de um link RTSP (ex: `rtsp://stream.strba.sk:1935/strba/VYHLAD_JAZERO.stream` ou um link local).

### 1. Fazer Login (Obter Token)
```bash
curl -X POST "http://localhost:8000/api/v1/login" \
     -H "Content-Type: application/json" \
     -d "{\"email\": \"admin@sistema.com\", \"password\": \"admin123\"}"
```
**Copie o `access_token`** da resposta.

### 2. Cadastrar uma Câmera
Substitua `<SEU_TOKEN>` pelo token copiado:

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

### 3. Visualizar o Vídeo
A resposta do cadastro retornará um campo `visualisation_url_hls` (ex: `http://localhost:8888/camera_teste/index.m3u8`).
1. Abra um player HLS online (ex: [https://hls-js.netlify.app/demo/](https://hls-js.netlify.app/demo/)).
2. Cole a URL HLS.
3. Dê Play. Se o vídeo aparecer, o sistema está funcionando!

## Endpoints

Todos os endpoints estão sob o prefixo `/api/v1`.

### 🔐 Autenticação & Usuários

| Método | Endpoint | Descrição | Permissão |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/login` | Realiza login e retorna o Token JWT. | Público |
| **GET** | `/api/v1/perfil` | Retorna dados do usuário logado. | Usuário |
| **GET** | `/api/v1/usuarios` | Lista todos os usuários cadastrados. | **Admin** |
| **POST** | `/api/v1/usuarios` | Cria um novo usuário. | **Admin** |
| **GET** | `/api/v1/area-restrita` | Endpoint de teste para validação de token. | Usuário |

### 📷 Câmeras

| Método | Endpoint | Descrição | Params/Body |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/camera` | Cadastra uma nova câmera. | JSON com `name`, `rtsp_url`, etc. |
| **GET** | `/api/v1/camera/{id}` | Obtém detalhes de uma câmera específica. | `id` da câmera na URL |
| **PUT** | `/api/v1/camera/{id}` | Atualiza dados de uma câmera (nome, rtsp, etc). | JSON com dados atualizados |
| **GET** | `/api/v1/camera/user/{uid}` | Lista todas as câmeras de um usuário. | `uid` (Use o ID do usuário logado) |

### 🎬 Gravações e Playback

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| **GET** | `/api/v1/camera/{id}/recordings` | Lista intervalos (segmentos) de gravação disponíveis. |
| **GET** | `/api/v1/camera/{id}/playback-url` | Gera um **token temporário** e retorna a URL para assistir o vídeo. |
| **GET** | `/api/v1/playback/video` | **Stream de Vídeo**. Usado pelo player com o token gerado acima. |
| **POST** | `/api/v1/record` | (Interno/Webhook) Cria registro de gravação no banco. |

### 📦 Outros

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| **GET** | `/` | Rota raiz, retorna status do sistema. |
| **GET** | `/status` | Retorna status detalhado e horário do servidor. |

## Problemas Comuns

### "Token inválido"
- Fazer login de novo
- Verificar se copiou o token completo
- Token expira em 8 horas

### "Email ou senha errados" 
- Conferir email e senha
- Usar os usuários de teste

### "Você não tem permissão"
- Só admin pode criar usuários e ver lista
- Fazer login como admin@sistema.com

### "Já existe usuário com esse email"
- Email já foi usado
- Escolher outro email

## Melhorias Futuras

Para usar em produção real:
- Trocar SHA256 por bcrypt (mais seguro)
- Usar banco de dados MySQL
- Mudar a chave secreta do JWT
- Adicionar HTTPS
- Limitar tentativas de login
- Logs de segurança

## Estrutura do Projeto

```
app/
  ├── controller/
  ├── domain/
  ├── dtos/
  ├── repository/
  ├── resources/
  ├── security/
  ├── service/
main.py
requirements.txt
.env
```

## Arquivos de Exemplo

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
PyJWT==2.8.0
```

### Docker (opcional)
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```