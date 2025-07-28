"""
Compression utilities for API response optimization.

This module provides compression functionality for API responses to reduce
bandwidth usage and improve performance.
"""

import gzip
import json
import zlib
from typing import Any, Dict, Optional, Union
from fastapi import Response, Request
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)

class CompressionManager:
    """Manager for response compression."""
    
    def __init__(self):
        """Initialize compression manager."""
        self.supported_encodings = ["gzip", "deflate", "br"]
        self.min_size_for_compression = 1024  # 1KB minimum for compression
    
    def should_compress(self, content: Union[str, bytes], encoding: str) -> bool:
        """
        Determine if content should be compressed.
        
        Args:
            content: Content to check
            encoding: Compression encoding
            
        Returns:
            True if content should be compressed
        """
        if encoding not in self.supported_encodings:
            return False
        
        content_size = len(content) if isinstance(content, str) else len(content)
        return content_size >= self.min_size_for_compression
    
    def compress_gzip(self, content: Union[str, bytes]) -> bytes:
        """
        Compress content using gzip.
        
        Args:
            content: Content to compress
            
        Returns:
            Compressed content
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        return gzip.compress(content, compresslevel=6)
    
    def compress_deflate(self, content: Union[str, bytes]) -> bytes:
        """
        Compress content using deflate.
        
        Args:
            content: Content to compress
            
        Returns:
            Compressed content
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        return zlib.compress(content, level=6)
    
    def compress_brotli(self, content: Union[str, bytes]) -> bytes:
        """
        Compress content using Brotli.
        
        Args:
            content: Content to compress
            
        Returns:
            Compressed content
        """
        try:
            import brotli
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            return brotli.compress(content, quality=6)
        except ImportError:
            logger.warning("Brotli not available, falling back to gzip")
            return self.compress_gzip(content)
    
    def compress_content(self, content: Union[str, bytes], encoding: str) -> bytes:
        """
        Compress content using specified encoding.
        
        Args:
            content: Content to compress
            encoding: Compression encoding
            
        Returns:
            Compressed content
        """
        if encoding == "gzip":
            return self.compress_gzip(content)
        elif encoding == "deflate":
            return self.compress_deflate(content)
        elif encoding == "br":
            return self.compress_brotli(content)
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")

def get_acceptable_encoding(request: Request) -> Optional[str]:
    """
    Get the best acceptable encoding from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Best acceptable encoding or None
    """
    accept_encoding = request.headers.get("accept-encoding", "")
    
    # Parse accept-encoding header
    encodings = []
    for encoding in accept_encoding.split(","):
        encoding = encoding.strip()
        if ";" in encoding:
            encoding, qvalue = encoding.split(";", 1)
            qvalue = qvalue.strip()
            if qvalue.startswith("q="):
                try:
                    q = float(qvalue[2:])
                    encodings.append((encoding, q))
                except ValueError:
                    encodings.append((encoding, 1.0))
        else:
            encodings.append((encoding, 1.0))
    
    # Sort by quality value (descending)
    encodings.sort(key=lambda x: x[1], reverse=True)
    
    # Return the first supported encoding
    supported = ["br", "gzip", "deflate"]
    for encoding, _ in encodings:
        if encoding in supported:
            return encoding
    
    return None

def compress_response(
    content: Union[str, bytes, Dict[str, Any]],
    encoding: str,
    content_type: str = "application/json"
) -> Response:
    """
    Create a compressed response.
    
    Args:
        content: Response content
        encoding: Compression encoding
        content_type: Content type
        
    Returns:
        Compressed response
    """
    # Convert dict to JSON string
    if isinstance(content, dict):
        content = json.dumps(content, default=str)
    
    # Convert string to bytes
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    # Compress content
    compression_manager = CompressionManager()
    compressed_content = compression_manager.compress_content(content, encoding)
    
    # Create response
    response = Response(
        content=compressed_content,
        media_type=content_type,
        headers={
            "Content-Encoding": encoding,
            "Content-Length": str(len(compressed_content)),
            "Vary": "Accept-Encoding"
        }
    )
    
    return response

