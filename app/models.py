from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    simulados = relationship("Simulado", back_populates="user", cascade="all, delete-orphan")
    chat_historico = relationship("ChatHistorico", back_populates="user", cascade="all, delete-orphan")
    desempenhos = relationship("Desempenho", back_populates="user", cascade="all, delete-orphan")


class Simulado(Base):
    __tablename__ = "simulados"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # opcional para demo/convidado
    titulo = Column(String(200), nullable=False)
    banca_filtro = Column(String(100), nullable=True)
    tema_filtro = Column(String(100), nullable=True)
    dificuldade = Column(String(50), default="Médio")
    total_questoes = Column(Integer, default=5)
    acertos = Column(Integer, default=0)
    score_final = Column(Float, default=0.0)
    tipo_origem = Column(String(50), default="misto") # "reais", "ia", "misto"
    concluido = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    concluido_em = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="simulados")
    questoes = relationship("Questao", back_populates="simulado", cascade="all, delete-orphan")


class Questao(Base):
    __tablename__ = "questoes"

    id = Column(Integer, primary_key=True, index=True)
    simulado_id = Column(Integer, ForeignKey("simulados.id"), nullable=False)
    ordem = Column(Integer, default=1)
    enunciado = Column(Text, nullable=False)
    # Lista de dicts: [{"letra": "A", "texto": "..."}, ...]
    alternativas = Column(JSON, nullable=False)
    resposta_certa = Column(String(5), nullable=False) # "A", "B", "C", "D", "E"
    resposta_usuario = Column(String(5), nullable=True)
    acertou = Column(Boolean, nullable=True)
    explicacao_ia = Column(Text, nullable=True)
    tema = Column(String(100), nullable=True)
    banca = Column(String(100), nullable=True)
    dificuldade = Column(String(50), nullable=True)

    simulado = relationship("Simulado", back_populates="questoes")


class ChatHistorico(Base):
    __tablename__ = "chat_historico"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), index=True, default="default")
    role = Column(String(20), nullable=False) # "user" ou "model"
    mensagem = Column(Text, nullable=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_historico")


class Desempenho(Base):
    __tablename__ = "desempenho"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tema = Column(String(100), index=True, nullable=False)
    banca = Column(String(100), nullable=True)
    total_feitas = Column(Integer, default=0)
    total_acertos = Column(Integer, default=0)
    ultima_atualizacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="desempenhos")


class Concurso(Base):
    __tablename__ = "concursos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    orgao = Column(String(150), nullable=False)
    banca = Column(String(100), nullable=True)
    regiao = Column(String(50), nullable=True) # "Nacional", "SP", "DF", etc.
    carreira = Column(String(100), nullable=True) # "Judiciária", "Fiscal", etc.
    cargos = Column(Text, nullable=True)
    vagas = Column(String(50), nullable=True)
    salario = Column(String(100), nullable=True)
    status = Column(String(50), default="Inscrições Abertas") # "Inscrições Abertas", "Edital Publicado", "Autorizado"
    data_inscricao_fim = Column(String(50), nullable=True)
    data_prova = Column(String(50), nullable=True)
    link_edital = Column(String(500), nullable=True)
    fonte = Column(String(100), default="PCI Concursos")
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProvaBanca(Base):
    __tablename__ = "provas_bancas"

    id = Column(Integer, primary_key=True, index=True)
    banca = Column(String(100), index=True, nullable=False)
    orgao = Column(String(150), nullable=False)
    cargo = Column(String(150), nullable=False)
    ano = Column(Integer, index=True, nullable=False)
    disciplinas_destaque = Column(String(250), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    gabarito_url = Column(String(500), nullable=True)
    fonte = Column(String(100), default="PCI Concursos / QConcursos")
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tema = Column(String(100), index=True, nullable=False)
    frente = Column(Text, nullable=False)
    verso = Column(Text, nullable=False)
    # Atributos do Algoritmo SM-2 (SuperMemo 2)
    repeticoes = Column(Integer, default=0)
    intervalo_dias = Column(Integer, default=1)
    fator_facilidade = Column(Float, default=2.5)
    proxima_revisao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


class PlanoEstudos(Base):
    __tablename__ = "planos_estudos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    concurso_alvo = Column(String(150), nullable=False)
    cargo = Column(String(150), nullable=False)
    horas_por_dia = Column(Integer, default=3)
    dias_semana = Column(Integer, default=6)
    conteudo_json = Column(JSON, nullable=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


class Disciplina(Base):
    __tablename__ = "disciplinas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    icone = Column(String(10), default="📚")
    slug = Column(String(100), unique=True, nullable=False)

    assuntos = relationship("Assunto", back_populates="disciplina", cascade="all, delete-orphan")
    questoes = relationship("QuestaoBanco", back_populates="disciplina")


class Assunto(Base):
    __tablename__ = "assuntos"

    id = Column(Integer, primary_key=True, index=True)
    disciplina_id = Column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    nome = Column(String(150), nullable=False)

    disciplina = relationship("Disciplina", back_populates="assuntos")
    questoes = relationship("QuestaoBanco", back_populates="assunto")


class QuestaoBanco(Base):
    __tablename__ = "questoes_banco"

    id = Column(Integer, primary_key=True, index=True)
    disciplina_id = Column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    assunto_id = Column(Integer, ForeignKey("assuntos.id"), nullable=True)
    banca = Column(String(100), index=True, nullable=False) # "Cebraspe", "FGV", "FCC", "Vunesp", etc.
    orgao = Column(String(150), nullable=False) # "Receita Federal", "TJ-SP", "PF", etc.
    cargo = Column(String(150), nullable=False)
    ano = Column(Integer, index=True, nullable=False)
    enunciado = Column(Text, nullable=False)
    alternativas = Column(JSON, nullable=False) # [{"letra": "A", "texto": "..."}]
    resposta_certa = Column(String(5), nullable=False) # "A", "B", "C", "D", "E"
    explicacao_fundamentada = Column(Text, nullable=True)
    dificuldade = Column(String(50), default="Médio")
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    disciplina = relationship("Disciplina", back_populates="questoes")
    assunto = relationship("Assunto", back_populates="questoes")





