from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Concurso, ProvaBanca
from app.modules.concursos.scraper import (
    buscar_concursos_rss,
    buscar_provas_bancas_online,
    sincronizar_concursos_background,
    obter_status_sincronizacao,
    _obter_concursos_fallback
)

router = APIRouter(prefix="/radar", tags=["Radar de Concursos e Bancas"])


@router.get("/concursos")
def api_listar_concursos(
    background_tasks: BackgroundTasks,
    regiao: Optional[str] = Query(None, description="Filtro por região ou UF"),
    carreira: Optional[str] = Query(None, description="Filtro por carreira"),
    banca: Optional[str] = Query(None, description="Filtro por banca examinadora"),
    db: Session = Depends(get_db)
):
    """
    Retorna a lista dinâmica e atualizada de concursos públicos com carregamento ultra-rápido.
    """
    concursos_db = db.query(Concurso).all()
    if not concursos_db:
        # Se vazio, carrega imediatamente a base de editais curados (< 5ms)
        for item in _obter_concursos_fallback():
            c = Concurso(**item)
            db.add(c)
        db.commit()
        concursos_db = db.query(Concurso).all()
        # E agenda a atualização online via RSS em segundo plano sem travar o usuário
        background_tasks.add_task(sincronizar_concursos_background)

    # Aplica filtros
    resultado = concursos_db
    if regiao:
        resultado = [c for c in resultado if regiao.lower() in (c.regiao or "").lower()]
    if carreira:
        resultado = [c for c in resultado if carreira.lower() in (c.carreira or "").lower()]
    if banca:
        resultado = [c for c in resultado if banca.lower() in (c.banca or "").lower()]

    return [
        {
            "id": c.id,
            "titulo": c.titulo,
            "orgao": c.orgao,
            "banca": c.banca,
            "regiao": c.regiao,
            "carreira": c.carreira,
            "cargos": c.cargos,
            "vagas": c.vagas,
            "salario": c.salario,
            "status": c.status,
            "data_inscricao_fim": c.data_inscricao_fim,
            "data_prova": c.data_prova,
            "link_edital": c.link_edital,
            "fonte": c.fonte
        }
        for c in resultado
    ]


@router.post("/concursos/atualizar", status_code=status.HTTP_202_ACCEPTED)
def api_sincronizar_concursos(background_tasks: BackgroundTasks):
    """
    Inicia a sincronização de editais e feed de notícias em segundo plano sem travar a requisição.
    """
    background_tasks.add_task(sincronizar_concursos_background)
    return {
        "status": "em_andamento",
        "mensagem": "Sincronização iniciada com sucesso em segundo plano. Os editais serão atualizados em instantes."
    }


@router.get("/concursos/status")
def api_status_sincronizacao():
    """
    Retorna se há uma raspagem ou atualização de concursos rodando em background no momento.
    """
    return obter_status_sincronizacao()



@router.get("/provas")
def api_listar_provas(
    banca: Optional[str] = Query(None, description="Filtro por banca"),
    termo: Optional[str] = Query(None, description="Filtro por órgão ou cargo"),
    db: Session = Depends(get_db)
):
    """
    Busca cadernos de prova reais de concursos das principais bancas examinadoras.
    """
    provas_db = db.query(ProvaBanca).all()
    if not provas_db:
        iniciais = buscar_provas_bancas_online()
        for p in iniciais:
            pb = ProvaBanca(**p)
            db.add(pb)
        db.commit()
        provas_db = db.query(ProvaBanca).all()

    resultado = provas_db
    if banca:
        resultado = [p for p in resultado if p.banca.lower() == banca.lower()]
    if termo:
        t = termo.lower()
        resultado = [
            p for p in resultado
            if t in p.orgao.lower() or t in p.cargo.lower() or t in (p.disciplinas_destaque or "").lower()
        ]

    return [
        {
            "id": p.id,
            "banca": p.banca,
            "orgao": p.orgao,
            "cargo": p.cargo,
            "ano": p.ano,
            "disciplinas_destaque": p.disciplinas_destaque,
            "pdf_url": p.pdf_url,
            "gabarito_url": p.gabarito_url,
            "fonte": p.fonte
        }
        for p in resultado
    ]
