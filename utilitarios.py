# ------------------------------------------------------------------------------
# Módulo: Motor xml para auditoria fiscal
# Versão: 5.4
# Autor: Pedro Henrique Oliveira da Silva
# Data: 01/06/2026
# Descrição: Automação de análise de documentos fiscais a fim de identificar inconsistências.
# ------------------------------------------------------------------------------

#liga as cores de texto
CORES 				= 1
#dicinario que é retornado a cada elemento processado
global_dic_documento = {
"tomador_servico"		:"",
"razao_social"			:"",
"cnpj_emissor"			:"",
"chave_documento"		:"",
"data_emissao"			:"",
"numero_documento"		:"",
"valor_documento"		:"",
"status_pedido"			:"",
"tipo_documento"		:"",
"pedido"				:"",
"informacoes_extras"	:"",
"origem"				:"",
"destino"				:"",
"p_setor_responsavel"	:"",
"palavras_chaves"		:"",
"metodo_analise"		:""

}

#inserir aqui o prestador como chave sem espaços no extremo e os setores em lista
global_dic_busca_direta = {

"SETOR X"	: ["SETOR Y"],

}

#lista de regex para achar palavras chaves de setores. o motor ignora maiusculas e minusculas e tenta ignorar erros de digitação. NÃO É PERMITIDO GRUPOS DE CAPTURA
global_regex_setores = {
   
   "Logística"	: r"\b(frota|ve[iíì]culo|placa|transporte)\b",
   "Financeiro"	: r"\b(nota|fatura|boleto|pagamento)\b",
   "TI"			: r"\b(software|licen[cç]a|suporte t[eéè]cnico)\b"
   }


#regex
regex_pedido 			= r"\b00\d{8}\b"				
regex_pregao 			= r"\b[YX]\d{5,6}\b"				
regex_placas 			= r'\b[A-Z]{3}\d{1}[A-Z]{1}\d{2}\b'	


#Escreve verde na tela
def EscreverVerde           (arg_texto):
	if CORES:
		verde = "\033[1;32m"
		reset = "\033[0m"
		return (f"{verde}{arg_texto}{reset}")
	return  arg_texto

#Escreve vermelho  na tela
def EscreverVermelho        (arg_texto):
	if CORES: 
		vermelho = "\033[1;31m"
		reset = "\033[0m"
		return (f"{vermelho}{arg_texto}{reset}")
	return arg_texto

#Escreve magenta escuro na tela
def EscreverRosa(arg_texto):
	if CORES:
		magenta_escuro = "\033[1;35m"
		reset = "\033[0m"
		return f"{magenta_escuro}{arg_texto}{reset}"
	return arg_texto
