import os
import re
import json
from functools import lru_cache

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig,
)
from langchain_huggingface import HuggingFacePipeline


MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")


@lru_cache(maxsize=1)
def get_llm():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    if torch.cuda.is_available():
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=quantization_config,
            device_map="auto",
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map="auto",
        )

    text_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=700,
        do_sample=False,
        return_full_text=False,
    )
    return HuggingFacePipeline(pipeline=text_pipeline)


def extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("No JSON object found in model response.")
    return json.loads(match.group(0))
