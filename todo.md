### Service Admin

##### сreate
Создание Admin. Все данные. Если есть login и пароль, то создаем Account. 
Если указан список ролей, то их создаем.
*Done*


#### update
Меняем только учетные данные. Ни Account, и роли не меняются здесь
*Done*

#### enable
активируем Admin
*Done*

#### disable
деактивируем Admin
*Done*

#### attach_account
Добавляем аккаунт, если его нет
*Done*

#### detach_account
Убираем аккаунт если есть
*Done*

#### change_password 
Меняем пароль
*Done*

#### grant_roles
Добавляем роли
*Done*

#### revoke_roles
Удаляем роли
*Done*


#### delete
Удаляем Admin. Нельзя удалить Admin, если есть User, Client, Ticket 
которые были созданы этим Admin.
*Done*

#### get_by_id
Получаем Admin по id
*Done*

#### find_by_login
Ищем Admin по login
*Done*

#### get_all
Получаем список всех admin-ов
*Done*



