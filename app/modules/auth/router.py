from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.auth_dependency import get_current_user
from app.models import User
from app.schemas import UserCreateRequest, UserLoginRequest, UserResponse, TokenResponse

from app.core.rate_limiter import rate_limit

router = APIRouter(prefix="/auth", tags=["Autenticação & Usuários"])


@router.post("/cadastrar", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(
    dados: UserCreateRequest,
    db: Session = Depends(get_db),
    _limit: bool = Depends(rate_limit("auth_cadastrar", max_requests=10, window_seconds=300))
):
    """
    Cria uma nova conta de estudante com senha criptografada.
    """
    email_limpo = dados.email.strip().lower()
    
    # 1. Verifica se o e-mail já está em uso
    existente = db.query(User).filter(User.email == email_limpo).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está cadastrado no sistema."
        )

    # 2. Cria o novo usuário com hash bcrypt
    novo_usuario = User(
        nome=dados.nome.strip(),
        email=email_limpo,
        senha_hash=hash_password(dados.senha),
        ativo=True
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    return novo_usuario


from sqlalchemy import or_

@router.post("/login", response_model=TokenResponse)
def login_usuario(
    dados: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    _limit: bool = Depends(rate_limit("auth_login", max_requests=15, window_seconds=60))
):
    """
    Autentica o concurseiro com email (ou nome) e senha. Retorna o Token de Acesso JWT.
    """
    termo = dados.email.strip().lower()
    usuario = db.query(User).filter(
        or_(
            User.email == termo,
            User.nome.ilike(dados.email.strip())
        )
    ).first()

    if not usuario or not verify_password(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail/usuário ou senha incorretos."
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta conta de usuário foi desativada."
        )

    # Gera o token de acesso
    access_token = create_access_token(data={"sub": str(usuario.id), "email": usuario.email})
    
    # Grava cookie no navegador para facilitar uso nos templates web
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=usuario
    )


@router.post("/login-form")
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _limit: bool = Depends(rate_limit("auth_login_form", max_requests=15, window_seconds=60))
):
    """
    Endpoint compatível com o botão 'Authorize' da documentação Swagger UI (/docs).
    Aceita e-mail ou nome no campo 'username'.
    """
    termo = form_data.username.strip().lower()
    usuario = db.query(User).filter(
        or_(
            User.email == termo,
            User.nome.ilike(form_data.username.strip())
        )
    ).first()

    if not usuario or not verify_password(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail/usuário ou senha incorretos."
        )

    access_token = create_access_token(data={"sub": str(usuario.id), "email": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def obter_perfil_atual(usuario_atual: User = Depends(get_current_user)):
    """
    Retorna os dados do perfil do concurseiro atualmente autenticado.
    """
    return usuario_atual


@router.post("/logout")
def logout_usuario(response: Response):
    """
    Encerra a sessão removendo o cookie de autenticação.
    """
    response.delete_cookie("access_token")
    return {"mensagem": "Logout realizado com sucesso."}
