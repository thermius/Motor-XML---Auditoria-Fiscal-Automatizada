# ------------------------------------------------------------------------------
# Módulo: Motor xml para auditoria fiscal
# Versão: 5.6
# Autor: Pedro Henrique Oliveira da Silva
# Data: 01/06/2026
# Descrição: Automação de análise de documentos fiscais a fim de identificar inconsistências.
# ------------------------------------------------------------------------------

VERSAO = 6.0
import xml.etree.ElementTree as ET
import pandas as pd
from decimal 					import Decimal, ROUND_HALF_UP
from pathlib 					import Path
from utilitarios 				import EscreverVermelho, EscreverVerde, EscreverRosa, global_dic_documento
from processar_cte 				import ProcessarCTE
from processar_nfs_ginfes 		import ProcessarNFSGinfes
from processar_nfs_nacional 	import ProcessarNFSNacional
from processar_nfe				import ProcessarNFe
from fpdf 						import FPDF
from fpdf.enums 				import XPos, YPos
import datetime
import os
import getpass
caminho 					= "./analise"					#caminho para os xml
p = Path(caminho)

conjunto_invalidos_cte 		= set  ()
conjunto_invalidos_nfs 		= set  ()
conjunto_desconhecido_nfs	= list ()			




#nome das colunas
CNPJ_EMISSOR 				= 'CNPJ do emissor'
CHAVE_DOCUMENTO 			= 'Chave do documento'
RAZAO_SOCIAL				= 'Razão social'
NUMERO_DOCUMENTO			= 'N° Documento'
DATA_EMISSAO				= 'Data de emissão'
VALOR_DOCUMENTO				= 'Valor do documento'
TIPO_DOCUMENTO				= 'Tipo de documento'
STATUS						= 'Status de pedido'
PEDIDO						= 'Pedido de compra'
INFORMACOES					= 'Placas/Pregões'
TOMADOR_SERVICO				= 'Tomador de serviço'
ORIGEM						= 'Origem'
DESTINO						= 'Destino'
PROVAVEL_SETOR				= 'Provavel S.Responsavel'
PALAVRA_CHAVE				= 'Palavras chaves'
METODO_ANALISE				= 'Metodo de analise'


#tabela panda
tabela_analise = pd.DataFrame  (columns = [
	
	CNPJ_EMISSOR			,
	CHAVE_DOCUMENTO			,
	RAZAO_SOCIAL			,
	NUMERO_DOCUMENTO		,
	DATA_EMISSAO			,
	VALOR_DOCUMENTO			,
	TIPO_DOCUMENTO			,
	METODO_ANALISE			,
	STATUS					,
	PEDIDO					,
	TOMADOR_SERVICO			,
	ORIGEM					,
	DESTINO					,
	PALAVRA_CHAVE			,
	PROVAVEL_SETOR			,
	INFORMACOES

	]
)

total_analisados 	= 0
linha_atual 		= -1
documento   		= {'doc':''}
contagem_setores 	= {}

#loop que intera sobre os arquivos do diretorio
for arquivo in p.iterdir():
	try:
		with arquivo.open(mode='r') as arquivo_xml:

			for chave in global_dic_documento:
				global_dic_documento[chave] = ''

			total_analisados += 1
			nfs = 0
			#limpa o documento anterior
			documento['doc'] = ''
			desconhecido = 0
			retorno = None

			#ler o xml
			conteudo_xml = arquivo_xml.read()	
			#faz o parsing
			raiz = ET.fromstring(conteudo_xml)
			# pega a tag pura ou quebra em '}' se houver espaço de nome
			tag_pura = raiz.tag.split("}")[1] if "}" in raiz.tag else raiz.tag
			# se CTE
			if tag_pura == 'cteProc':
				retorno = ProcessarCTE (raiz)
				if retorno == -1:
					conjunto_invalidos_cte.add (arquivo.name)
					continue
				elif retorno == -2:
					continue
			# se NFS
			elif tag_pura.upper() in ['NFE']:
				nfs = 1
				retorno = ProcessarNFe (raiz)
				#processa o retorno
				if retorno == -1:
					conjunto_invalidos_nfs.add (arquivo.name)
					continue
				elif retorno == -2:
					continue
			else:
				desconhecido = 1
			#se nfs desconhecida
			if desconhecido:
				print (EscreverRosa(' [ NOTA ] - main(): NFS desconhecida encontrada. Adicinando a lista de desconhecidos e continuando'))
				conjunto_desconhecido_nfs.append ((arquivo.name,raiz.tag))
				continue
			#garante não acessar retorno se não for dicionario
			if not isinstance(retorno, dict):
				continue		

			#insere as informações iniciais na tabela
			tabela_analise.loc [linha_atual , CNPJ_EMISSOR] 			= retorno 			['cnpj_emissor']
			tabela_analise.loc [linha_atual , CHAVE_DOCUMENTO]   		= retorno 			['chave_documento']
			tabela_analise.loc [linha_atual , RAZAO_SOCIAL] 			= retorno 			['razao_social']
			tabela_analise.loc [linha_atual , NUMERO_DOCUMENTO] 		= retorno 			['numero_documento']
			tabela_analise.loc [linha_atual , DATA_EMISSAO] 			= retorno			['data_emissao']
			tabela_analise.loc [linha_atual , VALOR_DOCUMENTO] 			= float (retorno 	['valor_documento'])
			tabela_analise.loc [linha_atual , TIPO_DOCUMENTO] 			= retorno 			['tipo_documento']
			tabela_analise.loc [linha_atual , STATUS	] 				= retorno 			['status_pedido']
			tabela_analise.loc [linha_atual , PEDIDO	] 				= retorno 			['pedido']
			tabela_analise.loc [linha_atual , TOMADOR_SERVICO] 			= retorno 			['tomador_servico']
			tabela_analise.loc [linha_atual , ORIGEM] 					= retorno 			['origem']
			tabela_analise.loc [linha_atual , DESTINO] 					= retorno 			['destino']
			tabela_analise.loc [linha_atual , PROVAVEL_SETOR	] 		= retorno			['p_setor_responsavel']
			tabela_analise.loc [linha_atual , PALAVRA_CHAVE	] 			= retorno			['palavras_chaves']
			tabela_analise.loc [linha_atual , METODO_ANALISE	] 		= retorno			['metodo_analise']
			tabela_analise.loc [linha_atual , INFORMACOES	] 			= retorno			['informacoes_extras']

			#aponta para a proxima linha da planilha
			linha_atual += 1

			# Pega o setor Responsavel
			setor = retorno.get('p_setor_responsavel', 'Não identicado')
			
			# tenta acessar o setor, se não existir, cria e devolve 0 para ser somado com + 1 e se inserido como valor do dicinario
			contagem_setores[setor] = contagem_setores.get(setor, 0) + 1
	except Exception as e:
		print(f"{EscreverVermelho(f'[ ERROR ] - Ouve um disparo de excessão durante a analise de: {arquivo} : {e}')}")
		exit()
		

