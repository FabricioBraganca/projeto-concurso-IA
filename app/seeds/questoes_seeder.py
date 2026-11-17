import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Disciplina, Assunto, QuestaoBanco

logger = logging.getLogger(__name__)

DISCIPLINAS_INICIAIS = [
    {
        "nome": "Direito Constitucional",
        "icone": "⚖️",
        "slug": "direito-constitucional",
        "assuntos": [
            "Direitos e Garantias Fundamentais (Art. 5º)",
            "Ações Constitucionais (MS, HC, HD, MI, AP)",
            "Controle de Constitucionalidade (ADI, ADC, ADO, ADPF)",
            "Organização do Estado e dos Poderes",
            "Princípios Fundamentais e Ordem Social"
        ]
    },
    {
        "nome": "Direito Administrativo",
        "icone": "🏛️",
        "slug": "direito-administrativo",
        "assuntos": [
            "Nova Lei de Licitações e Contratos (Lei 14.133/21)",
            "Atos Administrativos: Elementos, Atributos e Extinção",
            "Improbidade Administrativa (Lei 8.429/92 atualizada)",
            "Regime Jurídico dos Servidores Públicos (Lei 8.112/90)",
            "Poderes Administrativos e Responsabilidade Civil do Estado"
        ]
    },
    {
        "nome": "Língua Portuguesa",
        "icone": "✍️",
        "slug": "lingua-portuguesa",
        "assuntos": [
            "Interpretação de Texto e Tipologia Textual",
            "Sintaxe de Concordância Verbal e Nominal",
            "Emprego do Sinal Indicativo de Crase",
            "Pontuação e Conectivos Lógicos/Coesão",
            "Ortografia Oficial e Acentuação Gráfica"
        ]
    },
    {
        "nome": "Raciocínio Lógico-Matemático",
        "icone": "🧠",
        "slug": "raciocinio-logico",
        "assuntos": [
            "Estruturas Lógicas e Tabela Verdade",
            "Equivalências e Negações de Proposições",
            "Diagramas Lógicos e Teoria dos Conjuntos",
            "Análise Combinatória e Probabilidade",
            "Sequências e Raciocínio Analítico"
        ]
    },
    {
        "nome": "Direito Tributário",
        "icone": "📊",
        "slug": "direito-tributario",
        "assuntos": [
            "Sistema Tributário Nacional e Princípios Constitucionais",
            "Competência Tributária e Imunidades",
            "Obrigação e Crédito Tributário (Lançamento e Extinção)",
            "Suspensão e Exclusão do Crédito Tributário",
            "Responsabilidade Tributária e Garantias"
        ]
    },
    {
        "nome": "Informática & TI",
        "icone": "💻",
        "slug": "informatica-ti",
        "assuntos": [
            "Segurança da Informação, Criptografia e Malware",
            "Redes de Computadores, Internet e Protocolos",
            "Bancos de Dados Relacionais e Linguagem SQL",
            "Computação em Nuvem e Ferramentas Corporativas",
            "Sistemas Operacionais (Linux e Windows)"
        ]
    },
    {
        "nome": "Direito Penal",
        "icone": "⚔️",
        "slug": "direito-penal",
        "assuntos": [
            "Princípios Penais e Aplicação da Lei no Tempo e Espaço",
            "Teoria do Crime: Fato Típico, Ilicitude e Culpabilidade",
            "Crimes contra a Administração Pública",
            "Crimes contra o Patrimônio",
            "Crimes contra a Pessoa"
        ]
    },
    {
        "nome": "Direito Processual Penal",
        "icone": "🚓",
        "slug": "direito-processual-penal",
        "assuntos": [
            "Inquérito Policial (Características, Prazos e Notitia Criminis)",
            "Ação Penal (Pública Incondicionada, Condicionada e Privada)",
            "Prisões Cautelares (Flagrante, Preventiva e Temporária)",
            "Teoria das Provas e Cadeia de Custódia (Pacote Anticrime)",
            "Acordo de Não Persecução Penal (ANPP) e Juizados Especiais"
        ]
    },
    {
        "nome": "Direito Processual Civil",
        "icone": "⚖️",
        "slug": "direito-processual-civil",
        "assuntos": [
            "Normas Fundamentais e Competência no CPC/15",
            "Atos Processuais, Prazos e Nulidades",
            "Tutela Provisória (Urgência e Evidência)",
            "Teoria Geral dos Recursos e Apelação",
            "Cumprimento de Sentença e Execução de Título Extrajudicial"
        ]
    },
    {
        "nome": "Direito Civil",
        "icone": "📜",
        "slug": "direito-civil",
        "assuntos": [
            "LINDB e Aplicação da Lei no Tempo e Espaço",
            "Pessoas Naturais, Capacidade e Pessoas Jurídicas",
            "Bens e Fatos Jurídicos (Negócio Jurídico e Vícios)",
            "Teoria Geral das Obrigações e Inadimplemento",
            "Responsabilidade Civil e Contratos em Geral"
        ]
    },
    {
        "nome": "Contabilidade Geral & Pública",
        "icone": "📈",
        "slug": "contabilidade",
        "assuntos": [
            "Patrimônio: Ativo, Passivo e Patrimônio Líquido",
            "Balanço Patrimonial e DRE (Demonstração do Resultado)",
            "Escrituração Contábil, Lançamentos e Balancete",
            "Contabilidade Pública: MCASP, SIAFI e Variações Patrimoniais",
            "Demonstrações Contábeis Aplicadas ao Setor Público"
        ]
    },
    {
        "nome": "Administração Pública & Gestão Governamental",
        "icone": "🌐",
        "slug": "administracao-publica",
        "assuntos": [
            "Evolução da Gestão: Patrimonialista, Burocrática e Gerencial",
            "Governança Pública, Transparência e Accountability",
            "Gestão Estratégica, Indicadores e Gestão por Processos",
            "Políticas Públicas: Ciclo, Formulação e Avaliação",
            "Gestão de Pessoas e Liderança no Setor Público"
        ]
    },
    {
        "nome": "Direito do Trabalho & Processual do Trabalho",
        "icone": "👷",
        "slug": "direito-do-trabalho",
        "assuntos": [
            "Relação de Trabalho vs Emprego e Princípios da CLT",
            "Contrato de Trabalho, Teletrabalho e Terceirização",
            "Jornada de Trabalho, Descanso Semanal e Horas Extras",
            "Remuneração, Salário e Verbas Rescisórias",
            "Processo do Trabalho: Reclamação Trabalhista e Recursos"
        ]
    },
    {
        "nome": "Ética & Legislação do Servidor Público",
        "icone": "🛡️",
        "slug": "etica-servico-publico",
        "assuntos": [
            "Código de Ética do Servidor Público Federal (Dec. 1.171/94)",
            "Lei de Acesso à Informação - LAI (Lei 12.527/11)",
            "Lei Geral de Proteção de Dados - LGPD (Lei 13.709/18)",
            "Lei de Conflito de Interesses (Lei 12.813/13)",
            "Processo Administrativo Federal (Lei 9.784/99)"
        ]
    },
    {
        "nome": "Economia & Finanças Públicas",
        "icone": "💰",
        "slug": "economia-financas-publicas",
        "assuntos": [
            "Orçamento Público: PPA, LDO e LOA",
            "Princípios Orçamentários Constitucionais",
            "Receita Pública e Despesa Pública (Classificação e Estágios)",
            "Lei de Responsabilidade Fiscal - LRF (LC 101/00)",
            "Noções de Micro e Macroeconomia Aplicadas"
        ]
    },
    {
        "nome": "Conhecimentos Bancários & Mercado Financeiro",
        "icone": "🏦",
        "slug": "conhecimentos-bancarios",
        "assuntos": [
            "Sistema Financeiro Nacional (SFN): CMN, BACEN e CVM",
            "Produtos e Serviços Bancários (Crédito, Depósitos e Câmbio)",
            "Mercado de Capitais e Títulos Públicos e Privados",
            "Sistema de Pagamentos Brasileiro (SPB) e Pix",
            "Prevenção à Lavagem de Dinheiro (Lei 9.613/98)"
        ]
    }
]

