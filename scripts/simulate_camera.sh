#!/bin/bash

# Check requirements
if ! command -v jq &> /dev/null; then
    echo "Erro: 'jq' não está instalado. Por favor, instale-o para continuar."
    exit 1
fi

CAMERA_NAME=${1:-cam1}
# Formata o nome para o padrão do backend (live/nome_da_camera)
# Assume que o backend faz lower() e replace(' ', '_')
SAFE_NAME=$(echo "$CAMERA_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
RTSP_PATH="live/${SAFE_NAME}"
RTSP_URL="rtsp://host.docker.internal:8554/${RTSP_PATH}"

API_URL="http://localhost:8000/api/v1"
ADMIN_EMAIL="admin@admin.com"
ADMIN_PASS="sua_senha"

echo "=== Configuração da Simulação ==="
echo "Nome da Câmera: ${CAMERA_NAME}"
echo "Path no MediaMTX: ${RTSP_PATH}"
echo "URL de Destino: ${RTSP_URL}"
echo "================================="

# Função para registrar a câmera em background
register_camera() {
    echo "[Auto-Register] Aguardando inicio do stream..."
    sleep 5

    echo "[Auto-Register] Tentando logar como admin..."
    LOGIN_RESP=$(curl -s -X POST "${API_URL}/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"${ADMIN_EMAIL}\", \"password\": \"${ADMIN_PASS}\"}")

    TOKEN=$(echo "$LOGIN_RESP" | jq -r '.access_token')

    if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
        echo "[Auto-Register] Erro ao fazer login. Verifique as credenciais ou se o backend está rodando."
        echo "Resposta: $LOGIN_RESP"
        return
    fi

    echo "[Auto-Register] Login realizado com sucesso. Registrando câmera..."
    
    # Tenta registrar a câmera. Se ela já existir, o backend deve retornar 400, o que é aceitável aqui.
    # Note que enviamos rtsp_url="publisher" para que o backend configure o path para aceitar publicação.
    REGISTER_RESP=$(curl -s -X POST "${API_URL}/camera" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d "{
            \"name\": \"${CAMERA_NAME}\",
            \"rtsp_url\": \"publisher\",
            \"is_recording\": false
        }")
    
    # Verifica se deu certo ou se já existe
    if echo "$REGISTER_RESP" | jq -e '.id' > /dev/null; then
        echo "[Auto-Register] Câmera registrada com sucesso! ID: $(echo "$REGISTER_RESP" | jq -r '.id')"
    else
        DETAIL=$(echo "$REGISTER_RESP" | jq -r '.detail')
        if [[ "$DETAIL" == *"Já existe"* ]]; then
            echo "[Auto-Register] A câmera já estava registrada."
        else
            echo "[Auto-Register] Falha ao registrar câmera."
            echo "Erro: $DETAIL"
        fi
    fi
}

# Inicia o registro em background
register_camera &
REG_PID=$!

# Garante que matamos o processo de registro se o script parar
trap "kill $REG_PID 2>/dev/null" EXIT

echo "Iniciando FFmpeg..."
echo "Para parar, pressione CTRL+C"

# Loop infinito para garantir que se o backend resetar a conexão (ao criar o path), o ffmpeg reconecte.
while true; do
    docker run --rm -i \
      jrottenberg/ffmpeg:4.1-alpine \
      -re \
      -f lavfi -i "testsrc=size=1280x720:rate=30" \
      -c:v libx264 \
      -pix_fmt yuv420p \
      -preset ultrafast \
      -tune zerolatency \
      -f rtsp \
      -rtsp_transport tcp \
      "${RTSP_URL}"
    
    echo "FFmpeg parou ou caiu. Reiniciando em 2 segundos..."
    sleep 2
done
