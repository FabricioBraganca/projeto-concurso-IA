from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.models import Simulado, Questao, Desempenho, QuestaoBanco, Disciplina, Assunto
from app.schemas import SimuladoGerarRequest, SubmeterSimuladoRequest
from app.modules.ai.service import ai_service


def buscar_questoes_reais_banco(
    db: Session,
    banca: str = "",
    tema: str = "",
    disciplina_id: Optional[int] = None,
    assunto_id: Optional[int] = None,
    limite: int = 20
) -> List[QuestaoBanco]:
    """
    Busca questões reais de bancas catalogadas no banco de dados.
    """
    query = db.query(QuestaoBanco)
    if disciplina_id:
        query = query.filter(QuestaoBanco.disciplina_id == disciplina_id)
    if assunto_id:
        query = query.filter(QuestaoBanco.assunto_id == assunto_id)
    if banca and banca.lower() not in ["todas", "geral"]:
        query = query.filter(QuestaoBanco.banca.ilike(f"%{banca}%"))
    if tema and not disciplina_id:
        query = query.join(Disciplina, QuestaoBanco.disciplina_id == Disciplina.id).filter(
            (Disciplina.nome.ilike(f"%{tema}%")) | (QuestaoBanco.enunciado.ilike(f"%{tema}%"))
        )

    questoes = query.order_by(func.random()).limit(limite).all()

    # Se a busca estrita retornar menos que o limite, busca de outras bancas para completar
    if len(questoes) < limite:
        ids_ja = [q.id for q in questoes]
        subquery = db.query(QuestaoBanco).filter(~QuestaoBanco.id.in_(ids_ja)) if ids_ja else db.query(QuestaoBanco)
        if disciplina_id:
            subquery = subquery.filter(QuestaoBanco.disciplina_id == disciplina_id)
        extras = subquery.order_by(func.random()).limit(limite - len(questoes)).all()
        questoes.extend(extras)

    return questoes


