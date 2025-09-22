import logging
from typing import Final, List, Optional, Any
import torch
from transformers import AutoModel, AutoTokenizer
from librarian import logging_util

_LOGGER: Final[logging.Logger] = logging_util.get_logger(__name__)


class EmbeddingModel:
    def __init__(self):
        self.model_name = "pfnet/plamo-embedding-1b"
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_model()

    def _initialize_model(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True
            )
            self.model = AutoModel.from_pretrained(
                self.model_name, trust_remote_code=True
            )
            self.model = self.model.to(self.device)
            _LOGGER.info(f"Embedding model loaded on device: {self.device}")
        except Exception as e:
            _LOGGER.error(f"Failed to load embedding model: {e}")
            raise

    def encode_query(self, query: str) -> List[float]:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not initialized")
        with torch.inference_mode():
            embedding = self.model.encode_query(query, self.tokenizer)
            embedding_np = embedding.cpu().numpy()
            if len(embedding_np.shape) > 1:
                embedding_np = embedding_np.flatten()
            norm = (embedding_np ** 2).sum() ** 0.5
            if norm > 0:
                embedding_np = embedding_np / norm
            return embedding_np.tolist()

    def encode_document(self, document: str) -> List[float]:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not initialized")
        with torch.inference_mode():
            embedding = self.model.encode_document([document], self.tokenizer)
            embedding_np = embedding[0].cpu().numpy()
            norm = (embedding_np ** 2).sum() ** 0.5
            if norm > 0:
                embedding_np = embedding_np / norm
            return embedding_np.tolist()


_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
