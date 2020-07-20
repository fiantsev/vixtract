#имя пользователя для которого необходимо создать сервер на JupyterHub'e
username=$1

#пароль пользователя генерируется рандомный
password=$(mktemp -u XXXXXX)

#пароль суперюзера :) insecure - не надо так использовать
sudoPassword=sudoPassword

#хост тачки на которой крутиться JupyterHub
host=192.168.44.117
hubapi=http://$host/studio/hub/api

#необходимо создать пользователя с админскими правами на JupyterHub'e и задать ему api_key
#делается через jupyterhub_config.py конфиг след свойства: c.JupyterHub.api_tokens, c.Authenticator.admin_users, c.JupyterHub.admin_access
#api_key здесь это тот же что задан для админка в свойстве c.JupyterHub.api_tokens
api_key=b2a635cbef409b30b54c6cd1f39b180ec88c264ce135af9e5e407221bfab1ed9

#генерим корректный формат пароля для Linux'a (для Ubuntu 18.04 в данном случае)
encrypted_password=$(openssl passwd -6 -salt $password $password)
echo sudoPassword | sudo -S useradd -m -p "$encrypted_password" "$username" 2>/dev/null
#echo user created: $username/$password

#Создаем пользователя на JupyterHub'e
curl -s -X POST -H "Authorization: token $api_key" $hubapi/users/$username >/dev/null

#Запускаем для пользователя "single-user notebook server"
curl -s -X POST -H "Authorization: token $api_key" $hubapi/users/$username/server >/dev/null

#получаем новый токен для пользователя (чтобы впоследствии использовать его для авторизации)
json=$(curl -s -X POST -H "Authorization: token $api_key" $hubapi/users/$username/tokens)
token=$(node -e "console.log(JSON.parse(process.argv[1]).token)" "$json")
echo $token

#ссылка которую надо вбить в браузер чтобы попасть в сессию для конкретного пользователя (с авто авторизацией по токену)
laburl=http://$host/studio/user/$username/lab?token=$token
#echo laburl: $laburl