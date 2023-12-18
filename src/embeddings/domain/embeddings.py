from typing import List

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from cleantext import clean
from langchain_text_splitters import TokenTextSplitter
from tqdm import tqdm

from embeddings.api.schema import EmbeddingRequest
from embeddings.infrastructure.chroma_db_config import chroma_db_config
from embeddings.infrastructure.external_api_config import external_api_config

text_splitter = TokenTextSplitter.from_tiktoken_encoder(
    encoding_name=external_api_config.OPENAI_MODEL_ENCODER_NAME,
    model_name=external_api_config.OPENAI_MODEL_NAME,
    chunk_size=external_api_config.OPENAI_MODEL_MAX_INPUT,
    chunk_overlap=0
)
chroma_client = chromadb.HttpClient(host=chroma_db_config.HOST, port=chroma_db_config.PORT)
openai_embedding_function = OpenAIEmbeddingFunction(api_key=external_api_config.OPENAI_TOKEN, model_name=external_api_config.OPENAI_MODEL_NAME)
openai_collection_raw_big = chroma_client.get_or_create_collection(name='openai_collection_raw_big', embedding_function=openai_embedding_function)
openai_collection_clean_big = chroma_client.get_or_create_collection(name='openai_collection_clean_big', embedding_function=openai_embedding_function)


# openai_collection_raw_small = chroma_client.get_or_create_collection(name='openai_collection_raw_small', embedding_function=openai_embedding_function)
# openai_collection_clean_small = chroma_client.get_or_create_collection(name='openai_collection_clean_small', embedding_function=openai_embedding_function)


async def domain_save_embeddings(
    request: List[EmbeddingRequest],
):
    # if big:
    collection_raw = openai_collection_raw_big
    collection_clean = openai_collection_clean_big
    # else:
    #     collection_raw = openai_collection_raw_small
    #     collection_clean = openai_collection_clean_small
    for item in tqdm(request):
        print(f"Processing item {item.id}")
        full_text_clean = clean(
            item.text,
            fix_unicode=True,
            to_ascii=False,
            lower=True,
            normalize_whitespace=True,
            no_line_breaks=True,
            strip_lines=True,
            keep_two_line_breaks=False,
            no_urls=True,
            no_emails=True,
            no_phone_numbers=True,
            no_numbers=True,
            no_digits=True,
            no_currency_symbols=True,
            no_punct=True,
            no_emoji=True,
            replace_with_url="<ссылка>",
            replace_with_email="<почта>",
            replace_with_phone_number="<телефон>",
            replace_with_number="",
            replace_with_digit="",
            replace_with_currency_symbol="<валюта>",
            replace_with_punct="",
            lang="en",
        )
        full_text_clean = "".join([c for c in full_text_clean if c.isalpha() or c.isspace()])

        raw_splits = text_splitter.split_text(item.text)
        clean_splits = text_splitter.split_text(full_text_clean)

        dataset = item.id.split('/')[0]
        filename = item.id.split('/')[-1]

        document_id = item.id.split('/')[-1].replace('.txt', '')

        try:
            for idx, raw_chunk in enumerate(raw_splits):
                collection_raw.add(
                    ids=[f"{item.id.replace('.txt', '_' + str(idx) + '.txt')}"],
                    documents=[raw_chunk],
                    metadatas=[{"class": item.source, "part_index": idx, "dataset": dataset, "filename": filename, "document_id": document_id}],
                )

            for idx, cleaned_chunk in enumerate(clean_splits):
                collection_clean.add(
                    ids=[f"{item.id.replace('.txt', '_' + str(idx) + '.txt')}"],
                    documents=[cleaned_chunk],
                    metadatas=[{"class": item.source, "part_index": idx, "dataset": dataset, "filename": filename, "document_id": document_id}],
                )
        except Exception as e:
            print(f"Error processing item {item.id}: {e}")

    print("Embeddings saved for both raw and cleaned texts.")
