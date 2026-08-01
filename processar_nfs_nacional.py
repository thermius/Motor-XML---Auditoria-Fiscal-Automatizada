# ------------------------------------------------------------------------------
# Módulo: Motor xml para auditoria fiscal
# Versão: 5.4
# Autor: Pedro Henrique Oliveira da Silva
# Data: 01/06/2026
# Descrição: Automação de análise de documentos fiscais a fim de identificar inconsistências.
# ------------------------------------------------------------------------------

from utilitarios import global_dic_documento, EscreverVerde, EscreverRosa, EscreverVermelho,regex_pedido, regex_placas, regex_pregao
import re
import xml.etree.ElementTree as ET
from datetime import datetime

#NFS Nacional
buscar_numero_nacional			= "./ns:infNFSe/ns:identNFSe/ns:nNFSe"
buscar_chave_nacional			= "./ns:infNFSe"
buscar_data_emissao_nacional	= "./ns:infNFSe/ns:identNFSe/ns:dhEmit"
buscar_valor_liquido_nacional 	= "./ns:infNFSe/ns:valores/ns:vLiq"
buscar_cnpj_emissor_nacional 	= "./ns:infNFSe/ns:prest/ns:CNPJ"
buscar_razao_emissor_nacional	= "./ns:infNFSe/ns:prest/ns:xNome"
buscar_cnpj_tomador_nacional	= "./ns:infNFSe/ns:tom/ns:CNPJ"
buscar_descricao_nacional		= ".//ns:xDesc"
buscar_informoes_nacional		= ".//ns:infAdic"
buscar_complemento_naciomal		= ".//ns:infCompl"

espaco_nome_nfs_nacional	= { "ns": "http://www.nfse.gov.br/NFSe"}	
conjunto_nfs_analisados		= set ()

