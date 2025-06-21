"""
Skeleton for video analyzer models.
Define data structures and models used for video analysis.
"""


class Video:
    def __init__(self, id: str, title: str, file_path: str):
        self.id = id
        self.title = title
        self.file_path = file_path

    def __repr__(self):
        return f"Video(id={self.id}, title={self.title}, file_path={self.file_path})"
