# Relational Database for Authentication and Authorization

- `amqtt.contrib.auth_db.AuthUserDBPlugin` (authentication) verify a client's ability to connect to broker
- `amqtt.contrib.auth_db.AuthTopicDBPlugine` (authorization) determine a client's access to topics  

Relational database access is supported using SQLAlchemy so MySQL, MariaDB, Postgres and SQLite support is available.

For ease of use, the [`user_mgr` command-line utility](auth_db.md/#user_mgr) to add, remove, update and 
list clients. And the [`topic_mgr` command-line utility](auth_db.md/#topic_mgr) to add client access to
subscribe, publish and receive messages on topics.

## Authentication Configuration

::: amqtt.contrib.auth_db.UserAuthDBPlugin.Config
    options:
      show_source: false
      heading_level: 4

## Authorization Configuration

::: amqtt.contrib.auth_db.TopicAuthDBPlugin.Config
    options:
      show_source: false
      heading_level: 4

## Command line for authentication

::: mkdocs-typer2
    :module: amqtt.contrib.auth_db.user_mgr_cli
    :name: user_mgr

## Command line for authorization

::: mkdocs-typer2
    :module: amqtt.contrib.auth_db.topic_mgr_cli
    :name: topic_mgr
