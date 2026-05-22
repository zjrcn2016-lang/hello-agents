import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen1.5-0.5B-Chat"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id).to(device)
print("模型加载完成！\n")

# 采样参数-- 这些参数可以调整生成文本的多样性和质量
# temperature 控制生成文本的随机程度，值越高越随机
# top_p 和 top_k 控制生成文本的多样性，值越小越保守

generation_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,
    "max_new_tokens": 256,
}

def chat(messages, label=""):
    """发送对话并打印回答"""
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(device)
    generated_ids = model.generate(inputs.input_ids, **generation_config)
    # 只保留新生成的部分
    new_ids = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)]
    response = tokenizer.batch_decode(new_ids, skip_special_tokens=True)[0]
    print(f"{'='*40}")
    print(f"【{label}】")
    print(f"回答: {response}")
    print()
    return response

# ── 待分类的文本（跨领域模糊句，故意增加难度）──
# 这句话同时涉及科技、体育、娱乐，模型需要判断主要意图
text_to_classify = "他靠着在直播间卖球鞋赚到了第一桶金，随后投资了一家AI芯片公司。"

# ── 1. Zero-shot：直接问，不给任何示例 ────────
messages_zero_shot = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"请将以下文本分类为体育、科技、娱乐或其他，只输出类别名称：'{text_to_classify}'"}
]
chat(messages_zero_shot, "Zero-shot（无示例）")

# ── 2. Few-shot：给示例，但示例故意不覆盖跨领域情况 ──
messages_few_shot = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "请将以下文本分类为体育、科技、娱乐或其他，只输出类别名称：'苹果公司发布了最新的iPhone。'"},
    {"role": "assistant", "content": "科技"},
    {"role": "user", "content": "请将以下文本分类为体育、科技、娱乐或其他，只输出类别名称：'昨天的足球比赛非常精彩。'"},
    {"role": "assistant", "content": "体育"},
    {"role": "user", "content": "请将以下文本分类为体育、科技、娱乐或其他，只输出类别名称：'这部电影票房突破10亿。'"},
    {"role": "assistant", "content": "娱乐"},
    {"role": "user", "content": f"请将以下文本分类为体育、科技、娱乐或其他，只输出类别名称：'{text_to_classify}'"}
]
chat(messages_few_shot, "Few-shot（有示例，但无跨领域示例）")

# ── 3. Chain-of-Thought：让模型先推理再给答案 ──
messages_cot = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": (
        f"请将以下文本分类为体育、科技、娱乐或其他。\n"
        f"文本中可能同时涉及多个领域，请先逐一列出文本中出现的领域线索，"
        f"再判断哪个领域是核心主题，最后给出类别。\n"
        f"文本：'{text_to_classify}'"
    )}
]
chat(messages_cot, "Chain-of-Thought（逐步推理）")

# ── 4. Self-consistency：同一问题问三次，看答案是否一致 ──
print("="*40)
print("【Self-consistency（重复提问，检验稳定性）】")
answers = []
for i in range(3):
    result = chat(messages_zero_shot, f"第{i+1}次 Zero-shot")
    answers.append(result.strip())
print(f"三次答案: {answers}")
print(f"结论: {'一致 ✓' if len(set(answers)) == 1 else '不一致 ✗ — 模型对此句把握不足'}")



