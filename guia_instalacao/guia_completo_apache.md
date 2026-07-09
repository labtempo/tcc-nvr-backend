# Guia de Instalação e Configuração do Projeto TCC

## PASSO 1: Atualizar o Sistema e Instalar a Base do Frontend (Node 22 + Angular)

```bash
# 1. Atualiza as listas de pacotes do Ubuntu
sudo apt update

# 2. Instala o curl para conseguir baixar instaladores da internet
sudo apt install curl -y

# 3. Baixa e configura o repositório oficial do Node.js v22 (LTS atual)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -

# 4. Instala o Node.js atualizado (que já vem com o NPM)
sudo apt install -y nodejs

# 5. Instala o Angular CLI globalmente
sudo npm install -g @angular/cli
```

## PASSO 2: Instalar e Configurar o Banco de Dados (PostgreSQL)

```bash
# 1. Instala o PostgreSQL e extensões utilitárias no Linux
sudo apt install postgresql postgresql-contrib -y

# 2. Inicia o serviço do banco de dados (deixa ele ativo em segundo plano)
sudo service postgresql start

# 3. Entra no terminal de comandos do PostgreSQL como administrador
sudo -u postgres psql
```

## PASSO 3: Criar as Credenciais dentro do PostgreSQL

> **Nota:** Os comandos abaixo devem ser digitados dentro da tela do terminal interativo do PostgreSQL (`postgres=#`).

```sql
-- Cria o usuário do TCC com a senha padrão
CREATE USER tcc_usr WITH PASSWORD 'tcc_pwd';

-- Dá permissão total de superusuário para esse perfil
ALTER USER tcc_usr WITH SUPERUSER;

-- Cria o banco de dados principal apontando o usuário tcc_usr como dono
CREATE DATABASE tcc_db OWNER tcc_usr;

-- Sai do terminal do banco de dados e volta pro Ubuntu
\q
```

## PASSO 4: Preparar as Pastas e Clonar do GitHub do Labtempo

```bash
# 1. Instala o Git e a extensão de ambientes virtuais do Python (venv)
sudo apt install python3-venv git -y

# 2. Cria uma pasta limpa para o TCC na raiz do Linux e entra nela
mkdir -p ~/Projeto_TCC && cd ~/Projeto_TCC

# 3. Clona o repositório do Backend do laboratório
git clone https://github.com/labtempo/tcc-nvr-backend.git tcc-nvr-backend

# 4. Clona o repositório do Frontend do laboratório
git clone https://github.com/labtempo/tcc-nvr-frontend.git tcc-nvr-frontend
```

## PASSO 5: Configurar e Ativar o Ambiente Virtual do Backend (Python)

```bash
# 1. Entra na pasta do backend clonada
cd ~/Projeto_TCC/tcc-nvr-backend

# 2. Cria o ambiente virtual do Python chamado 'venv'
python3 -m venv venv

# 3. Ativa o ambiente virtual (o terminal mostrará '(venv)' no início)
source venv/bin/activate

# 4. Instala todas as bibliotecas e dependências do Python
pip install -r requirements.txt
```

## PASSO 6: Baixar e Inicializar o Servidor de Mídia (MediaMTX)

```bash
# 1. Baixa a versão oficial do MediaMTX para Linux AMD64
wget https://github.com/bluenviron/mediamtx/releases/download/v1.9.0/mediamtx_v1.9.0_linux_amd64.tar.gz

# 2. Extrai os arquivos binários na pasta atual do backend
tar -xf mediamtx_v1.9.0_linux_amd64.tar.gz

# 3. Executa o MediaMTX em SEGUNDO PLANO (&) para liberar o terminal
./mediamtx &
```

## PASSO 7: Resolver Dependências e Inicializar o Frontend (Angular)

```bash
# 1. Navega até a pasta do Frontend
cd ../tcc-nvr-frontend

# 2. Instala todos os pacotes e dependências do Node.js
npm install

# 3. ATENÇÃO AQUI, CASO FOR RODAR O ANGULAR LOCAL -> Executa o Angular em SEGUNDO PLANO de forma persistente (nohup) e silenciosa
nohup npm run start > angular.log 2>&1 &

# Caso for usar o apache
npm install
npm run build -- --configuration=production
```

## PASSO 8: Inicializar o Backend e Unificar o Sistema

```bash
# 1. Retorna para a pasta do Backend
cd ../tcc-nvr-backend

# 2. Inicializa o servidor Uvicorn do FastAPI na tela principal
uvicorn app.main:app --reload
```

## 💡 Comandos Utilitários de Monitoramento

Se em algum momento você precisar conferir se o Angular e o MediaMTX continuam rodando em segundo plano, use:

```bash
# Lista os processos que estão rodando em segundo plano nesta sessão do terminal
jobs
```

---

## 🌐 Configuração do Servidor Web Apache

O Apache atuará como o servidor web principal, servindo os arquivos estáticos do Angular na porta 80 e realizando proxy reverso das requisições de API para o backend.

### Passo 1.1: Criar o arquivo de configuração do site

Crie um novo arquivo de configuração específico para o projeto:

```bash
sudo nano /etc/apache2/sites-available/tcc.conf
```

Cole o seguinte conteúdo dentro do arquivo (ajustando os caminhos se necessário):

```apache
<VirtualHost *:80>
    ServerName localhost

    # 1. Diretório dos arquivos estáticos do Angular compilado
    DocumentRoot /home/projeto_TCC/tcc-nvr-frontend/dist/tcc-nvr-frontend/browser

    <Directory /home/projeto_TCC/tcc-nvr-frontend/dist/tcc-nvr-frontend/browser>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        # Redirecionamento para evitar erro 404 nas rotas internas do Angular
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule ^ index.html [L]
    </Directory>

    # 2. Proxy Reverso para o Backend FastAPI (Uvicorn)
    ProxyRequests Off
    ProxyPreserveHost On
    
    ProxyPass /api http://127.0.0.1:8000/api
    ProxyPassReverse /api http://127.0.0.1:8000/api

    ErrorLog ${APACHE_LOG_DIR}/tcc_error.log
    CustomLog ${APACHE_LOG_DIR}/tcc_access.log combined
</VirtualHost>
```

### Passo 1.2: Habilitar módulos e aplicar configurações

Execute os comandos para desativar o site padrão do Apache, ativar o site do TCC e habilitar os módulos de proxy e roteamento:

```bash
# Desativar o site padrão do Ubuntu
sudo a2dissite 000-default.conf

# Ativar o site do TCC
sudo a2ensite tcc.conf

# Habilitar os módulos necessários
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod rewrite

# Testar se a sintaxe do arquivo está correta
sudo apache2ctl configtest

# Caso essa comando acima não funcione, voce precisa dar permissao
chmod 755 /home/seu_usuario
```

> **Nota:** Certifique-se de que o retorno do comando acima seja `Syntax OK`.

### Passo 1.3: Reiniciar o serviço

```bash
sudo systemctl restart apache2
```

---

✅ **Instalação Completa!** O sistema está pronto para uso.
