# SciQuery: RAG System for Scientific Literature

This repository demonstrates the use of the LLAMA model for Retrieval-Augmented Generation (RAG), specifically designed for scientific literature Q&A. It showcases a complete system built from scratch, without utilizing any RAG-supported libraries or Vector databases. This approach help in understanding how this technique works. The system also provides an API for updating, deleting, and quering documents in the index.

## Steps to Implement SciQuery:

To get started, you need to download scientific literatures and save it in the `$PDF_DATA_DIR` folder for initial indexing. The application will creates an index of all documents and saves it as `numpy.ndarray` file.

### Step 1: PDF Processing:
The first step involves processing PDF documents and converting them into text. We use the `PyMuPDF` library to extract text blocks from each document of the PDF. Each text block's metadata including bounding box coordinates, helps us determine if it the block is part of a table or other content that needs special handling.

We use regex to identify the starting point of the `Reference` section, which is useful for preparing a bibliography for all document that has NeurIPS style citation.

### Step 2: Chunking:

To ensure each chunk is a relevant and not split randomly, we create chunks based on sections and passages. We use regex to extract important sections while ignoring elements such as titles, authors, correspondence, appendices etc.

Sections are further divided into passages if the number of words exceeds a predefined threshold. If the word count is below this threshold, smaller sections are combined to form larger chunks. Each chunk is associated with additional metadata, including `pdf_path`, `uuid`, and `title`, which helps in tracking and managing the chunks.

### Step 3: Embedding:

