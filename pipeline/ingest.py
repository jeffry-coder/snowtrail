from utility.data_models import Video, Note
from utility.database_manager import DatabaseManager


class ContentProcessor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def process_files(self, course_name: str, files_to_upload: dict, status):
        for pdf_file in files_to_upload['pdf']:
            lecture_name, pdf_file_path = pdf_file
            status.update(label=f"Processing PDF: {pdf_file_path.name}")
            note = Note(file_path=str(pdf_file_path))
            note.process_content()
            data = [(chunk.text, chunk.page_num, pdf_file_path.name, lecture_name) for chunk in note.chunks]
            self.db_manager.insert_data(course_name, data, "pdf")
        
        for video_file in files_to_upload['video']:
            lecture_name, video_file_path = video_file
            status.update(label=f"Processing Video: {video_file_path.name}")
            video = Video(file_path=str(video_file_path))
            video.process_content()
            data = [(chunk.text, chunk.start, chunk.end, video_file_path.name, lecture_name) for chunk in video.chunks]
            self.db_manager.insert_data(course_name, data, "video")

        status.update(label="Creating search service")
        self.db_manager.create_search_service(course_name)
