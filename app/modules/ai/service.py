import os
import json
import logging
from typing import Optional, List, Dict, Any
from google import genai

from google.genai import types
from app.core.config import settings
from app.schemas import SimuladoGeradoAI, SimuladoGerarRequest

logger = logging.getLogger(__name__)


class GeminiAIService:
    def __init__(self):
        # O cliente busca automaticamente GEMINI_API_KEY do ambiente se não for passado explicitamente
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if api_key:
            # Configura timeout de 35 segundos para suportar geração densa de até 20 questões detalhadas
            http_opts = types.HttpOptions(timeout=35000) # 35000 ms = 35s
            self.client = genai.Client(api_key=api_key, http_options=http_opts)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY não configurada. Operando em modo mock/fallback quando necessário.")


    def is_configured(self) -> bool:
        return self.client is not None

    def gerar_simulado(self, params: SimuladoGerarRequest) -> SimuladoGeradoAI:
        """
        Gera questões inéditas ou baseadas em estilo de banca com saída estruturada JSON.
        """
        if not self.is_configured():
            return self._gerar_simulado_fallback(params)

        prompt = f"""
Você é um elaborador sênior de provas e questões para concursos públicos brasileiros, com vasta experiência em bancas como {params.banca}.
Elabore um simulado técnico, rigoroso e de alto nível pedagógico com os seguintes parâmetros:
- Tema / Disciplina: {params.tema}
- Banca Examinadora: {params.banca}
- Nível de Dificuldade: {params.dificuldade}
- Cargo / Área Alvo: {params.cargo_foco or 'Geral'}
- Quantidade de questões: {params.quantidade}

Diretrizes obrigatórias:
1. Siga fielmente o estilo e pegadinha clássica da banca {params.banca} (ex: Cebraspe prefere contextualizações e literalidade/jurisprudência consolidada; FGV gosta de casos práticos e interdisciplinares; FCC foca na letra da lei e súmulas).
2. Cada questão deve ter exatamente 5 alternativas (A, B, C, D, E).
3. Apenas UMA alternativa é a correta.
4. Forneça uma explicação cirúrgica, didática e aprofundada para o gabarito comentado, citando artigos de lei, súmulas dos tribunais superiores (STF/STJ) ou doutrina dominante quando pertinente.
5. Retorne os dados estritamente no schema solicitado.
"""

        # Lista de modelos em ordem de preferência caso haja instabilidade (503/404) na API
        modelos_tentativa = [
            settings.GEMINI_MODEL,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro"
        ]

        for model_name in modelos_tentativa:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SimuladoGeradoAI,
                        temperature=0.3,
                    ),
                )
                data = json.loads(response.text)
                return SimuladoGeradoAI(**data)
            except Exception as e:
                logger.warning(f"Tentativa com modelo {model_name} falhou: {e}")
                continue

        logger.error("Todos os modelos de IA falharam momentaneamente. Ativando fallback pedagógico.")
        return self._gerar_simulado_fallback(params)


    def explicar_questao(self, enunciado: str, alternativa_escolhida: str, gabarito_correto: str, explicacao_base: str = "") -> str:
        """
        Gera uma explicação aprofundada como um tutor particular de concursos.
        """
        if not self.is_configured():
            return (
                f"Você marcou a opção ({alternativa_escolhida}), mas o gabarito correto é a opção ({gabarito_correto}).\n\n"
                f"Fundamentação: {explicacao_base or 'A alternativa está amparada na jurisprudência dominante e no texto literal da lei correspondente.'}\n\n"
                "💡 Dica de Memorização: Sempre destaque os termos restritivos nas assertivas (como 'nunca', 'sempre', 'exclusivamente') que costumam ser pegadinhas de concurso!"
            )

        prompt = f"""
Você é um professor tutor de concurso público de elite. O aluno acabou de responder a seguinte questão:

Enunciado:
{enunciado}

Resposta do aluno: Alternativa ({alternativa_escolhida})
Gabarito oficial: Alternativa ({gabarito_correto})
Explicação preliminar: {explicacao_base}

Instruções:
- Se o aluno errou: Explique de forma muito clara e encorajadora por que a opção ({alternativa_escolhida}) está incorreta, qual foi a provável armadilha (pegadinha) e por que a opção ({gabarito_correto}) é a indiscutivelmente correta.
- Se o aluno acertou: Parabenize e reforce o núcleo do conhecimento para fixação definitiva na memória de longo prazo.
- Inclua: 1) Diagnóstico do Erro/Acerto; 2) Base Legal / Jurisprudencial; 3) 'Dica de Ouro' para nunca mais errar em prova.
"""
        modelos_tentativa = [
            settings.GEMINI_MODEL,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro"
        ]

        for model_name in modelos_tentativa:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                    ),
                )
                return response.text
            except Exception as e:
                logger.warning(f"Tentativa de explicação com modelo {model_name} falhou: {e}")
                continue

        return f"Gabarito Oficial: ({gabarito_correto}). {explicacao_base}"

    def chat_tutor(self, mensagem: str, historico: List[Dict[str, str]] = None) -> str:
        """
        Chat com tutor especializado em concursos públicos.
        """
        if not self.is_configured():
            return (
                f"Sou o seu Tutor de Concursos! No momento, para respostas dinâmicas em tempo real com IA generativa, "
                f"adicione sua chave GEMINI_API_KEY no arquivo .env. Enquanto isso, posso lhe ajudar a resolver simulados "
                f"e acompanhar seu progresso no dashboard!"
            )

        system_instruction = (
            "Você é o 'Concurseiro Tutor AI', um mentor e professor especialista em aprovação em concursos públicos de alto nível no Brasil "
            "(Receita Federal, Tribunais, Carreiras Policiais, Fiscais e Administrativas). "
            "Seu tom é técnico, motivador, direto, focado na resolução de dúvidas de matérias (Constitucional, Administrativo, Português, RLM, etc.) "
            "e estratégias de revisão espaçada e ciclo de estudos. Use formatação markdown rica, tópicos e destaques com emojis."
        )

        contents = []
        if historico:
            for item in historico:
                role = "user" if item.get("role") == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=item.get("mensagem", ""))]))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=mensagem)]))

        modelos_tentativa = [
            settings.GEMINI_MODEL,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro"
        ]

        for model_name in modelos_tentativa:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.5,
                    ),
                )
                return response.text
            except Exception as e:
                logger.warning(f"Chat tentativa com {model_name} falhou: {e}")
                continue

        return "O tutor está com alta demanda momentânea na API do Gemini. Mas já estou pronto para continuar te ajudando com os simulados e análises!"

    def gerar_plano_estudos(self, concurso: str, cargo: str, horas: int, dias: int, dificuldades: str) -> Dict[str, Any]:
        """
        Gera um cronograma semanal estratégico de estudos com base nas horas disponíveis e dificuldades.
        """
        prompt = f"""
Você é um estrategista e mentor de aprovação em concursos públicos de alto rendimento.
Elabore um cronograma de estudos semanal estruturado para o seguinte perfil:
- Concurso Alvo: {concurso}
- Cargo: {cargo}
- Carga Horária: {horas} horas por dia
- Frequência: {dias} dias por semana
- Disciplinas de Maior Dificuldade / Prioridade: {dificuldades}

Instruções:
- Monte um ciclo de estudos equilibrando teoria, questões diárias e revisão espaçada.
- Retorne EXCLUSIVAMENTE um objeto JSON válido (sem tags markdown ```json) com a seguinte estrutura:
{{
  "titulo": "Plano Estratégico {concurso} - {cargo}",
  "estrategia_geral": "Breve parágrafo sobre a metodologia adotada",
  "dias": [
    {{
      "dia": "Segunda-feira",
      "disciplina_1": "Nome da Matéria",
      "foco_1": "Assunto a estudar",
      "disciplina_2": "Nome da Matéria 2 (se couber nas horas)",
      "foco_2": "Assunto ou questões",
      "tempo_questoes": "30 a 45 min",
      "meta_do_dia": "Resolver 20 questões e anotar erros no caderno de erros"
    }}
  ],
  "dicas_revisao": [
    "Dica 1",
    "Dica 2"
  ]
}}
"""
        modelos_tentativa = [
            settings.GEMINI_MODEL,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro"
        ]

        if self.is_configured():
            for m in modelos_tentativa:
                try:
                    response = self.client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.4
                        )
                    )
                    return json.loads(response.text)
                except Exception as e:
                    logger.warning(f"Erro gerando plano com {m}: {e}")
                    continue

        return self._obter_plano_fallback(concurso, cargo, horas, dias)


    def _obter_plano_fallback(self, concurso: str, cargo: str, horas: int, dias: int) -> Dict[str, Any]:
        return {
            "titulo": f"Plano Estratégico {concurso} - {cargo}",
            "estrategia_geral": f"Ciclo de estudos intervalado para {horas}h diárias, intercalando matérias de alto peso com resolução diária de questões de bancas.",
            "dias": [
                {
                    "dia": "Segunda-feira",
                    "disciplina_1": "Direito Constitucional",
                    "foco_1": "Direitos e Garantias Fundamentais (Art. 5º)",
                    "disciplina_2": "Língua Portuguesa",
                    "foco_2": "Interpretação e Tipologia Textual",
                    "tempo_questoes": "40 min",
                    "meta_do_dia": "25 questões comentadas no simulador"
                },
                {
                    "dia": "Terça-feira",
                    "disciplina_1": "Direito Administrativo",
                    "foco_1": "Poderes Administrativos e Atos",
                    "disciplina_2": "Raciocínio Lógico-Matemático",
                    "foco_2": "Equivalências e Tabela Verdade",
                    "tempo_questoes": "40 min",
                    "meta_do_dia": "Revisão dos flashcards do dia anterior"
                },
                {
                    "dia": "Quarta-feira",
                    "disciplina_1": "Legislação Específica",
                    "foco_1": "Regime Jurídico dos Servidores (Lei 8.112 ou correlata)",
                    "disciplina_2": "Direito Tributário / Penal",
                    "foco_2": "Princípios fundamentais e conceitos chave",
                    "tempo_questoes": "40 min",
                    "meta_do_dia": "Criar 5 flashcards dos artigos mais cobrados"
                },
                {
                    "dia": "Quinta-feira",
                    "disciplina_1": "Direito Constitucional",
                    "foco_1": "Organização do Estado e Poder Executivo/Judiciário",
                    "disciplina_2": "Língua Portuguesa",
                    "foco_2": "Crase e Sintaxe de Concordância",
                    "tempo_questoes": "45 min",
                    "meta_do_dia": "Simulado rápido de 5 questões no sistema"
                },
                {
                    "dia": "Sexta-feira",
                    "disciplina_1": "Direito Administrativo",
                    "foco_1": "Licitações e Contratos Administrativos (Nova Lei 14.133)",
                    "disciplina_2": "Informática / TI",
                    "foco_2": "Segurança da Informação e Redes",
                    "tempo_questoes": "40 min",
                    "meta_do_dia": "Caderno de erros das questões da semana"
                },
                {
                    "dia": "Sábado",
                    "disciplina_1": "Simulado Geral Cronometrado",
                    "foco_1": "Simulado completo na banca alvo",
                    "disciplina_2": "Revisão Geral",
                    "foco_2": "Análise aprofundada dos erros com o Tutor IA",
                    "tempo_questoes": "1h 30min",
                    "meta_do_dia": "Alcançar mais de 75% de acertos"
                }
            ],
            "dicas_revisao": [
                "Nunca deixe de revisar o caderno de erros no dia seguinte.",
                "Dedique pelo menos 30% do seu tempo diário à resolução ativa de questões.",
                "Utilize os Flashcards para prazos, súmulas vinculantes e exceções de leis."
            ]
        }



    def _gerar_simulado_fallback(self, params: SimuladoGerarRequest) -> SimuladoGeradoAI:
        """Fallback pedagógico de alta qualidade caso a chave do Gemini ainda não tenha sido inserida ou haja indisponibilidade"""
        banco_exemplos = [
            {
                "enunciado": f"(Estilo {params.banca}) No que concerne aos princípios fundamentais e normas gerais aplicáveis a {params.tema}, assinale a alternativa juridicamente correta:",
                "alternativas": [
                    {"letra": "A", "texto": "Os atos administrativos gozam de presunção absoluta de legitimidade (juris et de jure), não admitindo prova em contrário em sede judicial."},
                    {"letra": "B", "texto": "A motivação é obrigatória em todos os atos administrativos, sem qualquer exceção prevista em doutrina ou lei federal."},
                    {"letra": "C", "texto": "A legalidade impõe que a Administração Pública somente possa agir quando houver expressa autorização ou previsão legal, distinguindo-se da legalidade privada."},
                    {"letra": "D", "texto": "O princípio da moralidade administrativa confunde-se integralmente com a moralidade comum e dispensa padrões objetivos de conduta leal."},
                    {"letra": "E", "texto": "A eficiência é um princípio infraconstitucional derivado exclusivamente da legislação ordinária do processo administrativo."}
                ],
                "resposta_certa": "C",
                "explicacao": "A alternativa C está correta conforme a clássica lição doutrinária: na Administração Pública, a legalidade é estrita (só é permitido fazer o que a lei autoriza), enquanto no âmbito privado vigora a autonomia da vontade (art. 5º, II, CF/88).",
                "tema": params.tema,
                "dificuldade": params.dificuldade
            },
            {
                "enunciado": f"(Estilo {params.banca}) Considerando as disposições constitucionais e o entendimento pacificado dos Tribunais Superiores acerca de {params.tema}, assinale a assertiva correta:",
                "alternativas": [
                    {"letra": "A", "texto": "É inconstitucional a fixação de critério de idade em concurso público mesmo quando a natureza das atribuições do cargo o justificar."},
                    {"letra": "B", "texto": "O candidato aprovado dentro do número de vagas previsto no edital possui direito subjetivo à nomeação, ressalvadas situações excepcionalíssimas devidamente motivadas."},
                    {"letra": "C", "texto": "O prazo de validade do concurso público é de até 3 anos, improrrogável."},
                    {"letra": "D", "texto": "A realização de exame psicotécnico em concurso público independe de previsão legal, bastando a constatação no edital de abertura."},
                    {"letra": "E", "texto": "As vagas reservadas a pessoas com deficiência podem superar o percentual de 50% das vagas oferecidas sem justificativa técnica."}
                ],
                "resposta_certa": "B",
                "explicacao": "Correta a assertiva B. O STF fixou a tese de Repercussão Geral (RE 598.099) no sentido de que o candidato aprovado dentro do número de vagas tem direito subjetivo à nomeação durante a validade do edital.",
                "tema": params.tema,
                "dificuldade": params.dificuldade
            },
            {
                "enunciado": f"(Estilo {params.banca}) Acerca da responsabilidade civil do Estado em temas pertinentes a {params.tema}, assinale a alternativa correta:",
                "alternativas": [
                    {"letra": "A", "texto": "As pessoas jurídicas de direito público e as de direito privado prestadoras de serviços públicos responderão pelos danos que seus agentes causarem a terceiros com base na teoria do risco administrativo."},
                    {"letra": "B", "texto": "A responsabilidade civil do Estado no Brasil é integral e não admite excludentes como força maior ou culpa exclusiva da vítima."},
                    {"letra": "C", "texto": "O direito de regresso contra o agente responsável independe de culpa ou dolo deste."},
                    {"letra": "D", "texto": "A responsabilidade por omissão estatal genérica é objetiva, prescindindo de comprovação de falta do serviço (faute du service)."},
                    {"letra": "E", "texto": "Empresas públicas exploradoras de atividade econômica respondem sempre objetivamente, independentemente do regime jurídico da concorrência."}
                ],
                "resposta_certa": "A",
                "explicacao": "Correta a A. Art. 37, § 6º da CF/88 consagra a responsabilidade civil objetiva na modalidade do risco administrativo, admitindo excludentes (culpa exclusiva da vítima, caso fortuito e força maior). A ação regressiva contra o agente exige dolo ou culpa.",
                "tema": params.tema,
                "dificuldade": params.dificuldade
            },
            {
                "enunciado": f"(Estilo {params.banca}) No que tange à aplicabilidade das normas fundamentais e disciplinares de {params.tema}, assinale a alternativa correta:",
                "alternativas": [
                    {"letra": "A", "texto": "Normas de eficácia contida produzem efeitos plenos desde a sua promulgação, mas podem ter seu alcance restringido por legislação infraconstitucional superveniente."},
                    {"letra": "B", "texto": "Normas de eficácia plena dependem impreterivelmente de lei integradora para produzir seus efeitos essenciais."},
                    {"letra": "C", "texto": "Normas de eficácia limitada possuem aplicabilidade direta, imediata e integral."},
                    {"letra": "D", "texto": "O direito de greve dos servidores públicos civis (art. 37, VII da CF) é exemplo clássico de norma de eficácia plena autoaplicável originariamente."},
                    {"letra": "E", "texto": "A revogação de uma lei inconstitucional produz automaticamente o efeito repristinatório tácito irrestrito."}
                ],
                "resposta_certa": "A",
                "explicacao": "Correta a A. Na consagrada classificação de José Afonso da Silva: normas de eficácia contida têm aplicabilidade direta e imediata, mas não integral, pois podem ser restringidas por lei.",
                "tema": params.tema,
                "dificuldade": params.dificuldade
            }
        ]

        # Monta a lista repetindo ou adaptando até a quantidade solicitada (até 20)
        questoes_geradas = []
        for i in range(params.quantidade):
            modelo = banco_exemplos[i % len(banco_exemplos)].copy()
            if i >= len(banco_exemplos):
                # Variação para cadernos grandes
                modelo["enunciado"] = f"[{i+1}] " + modelo["enunciado"]
            questoes_geradas.append(modelo)

        return SimuladoGeradoAI(
            titulo=f"Simulado de {params.tema} - Estilo {params.banca} ({len(questoes_geradas)} Questões)",
            banca=params.banca,
            tema=params.tema,
            questoes=questoes_geradas
        )


ai_service = GeminiAIService()
