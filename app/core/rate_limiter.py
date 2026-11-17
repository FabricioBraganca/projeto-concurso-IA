import time
import threading
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status


class SlidingWindowRateLimiter:
    """
    Limitador de taxa em memória com janela deslizante (Sliding Window).
    Thread-safe e sem dependências externas.
    """
    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            
            # Remove requisições que caíram fora da janela de tempo
            timestamps = [ts for ts in self._requests[key] if ts > cutoff]
            self._requests[key] = timestamps
            
            if len(timestamps) >= max_requests:
                return False
                
            self._requests[key].append(now)
            return True

    def get_retry_after(self, key: str, window_seconds: int) -> int:
        with self._lock:
            now = time.time()
            timestamps = self._requests.get(key, [])
            if not timestamps:
                return 0
            oldest = timestamps[0]
            retry = int(oldest + window_seconds - now)
            return max(1, retry)


rate_limiter = SlidingWindowRateLimiter()


def rate_limit(key_prefix: str, max_requests: int, window_seconds: int):
    """
    Dependency injetável no FastAPI para limitar chamadas a rotas específicas.
    Exemplo: Depends(rate_limit("simulado_gerar", max_requests=10, window_seconds=3600))
    """
    def dependency(request: Request):
        # Identificador do cliente por IP ou token
        client_ip = request.client.host if request.client else "127.0.0.1"
        auth_cookie = request.cookies.get("access_token", "")
        identifier = f"{client_ip}:{auth_cookie[-10:]}" if auth_cookie else client_ip
        rate_key = f"{key_prefix}:{identifier}"

        if not rate_limiter.is_allowed(rate_key, max_requests, window_seconds):
            retry_after = rate_limiter.get_retry_after(rate_key, window_seconds)
            minutos = max(1, window_seconds // 60)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de requisições excedido. Máximo permitido: {max_requests} a cada {minutos} minuto(s). Tente novamente em {retry_after} segundos.",
                headers={"Retry-After": str(retry_after)}
            )
        return True

    return dependency
