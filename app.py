import streamlit as st
from utility.file_manager import FileManager
from utility.database_manager import DatabaseManager

import logging

for module in ["snowflake.connector", "snowflake.core", "snowflake.snowpark"]:
    logging.getLogger(module).setLevel(logging.ERROR)

st.set_page_config(page_title="RAG & ROLL", page_icon="💬", layout="wide")

if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager(st.connection("snowflake"))

if "course_structure" not in st.session_state:
    file_manager = FileManager()

    st.session_state.course_structure = {}
    course_names = file_manager.get_all_courses()

    for course in course_names:
        # Initialize the course dictionary first
        st.session_state.course_structure[course] = {}
        lecture_names = file_manager.get_course_lectures(course)
        for lecture in lecture_names:
            local_files = file_manager.get_files_in_lecture(course, lecture)
            if local_files:
                db_files = st.session_state.db_manager.get_files_in_lecture(course, lecture)

                # Create list of tuples with (file_name, processed_status)
                file_status = [
                    (file_path.name, file_path.name in db_files)
                    for file_path in local_files
                ]
                st.session_state.course_structure[course][lecture] = file_status
            else:
                st.session_state.course_structure[course][lecture] = []

home_page = st.Page("portal/home.py", title="Home", icon="🏠")
teacher_page = st.Page("portal/teacher.py", title="Teacher", icon="👨‍🏫")
student_page = st.Page("portal/student.py", title="Student", icon="👩‍🎓")

navigation = st.navigation(
    {"Home": [home_page], "E-Learning Portal": [teacher_page, student_page]},
    expanded=True,
)
navigation.run()
