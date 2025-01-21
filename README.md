# SnowTrail - Navigate the path to your lecture's key moments

SnowTrail is an innovative e-learning platform that helps teachers and students manage and interact with course content effectively. It features a dual-portal system for teachers to upload content and students to access and engage with learning materials.

## 🌟 Features

- **Dual Portal System**

  - 👨‍🏫 Teacher Portal: Upload and manage course materials
  - 👩‍🎓 Student Portal: Access and interact with learning content

- **Smart Content Processing**

  - Automatic processing of lecture materials
  - Support for multiple file formats including PDFs and videos
  - Integration with Amazon Textract for document processing
  - Video transcription using Deepgram

- **Snowflake Integration**
  - Secure data storage and management
  - Efficient content retrieval system
 
- **Trulens Evaluation**
source code is on `evaluation.ipynb`. two experiments were conducted:
  - Local search vs Global search (test the purpose of filter by lecture name)
  - Chunk duration (30 sec, 1 min, 2 min)
we score the app versions across key metrics: context, answer relevance and groundedness. 

## 📁 Project Structure

- `/portal`: main application pages
- `/utility`: document loaders, database, file managers
- `/courses`: organized into lecture subfolders, with PDF and MP4 content
- `/pipeline`: content ingestion and retrieval pipelines
- `/qna_for_eval`: questions to evaluate RAG chain

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- Snowflake account
- AWS account (for Amazon Textract)
- Deepgram API key

### Installation

1. Clone the repository:

```bash
git clone https://github.com/jeffry-coder/snowtrail
cd snowtrail
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

Before running `evaluation.ipynb`, please install the additional libraries:
```bash
pip install trulens trulens-providers-cortex
```

3. Configure environment variables in `.streamlit/secrets.toml`:

```toml
[aws]
access_key_id = ""
secret_access_key = ""
default_region = ""
bucket_name = ""

[deepgram]
api_key = ""

[connections.snowflake]
user = ""
password = ""
account = ""
warehouse = ""
database = ""
schema = ""
```

4. Start the application:

```bash
streamlit run app.py
```
