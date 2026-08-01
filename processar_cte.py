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

#CTE
buscar_evento 				= ".//ns:tpEvento"				
buscar_status 				= "./ns:protCTe/ns:infProt/ns:cStat"		
buscar_data_emissao 		= "./ns:CTe/ns:infCte/ns:ide/ns:dhEmi"		
buscar_valor 				= "./ns:CTe/ns:infCte/ns:vPrest/ns:vTPrest"	
buscar_prestador 			= "./ns:CTe/ns:infCte/ns:emit/ns:xNome"		
buscar_cnpj_prestador 	= "./ns:CTe/ns:infCte/ns:emit/ns:CNPJ"	
buscar_numero_cte 		= "./ns:CTe/ns:infCte/ns:ide/ns:nCT"		
buscar_chave 				= "./ns:protCTe/ns:infProt/ns:chCTe"		
buscar_obs 				= ".//ns:xObs"					
buscar_ndoc 				= ".//ns:nDoc"					
buscar_nfisco 				= ".//ns:infAdFisco"			
buscar_pred 				= ".//ns:proPred"


buscar_origem_cidade		= "./ns:CTe/ns:infCte/ns:ide/ns:xMunIni"
buscar_origem_uf		= "./ns:CTe/ns:infCte/ns:ide/ns:UFIni"
buscar_destino_cidade		= "./ns:CTe/ns:infCte/ns:ide/ns:xMunFim"
buscar_destino_uf		= "./ns:CTe/ns:infCte/ns:ide/ns:UFFim"

espaco_nome_cte			= { "ns":"http://www.portalfiscal.inf.br/cte" }
conjunto_cte_analisados 	= set()

#dicionario que guarda o tomador encontrado para fins de economia de memoria e redução de grab colector
dic_tomador = {
"tomador": ""
}

