from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.dtos.record import RecordCreate, RecordData
from app.domain.record import Record
from app.domain.user import User
from app.security.security import pegar_usuario_atual
from app.resources.database.connection import get_session

router = APIRouter()

@router.post("/record", response_model=RecordData)
async def criar_gravacao(
    dados_gravacao: RecordCreate,
    session: Session = Depends(get_session),
    usuario_atual: User = Depends(pegar_usuario_atual)
):
    
    url_acesso = f"/recordings/{dados_gravacao.nome_arquivo}"
    
    
    nova_gravacao = Record(
        camera_id=dados_gravacao.camera_id,
        nome_arquivo=dados_gravacao.nome_arquivo,
        url_acesso=url_acesso,
        duracao_segundos=dados_gravacao.duracao_segundos,
        data_inicio_segmento=dados_gravacao.data_inicio_segmento,
        data_fim_segmento=dados_gravacao.data_fim_segmento
    )
    

    session.add(nova_gravacao)
    session.commit()
    session.refresh(nova_gravacao)
    
    return nova_gravacao