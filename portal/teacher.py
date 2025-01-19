import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from pathlib import Path
from utility.database_manager import DatabaseManager
from utility.file_manager import FileManager
from pipeline.ingest import ContentProcessor


def sanitize_name(name: str) -> str:
    """Sanitize directory names by replacing invalid characters with underscores"""
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


def preview_file(file_path):
    if file_path.endswith(".mp4"):
        st.video(file_path)
    elif file_path.endswith(".pdf"):
        with st.container(height=600):
            pdf_viewer(file_path)


def show_file_btn(file_path, processed, files_to_upload, is_admin=False, key=None):
    """Modified to handle both admin and viewer modes"""
    file_name = file_path.name
    lecture_name = file_path.parent.name
    status = "✅" if processed else "⏳"

    if is_admin:
        if file_name.endswith(".pdf") and not processed:
            files_to_upload["pdf"].append((lecture_name, file_path))
        elif file_name.endswith(".mp4") and not processed:
            files_to_upload["video"].append((lecture_name, file_path))

    if st.button(f"{status} {file_name}", key=key):
        st.session_state.selected_file = str(file_path)
        st.rerun()


def teacher_portal():
    # Initialize authentication state
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    # Admin login section in sidebar
    with st.sidebar:
        if not st.session_state['authenticated']:
            st.title("Admin Login")
            password = st.text_input("Enter Password", type="password")
            if st.button("Login"):
                # Replace 'your_password' with your desired admin password
                if password == st.secrets['connections']['snowflake']['password']:
                    st.session_state['authenticated'] = True
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            st.success("Logged in as Admin")
            if st.button("Logout"):
                st.session_state['authenticated'] = False
                st.rerun()

    is_admin = st.session_state['authenticated']
    
    st.title("Teacher Portal - Course Management")
    if is_admin:
        st.write("*Admin Mode - Full Access*")
    else:
        st.write("*Viewer Mode - Read Only Access*")

    file_manager = FileManager()
    db_manager = st.session_state.db_manager
    content_processor = ContentProcessor(db_manager)

    course_names = list(st.session_state.course_structure.keys())
    
    # Create new course (admin only)
    if is_admin:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                new_course = st.text_input("Create New Course", key="new_course_input")
            with col2:
                if st.button("Create Course", key="create_course_btn"):
                    if new_course and new_course not in course_names:
                        new_course = sanitize_name(new_course)
                        file_manager.create_course(new_course)
                        db_manager.create_table(new_course)
                        st.session_state.course_structure[new_course] = {}
                        st.success(f"Created course: {new_course}")
                        st.rerun()

    if not course_names:
        st.info("No courses available yet.")
        return

    # Tabs for courses
    tabs = st.tabs(course_names)

    for idx, tab in enumerate(tabs):
        course = course_names[idx]

        with tab:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Course Content")

                # Lecture selection for file upload (admin only)
                if is_admin:
                    lecture_names = list(st.session_state.course_structure[course].keys())
                    lecture = st.selectbox(
                        "Select Lecture",
                        [""] + lecture_names,
                        format_func=lambda x: "Select a lecture" if x == "" else x,
                        key=f"lecture_select_{course}"
                    )

                    # File upload section
                    if lecture:
                        uploaded_files = st.file_uploader(
                            f"Upload files to {lecture}",
                            type=["mp4", "pdf"],
                            accept_multiple_files=True,
                            key=f"file_uploader_{course}_{lecture}"
                        )
                        if uploaded_files:
                            for file in uploaded_files:
                                file_manager.save_uploaded_file(course, lecture, file)
                                if file.name not in [
                                    f[0]
                                    for f in st.session_state.course_structure[course][
                                        lecture
                                    ]
                                ]:
                                    st.session_state.course_structure[course][
                                        lecture
                                    ].append((file.name, False))
                            st.success(f"Uploaded {len(uploaded_files)} files to {lecture}")

                with st.container(height=500):
                    col3, col4 = st.columns([4, 1])
                    with col3:
                        st.write("🎥 Lectures (Videos/Notes)")
                        if is_admin:
                            st.write(f"*Status: ✅ = Processed | ⏳ = Pending Processing*")
                    with col4:
                        if is_admin and st.button("➕", help="Add new lecture", key=f"add_lecture_btn_{course}"):
                            st.session_state[f"show_lecture_input_{course}"] = True

                    # New lecture input expander (admin only)
                    if is_admin and st.session_state.get(f"show_lecture_input_{course}", False):
                        with st.expander("New Lecture", expanded=True):
                            new_lecture = st.text_input("Lecture Name", key=f"new_lecture_input_{course}")
                            if new_lecture:
                                new_lecture = sanitize_name(new_lecture)
                                file_manager.create_lecture(course, new_lecture)
                                st.session_state.course_structure[course][
                                    new_lecture
                                ] = []
                                st.session_state[f"show_lecture_input_{course}"] = False
                                st.rerun()

                    # Display lectures and their files
                    files_to_upload = {"video": [], "pdf": []}
                    for lecture_name, files in st.session_state.course_structure[
                        course
                    ].items():
                        expand = True if files else False
                        with st.expander(f"📚 {lecture_name}", expanded=expand):
                            if files:
                                for i in range(0, len(files), 2):
                                    col5, col6 = st.columns(2)
                                    with col5:
                                        file_path = file_manager.get_file_path(
                                            course, lecture_name, files[i][0]
                                        )
                                        show_file_btn(
                                            file_path, files[i][1], files_to_upload, is_admin,
                                            key=f"file_btn_{course}_{lecture_name}_{i}"
                                        )

                                    if i + 1 < len(files):
                                        with col6:
                                            file_path = file_manager.get_file_path(
                                                course, lecture_name, files[i + 1][0]
                                            )
                                            show_file_btn(
                                                file_path,
                                                files[i + 1][1],
                                                files_to_upload,
                                                is_admin,
                                                key=f"file_btn_{course}_{lecture_name}_{i+1}"
                                            )
                            else:
                                st.info("This lecture has no content yet")

                # Action buttons (admin only)
                if is_admin:
                    col7, col8 = st.columns(2)
                    with col7:
                        if st.button("Process Lectures", key=f"process_btn_{course}"):
                            if files_to_upload['pdf'] or files_to_upload['video']:
                                with st.status("Processing files...", expanded=False) as status:
                                    content_processor.process_files(
                                        course, files_to_upload, status
                                    )
                                # Update file status after processing
                                for lecture in st.session_state.course_structure[course]:
                                    db_files = db_manager.get_files_in_lecture(course, lecture)
                                    st.session_state.course_structure[course][lecture] = [
                                        (file_name, file_name in db_files)
                                        for file_name, _ in st.session_state.course_structure[course][lecture]]
                                st.success("Files processed successfully!")
                                st.rerun()
                            else:
                                st.warning("No files to process")

                    with col8:
                        if st.button("Delete Course", key=f"delete_btn_{course}"):
                            file_manager.delete_course(course)
                            db_manager.delete_collection(course)
                            del st.session_state.course_structure[course]
                            st.success(f"Deleted course: {course}")
                            st.rerun()

            with col2:
                st.subheader("File Preview")
                if (
                    "selected_file" in st.session_state
                    and Path(st.session_state.selected_file).parent.parent.name
                    == course
                ):
                    preview_file(st.session_state.selected_file)
                else:
                    st.info("Select a file from the left panel to preview")


teacher_portal()
