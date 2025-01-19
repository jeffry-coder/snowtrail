from dataclasses import dataclass, asdict
from typing import Optional
import httpx
import json
import time
import os
import re
import logging

import boto3
import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from langchain_community.document_loaders import AmazonTextractPDFLoader

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoSection:
    text: str
    start: float
    end: float


@dataclass
class Video:
    """
    A class to handle video processing and transcription.

    Attributes:
        file_path (str): Path to the video file
        duration (Optional[int]): Duration of the video in seconds
        whole_transcript (Optional[str]): Complete transcript of the video
        sentence_level_transcript (Optional[list[dict]]): Transcript broken down into sentences with timestamps
    """

    file_path: str
    duration: Optional[int] = None
    transcript: Optional[str] = None
    chunks: Optional[list[VideoSection]] = None

    def _transcribe(self):
        """
        Transcribes a video file using Deepgram API.

        Args:
            file_path (str): Path to the video file

        Returns:
            tuple: Contains (duration, whole_transcript, sentence_level_transcript)

        Raises:
            FileNotFoundError: If the video file is not found
        """
        logger.info(f"Starting transcription for file: {self.file_path}")

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        audio_file_name = os.path.splitext(os.path.basename(self.file_path))[0] + ".mp3"
        audio_file_path = os.path.join(os.path.dirname(self.file_path), audio_file_name)
        video_file = VideoFileClip(self.file_path)

        if os.path.exists(audio_file_path):
            logger.info("Audio file already exists, skipping conversion")
        else:
            logger.info("Converting video to audio")
            video_file.audio.write_audiofile(audio_file_path, logger=None)
        
        # STEP 1 Create a Deepgram client using the API key
        deepgram = DeepgramClient(api_key=st.secrets.deepgram.api_key)

        with open(audio_file_path, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # Configure Deepgram options for audio analysis
        options = PrerecordedOptions(
            model="nova-2-video",
            smart_format=True,
        )

        logger.info("Converting speech to text")
        # Call the transcribe_file method with the text payload and options
        start_time = time.time()
        response = deepgram.listen.rest.v("1").transcribe_file(
            payload, options, timeout=httpx.Timeout(300, connect=10)
        )
        print(f"Time taken: {time.time() - start_time}")

        # Parse the response
        results = json.loads(response.to_json())["results"]
        results = results["channels"][0]["alternatives"][0]
        whole_transcript = results["transcript"]
        sentence_level_transcript = []

        for paragraph in results["paragraphs"]["paragraphs"]:
            for sentence in paragraph["sentences"]:
                sentence_level_transcript.append(sentence)

        logger.info("Transcription completed successfully")
        return int(video_file.duration), whole_transcript, sentence_level_transcript

    def _chunk_text(self, transcript: list[dict], chunk_size: int, overlap: int) -> list[VideoSection]:
        """
        Splits the transcript into overlapping chunks of specified duration.

        Args:
            transcript (list[dict]): List of transcript segments with start/end times and text
            chunk_size (int, optional): Duration in seconds for each chunk. Defaults to 60.
            overlap (int, optional): Overlap duration between chunks in seconds. Defaults to 10.

        Returns:
            list[dict]: List of chunks containing text, start and end times
        """
        chunks = []
        current_start = transcript[0]["start"]
        current_end = current_start + chunk_size

        # Sliding Window
        while current_start < transcript[-1]["end"]:
            chunk_text = []
            chunk_start = None
            chunk_end = None

            # Collect segments that fall within current window
            for segment in transcript:
                if segment["end"] < current_start:
                    continue
                if segment["start"] > current_end:
                    break

                if chunk_start is None:
                    chunk_start = max(segment["start"], current_start)

                chunk_text.append(segment["text"])
                chunk_end = segment["end"]

            chunks.append(
                VideoSection(
                    text=" ".join(chunk_text),
                    start=round(chunk_start, 1),
                    end=round(chunk_end, 1),
                )
            )

            # Handles overlap
            current_start += chunk_size - overlap
            current_end = current_start + chunk_size

        return chunks

    def process_content(self, chunk_size: int = 60, overlap: int = 10):
        """
        Processes the video content by calling the transcribe method and storing the results.
        """
        self.duration, self.whole_transcript, sentence_level_transcript = self._transcribe()
        self.chunks = self._chunk_text(sentence_level_transcript, chunk_size, overlap)


@dataclass
class NoteSection:
    text: str
    page_num: int


@dataclass
class Note:
    file_path: str
    num_pages: Optional[int] = None
    content: Optional[str] = None
    chunks: Optional[list[NoteSection]] = None

    def _load_document(self):
        """
        Loads a PDF document using Amazon Textract and returns the content.
        """
        session = boto3.Session(
            aws_access_key_id=st.secrets.aws.access_key_id,
            aws_secret_access_key=st.secrets.aws.secret_access_key,
            region_name=st.secrets.aws.default_region,
        )
        bucket_name = st.secrets.aws.bucket_name
        file_name = os.path.basename(self.file_path)
        bucket_file_path = f"s3://{bucket_name}/{file_name}"

        logger.info(f"Uploading file to {bucket_file_path}")
        bucket = session.client("s3")
        bucket.upload_file(Filename=self.file_path, Bucket=bucket_name, Key=file_name)

        logger.info("Extracting content from PDF")
        textract = session.client("textract")
        loader = AmazonTextractPDFLoader(bucket_file_path, client=textract)
        documents = loader.load()

        bucket.delete_object(Bucket=bucket_name, Key=file_name)

        whole_content = ""
        chunks = []

        for doc in documents:
            # Clean text content, remove newlines
            content = re.sub(r'[\n\r]+', ' ', doc.page_content)
            content = re.sub(r'\s{2,}', ' ', content)
            content = content.strip()

            page = doc.metadata["page"]
            whole_content += f"{'-'*20}PAGE {page}{'-'*20}\n{content}\n\n"
            chunks.append(NoteSection(text=content, page_num=page))

        logger.info("Content extraction completed successfully")

        return len(documents), whole_content, chunks

        # TODO: Try capturing each page as a still and extract content using LLM

    def process_content(self):
        self.num_pages, self.content, self.chunks = self._load_document()


if __name__ == "__main__":
    # Video Loader: deepgram for transcript, time-based chunking
    video = Video(
        file_path=r"lecture_series\machine learning for healthcare\videos\lecture_video_1.mp4"
    )
    video.process_content()

    print(video.whole_transcript[:1000])
    print("Duration: ", video.duration)
    with open("output/video_chunks.json", "w") as f:
        json.dump([asdict(chunk) for chunk in video.chunks], f)

    # PDF Loader: amazon textract for content, page-based chunking
    note = Note(
        file_path=r"lecture_series\machine learning for healthcare\pdfs\lecture_notes_1.pdf"
    )
    note.process_content()

    print(note.content[:1000])
    print("Num pages: ", note.num_pages)
    with open("output/note_chunks.json", "w") as f:
        json.dump([asdict(chunk) for chunk in note.chunks], f)
