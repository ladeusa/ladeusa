import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) # DON'T CHANGE THIS !!!

from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

app = Flask(__name__)
app.secret_key = 'ladeusa_supersegredo'

import os

# Caminhos seguros dos arquivos JSON na pasta 'protegido'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTEGIDO_DIR = os.path.join(BASE_DIR, 'protegido')

USUARIOS_FILE = os.path.join(PROTEGIDO_DIR, 'usuarios.json')
BINS_FILE = os.path.join(PROTEGIDO_DIR, 'bins.json')
COMPRAS_FILE = os.path.join(PROTEGIDO_DIR, 'compras.json')
INDICACOES_FILE = os.path.join(PROTEGIDO_DIR, 'indicacoes.json')
VALORES_BANDEIRAS_FILE = os.path.join(PROTEGIDO_DIR, 'valores_bandeiras.json')

# Removido - Funções auxiliares JSON não são mais necessárias
# def carregar_json(file_path): ...
# def salvar_json(file_path, data): ...
# def carregar_bins(): ...
# def carregar_compras(): ...
# def salvar_compras(compras): ...
# def carregar_cartoes_completos(): ...
# def atualizar_valor_no_json(bandeira, nivel, novo_valor): ...
# def carregar_valores(): ...
# def buscar_valor_por_combo(bandeira, nivel): ...
# def atualizar_valores_em_bins(bandeira, nivel, novo_valor): ...

# ================= ROTAS DE ADMIN ===================
from datetime import datetime, timedelta