def criar_e_gerar_simulado(db: Session, request_data: SimuladoGerarRequest, user_id: int = 1) -> Simulado:
    """
    Gera o simulado nos modos 'reais', 'ia' ou 'misto' suportando até 20 questões.
    """
    tipo_origem = getattr(request_data, "tipo_origem", "misto") or "misto"
    qtd_total = request_data.quantidade
    questoes_finais = []

    # 1. Modo 'reais' (apenas questões reais de provas passadas)
    if tipo_origem == "reais":
        reais = buscar_questoes_reais_banco(
            db,
            banca=request_data.banca,
            tema=request_data.tema,
            disciplina_id=request_data.disciplina_id,
            assunto_id=request_data.assunto_id,
            limite=qtd_total
        )
        for q in reais:
            questoes_finais.append({
                "enunciado": f"({q.banca} - {q.orgao}/{q.ano} • {q.cargo}) {q.enunciado}",
                "alternativas": q.alternativas,
                "resposta_certa": q.resposta_certa.strip().upper(),
                "explicacao": q.explicacao_fundamentada or "Fundamentação oficial da banca organizadora.",
                "tema": request_data.tema,
                "banca": q.banca,
                "dificuldade": q.dificuldade
            })
        
        # Se o banco tiver menos que o solicitado, complementa com IA
        if len(questoes_finais) < qtd_total:
            faltam = qtd_total - len(questoes_finais)
            req_comp = SimuladoGerarRequest(
                tema=request_data.tema,
                banca=request_data.banca,
                dificuldade=request_data.dificuldade,
                quantidade=faltam,
                cargo_foco=request_data.cargo_foco
            )
            gerado_comp = ai_service.gerar_simulado(req_comp)
            for q in gerado_comp.questoes:
                alts = [a.model_dump() if hasattr(a, "model_dump") else dict(a) for a in q.alternativas]
                questoes_finais.append({
                    "enunciado": q.enunciado,
                    "alternativas": alts,
                    "resposta_certa": q.resposta_certa.strip().upper(),
                    "explicacao": q.explicacao,
                    "tema": q.tema or request_data.tema,
                    "banca": request_data.banca,
                    "dificuldade": request_data.dificuldade
                })

    # 2. Modo 'misto' (50% Reais + 50% Inéditas IA)
    elif tipo_origem == "misto":
        qtd_reais = qtd_total // 2
        qtd_ia = qtd_total - qtd_reais

        # Busca lote de questões reais
        reais = buscar_questoes_reais_banco(
            db,
            banca=request_data.banca,
            tema=request_data.tema,
            disciplina_id=request_data.disciplina_id,
            assunto_id=request_data.assunto_id,
            limite=qtd_reais
        )
        for q in reais:
            questoes_finais.append({
                "enunciado": f"({q.banca} - {q.orgao}/{q.ano} • {q.cargo}) {q.enunciado}",
                "alternativas": q.alternativas,
                "resposta_certa": q.resposta_certa.strip().upper(),
                "explicacao": q.explicacao_fundamentada or "Fundamentação oficial da banca examinadora.",
                "tema": request_data.tema,
                "banca": q.banca,
                "dificuldade": q.dificuldade
            })

        # Busca lote com Gemini IA
        req_ia = SimuladoGerarRequest(
            tema=request_data.tema,
            banca=request_data.banca,
            dificuldade=request_data.dificuldade,
            quantidade=qtd_ia + (qtd_reais - len(reais)),
            cargo_foco=request_data.cargo_foco
        )
        gerado_ia = ai_service.gerar_simulado(req_ia)
        for q in gerado_ia.questoes:
            alts = [a.model_dump() if hasattr(a, "model_dump") else dict(a) for a in q.alternativas]
            questoes_finais.append({
                "enunciado": q.enunciado,
                "alternativas": alts,
                "resposta_certa": q.resposta_certa.strip().upper(),
                "explicacao": q.explicacao,
                "tema": q.tema or request_data.tema,
                "banca": request_data.banca,
                "dificuldade": request_data.dificuldade
            })

    # 3. Modo 'ia' (100% Inéditas com Gemini)
    else:
        gerado = ai_service.gerar_simulado(request_data)
        for q in gerado.questoes:
            alts = [a.model_dump() if hasattr(a, "model_dump") else dict(a) for a in q.alternativas]
            questoes_finais.append({
                "enunciado": q.enunciado,
                "alternativas": alts,
                "resposta_certa": q.resposta_certa.strip().upper(),
                "explicacao": q.explicacao,
                "tema": q.tema or request_data.tema,
                "banca": request_data.banca,
                "dificuldade": request_data.dificuldade
            })

    # Cria o registro do Simulado
    origem_label = "Reais de Provas" if tipo_origem == "reais" else ("Misto (Reais + IA)" if tipo_origem == "misto" else "Inéditas IA")
    novo_simulado = Simulado(
        user_id=user_id,
        titulo=f"Simulado {request_data.banca} ({len(questoes_finais)} Questões • {origem_label})",
        banca_filtro=request_data.banca,
        tema_filtro=request_data.tema,
        dificuldade=request_data.dificuldade,
        tipo_origem=tipo_origem,
        total_questoes=len(questoes_finais),
        acertos=0,
        score_final=0.0,
        concluido=False
    )
    db.add(novo_simulado)
    db.flush()

    # Cria as questões associadas
    for i, q in enumerate(questoes_finais, start=1):
        questao_obj = Questao(
            simulado_id=novo_simulado.id,
            ordem=i,
            enunciado=q["enunciado"],
            alternativas=q["alternativas"],
            resposta_certa=q["resposta_certa"],
            explicacao_ia=q["explicacao"],
            tema=q["tema"],
            banca=q["banca"],
            dificuldade=q["dificuldade"]
        )
        db.add(questao_obj)

    db.commit()
    db.refresh(novo_simulado)
    return novo_simulado


