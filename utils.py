# utils.py
import pandas as pd
import re
from unidecode import unidecode
from fuzzywuzzy import fuzz
from datetime import datetime
import config

# ==============================================
# NORMALIZAÇÃO (Etapa 3)
# ==============================================

def normalizar_nome(nome):
    """Converte para MAIÚSCULO sem acentos ou pontuação."""
    if pd.isna(nome):
        return ""
    nome = unidecode(str(nome)).upper()
    nome = re.sub(r'[^A-Z\s]', '', nome)
    nome = re.sub(r'\s+', ' ', nome).strip()
    return nome


def normalizar_documento(doc):
    """
    Remove máscara de CPF ou CNPJ.
    Retorna (documento_limpo, tipo, status)
    tipo = 'CPF', 'CNPJ' ou 'DESCONHECIDO'
    status = 'VALIDO', 'INVALIDO', 'AUSENTE'
    """
    if pd.isna(doc):
        return "", "AUSENTE", "AUSENTE"
    
    doc_limpo = re.sub(r'[^0-9]', '', str(doc))
    
    if len(doc_limpo) == 0:
        return "", "AUSENTE", "AUSENTE"
    elif len(doc_limpo) == 11:
        return doc_limpo, "CPF", "VALIDO"
    elif len(doc_limpo) == 14:
        return doc_limpo, "CNPJ", "VALIDO"
    else:
        return doc_limpo, "DESCONHECIDO", "INVALIDO"


def normalizar_endereco(logradouro, numero, bairro, complemento=""):
    """Padroniza componentes do endereço."""
    def limpar(texto):
        if pd.isna(texto):
            return ""
        texto = unidecode(str(texto)).upper()
        texto = re.sub(r'[^A-Z0-9\s]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    
    return limpar(logradouro), limpar(numero), limpar(bairro), limpar(complemento)


def construir_endereco_canonico(logradouro, numero, bairro):
    """
    Cria string padronizada: 'LOGRADOURO | NUMERO | BAIRRO'
    Exemplo: 'AMARIO BEZERRA DA LUZ | SN | JOSE CLOVIS'
    """
    partes = [logradouro, numero, bairro]
    return " | ".join([p for p in partes if p and p != ''])


def normalizar_telefone(tel):
    """Remove tudo que não for dígito."""
    if pd.isna(tel):
        return ""
    return re.sub(r'[^0-9]', '', str(tel))


def normalizar_email(email):
    """Minúsculo e sem espaços."""
    if pd.isna(email):
        return ""
    return str(email).lower().strip()


# ==============================================
# SCORING DE SIMILARIDADE (Etapa 8)
# ==============================================

def similaridade_nome(nome_a, nome_b):
    """Retorna 0 a 100. Usa token_sort para lidar com ordem trocada."""
    return fuzz.token_sort_ratio(nome_a, nome_b)


def similaridade_endereco(end_a, end_b):
    """Compara endereços canônicos completos."""
    return fuzz.token_sort_ratio(end_a, end_b)


def comparar_documento(doc_a, doc_b):
    """
    Compara CPF/CNPJ.
    Retorna 100 se exatamente igual, 0 caso contrário.
    """
    if doc_a and doc_b and doc_a == doc_b:
        return 100
    return 0


# ==============================================
# CLASSIFICAÇÃO DE CONFIANÇA
# ==============================================

def classificar_confianca(score, tem_documento_igual=False, tem_endereco_exato=False):
    """
    Classifica conforme Seção 7.8.3 do Manual.
    """
    if tem_documento_igual and tem_endereco_exato:
        return "ALTA"
    elif tem_documento_igual or score >= config.ALTA_CONFIANCA:
        return "ALTA"
    elif score >= config.MEDIA_CONFIANCA:
        return "MEDIA"
    else:
        return "BAIXA"


def determinar_status(grau_confianca, conflito=False):
    """Define status operacional."""
    if grau_confianca == "ALTA" and not conflito:
        return "CONFIRMADO"
    elif grau_confianca == "MEDIA":
        return "EM_REVISÃO"
    elif conflito:
        return "EM_REVISÃO"
    else:
        return "PENDENTE"


# ==============================================
# LOG DE RASTREABILIDADE
# ==============================================

def registrar_log(arquivo_log, etapa, mensagem):
    """Adiciona linha ao log."""
    with open(arquivo_log, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] ETAPA {etapa}: {mensagem}\n")