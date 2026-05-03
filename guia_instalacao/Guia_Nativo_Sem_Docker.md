# Guia Completo de Instalação do NVR (100% Nativo / Sem Docker)

Este guia destina-se a configurar e rodar o sistema **INTEIRO** (Backend, Banco de Dados, Servidor de Streaming e Frontend) diretamente na máquina, sem a utilização de Docker. Este tutorial foi escrito com foco no ambiente **Windows**.

---

## 1. Instalando os Programas Necessários (Pré-requisitos)

Como não estamos usando o Docker, precisamos instalar as ferramentas base individualmente.

### A. Python (Linguagem do Backend)
1. Acesse o site: [https://www.python.org/downloads/](https://www.python.org/downloads/) e baixe a versão mais recente (3.11+).
2. Execute o instalador.
3. **MUITO IMPORTANTE:** Na primeira tela de instalação, marque a caixa **"Add Python to PATH"** (Adicionar Python ao PATH).
4. Clique em "Install Now".

### B. PostgreSQL (Banco de Dados)
1. Acesse o site: [https://www.enterprisedb.com/downloads/postgres-postgresql-downloads](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) e baixe o instalador para Windows.
2. Siga o instalador clicando em "Next".
3. Quando for solicitada uma senha para o superusuário (`postgres`), digite uma de sua preferência e **anote-a**.
4. Mantenha a porta padrão (`5432`).
5. Termine a instalação (você pode desmarcar o "Stack Builder" no final).

### C. Node.js (Ambiente do Frontend)
1. Acesse o site: [https://nodejs.org/](https://nodejs.org/) e baixe a versão **LTS (Long Term Support)**.
2. Instale mantendo todas as configurações padrão ("Next" até o fim).

### D. Git (Gerenciador de Códigos)
1. Acesse o site: [https://git-scm.com/downloads](https://git-scm.com/downloads) e baixe para Windows.
2. Instale mantendo as opções padrão.

---

## 2. Preparando o Banco de Dados (pgAdmin)

Junto com o PostgreSQL, foi instalado um programa visual chamado **pgAdmin**. Vamos usá-lo para criar o banco de dados que o NVR irá utilizar.

1. Abra o **pgAdmin 4** no seu computador (busque no menu Iniciar).
2. No menu lateral esquerdo, expanda **Servers** -> **PostgreSQL**. Ele pedirá a senha que você criou na instalação.
3. Precisamos criar as credenciais do sistema. Clique com o botão direito em **Login/Group Roles** -> **Create** -> **Login/Group Role...**
   - Na aba **General**, digite o nome do usuário: `tcc_usr`
   - Na aba **Definition**, digite a senha: `tcc_pwd`
   - Na aba **Privileges**, marque "Can login?" como **Yes** e "Superuser?" como **Yes**. Clique em Save.
4. Agora vamos criar o banco. Clique com o botão direito em **Databases** -> **Create** -> **Database...**
   - Na aba **General**, no campo **Database**, digite: `tcc_db`
   - No campo **Owner**, selecione o usuário que criamos no passo anterior: `tcc_usr`
   - Clique em **Save**.

---

## 3. Baixando o Projeto

1. Crie uma pasta na sua Área de Trabalho chamada `Projeto_TCC`.
2. Abra essa pasta, clique com o botão direito em um espaço vazio e escolha **"Abrir no Terminal"** (ou "Open in Terminal" / "Git Bash Here").
3. Execute os dois comandos abaixo para baixar os repositórios do Backend e do Frontend:

```bash
git clone https://github.com/SEU_USUARIO/tcc-nvr-backend.git tcc-nvr-backend
git clone https://github.com/SEU_USUARIO/tcc-nvr-frontend.git tcc-nvr-frontend
```

*(Substitua a URL pela do seu projeto real)*.

Sua pasta deve ficar estruturada assim:
```text
Projeto_TCC/
 ├── tcc-nvr-backend/
 └── tcc-nvr-frontend/
```

---

## 4. Configurando e Rodando o Backend + MediaMTX

Para facilitar a vida no Windows, o projeto possui um script automatizado (`run_native_no_docker.ps1`) que resolve o download do servidor de vídeo (MediaMTX), instala as dependências do Python e inicia a API.

1. Abra o **PowerShell** (você pode pesquisar por PowerShell no menu iniciar).
2. Navegue até a pasta do backend digitando o comando `cd` e o caminho até ela:
   ```powershell
   cd Caminho\Para\Projeto_TCC\tcc-nvr-backend
   ```
3. Execute o script de automação:
   ```powershell
   .\run_native_no_docker.ps1
   ```
   > **⚠️ Aviso de Permissão:** Caso dê erro de permissão de script vermelho no PowerShell, digite o seguinte comando primeiro, aperte enter, aceite com 'Y' e tente o passo 3 novamente: 
   > `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted`

**O que este script faz automaticamente por você:**
- Baixa e extrai o **MediaMTX** (servidor de streaming) se não existir.
- Cria o arquivo de configuração local `.env`.
- Cria um ambiente Python (venv) e instala as dependências.
- Inicializa e popula o banco de dados com um usuário Admin (`admin@sistema.com` | `admin123`).
- Abre o **MediaMTX** em uma nova janela para gerenciar o vídeo.
- Inicia a API do **Backend FastAPI**.

Deixe essa janela do PowerShell aberta! Se você a fechar, o servidor desliga.

---

## 5. Configurando e Rodando o Frontend

Agora precisamos rodar a interface gráfica para o usuário final.

1. Abra um **novo** Terminal (pode ser o CMD ou outro PowerShell).
2. Navegue até a pasta do frontend:
   ```bash
   cd Caminho\Para\Projeto_TCC\tcc-nvr-frontend
   ```
3. Instale as dependências do painel (isso só precisa ser feito uma única vez):
   ```bash
   npm install
   ```
4. Se o frontend necessitar de configuração local para o endereço do backend, crie ou altere o arquivo `.env` dentro da pasta do frontend, apontando para:
   `VITE_API_URL=http://localhost:8000/api/v1` (ou a variável usada pelo seu projeto).
5. Inicie o painel visual:
   ```bash
   npm run dev
   ```

Ele mostrará uma mensagem verde de sucesso informando em qual endereço a página está rodando (geralmente vai ser `http://localhost:5173` ou `http://localhost:3000`).

---

## 6. Acessando o Sistema Final

Com todos os serviços online (PostgreSQL, MediaMTX, Backend e Frontend):

1. Abra seu navegador de internet e acesse o endereço que apareceu no terminal do Frontend (Ex: **http://localhost:5173**).
2. Faça o login utilizando a conta de administrador gerada automaticamente:
   - **E-mail:** `admin@sistema.com`
   - **Senha:** `admin123`

Pronto! Você agora possui um sistema de NVR rodando de forma 100% nativa no seu computador, podendo registrar câmeras e assistir transmissões.

---

## Como encerrar o sistema?
Quando terminar de utilizar o sistema e quiser fechar tudo:
- Volte na janela de Terminal do **Frontend** e pressione `Ctrl + C`.
- Volte na janela do PowerShell do **Backend** e pressione `Ctrl + C`. 
  - O script foi programado para também tentar fechar a janela do MediaMTX automaticamente após você parar o Backend.
- O Banco de Dados continuará rodando invisível como um serviço do Windows, gastando muito pouca memória, pronto para a próxima vez que você ligar as aplicações.