# Proteção contra brute force no admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Carregar tentativas anteriores do admin
        try:
            with open(os.path.join('protegido', 'admin_tentativas.json'), 'r') as f:
                tentativas_data = json.load(f)
        except:
            tentativas_data = {"erros": 0, "bloqueado_ate": None}

        agora = datetime.now()
        bloqueado_ate_str = tentativas_data.get("bloqueado_ate")
        bloqueado_ate = datetime.strptime(bloqueado_ate_str, "%Y-%m-%d %H:%M:%S") if bloqueado_ate_str else None

        if bloqueado_ate and agora < bloqueado_ate:
            flash('Admin bloqueado por muitas tentativas. Tente novamente em breve.', 'danger')
            return redirect('/admin/login')

        if username == 'admin' and password == 'Fetom2312@':
            session.permanent = True
            session['admin_logado'] = True
            # Reseta as tentativas
            tentativas_data = {"erros": 0, "bloqueado_ate": None}
            with open(os.path.join('protegido', 'admin_tentativas.json'), 'w') as f:
                json.dump(tentativas_data, f, indent=4)
            return redirect(url_for('admin_painel'))
        else:
            tentativas_data["erros"] += 1
            if tentativas_data["erros"] >= 5:
                tentativas_data["bloqueado_ate"] = (agora + timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
                flash('Muitas tentativas erradas. Login bloqueado por 60 segundos.', 'danger')
            else:
                flash('Credenciais de admin inválidas!', 'danger')

            with open(os.path.join('protegido', 'admin_tentativas.json'), 'w') as f:
                json.dump(tentativas_data, f, indent=4)

            return redirect('/admin/login')

    return render_template('admin_login.html')

@app.route('/admin/painel')
def admin_painel():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    bins = carregar_bins()
    cartoes_completos = carregar_cartoes_completos()

    bins_disponiveis = [b for b in bins if any(c['cartao'].startswith(b['bin']) for c in cartoes_completos)]
    total_bins = len(bins_disponiveis)

    return render_template('admin_painel.html', total_bins=total_bins)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logado', None)
    return redirect(url_for('admin_login'))

import os  # adiciona no topo do app.py se ainda não tiver

@app.route('/gerenciar_usuarios')
def gerenciar_usuarios():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    caminho_usuarios = os.path.join(os.path.dirname(__file__), 'protegido', 'usuarios.json')

    try:
        with open(caminho_usuarios, 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
    except FileNotFoundError:
        usuarios = []

    total_usuarios = len(usuarios)
    saldo_total = sum(float(u.get('saldo', 0)) for u in usuarios)

    return render_template('admin_usuarios.html',
                           usuarios=usuarios,
                           total_usuarios=total_usuarios,
                           saldo_total=saldo_total)

@app.route('/excluir_usuario/<email>')
def excluir_usuario(email):
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    caminho_usuarios = os.path.join(os.path.dirname(__file__), 'protegido', 'usuarios.json')

    try:
        with open(caminho_usuarios, 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
    except FileNotFoundError:
        usuarios = []

    usuarios = [u for u in usuarios if u.get('email') != email]

    with open(caminho_usuarios, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

    flash('Usuário excluído com sucesso.')
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/estatisticas')
def estatisticas():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    # Carregar os dados dos usuários
    try:
        with open(USUARIOS_FILE, 'r') as f:
            usuarios = json.load(f)
    except FileNotFoundError:
        usuarios = []

    total_usuarios = len(usuarios)
    saldo_total = sum(float(u.get('saldo', 0)) for u in usuarios)

    # Dados fictícios, substitua se já tiver pagamentos e vendas reais
    total_pagamentos = 0
    total_bins = 0
    total_valor_bins = 0

    return render_template('admin_estatisticas.html',
                           total_usuarios=total_usuarios,
                           saldo_total=saldo_total,
                           total_pagamentos=total_pagamentos,
                           total_bins=total_bins,
                           total_valor_bins=total_valor_bins)

@app.route('/gerenciar_bins', methods=['GET', 'POST'])
def gerenciar_bins():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        if arquivo and arquivo.filename.endswith('.txt'):
            linhas = arquivo.read().decode('utf-8').splitlines()

            try:
                with open('bins.json', 'r') as f:
                    bins = json.load(f)
            except FileNotFoundError:
                bins = []

            for linha in linhas:
                dados = linha.strip().split('|')
                if len(dados) == 8:
                    cartao, mes, ano, cvv, cpf, nome, bandeira, nivel = dados
                    valor = buscar_valor_por_combo(bandeira, nivel)  # valor automático do JSON
                    bins.append({
                        'cartao': cartao,
                        'mes': mes,
                        'ano': ano,
                        'cvv': cvv,
                        'cpf': cpf,
                        'nome': nome,
                        'bandeira': bandeira,
                        'nivel': nivel,
                        'valor': valor
                    })

            with open('bins.json', 'w', encoding='utf-8') as f:
                json.dump(bins, f, indent=2, ensure_ascii=False)

            flash('BINs importadas com sucesso!', 'success')

    try:
        with open('bins.json', 'r', encoding='utf-8') as f:
            bins = json.load(f)
    except FileNotFoundError:
        bins = []

    return render_template('admin_adicionar_bins.html', bins=bins)

@app.route('/admin/listar_bins')
def admin_listar_bins():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    # Agora puxa do cartoes_completos.json
    caminho_cartoes = os.path.join(os.path.dirname(__file__), 'protegido', 'cartoes_completos.json')

    try:
        with open(caminho_cartoes, 'r', encoding='utf-8') as f:
            bins = json.load(f)
    except FileNotFoundError:
        bins = []

    return render_template('admin_listar_bins.html', bins=bins)

def carregar_valores():
    caminho = os.path.join(os.path.dirname(__file__), 'protegido', 'valores_bins.json')
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

@app.route('/atualizar_valor', methods=['POST'])
def atualizar_valor():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))
    
    bandeira = request.form['bandeira']
    nivel = request.form['nivel']
    novo_valor = request.form['valor']

    atualizar_valor_no_json(bandeira, nivel, novo_valor)  # Atualiza valores_bandeiras.json
    atualizar_valores_em_bins(bandeira, nivel, novo_valor)  # Atualiza todos os bins e cartoes

    return redirect(url_for('gerenciar_valores'))


# Função dinâmica: busca valor em valores_bandeiras.json
def buscar_valor_por_combo(bandeira, nivel):
    try:
        with open('valores_bandeiras.json', 'r', encoding='utf-8') as f:
            valores = json.load(f)
    except FileNotFoundError:
        return 99.90  # valor padrão se o arquivo não existir

    for item in valores:
        if item['bandeira'].upper() == bandeira.upper() and item['nivel'].upper() == nivel.upper():
            return item['valor']

    return 99.90  # valor padrão se não encontrar a combinação


# NOVA FUNÇÃO: atualiza todas as BINs salvas com novo valor
def atualizar_valores_em_bins(bandeira, nivel, novo_valor):
    try:
        with open('bins.json', 'r', encoding='utf-8') as f:
            bins = json.load(f)
    except FileNotFoundError:
        bins = []

    for bin_item in bins:
        if bin_item['bandeira'].upper() == bandeira.upper() and bin_item['nivel'].upper() == nivel.upper():
            bin_item['valor'] = float(novo_valor)

    with open('bins.json', 'w', encoding='utf-8') as f:
        json.dump(bins, f, indent=2)

    try:
        with open('cartoes_completos.json', 'r', encoding='utf-8') as f:
            cartoes = json.load(f)
    except FileNotFoundError:
        cartoes = []

    for cartao in cartoes:
        if cartao['bandeira'].upper() == bandeira.upper() and cartao['nivel'].upper() == nivel.upper():
            cartao['valor'] = float(novo_valor)

    with open('cartoes_completos.json', 'w', encoding='utf-8') as f:
        json.dump(cartoes, f, indent=2)

@app.route('/admin/adicionar_bins', methods=['GET', 'POST'])
def admin_adicionar_bins():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    mensagem = ''
    duplicadas = 0
    adicionadas = 0
    ignoradas = 0

    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        if arquivo and arquivo.filename.endswith('.txt'):
            linhas = arquivo.read().decode('utf-8').splitlines()

            base_dir = os.path.dirname(__file__)
            caminho_cartoes = os.path.join(base_dir, 'protegido', 'cartoes_completos.json')
            caminho_bins = os.path.join(base_dir, 'protegido', 'bins.json')
            caminho_admin_bins = os.path.join(base_dir, 'protegido', 'admin_bins.json')
            caminho_valores = os.path.join(base_dir, 'protegido', 'valores_bandeiras.json')

            try:
                with open(caminho_cartoes, 'r', encoding='utf-8') as f:
                    cartoes = json.load(f)
            except FileNotFoundError:
                cartoes = []

            try:
                with open(caminho_bins, 'r', encoding='utf-8') as f:
                    bins_usuarios = json.load(f)
            except FileNotFoundError:
                bins_usuarios = []

            try:
                with open(caminho_admin_bins, 'r', encoding='utf-8') as f:
                    admin_bins = json.load(f)
            except FileNotFoundError:
                admin_bins = []

            try:
                with open(caminho_valores, 'r', encoding='utf-8') as f:
                    valores_bandeiras = json.load(f)
            except FileNotFoundError:
                valores_bandeiras = []

            cartoes_existentes = set(c['cartao'] for c in cartoes)
            bins_existentes = set(b['bin'] for b in bins_usuarios)

            for linha in linhas:
                linha = linha.strip()
                if not linha or '|' not in linha:
                    ignoradas += 1
                    continue

                try:
                    partes = [x.strip() for x in linha.split('|')]
                    if len(partes) < 9:
                        ignoradas += 1
                        continue

                    cartao, mes, ano, cvv, cpf, nome, bin_formatada, bandeira, nivel = partes[:9]

                    if cartao in cartoes_existentes:
                        duplicadas += 1
                        continue

                    # valor dinâmico
                    valor = next(
                        (v['valor'] for v in valores_bandeiras if v['bandeira'].upper() == bandeira.upper() and v['nivel'].upper() == nivel.upper()),
                        0.0
                    )

                    # adiciona cartão completo
                    cartoes.append({
                        'cartao': cartao,
                        'mes': mes,
                        'ano': ano,
                        'cvv': cvv,
                        'cpf': cpf,
                        'nome': nome,
                        'bin': bin_formatada, # Adiciona o bin formatado
                        'bandeira': bandeira,
                        'nivel': nivel,
                        'valor': valor,
                        'disponivel': True # Marcar como disponível
                    })
                    cartoes_existentes.add(cartao)
                    adicionadas += 1

                    # adiciona bin resumido (se não existir)
                    if bin_formatada not in bins_existentes:
                        bins_usuarios.append({
                            'bin': bin_formatada,
                            'bandeira': bandeira.lower(), # Padroniza para minúsculas
                            'nivel': nivel,
                            'valor': valor,
                            'disponivel': True # Marcar como disponível
                        })
                        bins_existentes.add(bin_formatada)

                    # adiciona bin no admin_bins
                    admin_bins.append({
                        'bin': bin_formatada,
                        'bandeira': bandeira,
                        'nivel': nivel,
                        'valor': valor
                    })

                except Exception as e:
                    print(f"Erro ao processar linha: {linha} - {e}")
                    ignoradas += 1

            # Salva os arquivos JSON atualizados
            with open(caminho_cartoes, 'w', encoding='utf-8') as f:
                json.dump(cartoes, f, indent=2, ensure_ascii=False)
            with open(caminho_bins, 'w', encoding='utf-8') as f:
                json.dump(bins_usuarios, f, indent=2, ensure_ascii=False)
            with open(caminho_admin_bins, 'w', encoding='utf-8') as f:
                json.dump(admin_bins, f, indent=2, ensure_ascii=False)

            mensagem = f'{adicionadas} BINs adicionadas, {duplicadas} duplicadas ignoradas, {ignoradas} linhas inválidas.'
            flash(mensagem, 'success')

    return render_template('admin_adicionar_bins.html')


@app.route('/admin/gerenciar_valores', methods=['GET', 'POST'])
def gerenciar_valores():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    caminho_valores = os.path.join(os.path.dirname(__file__), 'protegido', 'valores_bandeiras.json')

    if request.method == 'POST':
        bandeira = request.form['bandeira']
        nivel = request.form['nivel']
        valor = request.form['valor']

        try:
            with open(caminho_valores, 'r', encoding='utf-8') as f:
                valores = json.load(f)
        except FileNotFoundError:
            valores = []

        # Atualiza ou adiciona novo valor
        encontrado = False
        for item in valores:
            if item['bandeira'] == bandeira and item['nivel'] == nivel:
                item['valor'] = float(valor)
                encontrado = True
                break
        
        if not encontrado:
            valores.append({'bandeira': bandeira, 'nivel': nivel, 'valor': float(valor)})

        with open(caminho_valores, 'w', encoding='utf-8') as f:
            json.dump(valores, f, indent=2, ensure_ascii=False)

        flash('Valor atualizado/adicionado com sucesso!', 'success')
        return redirect(url_for('gerenciar_valores'))

    try:
        with open(caminho_valores, 'r', encoding='utf-8') as f:
            valores = json.load(f)
    except FileNotFoundError:
        valores = []

    return render_template('admin_valores.html', valores=valores)


# ================= ROTAS DE USUÁRIO ===================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        # Consulta o usuário no banco de dados
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário existe e a senha está correta (usando hash)
        if usuario and check_password_hash(usuario.password, password):
            session.permanent = True
            session["usuario_logado"] = usuario.email
            session["saldo"] = usuario.saldo # Carrega o saldo na sessão
            return redirect(url_for("painel"))
        else:
            flash("Email ou senha inválidos!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form["confirm_password"].strip()

        if password != confirm_password:
            flash("As senhas não coincidem!", "danger")
            return redirect(url_for("cadastro"))

        # Verifica se o email já existe no banco de dados
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash("Este email já está cadastrado!", "warning")
            return redirect(url_for("cadastro"))

        # Cria novo usuário no banco de dados
        try:
            hashed_password = generate_password_hash(password)
            novo_usuario = Usuario(
                username=nome, 
                email=email, 
                password=hashed_password, 
                saldo=0.0, 
                # Adicione outros campos como codigo, indicou se necessário
            )
            db.session.add(novo_usuario)
            db.session.commit()
            flash("Cadastro realizado com sucesso! Faça login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar usuário: {e}", "danger")
            print(f"Erro DB cadastro: {e}") # Log do erro
            return redirect(url_for("cadastro"))

    return render_template("cadastro.html")

@app.route("/painel")
def painel():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    email_logado = session["usuario_logado"]
    # Busca o usuário no banco de dados
    usuario_atual = Usuario.query.filter_by(email=email_logado).first()

    if usuario_atual:
        # Atualiza o saldo na sessão para garantir que esteja sempre correto
        session["saldo"] = usuario_atual.saldo
        # Passa o objeto usuario_atual (do DB) e o saldo para o template
        return render_template("painel.html", usuario=usuario_atual, saldo=usuario_atual.saldo)
    else:
        # Se não encontrar o usuário no DB, desloga
        session.pop("usuario_logado", None)
        session.pop("saldo", None)
        flash("Usuário não encontrado. Faça login novamente.", "warning")
        return redirect(url_for("login"))
@app.route("/logout")
def logout():
    session.pop('usuario_logado', None)
    session.pop('carrinho', None)
    session.pop('saldo', None)
    return redirect(url_for('login'))

@app.route("/catalogo_bins")
def catalogo_bins():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    # Carrega as BINs e suas contagens do banco de dados
    bins_disponiveis = carregar_bins_com_contagem_db()
    saldo_usuario = session.get("saldo", 0.0) # Pega o saldo da sessão
    return render_template("catalogo_bins.html", bins=bins_disponiveis, saldo=saldo_usuario)

@app.route("/adicionar_carrinho/<bin_id>")
def adicionar_carrinho(bin_id):
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    # Busca informações agregadas do tipo de BIN no banco de dados
    try:
        bin_info = db.session.query(
            CartaoCompleto.bin_formatada,
            CartaoCompleto.bandeira,
            CartaoCompleto.nivel,
            CartaoCompleto.valor,
            func.count(CartaoCompleto.id).label("quantidade")
        ).filter(
            CartaoCompleto.bin_formatada == bin_id,
            CartaoCompleto.disponivel == True
        ).group_by(
            CartaoCompleto.bin_formatada,
            CartaoCompleto.bandeira,
            CartaoCompleto.nivel,
            CartaoCompleto.valor
        ).first()

        if bin_info and bin_info.quantidade > 0:
            carrinho = session.get("carrinho", [])
            # Verifica se o *tipo* de BIN já está no carrinho
            if bin_id not in [item["bin"] for item in carrinho]:
                # Adiciona informações relevantes do tipo de BIN ao carrinho
                carrinho.append({
                    "bin": bin_info.bin_formatada,
                    "bandeira": bin_info.bandeira.lower(),
                    "nivel": bin_info.nivel,
                    "valor": bin_info.valor,
                    "quantidade_disponivel": bin_info.quantidade # Informação extra, pode ser útil
                })
                session["carrinho"] = carrinho
                flash(f"BIN {bin_id} adicionada ao carrinho.", "success")
            else:
                flash(f"BIN {bin_id} já está no carrinho.", "info")
        else:
            flash("BIN não encontrada ou indisponível.", "danger")
            
    except Exception as e:
        flash(f"Erro ao adicionar BIN ao carrinho: {e}", "danger")
        print(f"Erro DB adicionar_carrinho: {e}")

    return redirect(url_for("catalogo_bins"))

@app.route('/ver_carrinho')
def ver_carrinho():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    carrinho = session.get('carrinho', [])
    total_carrinho = sum(float(item.get('valor', 0)) for item in carrinho)
    return render_template('ver_carrinho.html', carrinho=carrinho, total=total_carrinho)

@app.route('/remover_carrinho/<bin_id>')
def remover_carrinho(bin_id):
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    carrinho = session.get('carrinho', [])
    carrinho = [item for item in carrinho if item['bin'] != bin_id]
    session['carrinho'] = carrinho

    flash(f'BIN {bin_id} removida do carrinho.', 'success')
    return redirect(url_for('ver_carrinho'))

@app.route("/comprar")
def comprar():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    carrinho = session.get("carrinho", [])
    if not carrinho:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for("catalogo_bins"))

    total_compra = sum(float(item.get("valor", 0)) for item in carrinho)
    email_usuario = session["usuario_logado"]

    try:
        # Busca o usuário no banco de dados
        usuario_atual = Usuario.query.filter_by(email=email_usuario).first()
        if not usuario_atual:
            flash("Erro ao encontrar usuário. Faça login novamente.", "danger")
            session.pop("usuario_logado", None)
            session.pop("saldo", None)
            return redirect(url_for("login"))

        # Verifica saldo
        if usuario_atual.saldo < total_compra:
            flash("Saldo insuficiente para completar a compra.", "danger")
            return redirect(url_for("adicionar_saldo"))

        cartoes_comprados_db = []
        bins_no_carrinho = [item["bin"] for item in carrinho]

        # Bloqueia e seleciona os cartões no banco de dados
        # Itera sobre cada *tipo* de BIN no carrinho
        for bin_id in bins_no_carrinho:
            # Encontra UM cartão disponível desse tipo
            cartao_para_compra = CartaoCompleto.query.filter_by(
                bin_formatada=bin_id, 
                disponivel=True
            ).first() # Pega o primeiro disponível

            if not cartao_para_compra:
                # Se não encontrar um cartão disponível para esta BIN (pode ter acabado entre adicionar e comprar)
                db.session.rollback() # Desfaz qualquer alteração na transação
                flash(f"Desculpe, a BIN {bin_id} não está mais disponível. Remova-a do carrinho e tente novamente.", "warning")
                return redirect(url_for("ver_carrinho"))
            
            # Marca o cartão como indisponível
            cartao_para_compra.disponivel = False
            cartoes_comprados_db.append(cartao_para_compra)

        # Cria o registro da compra
        nova_compra = Compra(
            usuario_id=usuario_atual.id,
            valor_total=total_compra
        )
        db.session.add(nova_compra)
        
        # Associa os cartões comprados à compra e atualiza saldo do usuário
        for cartao in cartoes_comprados_db:
            cartao.compra_info = nova_compra # Associa o cartão à compra
        usuario_atual.saldo -= total_compra

        # Commita todas as alterações (compra, cartões, saldo)
        db.session.commit()

        # Atualiza saldo na sessão
        session["saldo"] = usuario_atual.saldo
        # Limpa carrinho da sessão
        session.pop("carrinho", None)

        # Prepara dados para a página de sucesso (pode ser simplificado)
        compra_detalhes = {
            "id": nova_compra.id,
            "data_compra": nova_compra.data_compra.strftime("%Y-%m-%d %H:%M:%S"),
            "valor_total": nova_compra.valor_total,
            "cartoes": [
                {
                    "cartao": c.cartao,
                    "mes": c.mes,
                    "ano": c.ano,
                    "cvv": c.cvv,
                    "bandeira": c.bandeira,
                    "nivel": c.nivel,
                    "valor": c.valor
                } for c in cartoes_comprados_db
            ]
        }
        session["ultima_compra"] = compra_detalhes # Salva na sessão para exibir

        flash("Compra realizada com sucesso!", "success")
        return redirect(url_for("pagamento_completo"))

    except Exception as e:
        db.session.rollback() # Garante rollback em caso de erro
        flash(f"Erro durante a compra: {e}", "danger")
        print(f"Erro DB compra: {e}")
        return redirect(url_for("ver_carrinho"))

@app.route('/pagamento_completo')
def pagamento_completo():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    ultima_compra = session.get('ultima_compra')
    if not ultima_compra:
        # Se não houver última compra na sessão, redireciona para o painel
        return redirect(url_for('painel'))

    # Limpa a última compra da sessão após exibir
    session.pop('ultima_compra', None)

    return render_template('pagamento_completo.html', compra=ultima_compra)

@app.route("/minhas_compras")
def minhas_compras():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    email_usuario = session["usuario_logado"]
    try:
        usuario_atual = Usuario.query.filter_by(email=email_usuario).first()
        if not usuario_atual:
            flash("Usuário não encontrado.", "warning")
            return redirect(url_for("login"))

        # Busca as compras do usuário no banco de dados, ordenadas pela mais recente
        compras_usuario_db = Compra.query.filter_by(usuario_id=usuario_atual.id).order_by(Compra.data_compra.desc()).all()

        # Formata os dados para exibição no template
        compras_formatadas = []
        for compra in compras_usuario_db:
            cartoes_desta_compra = []
            # Acessa os cartões associados a esta compra através do relationship
            for cartao in compra.cartoes:
                cartoes_desta_compra.append({
                    "cartao": cartao.cartao,
                    "mes": cartao.mes,
                    "ano": cartao.ano,
                    "cvv": cartao.cvv,
                    "bandeira": cartao.bandeira,
                    "nivel": cartao.nivel,
                    "valor": cartao.valor
                })
            
            compras_formatadas.append({
                "id": compra.id,
                "data_compra": compra.data_compra.strftime("%Y-%m-%d %H:%M:%S"),
                "valor_total": compra.valor_total,
                "cartoes": cartoes_desta_compra
            })

        return render_template("minhas_compras.html", compras=compras_formatadas)

    except Exception as e:
        flash(f"Erro ao buscar histórico de compras: {e}", "danger")
        print(f"Erro DB minhas_compras: {e}")
        return redirect(url_for("painel"))

@app.route('/adicionar_saldo', methods=['GET', 'POST'])
def adicionar_saldo():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        valor_str = request.form.get('valor')
        try:
            valor = float(valor_str)
            if valor <= 0:
                flash('O valor deve ser positivo.', 'danger')
                return redirect(url_for('adicionar_saldo'))
            
            # Aqui você integraria com a API de pagamento BTC
            # Por enquanto, vamos simular a geração de um pagamento
            # e redirecionar para uma página de confirmação
            session['valor_pendente'] = valor
            # Gere um ID de pagamento único ou use um identificador
            session['pagamento_id'] = f"PAG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Redireciona para a página de pagamento com QR Code
            return redirect(url_for('pagamento'))

        except (ValueError, TypeError):
            flash('Valor inválido.', 'danger')
            return redirect(url_for('adicionar_saldo'))

    return render_template('adicionar_saldo.html')

@app.route('/pagamento')
def pagamento():
    if 'usuario_logado' not in session or 'valor_pendente' not in session:
        return redirect(url_for('adicionar_saldo'))

    valor = session['valor_pendente']
    pagamento_id = session['pagamento_id']
    endereco_btc = "SEU_ENDERECO_BTC_AQUI" # Substitua pelo seu endereço real
    
    # Você pode usar uma biblioteca para gerar QR Code dinamicamente se preferir
    # Exemplo: qrcode.make(f"bitcoin:{endereco_btc}?amount={valor}").save('static/qrcode.png')
    
    # Por agora, usamos uma imagem estática
    qr_code_url = url_for('static', filename='qrcode-btc.jpg')

    return render_template('pagamento.html', valor=valor, pagamento_id=pagamento_id, qr_code_url=qr_code_url, endereco_btc=endereco_btc)

@app.route("/verificar_pagamento")
def verificar_pagamento():
    if "usuario_logado" not in session or "pagamento_id" not in session:
        return redirect(url_for("adicionar_saldo"))

    pagamento_id = session["pagamento_id"]
    valor_pendente = session.get("valor_pendente") # Usar .get() para segurança
    email_usuario = session["usuario_logado"]

    if valor_pendente is None:
        flash("Erro: Valor pendente não encontrado na sessão.", "danger")
        return redirect(url_for("adicionar_saldo"))

    # ==========================================================
    # AQUI ENTRA A LÓGICA REAL DE VERIFICAÇÃO COM A API DE PAGAMENTO BTC
    # ==========================================================
    # Exemplo SIMULADO: Suponha que a verificação foi bem-sucedida
    pagamento_confirmado = True # Mude para False para simular falha

    if pagamento_confirmado:
        try:
            # Busca o usuário no banco de dados
            usuario_atual = Usuario.query.filter_by(email=email_usuario).first()
            if usuario_atual:
                # Atualiza o saldo no banco de dados
                usuario_atual.saldo += valor_pendente
                db.session.commit()
                
                # Atualiza saldo na sessão
                session["saldo"] = usuario_atual.saldo
                
                # Limpa os dados de pagamento pendente da sessão
                session.pop("valor_pendente", None)
                session.pop("pagamento_id", None)

                flash(f"Pagamento de R$ {valor_pendente:.2f} confirmado! Saldo atualizado.", "success")
                return redirect(url_for("painel"))
            else:
                flash("Erro ao encontrar usuário para atualizar saldo.", "danger")
                # Mantém na página de verificação para tentar novamente ou contatar suporte
                return render_template("verificar_pagamento.html", pagamento_id=pagamento_id)
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar saldo no banco de dados: {e}", "danger")
            print(f"Erro DB verificar_pagamento: {e}")
            return render_template("verificar_pagamento.html", pagamento_id=pagamento_id)
    else:
        flash("Pagamento ainda não confirmado. Verifique novamente em alguns minutos.", "warning")
        return render_template("verificar_pagamento.html", pagamento_id=pagamento_id)

# ================== ROTA PARA SINCRONIZAR BINS ==================
@app.route('/sincronizar_bins_route') # Nome diferente da função
def sincronizar_bins_route():
    if not session.get('admin_logado'):
        return redirect(url_for('admin_login'))

    try:
        # Chama a função do script sincronizar_bins.py
        # Certifique-se que sincronizar_bins.py está no mesmo diretório ou no sys.path
        from sincronizar_bins import sincronizar_e_atualizar_bins
        sincronizar_e_atualizar_bins()
        flash('Sincronização de BINs concluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro durante a sincronização: {e}', 'danger')

    return redirect(url_for('admin_painel')) # Ou outra página admin

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



from sqlalchemy import func, case

def carregar_bins_com_contagem_db():
    """Consulta o banco de dados para obter os tipos de BINs disponíveis e a contagem de cartões disponíveis para cada.
    Retorna uma lista de dicionários para o catálogo.
    """
    try:
        # Consulta para agrupar por BIN, bandeira, nível, valor e contar cartões disponíveis
        contagem_bins = db.session.query(
            CartaoCompleto.bin_formatada,
            CartaoCompleto.bandeira,
            CartaoCompleto.nivel,
            CartaoCompleto.valor,
            func.count(CartaoCompleto.id).label("quantidade")
        ).filter(CartaoCompleto.disponivel == True).group_by(
            CartaoCompleto.bin_formatada,
            CartaoCompleto.bandeira,
            CartaoCompleto.nivel,
            CartaoCompleto.valor
        ).all()

        bins_para_catalogo = []
        for bin_info in contagem_bins:
            bins_para_catalogo.append({
                "bin": bin_info.bin_formatada,
                "bandeira": bin_info.bandeira.lower(), # Padroniza para minúsculas
                "nivel": bin_info.nivel,
                "valor": bin_info.valor,
                "quantidade": bin_info.quantidade
            })
        
        return bins_para_catalogo
    except Exception as e:
        print(f"Erro ao carregar bins do banco de dados: {e}")
        return []


from werkzeug.security import generate_password_hash, check_password_hash

from flask_sqlalchemy import SQLAlchemy


# Configuração do Banco de Dados SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'protegido', 'ladeusa.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)



# --- Modelos do Banco de Dados ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) # Armazenará o hash
    saldo = db.Column(db.Float, default=0.0)
    indicou = db.Column(db.String(10)) # Código de quem indicou
    codigo = db.Column(db.String(10), unique=True) # Código próprio para indicar
    pago = db.Column(db.Boolean, default=False)
    compras = db.relationship("Compra", backref="comprador", lazy=True)

class CartaoCompleto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cartao = db.Column(db.String(20), unique=True, nullable=False)
    mes = db.Column(db.String(2), nullable=False)
    ano = db.Column(db.String(4), nullable=False)
    cvv = db.Column(db.String(4), nullable=False)
    cpf = db.Column(db.String(14))
    nome = db.Column(db.String(100))
    bin_formatada = db.Column(db.String(6), nullable=False, index=True)
    bandeira = db.Column(db.String(20), nullable=False)
    nivel = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    disponivel = db.Column(db.Boolean, default=True, index=True)
    compra_id = db.Column(db.Integer, db.ForeignKey("compra.id"), nullable=True)

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    data_compra = db.Column(db.DateTime, default=datetime.utcnow)
    valor_total = db.Column(db.Float, nullable=False)
    cartoes = db.relationship("CartaoCompleto", backref="compra_info", lazy=True)

# --- Fim dos Modelos ---

# Função para criar o banco de dados (se não existir)
with app.app_context():
    db.create_all()

