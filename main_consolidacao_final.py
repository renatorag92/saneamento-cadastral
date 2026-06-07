# main_consolidacao_final.py
# ==============================================
# CONSOLIDAÇÃO FINAL - BASE ÚNICA LIMPA
# Junta CONFIRMADOS + REVISADOS (após decisão humana)
# Remove duplicações e colunas de debug
# ==============================================

import pandas as pd
import os
from datetime import datetime

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

# ==============================================
# 1. CARREGAR BASE ENRIQUECIDA
# ==============================================
import glob

# Pega o enriquecimento mais recente
arquivos = sorted(glob.glob('outputs/ENRIQUECIDO_*/BASE_ENRIQUECIDA_COMPLETA.xlsx'))
if not arquivos:
    print("❌ Nenhuma base enriquecida encontrada.")
    exit()

arquivo_entrada = arquivos[-1]
print(f"\n📂 Carregando: {arquivo_entrada}")

df = pd.read_excel(arquivo_entrada)
print(f"   Total de registros: {len(df)}")

# ==============================================
# 2. FILTRAR REGISTROS VÁLIDOS
# ==============================================
print("\n🔍 Filtrando registros válidos...")

# Mantém apenas CONFIRMADOS (automáticos + revisados)
# Se você tiver uma planilha de revisão com decisões, podemos carregá-la aqui
# Por enquanto, mantemos apenas os CONFIRMADOS

df_validos = df[df['STATUS'] == 'CONFIRMADO'].copy()
print(f"   CONFIRMADOS: {len(df_validos)}")

# Se quiser incluir os REVISADOS manualmente, descomente:
# df_revisados = pd.read_excel('PLANILHA_REVISAO_HUMANA.xlsx')
# ids_confirmados = df_revisados[df_revisados['DECISAO'] == 'CONFIRMADO']['OBJECTID'].tolist()
# df_validos = pd.concat([df_validos, df[df['OBJECTID'].isin(ids_confirmados)]])

# ==============================================
# 3. REMOVER DUPLICAÇÕES
# ==============================================
print("\n🧹 Removendo duplicações...")

antes = len(df_validos)

# Prioridade: mantém o registro com MAIS dados preenchidos
df_validos['CAMPOS_PREENCHIDOS'] = df_validos.notna().sum(axis=1)
df_validos = df_validos.sort_values('CAMPOS_PREENCHIDOS', ascending=False)
df_validos = df_validos.drop_duplicates(subset='OBJECTID', keep='first')
df_validos = df_validos.drop(columns=['CAMPOS_PREENCHIDOS'])

depois = len(df_validos)
print(f"   Antes: {antes} | Depois: {depois} | Removidas: {antes - depois}")

# ==============================================
# 4. MONTAR PLANILHA LIMPA
# ==============================================
print("\n📊 Montando planilha limpa para entrega...")

# Colunas que vão para o cliente (sem debug)
colunas_entrega = {
    'OBJECTID': 'ID_IMOVEL',
    'NOME_PESQUISA': 'NOME_PROPRIETARIO',
    'CPF_CNPJ_PESQUISA': 'CPF_CNPJ',
    'ENDERECO_PESQUISA': 'ENDERECO_IMOVEL',
    'BAIRRO_PESQUISA': 'BAIRRO',
    'TELEFONE_PESQUISA': 'TELEFONE',
    'INSCRICAO_IPTU': 'INSCRICAO_IMOBILIARIA',
    'SAUDE_NOME': 'NOME_ATUALIZADO_SAUDE',
    'SAUDE_DATA_NASC': 'DATA_NASCIMENTO',
    'SAUDE_TELEFONE': 'TELEFONE_SAUDE',
    'SAUDE_CARTAO_SUS': 'CARTAO_SUS',
    'SAUDE_STATUS': 'STATUS_SAUDE',
}

# Seleciona e renomeia apenas as colunas que existem
df_entrega = pd.DataFrame()
for col_origem, col_destino in colunas_entrega.items():
    if col_origem in df_validos.columns:
        df_entrega[col_destino] = df_validos[col_origem]

# Formata CPF (xxx.xxx.xxx-xx)
def formatar_cpf(cpf):
    if pd.isna(cpf) or str(cpf) == '':
        return ''
    cpf = str(cpf).replace('.0', '')  # Remove .0 do float
    cpf = cpf.zfill(11)  # Completa com zeros à esquerda
    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}'

if 'CPF_CNPJ' in df_entrega.columns:
    df_entrega['CPF_CNPJ'] = df_entrega['CPF_CNPJ'].apply(formatar_cpf)

# Formata telefone ((XX) XXXXX-XXXX)
def formatar_tel(tel):
    if pd.isna(tel) or str(tel) == '':
        return ''
    tel = str(tel).replace('.0', '')
    if len(tel) == 11:
        return f'({tel[:2]}) {tel[2:7]}-{tel[7:]}'
    elif len(tel) == 10:
        return f'({tel[:2]}) {tel[2:6]}-{tel[6:]}'
    return tel

if 'TELEFONE' in df_entrega.columns:
    df_entrega['TELEFONE'] = df_entrega['TELEFONE'].apply(formatar_tel)
if 'TELEFONE_SAUDE' in df_entrega.columns:
    df_entrega['TELEFONE_SAUDE'] = df_entrega['TELEFONE_SAUDE'].apply(formatar_tel)

# Ordena por ID
if 'ID_IMOVEL' in df_entrega.columns:
    df_entrega = df_entrega.sort_values('ID_IMOVEL')

print(f"   Registros finais: {len(df_entrega)}")
print(f"   Colunas: {list(df_entrega.columns)}")

# ==============================================
# 5. EXPORTAR
# ==============================================
print("\n💾 Exportando...")

# Arquivo principal (pronto para entrega)
df_entrega.to_excel(f'{PASTA_OUTPUT}/CADASTRO_IMOBILIARIO_FINAL.xlsx', index=False)

# Também exporta os que ficaram de fora
df_pendentes = df[df['STATUS'] != 'CONFIRMADO']
df_pendentes.to_excel(f'{PASTA_OUTPUT}/PENDENCIAS_REMANESCENTES.xlsx', index=False)

# Indicadores finais
pd.DataFrame({
    'Indicador': [
        'Total de imóveis na pesquisa',
        'Imóveis na base final (confirmados)',
        'Percentual de aproveitamento',
        'Imóveis enriquecidos pela saúde',
        'Pendências remanescentes',
        'Data de processamento'
    ],
    'Valor': [
        9279,
        len(df_entrega),
        f"{round(len(df_entrega)/9279*100, 1)}%",
        len(df_entrega[df_entrega['STATUS_SAUDE'] == 'ENCONTRADO']) if 'STATUS_SAUDE' in df_entrega.columns else 0,
        len(df_pendentes),
        datetime.now().strftime('%d/%m/%Y %H:%M')
    ]
}).to_excel(f'{PASTA_OUTPUT}/INDICADORES_ENTREGA.xlsx', index=False)

print(f"\n📁 Resultados em: {PASTA_OUTPUT}/")
print("   ✅ CADASTRO_IMOBILIARIO_FINAL.xlsx ← ENTREGAR AO CLIENTE")
print("   ✅ PENDENCIAS_REMANESCENTES.xlsx")
print("   ✅ INDICADORES_ENTREGA.xlsx")
print("\n🎉 Base final consolidada com sucesso!")