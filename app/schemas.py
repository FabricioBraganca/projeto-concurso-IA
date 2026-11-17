from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Alternativa de Questão
class AlternativaSchema(BaseModel):
    letra: str = Field(..., description="Letra da alternativa, ex: A, B, C, D, E")
    texto: str = Field(..., description="Texto da alternativa")


# Questão de Simulado (JSON Gerado pela IA)
class QuestaoGerada(BaseModel):
    enunciado: str
    alternativas: List[AlternativaSchema]
    resposta_certa: str = Field(..., description="Apenas a letra correta (A, B, C, D ou E)")
    explicacao: str = Field(..., description="Fundamentação teórica, citação legal e jurisprudência se houver")
    tema: Optional[str] = None
    dificuldade: Optional[str] = None


class SimuladoGeradoAI(BaseModel):
    titulo: str
    banca: str
    tema: str
    questoes: List[QuestaoGerada]


# Requisições do usuário
class SimuladoGerarRequest(BaseModel):
    tema: str = Field("Direito Constitucional", description="Disciplina ou tema específico")
    banca: str = Field("Cebraspe", description="Banca examinadora (ex: FGV, Cebraspe, FCC, Vunesp, etc.)")
    dificuldade: str = Field("Médio", description="Fácil, Médio, Difícil ou Avançado")
    quantidade: int = Field(5, ge=1, le=20, description="Quantidade de questões (1 a 20)")
    tipo_origem: str = Field("misto", description="Origem das questões: 'reais', 'ia' ou 'misto'")
    disciplina_id: Optional[int] = Field(None, description="ID da disciplina do catálogo (opcional)")
    assunto_id: Optional[int] = Field(None, description="ID do assunto de edital (opcional)")
    cargo_foco: Optional[str] = Field("Técnico/Analista Judiciário", description="Cargo ou área almejada")


class AssuntoCreateRequest(BaseModel):
    nome: str = Field(..., description="Nome do tópico ou assunto de edital")


class DisciplinaCreateRequest(BaseModel):
    nome: str = Field(..., description="Nome da matéria / disciplina")
    icone: Optional[str] = Field("📚", description="Emoji ou ícone da matéria")
    slug: Optional[str] = Field(None, description="Slug único (gerado automaticamente se nulo)")
    assuntos: List[str] = Field(default=[], description="Lista de nomes de assuntos para cadastrar")


class AssuntoResponse(BaseModel):
    id: int
    disciplina_id: int
    nome: str

    class Config:
        from_attributes = True


class DisciplinaResponse(BaseModel):
    id: int
    nome: str
    icone: str
    slug: str
    assuntos: List[AssuntoResponse] = []

    class Config:
        from_attributes = True


class SimuladoRecuperacaoRequest(BaseModel):
    tema: Optional[str] = Field(None, description="Filtrar erros por disciplina específica (opcional)")
    banca: Optional[str] = Field(None, description="Filtrar erros por banca específica (opcional)")
    quantidade: int = Field(5, ge=1, le=20, description="Quantidade de questões a recuperar (1 a 20)")


class SubmeterRespostaItem(BaseModel):
    questao_id: int
    resposta: str # Letra A-E


class SubmeterSimuladoRequest(BaseModel):
    respostas: List[SubmeterRespostaItem]


class ChatRequest(BaseModel):
    mensagem: str
    session_id: Optional[str] = "default"
    tema_contexto: Optional[str] = None


class ExplicarQuestaoRequest(BaseModel):
    enunciado: str
    alternativa_escolhida: str
    resposta_correta: str
    explicacao_base: Optional[str] = None


class FlashcardCreateRequest(BaseModel):
    tema: str = Field(..., description="Disciplina ou assunto")
    frente: str = Field(..., description="Pergunta ou conceito na frente do card")
    verso: str = Field(..., description="Resposta, mnemônico ou artigo no verso")


class FlashcardAvaliarRequest(BaseModel):
    qualidade: int = Field(..., ge=0, le=5, description="0-2=Errei (reinicia ciclo), 3=Difícil, 4=Bom, 5=Fácil")


class PlanoEstudosGerarRequest(BaseModel):
    concurso_alvo: str = Field("Receita Federal", description="Concurso almejado")
    cargo: str = Field("Auditor-Fiscal", description="Cargo ou área")
    horas_por_dia: int = Field(3, ge=1, le=12, description="Horas disponíveis por dia")
    dias_semana: int = Field(6, ge=1, le=7, description="Dias disponíveis para estudar na semana")
    dificuldades_principais: Optional[str] = Field("Direito Tributário e Contabilidade", description="Matérias que tem maior dificuldade")


# --- Schemas de Autenticação & Usuários ---

class UserCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, description="Nome completo do usuário")
    email: str = Field(..., description="E-mail válido do concurseiro")
    senha: str = Field(..., min_length=6, description="Senha com no mínimo 6 caracteres")


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="E-mail cadastrado")
    senha: str = Field(..., description="Senha de acesso")


class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


