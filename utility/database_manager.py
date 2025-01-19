from snowflake.connector.connection import SnowflakeConnection
import streamlit as st


class DatabaseManager:
    def __init__(self, conn: SnowflakeConnection):
        self.conn = conn
        self._init_database()
    
    def _init_database(self):
        create_db = f"""
        CREATE DATABASE IF NOT EXISTS {st.secrets["connections"]["snowflake"]["database"]}
        """
        self._run_query(create_db)

        create_schema = f"""
        CREATE SCHEMA IF NOT EXISTS {st.secrets["connections"]["snowflake"]["schema"]}
        """
        self._run_query(create_schema)

    def _run_query(self, query: str, params=None, return_results: bool = False):
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if return_results:
                return cursor.fetchall()
            return True
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")
        finally:
            cursor.close()

    def create_table(self, course_name: str):
        video_table = f"{course_name}_video"
        pdf_table = f"{course_name}_pdf"
        
        video_query = f"""
        CREATE TABLE IF NOT EXISTS {video_table} (
            text STRING,
            start_time INTEGER,
            end_time INTEGER,
            file_name STRING,
            lecture_name STRING
        )
        """
        
        pdf_query = f"""
        CREATE TABLE IF NOT EXISTS {pdf_table} (
            text STRING,
            page_num INTEGER,
            file_name STRING,
            lecture_name STRING
        )
        """
        
        self._run_query(video_query)
        self._run_query(pdf_query)
    
    def insert_data(self, course_name: str, data: list[tuple], content_type: str):
        """
        Generic method to insert data into video or pdf tables
        
        Args:
            course_name (str): Name of the course to insert into
            data (list[tuple]): List of data tuples to insert
            content_type (str): Type of content - "video" or "pdf"
        """
        print(f'Inserting {content_type} data into {course_name}')
        if content_type == "video":
            columns = "(text, start_time, end_time, file_name, lecture_name)"
            placeholders = "(?, ?, ?, ?, ?)"
        elif content_type == "pdf":
            columns = "(text, page_num, file_name, lecture_name)" 
            placeholders = "(?, ?, ?, ?)"
        else:
            raise ValueError(f"Invalid content type: {content_type}")

        table_name = f'{course_name}_{content_type}'
        insert_query = f"""
        INSERT INTO {table_name} {columns}
        VALUES {placeholders}
        """

        cursor = self.conn.cursor()
        try:
            cursor.executemany(insert_query, data)
        except Exception as e:
            raise Exception(f"Error inserting data into table {table_name}: {str(e)}")
        finally:
            cursor.close()
    
    def create_search_service(self, course_name: str):
        print(f'Creating search service for {course_name}')
        for content_type in ["pdf", "video"]:
            table_name = f'{course_name}_{content_type}'
            service_query = f"""
            CREATE CORTEX SEARCH SERVICE IF NOT EXISTS {table_name}
            ON text
            ATTRIBUTES lecture_name
            warehouse = COMPUTE_WH
            TARGET_LAG = '1 minute'
            as (
                SELECT *
                FROM {table_name}
            );
            """
            self._run_query(service_query)

    def get_files_in_lecture(self, course_name: str, lecture_name: str):
        unique_files = set()
        for content_type in ['video', 'pdf']:
            table_name = f'{course_name}_{content_type}'
            query = f"""
            SELECT DISTINCT file_name 
            FROM {table_name}
            WHERE lecture_name = '{lecture_name}'
            """
            results = self._run_query(query, return_results=True)
            for result in results:
                unique_files.add(result[0])

        return list(unique_files)

    def delete_collection(self, course_name: str):
        for content_type in ['video', 'pdf']:
            table_name = f'{course_name}_{content_type}'
            delete_table_query = f"""
            DROP TABLE IF EXISTS {table_name}
            """
            self._run_query(delete_table_query)

            delete_service_query = f"""
            DROP CORTEX SEARCH SERVICE IF EXISTS {table_name}
            """
            self._run_query(delete_service_query)

    def list_collections(self):
        list_tables_query = f"""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = CURRENT_SCHEMA();
        """
        results = self._run_query(list_tables_query, return_results=True)
        table_names = [result[0] for result in results]
        courses = set()
        for table_name in table_names:
            if table_name.endswith('_video'):
                # Remove _video suffix and add to courses
                course_name = table_name[:-6]
            elif table_name.endswith('_pdf'):
                # Remove _pdf suffix and add to courses
                course_name = table_name[:-4]
            else:
                continue
            courses.add(course_name)
        
        return list(courses)
