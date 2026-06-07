# main_consolidacao_v2.py
# ==============================================
# CONSOLIDAÇÃO FINAL v2 - PARELHAS/RN
# Melhorias:
#   1. Bloqueio por bairro (reduz tempo em 10x)
#   2. Telefone e email no scoring (+60 pontos)
#   3. Threshold ALTA = 85
# ==============================================

import pandas as pd
import os
from datetime import datetime
from unidecode import unidecode
from fuzzywuzzy import fuzz
import re
import utils

# ==============================================
# CONFIGURAÇÃO
# ==============================================
DATA_EXECUCAO = datetime.now().strftime('%Y%m%d_%H%M%S')
PASTA_OUTPUT = f'outputs/CONSOLIDADO_v2_{DATA_EXECUCAO}'
ARQUIVO_LOG = f'{PASTA_OUTPUT}/log_consolidacao.txt'
os.makedirs(PASTA_OUTPUT, exist_ok=True)

ALTA_CONFIANCA = 85
MEDIA_CONFIANCA = 70

PASTA_BRUTAS = 'bases_brutas'

print("=" * 60)
print("🏁 CONSOLIDAÇÃO FINAL v2 - PARELHAS/RN")
print(f"   Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(f"   Threshold ALTA: {ALTA_CONFIANCA} | MÉDIA: {MEDIA_CONFIANCA}")
print(f"   Bloqueio: BAIRRO | Scoring extra: TELEFONE + EMAIL")
print("=" * 60)

# ==============================================
# 1. CARREGAR E PADRONIZAR
# ==============================================
print("\n📂 Carregando bases...")
df_campo = pd.read_excel(f'{PASTA_BRUTAS}/pesquisa_campo.xls')
df_iptu = pd.read_excel(f'{PASTA_BRUTAS}/cadastro_iptu.xlsx')
print(f"   Pesquisa: {len(df_campo)} | IPTU: {len(df_iptu)}")

import config

def normalizar_nome(nome):
    if pd.isna(nome): return ""
    nome = unidecode(str(nome)).upper()
    nome = re.sub(r'[^A-Z\s]', '', nome)
    return re.sub(r'\s+', ' ', nome).strip()

def normalizar_doc(doc):
    if pd.isna(doc): return "", "AUSENTE", "AUSENTE"
    limpo = re.sub(r'[^0-9]', '', str(doc))
    if len(limpo) == 0: return "", "AUSENTE", "AUSENTE"
    elif len(limpo) == 11: return limpo, "CPF", "VALIDO"
    elif len(limpo) == 14: return limpo, "CNPJ", "VALIDO"
    else: return limpo, "DESCONHECIDO", "INVALIDO"

def limpar(t):
    if pd.isna(t): return ""
    t = unidecode(str(t)).upper()
    t = re.sub(r'[^A-Z0-9\s]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def normalizar_telefone(tel):
    if pd.isna(tel): return ""
    return re.sub(r'[^0-9]', '', str(tel))

def normalizar_email(email):
    if pd.isna(email): return ""
    return str(email).lower().strip()

# Padronizar CAMPO
print("\n🧹 Padronizando...")
df_campo['NOME_PADRAO'] = df_campo[config.COLUNAS_CAMPO['nome']].apply(normalizar_nome)
docs = df_campo[config.COLUNAS_CAMPO['cpf_cnpj']].apply(normalizar_doc)
df_campo['CPF_CNPJ_LIMPO'] = docs.apply(lambda x: x[0])
df_campo['LOGR_PADRAO'] = df_campo[config.COLUNAS_CAMPO['logradouro']].apply(limpar)
df_campo['NUM_PADRAO'] = df_campo[config.COLUNAS_CAMPO['numero']].apply(limpar)
df_campo['BAIRRO_PADRAO'] = df_campo[config.COLUNAS_CAMPO['bairro']].apply(limpar)
df_campo['ENDERECO_CANONICO'] = df_campo.apply(
    lambda r: " | ".join([p for p in [r['LOGR_PADRAO'], r['NUM_PADRAO'], r['BAIRRO_PADRAO']] if p]), axis=1)
df_campo['TELEFONE_PADRAO'] = df_campo[config.COLUNAS_CAMPO['telefone']].apply(normalizar_telefone)
df_campo['EMAIL_PADRAO'] = df_campo[config.COLUNAS_CAMPO['email']].apply(normalizar_email)

# Padronizar IPTU
df_iptu['NOME_PADRAO'] = df_iptu[config.COLUNAS_IPTU['proprietario']].apply(normalizar_nome)
docs = df_iptu[config.COLUNAS_IPTU['cpf_cnpj']].apply(normalizar_doc)
df_iptu['CPF_CNPJ_LIMPO'] = docs.apply(lambda x: x[0])
df_iptu['LOGR_PADRAO'] = df_iptu[config.COLUNAS_IPTU['logradouro']].apply(limpar)
df_iptu['NUM_PADRAO'] = df_iptu[config.COLUNAS_IPTU['numero']].apply(limpar)
df_iptu['BAIRRO_PADRAO'] = df_iptu[config.COLUNAS_IPTU['bairro']].apply(limpar)
df_iptu['ENDERECO_CANONICO'] = df_iptu.apply(
    lambda r: " | ".join([p for p in [r['LOGR_PADRAO'], r['NUM_PADRAO'], r['BAIRRO_PADRAO']] if p]), axis=1)
df_iptu['TELEFONE_PADRAO'] = df_iptu[config.COLUNAS_IPTU['telefone']].apply(normalizar_telefone)
df_iptu['EMAIL_PADRAO'] = df_iptu[config.COLUNAS_IPTU['email']].apply(normalizar_email)
print("   ✅ Padronização concluída")

# ==============================================
# 2. DETERMINÍSTICO (igual antes)
# ==============================================
print("\n🔗 Determinístico...")
resultados_det = []
for idx, row in df_campo.iterrows():
    doc = row['CPF_CNPJ_LIMPO']
    end = row['ENDERECO_CANONICO']
    match = None
    motivo = ""
    
    if doc:
        m = df_iptu[df_iptu['CPF_CNPJ_LIMPO'] == doc]
        if len(m) == 1:
            match = m.iloc[0]
            motivo = 'CPF/CNPJ exato'
    
    if match is None and end:
        m = df_iptu[df_iptu['ENDERECO_CANONICO'] == end]
        if len(m) == 1:
            match = m.iloc[0]
            motivo = 'Endereço canônico exato'
    
    if match is not None:
        resultados_det.append({
            'OBJECTID': row['OBJECTID'],
            'NOME_PESQUISA': row['NOME_PADRAO'],
            'CPF_CNPJ_PESQUISA': doc,
            'ENDERECO_PESQUISA': end,
            'BAIRRO_PESQUISA': row['BAIRRO_PADRAO'],
            'TELEFONE_PESQUISA': row['TELEFONE_PADRAO'],
            'EMAIL_PESQUISA': row['EMAIL_PADRAO'],
            'INSCRICAO_IPTU': match[config.COLUNAS_IPTU['inscricao']],
            'NOME_IPTU': match['NOME_PADRAO'],
            'CPF_CNPJ_IPTU': match['CPF_CNPJ_LIMPO'],
            'ENDERECO_IPTU': match['ENDERECO_CANONICO'],
            'TELEFONE_IPTU': match['TELEFONE_PADRAO'],
            'EMAIL_IPTU': match['EMAIL_PADRAO'],
            'SCORE': 100,
            'METODO': 'DETERMINISTICO',
            'MOTIVO': motivo,
            'GRAU_CONFIANCA': 'ALTA',
            'STATUS': 'CONFIRMADO'
        })

df_det = pd.DataFrame(resultados_det)
print(f"   {len(df_det)} matches determinísticos")

# ==============================================
# 3. PROBABILÍSTICO COM BLOQUEIO + TEL/EMAIL
# ==============================================
print("\n🎲 Probabilístico com bloqueio por bairro...")

ids_det = set(df_det['OBJECTID'].tolist())
df_pendentes = df_campo[~df_campo['OBJECTID'].isin(ids_det)].copy()
print(f"   {len(df_pendentes)} pendentes para análise")

# Agrupa IPTU por bairro para busca rápida
iptu_por_bairro = {}
for bairro in df_iptu['BAIRRO_PADRAO'].unique():
    iptu_por_bairro[bairro] = df_iptu[df_iptu['BAIRRO_PADRAO'] == bairro]
print(f"   {len(iptu_por_bairro)} bairros distintos no IPTU")

def calcular_score_v2(row_campo, row_iptu):
    """
    Scoring melhorado:
    - Nome: até 60 pts
    - Endereço: até 50 pts
    - Bairro: 30 pts (já garantido pelo bloqueio)
    - Número: 20 pts
    - Telefone: 30 pts (NOVO)
    - Email: 30 pts (NOVO)
    Total máximo: 220 pontos
    """
    score = 0
    motivos = []
    
    # 1. Nome (60 pts)
    if row_campo['NOME_PADRAO'] and row_iptu['NOME_PADRAO']:
        ns = fuzz.token_sort_ratio(row_campo['NOME_PADRAO'], row_iptu['NOME_PADRAO'])
        score += (ns / 100) * 60
        if ns >= 90: motivos.append(f"Nome muito similar ({ns}%)")
        elif ns >= 70: motivos.append(f"Nome similar ({ns}%)")
    
    # 2. Endereço (50 pts)
    if row_campo['ENDERECO_CANONICO'] and row_iptu['ENDERECO_CANONICO']:
        es = fuzz.token_sort_ratio(row_campo['ENDERECO_CANONICO'], row_iptu['ENDERECO_CANONICO'])
        score += (es / 100) * 50
        if es >= 80: motivos.append(f"Endereço similar ({es}%)")
    
    # 3. Bairro (30 pts) - já é garantido pelo bloqueio, mas confirmamos
    if row_campo['BAIRRO_PADRAO'] and row_iptu['BAIRRO_PADRAO']:
        if row_campo['BAIRRO_PADRAO'] == row_iptu['BAIRRO_PADRAO']:
            score += 30
            motivos.append("Bairro idêntico")
    
    # 4. Número (20 pts)
    num_p = row_campo['NUM_PADRAO']
    num_i = row_iptu['NUM_PADRAO']
    if num_p and num_i:
        sem_num = ['SN', 'S N', 'SEM NUMERO', '0', '']
        if (num_p in sem_num and num_i in sem_num) or num_p == num_i:
            score += 20
            motivos.append("Número compatível")
    
    # 5. TELEFONE (30 pts) - NOVO
    tel_p = row_campo['TELEFONE_PADRAO']
    tel_i = row_iptu['TELEFONE_PADRAO']
    if tel_p and tel_i and tel_p == tel_i:
        score += 30
        motivos.append("Telefone idêntico")
    
    # 6. EMAIL (30 pts) - NOVO
    email_p = row_campo['EMAIL_PADRAO']
    email_i = row_iptu['EMAIL_PADRAO']
    if email_p and email_i and email_p == email_i:
        score += 30
        motivos.append("Email idêntico")
    
    return round(score, 2), " | ".join(motivos) if motivos else "Baixa similaridade"


# Executa o probabilístico com bloqueio
resultados_prob = []
sem_bairro = 0

for idx, row_campo in df_pendentes.iterrows():
    if idx % 500 == 0:
        print(f"   Processando... {idx}/{len(df_pendentes)}")
    
    bairro = row_campo['BAIRRO_PADRAO']
    
    # 🔥 BLOQUEIO: só compara com IPTUs do mesmo bairro
    if bairro and bairro in iptu_por_bairro:
        candidatos = iptu_por_bairro[bairro]
    else:
        # Se não tem bairro ou bairro não existe no IPTU, compara com todos
        candidatos = df_iptu
        sem_bairro += 1
    
    melhor_score = 0
    melhor_iptu = None
    melhor_motivo = ""
    
    for _, row_iptu in candidatos.iterrows():
        score, motivo = calcular_score_v2(row_campo, row_iptu)
        if score > melhor_score:
            melhor_score = score
            melhor_iptu = row_iptu
            melhor_motivo = motivo
    
    if melhor_score >= ALTA_CONFIANCA:
        grau = 'ALTA'
        status = 'CONFIRMADO'
    elif melhor_score >= MEDIA_CONFIANCA:
        grau = 'MEDIA'
        status = 'EM_REVISÃO'
    else:
        grau = 'BAIXA'
        status = 'PENDENTE'
        melhor_iptu = None
    
    resultados_prob.append({
        'OBJECTID': row_campo['OBJECTID'],
        'NOME_PESQUISA': row_campo['NOME_PADRAO'],
        'CPF_CNPJ_PESQUISA': row_campo['CPF_CNPJ_LIMPO'],
        'ENDERECO_PESQUISA': row_campo['ENDERECO_CANONICO'],
        'BAIRRO_PESQUISA': row_campo['BAIRRO_PADRAO'],
        'TELEFONE_PESQUISA': row_campo['TELEFONE_PADRAO'],
        'EMAIL_PESQUISA': row_campo['EMAIL_PADRAO'],
        'INSCRICAO_IPTU': melhor_iptu[config.COLUNAS_IPTU['inscricao']] if melhor_iptu is not None else '',
        'NOME_IPTU': melhor_iptu['NOME_PADRAO'] if melhor_iptu is not None else '',
        'CPF_CNPJ_IPTU': melhor_iptu['CPF_CNPJ_LIMPO'] if melhor_iptu is not None else '',
        'ENDERECO_IPTU': melhor_iptu['ENDERECO_CANONICO'] if melhor_iptu is not None else '',
        'TELEFONE_IPTU': melhor_iptu['TELEFONE_PADRAO'] if melhor_iptu is not None else '',
        'EMAIL_IPTU': melhor_iptu['EMAIL_PADRAO'] if melhor_iptu is not None else '',
        'SCORE': melhor_score,
        'METODO': 'PROBABILISTICO',
        'MOTIVO': melhor_motivo,
        'GRAU_CONFIANCA': grau,
        'STATUS': status
    })

df_prob = pd.DataFrame(resultados_prob)
print(f"   Probabilístico: {len(df_prob)} analisados")
print(f"   Imóveis sem bairro correspondente: {sem_bairro}")

# ==============================================
# 4. CONSOLIDAR
# ==============================================
print("\n📊 Consolidando...")
df_final = pd.concat([df_det, df_prob], ignore_index=True)

total = len(df_final)
confirmados = len(df_final[df_final['STATUS'] == 'CONFIRMADO'])
em_revisao = len(df_final[df_final['STATUS'] == 'EM_REVISÃO'])
pendentes = len(df_final[df_final['STATUS'] == 'PENDENTE'])

print("\n" + "=" * 60)
print("📊 RESULTADOS FINAIS v2")
print("=" * 60)
print(f"   Total: {total}")
print(f"   ✅ CONFIRMADOS: {confirmados} ({round(confirmados/total*100, 1)}%)")
print(f"   🔍 EM REVISÃO: {em_revisao} ({round(em_revisao/total*100, 1)}%)")
print(f"   ⚠️ PENDENTES: {pendentes} ({round(pendentes/total*100, 1)}%)")

# ==============================================
# 5. EXPORTAR
# ==============================================
print("\n💾 Exportando...")

colunas_finais = [
    'OBJECTID', 'NOME_PESQUISA', 'CPF_CNPJ_PESQUISA', 'ENDERECO_PESQUISA', 'BAIRRO_PESQUISA',
    'TELEFONE_PESQUISA', 'EMAIL_PESQUISA',
    'INSCRICAO_IPTU', 'NOME_IPTU', 'CPF_CNPJ_IPTU', 'ENDERECO_IPTU',
    'TELEFONE_IPTU', 'EMAIL_IPTU',
    'SCORE', 'METODO', 'MOTIVO', 'GRAU_CONFIANCA', 'STATUS'
]

df_final[colunas_finais].to_excel(f'{PASTA_OUTPUT}/BASE_FINAL_COMPLETA.xlsx', index=False)

with pd.ExcelWriter(f'{PASTA_OUTPUT}/BASE_FINAL_CONSOLIDADA.xlsx') as writer:
    df_final[df_final['STATUS'] == 'CONFIRMADO'][colunas_finais].to_excel(writer, sheet_name='CONFIRMADOS', index=False)
    df_final[df_final['STATUS'] == 'EM_REVISÃO'][colunas_finais].to_excel(writer, sheet_name='EM_REVISAO', index=False)
    df_final[df_final['STATUS'] == 'PENDENTE'][colunas_finais].to_excel(writer, sheet_name='PENDENTES', index=False)

# Indicadores
indicadores = {
    'Indicador': [
        'Total de imóveis',
        'CONFIRMADOS (automático)',
        'EM REVISÃO (média confiança)',
        'PENDENTES (sem match)',
        'Threshold ALTA',
        'Threshold MÉDIA',
        'Bloqueio por bairro',
        'Scoring extra (tel/email)',
        'Data'
    ],
    'Valor': [
        total,
        f"{confirmados} ({round(confirmados/total*100, 1)}%)",
        f"{em_revisao} ({round(em_revisao/total*100, 1)}%)",
        f"{pendentes} ({round(pendentes/total*100, 1)}%)",
        ALTA_CONFIANCA,
        MEDIA_CONFIANCA,
        'Sim',
        'Sim (+60 pts)',
        datetime.now().strftime('%d/%m/%Y %H:%M')
    ]
}
pd.DataFrame(indicadores).to_excel(f'{PASTA_OUTPUT}/INDICADORES_FINAIS.xlsx', index=False)

# Planilha de revisão
df_revisao = df_final[df_final['STATUS'] == 'EM_REVISÃO'].copy()
df_revisao[['REVISOR', 'DECISAO', 'OBSERVACAO']] = '', '', ''
colunas_revisao = [c for c in colunas_finais if c not in ['CPF_CNPJ_PESQUISA', 'CPF_CNPJ_IPTU']] + ['REVISOR', 'DECISAO', 'OBSERVACAO']
colunas_revisao = [c for c in colunas_revisao if c in df_revisao.columns]
df_revisao[colunas_revisao].to_excel(f'{PASTA_OUTPUT}/PLANILHA_REVISAO_MANUAL.xlsx', index=False)

utils.registrar_log(ARQUIVO_LOG, 12, f"v2: {confirmados} conf, {em_revisao} rev, {pendentes} pend")

print(f"\n📁 Resultados em: {PASTA_OUTPUT}/")
print("   ✅ BASE_FINAL_COMPLETA.xlsx")
print("   ✅ BASE_FINAL_CONSOLIDADA.xlsx")
print("   ✅ INDICADORES_FINAIS.xlsx")
print("   ✅ PLANILHA_REVISAO_MANUAL.xlsx")
print("\n🎉 v2 concluída!")