#Função que processa os CTEs. Recebe como argumento o node xml. Retorna 0 se sucesso e -1 se erro, -2 se o CTE for repetido, global_dic_documento se sucesso
def ProcessarCTE (arg_node):

	#verifica o tipo
	if type (arg_node) != ET.Element:
		raise TypeError(' [ ERROR ] - ProcessarCTE(): objeto invalido recebido como argumento')
		
	#busca pelo evento de cancelamento e se cancelado, retorna -1
	cancelamentos = arg_node.findall(buscar_evento, espaco_nome_cte)
	for i in cancelamentos:
		if  i.text and i.text.strip() == "110111":
			print  (EscreverRosa ('[ NOTA ] - ProcessarCTE(): CTE cancelado. Retornando -1'))
			return -1

	#verifica se é autorizado pelo sefaz e se não autorizado retorna -1
	validacao_cte = arg_node.find(buscar_status, espaco_nome_cte)
	if validacao_cte is None or not validacao_cte.text or validacao_cte.text.strip() != "100":
		print(EscreverRosa('[ NOTA ] - ProcessarCTE(): CTE não autorizado.  Retornando -1'))
		return -1

	#busca pelos elementos do cte
	chave_cte 			= arg_node.find (buscar_chave,			espaco_nome_cte)
	valor_cte 			= arg_node.find (buscar_valor,			espaco_nome_cte)
	prestador_cte 		= arg_node.find (buscar_prestador, 		espaco_nome_cte)
	data_emissao  		= arg_node.find (buscar_data_emissao, 	espaco_nome_cte)
	numero_cte 			= arg_node.find (buscar_numero_cte, 	espaco_nome_cte)
	cnpj_emissor 		= arg_node.find (buscar_cnpj_prestador, 	espaco_nome_cte)
	
	elemento_origem			= arg_node.find (buscar_origem_cidade,	espaco_nome_cte)
	elemento_uf_origem		= arg_node.find (buscar_origem_uf,	espaco_nome_cte)
	elemento_destino		= arg_node.find (buscar_destino_cidade,	espaco_nome_cte)
	elemento_uf_destino		= arg_node.find (buscar_destino_uf,	espaco_nome_cte)


	#condições para que um cte seja invalido: ausencia de valor, ausencia de chave, ausencia de nome do prestador e data de emissão, falta de cnpj tomador e emissor
	if ( 	numero_cte 		is None or numero_cte.text 	is None or
		valor_cte 		is None or valor_cte.text 		is None or
		chave_cte 		is None or chave_cte.text 	is None or
		prestador_cte 	is None or prestador_cte.text	is None or
		data_emissao 	is None or data_emissao.text	is None or
		cnpj_emissor 	is None or cnpj_emissor.text 	is None ):
		print(EscreverVermelho(f'[ ERROR ] - ProcessarCTE(): CTE invalidado por falta de elemento. Inserindo na lista de invalidos e continuando'))
		return -1

	#obtem os principais dados do cte
	chave_atual 			= chave_cte.text.strip()
	valor_atual 			= valor_cte.text.strip()
	prestador_atual 		= prestador_cte.text.strip()
	numero_cte_atual	= numero_cte.text.strip()
	cnpj_emissor_atual	= cnpj_emissor.text.strip()
	tomador_atual		= BuscarTomador (arg_node)

	
	try:
		data_atual = date.fromisoformat(data_emissao.text.strip().split('T')[0])
	except Exception as e:
		print(EscreverVermelho(f'[ ERROR ] - falha ao extrair data: {e}'))
		data_atual = '[ ERROR ] - falha ao extrair data'
    
	if tomador_atual is None:
		print(EscreverVermelho(f'[ ERROR ] - ProcessarCTE(): CTE invalidado por falta de elemento. Inserindo na lista de invalidos e continuando'))
		return -1
	
	#invalida se as informaçoes forem em branco
	if  "" in [valor_atual, chave_atual, prestador_atual, numero_cte_atual, tomador_atual, cnpj_emissor_atual]:
		print(EscreverVermelho(f'[ ERROR ] - ProcessarCTE(): CTE invalidado por informações em branco. Inserindo na lista de invalidos e continuando'))
		return -1
		
	#invalida se a chave for menor que 44 e não for somente digitos
	if len (chave_atual) != 44 or not chave_atual.isdigit():
		print(EscreverVermelho(f"[ ERROR ] - ProcessarCTE(): CTE invalidado por chave corrompida"))
		return -1
		
	#ingnora caso ja tenha sido analisado
	if chave_atual  in conjunto_cte_analisados:
		return -2
	else:
		conjunto_cte_analisados.add(chave_atual)
		
	#encontra todos os elementos da tag observações em qualquer profundidade
	encontrados_obs 	= arg_node.findall(buscar_obs,		espaco_nome_cte)
	#encontra todos os elementos da tag ndoc em qualquer profundidade
	encontrados_ndoc 	= arg_node.findall(buscar_ndoc,		espaco_nome_cte)
	#encontra todos os elementos da tag infAdFisco em qualquer profundidade
	encontrados_nfisco 	= arg_node.findall(buscar_nfisco,	espaco_nome_cte)
	#encontra todos os elementos da tag proPred em qualquer profundidade
	encontrados_pred 	= arg_node.findall(buscar_pred,		espaco_nome_cte)
	
	#armazena todos os pedidos encontrados
	match = list ()
	#cria uma lista com todos os pedidos encontrados
	lista_pedidos = [*encontrados_obs, *encontrados_ndoc, *encontrados_nfisco, *encontrados_pred]
	
	#busca pelo numero do pedido em todas as tags observações e anexa na lista
	for i in lista_pedidos:
		if i.text:
			match.extend (re.findall(regex_pedido,i.text))

	#cria uma nova lista sem repetição
	lista_limpa = list (set (match))
	
	#trata a origem e destino. em caso de erros, basta comentar todas essas linhas:
	origem				= elemento_origem.text + ' - ' + elemento_uf_origem.text
	destino				= elemento_destino.text + ' - '  + elemento_uf_destino.text
	
	#preenche o dicionario
	global_dic_documento ['chave_documento']		= chave_atual
	global_dic_documento ['razao_social'] 			= prestador_atual
	global_dic_documento ['cnpj_emissor'] 			= cnpj_emissor_atual
	global_dic_documento ['tomador_servico']		= tomador_atual
	global_dic_documento ['numero_documento']		= numero_cte_atual
	global_dic_documento ['tipo_documento'] 		= 'CT-E'
	global_dic_documento ['valor_documento']		= valor_atual
	global_dic_documento ['data_emissao']			= data_atual
	global_dic_documento ['origem']					= origem
	global_dic_documento ['destino']					= destino
	
	
	#se não encotrar pedido, tenta encontrar placas ou  pregão
	if len (lista_limpa) == 0:
	
		global_dic_documento ['status_pedido'] = 's/pedido'
		#se não encontrar pedido, busca pelos pregões ou placas
		lista_pregao = set()
		#busca pelo numero do pregão em todas as tags observações e anexa no conjunto
		for i in lista_pedidos:
			if i.text:
				lista_pregao.update (re.findall(regex_pregao,i.text))
				lista_pregao.update (re.findall(regex_placas,i.text))
		
		#cria uma lista de pregoes/placas sem repetição
		lista_limpa_pregoes = list(lista_pregao)

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
	
