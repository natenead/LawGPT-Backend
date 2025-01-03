from langchain.vectorstores import Qdrant
from dotenv import load_dotenv
import logging
from qdrant_client import QdrantClient
import os
from ..utils import get_vectors_count
from langchain_pinecone import PineconeVectorStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s:%(name)s:%(levelname)s:%(message)s:%(funcName)s')
file_handler = logging.FileHandler('raf.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
load_dotenv()

def create_new_vectorstore_qdrant(doc_list, embed_fn, COLLECTION_NAME,index):
    try:
        c_name = COLLECTION_NAME.replace('>',"").replace('<',"")
        # qdrant = Qdrant.from_documents(
        #     documents = doc_list,
        #     embedding = embed_fn,
        #     url=qdrant_url,
        #     prefer_grpc=False,
        #     api_key=qdrant_api_key,
        #     collection_name=c_name,
        # )
        #
        # qdrant_client = QdrantClient(
        #     url=os.getenv('qdrant_url'),
        #     prefer_grpc=True,
        #     api_key=os.getenv('api_key'),
        # )
        # collection_status = qdrant_client.get_collection(collection_name=c_name)
        pine_cone = PineconeVectorStore.from_documents(
            doc_list,
            embedding=embed_fn,
            index_name=index,
            namespace=c_name + '__ind__' + index
        )

        # except Exception as e:
        #     raise {"error": e}
        logger.info("Successfully created the vectordb")
        return pine_cone
    except Exception as ex:
        logger.critical("Vectordb Failed:"+str(ex))
        raise Exception({"Error": str(ex)})

def load_local_vectordb_using_qdrant(vectordb_folder_path, embed_fn):
    # qdrant_client = QdrantClient(
    #     url=os.getenv('qdrant_url'),
    #     prefer_grpc=True,
    #     api_key=os.getenv('api_key'),
    # )
    #
    # qdrant_store= Qdrant(qdrant_client, vectordb_folder_path, embed_fn)
    # return qdrant_store
    try:
        index_name = vectordb_folder_path.split('__ind__')[1]

        docsearch = PineconeVectorStore.from_existing_index(
            embedding=embed_fn, index_name=index_name, namespace=vectordb_folder_path)
        return docsearch
    except Exception as e:
        return False
def delete_vectordb_using_qdrant( vectordb_folder_path,  qdrant_url=os.getenv('qdrant_url'), qdrant_api_key=os.getenv('api_key')):
    try:
        qdrant_client = QdrantClient(
            url=qdrant_url,
            prefer_grpc=True,
            api_key=qdrant_api_key,
        )
        qdrant_client.delete_collection(collection_name=vectordb_folder_path)
    except Exception as e:
        raise Exception(str(e))
    return "Done"
def get_collection_list_qdrant(qdrant_url=os.getenv('qdrant_url'), qdrant_api_key=os.getenv('api_key')):
    try:
        qdrant_client = QdrantClient(
            url=qdrant_url,
            prefer_grpc=True,
            api_key=qdrant_api_key,
        )
        collections=qdrant_client.get_collections()
    except Exception as e:
        raise Exception(str(e))
    return collections