For effective semantic search, it is crucial to obtain vector embeddings of text passages. We generate these embeddings using the [Sentence Transformer](https://pypi.org/project/sentence-transformers/) library and [MixedBread Embedding](https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1).

These embeddings, along with the original text passages and their metadata, are saved as `numpy.ndarray` files. This method works well for small datasets and simple use cases. For more complex scenarios and better scalability, you may use advanced vector databases such as [Pinecone](https://www.pinecone.io/), [Qdrant](https://qdrant.tech/), [LlamaIndex](https://www.llamaindex.ai/), and similar services.

### Step 4: Retrieval and Ranking:
After indexing, the system processes a query by generating its embedding and then performs a brute-force cosine similarity search against all document embeddings. We retrieve a predefined number of top `$TOP_K_RETRIEVED` documents and then re-rank the top `$TOP_K_RANKED` documents. 

This brute-force approach is straightforward but may not be the most efficient. Better performance can be achieved by using vector databases with their sophisticated indexing mechanisms.

Reranking is beneficial because it helps to refine the results and improve the relevance of the retrieved documents. For this purpose, we use the [MixedBread ReRanker](https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v1).

### Step 5: Answer Generation:
In the final step, we combine all retrieved and reranked passages to form the context for generating the final RAG prompt. We instruct the LLM (Large Language Model) to provide answers based solely on the provided context. This approach minimizes the risk of hallucinations and ensures that the answers are directly relevant to the context provided.

## REST API Endpoints

The SciQuery system exposes several REST API endpoints to manage and query the document index. Below is a description of each endpoint, along with example `curl` commands for interacting with them.

### 1. **Manage Index**

This resource handles operations related to managing the document index, including retrieving, adding, and deleting documents.

- **GET `/api/documents`**

  Fetches a dictionary mapping UUIDs to filenames of all PDF documents currently in the index. Later, these UUID can be use to delete a document from INDEX.

  **Example `curl` Command:**
  ```bash
  curl -X GET "http://localhost:5000/api/documents"
  ```

  **Sample Response**
  ```json
  {
  "00da0765-ab15-4553-9ea1-3cfab674b3b0": "levy2014_neural_word_embeddings_implicit_matrix_factorization.pdf",
  "01c79fe2-7f76-487f-97c9-32b30ad89b75": "bojaniwski2017_enriching_we_with_subword_info_fasttext.pdf",
  "0307bfb7-e32c-49bd-8df0-eb197cf92660": "wudredze2019_betobentzbecas.pdf",
  "088a5d31-0228-4647-aa5f-bc9456c80cf4": "conneau2017_word_translation_without_parallel_data_muse_csls.pdf",
  "09a653e3-212e-4229-8685-930f2e8b013c": "lample2018_words_translation_withou_pralell.pdf",
  }
  ```

- **DELETE `/api/documents/<string:uid>`**

  Deletes a document from the index by its UUID. Replace `<string:uid>` with the actual UUID of the document you want to delete.

  **Example `curl` Command:**
  ```bash
  curl -X DELETE "http://localhost:5000/api/documents/00da0765-ab15-4553-9ea1-3cfab674b3b0"
  ```

  **Sample Response**
  ```json
  {
    "message": "Document with UID 01c79fe2-7f76-487f-97c9-32b30ad89b75 and filename bojaniwski2017_enriching_we_with_subword_info_fasttext.pdf deleted successfully from Index"
  }
  ```
  **You can see File with UUID "01c79fe2-7f76-487f-97c9-32b30ad89b75" is deleted from Index**
  ```json
  {
  "00da0765-ab15-4553-9ea1-3cfab674b3b0": "levy2014_neural_word_embeddings_implicit_matrix_factorization.pdf",
  "0307bfb7-e32c-49bd-8df0-eb197cf92660": "wudredze2019_betobentzbecas.pdf",
  "088a5d31-0228-4647-aa5f-bc9456c80cf4": "conneau2017_word_translation_without_parallel_data_muse_csls.pdf",
  "09a653e3-212e-4229-8685-930f2e8b013c": "lample2018_words_translation_withou_pralell.pdf",
  }
  ```

- **POST `/api/documents`**

  Adds a new PDF document to the index. The PDF file should be included in the form-data under the key `file`.

  **Example `curl` Command:**
  ```bash
  curl -X POST "http://localhost:5000/api/documents" \
  -F "file=@/path/to/bojaniwski2017_enriching_we_with_subword_info_fasttext.pdf.pdf"
  ```

  **Sample Response**
  ```json
  {
    "filename": "bojaniwski2017_enriching_we_with_subword_info_fasttext.pdf",
    "uid": "bd49bc59-cea9-4eaa-84c2-53b43a5dc93e"
  }
  ```

  **You can see "bojaniwski2017_enriching_we_with_subword_info_fasttext.pdf" is added back to the Index but with different UUID**
  ```json
  {
  "00da0765-ab15-4553-9ea1-3cfab674b3b0": "levy2014_neural_word_embeddings_implicit_matrix_factorization.pdf",
  "0307bfb7-e32c-49bd-8df0-eb197cf92660": "wudredze2019_betobentzbecas.pdf",
  "088a5d31-0228-4647-aa5f-bc9456c80cf4": "conneau2017_word_translation_without_parallel_data_muse_csls.pdf",
  "09a653e3-212e-4229-8685-930f2e8b013c": "lample2018_words_translation_withou_pralell.pdf",
  "bd49bc59-cea9-4eaa-84c2-53b43a5dc93e": "bojaniwski2017_enriching_we_with_subword_info_fasttext.pdf",
  }
  ```


### 2. **Query Index**

This resource processes queries to retrieve relevant information from the indexed documents.

- **POST `/api/query`**

  Sends a query to retrieve relevant passages and generate an answer. The query should be provided in the JSON body under the key `query`.

  **Example `curl` Command:**
  ```bash
  curl -X POST "http://localhost:5000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain what is ULMFIT?"}'
  ```

  **Sample Response with [TRUNCATED] passage**
  ```json
  {
    "query": "Explain what is ULMFIT?",
    "answer": "\nULMFiT is a transfer learning method for NLP (Natural Language Processing) that can be applied to any NLP task. It is a type of language model fine-tuning that uses a universal language model (ULM) as a starting point for adapting to specific NLP tasks. ULMFiT enables robust learning across a diverse range of tasks and prevents catastrophic forgetting, which means it can retain knowledge from previous tasks while learning new ones. It is an effective and extremely sample-efficient transfer learning method that can significantly outperform existing transfer learning techniques and the state-of-the-art on representative text classification tasks.",
    "metadata": [
        {
            "passage": "## Discussion and future directions\nWhile we have shown that ULMFiT can achieve state-of-the-art performance on widely used text classification tasks, we believe that language model fine-tuning will be particularly useful in the following settings compared to existing transfer learning approaches (Conneau et al., 2017; McCann et al., 2017; Peters et al., 2018): a) NLP for non-English languages, [TRUNCATED] .....",
            "pdf_path": "data/documents/ruder2019_ulmfit.pdf",
            "citations": [
                "Mahajan et al., 2018",
                "Peters et al., 2018",
                "Caruana, 1993",
                "Conneau et al., 2017",
                "Linzen et al., 2016",
                "McCann et al., 2017",
                "Huh et al., 2016"
            ]
        }
    ]
  }
  ```

### 3. **Bibliography**

This resource retrieves the bibliography information formatted in the NeurIPS citation style.

- **GET `/api/bibliography`**

  Fetches a dictionary of all bibliographic entries formatted according to the NeurIPS citation style.

  **Example `curl` Command:**
  ```bash
  curl -X GET "http://localhost:5000/api/bibliography"
  ```
  
  **Sample Response [TRUNCATED]**
  ```json
  {
    "data/documents/lample2019-cross-lingual-language-model-pretraining-Paper.pdf": {
        "[10]": {
            "authors": "Alexis Conneau and Douwe Kiela",
            "publication": "LREC, .",
            "title": "Senteval: An evaluation toolkit for universal sentence representations",
            "year": "2018"
        },
        "[11]": {
            "authors": "Alexis Conneau, Guillaume Lample, Marc’Aurelio Ranzato, Ludovic Denoyer, and Hervé Jegou",
            "publication": "In ICLR, .",
            "title": "Word translation without parallel data",
            "year": "2018"
        },
        "[12]": {
            "authors": "Alexis Conneau, Ruty Rinott, Guillaume Lample, Adina Williams, Samuel R",
            "publication": "Xnli: Evaluating cross-lingual sentence representations. In Proceedings of the  Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics, .",
            "title": "Bowman, Holger Schwenk, and Veselin Stoyanov",
            "year": "2018"
        },
    }
  }
  ```

## Installation and Setup

To get started with SciQuery, follow these steps to set up your Python environment, install the required dependencies, and start the Flask application.

1. **Create a Python Virtual Environment**

   First, create a virtual environment to manage your project's dependencies. Run the following command:

   ```bash
   python -m venv venv
   ```

2. **Activate the Virtual Environment**

   Activate the virtual environment. The command depends on your operating system:

   - On **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

3. **Install Required Dependencies**

   With the virtual environment activated, install the necessary packages using `pip`. Make sure to also install [MLX](https://pypi.org/project/mlx-llm/) library for Apple Silicon. This library is useful to load quantized model on Apple Silicon.:

   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Flask Application**

   Finally, start the Flask application using the following command:

   ```bash
   flask run
   ```

Make sure to set any necessary environment variables as specified in the `config.py` file before running the application.

TODO: 
- [ ] Test Docker script.
- [ ] Improve PDF parsing.
- [ ] Improve Bibliography parsing.

Replace `http://localhost:5000` with the actual base URL of your SciQuery API server. For the `POST` and `DELETE` requests, make sure to use the appropriate file paths and UUIDs as needed.

Thank you for exploring the SciQuery project. If you have any questions or contributions, please feel free to reach out.
