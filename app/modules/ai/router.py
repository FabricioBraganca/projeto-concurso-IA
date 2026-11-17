from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import ChatRequest, ExplicarQuestaoRequest
from app.modules.ai.service import ai_service
from app.models import ChatHistorico, User
from app.core.auth_dependency import get_optional_current_user
from app.core.rate_limiter import rate_limit

router = APIRouter(prefix="/ai", tags=["Inteligência Artificial"])


@router.post("/chat")
def api_chat_tutor(
    dados: ChatRequest,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_optional_current_user),
    _limit: bool = Depends(rate_limit("ai_chat", max_requests=40, window_seconds=3600))
):
    """Conversa em tempo real com o Tutor de Concursos da IA."""
    # Recupera histórico recente
    historico_recente = (
        db.query(ChatHistorico)
        .filter(ChatHistorico.session_id == dados.session_id, ChatHistorico.user_id == usuario.id)
        .order_by(ChatHistorico.id.desc())
        .limit(6)
        .all()
    )
    historico_formatado = [
        {"role": h.role, "mensagem": h.mensagem}
        for h in reversed(historico_recente)
    ]

    # Chama o tutor
    resposta = ai_service.chat_tutor(dados.mensagem, historico=historico_formatado)

    # Salva no histórico
    msg_user = ChatHistorico(session_id=dados.session_id, role="user", mensagem=dados.mensagem, user_id=usuario.id)
    msg_model = ChatHistorico(session_id=dados.session_id, role="model", mensagem=resposta, user_id=usuario.id)
    db.add(msg_user)
    db.add(msg_model)
    db.commit()

    return {"resposta": resposta}


@router.post("/explicar")
def api_explicar_questao(
    dados: ExplicarQuestaoRequest,
    _limit: bool = Depends(rate_limit("ai_explicar", max_requests=60, window_seconds=3600))
):
    """Explicação aprofundada de erro ou acerto com base doutrinária e legal (protegido por rate limit)."""
    explicacao = ai_service.explicar_questao(
        enunciado=dados.enunciado,
        alternativa_escolhida=dados.alternativa_escolhida,
        gabarito_correto=dados.resposta_correta,
        explicacao_base=dados.explicacao_base or ""
    )
    return {"explicacao": explicacao}
