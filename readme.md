# API Sistema - Documentação

## Sobre o Sistema

API simples para controle de acesso com autenticação JWT. Feita com FastAPI para gerenciar usuários e permissões. (ATÉ O MOMENTO!!)

## Como Usar

### Instalação
```bash
pip install fastapi uvicorn pydantic[email] pyjwt
```

### Rodando
```bash
python main.py
```

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

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
- **Nome**: nome completo
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

### Públicos (não precisa token)

#### GET /
Status da API
```json
{
  "sistema": "API Online",
  "versao": "1.0",
  "status": "funcionando"
}
```

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

#### GET /status
Verificar se está funcionando
```json
{
  "online": true,
  "horario": "15/09/2025 14:30:25",
  "sistema": "API Sistema",
  "versao": "1.0"
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
  "nome": "Administrator",
  "tipo": "admin"
}
```

#### GET /area-restrita  
Área de exemplo protegida
```json
{
  "msg": "Ola Administrator, voce acessou a area restrita!",
  "user_id": 1,
  "acesso_em": "15/09/2025 14:35:10"
}
```

### Administrativos (só admin)

#### GET /usuarios
Listar todos usuários
```json
{
  "usuarios": [
    {
      "id": 1,
      "email": "admin@sistema.com",
      "nome": "Administrator", 
      "tipo": "admin"
    },
    {
      "id": 2,
      "email": "joao@sistema.com",
      "nome": "João Silva",
      "tipo": "usuario"
    }
  ],
  "total": 2
}
```

#### POST /usuarios
Criar novo usuário
```json
// Enviar:
{
  "email": "maria@sistema.com",
  "password": "senha123",
  "nome": "Maria Santos"
}

// Recebe:
{
  "msg": "Usuario maria@sistema.com criado!",
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
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sistema.com","password":"admin123"}'
```

**Usar token:**
```bash
curl -X GET "http://localhost:8000/perfil" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### Com JavaScript

```javascript
// Fazer login
const fazerLogin = async (email, senha) => {
  const resp = await fetch('http://localhost:8000/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: senha })
  });
  return await resp.json();
};

// Pegar perfil
const verPerfil = async (token) => {
  const resp = await fetch('http://localhost:8000/perfil', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await resp.json();
};

// Exemplo de uso
const token = await fazerLogin('admin@sistema.com', 'admin123');
const perfil = await verPerfil(token.access_token);
```

### Com Python

```python
import requests

# Login
resp = requests.post('http://localhost:8000/login', json={
    'email': 'admin@sistema.com',
    'password': 'admin123'
})
token = resp.json()['access_token']

# Usar token
perfil = requests.get('http://localhost:8000/perfil', 
    headers={'Authorization': f'Bearer {token}'})
print(perfil.json())
```

## Problemas Comuns

### "Token invalido"
- Fazer login de novo
- Verificar se copiou o token completo
- Token expira em 8 horas

### "Email ou senha errados" 
- Conferir email e senha
- Usar os usuários de teste

### "Voce nao tem permissao"
- Só admin pode criar usuários e ver lista
- Fazer login como admin@sistema.com

### "Ja existe usuario com esse email"
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
projeto/
├── main.py              # Código principal
├── requirements.txt     # Dependências
└── docs/               
    └── README.md        # Esta documentação
```

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
PyJWT==2.8.0
```

## Arquivos de Exemplo

### Docker (opcional)
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```
