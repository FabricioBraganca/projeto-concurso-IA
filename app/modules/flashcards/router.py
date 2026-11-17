from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Flashcard, User
from app.schemas import FlashcardCreateRequest, FlashcardAvaliarRequest
from app.modules.flashcards.sm2 import calcular_sm2
from app.core.auth_dependency import get_optional_current_user

router = APIRouter(prefix="/flashcards", tags=["Flashcards & Revisão Espaçada"])


@router.get("/")
def api_listar_flashcards(tema: Optional[str] = None, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """
    Lista todos os flashcards do usuário ou filtra por disciplina.
    """
    query = db.query(Flashcard).filter(Flashcard.user_id == usuario.id)
    if tema:
        query = query.filter(Flashcard.tema.ilike(f"%{tema}%"))
    cards = query.order_by(Flashcard.id.desc()).all()
    
    # Se estiver vazio, popula com cards fundamentais de concursos
    if not cards:
        cards_iniciais = [
            {
                "tema": "Direito Administrativo",
                "frente": "Quais são os 5 princípios explícitos no art. 37 da CF/88 que regem a Administração Pública?",
                "verso": "Mnemônico LIMPE:\n• L - Legalidade\n• I - Impessoalidade\n• M - Moralidade\n• P - Publicidade\n• E - Eficiência (acrescentado pela EC 19/98)"
            },
            {
                "tema": "Direito Constitucional",
                "frente": "Qual a diferença entre a Ação Direta de Inconstitucionalidade (ADI) e a Arguição de Descumprimento de Preceito Fundamental (ADPF)?",
                "verso": "A ADI tem como objeto leis ou atos normativos federais ou estaduais pós-constitucionais.\nA ADPF tem caráter subsidiário e alcança normas pré-constitucionais e atos municipais."
            },
            {
                "tema": "Direito Penal",
                "frente": "Quais são os elementos integrantes da culpabilidade segundo a teoria limitada adotada no Código Penal?",
                "verso": "1) Imputabilidade penal;\n2) Potencial consciência da ilicitude;\n3) Exigibilidade de conduta diversa."
            },
            {
                "tema": "Língua Portuguesa",
                "frente": "Em quais casos o uso da crase é PROIBIDO segundo a regra geral?",
                "verso": "• Antes de palavras masculinas;\n• Antes de verbos no infinitivo;\n• Antes de pronomes de tratamento (exceto dona, senhora e senhorita);\n• Em expressões com palavras repetidas (dia a dia, cara a cara)."
            }
        ]
        for c in cards_iniciais:
            fc = Flashcard(user_id=usuario.id, **c)
            db.add(fc)
        db.commit()
        cards = db.query(Flashcard).filter(Flashcard.user_id == usuario.id).all()

    return [
        {
            "id": c.id,
            "tema": c.tema,
            "frente": c.frente,
            "verso": c.verso,
            "repeticoes": c.repeticoes,
            "intervalo_dias": c.intervalo_dias,
            "proxima_revisao": c.proxima_revisao.isoformat() if c.proxima_revisao else None
        }
        for c in cards
    ]


@router.post("/")
def api_criar_flashcard(dados: FlashcardCreateRequest, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """
    Cria um novo flashcard personalizado no caderno do estudante.
    """
    card = Flashcard(
        user_id=usuario.id,
        tema=dados.tema,
        frente=dados.frente,
        verso=dados.verso
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return {"id": card.id, "mensagem": "Flashcard criado com sucesso!"}


@router.post("/{card_id}/avaliar")
def api_avaliar_flashcard(card_id: int, dados: FlashcardAvaliarRequest, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """
    Processa a avaliação do card via algoritmo SM-2 e reagenda a data de revisão futura.
    """
    card = db.query(Flashcard).filter(Flashcard.id == card_id, Flashcard.user_id == usuario.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard não encontrado")

    novas_reps, novo_ef, novo_intervalo, proxima_data = calcular_sm2(
        qualidade=dados.qualidade,
        repeticoes=card.repeticoes or 0,
        fator_facilidade=card.fator_facilidade or 2.5,
        intervalo_atual=card.intervalo_dias or 1
    )

    card.repeticoes = novas_reps
    card.fator_facilidade = novo_ef
    card.intervalo_dias = novo_intervalo
    card.proxima_revisao = proxima_data
    db.commit()

    return {
        "card_id": card.id,
        "novas_repeticoes": novas_reps,
        "novo_intervalo_dias": novo_intervalo,
        "proxima_revisao": proxima_data.strftime("%d/%m/%Y")
    }
