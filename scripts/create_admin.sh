
curl  -i -X 'POST' \
  'http://0.0.0.0:8000/admins/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "string1111111",
  "email": "1@1111.ru",
  "password": "1234567890",
  "enabled": true
}'