try:	
	print(EscreverRosa('[ ENTRADA ] - main(): Informe o nome da saida: '), end='')
	nome = input ('')
	nome_arquivo = 'analise_' + nome +'.xlsx'
	print(EscreverVerde(f"Salvando como {nome_arquivo}"))
	tabela_analise.to_excel(nome_arquivo, index=False)

	# --- GERANDO O PDF COM A LIB FPDF. Gerado por IA
	nome_pdf = 'analise_' + nome + '.pdf'
	print(EscreverVerde(f"Gerando relatório formalizado em {nome_pdf}..."))

	# Captura de dados sistêmicos
	data_hora_atual = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
	host_sistema = os.uname().nodename if hasattr(os, 'uname') else 'localhost'
	id_execucao = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

	pdf = FPDF()
	pdf.add_page()
	pdf.set_font("Helvetica", style="B", size=12)

	# --- CABEÇALHO SITEMÁTICO ---
	pdf.cell(200, 10, text="==========================================================", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
	pdf.cell(200, 10, text=f"RELATORIO DA ANALISE REALIZADA VIA MOTOR XML - v {VERSAO}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
	pdf.cell(200, 10, text="==========================================================", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

	# Informações de Auditoria Sistêmica (A poluição corporativa perfeita)
	pdf.set_font("Helvetica", style="B", size=9)
	pdf.cell(200, 5, text=f"Data e Hora do processamento: {data_hora_atual}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.cell(200, 5, text=f"#{id_execucao}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.cell(200, 5, text="--------------------------------------------------------------------------------------------------------", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.ln(5)

	# Voltar para o tamanho normal do texto
	pdf.set_font("Helvetica", style="B", size=12)

	pdf.cell(200, 10, text="1. RESUMO DE EXECUÇÃO DO LOTE:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	# Dica: o fpdf2 não renderiza bem o caractere '\t' diretamente. Usei 8 espaços para simular o tab
	pdf.cell(200, 8, text=f"        Total de documentos mapeados: {total_analisados}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.cell(200, 8, text=f"        Documentos processados com sucesso: {len(tabela_analise)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.ln(5)

	pdf.cell(200, 10, text="2. QUANTIDADE DE INCONSISTÊNCIAS POR SETOR RESPONSÁVEL:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	for setor, qtd in contagem_setores.items():
		pdf.cell(200, 8, text=f"        Setor [{setor}]: {qtd} documento(s)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.ln(5)

	pdf.cell(200, 10, text="3. DIAGNÓSTICO DE DOCUMENTOS INVÁLIDOS / CORROMPIDOS:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.cell(200, 8, text=f"        CT-es inválidos: {len(conjunto_invalidos_cte)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.cell(200, 8, text=f"        NF-es/NFS-es inválidas: {len(conjunto_invalidos_nfs)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.cell(200, 8, text=f"        Estruturas XML desconhecidas: {len(conjunto_desconhecido_nfs)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
	pdf.ln(10)

	pdf.cell(200, 10, text="----------------------------------------------------------", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
	pdf.cell(200, 10, text=f"Relatório automático gerado pelo Motor XML v {VERSAO}.", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

	pdf.output(nome_pdf)
	print(EscreverVerde(f"PDF {nome_pdf} criado com sucesso!"))

except Exception as e:
	print (EscreverVermelho ('[ ERROR ] - Ouve um erro ao salvar:'), e)
	
#exibe os documentos desconhecidos e invalidos
print (EscreverRosa(f'[ NOTA ] - main(): Conjunto de NFS deconhecido: {len (conjunto_desconhecido_nfs)}'))
for i in conjunto_desconhecido_nfs:
	print(EscreverVermelho(i))

print (EscreverRosa(f'[ NOTA ] - main(): Conjunto de CTEs invalidos: {len (conjunto_invalidos_cte)}'))
for i in conjunto_invalidos_cte:
	print(EscreverVermelho(i))

print (EscreverRosa(f'[ NOTA ] - main(): Conjunto de NFS invalidas: {len (conjunto_invalidos_nfs)}'))
for i in conjunto_invalidos_nfs:
	print(EscreverVermelho(i))
	

