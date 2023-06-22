from itsdangerous import URLSafeTimedSerializer
from key import secret_key,salt
def token(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data,salt=salt)
