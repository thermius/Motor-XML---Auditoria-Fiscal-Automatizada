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
from datetime import date
			
#NFS Ginfes
buscar_numero_nfs 		= "./ns:Nfse/ns:InfNfse/ns:Numero"
buscar_data_emissao_nfs 	= "./ns:Nfse/ns:InfNfse/ns:DataEmissao"
buscar_chave_nfs		= "./ns:Nfse/ns:InfNfse/ns:ChaveAcesso"
buscar_valor_nfs		= "./ns:Nfse/ns:InfNfse/ns:Servico/ns:Valores/ns:ValorLiquidoNfse"
buscar_descricao_nfs		= "./ns:Nfse/ns:InfNfse/ns:Servico/ns:Discriminacao"
buscar_cnpj_emissor_nfs		= "./ns:Nfse/ns:InfNfse/ns:PrestadorServico/ns:IdentificacaoPrestador/ns:Cnpj"
buscar_razao_emissor_nfs	= "./ns:Nfse/ns:InfNfse/ns:PrestadorServico/ns:RazaoSocial"
buscar_cnpj_tomador_nfs		= "./ns:Nfse/ns:InfNfse/ns:TomadorServico/ns:IdentificacaoTomador/ns:CpfCnpj/ns:Cnpj"

espaco_nome_nfs			= { "ns": "http://www.ginfes.com.br/tipos_v03.xsd"}	
conjunto_nfs_analisados		= set ()

#Função que processa os NFS Ginfes.Recebe como argumento o node xml. Retorna 0 se sucesso e -1 se erro, -2 se o CTE for repetido e global_dic_documento se sucesso
def ProcessarNFSGinfes (arg_node):

	#verifica o tipo
	if type (arg_node) != ET.Element:
		raise TypeError(' [ ERROR ] - ProcessarNFSGinfes(): objeto invalido recebido como argumento')
		
	#reseta a cada execução
	for chave in global_dic_documento:
		global_dic_documento[chave] = ''
			
	#busca pelos elementos da nota fiscal
	chave_nfs 		= arg_node.find (buscar_chave_nfs,		espaco_nome_nfs)
	valor_nfs 		= arg_node.find (buscar_valor_nfs,		espaco_nome_nfs)
	prestador_nfs 		= arg_node.find (buscar_razao_emissor_nfs, 	espaco_nome_nfs)
	data_emissao 		= arg_node.find (buscar_data_emissao_nfs, 	espaco_nome_nfs)
	numero_nfs		= arg_node.find (buscar_numero_nfs, 		espaco_nome_nfs)
	cnpj_emissor 		= arg_node.find (buscar_cnpj_emissor_nfs, 	espaco_nome_nfs)
	tomador			= arg_node.find (buscar_cnpj_tomador_nfs,	espaco_nome_nfs)
	descricao		= arg_node.find (buscar_descricao_nfs,		espaco_nome_nfs)
	
	#verfifica se todos os elementos foram encontrados
	if ( 	chave_nfs 	is None or chave_nfs.text 	is None or
		valor_nfs 	is None or valor_nfs.text 	is None or
		prestador_nfs 	is None or prestador_nfs.text 	is None or
		data_emissao 	is None or data_emissao.text 	is None or
		numero_nfs 	is None or numero_nfs.text 	is None or
		cnpj_emissor 	is None or cnpj_emissor.text 	is None or
		tomador 	is None or tomador.text 	is None or 
		descricao	is None or descricao.text	is None):
		print(EscreverVermelho(f'[ ERROR ] - ProcessarNFS(): NFS invalidado por falta de elemento. Inserindo na lista de invalidos e continuando'))
		return -1
		
	#pega a data 
	try:
		data_atual = date.fromisoformat(data_emissao.text.strip().split('T')[0])
	except Exception as e:
		print(EscreverVermelho(f'[ ERROR ] - falha ao extrair data: {e}'))
		data_atual = '[ ERROR ] - falha ao extrair data'	
		
	#obtem os principais dados da nfs
	chave_atual 		= chave_nfs.text.strip()
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
		
	#lista que guarda os pedidos
	match = list()
	#busca o pedido na descrição
	match = re.findall (regex_pedido,	descricao.text)
	lista_limpa_pedido = list(set(match))
	
	#preenche o dicionario
	global_dic_documento ['chave_documento']	= chave_atual
	global_dic_documento ['razao_social'] 		= prestador_atual
	global_dic_documento ['cnpj_emissor'] 		= cnpj_emissor_atual
	global_dic_documento ['numero_documento']	= numero_nfs_atual
	global_dic_documento ['tipo_documento'] 	= 'NFS Ginfes'
	global_dic_documento ['valor_documento']	= valor_atual
	global_dic_documento ['data_emissao']		= data_atual
	try:
		global_dic_documento ['tomador_servico']	= ('LI' + tomador_atual[10:12])
		print (global_dic_documento ['tomador_servico'])
	except:
		global_dic_documento ['tomador_servico']	= "Erro de indexação ao extrair CNPJ"
		
	#se não encontrar pedidos
	if len (lista_limpa_pedido) == 0:
		global_dic_documento ['status_pedido'] 	= 's/pedido'
		lista_pregoes = list()
		
		#busca por todos os pregões e placas
		lista_pregoes.extend (re.findall (regex_placas,	descricao.text))
		lista_pregoes.extend (re.findall (regex_pregao,	descricao.text))
		
		#cria uma lista sem repeticao
		lista_limpa_pregoes = list(set(lista_pregoes))
		
		#se não encontrar nenhuma informação extra
		if len(lista_limpa_pregoes) == 0:
			global_dic_documento ['informacoes_extras'] = ('nenhum pregão/placa encontrado')
			return global_dic_documento
		#se encontrar anexa
		else:	
			global_dic_documento ['informacoes_extras'] += (", ".join(lista_limpa_pregoes))
			return global_dic_documento
			
	#muda o status para com pedido ou com multiplos pedidos
	elif len (lista_limpa_pedido) == 1:
		global_dic_documento ['status_pedido'] 	= 'c/pedido'
	elif len (lista_limpa_pedido) > 1:	
		global_dic_documento ['status_pedido'] 	= 'm/pedido'
		
	#insere os pedidos encontrados e retorna
	global_dic_documento ['pedido'] 	= ", ".join(lista_limpa_pedido)
	return global_dic_documento
