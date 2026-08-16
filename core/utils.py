import os
import re

def sanitize_filename(filename: str) -> str:
    """
    Higieniza o nome de arquivo removendo caracteres especiais e prevenindo path traversal.
    Substitui qualquer caractere não alfanumérico (exceto '.', '-', '_') por '_'.
    """
    clean_name = os.path.basename(filename or "file")
    return re.sub(r'[^a-zA-Z0-9.\-_]', '_', clean_name)
