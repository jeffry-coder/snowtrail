from snowflake.cortex import Complete
from snowflake.snowpark import Session
from snowflake.core import Root

class ContentRetriever():

    def __init__(
        self,
        session: Session,
        course_name: str,
        model_name: str = "mistral-large2",
        msg_limit: int = 6,
    ):
        self.course_name = course_name
        self.model_name = model_name
        self.msg_limit = msg_limit
        self.system_prompt = """
        You are a knowledgeable teaching assistant helping university students learn from their lecture materials. Use the provided context from lecture videos and notes to answer questions. If the context doesn't contain relevant information, simply state that you don't know. Keep responses friendly but concise, using no more than three sentences. For general greetings or casual conversation, respond naturally without needing context.
        """

        root = Root(session)
        db, schema = (
            session.get_current_database(),
            session.get_current_schema(),
        )

        source = root.databases[db].schemas[schema]
        self.pdf_service = source.cortex_search_services[f'{course_name}_pdf']
        self.video_service = source.cortex_search_services[f'{course_name}_video']

        base_columns = ["text", "file_name", "lecture_name"]
        self.pdf_columns = base_columns + ["page_num"]
        self.video_columns = base_columns + ["start_time", "end_time"]

    def contextualize(self, query: str, chat_history: list[dict]) -> str:
        """
        Contextualize the query with the chat history. 
        Limit is the number of most recent messages to include in the chat history.
        """
        context_prompt = """
        Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is.
        """
        messages = [{"role": "system", "content": context_prompt}]
        messages.extend(chat_history[-self.msg_limit:])
        messages.append({"role": "user", "content": f'Question to reformulate: {query}'})
        return Complete(model=self.model_name, prompt=messages)

    def complete(self, query: str, documents: dict, chat_history: list[dict]):
        """
        Get a completion from the Snowflake Cortex model.
        Chat history must contain a role key and a content key.
        The role key must be either "system", "user", or "assistant".
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(chat_history[-self.msg_limit :])
        prompt = f'Context: {self._parse_docs(documents)}\nQuestion: {query}\nAnswer:'
        messages.append({"role": "user", "content": prompt})

        return Complete(model=self.model_name, prompt=messages, stream=True)

    def retrieve(self, query: str, lecture_names: list[str], limit: int = 3) -> dict:
        """
        Retrieve documents from cortex search service.
        """
        filter_query = {
            "@or": [{"@eq": {"lecture_name": lecture}} for lecture in lecture_names]
        }
        pdf_documents = self.pdf_service.search(
            query, columns=self.pdf_columns, limit=limit, filter=filter_query
        )
        video_documents = self.video_service.search(
            query, columns=self.video_columns, limit=limit, filter=filter_query
        )
        return {'pdf': pdf_documents.results, 'video': video_documents.results}

    def _parse_docs(self, documents: dict) -> str:
        pdf_content = '\n'.join([doc['text'] for doc in documents['pdf']])
        video_content = '\n'.join([doc['text'] for doc in documents['video']])
        return f'PDF Content: {pdf_content}\nVideo Content: {video_content}'
