# ------------------------------------------------------------------------------
# Módulo: Motor xml para auditoria fiscal
# Versão: 5.4
# Autor: Pedro Henrique Oliveira da Silva
# Data: 01/06/2026
# Descrição: Automação de análise de documentos fiscais a fim de identificar inconsistências.
# -----------------------------------------------------------------------------------------------------------------------------------------



from utilitarios import global_dic_documento, EscreverVerde, EscreverRosa, EscreverVermelho,regex_pedido, regex_placas, regex_pregao, global_regex_setores
from utilitarios import global_dic_busca_direta
import xml.etree.ElementTree as ET
from datetime import date
import re


# Caminhos para extração de dados do XML
buscar_chave_nfe         = "./NumeracaoNota/CodigoVerificacao"
buscar_numero_nfe        = "./NumeracaoNota/NumeroDocumento"
buscar_data_emissao_nfe  = "./DataEmissao"
buscar_cnpj_prestador    = "./Emitente/CNPJ"
buscar_razao_prestador   = "./Emitente/RazaoSocial"
buscar_uf_prestador      = "./Emitente/Endereco/UF"
buscar_valor_total       = "./ValorTotal"
buscar_cnpj_tomador      = "./Destinatario/CNPJ"
buscar_discriminacao     = "./Servicos/Discriminacao"

