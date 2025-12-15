param (
    [string]$CameraName = "cam1"
)

$ErrorActionPreference = "Stop"

$SafeName = $CameraName.ToLower().Replace(" ", "_")
$RtspPath = "$SafeName"
$RtspUrl = "rtsp://host.docker.internal:8554/$RtspPath"
$ApiUrl = "http://localhost:8000/api/v1"
$AdminEmail = "admin@sistema.com"  # Updated to match the readme/db value
$AdminPass = "sua_senha"            # Updated to match the readme/db value

Write-Host "=== Configuração da Simulação ===" -ForegroundColor Cyan
Write-Host "Nome da Câmera: $CameraName"
Write-Host "Path no MediaMTX: $RtspPath"
Write-Host "URL de Destino: $RtspUrl"
Write-Host "=================================" -ForegroundColor Cyan

function Register-Camera {
    Write-Host "[Auto-Register] Tentando logar como admin..." -ForegroundColor Yellow
    
    try {
        $LoginBody = @{
            email = $AdminEmail
            password = $AdminPass # Fixed param name from DB check if needed, mainly it is 'password' in payload
        } | ConvertTo-Json

        $LoginResponse = Invoke-RestMethod -Uri "$ApiUrl/login" -Method Post -Body $LoginBody -ContentType "application/json"
        $Token = $LoginResponse.access_token

        if ([string]::IsNullOrEmpty($Token)) {
            Write-Error "[Auto-Register] Token não recebido. Verifique credenciais."
        }

        Write-Host "[Auto-Register] Login realizado. Registrando câmera..." -ForegroundColor Green

        $RegisterBody = @{
            name = $CameraName
            rtsp_url = "publisher"
            is_recording = $true
        } | ConvertTo-Json

        $Headers = @{
            Authorization = "Bearer $Token"
        }

        try {
            $RegisterResponse = Invoke-RestMethod -Uri "$ApiUrl/camera" -Method Post -Body $RegisterBody -ContentType "application/json" -Headers $Headers
            Write-Host "[Auto-Register] Câmera registrada com sucesso! ID: $($RegisterResponse.id)" -ForegroundColor Green
        } catch {
            $ErrorResponse = $_.Exception.Response.GetResponseStream()
            $Reader = New-Object System.IO.StreamReader($ErrorResponse)
            $Detail = $Reader.ReadToEnd()
            
            if ($Detail -match "Já existe" -or $_.Exception.Message -match "409") {
                Write-Host "[Auto-Register] A câmera já estava registrada." -ForegroundColor Yellow
            } else {
                Write-Host "[Auto-Register] Falha ao registrar câmera: $Detail" -ForegroundColor Red
            }
        }

    } catch {
        Write-Host "[Auto-Register] Erro ao conectar na API: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Certifique-se que o backend está rodando em localhost:8000" -ForegroundColor Gray
    }
}

# Register synchronously before starting stream
Register-Camera

Write-Host "Iniciando FFmpeg via Docker..." -ForegroundColor Cyan
Write-Host "Para parar, pressione CTRL+C" -ForegroundColor Cyan

while ($true) {
    docker run --rm -i `
      jrottenberg/ffmpeg:4.1-alpine `
      -re `
      -f lavfi -i "testsrc=size=1280x720:rate=30" `
      -c:v libx264 `
      -pix_fmt yuv420p `
      -preset ultrafast `
      -tune zerolatency `
      -f rtsp `
      -rtsp_transport tcp `
      $RtspUrl

    Write-Host "FFmpeg parou ou caiu. Reiniciando em 2 segundos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}
