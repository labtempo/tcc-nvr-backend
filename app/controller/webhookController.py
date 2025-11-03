from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select
from app.domain.record import Record
from app.domain.camera import Camera # <--- ASSUMINDO QUE VOCÊ TEM ESSE MODELO
from app.dtos.webhook import MediaMTXWebhookPayload
from app.resources.database.connection import get_session

# Este router é SÓ para webhooks, não para usuários
router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"]
)

@router.post(
    "/recording-ready",
    summary="Webhook para receber notificação de gravação do mediaMTX"
)
async def webhook_gravacao_pronta(
    # 1. Recebe o JSON do mediaMTX e converte usando o DTO
    payload: MediaMTXWebhookPayload = Body(...), 
    session: Session = Depends(get_session)
    # 2. NOTE: SEM AUTENTICAÇÃO DE USUÁRIO!
):
    """
    Este endpoint é chamado DIRETAMENTE pelo mediaMTX (via runOnRecordClose).
    Ele deve ser anônimo (sem autenticação) e rápido.
    """
    try:
        camera = session.exec(
            select(Camera).where(Camera.stream_path == payload.stream_path)
        ).first()
        
        if not camera:
            # Se a câmera não está cadastrada no seu banco, o mediaMTX
            # vai gravar, mas sua API não vai salvar o registro.
            print(f"Erro: Câmera com stream_path '{payload.stream_path}' não encontrada.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Câmera com path '{payload.stream_path}' não cadastrada."
            )

        
        url_acesso = f"/api/v1/videos/{payload.nome_arquivo}"
        
        nova_gravacao = Record(
            camera_id=camera.id,  
            stream_path=payload.stream_path,
            nome_arquivo=payload.nome_arquivo,
            url_acesso=url_acesso,
            duracao_segundos=payload.duracao_segundos,
            data_inicio_segmento=payload.data_inicio_segmento,
            data_fim_segmento=payload.data_fim_segmento
        )
        
        session.add(nova_gravacao)
        session.commit()
        session.refresh(nova_gravacao)
        
        print(f"Webhook: Gravação salva com sucesso - {nova_gravacao.nome_arquivo}")
        
        return {"status": "sucesso", "record_id": nova_gravacao.id}

    except Exception as e:
        print(f"Erro ao processar webhook do mediaMTX: {e}")
        session.rollback() # Desfaz qualquer mudança no banco
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar a gravação: {str(e)}"
        )