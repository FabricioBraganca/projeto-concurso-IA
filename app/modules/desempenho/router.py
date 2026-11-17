from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.simulados.service import obter_resumo_desempenho

from app.models import User
from app.core.auth_dependency import get_optional_current_user

router = APIRouter(prefix="/desempenho", tags=["Desempenho"])


@router.get("/geral")
def api_desempenho_geral(db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """Retorna métricas consolidadas de acertos, simulados e estatísticas por tema."""
    return obter_resumo_desempenho(db, user_id=usuario.id)