#Função que determina e retorna o tomador de servico. Retorna a string do tomador se sucesso ou None se erro
def BuscarTomador (raiz):

	if type (raiz) is not ET.Element:
		raise TypeError("[ ERROR ] - BuscarTomador(): objeto invalido recebido como argumento")
		
	#limpa o dicionario		
	dic_tomador ['tomador'] = ''

	#busca pelo codigo que indica quem é o tomador
	tomador_3 = "./ns:CTe/ns:infCte/ns:ide/ns:toma3/ns:toma"
	tomador_4 = "./ns:CTe/ns:infCte/ns:ide/ns:toma4/ns:CNPJ"
	
	#determina se  é tomador  4
	tipo_tomador = raiz.find (tomador_4,		espaco_nome_cte)
	if tipo_tomador is not None and tipo_tomador.text.strip() != "":
		if len (tipo_tomador.text.strip()) == 14:
			dic_tomador ['tomador'] = tipo_tomador.text.strip()
			return 'LI' + dic_tomador ['tomador'][10] + dic_tomador ['tomador'][11]
		return  None
		
	#tomador  3
	tipo_tomador = raiz.find (tomador_3,		espaco_nome_cte)			
	if tipo_tomador is None:
		return None
		
	#determina o tomador
	match tipo_tomador.text.strip():
	
		case '0':
			#o tomador é o remetente (quem envia a mercadoria/emite a NF)
			caminho_cnpj = "./ns:CTe/ns:infCte/ns:rem/ns:CNPJ"
		case '1':
			#o tomador é o expedidor (quem entrega a carga fisicamente ao transportador)
			caminho_cnpj = "./ns:CTe/ns:infCte/ns:exped/ns:CNPJ"
		case '2':
			#o tomador é o recebedor (quem coleta a carga do transportador)
			caminho_cnpj = "./ns:CTe/ns:infCte/ns:receb/ns:CNPJ"
		case '3':
			#o tomador é o destinatário (quem recebe a mercadoria final/comprador)
			caminho_cnpj = "./ns:CTe/ns:infCte/ns:dest/ns:CNPJ"
		case _:
			return None	
			
	#busca o tomador no caminho determinado
	tomador = raiz.find (caminho_cnpj,		espaco_nome_cte)			
	if tomador is not None and tomador.text.strip() != "" and len (tomador.text.strip()) == 14:
		dic_tomador ['tomador'] = tomador.text.strip()
		return 'LI' + dic_tomador ['tomador'][10] + dic_tomador ['tomador'][11]
	return None
