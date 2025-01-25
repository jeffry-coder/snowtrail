import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from utility.file_manager import FileManager
from pipeline.retrieve import ContentRetriever


@st.cache_resource
def init_snow_session():
    return st.connection('snowflake').session()

@st.dialog("📄 Full PDF Viewer", width="large")
def full_pdf_viewer(pdf_path, page_num):
    with st.container(height=600):
        pdf_viewer(
            str(pdf_path),
            scroll_to_page=page_num,
            key=f"full_view_pdf_{pdf_path}_{page_num}",
        )


def student_portal():
    st.sidebar.title("Student's Portal - Lecture Q&A")

    course_names = list(st.session_state.course_structure.keys())

    if not course_names:
        st.info("No lecture series available yet. Please check back later!")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "artifacts" not in st.session_state:
        st.session_state.artifacts = {}

    course = st.sidebar.selectbox("Select Course", course_names)
    clear_chat = st.sidebar.button("Clear Chat")

    if clear_chat:
        st.session_state.messages = []
        st.session_state.artifacts = {}

    if (
        "content_retriever" not in st.session_state
        or st.session_state.content_retriever.course_name != course
    ):
        st.session_state.available_lectures = []
        st.session_state.selected_lectures = []
        for lecture, files in st.session_state.course_structure[course].items():
            for file in files:
                _, processed = file
                if processed:
                    st.session_state.available_lectures.append(lecture)
                    break
        
        session = init_snow_session()
        st.session_state.content_retriever = ContentRetriever(session, course)

    file_manager = FileManager()

    # Main content area
    col1, col2 = st.columns([3, 2])

    # Chat Interface (Left Column)
    with col1:
        st.subheader("Student's Portal - Lecture Q&A")
        with st.container(height=550):
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.chat_message("user", avatar="👤").write(msg["content"])
                else:
                    st.chat_message("assistant", avatar="🤖").write(msg["content"])

            user_msg = st.empty()
            ai_msg = st.empty()

        st.session_state.selected_lectures = st.multiselect(
            "Lectures to include on search",
            options=st.session_state.available_lectures,
            default=st.session_state.available_lectures,
            label_visibility="collapsed",
        )

        if query := st.chat_input("Ask a question about the lecture series"):
            user_msg.chat_message("user", avatar="👤").write(query)

            with ai_msg.chat_message("assistant", avatar="🤖"):
                with st.spinner("Searching for relevant documents.."):
                    if st.session_state.messages:
                        context_query = (
                            st.session_state.content_retriever.contextualize(
                                query, st.session_state.messages
                            )
                        )
                        documents = st.session_state.content_retriever.retrieve(
                            context_query, st.session_state.selected_lectures
                        )
                    else:
                        documents = st.session_state.content_retriever.retrieve(
                            query, st.session_state.selected_lectures
                        )

                    if documents["pdf"]:
                        pdf_doc = documents["pdf"][0]
                        st.session_state.artifacts["pdf"] = {
                            "text": pdf_doc["text"],
                            "page_num": int(pdf_doc["page_num"]), 
                            "file_path": file_manager.get_file_path(
                                course, pdf_doc["lecture_name"], pdf_doc["file_name"]
                            ),
                            "lecture_name": pdf_doc["lecture_name"],
                        }
                    else:
                        st.session_state.artifacts["pdf"] = None

                    if documents["video"]:
                        video_doc = documents["video"][0]
                        st.session_state.artifacts["video"] = {
                            "text": video_doc["text"],
                            "start_time": float(video_doc["start_time"]),
                            "end_time": float(video_doc["end_time"]),
                            "file_path": file_manager.get_file_path(
                                course,
                                video_doc["lecture_name"],
                                video_doc["file_name"],
                            ),
                            "lecture_name": video_doc["lecture_name"],
                        }
                    else:
                        st.session_state.artifacts["video"] = None

                    response_stream = st.session_state.content_retriever.complete(
                        query, documents, st.session_state.messages
                    )

                response_str = st.write_stream(response_stream)

            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.messages.append(
                {"role": "assistant", "content": response_str}
            )

    # Artifacts Display (Right Column)
    with col2:
        if st.session_state.artifacts:
            pdf_artifact = st.session_state.artifacts["pdf"]
            if pdf_artifact:
                pdf_path = str(pdf_artifact["file_path"])
                page_num = pdf_artifact["page_num"]

                col3, col4 = st.columns([4, 1])
                with col3:
                    st.write(f"📄 {pdf_artifact['lecture_name']}")
                with col4:
                    if st.button("🔍", help="Open full page PDF"):
                        full_pdf_viewer(pdf_path, page_num)

                with st.container(height=300):
                    pdf_viewer(pdf_path, scroll_to_page=page_num, key=f"preview_pdf_{pdf_path}_{page_num}")
            else:
                st.info("This lecture does not contain notes")

            video_artifact = st.session_state.artifacts["video"]
            if video_artifact:
                st.write(f"🎥 {video_artifact['lecture_name']}")
                start_time = video_artifact["start_time"]
                end_time = video_artifact["end_time"]

                st.video(
                    str(video_artifact["file_path"]),
                    start_time=start_time,
                    end_time=end_time,
                )
                with st.expander("🔍 Video Transcript"):
                    start_hours = int(start_time // 3600)
                    start_minutes = int((start_time % 3600) // 60)
                    start_seconds = int(start_time % 60)

                    end_hours = int(end_time // 3600)
                    end_minutes = int((end_time % 3600) // 60)
                    end_seconds = int(end_time % 60)

                    st.write(
                        f"**Timestamp**: {start_hours:02d}:{start_minutes:02d}:{start_seconds:02d} - {end_hours:02d}:{end_minutes:02d}:{end_seconds:02d}"
                    )

                    st.write(video_artifact["text"])
            else:
                st.info("This lecture does not contain a video")
        else:
            st.info("Chat with us to display relevant artifacts")


student_portal()
