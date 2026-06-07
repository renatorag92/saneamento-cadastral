# config.py
# ==============================================
# CONFIGURAÇÕES DO SANEAMENTO - PARELHAS/RN
# ==============================================

# Thresholds de confiança
ALTA_CONFIANCA = 90
MEDIA_CONFIANCA = 70

# Pesos para scoring probabilístico
PESOS = {
    'cpf_cnpj_exato': 100,
    'nome_exato': 80,
    'nome_similar': 50,
    'endereco_exato': 70,
    'endereco_similar': 40,
    'bairro_igual': 30,
    'telefone_igual': 40,
    'email_igual': 50,
}

# Status e graus (conforme Manual)
STATUS = ['CONFIRMADO', 'COMPLEMENTADO', 'EM_REVISÃO', 'PENDENTE', 'REJEITADO']
GRAU_CONFIANCA = ['ALTA', 'MEDIA', 'BAIXA']

# ==============================================
# MAPEAMENTO DAS COLUNAS REAIS
# ==============================================

# Pesquisa de Campo
COLUNAS_CAMPO = {
    'id': 'OBJECTID',
    'bairro': 'BAIRRO_DO_IMOVEL',
    'logradouro': 'LOGRADOURO_DO_IMOVEL_AJUSTADO',  # Usar o AJUSTADO!
    'logradouro_original': 'LOGRADOURO_DO_IMOVEL',
    'numero': 'NUMERO_DO_IMOVEL',
    'cpf_cnpj': 'CPF_CNPJ__DO_PROPRIETARIO',
    'nome': 'NOME_DO_PROPRIETARIO',
    'telefone': 'TELEFONE_DO_PROPRIETARIO',
    'email': 'EMAIL_DO_PROPRIETARIO',
    'tipologia': 'TIPOLOGIA_DO_IMOVEL',
    'complemento': 'COMPLEMENTO_DO_IMOVEL',
    'foto': 'FOTO',
    'pavimentos': 'QUANTIDADE_DE_PAVIMENTOS',
}

# Base IPTU
COLUNAS_IPTU = {
    'inscricao': 'Inscriao_mobiliaria',
    'proprietario': 'Proprietario',
    'cpf_cnpj': 'CPF/CNPJ',
    'logradouro': 'Logradouro',
    'numero': 'Numero',
    'complemento': 'Complemento',
    'bairro': 'Bairro',
    'cep': 'CEP',
    'endereco_completo': 'EndereçoCompleto',
    'utilizacao': 'Utilizaçao',
    'telefone': 'Proprietrio-Telefone',
    'email': 'Proprietrio-Email',
    'area_terreno': 'AreaTerreno',
    'area_construida': 'AreaConstruÌdaUnidade',
    'valor_venal': 'ValorVenalImovel',
}