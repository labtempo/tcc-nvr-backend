import httpx
import sys
import time

# Configurações
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@sistema.com"
ADMIN_PASS = "admin123"

# Cores para terminal
VERDE = "\033[92m"
VERMELHO = "\033[91m"
RESET = "\033[0m"

def log(msg, tipo="INFO"):
    if tipo == "SUCESSO":
        print(f"{VERDE}[SUCESSO] {msg}{RESET}")
    elif tipo == "ERRO":
        print(f"{VERMELHO}[ERRO] {msg}{RESET}")
    else:
        print(f"[INFO] {msg}")

def main():
    log("Iniciando Testes de RBAC (Controle de Acesso)...")
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Login como Admin
        log("1. Tentando login como Admin...")
        resp = client.post("/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        if resp.status_code != 200:
            log(f"Falha no login Admin: {resp.text}", "ERRO")
            sys.exit(1)
        
        token_admin = resp.json()["access_token"]
        role_admin = resp.json().get("role")
        user_id_admin = resp.json()["user_id"]
        
        if role_admin != "admin":
            log(f"Role do admin incorreta: {role_admin}", "ERRO")
        else:
            log(f"Login Admin OK. Role identificada: {role_admin}", "SUCESSO")

        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        # 2. Criar Usuário Viewer
        viewer_email = f"viewer_{int(time.time())}@teste.com"
        viewer_pass = "senha123"
        log(f"2. Criando usuário Viewer ({viewer_email})...")
        
        resp = client.post("/usuarios", json={
            "email": viewer_email,
            "password": viewer_pass,
            "full_name": "Usuário Teste Viewer"
        }, headers=headers_admin)
        
        if resp.status_code != 200:
            log(f"Falha ao criar usuário: {resp.text}", "ERRO")
            sys.exit(1)
        
        log("Usuário Viewer criado com sucesso.", "SUCESSO")

        # 3. Login como Viewer
        log("3. Tentando login como Viewer...")
        resp = client.post("/login", json={"email": viewer_email, "password": viewer_pass})
        if resp.status_code != 200:
            log(f"Falha no login Viewer: {resp.text}", "ERRO")
            sys.exit(1)
            
        token_viewer = resp.json()["access_token"]
        role_viewer = resp.json().get("role")
        
        if role_viewer != "viewer":
            log(f"Role do viewer incorreta: {role_viewer} (Esperado: viewer)", "ERRO")
        else:
            log(f"Login Viewer OK. Role identificada: {role_viewer}", "SUCESSO")

        headers_viewer = {"Authorization": f"Bearer {token_viewer}"}

        # 4. Viewer tentando criar Câmera (Deve FALHAR 403)
        log("4. Testando bloqueio: Viewer tentando criar câmera...")
        resp = client.post("/camera", json={
            "name": "Câmera Proibida",
            "rtsp_url": "rtsp://fake/1",
            "is_recording": False
        }, headers=headers_viewer)
        
        if resp.status_code == 403:
            log("Viewer foi bloqueado corretamente ao tentar criar câmera (403 Forbidden).", "SUCESSO")
        else:
            log(f"Falha de segurança! Viewer conseguiu criar câmera ou erro inesperado. Status: {resp.status_code}", "ERRO")

        # 5. Viewer listando TODAS as câmeras (Deve SUCESSO 200)
        log("5. Viewer listando todas as câmeras (GET /cameras)...")
        resp = client.get("/cameras", headers=headers_viewer)
        
        if resp.status_code == 200:
            cameras = resp.json()
            log(f"Viewer listou câmeras com sucesso. Total encontradas: {len(cameras)}", "SUCESSO")
        else:
            log(f"Erro ao listar câmeras como Viewer. Status: {resp.status_code} - {resp.text}", "ERRO")

        # 6. Admin tentando criar Câmera (Deve Funcionar - Mock)
        # Não vamos criar de verdade para não poluir ou precisar de MediaMTX ativo, mas vamos verificar se NÃO é 403
        # Se o MediaMTX não estiver rodando, vai dar 503 ou 500, mas não 403.
        log("6. Verificando permissão de Admin criar câmera...")
        resp = client.post("/camera", json={
            "name": f"CamTeste_{int(time.time())}",
            "rtsp_url": "rtsp://localhost:8554/cam_teste",
            "is_recording": False
        }, headers=headers_admin)
        
        if resp.status_code == 403:
             log("Admin foi bloqueado incorretamente (403).", "ERRO")
        elif resp.status_code in [200, 201]:
             log("Admin criou câmera com sucesso.", "SUCESSO")
        else:
             # Pode dar erro de MediaMTX, mas importante é não ser 403
             log(f"Admin passou da verificação de permissão (Status: {resp.status_code}).", "SUCESSO")

    log("\nResumo dos Testes Finalizado.", "INFO")

if __name__ == "__main__":
    main()
