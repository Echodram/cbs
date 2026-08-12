# CBS — Center for Biblical Studies (Backend)

Backend Django pour **Center for Biblical Studies**, une plateforme d'enseignement biblique en ligne. Il expose une API REST (Django REST Framework) pour la gestion des cours, des utilisateurs, des blogs/événements, ainsi qu'un système de chat en temps réel (WebSocket) pour un forum communautaire.

## Stack technique

- **Langage** : Python
- **Framework** : Django + Django REST Framework
- **Temps réel** : Django Channels + Daphne (ASGI) + Redis (canal WebSocket)
- **Base de données** : SQLite en développement, PostgreSQL (Supabase) en production
- **Stockage fichiers** : Supabase Storage (images, livres, audios, vidéos)
- **Fichiers statiques** : WhiteNoise
- **Authentification** : Token DRF (`rest_framework.authtoken`) + Session
- **Déploiement** : Docker / Docker Compose (hébergé sur Leapcell)

## Structure du projet

```
cbs_back/            Configuration du projet Django (settings, urls, asgi/wsgi)
  settings/https://github.com/Echodram/nutrimboa.git
    base.py            Configuration commune
    dev.py              Configuration développement (SQLite, Redis local)
    prod.py             Configuration production (PostgreSQL/Supabase, Redis distant)
  supabase_service.py   Client Supabase (upload/gestion de fichiers)

backend/              App cœur : utilisateurs, cours, leçons, livres, audios/vidéos, chat
  models.py             CustomUser, Course, Enrollement, Lesson, Book, Audio, Video, Room, Message, RoomParticipant
  views.py, serializers.py, urls.py

cbs_blogs/            App Blogs & Events
  models.py             Blog, Event

forum/                App du chat/forum en temps réel (WebSocket)
  consumers.py, routing.py   Logique WebSocket
  views.py, serializers.py, urls.py   API REST du chat (réutilise les modèles de `backend`)
```

## Fonctionnalités principales

### Utilisateurs & authentification
- Inscription / connexion par email (`CustomUser`, rôles : étudiant, enseignant, admin)
- Authentification par token DRF
- Réinitialisation de mot de passe par email

### Cours
- Création et gestion de cours (par les enseignants)
- Inscription des étudiants à des cours (`Enrollement`)
- Leçons associées à un cours (`Lesson`)

### Bibliothèque
- Livres (`Book`), audios et vidéos d'enseignement, avec upload et catégorisation

### Blogs & Événements
- Articles de blog (`Blog`) et événements (`Event`) avec image et description

### Forum / Chat en temps réel
- Salons de discussion (`Room`), publics ou privés, avec participants (`RoomParticipant`)
- Messages (`Message`) texte, image ou fichier, avec édition et suppression douce (soft delete)
- Communication en temps réel via WebSocket (`ws/chat/<room_id>/`)

## Principaux endpoints API

Toutes les routes REST sont préfixées par leur app respective.

### `backend/` (racine `/`)
| Endpoint | Description |
|---|---|
| `POST /login/` | Connexion (email/mot de passe), retourne un token |
| `POST /user/` | Inscription |
| `GET /me/` | Profil de l'utilisateur connecté |
| `GET/POST /course/` | Liste / création de cours |
| `POST /course/enroll/` | Inscription à un cours |
| `GET/POST /lesson/` | Leçons (filtrable par `?course_uuid=`) |
| `GET/POST /book/` | Livres |
| `GET /teachers/` | Liste des enseignants et leurs cours |
| `GET /students/` | Liste des étudiants et leurs inscriptions |
| `POST /request_reset/` | Demande de réinitialisation de mot de passe |
| `POST /reset/<token>/` | Réinitialisation du mot de passe |

### `cbs_blogs/` (racine `/`)
| Endpoint | Description |
|---|---|
| `GET/POST /blogs/` | Articles de blog |
| `GET/POST /event/` | Événements |

### `forum/` (préfixe `/chat/api/`)
| Endpoint | Description |
|---|---|
| `GET/POST /rooms/` | Salons de discussion |
| `POST /rooms/<id>/join/` | Rejoindre un salon |
| `GET /rooms/<id>/messages/` | Messages d'un salon |
| `GET /rooms/<id>/participants/` | Participants d'un salon |
| `GET/POST /messages/` | Messages (filtrable par `?room_id=`) |
| `GET /users/` | Utilisateurs du forum |
| `GET /users/online/` | Utilisateurs en ligne |

### WebSocket
| Route | Description |
|---|---|
| `ws/chat/<room_id>/` | Connexion temps réel à un salon de chat |

## Installation

### Prérequis
- Python 3.11+
- Redis (nécessaire pour le chat en temps réel)

### Étapes

```bash
git clone <url-du-repo>
cd cbs
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Créer un fichier `.env` à la racine avec les variables suivantes :

```
DJANGO_SECRET_KEY=
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données (production, PostgreSQL/Supabase)
DB_NAME=
DB_USERNAME=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# Stockage fichiers (Supabase)
SUPABASE_URL=
SUPABASE_KEY=

# Redis (production)
LEAPCELL_REDIS_HOST=
LEAPCELL_REDIS_PORT=
LEAPCELL_REDIS_PASSWORD=
LEAPCELL_REDIS_DB=
```

Puis :

```bash
python manage.py migrate
python manage.py runserver
```

Par défaut, le projet démarre avec la configuration `cbs_back.settings.dev` (SQLite + Redis local).

### Avec Docker

```bash
docker-compose up --build
```

## Tests

```bash
python manage.py test
```

## Points connus / à améliorer

- `djangorestframework-simplejwt` est présent dans `requirements.txt` mais n'est pas activé (l'authentification utilisée est le Token DRF).
- Les identifiants sensibles (base de données, Redis, clé secrète Django, SMTP) doivent être fournis via variables d'environnement et jamais commités.
