import json
import os

# Caminhos dos arquivos
CAMINHO_CARTOES = 'protegido/cartoes_completos.json'
CAMINHO_BINS = 'protegido/bins.json'

def sincronizar_bins():
    if not os.path.exists(CAMINHO_CARTOES):
        print("Arquivo cartoes_completos.json não encontrado.")
        return

    # Carrega os cartões completos
    with open(CAMINHO_CARTOES, 'r', encoding='utf-8') as f:
        cartoes = json.load(f)

    print(f"Total de cartões encontrados: {len(cartoes)}")

    # Cria um dicionário para evitar BINs duplicadas
    bins_dict = {}

    for cartao in cartoes:
        bin_num = cartao.get('cartao', '')[:6]

        if not bin_num:
            continue

        # Se a BIN ainda não foi registrada, adiciona
        if bin_num not in bins_dict:
            bins_dict[bin_num] = {
                "bin": bin_num,
                "bandeira": cartao.get("bandeira", "").upper(),
                "nivel": cartao.get("nivel", "").upper(),
                "valor": cartao.get("valor", 0)
            }

    # Converte os valores únicos para lista
    lista_bins = list(bins_dict.values())

    # Salva no bins.json
    with open(CAMINHO_BINS, 'w', encoding='utf-8') as f:
        json.dump(lista_bins, f, indent=4, ensure_ascii=False)

    print(f"{len(lista_bins)} BINs sincronizadas com sucesso!")

if __name__ == "__main__":
    sincronizar_bins()