QUESTOES_REAIS_SEEDS: List[Dict[str, Any]] = [
    # --- DIREITO CONSTITUCIONAL ---
    {
        "disciplina_slug": "direito-constitucional",
        "assunto_nome": "Direitos e Garantias Fundamentais (Art. 5º)",
        "banca": "Cebraspe",
        "orgao": "Polícia Federal (PF)",
        "cargo": "Agente de Polícia Federal",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "A respeito dos direitos e deveres individuais e coletivos previstos na Constituição Federal de 1988, assinale a opção correta:",
        "alternativas": [
            {"letra": "A", "texto": "A casa é asilo inviolável do indivíduo, não sendo permitida a entrada sem consentimento do morador em nenhuma hipótese durante a noite."},
            {"letra": "B", "texto": "A prisão de qualquer pessoa e o local onde se encontre serão comunicados imediatamente apenas à família do preso."},
            {"letra": "C", "texto": "É plena a liberdade de associação para fins lícitos, vedada a de caráter paramilitar."},
            {"letra": "D", "texto": "A criação de associações depende de expressa autorização do Poder Executivo estadual ou federal."},
            {"letra": "E", "texto": "A prática do racismo constitui crime inafiançável e prescritível, sujeito à pena de detenção."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a alternativa C. O art. 5º, XVII da CF/88 estabelece textualmente: 'é plena a liberdade de associação para fins lícitos, vedada a de caráter paramilitar'. Erros das demais: A) Flagrante delito, desastre ou socorro autorizam entrada noturna; B) Comunica-se ao juiz e à família/pessoa indicada (art. 5º, LXII); D) Independe de autorização (art. 5º, XVIII); E) O racismo é inafiançável e imprescritível (art. 5º, XLII)."
    },
    {
        "disciplina_slug": "direito-constitucional",
        "assunto_nome": "Controle de Constitucionalidade (ADI, ADC, ADO, ADPF)",
        "banca": "FGV",
        "orgao": "Senado Federal",
        "cargo": "Analista Legislativo",
        "ano": 2024,
        "dificuldade": "Difícil",
        "enunciado": "Sobre o sistema brasileiro de controle concentrado de constitucionalidade, assinale a alternativa em consonância com a jurisprudência do STF:",
        "alternativas": [
            {"letra": "A", "texto": "A Ação Direta de Inconstitucionalidade (ADI) pode ter como objeto lei municipal que contrarie norma da Constituição Federal."},
            {"letra": "B", "texto": "A Arguição de Descumprimento de Preceito Fundamental (ADPF) rege-se pelo princípio da subsidiariedade, cabendo apenas quando não houver outro meio eficaz de sanar a lesividade."},
            {"letra": "C", "texto": "O Governador de Estado possui legitimidade ativa universal, dispensando demonstração de pertinência temática em qualquer ADI."},
            {"letra": "D", "texto": "A decisão de mérito em Ação Declaratória de Constitucionalidade (ADC) produz efeitos ex nunc de forma automática, vedada a modulação."},
            {"letra": "E", "texto": "Partidos políticos sem representação no Congresso Nacional podem ajuizar ADI perante o STF desde que registrados no TSE."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a assertiva B. Conforme art. 4º, § 1º da Lei nº 9.882/1999 e pacífico entendimento do STF, a ADPF submete-se ao princípio da subsidiariedade. Erros: A) Lei municipal perante a CF/88 é objeto de ADPF, não de ADI; C) Governadores e Mesas de Assembleias são legitimados especiais e exigem pertinência temática; D) O efeito regra é ex tunc; E) Exige-se representação no Congresso Nacional (art. 103, VIII, CF)."
    },
    {
        "disciplina_slug": "direito-constitucional",
        "assunto_nome": "Ações Constitucionais (MS, HC, HD, MI, AP)",
        "banca": "FCC",
        "orgao": "TRF 3ª Região",
        "cargo": "Analista Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Para assegurar o conhecimento de informações relativas à pessoa do impetrante, constantes de registros ou bancos de dados de entidades governamentais, o remédio constitucional cabível é:",
        "alternativas": [
            {"letra": "A", "texto": "Mandado de Injunção."},
            {"letra": "B", "texto": "Ação Popular."},
            {"letra": "C", "texto": "Habeas Data."},
            {"letra": "D", "texto": "Mandado de Segurança Coletivo."},
            {"letra": "E", "texto": "Reclamação Constitucional."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a C. Nos termos do art. 5º, LXXII, 'a' da CF/88, concede-se Habeas Data para assegurar o conhecimento de informações relativas à pessoa do impetrante constantes de registros governamentais ou de caráter público (Súmula 2 do STJ exige prévia recusa administrativa)."
    },

    # --- DIREITO ADMINISTRATIVO ---
    {
        "disciplina_slug": "direito-administrativo",
        "assunto_nome": "Nova Lei de Licitações e Contratos (Lei 14.133/21)",
        "banca": "FGV",
        "orgao": "Receita Federal do Brasil",
        "cargo": "Auditor-Fiscal da Receita Federal",
        "ano": 2024,
        "dificuldade": "Difícil",
        "enunciado": "À luz da Nova Lei de Licitações e Contratos Administrativos (Lei nº 14.133/2021), assinale a afirmativa correta:",
        "alternativas": [
            {"letra": "A", "texto": "A tomada de preços e o convite continuam sendo modalidades licitatórias regulares na administração federal."},
            {"letra": "B", "texto": "O diálogo competitivo é uma modalidade destinada à contratação de obras, serviços e compras em que a Administração não possui a solução técnica pronta."},
            {"letra": "C", "texto": "O pregão pode ser utilizado para a contratação de obras especiais e de engenharia complexa sem limite de valor."},
            {"letra": "D", "texto": "A fase preparatória (planejamento) foi suprimida para dar maior celeridade às contratações de tecnologia."},
            {"letra": "E", "texto": "A inexigibilidade de licitação aplica-se quando houver possibilidade de competição ampla entre fornecedores com padronização objetiva."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a alternativa B. O diálogo competitivo (art. 6º, XLII e art. 32 da Lei 14.133/21) destina-se a inovações técnicas e contratações em que o órgão público busca desenvolver soluções com os participantes. A e C estão incorretas pois convite e tomada de preços foram extintos, e pregão não se aplica a obras de engenharia comuns complexas."
    },
    {
        "disciplina_slug": "direito-administrativo",
        "assunto_nome": "Improbidade Administrativa (Lei 8.429/92 atualizada)",
        "banca": "Cebraspe",
        "orgao": "TSE Unificado",
        "cargo": "Analista Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Com base nas inovações introduzidas pela Lei nº 14.230/2021 na Lei de Improbidade Administrativa (Lei nº 8.429/1992), é correto afirmar que:",
        "alternativas": [
            {"letra": "A", "texto": "Configura ato de improbidade administrativa a conduta meramente culposa quando causar grave prejuízo ao erário."},
            {"letra": "B", "texto": "Exige-se expressamente o dolo específico para a caracterização de qualquer ato de improbidade administrativa."},
            {"letra": "C", "texto": "A divergência interpretativa da lei, fundada em jurisprudência não pacificada, configura improbidade com perda de cargo."},
            {"letra": "D", "texto": "O prazo prescricional para ajuizamento da ação de improbidade é de 2 anos a contar da exoneração do cargo em comissão."},
            {"letra": "E", "texto": "O particular que concorre para o ato pode responder isoladamente por improbidade sem a presença do agente público."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Conforme art. 1º, §§ 1º, 2º e 3º da Lei 8.429/92 (com redação da Lei 14.230/21) e tese firmada pelo STF no ARE 843.989 (Tema 1.199), a revogação da modalidade culposa é irretroativa para condenações transitadas em julgado e todos os tipos exigem dolo específico com vontade livre e consciente."
    },
    {
        "disciplina_slug": "direito-administrativo",
        "assunto_nome": "Atos Administrativos: Elementos, Atributos e Extinção",
        "banca": "Vunesp",
        "orgao": "TJ-SP",
        "cargo": "Escrevente Técnico Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "A revogação de um ato administrativo pela Administração Pública:",
        "alternativas": [
            {"letra": "A", "texto": "Opera efeitos retroativos (ex tunc), desfazendo todas as relações jurídicas pretéritas."},
            {"letra": "B", "texto": "Funda-se em vício de legalidade insanável que macula a gênese do ato."},
            {"letra": "C", "texto": "Recai sobre ato discricionário perfeito, por razões de conveniência e oportunidade, produzindo efeitos ex nunc."},
            {"letra": "D", "texto": "Pode ser decretada de ofício pelo Poder Judiciário em sede de controle abstrato de constitucionalidade."},
            {"letra": "E", "texto": "Pode incidir livremente sobre atos que geraram direitos adquiridos para o administrado."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a C. A revogação funda-se no mérito administrativo (conveniência e oportunidade) e tem efeitos não retroativos (ex nunc). A anulação é que decorre de ilegalidade com efeitos ex tunc (Súmulas 346 e 473 do STF). O Judiciário não revoga ato do Executivo, e direito adquirido não pode ser revogado (art. 53 da Lei 9.784/99)."
    },

    # --- LÍNGUA PORTUGUESA ---
    {
        "disciplina_slug": "lingua-portuguesa",
        "assunto_nome": "Emprego do Sinal Indicativo de Crase",
        "banca": "FGV",
        "orgao": "Receita Federal",
        "cargo": "Analista Tributário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Assinale a frase em que o emprego do acento grave indicativo de crase está inteiramente correto segundo a norma-padrão:",
        "alternativas": [
            {"letra": "A", "texto": "O fiscal dirigiu-se à ela para solicitar a apresentação das notas fiscais de entrada."},
            {"letra": "B", "texto": "O candidato estava disposto à prestar concurso para qualquer tribunal do país."},
            {"letra": "C", "texto": "Ficamos face à face com os novos desafios impostos pela inteligência artificial nos tributos."},
            {"letra": "D", "texto": "A equipe de auditores compareceu à cerimônia de posse do novo secretário da Fazenda."},
            {"letra": "E", "texto": "O relatório foi encaminhado à qualquer repartição que solicitasse cópia oficial."}
        ],
        "resposta_certa": "D",
        "explicacao_fundamentada": "Correta a D. 'Compareceu a' (rege preposição 'a') + 'a cerimônia' (artigo feminino) = crase obrigatória. Erros: A) Antes de pronome pessoal não há artigo; B) Antes de verbo no infinitivo não se usa crase; C) Expressões com palavras repetidas não levam crase; E) Antes de pronome indefinido não ocorre crase."
    },
    {
        "disciplina_slug": "lingua-portuguesa",
        "assunto_nome": "Sintaxe de Concordância Verbal e Nominal",
        "banca": "FCC",
        "orgao": "TRT 2ª Região",
        "cargo": "Técnico Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "A concordância verbal está de acordo com as normas gramaticais vigentes na seguinte frase:",
        "alternativas": [
            {"letra": "A", "texto": "Fazem dez anos que os servidores aguardavam a reestruturação da carreira judiciária."},
            {"letra": "B", "texto": "Houveram muitos incidentes durante a aplicação das provas no turno da manhã."},
            {"letra": "C", "texto": "Mais de um candidato contestaram o gabarito preliminar da banca examinadora."},
            {"letra": "D", "texto": "Alugam-se salas completas para cursos preparatórios no centro da cidade."},
            {"letra": "E", "texto": "Precisa-se de técnicos especializados em tecnologia da informação nos tribunais."}
        ],
        "resposta_certa": "D",
        "explicacao_fundamentada": "Correta a alternativa D. Na voz passiva sintética com pronome apassivador 'se' ('Alugam-se salas'), o verbo transita diretamente e concorda com o sujeito paciente ('salas são alugadas'). A e B: Fazer e Haver com sentido de tempo/existência são impessoais (Faz dez anos / Houve muitos incidentes)."
    },

    # --- RACIOCÍNIO LÓGICO-MATEMÁTICO ---
    {
        "disciplina_slug": "raciocinio-logico",
        "assunto_nome": "Equivalências e Negações de Proposições",
        "banca": "Cebraspe",
        "orgao": "Polícia Federal (PF)",
        "cargo": "Escrivão de Polícia Federal",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Considere a seguinte proposição condicional: 'Se o suspeito mente, então o inquérito não é concluído'. A negação lógica dessa proposição é dada por:",
        "alternativas": [
            {"letra": "A", "texto": "Se o suspeito não mente, então o inquérito é concluído."},
            {"letra": "B", "texto": "O suspeito mente e o inquérito é concluído."},
            {"letra": "C", "texto": "O suspeito não mente ou o inquérito não é concluído."},
            {"letra": "D", "texto": "Se o inquérito é concluído, então o suspeito não mente."},
            {"letra": "E", "texto": "O suspeito mente ou o inquérito é concluído."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Pela regra de negação do condicional (Regra do 'MANÉ'): ~(P -> Q) <=> P ^ ~Q. Mantém a primeira ('O suspeito mente') E nega a segunda ('o inquérito é concluído'). Portanto: 'O suspeito mente e o inquérito é concluído'."
    },
    {
        "disciplina_slug": "raciocinio-logico",
        "assunto_nome": "Estruturas Lógicas e Tabela Verdade",
        "banca": "FGV",
        "orgao": "TSE Unificado",
        "cargo": "Técnico Judiciário",
        "ano": 2024,
        "dificuldade": "Fácil",
        "enunciado": "Dadas as proposições p: 'O candidato estuda' (verdadeira) e q: 'O candidato passa' (falsa), o valor lógico da proposição composta p -> q é:",
        "alternativas": [
            {"letra": "A", "texto": "Verdadeiro, pois a primeira proposição é verdadeira."},
            {"letra": "B", "texto": "Falso, pois em uma condicional antecedente verdadeiro com consequente falso resulta em falsidade."},
            {"letra": "C", "texto": "Verdadeiro, devido à equivalência com a disjunção inclusiva."},
            {"letra": "D", "texto": "Indeterminado, pois depende do conectivo de conjunção."},
            {"letra": "E", "texto": "Falso somente se ambas forem falsas simultaneamente."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Na tabela-verdade do condicional (p -> q), a única linha com resultado Falso ocorre quando o antecedente é Verdadeiro (V) e o consequente é Falso (F) (o famoso 'Vera Fischer é Falsa')."
    },

    # --- DIREITO TRIBUTÁRIO ---
    {
        "disciplina_slug": "direito-tributario",
        "assunto_nome": "Suspensão e Exclusão do Crédito Tributário",
        "banca": "FGV",
        "orgao": "Receita Federal",
        "cargo": "Auditor-Fiscal",
        "ano": 2024,
        "dificuldade": "Difícil",
        "enunciado": "Consoante as regras expressas do Código Tributário Nacional (CTN), são causas que, respectivamente, SUSPENDEM a exigibilidade e EXCLUEM o crédito tributário:",
        "alternativas": [
            {"letra": "A", "texto": "A compensação e a anistia."},
            {"letra": "B", "texto": "O depósito do montante integral e a isenção."},
            {"letra": "C", "texto": "A remissão e a moratória."},
            {"letra": "D", "texto": "A prescrição e o parcelamento."},
            {"letra": "E", "texto": "A decadência e o pagamento antecipado."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Art. 151 do CTN (Suspensão): Moratória, depósito integral, reclamações/recursos administrativos, liminar em MS, tutela provisória e parcelamento. Art. 175 do CTN (Exclusão): Isenção e anistia. Compensação, remissão, decadência e prescrição são causas de extinção (art. 156)."
    },

    # --- INFORMÁTICA & TI ---
    {
        "disciplina_slug": "informatica-ti",
        "assunto_nome": "Segurança da Informação, Criptografia e Malware",
        "banca": "Cebraspe",
        "orgao": "Polícia Federal (PF)",
        "cargo": "Perito Criminal Federal",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Em segurança da informação, o tipo de código malicioso que sequestra os arquivos de um sistema criptografando seus dados e exigindo pagamento financeiro para a chave de decifragem denomina-se:",
        "alternativas": [
            {"letra": "A", "texto": "Spyware."},
            {"letra": "B", "texto": "Ransomware."},
            {"letra": "C", "texto": "Trojan Horse (Cavalo de Troia)."},
            {"letra": "D", "texto": "Worm de replicação em rede."},
            {"letra": "E", "texto": "Keylogger silencioso."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Ransomware é o malware sequestrador que encripta os dados da vítima e exige resgate (ransom) geralmente em criptomoedas. Spyware espiona; Trojan abre portas backdoor; Worm se auto-propaga sem precisar de hospedeiro."
    },
    {
        "disciplina_slug": "informatica-ti",
        "assunto_nome": "Bancos de Dados Relacionais e Linguagem SQL",
        "banca": "FCC",
        "orgao": "TRT 2ª Região",
        "cargo": "Analista de Tecnologia da Informação",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Na linguagem SQL padrão ANSI, para remover todas as tuplas de uma tabela preservando sua estrutura sem gerar logs individuais de rollback linha a linha, o comando mais eficiente é:",
        "alternativas": [
            {"letra": "A", "texto": "DELETE FROM tabela WHERE 1=1;"},
            {"letra": "B", "texto": "DROP TABLE tabela;"},
            {"letra": "C", "texto": "TRUNCATE TABLE tabela;"},
            {"letra": "D", "texto": "ALTER TABLE tabela DROP ALL;"},
            {"letra": "E", "texto": "REMOVE ALL ROWS FROM tabela;"}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a C. TRUNCATE TABLE é um comando DDL que desaloca as páginas de dados rapidamente, resetando a tabela e preservando sua estrutura e índices, sendo muito mais performático que o DELETE DML que gera log individual para cada linha."
    },

    # --- DIREITO PENAL ---
    {
        "disciplina_slug": "direito-penal",
        "assunto_nome": "Crimes contra a Administração Pública",
        "banca": "Vunesp",
        "orgao": "TJ-SP",
        "cargo": "Escrevente Técnico Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "O funcionário público que exige, para si ou para outrem, direta ou indiretamente, em razão da função, vantagem indevida, comete o crime de:",
        "alternativas": [
            {"letra": "A", "texto": "Corrupção passiva."},
            {"letra": "B", "texto": "Concussão."},
            {"letra": "C", "texto": "Prevaricação."},
            {"letra": "D", "texto": "Condescendência criminosa."},
            {"letra": "E", "texto": "Peculato-apropriação."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a alternativa B. Concussão (art. 316 do CP): verbo nuclear é EXIGIR. Corrupção passiva (art. 317): solicitar, receber ou aceitar promessa. Prevaricação (art. 319): retardar ou deixar de praticar ato de ofício para satisfazer interesse ou sentimento pessoal."
    },

    # --- DIREITO PROCESSUAL PENAL ---
    {
        "disciplina_slug": "direito-processual-penal",
        "assunto_nome": "Teoria das Provas e Cadeia de Custódia (Pacote Anticrime)",
        "banca": "Cebraspe",
        "orgao": "Polícia Federal (PF)",
        "cargo": "Perito Criminal Federal",
        "ano": 2024,
        "dificuldade": "Difícil",
        "enunciado": "De acordo com as regras do Código de Processo Penal introduzidas pelo Pacote Anticrime (Lei nº 13.964/2019) a respeito da cadeia de custódia, assinale a opção correta:",
        "alternativas": [
            {"letra": "A", "texto": "A cadeia de custódia inicia-se apenas com a instauração formal do inquérito policial pela autoridade competente."},
            {"letra": "B", "texto": "O isolamento do local do crime é atribuição exclusiva do juiz das garantias."},
            {"letra": "C", "texto": "O início da cadeia de custódia dá-se com a preservação do local de crime ou com procedimentos policiais nos quais seja detectada a existência de vestígio."},
            {"letra": "D", "texto": "O acondicionamento de vestígios pode ser feito sem lacre numerado desde que certificado por duas testemunhas."},
            {"letra": "E", "texto": "A quebra da cadeia de custódia gera nulidade absoluta automática e insanável em qualquer circunstância processual."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a alternativa C. O art. 158-A, § 1º do CPP prevê expressamente que o início da cadeia de custódia dá-se com a preservação do local de crime ou com procedimentos policiais/periciais em que seja detectada a presença de vestígio."
    },

    # --- DIREITO PROCESSUAL CIVIL ---
    {
        "disciplina_slug": "direito-processual-civil",
        "assunto_nome": "Tutela Provisória (Urgência e Evidência)",
        "banca": "FGV",
        "orgao": "TJ-SP",
        "cargo": "Analista Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "A respeito da tutela de evidência regulada pelo Código de Processo Civil de 2015 (art. 311), é correto afirmar que:",
        "alternativas": [
            {"letra": "A", "texto": "Depende da demonstração inequívoca de perigo de dano ou de risco ao resultado útil do processo (periculum in mora)."},
            {"letra": "B", "texto": "Pode ser concedida liminarmente quando as alegações de fato puderem ser comprovadas apenas documentalmente e houver tese firmada em julgamento de casos repetitivos ou em súmula vinculante."},
            {"letra": "C", "texto": "Exige sempre e obrigatoriamente a oitiva prévia da parte contrária antes de qualquer apreciação judicial."},
            {"letra": "D", "texto": "Não admite execução provisória de decisão concessiva antes do trânsito em julgado."},
            {"letra": "E", "texto": "Tem caráter estritamente cautelar e não pode antecipar os efeitos práticos do pedido principal."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Art. 311, parágrafo único do CPC/15: a tutela de evidência independe de perigo de dano e pode ser concedida liminarmente nas hipóteses dos incisos II (tese repetitiva/súmula vinculante com prova documental) e III (pedido reipersecutório)."
    },

    # --- DIREITO CIVIL ---
    {
        "disciplina_slug": "direito-civil",
        "assunto_nome": "Bens e Fatos Jurídicos (Negócio Jurídico e Vícios)",
        "banca": "FCC",
        "orgao": "TRF 3ª Região",
        "cargo": "Analista Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "No direito civil brasileiro, o negócio jurídico praticado com vício de simulação é considerado:",
        "alternativas": [
            {"letra": "A", "texto": "Anulável, no prazo decadencial de 4 anos contados da data de celebração do negócio."},
            {"letra": "B", "texto": "Nulo de pleno direito, não convalescendo pelo decurso do tempo nem admitindo confirmação."},
            {"letra": "C", "texto": "Eficaz perante terceiros de boa-fé, mas rescindível por ação rescisória autônoma."},
            {"letra": "D", "texto": "Válido se a simulação for relativa e não causar prejuízo imediato ao credor fiduciário."},
            {"letra": "E", "texto": "Anulável apenas se arguido por credor quirografário preexistente à data do negócio."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Diferentemente do Código Civil de 1916 (onde era anulável), no CC/2002 (art. 167) a simulação é causa de NULIDADE absoluta do negócio jurídico, e o art. 169 estabelece que o negócio nulo não convalesce pelo decurso do tempo."
    },

    # --- CONTABILIDADE GERAL & PÚBLICA ---
    {
        "disciplina_slug": "contabilidade",
        "assunto_nome": "Patrimônio: Ativo, Passivo e Patrimônio Líquido",
        "banca": "FGV",
        "orgao": "Receita Federal do Brasil",
        "cargo": "Auditor-Fiscal da Receita Federal",
        "ano": 2024,
        "dificuldade": "Difícil",
        "enunciado": "De acordo com o Pronunciamento Técnico CPC 00 (R2) - Estrutura Conceitual para Relatório Financeiro, um Ativo é definido como:",
        "alternativas": [
            {"letra": "A", "texto": "Um recurso de propriedade legal e física exclusiva da entidade que gerou receitas no exercício anterior."},
            {"letra": "B", "texto": "Um recurso econômico presente controlado pela entidade como resultado de eventos passados."},
            {"letra": "C", "texto": "Toda entrada futura e certa de caixa decorrente de transações operacionais do ativo imobilizado."},
            {"letra": "D", "texto": "O valor residual dos ativos da entidade após a dedução de todos os seus passivos exigíveis."},
            {"letra": "E", "texto": "A soma de bens corpóreos e incorpóreos avaliados unicamente pelo método do custo histórico."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Item 4.3 do CPC 00 (R2): 'Um ativo é um recurso econômico presente controlado pela entidade como resultado de eventos passados'. Note que o controle econômico prevalece sobre a propriedade jurídica."
    },

    # --- ADMINISTRAÇÃO PÚBLICA ---
    {
        "disciplina_slug": "administracao-publica",
        "assunto_nome": "Evolução da Gestão: Patrimonialista, Burocrática e Gerencial",
        "banca": "Cebraspe",
        "orgao": "TCU",
        "cargo": "Auditor Federal de Controle Externo",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Acerca da evolução dos modelos de administração pública no Brasil, assinale a opção correta:",
        "alternativas": [
            {"letra": "A", "texto": "O modelo patrimonialista caracterizava-se pela estrita separação entre a coisa pública (res publica) e os bens particulares do soberano."},
            {"letra": "B", "texto": "O modelo gerencial rejeita integralmente todos os mecanismos burocráticos de impessoalidade e legalidade formal."},
            {"letra": "C", "texto": "A Reforma do Estado de 1995 (Plano Diretor da Reforma do Aparelho do Estado - PDRAE) buscou transitar de uma administração burocrática focada em processos para uma gestão orientada a resultados e cidadão."},
            {"letra": "D", "texto": "O DASP (Departamento Administrativo do Serviço Público) foi criado na década de 1990 para introduzir o neoliberalismo no Poder Executivo."},
            {"letra": "E", "texto": "O modelo burocrático weberiano prioriza a descentralização decisória e o controle flexível a posteriori."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a alternativa C. O PDRAE de 1995 liderado por Bresser-Pereira introduziu o modelo de Administração Pública Gerencial no Brasil, mantendo o núcleo burocrático de impessoalidade e meritocracia, mas focando na eficiência dos serviços públicos e avaliação de resultados."
    },

    # --- DIREITO DO TRABALHO ---
    {
        "disciplina_slug": "direito-do-trabalho",
        "assunto_nome": "Jornada de Trabalho, Descanso Semanal e Horas Extras",
        "banca": "FCC",
        "orgao": "TRT 2ª Região",
        "cargo": "Analista Judiciário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "Segundo a Consolidação das Leis do Trabalho (CLT) com as alterações da Reforma Trabalhista (Lei nº 13.467/2017), o tempo despendido pelo empregado desde a sua residência até a efetiva ocupação do posto de trabalho e para o seu retorno (horas in itinere):",
        "alternativas": [
            {"letra": "A", "texto": "Será computado na jornada de trabalho sempre que o local de trabalho for de difícil acesso ou não servido por transporte público regular."},
            {"letra": "B", "texto": "Não será computado na jornada de trabalho, por não ser tempo à disposição do empregador, ainda que fornecido transporte pela empresa."},
            {"letra": "C", "texto": "Será pago como hora extraordinária com adicional mínimo obrigatório de 100%."},
            {"letra": "D", "texto": "Gera direito a banco de horas semestral obrigatório previsto em acordo individual."},
            {"letra": "E", "texto": "Será considerado tempo à disposição apenas para empregados com contrato de trabalho intermitente."}
        ],
        "resposta_certa": "B",
        "explicacao_fundamentada": "Correta a B. Art. 58, § 2º da CLT (alterado pela Reforma Trabalhista Lei 13.467/17): o tempo de deslocamento residência-trabalho e vice-versa, qualquer que seja o meio de transporte (mesmo fornecido pelo empregador), NÃO é tempo à disposição e não integra a jornada."
    },

    # --- ÉTICA & LEGISLAÇÃO ---
    {
        "disciplina_slug": "etica-servico-publico",
        "assunto_nome": "Código de Ética do Servidor Público Federal (Dec. 1.171/94)",
        "banca": "Cebraspe",
        "orgao": "INSS",
        "cargo": "Técnico do Seguro Social",
        "ano": 2024,
        "dificuldade": "Fácil",
        "enunciado": "Consoante o Decreto Federal nº 1.171/1994 (Código de Ética Profissional do Servidor Público Civil do Poder Executivo Federal), a pena aplicável pela Comissão de Ética ao servidor que descumprir preceito ético é:",
        "alternativas": [
            {"letra": "A", "texto": "Demissão a bem do serviço público."},
            {"letra": "B", "texto": "Suspensão disciplinar de até 30 dias com perda da remuneração."},
            {"letra": "C", "texto": "Censura ética fundamentada."},
            {"letra": "D", "texto": "Destituição de cargo em comissão ou função de confiança."},
            {"letra": "E", "texto": "Multa pecuniária equivalente a um mês de vencimento básico."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a C. Item XXII do Decreto 1.171/94: 'A pena aplicável ao servidor público pela Comissão de Ética é a de CENSURA e sua fundamentação constará do respectivo parecer, assinado por todos os seus integrantes'."
    },

    # --- ECONOMIA & FINANÇAS PÚBLICAS ---
    {
        "disciplina_slug": "economia-financas-publicas",
        "assunto_nome": "Lei de Responsabilidade Fiscal - LRF (LC 101/00)",
        "banca": "FGV",
        "orgao": "Receita Federal",
        "cargo": "Auditor-Fiscal",
        "ano": 2024,
        "dificuldade": "Difícil",
        "enunciado": "Nos termos da Lei de Responsabilidade Fiscal (Lei Complementar nº 101/2000), o limite total da despesa com pessoal para o Poder Executivo da União é de:",
        "alternativas": [
            {"letra": "A", "texto": "60% da Receita Corrente Líquida (RCL)."},
            {"letra": "B", "texto": "50% da Receita Corrente Líquida (RCL)."},
            {"letra": "C", "texto": "40,9% da Receita Corrente Líquida (RCL)."},
            {"letra": "D", "texto": "30% da Receita Tributária Própria."},
            {"letra": "E", "texto": "70% do orçamento fiscal e de seguridade social."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a C. Na União, o limite total de despesa com pessoal é de 50% da RCL (art. 19, I). Desse percentual, o art. 20, I, 'c' da LRF reparte 40,9% para o Poder Executivo, 6% para o Judiciário, 2,5% para o Legislativo e 0,6% para o MPU."
    },

    # --- CONHECIMENTOS BANCÁRIOS ---
    {
        "disciplina_slug": "conhecimentos-bancarios",
        "assunto_nome": "Sistema Financeiro Nacional (SFN): CMN, BACEN e CVM",
        "banca": "Cesgranrio",
        "orgao": "Banco do Brasil / Caixa Econômica Federal",
        "cargo": "Escriturário / Técnico Bancário",
        "ano": 2024,
        "dificuldade": "Médio",
        "enunciado": "No âmbito do Sistema Financeiro Nacional (SFN), o órgão normativo máximo responsável por fixar as diretrizes gerais das políticas monetária, cambial e creditícia é:",
        "alternativas": [
            {"letra": "A", "texto": "O Banco Central do Brasil (BACEN)."},
            {"letra": "B", "texto": "A Comissão de Valores Mobiliários (CVM)."},
            {"letra": "C", "texto": "O Conselho Monetário Nacional (CMN)."},
            {"letra": "D", "texto": "O Banco do Brasil (BB)."},
            {"letra": "E", "texto": "A Federação Brasileira de Bancos (FEBRABAN)."}
        ],
        "resposta_certa": "C",
        "explicacao_fundamentada": "Correta a C. O Conselho Monetário Nacional (CMN) é o órgão superior normativo do SFN (Lei 4.595/64), responsável por fixar diretrizes e metas de inflação. O BACEN e a CVM são entidades supervisoras e executoras."
    }
]


def popular_banco_se_vazio(db: Session):
    """
    Popula o catálogo de disciplinas, assuntos e acervo inicial de questões reais de bancas.
    Executado de forma estritamente idempotente (adiciona novas disciplinas e questões sem duplicar existentes).
    """
    logger.info("Verificando integridade e sincronização do catálogo de disciplinas...")
    for d_info in DISCIPLINAS_INICIAIS:
        disc = db.query(Disciplina).filter(Disciplina.slug == d_info["slug"]).first()
        if not disc:
            disc = Disciplina(
                nome=d_info["nome"],
                icone=d_info["icone"],
                slug=d_info["slug"]
            )
            db.add(disc)
            db.flush()

        for ass_nome in d_info["assuntos"]:
            ass = db.query(Assunto).filter(
                Assunto.disciplina_id == disc.id,
                Assunto.nome == ass_nome
            ).first()
            if not ass:
                ass = Assunto(
                    disciplina_id=disc.id,
                    nome=ass_nome
                )
                db.add(ass)
    db.commit()

    logger.info("Sincronizando acervo de questões reais oficiais...")
    for q_info in QUESTOES_REAIS_SEEDS:
        disc = db.query(Disciplina).filter(Disciplina.slug == q_info["disciplina_slug"]).first()
        if not disc:
            continue
        
        assunto = db.query(Assunto).filter(
            Assunto.disciplina_id == disc.id,
            Assunto.nome == q_info["assunto_nome"]
        ).first()

        # Evita duplicação se o enunciado já estiver no banco
        existe = db.query(QuestaoBanco).filter(
            QuestaoBanco.enunciado == q_info["enunciado"],
            QuestaoBanco.banca == q_info["banca"]
        ).first()

        if not existe:
            qb = QuestaoBanco(
                disciplina_id=disc.id,
                assunto_id=assunto.id if assunto else None,
                banca=q_info["banca"],
                orgao=q_info["orgao"],
                cargo=q_info["cargo"],
                ano=q_info["ano"],
                enunciado=q_info["enunciado"],
                alternativas=q_info["alternativas"],
                resposta_certa=q_info["resposta_certa"],
                explicacao_fundamentada=q_info["explicacao_fundamentada"],
                dificuldade=q_info["dificuldade"]
            )
            db.add(qb)
    db.commit()
    logger.info("Catálogo de matérias e acervo oficial 100% sincronizados.")

