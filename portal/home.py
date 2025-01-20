import streamlit as st

st.title("Chat with your Lecture Series 😁")
st.write(
    """This is a chatbot that can answer questions about your lecture series. 
    While displaying the section of videos or notes that are relevant to the question."""
)
st.write("The lecture series is from MIT OCW [6.S897 Machine Learning for Healthcare]")
st.page_link(
    "https://ocw.mit.edu/courses/6-s897-machine-learning-for-healthcare-spring-2019/pages/syllabus/",
    label="Visit Source",
    icon="📖",
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Instructions for Teacher")
    st.markdown(
        """
1. **Logging In**
   - Navigate to the **Teacher's Portal**.
   - Enter the admin password in the sidebar to access admin features.
   - If you’re not an admin, you can still view content in **Viewer Mode**.

2. **Creating and Managing Courses**
   - **Create a New Course**:
     - Enter the desired course name in the input field and click "Create Course."
   - **Add Lectures**:
     - Click "➕" in the course tab to add a new lecture to the selected course.

3. **Uploading Lecture Materials**
   - Select a lecture and upload files (PDFs or MP4s) to associate them with the lecture.
   - Uploaded files are listed under the corresponding lecture.

4. **Processing Files**
   - Click "Process Lectures" to prepare the uploaded files for student access.
   - Processed files are marked with a ✅; unprocessed files show ⏳.

5. **Previewing Files**
   - Select a file from the lecture list to preview it in the **File Preview** section.

6. **Managing Courses**
   - Delete a course by clicking "Delete Course" in the corresponding tab.
   - All associated lectures and files will also be removed.
                """
    )

with col2:
    st.subheader("Instructions for Student")
    st.markdown(
        """
1. **Accessing the Student's Portal**
   - Open the app and navigate to the **Student's Portal** section.
   - Use the sidebar to select a course from the available list.

2. **Features**
   - **Lecture Q&A Chat**:
     - Use the chat interface to ask questions about the selected course's lecture series.
     - You can also filter the lectures you want to talk about from the menu above chat input. 
   - **Artifacts (Documents and Videos)**:
     - Relevant PDFs and videos are displayed based on your query.
     - Click on "🔍" to open a full PDF viewer for detailed reading.
     - Watch video clips directly in the app, with timestamps and transcripts provided.

3. **Additional Options**
   - **Clear Chat**: Reset the chat by clicking the "Clear Chat" button in the sidebar.
                """
    )
