from typing import List
from enum import Enum


class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    SENTENCE_BASED = "sentence_based"


class TextChunker:
    @staticmethod
    def chunk_fixed_size(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into fixed-size chunks with overlap
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            start += chunk_size - overlap
        
        return chunks
    
    @staticmethod
    def chunk_sentence_based(text: str, sentences_per_chunk: int = 5) -> List[str]:
        """
        Split text into chunks based on sentences
        """
        sentences = []
        for sentence in text.replace('\n', ' ').split('.'):
            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence + '.')
        
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            chunk = ' '.join(sentences[i:i + sentences_per_chunk])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    @staticmethod
    def chunk_text(text: str, strategy: ChunkingStrategy) -> List[str]:
        """
        Chunk text using the specified strategy
        """
        if strategy == ChunkingStrategy.FIXED_SIZE:
            return TextChunker.chunk_fixed_size(text)
        elif strategy == ChunkingStrategy.SENTENCE_BASED:
            return TextChunker.chunk_sentence_based(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")