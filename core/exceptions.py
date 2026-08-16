from fastapi import HTTPException, status

class DomainException(HTTPException):
    """Exceção base de domínio para tratamento padronizado"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class BusinessException(DomainException):
    """Exceção para violações de regras de negócio."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(detail=detail, status_code=status_code)

class ResourceNotFoundException(DomainException):
    """Exceção para recursos não encontrados no banco ou no storage."""
    def __init__(self, detail: str = "NOT FOUND"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)

class UnauthorizedException(DomainException):
    """Exceção para falhas de autenticação ou falta de permissão."""
    def __init__(self, detail: str = "UNAUTHORIZED"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)
