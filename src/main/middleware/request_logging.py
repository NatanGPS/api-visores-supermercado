from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging
import json
import traceback

from src.main.security.api_key import API_KEYS

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        api_logger = logging.getLogger("api")
        err_logger = logging.getLogger("error")

        try:
            
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8") if body_bytes else ""
                try:
                    body_obj = json.loads(body_text) if body_text else None
                except Exception:
                    body_obj = body_text
            except Exception:
                body_obj = None
# Podemos pensar como uma forma nova de declara as funções
            x_api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")

            
            api_key_name = None
            if x_api_key:
                api_key_name = API_KEYS.get(x_api_key)
#            
            response = await call_next(request)

            log_entry = {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status_code": response.status_code,
                "api_key": api_key_name,
                "body": body_obj,
            }
# Podemos pensar como uma forma nova declarar o log (Como Pegar a informação) ---> Poderiamos pegar daqui
            api_logger.info(json.dumps(log_entry, ensure_ascii=False))

            return response

        except Exception as exc:  
            err_logger.error("Unhandled exception: %s", traceback.format_exc())
            raise
