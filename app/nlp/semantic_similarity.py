from sklearn.metrics.pairwise import cosine_similarity


def most_similar(query_embedding, candidate_embeddings, top_k: int = 3):
    scores = cosine_similarity([query_embedding], candidate_embeddings)[0]
    ranking = scores.argsort()[::-1][:top_k]
    return [(int(index), float(scores[index])) for index in ranking]
