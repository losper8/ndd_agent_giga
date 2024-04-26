from typing import List

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from cleantext import clean
from langchain_community.embeddings.gigachat import GigaChatEmbeddings
from langchain_text_splitters import TokenTextSplitter
from tqdm import tqdm

from embeddings.api.schema import EmbeddingRequest
from embeddings.infrastructure.chroma_db_config import chroma_db_config
from embeddings.infrastructure.config import giga_chat_api_config


class GigaChatEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, credentials: str, scope: str):
        self.embeddings = GigaChatEmbeddings(credentials=credentials, verify_ssl_certs=False, scope=scope)

    def __call__(self, input: Documents) -> Embeddings:
        return self.embeddings.embed_documents(texts=input)


text_splitter = TokenTextSplitter.from_tiktoken_encoder(
    encoding_name='cl100k_base',
    model_name="text-embedding-3-large",
    chunk_size=4096,
    chunk_overlap=0
)
chroma_client = chromadb.HttpClient(host=chroma_db_config.HOST, port=chroma_db_config.PORT)
gigachat_embedding_function = GigaChatEmbeddingFunction(credentials=giga_chat_api_config.TOKEN, scope=giga_chat_api_config.SCOPE)
# chroma_client.delete_collection(name='gigachat_rospatent_titles_collection')
gigachat_rospatent_titles_collection = chroma_client.get_or_create_collection(name='gigachat_rospatent_titles_collection', embedding_function=gigachat_embedding_function)


async def domain_save_embeddings(
    request: List[EmbeddingRequest],
):
    collection_clean = gigachat_rospatent_titles_collection
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

        clean_splits = text_splitter.split_text(full_text_clean)

        try:
            for idx, cleaned_chunk in enumerate(clean_splits):
                collection_clean.add(
                    ids=[f"{item.id.replace('.txt', '_' + str(idx) + '.txt')}"],
                    documents=[cleaned_chunk],
                    metadatas=[{"part_index": idx, 'id': item.id}],
                )
        except Exception as e:
            print(f"Error processing item {item.id}: {e}")

    print("Embeddings saved for both raw and cleaned texts.")