def processar_respostas_simulado(db: Session, simulado_id: int, submissao: SubmeterSimuladoRequest, user_id: int = 1) -> Dict[str, Any]:
    """
    Calcula gabarito, acertos/erros e atualiza as métricas de desempenho.
    """
    simulado = db.query(Simulado).filter(Simulado.id == simulado_id).first()
    if not simulado:
        raise ValueError("Simulado não encontrado")

    respostas_map = {item.questao_id: item.resposta.strip().upper() for item in submissao.respostas}
    
    total_acertos = 0
    questoes = db.query(Questao).filter(Questao.simulado_id == simulado_id).all()

    for q in questoes:
        resp_user = respostas_map.get(q.id)
        q.resposta_usuario = resp_user
        if resp_user and resp_user == q.resposta_certa:
            q.acertou = True
            total_acertos += 1
        else:
            q.acertou = False

    simulado.acertos = total_acertos
    simulado.score_final = round((total_acertos / len(questoes)) * 100, 1) if questoes else 0.0
    simulado.concluido = True
    simulado.concluido_em = datetime.now(timezone.utc)

    # Atualiza tabela de desempenho
    tema = simulado.tema_filtro or "Geral"
    desempenho = db.query(Desempenho).filter(
        Desempenho.user_id == user_id,
        Desempenho.tema == tema
    ).first()

    if not desempenho:
        desempenho = Desempenho(
            user_id=user_id,
            tema=tema,
            banca=simulado.banca_filtro,
            total_feitas=len(questoes),
            total_acertos=total_acertos
        )
        db.add(desempenho)
    else:
        desempenho.total_feitas += len(questoes)
        desempenho.total_acertos += total_acertos
        desempenho.ultima_atualizacao = datetime.now(timezone.utc)

    db.commit()
    db.refresh(simulado)

    return {
        "simulado_id": simulado.id,
        "total_questoes": len(questoes),
        "acertos": total_acertos,
        "erros": len(questoes) - total_acertos,
        "score_percentual": simulado.score_final
    }


def obter_resumo_desempenho(db: Session, user_id: int = 1) -> Dict[str, Any]:
    """
    Consolida as métricas globais e por tema do usuário.
    """
    simulados = db.query(Simulado).filter(Simulado.user_id == user_id).all()
    concluidos = [s for s in simulados if s.concluido]

    total_simulados = len(concluidos)
    total_questoes = sum(s.total_questoes for s in concluidos)
    total_acertos = sum(s.acertos for s in concluidos)
    taxa_acerto_geral = round((total_acertos / total_questoes * 100), 1) if total_questoes > 0 else 0.0

    desempenho_temas = db.query(Desempenho).filter(Desempenho.user_id == user_id).all()
    temas_stats = []
    for d in desempenho_temas:
        taxa = round((d.total_acertos / d.total_feitas * 100), 1) if d.total_feitas > 0 else 0.0
        temas_stats.append({
            "tema": d.tema,
            "banca": d.banca or "Mistas",
            "feitas": d.total_feitas,
            "acertos": d.total_acertos,
            "taxa_acerto": taxa
        })

    return {
        "total_simulados": total_simulados,
        "total_questoes_resolvidas": total_questoes,
        "total_acertos": total_acertos,
        "taxa_acerto_geral": taxa_acerto_geral,
        "desempenho_por_tema": temas_stats,
        "ultimos_simulados": [
            {
                "id": s.id,
                "titulo": s.titulo,
                "tema": s.tema_filtro,
                "banca": s.banca_filtro,
                "score": s.score_final,
                "acertos": s.acertos,
                "total": s.total_questoes,
                "data": s.criado_em.strftime("%d/%m/%Y %H:%M") if s.criado_em else ""
            }
            for s in sorted(concluidos, key=lambda x: x.id, reverse=True)[:5]
        ]
    }


