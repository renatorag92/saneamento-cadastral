# 🏛️ Saneamento Cadastral Imobiliário - Parelhas/RN

Pipeline de saneamento, vinculação e enriquecimento do cadastro imobiliário municipal, conforme Manual Operacional.

## 📋 Etapas

| Etapa | Script | Descrição |
| :--- | :--- | :--- |
| 1 | `main_consolidacao_v2.py` | Vincula imóveis (Pesquisa de Campo × IPTU) |
| 2 | `main_enriquecimento_saude.py` | Enriquece com dados da Saúde (CPF, telefone, nascimento) |
| 3 | `main_consolidacao_final.py` | Gera base final limpa para entrega |

## 🚀 Como usar

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install pandas fuzzywuzzy python-Levenshtein unidecode openpyxl xlrd

# 3. Colocar as bases na pasta bases_brutas/
#    - pesquisa_campo.xls
#    - cadastro_iptu.xlsx
#    - base_saude_unificada.xlsx

# 4. Executar o pipeline
python main_consolidacao_v2.py
python main_enriquecimento_saude.py
python main_consolidacao_final.py
