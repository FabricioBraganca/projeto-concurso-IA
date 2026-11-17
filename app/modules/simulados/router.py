from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import SimuladoGerarRequest, SubmeterSimuladoRequest, SimuladoRecuperacaoRequest
from app.modules.simulados.service import (
    criar_e_gerar_simulado,
    processar_respostas_simulado,
    obter_resumo_desempenho,
    obter_caderno_erros,
    gerar_simulado_recuperacao
)
from app.models import Simulado, Questao, User
from app.core.auth_dependency import get_optional_current_user
from app.core.rate_limiter import rate_limit

router = APIRouter(prefix="/simulados", tags=["Simulados"])


@router.post("/gerar")
def api_gerar_simulado(
    dados: SimuladoGerarRequest,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_optional_current_user),
    _limit: bool = Depends(rate_limit("simulado_gerar", max_requests=15, window_seconds=3600))
):
    """Gera um novo caderno de simulado via Gemini AI e persiste no banco (protegido por rate limit)."""
    simulado = criar_e_gerar_simulado(db, dados, user_id=usuario.id)
    return {
        "id": simulado.id,
        "titulo": simulado.titulo,
        "total_questoes": simulado.total_questoes,
        "banca": simulado.banca_filtro,
        "tema": simulado.tema_filtro
    }


@router.get("/")
def api_listar_simulados(db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """Retorna a lista de simulados do usuário."""
    simulados = db.query(Simulado).filter(Simulado.user_id == usuario.id).order_by(Simulado.id.desc()).all()
    return [
        {
            "id": s.id,
            "titulo": s.titulo,
            "banca": s.banca_filtro,
            "tema": s.tema_filtro,
            "total_questoes": s.total_questoes,
            "concluido": s.concluido,
            "score_final": s.score_final,
            "acertos": s.acertos,
            "data_criacao": s.criado_em.isoformat() if s.criado_em else None
        }
        for s in simulados
    ]


@router.get("/caderno-erros")
def api_consultar_caderno_erros(
    tema: Optional[str] = Query(None, description="Filtrar erros por disciplina"),
    banca: Optional[str] = Query(None, description="Filtrar erros por banca"),
    db: Session = Depends(get_db),
    usuario: User = Depends(get_optional_current_user)
):
    """
    Retorna todas as questões que o estudante errou nos simulados, agrupadas por disciplina.
    """
    return obter_caderno_erros(db, user_id=usuario.id, tema=tema, banca=banca)


@router.post("/recuperacao")
def api_gerar_simulado_recuperacao(
    dados: SimuladoRecuperacaoRequest,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_optional_current_user)
):
    """
    Cria automaticamente um simulado focado apenas no refazimento das questões erradas pelo concurseiro.
    """
    try:
        simulado = gerar_simulado_recuperacao(
            db,
            user_id=usuario.id,
            tema=dados.tema,
            banca=dados.banca,
            quantidade=dados.quantidade
        )
        return {
            "id": simulado.id,
            "titulo": simulado.titulo,
            "total_questoes": simulado.total_questoes,
            "mensagem": "Simulado de recuperação gerado com sucesso a partir do seu caderno de erros!"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{simulado_id}")
def api_obter_simulado(simulado_id: int, db: Session = Depends(get_db)):
    """Retorna detalhes completos do simulado e suas questões."""
    simulado = db.query(Simulado).filter(Simulado.id == simulado_id).first()
    if not simulado:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")

    questoes = db.query(Questao).filter(Questao.simulado_id == simulado_id).order_by(Questao.ordem).all()

    return {
        "id": simulado.id,
        "titulo": simulado.titulo,
        "banca": simulado.banca_filtro,
        "tema": simulado.tema_filtro,
        "concluido": simulado.concluido,
        "score_final": simulado.score_final,
        "acertos": simulado.acertos,
        "questoes": [
            {
                "id": q.id,
                "ordem": q.ordem,
                "enunciado": q.enunciado,
                "alternativas": q.alternativas,
                "resposta_usuario": q.resposta_usuario,
                "resposta_certa": q.resposta_certa if simulado.concluido else None,
                "explicacao_ia": q.explicacao_ia if simulado.concluido else None,
                "acertou": q.acertou
            }
            for q in questoes
        ]
    }


@router.post("/{simulado_id}/responder")
def api_responder_simulado(simulado_id: int, payload: SubmeterSimuladoRequest, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """Calcula acertos, gabarito e atualiza as estatísticas de desempenho."""
    try:
        resultado = processar_respostas_simulado(db, simulado_id, payload, user_id=usuario.id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
