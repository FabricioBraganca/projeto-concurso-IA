from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login-form",
    auto_error=False
)


def get_token_from_request(request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Recupera o token JWT do header Authorization (Bearer) ou do cookie 'access_token'."""
    if bearer_token:
        return bearer_token
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # Remove 'Bearer ' caso o cookie tenha o prefixo
        if cookie_token.startswith("Bearer "):
            return cookie_token.replace("Bearer ", "", 1)
        return cookie_token
    return None


def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """Valida o token JWT e retorna o usuário autenticado correspondente."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.ativo:
        raise credentials_exception

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """
    Retorna o usuário autenticado se houver token válido.
    Caso contrário, retorna ou cria o usuário padrão (id=1) para navegação sem travar o usuário.
    """
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            try:
                user_id = int(payload.get("sub"))
                user = db.query(User).filter(User.id == user_id, User.ativo == True).first()
                if user:
                    return user
            except ValueError:
                pass

    # Fallback para o usuário padrão (id=1)
    default_user = db.query(User).filter(User.id == 1).first()
    if not default_user:
        from app.core.security import hash_password
        default_user = User(
            id=1,
            nome="Concurseiro Padrão",
            email="aluno@concurseiroai.com.br",
            senha_hash=hash_password("concurseiro123"),
            ativo=True
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
    return default_user
