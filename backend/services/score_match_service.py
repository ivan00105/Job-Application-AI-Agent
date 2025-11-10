""" 
    I didnt set up the requirements.txt
"""

#%%
import pandas as pd
import os
import spacy
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

cur_dir = os.getcwd()
parent_dir = os.path.dirname(cur_dir)
grandparent_dir = os.path.dirname(parent_dir) 

jobs_df = pd.read_csv(grandparent_dir + '\\job_data_clean.csv')

#%%
""" 
    Extract key points from job descriptions using spaCy 
        - tmp testingm -> just select the first 10 noun tokens
"""
def extract_key_points(text):
    doc = nlp(text)
    key_points = [chunk.text for chunk in doc.noun_chunks]  # Or use entities: [ent.text for ent in doc.ents]
    return " ".join(key_points[:10])  # Limit to top 10 for brevity

nlp = spacy.load("en_core_web_sm")
jobs_df['key_points'] = jobs_df['Job Title'] + " " + jobs_df['Job Responsibilities'] + " " + jobs_df['Job Requirements']
jobs_df['key_points'] = jobs_df['key_points'].apply(extract_key_points)

#%%
""" 
    vectorize key points using SentenceTransformer and compute similarity
"""
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight and effective
jobs_df['embeddings'] = jobs_df['key_points'].apply(lambda x: model.encode(x).tolist())  # Store as list for DataFrame


# Example similarity computation
query = "software engineer python"
query_embedding = model.encode(query)

similarities = []
for emb in jobs_df['embeddings']:
    sim = cosine_similarity([query_embedding], [emb])[0][0]
    similarities.append(sim)

jobs_df['similarity'] = similarities
top_matches = jobs_df.sort_values('similarity', ascending=False).head(5)
print(top_matches[['Job Title', 'similarity']])
# %%
