# -*- coding: utf-8 -*-
"""
@author: Rafael Dana Christof
"""
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Table
import cv2
import numpy as np
import PySimpleGUI as sg
import re
import concurrent.futures


def URLSerch(cardName, qntCard, pitch_value):
    url_json = 'https://raw.githubusercontent.com/the-fab-cube/flesh-and-blood-cards/develop/json/english/card.json'

    def SearchImageURL(json_url, nome, qntCard, pitch_value):
        response = requests.get(json_url)

        if response.status_code == 200:
            content_data = response.json()
            urls_de_imagem = []

            # Converter o nome de busca para minúsculas
            nome_minusculo = nome.lower()

            for item in content_data:
                if ("name" in item and item["name"].lower() == nome_minusculo) and (("pitch" in item and item["pitch"].lower() == str(pitch_value)) if pitch_value else True):
                    # Se o nome corresponde, adiciona todas as URLs de imagem associadas
                    for printing in item.get("printings", []):
                        image_url = printing.get("image_url")
                        if image_url:
                            urls_de_imagem.extend([image_url] * qntCard)
                            break

            return urls_de_imagem
        else:
            print(
                f"Erro ao obter o arquivo JSON. Código de status: {response.status_code}")
            return None

    imageURL = SearchImageURL(url_json, cardName, qntCard, pitch_value)

    if imageURL:
        # print(f"URLs de imagem para '{cardName}':")
        # for url in imageURL:
        #     print(url)
        pass

    else:
        print(f"'{cardName}' não encontrado.")
        return 0

    return imageURL


def obter_tamanho_imagem(url):
    response = requests.get(url)
    if response.status_code == 200:
        arr = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        return img.shape[1], img.shape[0]  # Retorna largura e altura da imagem


def extract_pitch_value(color):
    if color == 'red':
        return 1
    elif color == 'yellow':
        return 2
    elif color == 'blue':
        return 3
    else:
        return None  # Retornar 0 para cores não especificadas


def criar_pdf_com_imagens(lista_urls_imagens, nome_arquivo_pdf):
    doc = SimpleDocTemplate(nome_arquivo_pdf, pagesize=A4,
                            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []

    border_size = 144
    # Define a largura total da área de trabalho
    max_width = A4[0] - border_size
    max_images_per_row = 3  # Número máximo de imagens por linha

    # Agrupa as imagens em linhas
    rows = [lista_urls_imagens[i:i + max_images_per_row]
            for i in range(0, len(lista_urls_imagens), max_images_per_row)]

    for row in rows:
        row_elements = []
        for url in row:
            width, height = obter_tamanho_imagem(url)

            if width and height:
                img_ratio = width / height

                if width > max_width / max_images_per_row:
                    width = max_width / max_images_per_row
                    height = width / img_ratio

                image = Image(url, width=width, height=height)
                s = Spacer(width=5, height=5)
                row_elements.append(image)

        # Preenche a linha com células vazias para manter a estrutura da grade
        if len(row_elements) < max_images_per_row:
            remaining_cells = max_images_per_row - len(row_elements)
            row_elements.extend([None] * remaining_cells)

        elements.append(row_elements)

    # Cria um Table para posicionar as imagens em uma grade
    t = Table(elements, colWidths=[max_width / max_images_per_row for _ in range(
        max_images_per_row)], rowHeights=[height for _ in range(len(elements))], hAlign='LEFT')
    doc.build([t])

    print(f"PDF salvo com sucesso como '{nome_arquivo_pdf}'")


def main():
    url_list = []

    layout = [
        [sg.Text()],
        [sg.Multiline(size=(100, 30))],
        [sg.Submit()]
    ]

    window = sg.Window("Proxy Generator", layout=layout, size=(800, 570))

    events, values = window.read()
    window.close()
    print(events)

    nomeQualquer = values[0]
    linhas = nomeQualquer.splitlines()

    for linha in linhas:
        match = re.match(
            r'(?:[\(\[]?(\d+)[\]\)]? )?(.*?)(?: \((red|blue|yellow)\)| (red|blue|yellow)|\[(red|blue|yellow)\])?\s*$', linha)
        if match:
            numero = int(match.group(1) or 1)
            nomeCarta = match.group(2).strip()
            color = match.group(3) or match.group(4) or match.group(5)
            pitch_value = extract_pitch_value(color)
        else:
            print("Padrão não encontrado")
            continue

        # Adiciona um tuple com os parâmetros necessários para URLSerch
        url_list.append((nomeCarta, numero, pitch_value))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Usando map para aplicar URLSerch em paralelo nos itens da lista
        results = executor.map(lambda x: URLSerch(*x), url_list)

        urls_de_imagem = [url for result in results if result != 0 for url in result]

    criar_pdf_com_imagens(urls_de_imagem, "teste.pdf")


if __name__ == '__main__':
    main()
