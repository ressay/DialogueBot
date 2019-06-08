class DialogueError(Exception):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.reward = -1


class FileNameExistsError(DialogueError):
    def __init__(self, path, name, type_of_existing_file, *args) -> None:
        super().__init__(*args)
        self.path = path
        self.name = name
        self.type_of_file = type_of_existing_file
        self.reward = -0.1


class FileDoesNotExist(DialogueError):
    def __init__(self, file_name, *args) -> None:
        super().__init__(*args)
        self.file_name = file_name


class RemoveCurrentDirError(DialogueError):
    def __init__(self, file_name, is_ancestor_of_current_dir, *args) -> None:
        super().__init__(*args)
        self.file_name = file_name
        self.is_ancestor = is_ancestor_of_current_dir
        self.reward = -0.1


class MoveFileInsideItself(DialogueError):
    def __init__(self, file_name, path, dest_path, *args) -> None:
        super().__init__(*args)
        self.file_name = file_name
        self.path = path
        self.dest_path = dest_path
        self.reward = -0.1
