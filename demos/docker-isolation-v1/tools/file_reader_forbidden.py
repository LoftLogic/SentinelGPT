def file_reader_forbidden() -> str:
    with open(FILE_PATH, "r") as f:
        return f.read()
