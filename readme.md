# API Sistema - Documentação

## Sobre o Sistema

API para controle de acesso com autenticação JWT. Feita com FastAPI para gerenciar usuários e permissões.

## Instalação

```bash
pip install -r requirements.txt
```

## Rodando

```bash
uvicorn app.main:app --reload
```

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

## User Roles

Os tipos de usuário (`admin`, `usuario`) são criados automaticamente no banco ao iniciar a API.

## Primeiro Usuário Admin

Após rodar a aplicação pela primeira vez, o banco estará vazio.  
**Você precisa inserir manualmente o primeiro usuário admin para conseguir logar e criar outros usuários.**

### Gerando o hash da senha

No terminal Python:
```python
from app.security.security import criar_hash_senha
print(criar_hash_senha("admin123"))
```
Copie o hash gerado.

### Inserindo o usuário admin no banco (exemplo para PostgreSQL)

```sql
INSERT INTO public."user"
(email, password_hash, full_name, user_role_id, is_active, created_at, updated_at)
VALUES (
  'admin@sistema.com',
  'HASH_GERADO_AQUI',
  'Administrador',
  1,
  true,
  NOW(),
  NOW()
);
```

## Tecnologias

- FastAPI (framework web)
- JWT (tokens de autenticação)
- SHA256 (hash das senhas)
- Pydantic (validação de dados)

## Como Funciona

### Usuários
Cada usuário tem:
- **ID**: número único
- **Email**: para login
- **Full Name**: nome completo
- **Senha**: guardada com hash
- **Tipo**: "admin" ou "usuario"

### Autenticação
1. Faz login com email/senha
2. Recebe um token JWT
3. Usa o token nas próximas requisições
4. Token dura 8 horas

## Usuários de Teste

**Administrador:**
- Email: admin@sistema.com
- Senha: admin123

## Endpoints

Todos os endpoints estão sob o prefixo `/api/v1` (exemplo: `/api/v1/login`, `/api/v1/usuarios`).

### Públicos (não precisa token)

#### POST /login
Fazer login
```json
// Enviar:
{
  "email": "admin@sistema.com",
  "password": "admin123"
}

// Recebe:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Protegidos (precisa token)

#### GET /perfil
Ver seus dados
```bash
# Header necessário:
Authorization: Bearer SEU_TOKEN_AQUI
```
```json
{
  "id": 1,
  "email": "admin@sistema.com",
  "full_name": "Administrador",
  "user_role": 1
}
```

### Administrativos (só admin)

#### GET /usuarios
Listar todos usuários
```json
[
  {
    "id": 1,
    "email": "admin@sistema.com",
    "full_name": "Administrador", 
    "user_role": 1
  },
  {
    "id": 2,
    "email": "joao@sistema.com",
    "full_name": "João Silva",
    "user_role": 2
  }
]
```

#### POST /usuarios
Criar novo usuário
```json
// Enviar:
{
  "email": "maria@sistema.com",
  "password": "senha123",
  "full_name": "Maria Santos"
}

// Recebe:
{
  "msg": "Usuário maria@sistema.com criado!",
  "id": 3
}
```

## Códigos de Erro

- **200**: Deu certo
- **400**: Dados errados (ex: email já existe)
- **401**: Não está logado ou senha errada
- **403**: Não tem permissão (precisa ser admin)

## Como Testar

### Com cURL

**Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sistema.com","password":"admin123"}'
```

**Usar token:**
```bash
curl -X GET "http://localhost:8000/api/v1/perfil" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### Com Python

```python
import requests

# Login
resp = requests.post('http://localhost:8000/api/v1/login', json={
    'email': 'admin@sistema.com',
    'password': 'admin123'
})
token = resp.json()['access_token']

# Usar token
perfil = requests.get('http://localhost:8000/api/v1/perfil', 
    headers={'Authorization': f'Bearer {token}'})
print(perfil.json())
```

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