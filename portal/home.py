import streamlit as st

st.title("Chat with your Lecture Series 😁")
st.write(
    '''This is a chatbot that can answer questions about your lecture series. 
    While displaying the section of videos or notes that are relevant to the question.'''
)
st.write('The lecture series is from MIT OCW [6.S897 Machine Learning for Healthcare]')
st.page_link(
    "https://ocw.mit.edu/courses/6-s897-machine-learning-for-healthcare-spring-2019/pages/syllabus/",
    label='Visit Source', icon='📖'
)
