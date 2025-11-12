""" 
    I didnt set up the requirements.txt, tmp testing
"""

#%%
import pandas as pd
import os
import spacy
from sentence_transformers import SentenceTransformer
import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity

cur_dir = os.getcwd()
parent_dir = os.path.dirname(cur_dir)

jobs_df = pd.read_csv(parent_dir + '\\DATA\\test_job_data.csv')

tmp_df = pd.read_csv(parent_dir + '\\DATA\\Job_scraping_Data.csv')


class SimiliarityFactory:
    nlp = spacy.load("en_core_web_sm")
    embed_model = SentenceTransformer('all-MiniLM-L6-v2') 

    def __init__(self, raw_cv_df : pd.DataFrame, raw_job_df : pd.DataFrame):
        self.raw_cv_df = raw_cv_df
        self.raw_job_df = raw_job_df
    
    
    @classmethod
    def _normalize_keyword_list(cls, raw_description : str) -> str:
        """
            keep deduplicated tokens only
        """
        normalized : list[str] = []
        raw_token = cls.nlp(raw_description)
        key_points = [chunk.text for chunk in raw_token.noun_chunks]
        seen = set()
        for keyword in key_points:
            if not isinstance(keyword, str):
                continue
            kw = keyword.strip()
            if not kw:
                continue
            if kw.lower() in seen:
                continue
            seen.add(kw.lower())
            normalized.append(kw)
        return ", ".join(normalized)

    @staticmethod
    def _prepare_text_for_vectorization(text : str) -> str:
        """ 
            keep lowercase, remove special characters, etc.
        """
        lowered = text.lower()
        lowered = re.sub(r"[`*_>#\-•]", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered)
        return lowered


    @classmethod
    def _spacy_extract_key_points(cls, text : str) -> str:
        """
            For simply testing purpose 

            Extract key points from job descriptions using spaCy
        """

        doc = cls.nlp(text)
        key_points = [chunk.text for chunk in doc.noun_chunks]  # Or use entities: [ent.text for ent in doc.ents]
        return " ".join(key_points) 
    
    @classmethod
    def _transformer_text_vectorization(cls, text : str) -> list:
        """
            Use SentenceTransformer to convert text to embeddings
        """
        return cls.embed_model.encode(text).tolist()
    
    @classmethod
    def process_and_add_columns(cls, df: pd.DataFrame, text_column: str, key_column: str = 'extracted_keys', embed_column: str = 'embeddings') -> pd.DataFrame:
        """
        Process text column to extract keys and embeddings, adding them as new columns.
        """
        def safe_apply(func, text, default):
            if not isinstance(text, str) or not text.strip():
                return default
            try:
                return func(text)
            except Exception as e:
                print(f"Error in {func.__name__}: {e}")
                return default
        
        # Extract keys
        df[key_column] = df[text_column].apply(lambda x: safe_apply(cls._spacy_extract_key_points, x, ""))
        df[key_column] = df[key_column].apply(lambda x: safe_apply(cls._prepare_text_for_vectorization, x, ""))
        df[key_column] = df[key_column].apply(lambda x: safe_apply(cls._normalize_keyword_list, x, ""))
        
        # Generate embeddings from keys
        df[embed_column] = df[key_column].apply(lambda x: safe_apply(cls._transformer_text_vectorization, x, []))
        
        return df

#%%
jobs_df = SimiliarityFactory.process_and_add_columns(jobs_df, 'Job Responsibilities', 'extracted_keys', 'embeddings')

#%%
query = "LLM, AI, Machine learning"
query_embedding = SimiliarityFactory.embed_model.encode(query)

similarities = []
for emb in jobs_df['embeddings']:
    sim = cosine_similarity([query_embedding], [emb])[0][0]
    similarities.append(sim)

jobs_df['similarity'] = similarities
top_matches = jobs_df.sort_values('similarity', ascending=False).head(5)
print(top_matches[['Job Title', 'similarity']])


