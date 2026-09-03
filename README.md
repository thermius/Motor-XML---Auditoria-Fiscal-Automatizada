# Motor-XML---Auditoria-Fiscal-Automatizada
Um motor de análise de documentos fiscais em Python que processa arquivos XML (NFe, CTe, NFS), identifica inconsistências e classifica automaticamente por setor responsável.
# Motor XML - Auditoria Fiscal Automatizada

Um **motor de análise de documentos fiscais** em Python que processa arquivos XML (NFe, CTe, NFS), identifica inconsistências e classifica automaticamente por setor responsável.

## 🎯 O Que É

Sistema completo de **auditoria fiscal automatizada** que:
1. Lê documentos fiscais em formato XML
2. Extrai dados estruturados (CNPJ, datas, valores, etc.)
3. **Classifica automaticamente** por setor responsável usando inteligência em cascata
4. Gera relatórios em **Excel (XLSX)** e **PDF** com análise consolidada

**Por que foi criado:**
Quando sistemas críticos falham, alguém precisa processar manualmente centenas de documentos. Este motor **automatiza totalmente** esse processo, identificando inconsistências e atribuindo responsabilidades.

---

## 🏗️ Arquitetura

### Módulos Especializados

**Cada tipo de documento fiscal tem um processador:**

```
├── processar_nfe.py          # Notas Fiscais Eletrônicas (NFe)
├── processar_cte.py          # Conhecimentos de Transporte Eletrônico (CTe)
├── processar_nfs_nacional.py # Notas Fiscais de Serviço Nacionais
├── processar_nfs_ginfes.py   # Notas Fiscais de Serviço (GINFES)
├── utilitarios.py            # Dicionários, regexes e funções auxiliares
└── main.py                   # Orquestrador principal
```

**Como funciona:**

1. `main.py` itera sobre arquivos XML num diretório
2. Identifica o tipo de documento pela tag raiz
3. Chama o processador específico
4. Processador extrai dados e retorna dicionário
5. Dados são inseridos na tabela de análise
6. Ao final: gera Excel + PDF com relatório

---

## 🧠 Sistema de Classificação em Cascata

A **inteligência do motor** está em classificar documentos por setor responsável. Usa 4 níveis progressivos:

### Nível 1: Busca Específica Prioritária
```python
# Setor com regras muito específicas (ex: logística)
regex_pedido   = r"\b00\d{8}\b"      # Busca números de pedido
regex_pregao   = r"\b[YX]\d{5,6}\b"  # Busca pregões
regex_placas   = r'\b[A-Z]{3}\d{1}[A-Z]{1}\d{2}\b'  # Busca placas
```

**Resultado:** Se encontra um padrão muito específico do setor → classifica direto

---

### Nível 2: Busca Direta por Prestador
```python
global_dic_busca_direta = {
    "SETOR X": ["SETOR Y"],  # Se prestador = SETOR X → classifica como SETOR Y
}
```

**Como funciona:**
- Mantém um mapa de prestadores conhecidos por cada setor
- Se a Razão Social do documento bate com um prestador conhecido → atribui aquele setor
- **Vantagem:** zero processamento, lookup direto

**Exemplo real:**
```python
global_dic_busca_direta = {
    "LogisticaXYZ": ["Logística"],
    "XP Investimentos": ["Financeiro", "Investimentos"],
    "Softtech Solutions": ["TI", "Sistemas"]
}
```

---

### Nível 3: Busca por Palavras-Chave (Regex)
```python
global_regex_setores = {
    "Logística": r"\b(frota|ve[iíì]culo|placa|transporte)\b",
    "Financeiro": r"\b(nota|fatura|boleto|pagamento)\b",
    "TI": r"\b(software|licen[cç]a|suporte t[eéè]cnico)\b"
}
```

**Como funciona:**
- Se nível 1 e 2 falharem, busca palavras-chave na discriminação/descrição
- Usa regex com suporte a acentuação e variações de digitação
- **Permite múltiplos matches** — um documento pode ser atribuído a vários setores
- Registra a palavra-chave que causou o match (rastreabilidade)

**Exemplo de processamento:**
```
Documento: "Serviço de reparo de frota - 5 veículos"
   ↓
Teste nível 1: (busca específica) ✗ Não encontrou
   ↓
Teste nível 2: (prestador conhecido) ✗ Não encontrou
   ↓
Teste nível 3: Regex Logística → casa com "frota" e "veículos" ✓
   ↓
Resultado: Setor = "Logística", Palavra-chave = "frota; veículos"
```

---

### Nível 4: Fallback — "Outras Áreas"
Se nenhum nível anterior encontrar um match → classifica como **"Outras Áreas"**

**Vantagem:** nada fica sem classificação, facilitando análise manual posterior

---

## 📊 Estrutura de Dados

### Dicionário de Documento (retornado por cada processador)

