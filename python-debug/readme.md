## настройки jupyterhub_config.py
добавляем пользователя admin и админскими правами в JupyterHub и генерим токен для него (впоследствии будет использоватся)

```
c.Spawner.default_url = '/lab' 
c.JupyterHub.bind_url = 'http://0.0.0.0:8000/studio'
c.JupyterHub.api_tokens = {
    'b2a635cbef409b30b54c6cd1f39b180ec88c264ce135af9e5e407221bfab1ed9': 'admin',
}
c.Authenticator.admin_users = set('admin')
c.JupyterHub.admin_access = True
```

## install.sh
запустить скрипт install.sh на Ubuntu 18.04 с правами админа

```
sudo ./install.sh
```

## proxy container nginx config
необходимо добавить следующие изменения в proxy контейнере платформы (nginx конфиг)

```
location /studio {
                proxy_pass http://192.168.44.117:8000;
                proxy_redirect   off;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                # websocket headers
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
        }
```

## create_user.sh
создает нового пользователя в Linux'e и на JupyterHub'e после чего инициализирует новый сервер под пользователя

пример использования

```
./create_user.sh userName
```