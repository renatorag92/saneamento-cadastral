# main_consolidacao_final.py
# ==============================================
# CONSOLIDAÇÃO FINAL - BASE ÚNICA LIMPA
# Junta CONFIRMADOS + REVISADOS (após decisão humana)
# Remove duplicações e gera lista de campo inteligência por bairro
# ==============================================

import pandas as pd
import os
from datetime import datetime
import glob

# ==============================================
# CONFIGURAÇÃO
# ==============================================
DATA_EXECUCAO = datetime.now().strftime('%Y%m%d_%H%M%S')
PASTA_OUTPUT = f'outputs/BASE_FINAL_{DATA_EXECUCAO}'
os.makedirs(PASTA_OUTPUT, exist_ok=True)

print("=" * 60)
print("🏁 CONSOLIDAÇÃO FINAL - BASE ÚNICA PARA ENTREGA")
print(f"   Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 60)

# Dicionário de renomeio padrão para alinhar as colunas das duas bases
renomeios_padrao = {
    'SAUDE_NOME': 'NOME_SAUDE',
    'SAUDE_CARTAO_SUS': 'CPF_SAUDE',
    'SAUDE_TELEFONE': 'TEL_SAUDE',
    'SAUDE_DATA_NASC': 'DATA_NASC',
    'CPF_CNPJ_PESQUISA': 'CPF_PESQUISA',
    'CPF_CNPJ_IPTU': 'CPF_IPTU',
    'TELEFONE_PESQUISA': 'TEL_PESQUISA',
    'TELEFONE_IPTU': 'TEL_IPTU',
}

# ==============================================
# 1. CARREGAR BASE ENRIQUECIDA E REVISÕES
# ==============================================
arquivos = sorted(glob.glob('outputs/ENRIQUECIDO_*/BASE_ENRIQUECIDA_COMPLETA.xlsx'))
if not arquivos:
    print("❌ Nenhuma base enriquecida encontrada.")
    exit()

arquivo_entrada = arquivos[-1]
print(f"\n📂 Carregando base bruta: {arquivo_entrada}")
df_bruto = pd.read_excel(arquivo_entrada)

# Carrega planilha de revisão humana
planilhas_revisao = sorted(glob.glob('outputs/ENRIQUECIDO_*/PLANILHA_REVISAO_ENRIQUECIDA.xlsx'))
if not planilhas_revisao:
    print("❌ Planilha de revisão manual não encontrada. Execute a revisão humana primeiro.")
    exit()

planilha_revisao = planilhas_revisao[-1]
print(f"📂 Carregando revisões humanas: {planilha_revisao}")
df_revisao_humana = pd.read_excel(planilha_revisao)

# ==============================================
# 2. SEGREGAÇÃO AUTOMÁTICA DAS ESTEIRAS
# ==============================================
print("\n⚡ Processando decisões e unificando dados mestres...")

# --- ESTEIRA A: CONFIRMADOS DIRETOS PELA MÁQUINA ---
df_auto_confirmados = df_bruto[df_bruto['STATUS'] == 'CONFIRMADO'].copy()
# Para os automáticos, o dado final padrão é o coletado na pesquisa de campo
df_auto_confirmados['NOME_FINAL'] = df_auto_confirmados['NOME_PESQUISA']
df_auto_confirmados['CPF_FINAL'] = df_auto_confirmados['CPF_CNPJ_PESQUISA']
df_auto_confirmados['TEL_FINAL'] = df_auto_confirmados['TELEFONE_PESQUISA']
# Alinha o nome das colunas com o padrão da planilha de revisão
df_auto_confirmados = df_auto_confirmados.rename(columns=renomeios_padrao)

# --- ESTEIRA B: CONFIRMADOS PELO REVISOR HUMANO ---
# Puxa diretamente os dados da planilha de revisão (mantém as colunas _FINAL e edições manuais!)
df_humano_confirmados = df_revisao_humana[df_revisao_humana['DECISAO'] == 'CONFIRMADO'].copy()

# UNIFICAÇÃO DA BASE FINAL VÁLIDA
df_validos = pd.concat([df_auto_confirmados, df_humano_confirmados], ignore_index=True)

# --- ESTEIRA C: BACKLOG PARA VISITA DE CAMPO ---
# 1. O que a máquina não deu match (PENDENTE automático)
df_auto_pendentes = df_bruto[df_bruto['STATUS'] == 'PENDENTE'].copy().rename(columns=renomeios_padrao)
df_auto_pendentes['MOTIVO_DA_VISITA'] = 'Sem correspondência automática (Baixa Similaridade)'

# 2. O que o revisor humano rejeitou explicitamente
df_humano_rejeitados = df_revisao_humana[df_revisao_humana['DECISAO'] == 'REJEITADO'].copy()
df_humano_rejeitados['MOTIVO_DA_VISITA'] = 'Cruzamento inválido rejeitado na revisão humana'

# 3. O que o revisor ficou na dúvida e deixou em branco
df_humano_duvidosos = df_revisao_humana[df_revisao_humana['DECISAO'].isna() | (df_revisao_humana['DECISAO'] == '')].copy()
df_humano_duvidosos['MOTIVO_DA_VISITA'] = 'Dúvida na revisão visual (Dados inconsistentes)'

# UNIFICAÇÃO DA LISTA DE CAMPO (Ordenada por Bairro para facilitar a logística de rotas!)
df_visita_campo = pd.concat([df_auto_pendentes, df_humano_rejeitados, df_humano_duvidosos], ignore_index=True)
if 'BAIRRO_PESQUISA' in df_visita_campo.columns:
    df_visita_campo = df_visita_campo.sort_values(by=['BAIRRO_PESQUISA', 'LOGRADOURO_PESQUISA'])

# ==============================================
# 3. REMOVER DUPLICAÇÕES DE SEGURANÇA
# ==============================================
print("\n🧹 Executando faxina final antifraude...")
antes = len(df_validos)
df_validos['CAMPOS_PREENCHIDOS'] = df_validos.notna().sum(axis=1)
df_validos = df_validos.sort_values('CAMPOS_PREENCHIDOS', ascending=False)
df_validos = df_validos.drop_duplicates(subset='OBJECTID', keep='first')
df_validos = df_validos.drop(columns=['CAMPOS_PREENCHIDOS'])
print(f"   Registros limpos na base de entrega: {len(df_validos)} (Removidos {antes - len(df_validos)} conflitos)")

# ==============================================
# 4. MAPEAMENTO LIMPO PARA ENTREGA AO CLIENTE
# ==============================================
print("\n📊 Estruturando layouts finais...")

# Mapeia apontando para as colunas mestres '_FINAL' validadas
colunas_entrega = {
    'OBJECTID': 'ID_IMOVEL',
    'NOME_FINAL': 'NOME_PROPRIETARIO',
    'CPF_FINAL': 'CPF_CNPJ',
    'TEL_FINAL': 'TELEFONE',
    'LOGRADOURO_PESQUISA': 'LOGRADOURO',
    'NUMERO_PESQUISA': 'NUMERO',
    'BAIRRO_PESQUISA': 'BAIRRO',
    'INSCRICAO_IPTU': 'INSCRICAO_IMOBILIARIA',
    'NOME_SAUDE': 'NOME_CADASTRAL_SUS',
    'DATA_NASC': 'DATA_NASCIMENTO',
    'TEL_SAUDE': 'TELEFONE_SAUDE',
    'SAUDE_STATUS': 'STATUS_ENRIQUECIMENTO',
}

df_entrega = pd.DataFrame()
for col_origem, col_destino in colunas_entrega.items():
    if col_origem in df_validos.columns:
        df_entrega[col_destino] = df_validos[col_origem]

# --- FORMATADORES SENSORIAIS (CPF e Telefone) ---
def formatar_cpf(cpf):
    if pd.isna(cpf) or str(cpf).strip() in ['', 'nan', 'None']: return ''
    limpo = ''.join(filter(str.isdigit, str(cpf)))
    if len(limpo) == 11: return f'{limpo[:3]}.{limpo[3:6]}.{limpo[6:9]}-{limpo[9:11]}'
    if len(limpo) == 14: return f'{limpo[:2]}.{limpo[2:5]}.{limpo[5:8]}/{limpo[8:12]}-{limpo[12:]}'
    return limpo

def formatar_tel(tel):
    if pd.isna(tel) or str(tel).strip() in ['', 'nan', 'None']: return ''
    limpo = ''.join(filter(str.isdigit, str(tel)))
    if len(limpo) == 11: return f'({limpo[:2]}) {limpo[2:7]}-{limpo[7:]}'
    if len(limpo) == 10: return f'({limpo[:2]}) {limpo[2:6]}-{limpo[6:]}'
    return limpo

if 'CPF_CNPJ' in df_entrega.columns:
    df_entrega['CPF_CNPJ'] = df_entrega['CPF_CNPJ'].apply(formatar_cpf)
if 'TELEFONE' in df_entrega.columns:
    df_entrega['TELEFONE'] = df_entrega['TELEFONE'].apply(formatar_tel)
if 'TELEFONE_SAUDE' in df_entrega.columns:
    df_entrega['TELEFONE_SAUDE'] = df_entrega['TELEFONE_SAUDE'].apply(formatar_tel)

# ==============================================
# 5. EXPORTAÇÃO DOS PRODUTOS
# ==============================================
print("\n💾 Gravando planilhas finais...")

# 1. Base Pronta para o Cliente
df_entrega.to_excel(f'{PASTA_OUTPUT}/CADASTRO_IMOBILIARIO_FINAL.xlsx', index=False)

# 2. Backlog do Campo (Apenas colunas úteis para o leiturista/fiscal na rua)
colunas_campo_reais = [
    'OBJECTID', 'MOTIVO_DA_VISITA', 'NOME_PESQUISA', 'CPF_PESQUISA', 
    'LOGRADOURO_PESQUISA', 'NUMERO_PESQUISA', 'BAIRRO_PESQUISA', 'TEL_PESQUISA',
    'NOME_IPTU', 'INSCRICAO_IPTU', 'LOGRADOURO_IPTU', 'BAIRRO_IPTU'
]
colunas_campo_exportar = [c for c in colunas_campo_reais if c in df_visita_campo.columns]
df_visita_campo[colunas_campo_exportar].to_excel(f'{PASTA_OUTPUT}/LISTA_VISITA_CAMPO.xlsx', index=False)

# 3. Painel de Controle (Indicadores)
total_geral = len(df_bruto)
pd.DataFrame({
    'Indicador': [
        'Total de Imóveis Processados',
        'Imóveis Saneados com Sucesso (Entrega)',
        'Percentual de Solutividade Cadastral',
        'Imóveis Encaminhados para Revisão de Campo',
        'Data do Fechamento do Lote'
    ],
    'Valor': [
        total_geral,
        len(df_entrega),
        f"{round(len(df_entrega)/total_geral*100, 1)}%",
        len(df_visita_campo),
        datetime.now().strftime('%d/%m/%Y %H:%M')
    ]
}).to_excel(f'{PASTA_OUTPUT}/INDICADORES_FECHAMENTO.xlsx', index=False)

print(f"\n📁 Lote finalizado com sucesso em: {PASTA_OUTPUT}/")
print("   ✅ CADASTRO_IMOBILIARIO_FINAL.xlsx  -> (Base rica e higienizada para entrega)")
print("   ✅ LISTA_VISITA_CAMPO.xlsx          -> (Roteirizada por Bairro com motivos claros)")
print("   ✅ INDICADORES_FECHAMENTO.xlsx      -> (Métricas de desempenho do projeto)")
print("\n🎉 Processo concluído de ponta a ponta!")
