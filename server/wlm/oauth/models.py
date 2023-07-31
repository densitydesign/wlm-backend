from django.db import models
from django.contrib.auth import get_user_model

User  = get_user_model()

class OAuth2Token(models.Model):
    name = models.CharField(max_length=40)
    token_type = models.CharField(max_length=40)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def to_token(self):
        return dict(
            access_token=self.access_token,
            token_type=self.token_type,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
        )