def obter_caderno_erros(db: Session, user_id: int, tema: Optional[str] = None, banca: Optional[str] = None) -> Dict[str, Any]:
    """
    Retorna todas as questões erradas pelo concurseiro, agrupadas com estatísticas.
    """
    query = (
        db.query(Questao)
        .join(Simulado, Questao.simulado_id == Simulado.id)
        .filter(Simulado.user_id == user_id, Questao.acertou == False)
    )

    if tema:
        query = query.filter(Questao.tema.ilike(f"%{tema}%"))
    if banca:
        query = query.filter(Questao.banca.ilike(f"%{banca}%"))

    questoes_erradas = query.order_by(Questao.id.desc()).all()

    # Agrupa erros por disciplina para diagnóstico
    contagem_disciplinas: Dict[str, int] = {}
    for q in questoes_erradas:
        disciplina = q.tema or "Geral"
        contagem_disciplinas[disciplina] = contagem_disciplinas.get(disciplina, 0) + 1

    ranking_erros = [
        {"disciplina": disc, "erros": qtd}
        for disc, qtd in sorted(contagem_disciplinas.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "total_erros": len(questoes_erradas),
        "ranking_erros_por_disciplina": ranking_erros,
        "questoes": [
            {
                "questao_id": q.id,
                "simulado_id": q.simulado_id,
                "tema": q.tema,
                "banca": q.banca,
                "enunciado": q.enunciado,
                "alternativas": q.alternativas,
                "resposta_marcada": q.resposta_usuario,
                "gabarito_correto": q.resposta_certa,
                "explicacao_ia": q.explicacao_ia,
                "dificuldade": q.dificuldade
            }
            for q in questoes_erradas
        ]
    }


def gerar_simulado_recuperacao(
    db: Session,
    user_id: int,
    tema: Optional[str] = None,
    banca: Optional[str] = None,
    quantidade: int = 5
) -> Simulado:
    """
    Cria um simulado inédito de refazimento a partir das questões presentes no Caderno de Erros.
    """
    query = (
        db.query(Questao)
        .join(Simulado, Questao.simulado_id == Simulado.id)
        .filter(Simulado.user_id == user_id, Questao.acertou == False)
    )

    if tema:
        query = query.filter(Questao.tema.ilike(f"%{tema}%"))
    if banca:
        query = query.filter(Questao.banca.ilike(f"%{banca}%"))

    # Pega até a quantidade solicitada
    candidatas = query.order_by(Questao.id.desc()).limit(quantidade).all()

    if not candidatas:
        raise ValueError("Seu caderno de erros está vazio para os filtros selecionados! Parabéns ou realize novos simulados.")

    # Cria o novo simulado de recuperação
    titulo_simulado = f"Simulado de Recuperação: {tema or 'Caderno de Erros Geral'}"
    novo_simulado = Simulado(
        user_id=user_id,
        titulo=titulo_simulado,
        banca_filtro=banca or "Caderno de Erros",
        tema_filtro=tema or "Recuperação de Erros",
        dificuldade="Reforço",
        total_questoes=len(candidatas),
        acertos=0,
        score_final=0.0,
        concluido=False
    )
    db.add(novo_simulado)
    db.flush()

    # Clona as questões erradas limpas para nova tentativa
    for i, q in enumerate(candidatas, start=1):
        nova_q = Questao(
            simulado_id=novo_simulado.id,
            ordem=i,
            enunciado=q.enunciado,
            alternativas=q.alternativas,
            resposta_certa=q.resposta_certa,
            resposta_usuario=None,
            acertou=None,
            explicacao_ia=q.explicacao_ia,
            tema=q.tema,
            banca=q.banca,
            dificuldade=q.dificuldade
        )
        db.add(nova_q)

    db.commit()
    db.refresh(novo_simulado)
    return novo_simulado

