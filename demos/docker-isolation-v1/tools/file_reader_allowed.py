def file_reader_allowed() -> str:
    with open(FILE_PATH, "r") as f:
        return f.read()
