try:
    from cuvis_il import cuvis_il # type: ignore
except ImportError as e:
    if e.msg.startswith('DLL'):
        raise
    import cuvis_il # type: ignore