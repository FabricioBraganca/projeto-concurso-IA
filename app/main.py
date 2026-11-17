import os
import sys
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.core.auth_dependency import get_optional_current_user
from app.modules.auth.router import router as auth_router
from app.modules.simulados.router import router as simulados_router
from app.modules.ai.router import router as ai_router
from app.modules.desempenho.router import router as desempenho_router
from app.modules.concursos.router import router as radar_router
from app.modules.flashcards.router import router as flashcards_router
from app.modules.plano_estudos.router import router as plano_router
from app.modules.disciplinas.router import router as disciplinas_router
from app.modules.simulados.service import obter_resumo_desempenho
from app.models import Simulado, Questao, Concurso, ProvaBanca, Flashcard, PlanoEstudos, User, Disciplina, Assunto, QuestaoBanco
from app.seeds.questoes_seeder import popular_banco_se_vazio
from app.modules.concursos.scraper import (
    buscar_concursos_rss,
    buscar_provas_bancas_online,
    sincronizar_concursos_background,
    _obter_concursos_fallback
)
from app.schemas import PlanoEstudosGerarRequest
from app.modules.flashcards.router import api_listar_flashcards
from app.modules.plano_estudos.router import api_gerar_plano

# Cria as tabelas do banco de dados na inicialização
Base.metadata.create_all(bind=engine)

# Garante migração de colunas adicionais para tabelas pré-existentes
try:
    with engine.connect() as conn:
        res = conn.execute(Base.metadata.tables["simulados"].select().limit(1))
except Exception:
    pass

try:
    with engine.begin() as conn:
        from sqlalchemy import text
        # Verifica se coluna tipo_origem existe
        col_check = conn.execute(text("PRAGMA table_info(simulados)")).fetchall()
        col_names = [c[1] for c in col_check]
        if "tipo_origem" not in col_names:
            conn.execute(text("ALTER TABLE simulados ADD COLUMN tipo_origem VARCHAR(50) DEFAULT 'misto'"))
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Aviso migração colunas: {e}")

# Popula catálogo de disciplinas e acervo inicial de questões reais de bancas se estiver vazio
try:
    from app.core.database import SessionLocal
    with SessionLocal() as db_init:
        popular_banco_se_vazio(db_init)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Aviso ao verificar seeder inicial: {e}")

app = FastAPI(
    title="ConcurseiroAI API",
    description="API e Plataforma Inteligente de Estudos para Concursos Públicos Brasileiros",
    version="1.0.0"
)

# Suporte a CORS para consumo por aplicações Web e Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminhos de estáticos e templates compatíveis com PyInstaller
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = os.path.join(sys._MEIPASS, "app")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

static_dir = os.path.join(BASE_DIR, "frontend", "static")
templates_dir = os.path.join(BASE_DIR, "frontend", "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


# Registra as rotas da API REST
app.include_router(auth_router, prefix="/api/v1")
app.include_router(simulados_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(desempenho_router, prefix="/api/v1")
app.include_router(radar_router, prefix="/api/v1")
app.include_router(flashcards_router, prefix="/api/v1")
app.include_router(plano_router, prefix="/api/v1")
app.include_router(disciplinas_router, prefix="/api/v1")



# --- ROTAS DA INTERFACE GRÁFICA (FRONT-END) ---

@app.get("/", response_class=HTMLResponse)
def page_dashboard(request: Request, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """Renderiza a página principal do Dashboard de Estudos."""
    stats = obter_resumo_desempenho(db, user_id=usuario.id)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"active_page": "dashboard", "stats": stats, "usuario": usuario}
    )


@app.get("/simulados", response_class=HTMLResponse)
def page_simulados(request: Request, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """Renderiza a página de gerador e lista de simulados com catálogo de matérias."""
    simulados = db.query(Simulado).filter(Simulado.user_id == usuario.id).order_by(Simulado.id.desc()).all()
    disciplinas = db.query(Disciplina).order_by(Disciplina.nome).all()
    total_reais = db.query(QuestaoBanco).count()
    return templates.TemplateResponse(
        request=request,
        name="simulados.html",
        context={
            "active_page": "simulados",
            "simulados": simulados,
            "disciplinas": disciplinas,
            "total_reais": total_reais,
            "usuario": usuario
        }
    )


@app.get("/simulados/{simulado_id}", response_class=HTMLResponse)
def page_simulado_detalhe(simulado_id: int, request: Request, db: Session = Depends(get_db)):
    """Renderiza a página de realização/revisão de um simulado específico."""
    simulado = db.query(Simulado).filter(Simulado.id == simulado_id).first()
    if not simulado:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    
    questoes = db.query(Questao).filter(Questao.simulado_id == simulado_id).order_by(Questao.ordem).all()
    
    return templates.TemplateResponse(
        request=request,
        name="simulado_detalhe.html",
        context={
            "active_page": "simulados",
            "simulado": simulado,
            "questoes": questoes
        }
    )


@app.get("/simulados/{simulado_id}/imprimir", response_class=HTMLResponse)
def page_simulado_imprimir(simulado_id: int, request: Request, db: Session = Depends(get_db)):
    """Renderiza o caderno oficial diagramado com folha de respostas e gabarito para impressão/PDF."""
    simulado = db.query(Simulado).filter(Simulado.id == simulado_id).first()
    if not simulado:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    
    questoes = db.query(Questao).filter(Questao.simulado_id == simulado_id).order_by(Questao.ordem).all()
    
    return templates.TemplateResponse(
        request=request,
        name="simulado_imprimir.html",
        context={
            "simulado": simulado,
            "questoes": questoes
        }
    )


@app.get("/chat", response_class=HTMLResponse)
def page_chat(request: Request):
    """Renderiza a interface do tutor de IA."""
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"active_page": "chat"}
    )


