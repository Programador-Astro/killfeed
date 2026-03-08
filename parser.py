import re

def parse_killfeed(texto: str):

    texto = texto.replace("$", "").strip()

    pattern = r"(.*?) apagou (.*?) - (.*?) - (\d+m)"

    match = re.search(pattern, texto)

    if match:
        return {
            "killer": match.group(1).strip(),
            "vitima": match.group(2).strip(),
            "arma": match.group(3).strip(),
            "distancia": match.group(4).strip()
        }

    return None