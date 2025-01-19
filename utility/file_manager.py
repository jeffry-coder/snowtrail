from pathlib import Path
import shutil


class FileManager:
    def __init__(self):
        self.base_path = Path("courses")

    def create_course(self, course_name: str) -> Path:
        """Create a new course directory"""
        course_path = self.base_path / course_name
        if not course_path.exists():
            course_path.mkdir(parents=True)
        return course_path

    def create_lecture(self, course_name: str, lecture_name: str) -> Path:
        """Create a new lecture directory within a course"""
        course_path = self.base_path / course_name
        lecture_path = course_path / lecture_name
        if not lecture_path.exists():
            lecture_path.mkdir(parents=True)
        return lecture_path

    def get_all_courses(self) -> list[str]:
        """Get list of all course names"""
        if not self.base_path.exists():
            return []
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]

    def get_course_lectures(self, course_name: str) -> list[str]:
        """Get list of lecture names for a course"""
        course_path = self.base_path / course_name
        if not course_path.exists():
            return []
        return [d.name for d in course_path.iterdir() if d.is_dir()]

    def delete_course(self, course_name: str) -> None:
        """Delete an entire course directory"""
        course_path = self.base_path / course_name
        if course_path.exists():
            shutil.rmtree(course_path)

    def delete_lecture(self, course_name: str, lecture_name: str) -> None:
        """Delete a specific lecture directory"""
        lecture_path = self.base_path / course_name / lecture_name
        if lecture_path.exists():
            shutil.rmtree(lecture_path)

    def save_uploaded_file(
        self, course_name: str, lecture_name: str, uploaded_file
    ) -> None:
        """Save an uploaded file to the appropriate lecture directory"""
        lecture_path = self.base_path / course_name / lecture_name
        
        # Create lecture folder if it doesn't exist
        if not lecture_path.exists():
            self.create_lecture(course_name, lecture_name)
            
        with open(lecture_path / uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

    def get_files_in_lecture(self, course_name: str, lecture_name: str) -> list[Path]:
        """Get all files in a lecture"""
        lecture_path = self.base_path / course_name / lecture_name
        return list(lecture_path.glob("*.mp4")) + list(lecture_path.glob("*.pdf")) # exclude audio mp3

    def get_file_path(self, course_name: str, lecture_name: str, file_name: str) -> Path:
        """Get the path to a specific file"""
        lecture_path = self.base_path / course_name / lecture_name
        file_path = lecture_path / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path