def ProcessarNFe(arg_node):

	#valida o tipo do argumento recebido
	if type(arg_node) != ET.Element:
		raise TypeError('[ ERROR ] - ProcessarNFe(): objeto inválido recebido como argumento')

	#valida se busca direta está de acordo com o esperado: lista
	for chave, valor in global_dic_busca_direta.items():
		if type(valor) != list:
			raise TypeError('[ ERROR ] - ProcessarNFe(): a lista de busca direta não está inicializada corretamente')

	#busca pelos elementos da nota
	chave_nfe        = arg_node.find(buscar_chave_nfe)
	numero_nfe       = arg_node.find(buscar_numero_nfe)
	data_emissao     = arg_node.find(buscar_data_emissao_nfe)
	cnpj_prestador   = arg_node.find(buscar_cnpj_prestador)
	razao_prestador  = arg_node.find(buscar_razao_prestador)
	valor_total      = arg_node.find(buscar_valor_total)
	cnpj_tomador     = arg_node.find(buscar_cnpj_tomador)
	discriminacao    = arg_node.find(buscar_discriminacao)

	#invalida se algum campo obrigatório estiver ausente 
	if (chave_nfe       is None or chave_nfe.text       is None or
	numero_nfe      is None or numero_nfe.text      is None or
	data_emissao    is None or data_emissao.text    is None or
	cnpj_prestador  is None or cnpj_prestador.text  is None or
	razao_prestador is None or razao_prestador.text is None or
	valor_total     is None or valor_total.text     is None or
	cnpj_tomador    is None or cnpj_tomador.text    is None):
		print(EscreverVermelho('[ ERROR ] - ProcessarNFe(): NF-e invalidada por falta de elemento. Inserindo na lista de inválidos e continuando'))
		return -1

	#extrai e limpa os valores
	chave_atual         = chave_nfe.text.strip()
	numero_atual        = numero_nfe.text.strip()
	cnpj_emissor_atual  = cnpj_prestador.text.strip()
	razao_atual         = razao_prestador.text.strip()
	valor_atual         = valor_total.text.strip()
	cnpj_tomador_atual  = cnpj_tomador.text.strip()

	#invalida se algum campo obrigatório estiver em branco após limpeza
	if "" in [chave_atual, numero_atual, cnpj_emissor_atual, razao_atual, valor_atual, cnpj_tomador_atual]:
		print(EscreverVermelho('[ ERROR ] - ProcessarNFe(): NF-e invalidada por informações em branco. Inserindo na lista de inválidos e continuando'))
		return -1

	#valida o CNPJ do tomador: deve ter 14 dígitos
	if len(cnpj_tomador_atual) != 14 or not cnpj_tomador_atual.isdigit():
		print(EscreverVermelho('[ ERROR ] - ProcessarNFe(): NF-e invalidada por CNPJ do tomador corrompido. Inserindo na lista de inválidos e continuando'))
		return -1

	#converte a data de emissão
	try:
		#data_atual = datetime.fromisoformat(data_emissao.text.strip()).date()
		data_atual = date.fromisoformat(data_emissao.text.strip().split('T')[0])

	except Exception as e:
		print(EscreverVermelho(f'[ ERROR ] - falha ao extrair data: {e}'))
		data_atual = '[ ERROR ] - falha ao extrair data'


	#monta o tomador no padrão TM + dígitos 10 e 11 do CNPJ ──
	tomador_atual = 'TM' + cnpj_tomador_atual[10] + cnpj_tomador_atual[11]

	#captura a discriminação se disponível
	discriminacao_atual = discriminacao.text.strip() if discriminacao is not None and discriminacao.text else 'nada informado'
	
	#guarda os pedidos encontrados
	match = list()
	if discriminacao_atual:
		match.extend(re.findall(regex_pedido, discriminacao_atual))

	# remove duplicatas
	lista_limpa = list(set(match))

	#preenche o dicionário compartilhado
	global_dic_documento['chave_documento']  		= chave_atual
	global_dic_documento['numero_documento'] 		= numero_atual
	global_dic_documento['cnpj_emissor']     		= cnpj_emissor_atual
	global_dic_documento['razao_social']     		= razao_atual
	global_dic_documento['valor_documento']  		= valor_atual
	global_dic_documento['tomador_servico']  		= tomador_atual
	global_dic_documento['data_emissao']     		= data_atual
	global_dic_documento['tipo_documento']   		= 'NF-E'
	

	#se não tiver pedido, tentará identificar ID e setores responsaveis
	if len (lista_limpa) == 0:

		global_dic_documento ['status_pedido'] = 's/pedido'
		#se não encontrar pedido, busca pelos ID ou placas
		lista_limpa_id = set()
		#busca pelo numero do pregão em todas as tags observações e anexa no conjunto
		if discriminacao_atual:
			lista_pregao.update(re.findall(regex_pregao, discriminacao_atual))
			#lista_pregao.update(re.findall(regex_placas,  discriminacao_atual))
	
		#cria uma lista de pregoes/placas sem repetição
		lista_limpa_id = list(lista_pregao)

		#se não encontrar nenhum pregão, busca pela descrição e tenta identificar os setores responsaveis por meio do dicionário de plavras chaves
		if len (lista_limpa_id) == 0:
			global_dic_documento ['informacoes_extras'] = ('[ DESCRIÇÃO ]: ') + discriminacao_atual

			#faz a busca direta do setor responsavel. a busca direta é interropida ao encontar o primeiro setor responsavel
			razao = global_dic_documento['razao_social']
			if razao in global_dic_busca_direta:
				setores = global_dic_busca_direta[razao]
				global_dic_documento['p_setor_responsavel'] = ", ".join(setores)
				global_dic_documento['metodo_analise'] = "Busca direta"
				return global_dic_documento

			#se não achar o setor responsavel via busca direta, tenta as palavras chaves
			setores_responsaveis 		= set()
			palavras_chaves_encontradas	= set()
			for chave,valor in global_regex_setores.items():
				palavras_chaves = (re.findall(valor,global_dic_documento ['informacoes_extras'] , flags=re.IGNORECASE))
				#se achar palavras chaves, adciona na lista e adiona o setor responsavel
				if len(palavras_chaves) > 0:
					for i in palavras_chaves:
						palavras_chaves_encontradas.add(i)
					setores_responsaveis.add (chave)

			#informa o setor responsavel
			if len (setores_responsaveis) > 0:
				global_dic_documento ['metodo_analise'] 		= "Palavra chave"
				global_dic_documento ['p_setor_responsavel'] 	= ", ".join(sorted (setores_responsaveis))
				global_dic_documento ['palavras_chaves'] 		= ", ".join(palavras_chaves_encontradas)

			else:
				#tenta analisar trechos de razão social. pode-se aplicar elif em cadeia para tentar identificar palavras via razão social
				trechos = (re.findall(r"\bregex\b", global_dic_documento['razao_social'] , flags=re.IGNORECASE))
				if len(trechos) > 0:
					global_dic_documento ['metodo_analise'] 		= "Trecho de razão social"
					global_dic_documento ['p_setor_responsavel'] 	= "<informa setor responsavel>"
					global_dic_documento ['palavras_chaves'] 		= ", ".join(trechos)
				else:
					global_dic_documento ['p_setor_responsavel'] 	= "Outras areas"

			return global_dic_documento

		#se encontrar, intera sobre a lista e adciona as informações extras encontradas 
		else:
			global_dic_documento ['metodo_analise'] 	 = "setor logistica"
			global_dic_documento ['informacoes_extras'] += (", ".join(lista_limpa_id))
			global_dic_documento ['p_setor_responsavel'] 	="Não se aplica"
			return global_dic_documento

	#muda o status para com pedido ou com multiplos pedidos	
	elif len (lista_limpa) > 1:	
		global_dic_documento ['status_pedido'] 			= 'm/pedido'
		global_dic_documento ['p_setor_responsavel'] 	= "Não se aplica"

	elif len (lista_limpa) == 1:
		global_dic_documento ['status_pedido'] 			= 'c/pedido'
		global_dic_documento ['p_setor_responsavel'] 	= "Não se aplica"


	#insere os pedidos encontrados e retorna
	global_dic_documento ['pedido'] 	= ", ".join(lista_limpa)
	return global_dic_documento	

