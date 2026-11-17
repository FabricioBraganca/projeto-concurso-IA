from typing import List, Dict, Any, Optional
import re
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import Disciplina, Assunto, QuestaoBanco
from app.schemas import DisciplinaResponse, AssuntoResponse, DisciplinaCreateRequest, AssuntoCreateRequest
from app.seeds.questoes_seeder import popular_banco_se_vazio

router = APIRouter(prefix="/disciplinas", tags=["Catálogo de Disciplinas & Assuntos"])


def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


@router.get("/", response_model=List[DisciplinaResponse])
def api_listar_disciplinas(db: Session = Depends(get_db)):
    """
    Retorna todas as disciplinas com seus respectivos tópicos de edital.
    """
    disciplinas = db.query(Disciplina).order_by(Disciplina.nome).all()
    return disciplinas


@router.post("/", response_model=DisciplinaResponse, status_code=status.HTTP_201_CREATED)
def api_criar_disciplina(dados: DisciplinaCreateRequest, db: Session = Depends(get_db)):
    """
    Cadastra uma nova disciplina no catálogo e adiciona seus tópicos de edital.
    """
    slug = dados.slug or slugify(dados.nome)
    existente = db.query(Disciplina).filter((Disciplina.nome == dados.nome) | (Disciplina.slug == slug)).first()
    if existente:
        raise HTTPException(status_code=400, detail="Esta disciplina já está cadastrada no catálogo.")

    nova_disc = Disciplina(
        nome=dados.nome.strip(),
        icone=dados.icone or "📚",
        slug=slug
    )
    db.add(nova_disc)
    db.flush()

    for a_nome in dados.assuntos:
        if a_nome.strip():
            assunto = Assunto(disciplina_id=nova_disc.id, nome=a_nome.strip())
            db.add(assunto)

    db.commit()
    db.refresh(nova_disc)
    return nova_disc


@router.post("/{disciplina_id}/assuntos", response_model=AssuntoResponse, status_code=status.HTTP_201_CREATED)
def api_adicionar_assunto(disciplina_id: int, dados: AssuntoCreateRequest, db: Session = Depends(get_db)):
    """
    Adiciona um novo tópico/assunto a uma disciplina já existente.
    """
    disc = db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")

    novo_assunto = Assunto(disciplina_id=disc.id, nome=dados.nome.strip())
    db.add(novo_assunto)
    db.commit()
    db.refresh(novo_assunto)
    return novo_assunto


@router.get("/{disciplina_id}/assuntos", response_model=List[AssuntoResponse])
def api_listar_assuntos(disciplina_id: int, db: Session = Depends(get_db)):
    """
    Retorna os tópicos/assuntos específicos de uma determinada disciplina.
    """
    disc = db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
    return disc.assuntos


@router.post("/sincronizar")
def api_sincronizar_catalogo(db: Session = Depends(get_db)):
    """
    Sincroniza o catálogo completo de disciplinas e questões oficiais no banco de dados.
    """
    popular_banco_se_vazio(db)
    total_disc = db.query(Disciplina).count()
    total_ass = db.query(Assunto).count()
    total_questoes = db.query(QuestaoBanco).count()
    return {
        "status": "sucesso",
        "mensagem": "Catálogo de matérias e acervo oficial sincronizados com sucesso!",
        "total_disciplinas": total_disc,
        "total_assuntos": total_ass,
        "total_questoes_reais": total_questoes
    }


@router.get("/estatisticas/acervo")
def api_estatisticas_acervo(db: Session = Depends(get_db)):
    """
    Retorna o quantitativo de questões reais disponíveis por banca e matéria.
    """
    total_questoes = db.query(QuestaoBanco).count()
    
    por_banca = (
        db.query(QuestaoBanco.banca, func.count(QuestaoBanco.id))
        .group_by(QuestaoBanco.banca)
        .all()
    )
    
    por_disciplina = (
        db.query(Disciplina.nome, func.count(QuestaoBanco.id))
        .join(QuestaoBanco, QuestaoBanco.disciplina_id == Disciplina.id)
        .group_by(Disciplina.nome)
        .all()
    )

    return {
        "total_questoes_reais": total_questoes,
        "por_banca": [{"banca": b[0], "total": b[1]} for b in por_banca],
        "por_disciplina": [{"disciplina": d[0], "total": d[1]} for d in por_disciplina]
    }

