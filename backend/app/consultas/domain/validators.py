def buscar_normalizado(texto: str) -> str:
    valor = ' '.join(texto.strip().split())
    if len(valor) < 2 or len(valor) > 100 or not any(caracter.isalnum() for caracter in valor):
        raise ValueError('Escribe al menos dos caracteres para buscar.')
    return valor
