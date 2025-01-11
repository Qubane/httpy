class PageManager:
    """
    Controls access to pages and page indexing
    """

    # 'web_path': {"en": "path", "ru": "path"}
    path_tree: dict[str, dict]

