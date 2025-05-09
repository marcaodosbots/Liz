from TikTokApi import TikTokApi

with TikTokApi() as api:
    user = api.user(username="algum_usuario")
    print(user.info())  # ou outro método válido