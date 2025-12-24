#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
```

#### 2. Créer `Procfile` (optionnel mais recommandé)
```
web: daphne -b 0.0.0.0 -p $PORT config.asgi:application