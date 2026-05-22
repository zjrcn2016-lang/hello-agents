import numpy as np

# 假设我们已经学习到了简化的二维词向量
embeddings = {
    "king": np.array([0.9, 0.8]),
    "queen": np.array([0.9, 0.2]),
    "man": np.array([0.7, 0.9]),
    "woman": np.array([0.7, 0.3])
}

# 定义一个函数来计算两个向量之间的余弦相似度，以衡量它们的相似程度
# 余弦相似度的计算公式为：cosine_similarity(vec1, vec2) = (vec1 · vec2) / (||vec1|| * ||vec2||)
# 其中，vec1 · vec2 是两个向量的点积，||vec1|| 和 ||vec2|| 分别是两个向量的范数（长度）。
# 余弦相似度的值范围在 -1 到 1 之间，值越接近 1 表示两个向量越相似，值越接近 -1 表示两个向量越不相似，值为 0 表示两个向量正交（没有相似性）。

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return dot_product / norm_product

# king - man + woman
result_vec = embeddings["king"] - embeddings["man"] + embeddings["woman"]

# 计算结果向量与 "queen" 的相似度
sim = cosine_similarity(result_vec, embeddings["queen"])

print(f"king - man + woman 的结果向量: {result_vec}")
print(f"该结果与 'queen' 的相似度: {sim:.4f}")