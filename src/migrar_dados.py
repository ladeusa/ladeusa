#!/usr/bin/env python3
import sys
import os
import json
from werkzeug.security import generate_password_hash

# Garante que o diretório pai (onde está main.py) esteja no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa o app e o db de main.py
# ATENÇÃO: Isso pode causar problemas se main.py tiver código que executa na importação.
# Idealmente, a criação do app e db seria movida para um arquivo separado (ex: app_factory.py)
# Mas para simplificar, vamos tentar importar diretamente.
try:
    from main import app, db, Usuario, CartaoCompleto, Compra
except ImportError as e:
    print(f"Erro ao importar de main.py: {e}")
    print("Certifique-se de que main.py está no mesmo diretório e não tem erros de sintaxe.")
    sys.exit(1)

# Caminhos para os arquivos JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTEGIDO_DIR = os.path.join(BASE_DIR, 'protegido')
USUARIOS_FILE = os.path.join(PROTEGIDO_DIR, 'usuarios.json')
CARTOES_COMPLETOS_FILE = os.path.join(PROTEGIDO_DIR, 'cartoes_completos.json')
BINS_FILE = os.path.join(PROTEGIDO_DIR, 'bins.json') # Usado para referência, não migrado diretamente

def carregar_json_local(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON: {file_path}")
            return []
    print(f"Arquivo não encontrado: {file_path}")
    return []

def migrar_dados():
    print("Iniciando migração de dados...")
    usuarios_json = carregar_json_local(USUARIOS_FILE)
    cartoes_json = carregar_json_local(CARTOES_COMPLETOS_FILE)
    rejeitados_file_path = os.path.join(PROTEGIDO_DIR, 'migracao_rejeitados.txt')
    cartoes_adicionados = 0
    cartoes_rejeitados = 0
    cartoes_duplicados = 0

    with open(rejeitados_file_path, 'w', encoding='utf-8') as f_rejeitados:
        f_rejeitados.write("Relatório de Cartões Rejeitados na Migração\n")
        f_rejeitados.write("=============================================\n\n")

        with app.app_context():
            print("Migrando usuários...")
            # ... (código de migração de usuários permanece o mesmo) ...
            for user_data in usuarios_json:
                # Verifica se o usuário já existe pelo email
                existente = Usuario.query.filter_by(email=user_data.get('email')).first()
                if existente:
                    # print(f"Usuário {user_data.get('email')} já existe. Pulando.")
                    continue

                # Gera hash da senha se ela existir e não parecer já hasheada
                senha_hash = user_data.get('password', '')
                if senha_hash and not senha_hash.startswith('pbkdf2:sha256:'):
                    try:
                        senha_hash = generate_password_hash(senha_hash)
                    except Exception as e:
                        print(f"Erro ao gerar hash para usuário {user_data.get('email')}: {e}. Usando hash vazio.")
                        senha_hash = generate_password_hash('')

                novo_usuario = Usuario(
                    username=user_data.get('username'),
                    email=user_data.get('email'),
                    password=senha_hash,
                    saldo=float(user_data.get('saldo', 0.0)),
                    indicou=user_data.get('indicou'),
                    codigo=user_data.get('codigo'),
                    pago=user_data.get('pago', False)
                )
                db.session.add(novo_usuario)
                # print(f"Usuário {novo_usuario.email} adicionado.")

            try:
                db.session.commit()
                print("Usuários commitados.")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao commitar usuários: {e}")
                f_rejeitados.write(f"ERRO CRÍTICO AO COMMITAR USUÁRIOS: {e}\n")
                return # Aborta se não conseguir salvar usuários

            print("Migrando cartões completos...")
            for cartao_data in cartoes_json:
                cartao_numero = cartao_data.get('cartao')
                # Verifica se o cartão já existe
                existente = CartaoCompleto.query.filter_by(cartao=cartao_numero).first()
                if existente:
                    # print(f"Cartão {cartao_numero} já existe. Pulando.")
                    cartoes_duplicados += 1
                    continue

                # *** CHECK FOR REQUIRED FIELDS ***
                bin_formatada_valor = cartao_data.get('bin')
                mes_valor = cartao_data.get('mes')
                ano_valor = cartao_data.get('ano')
                cvv_valor = cartao_data.get('cvv')
                bandeira_valor = cartao_data.get('bandeira')
                nivel_valor = cartao_data.get('nivel')
                valor_cartao = cartao_data.get('valor')

                campos_faltando = []
                if not bin_formatada_valor: campos_faltando.append('bin')
                if not cartao_numero: campos_faltando.append('cartao')
                if not mes_valor: campos_faltando.append('mes')
                if not ano_valor: campos_faltando.append('ano')
                if not cvv_valor: campos_faltando.append('cvv')
                if not bandeira_valor: campos_faltando.append('bandeira')
                if not nivel_valor: campos_faltando.append('nivel')
                if valor_cartao is None: campos_faltando.append('valor')

                if campos_faltando:
                    motivo = f"Campos obrigatórios faltando: {', '.join(campos_faltando)}"
                    print(f"AVISO: Cartão {cartao_numero or '(sem número)'} ignorado. Motivo: {motivo}")
                    f_rejeitados.write(f"Cartão: {cartao_numero or '(sem número)'}\n")
                    f_rejeitados.write(f"Motivo: {motivo}\n")
                    f_rejeitados.write(f"Dados: {cartao_data}\n---\n")
                    cartoes_rejeitados += 1
                    continue
                # *** END CHECK ***

                novo_cartao = CartaoCompleto(
                    cartao=cartao_numero,
                    mes=mes_valor,
                    ano=ano_valor,
                    cvv=cvv_valor,
                    cpf=cartao_data.get('cpf'),
                    nome=cartao_data.get('nome'),
                    bin_formatada=bin_formatada_valor,
                    bandeira=bandeira_valor,
                    nivel=nivel_valor,
                    valor=float(valor_cartao),
                    disponivel=cartao_data.get('disponivel', True)
                )
                db.session.add(novo_cartao)
                # print(f"Cartão {novo_cartao.cartao} adicionado.")
                cartoes_adicionados += 1

            try:
                db.session.commit()
                print(f"Cartões commitados. Adicionados: {cartoes_adicionados}, Rejeitados: {cartoes_rejeitados}, Duplicados: {cartoes_duplicados}")
                f_rejeitados.write(f"\nResumo:\nCartões Adicionados: {cartoes_adicionados}\nCartões Rejeitados: {cartoes_rejeitados}\nCartões Duplicados Ignorados: {cartoes_duplicados}\n")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao commitar cartões: {e}")
                f_rejeitados.write(f"ERRO CRÍTICO AO COMMITAR CARTÕES: {e}\n")

    print(f"Migração de dados concluída. Relatório de rejeitados salvo em: {rejeitados_file_path}")

if __name__ == "__main__":
    migrar_dados()

