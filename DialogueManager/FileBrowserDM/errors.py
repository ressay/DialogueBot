


class FileNameExistsError(Exception):
    def __init__(self,path,name,t1,t2, *args) -> None:
        super().__init__(*args)
        #TODO FINISH PARAMETERS


class FileDoesNotExist(Exception):
    def __init__(self, file_name, *args) -> None:
        super().__init__(*args)

class RemoveCurrentDirError(Exception):
    def __init__(self, file_name, *args) -> None:
        super().__init__(*args)