```python
global_dic_documento = {
    "tomador_servico": "",           # Quem contratou o serviço
    "razao_social": "",              # Nome da empresa emitente
    "cnpj_emissor": "",              # CNPJ de quem emitiu
    "chave_documento": "",           # Identificador único do documento
    "data_emissao": "",              # Data de emissão
    "numero_documento": "",          # Número sequencial
    "valor_documento": "",           # Valor em R$
    "status_pedido": "",             # Status (entregue, pendente, etc.)
    "tipo_documento": "",            # NFe, CTe, NFS, etc.
    "pedido": "",                    # Número do pedido de compra
    "informacoes_extras": "",        # Dados adicionais (placas, pregões)
    "origem": "",                    # Local de saída
    "destino": "",                   # Local de chegada
    "p_setor_responsavel": "",       # ← PREENCHIDO PELA CASCATA
    "palavras_chaves": "",           # ← PREENCHIDO PELA CASCATA
    "metodo_analise": ""             # Qual nível da cascata encontrou
}
```

---

## 📋 Saída: Excel + PDF

### Arquivo Excel (XLSX)

Tabela com **uma linha por documento processado:**

| CNPJ do emissor | Chave do documento | Razão social | N° Documento | Data de emissão | Valor | Tipo | Metodo | Status | Setor | Palavra-chave |
|---|---|---|---|---|---|---|---|---|---|---|
| 12.345.678/0001-90 | NFe123456... | Empresa A | 001 | 01/01/2026 | 5000.00 | NFe | Regex | OK | Logística | frota |
| 98.765.432/0001-10 | CTe654321... | Empresa B | 002 | 02/01/2026 | 3000.00 | CTe | Direta | OK | Financeiro | - |

---

### Arquivo PDF

Relatório formalizado com:

**1. RESUMO DE EXECUÇÃO**
- Total de documentos mapeados
- Documentos processados com sucesso
- Documentos com erro

**2. QUANTIDADE DE INCONSISTÊNCIAS POR SETOR**
```
Setor [Logística]: 45 documento(s)
Setor [Financeiro]: 32 documento(s)
Setor [TI]: 8 documento(s)
Setor [Outras Áreas]: 15 documento(s)
```

**3. DIAGNÓSTICO DE DOCUMENTOS INVÁLIDOS**
```
CT-es inválidos: 2
NF-es/NFS-es inválidas: 3
Estruturas XML desconhecidas: 1
```

**4. RASTREABILIDADE**
- Timestamp de execução
- ID único da análise
- Host de execução

---

## 💻 Como Usar

### Pré-requisitos
```bash
pip install pandas fpdf2
```

### Estrutura de Diretórios
```
projeto/
├── main.py
├── utilitarios.py
├── processar_nfe.py
├── processar_cte.py
├── processar_nfs_nacional.py
├── processar_nfs_ginfes.py
└── analise/          ← Coloca arquivos XML aqui
    ├── documento1.xml
    ├── documento2.xml
    └── ...
```

### Executar

```bash
python main.py
```

**Processo:**
1. Pede o nome da análise (ex: `auditoria_janeiro`)
2. Processa todos os XMLs em `./analise/`
3. Gera:
   - `analise_auditoria_janeiro.xlsx`
   - `analise_auditoria_janeiro.pdf`

---

## ⚙️ Configuração

**Tudo é parametrizado em `utilitarios.py`:**

### Adicionar novo prestador conhecido
```python
global_dic_busca_direta = {
    "LogisticaXYZ": ["Logística"],
    "Seu Prestador": ["Seu Setor"]
}
```

### Adicionar novo setor com palavras-chave
```python
global_regex_setores = {
    "Seu Setor": r"\b(palavra1|palavra2|palavra3)\b"
}
```

**Dicas de Regex:**
- `\b` = limite de palavra (não confunde "carro" com "scare")
- `[iíì]` = aceita variações (ignora acentuação)
- Sem grupos de captura `()` — o motor não suporta
- Testa em https://regex101.com antes de adicionar

---

## 🔬 Conceitos Demonstrados

- ✅ Processamento de XML em Python (`xml.etree`)
- ✅ Manipulação de dados com Pandas
- ✅ Regex avançado com suporte a acentuação e variações
- ✅ Geração de relatórios (Excel + PDF)
- ✅ Arquitetura modular e extensível
- ✅ Sistema de classificação em cascata (fallback progressivo)
- ✅ Tratamento de exceções e validação
- ✅ Rastreabilidade e auditoria
- ✅ Automação de processos repetitivos

---

## 📚 Referências

- **XML em Python:** https://docs.python.org/3/library/xml.etree.elementtree.html
- **Pandas:** https://pandas.pydata.org/
- **FPDF2:** https://py-pdf.github.io/fpdf2/
- **Regex:** https://docs.python.org/3/library/re.html

---

## 🎓 Conhecimentos Demonstrados

- ✅ Python intermediário/avançado
- ✅ Processamento de documentos estruturados
- ✅ Automação de workflows
- ✅ Geração de relatórios profissionais
- ✅ Design de sistemas extensíveis
- ✅ Resolução de problemas em produção
- ✅ Rastreabilidade e conformidade

---

## 📝 Histórico & Versão

- **Versão:** 6.0
- **Autor:** Pedro Henrique Oliveira da Silva
- **Data:** 01/06/2026
- **Descrição:** Automação de análise de documentos fiscais com classificação inteligente por setor

---
## 📄 Licença

Todos os direitos reservados.

Este projeto é disponibilizado exclusivamente para fins de portfólio e demonstração técnica. O código-fonte não pode ser copiado, redistribuído, modificado ou utilizado, integral ou parcialmente, sem autorização prévia e explícita do autor.
