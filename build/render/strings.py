"""Localised layout labels (not story content). en-GB canonical, es-ES synced."""

UI: dict[str, dict[str, str]] = {
    "en-GB": {
        "glossary_title": "Who's Who and What's What",
        "group_place": "Places",
        "group_character": "Characters",
        "group_creature": "Creatures",
        "group_item": "Items",
        "group_term": "Words to Know",
        "sheet_title": "My Adventure Sheet",
        "sheet_name": "My name",
        "sheet_magic": "My magic (write or draw it)",
        "sheet_energy": "My energy stars (colour one in when you spend it)",
        "sheet_draw": "Draw your hero",
        "sheet_inventory": "What I am carrying",
        "sheet_notes": "Notes",
        "sheet_footer": "Here nobody loses. If a try does not work, find another way.",
    },
    "es-ES": {
        "glossary_title": "Quien es Quien y Que es Que",
        "group_place": "Lugares",
        "group_character": "Personajes",
        "group_creature": "Criaturas",
        "group_item": "Objetos",
        "group_term": "Palabras que conviene saber",
        "sheet_title": "Mi Ficha de Aventura",
        "sheet_name": "Mi nombre",
        "sheet_magic": "Mi magia (escribela o dibujala)",
        "sheet_energy": "Mis estrellas de energia (colorea una al gastarla)",
        "sheet_draw": "Dibuja a tu heroe o heroina",
        "sheet_inventory": "Lo que llevo conmigo",
        "sheet_notes": "Notas",
        "sheet_footer": "Aqui nadie pierde. Si algo no sale, se busca otra manera.",
    },
}


def ui(locale: str, key: str) -> str:
    """Return the label for a locale and key. Raises KeyError if either is absent."""
    return UI[locale][key]
