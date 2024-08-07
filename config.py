EMBEDDING_MODEL_PATH = "mixedbread-ai/mxbai-embed-large-v1" #'all-MiniLM-L6-v2'
RERANKER_MODEL_PATH = "mixedbread-ai/mxbai-rerank-base-v1"
PDF_DATA_DIR = "data/documents"
INDEX_AND_BIB_DIR = "data/index_and_bib"
INDEX_ARRAY_NAME = "index.npy"
BIB_JSON_NAME = "bibliographies.json"

TOP_K_RETRIEVED = 5
TOP_K_RANKED = 1
LLAMA_MODEL_PATH_MLX = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit" #for apple silicon
LLAMA_MODEL_PATH = "meta-llama/Meta-Llama-3.1-8B-Instruct"
DEVICE = "MPS" 
GENERATION_KWARGS = {"temperature":0.85,
                     "top_p": 1.0}

MAX_TOKENS = 4096

DEBUG = False