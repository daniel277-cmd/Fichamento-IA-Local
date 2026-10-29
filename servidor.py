import json
import io
import ollama
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pypdf import PdfReader

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/fichar', methods=['POST'])
def fichar():
    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo foi enviado.'}), 400

    file = request.files['arquivo']
    if file.filename == '':
        return jsonify({'erro': 'Arquivo não selecionado.'}), 400

    filename = file.filename.lower()
    texto = ""

    try:
        if filename.endswith('.pdf'):
            reader = PdfReader(file.stream)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    texto += extracted + "\n"
        elif filename.endswith('.txt'):
            texto = file.stream.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({'erro': 'Formato não suportado. Envie apenas .pdf ou .txt'}), 400
    except Exception as e:
        return jsonify({'erro': f'Falha ao ler o arquivo: {str(e)}'}), 500

    if not texto.strip():
        return jsonify({'erro': 'Não foi possível extrair texto do arquivo fornecido.'}), 400

    prompt = f'''
    ### TEXTO PARA ANÁLISE ###
    {texto}

    ### INSTRUÇÕES DE ALTO NÍVEL (TUTORIA ACADÊMICA) ###
    Você atua como um Professor Universitário Titular e Especialista em Letramento Acadêmico e Metodologia Científica. 
    Seu objetivo NÃO é apenas resumir, mas processar o texto de forma que ajude o estudante a compreender a ESTRUTURA COMPLETA da obra, mapeando TODOS os problemas apresentados.

    CRITÉRIOS PEDAGÓGICOS RIGOROSOS:
    1. TESE E PROBLEMAS MÚLTIPLOS (VISÃO HOLÍSTICA): O autor provavelmente aborda *vários* problemas, falhas ou estudos de caso diferentes ao longo do texto. Na "tese", você DEVE englobar a TOTALIDADE da obra, listando a pluralidade de problemas discutidos (não isole apenas um assunto!), o argumento central que os une e a implicação geral.
    2. CONCEITOS DISTRIBUÍDOS: Escolha conceitos que representem partes *diferentes* do texto (início, meio e fim), para garantir que o aluno estude todos os cenários abordados. Explique cada termo estritamente à luz do texto.
    3. ARGUMENTOS E DESCOBERTAS: O que o texto provou ou defendeu? Extraia de 2 a 3 argumentos centrais, premissas ou descobertas principais da obra. Escreva de forma assertiva e explicativa (não faça cópia literal de trechos). O aluno deve ler isso e entender exatamente quais são os pilares práticos e teóricos que sustentam a conclusão do texto.
    4. QUESTÕES (Nível ENADE / Prova de Mestrado): 
       - Questão 1 (Análise Comparativa de Problemas): Exija que o aluno compare, diferencie ou relacione dois ou mais problemas diferentes apresentados no texto.
       - Questão 2 (Síntese Conceitual): Peça para o aluno justificar como as soluções apresentadas resolvem os problemas estruturais levantados.
       - Questão 3 (Aplicação Prática Holística): Crie um cenário prático que exija o conhecimento global do documento para ser resolvido.
       * O "gabarito" deve ser um padrão de resposta direto, EXTREMAMENTE TÉCNICO E ESPECÍFICO. É estritamente PROIBIDO repetir ou parafrasear a pergunta. Você DEVE fornecer os conceitos reais e as justificativas técnicas que o aluno precisa escrever para ter nota máxima (Exemplo correto: "Demonstrar que a função ReLU evita a dissipação do gradiente, enquanto uma taxa alta causa divergência..."). NUNCA dê respostas circulares ou genéricas.

    ### SAÍDA OBRIGATÓRIA EM JSON ###
    Responda ESTRITAMENTE em formato JSON usando as chaves exatas abaixo. NÃO adicione nenhum texto, formatação markdown (como ```json) ou explicação fora do objeto JSON.

    {{
      "tese": "Síntese mapeando TODOS os principais problemas da obra + Argumento Central unificador + Implicação. Seja denso, analítico e abranja o texto todo (máximo de 5 linhas).",
      "conceitos": [
        {{"termo": "Conceito 1 (focado no 1º problema do texto)", "definicao": "Explicação profunda do termo contextualizada."}},
        {{"termo": "Conceito 2 (focado no 2º problema do texto)", "definicao": "Explicação profunda do termo contextualizada."}},
        {{"termo": "Conceito 3 (focado no 3º problema do texto)", "definicao": "Explicação profunda do termo contextualizada."}},
        {{"termo": "Conceito 4 (focado na metodologia/solução)", "definicao": "Explicação profunda do termo contextualizada."}},
        {{"termo": "Conceito 5 (focado na conclusão/implicação)", "definicao": "Explicação profunda do termo contextualizada."}}
      ],
      "argumentos": [
        "Descoberta/Argumento 1: Explicação direta do porquê o autor defende isso e qual o impacto.",
        "Descoberta/Argumento 2: Explicação direta da segunda grande premissa levantada no artigo."
      ],
      "questoes": [
        {{"pergunta": "Pergunta analítica relacionando MÚLTIPLOS problemas do texto?", "gabarito": "Abordar os cenários X e Y, demonstrando como a falha em um impacta diretamente a consistência do outro, concluindo com..."}},
        {{"pergunta": "Pergunta exigindo relação entre falhas sistêmicas e conceitos?", "gabarito": "Articular que o mecanismo de controle falha porque a ausência de restrições estruturais permite..."}},
        {{"pergunta": "Pergunta de nível crítico abrangendo a obra toda?", "gabarito": "Demonstrar criticamente que, caso as premissas de validação sejam ignoradas, o impacto gerado compromete..."}}
      ]
    }}
    '''

    try:
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        content = response['message']['content']
        dados = json.loads(content)
        return jsonify(dados)
    except json.JSONDecodeError:
        return jsonify({'erro': 'A IA não devolveu uma estrutura JSON válida. Tente novamente.'}), 500
    except Exception as e:
        return jsonify({'erro': f'Falha na comunicação com o Ollama: {str(e)}'}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Servidor do Fichário.ai rodando em http://localhost:8000")
    print("Acesse no navegador e faça o upload dos seus arquivos!")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=8000, debug=True)