#Função que processa os NFS Nacional. Recebe como argumento o node xml. Retorna 0 se sucesso e -1 se erro, -2 se o CTE for repetido e global_dic_documento se sucesso
def ProcessarNFSNacional (arg_node):

	#verifica o tipo
	if type (arg_node) != ET.Element:
		raise TypeError(' [ ERROR ] - ProcessarNFSNacional(): objeto invalido recebido como argumento')
		
	#busca pelos elementos da nota fiscal
	chave_nfs 		= arg_node.find (buscar_chave_nacional,		global_espaco_nome_nfs_nacional)
	valor_nfs 		= arg_node.find (buscar_valor_liquido_nacional,	global_espaco_nome_nfs_nacional)
	prestador_nfs 		= arg_node.find (buscar_razao_emissor_nacional, global_espaco_nome_nfs_nacional)
	data_emissao 		= arg_node.find (buscar_data_emissao_nacional, 	global_espaco_nome_nfs_nacional)
	numero_nfs		= arg_node.find (buscar_numero_nacional, 	global_espaco_nome_nfs_nacional)
	cnpj_emissor 		= arg_node.find (buscar_cnpj_emissor_nacional, 	global_espaco_nome_nfs_nacional)
	tomador			= arg_node.find (buscar_cnpj_tomador_nacional,	global_espaco_nome_nfs_nacional)

	#verfifica se todos os elementos foram encontrados
	if (	chave_nfs 	is None	or
		valor_nfs 	is None or valor_nfs.text 	is None or
		prestador_nfs 	is None or prestador_nfs.text 	is None or
		data_emissao 	is None or data_emissao.text 	is None or
		numero_nfs 	is None or numero_nfs.text 	is None or
		cnpj_emissor 	is None or cnpj_emissor.text 	is None or
		tomador 	is None or tomador.text 	is None ):
		print(EscreverVermelho(f'[ ERROR ] - ProcessarNFSNacional(): NFS invalidado por falta de elemento. Inserindo na lista de invalidos e continuando'))
		return -1
		
	#obtema chave da nfs no atributo id e valida
	chave_atual = chave_nfs.get ('Id','').replace('NFS','').strip()
	if len (chave_atual) != 50 or not chave_atual.isdigit():
		print(EscreverVermelho(f"[ ERROR ] - ProcessarNFSNacional(): NFS invalidado por chave corrompida"))
		return -1
	#pega a data 
	try:
		data_atual  = datetime.fromisoformat(data_emissao.text.strip()).date()
	except:
		print(EscreverVermelho(f'[ ERROR ] - ProcessarNFS(): NFS invalidado por falta de elemento. Inserindo na lista de invalidos e continuando'))
		return -1
		
	#obtem os principais dados da nfs
	valor_atual 		= valor_nfs.text.strip()
	prestador_atual 	= prestador_nfs.text.strip()
	numero_nfs_atual	= numero_nfs.text.strip()
	cnpj_emissor_atual	= cnpj_emissor.text.strip()
	tomador_atual		= tomador.text.strip()	
			
	#invalida se as informaçoes forem em branco
	if  "" in [valor_atual, chave_atual, prestador_atual, numero_nfs_atual, tomador_atual, cnpj_emissor_atual]:
		print(EscreverVermelho(f'[ ERROR ] - ProcessarNFS(): NFS invalidado por informações em branco. Inserindo na lista de invalidos e continuando'))
		return -1
		
	#ingnora caso ja tenha sido analisado
	if chave_atual  in conjunto_nfs_analisados:
		return -2
	else:
		conjunto_nfs_analisados.add(chave_atual)
	
	#preenche o dicionario
	global_dic_documento ['chave_documento']	= chave_atual
	global_dic_documento ['razao_social'] 		= prestador_atual
	global_dic_documento ['cnpj_emissor'] 		= cnpj_emissor_atual
	global_dic_documento ['numero_documento']	= numero_nfs_atual
	global_dic_documento ['tipo_documento'] 	= 'NFS Nacional'
	global_dic_documento ['valor_documento']	= valor_atual
	global_dic_documento ['data_emissao']		= data_atual
	try:
		global_dic_documento ['tomador_servico']	= ('TM' + tomador_atual[10:12])
	except:
		global_dic_documento ['tomador_servico']	= "Erro de indexação ao extrair CNPJ"
		
		
	#encontra todos os elementos da tag observações em qualquer profundidade
	encontrados_descricao 	= arg_node.findall(buscar_descricao_nacional,		espaco_nome_nfs_nacional)
	#encontra todos os elementos da tag ndoc em qualquer profundidade
	encontrados_informacoes = arg_node.findall(buscar_informoes_nacional,		espaco_nome_nfs_nacional)
	#encontra todos os elementos da tag infAdFisco em qualquer profundidade
	encontrados_complemento = arg_node.findall(buscar_complemento_naciomal,		espaco_nome_nfs_nacional)
	
	#armazena todos os pedidos encontrados
	match = list ()
	
	#coloca todas as buscas em uma lista
	lista_pedidos = [*encontrados_descricao, *encontrados_informacoes, *encontrados_complemento]
	
	#busca pelo pedido
	for i in lista_pedidos:
		if i.text:
			match.extend (re.findall(regex_pedido,i.text))
			
	lista_limpa = list (set(match))
	#se não encotrar pedido, tenta encontrar placas ou  pregão
	if len (lista_limpa) == 0:
	
		global_dic_documento ['status_pedido'] = 's/pedido'
		#se não encontrar pedido, busca pelos pregões ou placas
		lista_pregao = list()
		#busca pelo numero do pregão na lista
		for i in lista_pedidos:
			if i.text:
				lista_pregao.extend (re.findall(regex_pregao,i.text))
				lista_pregao.extend (re.findall(regex_placas,i.text))
				
		#cria uma lista de pregoes/placas sem repetição
		lista_limpa_pregoes = list (set(lista_pregao))

		#se não encontrar nenhum pregão, adiciona a mensagem de não encontrado na lista
		if len (lista_limpa_pregoes) == 0:
			global_dic_documento ['informacoes_extras'] = ('nenhum pregão/placa encontrado')
			return global_dic_documento
			
		#se encontrar, intera sobre a lista e adciona as informações extras encontradas 
		else:
			global_dic_documento ['informacoes_extras'] += (", ".join(lista_limpa_pregoes))
			return global_dic_documento
	
	#muda o status para com pedido ou com multiplos pedidos	
	elif len (lista_limpa) > 1:	
		global_dic_documento ['status_pedido'] 	= 'm/pedido'
	elif len (lista_limpa) == 1:
		global_dic_documento ['status_pedido'] 	= 'c/pedido'

	#insere os pedidos encontrados e retorna
	global_dic_documento ['pedido'] 	= ", ".join(lista_limpa)
	return global_dic_documento
	