@app.get("/concursos-abertos", response_class=HTMLResponse)
def page_concursos(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Renderiza o radar de concursos públicos com dados sincronizados e resposta ultra-rápida."""
    concursos = db.query(Concurso).all()
    if not concursos:
        try:
            for item in _obter_concursos_fallback():
                c = Concurso(**item)
                db.add(c)
            db.commit()
            background_tasks.add_task(sincronizar_concursos_background)
        except Exception:
            db.rollback()
        concursos = db.query(Concurso).all()

    return templates.TemplateResponse(
        request=request,
        name="concursos.html",
        context={"active_page": "concursos", "concursos": concursos}
    )


@app.get("/provas", response_class=HTMLResponse)
def page_provas(request: Request, db: Session = Depends(get_db)):
    """Renderiza o banco de provas reais de bancas."""
    provas = db.query(ProvaBanca).all()
    if not provas:
        try:
            iniciais = buscar_provas_bancas_online()
            for p in iniciais:
                pb = ProvaBanca(**p)
                db.add(pb)
            db.commit()
        except Exception:
            db.rollback()
        provas = db.query(ProvaBanca).all()

    return templates.TemplateResponse(
        request=request,
        name="provas.html",
        context={"active_page": "provas", "provas": provas}
    )



@app.get("/flashcards", response_class=HTMLResponse)
def page_flashcards(request: Request, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """Renderiza os flashcards Anki/SM-2 de repetição espaçada."""
    cards = db.query(Flashcard).filter(Flashcard.user_id == usuario.id).all()
    if not cards:
        # Popula os cards iniciais via função do router (tem side-effect de DB)
        api_listar_flashcards(db=db, usuario=usuario)
        cards = db.query(Flashcard).filter(Flashcard.user_id == usuario.id).all()

    return templates.TemplateResponse(
        request=request,
        name="flashcards.html",
        context={"active_page": "flashcards", "cards": cards, "usuario": usuario}
    )


@app.get("/plano-estudos", response_class=HTMLResponse)
def page_plano_estudos(request: Request, db: Session = Depends(get_db), usuario: User = Depends(get_optional_current_user)):
    """Renderiza o cronograma semanal estratégico de estudos com IA."""
    plano_registro = db.query(PlanoEstudos).filter(PlanoEstudos.user_id == usuario.id).order_by(PlanoEstudos.id.desc()).first()
    if not plano_registro:
        # Gera o plano inicial automático
        req = PlanoEstudosGerarRequest()
        res = api_gerar_plano(req, db, usuario=usuario)
        plano_dados = res
        plano = res["plano"]
    else:
        plano_dados = {
            "concurso_alvo": plano_registro.concurso_alvo,
            "cargo": plano_registro.cargo,
            "horas_por_dia": plano_registro.horas_por_dia,
            "dias_semana": plano_registro.dias_semana
        }
        plano = plano_registro.conteudo_json

    return templates.TemplateResponse(
        request=request,
        name="plano_estudos.html",
        context={
            "active_page": "plano",
            "plano": plano,
            "plano_dados": plano_dados,
            "usuario": usuario
        }
    )

