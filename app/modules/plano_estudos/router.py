from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import PlanoEstudos, User
from app.schemas import PlanoEstudosGerarRequest
from app.modules.ai.service import ai_service
from app.core.auth_dependency import get_optional_current_user

router = APIRouter(prefix="/plano-estudos", tags=["Plano de Estudos IA"])


@router.post("/gerar")
def api_gerar_plano(dados: PlanoEstudosGerarRequest, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """
    Gera um plano semanal inteligente com o Gemini AI e o persiste no banco de dados.
    """
    plano_dict = ai_service.gerar_plano_estudos(
        concurso=dados.concurso_alvo,
        cargo=dados.cargo,
        horas=dados.horas_por_dia,
        dias=dados.dias_semana,
        dificuldades=dados.dificuldades_principais or "Gerais"
    )

    novo_plano = PlanoEstudos(
        user_id=usuario.id,
        concurso_alvo=dados.concurso_alvo,
        cargo=dados.cargo,
        horas_por_dia=dados.horas_por_dia,
        dias_semana=dados.dias_semana,
        conteudo_json=plano_dict
    )
    db.add(novo_plano)
    db.commit()
    db.refresh(novo_plano)

    return {
        "id": novo_plano.id,
        "concurso_alvo": novo_plano.concurso_alvo,
        "plano": plano_dict
    }


@router.get("/ativo")
def api_obter_plano_ativo(db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """
    Recupera o plano de estudos mais recente gerado para o estudante.
    """
    plano = db.query(PlanoEstudos).filter(PlanoEstudos.user_id == usuario.id).order_by(PlanoEstudos.id.desc()).first()
    if not plano:
        # Se não houver, gera o padrão inicial
        req = PlanoEstudosGerarRequest()
        return api_gerar_plano(req, db, usuario=usuario)

    return {
        "id": plano.id,
        "concurso_alvo": plano.concurso_alvo,
        "cargo": plano.cargo,
        "horas_por_dia": plano.horas_por_dia,
        "dias_semana": plano.dias_semana,
        "plano": plano.conteudo_json
    }
