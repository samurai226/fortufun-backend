from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
from jwt import decode as jwt_decode
from accounts.models import User


@database_sync_to_async
def get_user(token):
    """Récupérer l'utilisateur à partir du token JWT"""
    try:
        # Valider le token
        UntypedToken(token)
        
        # Décoder le token
        decoded_data = jwt_decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Récupérer l'utilisateur
        user_id = decoded_data.get('user_id')
        if user_id:
            user = User.objects.get(id=user_id)
            return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        pass
    
    return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Middleware pour l'authentification JWT dans les WebSockets"""
    
    async def __call__(self, scope, receive, send):
        # Récupérer le token depuis les query parameters
        query_string = scope.get('query_string', b'').decode()
        params = dict(qp.split('=') for qp in query_string.split('&') if '=' in qp)
        token = params.get('token')
        
        if token:
            scope['user'] = await get_user(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)