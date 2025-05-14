# Analisador CNP

🔍 Analisador de Bases CNP - Controle Da Base

## Descrição

O Analisador CNP é uma aplicação web desenvolvida em Python utilizando a biblioteca Streamlit. A ferramenta permite a análise e comparação de bases de dados CSV no contexto de solicitações do CNP. O projeto não só sanitiza e limpa os dados, como também identifica duplicatas e realiza análises de qualidade.

## Funcionalidades

- **Carga de Dados**: Permite o upload de duas bases CSV:
  - Base Histórica
  - Base Atual

- **Análise de Qualidade**: Fornece informações sobre:
  - Percentual de campos nulos
  - Tipos de dados em cada coluna
  - Problemas como datas inválidas e valores negativos

- **Análise de Duplicatas**: Identifica e permite visualizar duplicatas com base em:
  - Número de solicitação
  - Tarefa da solicitação
  - Combinação de ambos

- **Comparação Mensal**: Compara as bases mês a mês, destacando solicitações faltantes.

- **Identificação de Novos Meses**: Detecta meses que estão presentes na base atual, mas não na histórica.

## Tecnologias Utilizadas

- Python
- Pandas
- Streamlit
- Openpyxl (para exportação para Excel)

## Como Executar o Projeto

### Pré-requisitos

Certifique-se de que você tem o Python instalado em seu sistema. Recomenda-se usar um ambiente virtual.


