# run_native_no_docker.ps1
# Script para configurar e rodar 100% nativo no Windows (Sem Docker)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Configuração 100% Nativa - TCC NVR Backend (Sem Docker)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Instruções para PostgreSQL (Dependência Manual)
Write-Host "`n[1] Verificação do PostgreSQL" -ForegroundColor Yellow
Write-Host "Como estamos rodando sem Docker, você DEVE ter o PostgreSQL instalado no seu Windows." -ForegroundColor White
Write-Host "Certifique-se de que:" -ForegroundColor White
Write-Host "  - O PostgreSQL está rodando na porta 5432 (padrão)." -ForegroundColor White
Write-Host "  - Você criou o banco de dados: tcc_db" -ForegroundColor White
Write-Host "  - Você criou o usuário 'tcc_usr' com senha 'tcc_pwd'." -ForegroundColor White
Write-Host "  - DICA: Você pode rodar o código do ./init.sql no pgAdmin para criar o schema inicial se necessário." -ForegroundColor White
Read-Host "Pressione ENTER quando tiver certeza que o PostgreSQL está rodando localmente..."

# 2. Baixar MediaMTX
Write-Host "`n[2] Configurando MediaMTX" -ForegroundColor Yellow
$mediamtxExe = "mediamtx.exe"
if (-Not (Test-Path -Path $mediamtxExe)) {
    Write-Host "MediaMTX não encontrado. Baixando a versão v1.6.0 (Windows AMD64)..." -ForegroundColor Cyan
    $url = "https://github.com/bluenviron/mediamtx/releases/download/v1.6.0/mediamtx_v1.6.0_windows_amd64.zip"
    Invoke-WebRequest -Uri $url -OutFile "mediamtx.zip"
    Expand-Archive -Path "mediamtx.zip" -DestinationPath "." -Force
    Remove-Item "mediamtx.zip"
    Write-Host "MediaMTX baixado e extraído com sucesso!" -ForegroundColor Green
} else {
    Write-Host "MediaMTX (mediamtx.exe) já está na pasta do projeto." -ForegroundColor Green
}

# 3. Configurar .env nativo
Write-Host "`n[3] Configurando variáveis de ambiente (.env)" -ForegroundColor Yellow
$envContent = @"
# Usa a porta nativa do PostgreSQL (geralmente 5432)
DATABASE_URL=postgresql://tcc_usr:tcc_pwd@localhost:5432/tcc_db

# Usa as portas padroes do MediaMTX localmente (Sem os redirecionamentos do docker)
MEDIA_MTX_HOST=http://localhost
CONTROL_API_PORT=9997
MEDIA_MTX_PLAYBACK_PORT=9996
HLS_PORT=8888
WEBRTC_PORT=8889

MEDIAMTX_API_USER=api-backend
MEDIAMTX_API_PASS=UMA_SENHA_FORTE_E_SECRETA_AQUI
SECRET_KEY=dev_secret_key_change_me_in_prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

PUBLIC_SERVER_IP=127.0.0.1
PUBLIC_HLS_PORT=8888
PUBLIC_WEBRTC_PORT=8889
"@
Set-Content -Path ".env" -Value $envContent -Encoding UTF8
Write-Host "Arquivo .env configurado." -ForegroundColor Green

# 4. Configurar VENV Python
Write-Host "`n[4] Configurando ambiente Python" -ForegroundColor Yellow
if (-Not (Test-Path -Path "venv")) {
    Write-Host "Criando ambiente virtual (venv)..." -ForegroundColor Cyan
    python -m venv venv
}
Write-Host "Instalando dependências..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe -m pip install --upgrade pip | Out-Null
& .\venv\Scripts\python.exe -m pip install -r requirements.txt

# 5. Semeando banco
Write-Host "`n[5] Criando usuário admin no banco de dados (se não existir)..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\python.exe seed_admin.py
} catch {
    Write-Host "ERRO: Falha ao semear o banco. O PostgreSQL está rodando com o user/db correto?" -ForegroundColor Red
}

# 6. Iniciar Servidores
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " Iniciando a Aplicação" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Write-Host "Iniciando MediaMTX em nova janela..." -ForegroundColor Yellow
Start-Process -FilePath ".\mediamtx.exe" -WindowStyle Normal

Write-Host "Iniciando FastAPI nativamente..." -ForegroundColor Green
Write-Host "Swagger Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Pressione Ctrl+C para parar a API." -ForegroundColor Green

& .\venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Quando a API for interrompida, fechar o mediamtx
Write-Host "`nEncerrando MediaMTX..." -ForegroundColor Yellow
Stop-Process -Name "mediamtx" -ErrorAction SilentlyContinue
Write-Host "Encerrado com sucesso." -ForegroundColor Green