def compress_response_middleware(request: Request, call_next):
    """
    Middleware to automatically compress responses.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware function
        
    Returns:
        Compressed response
    """
    # Get the best acceptable encoding
    encoding = get_acceptable_encoding(request)
    
    # Call the next middleware/endpoint
    response = call_next(request)
    
    # Check if response should be compressed
    if encoding and response.status_code == 200:
        content = response.body
        if len(content) >= 1024:  # Only compress if content is >= 1KB
            compression_manager = CompressionManager()
            compressed_content = compression_manager.compress_content(content, encoding)
            
            # Update response
            response.body = compressed_content
            response.headers["Content-Encoding"] = encoding
            response.headers["Content-Length"] = str(len(compressed_content))
            response.headers["Vary"] = "Accept-Encoding"
    
    return response

def create_compressed_streaming_response(
    content_generator,
    encoding: str,
    content_type: str = "application/json"
) -> StreamingResponse:
    """
    Create a compressed streaming response.
    
    Args:
        content_generator: Generator yielding content chunks
        encoding: Compression encoding
        content_type: Content type
        
    Returns:
        Compressed streaming response
    """
    def compress_stream():
        compression_manager = CompressionManager()
        
        # Initialize compression
        if encoding == "gzip":
            compressor = gzip.GzipFile(mode='wb', fileobj=None)
        elif encoding == "deflate":
            compressor = zlib.compressobj(level=6)
        elif encoding == "br":
            try:
                import brotli
                compressor = brotli.Compressor(quality=6)
            except ImportError:
                logger.warning("Brotli not available, falling back to gzip")
                compressor = gzip.GzipFile(mode='wb', fileobj=None)
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")
        
        # Compress content chunks
        for chunk in content_generator:
            if isinstance(chunk, str):
                chunk = chunk.encode('utf-8')
            
            if encoding == "gzip":
                compressed_chunk = compressor.compress(chunk)
                if compressed_chunk:
                    yield compressed_chunk
            elif encoding == "deflate":
                compressed_chunk = compressor.compress(chunk)
                if compressed_chunk:
                    yield compressed_chunk
            elif encoding == "br":
                compressed_chunk = compressor.process(chunk)
                if compressed_chunk:
                    yield compressed_chunk
        
        # Finalize compression
        if encoding == "gzip":
            final_chunk = compressor.flush()
            if final_chunk:
                yield final_chunk
        elif encoding == "deflate":
            final_chunk = compressor.flush()
            if final_chunk:
                yield final_chunk
        elif encoding == "br":
            final_chunk = compressor.finish()
            if final_chunk:
                yield final_chunk
    
    return StreamingResponse(
        compress_stream(),
        media_type=content_type,
        headers={
            "Content-Encoding": encoding,
            "Vary": "Accept-Encoding"
        }
    )

def optimize_response_size(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize response content to reduce size.
    
    Args:
        content: Response content
        
    Returns:
        Optimized content
    """
    def optimize_value(value):
        if isinstance(value, dict):
            return {k: optimize_value(v) for k, v in value.items() if v is not None}
        elif isinstance(value, list):
            return [optimize_value(v) for v in value if v is not None]
        elif isinstance(value, str) and value.strip() == "":
            return None
        elif isinstance(value, (int, float)) and value == 0:
            return None
        else:
            return value
    
    return optimize_value(content)

def add_compression_headers(response: Response, encoding: str):
    """
    Add compression headers to response.
    
    Args:
        response: FastAPI response object
        encoding: Compression encoding
    """
    response.headers["Content-Encoding"] = encoding
    response.headers["Vary"] = "Accept-Encoding"

def get_compression_stats(content: bytes, compressed_content: bytes) -> Dict[str, Any]:
    """
    Get compression statistics.
    
    Args:
        content: Original content
        compressed_content: Compressed content
        
    Returns:
        Compression statistics
    """
    original_size = len(content)
    compressed_size = len(compressed_content)
    compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    
    return {
        "original_size_bytes": original_size,
        "compressed_size_bytes": compressed_size,
        "compression_ratio_percent": round(compression_ratio, 2),
        "bytes_saved": original_size - compressed_size
    }

# Global compression manager instance
compression_manager = CompressionManager() 