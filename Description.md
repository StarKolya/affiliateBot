# Affiliate bot description 

An affiliate management Telegram bot is a platform where users join via telegram, can browse through available job/partnership posting, apply to them or become a referer, create links invite people and earn money based of them.

---

## Purpouse and problem

The owner actively looks for new people in his team and the bot automates the hiring/partnership pipeline. It basically gives an opportunity to regular people to earn money by bringing a talent to our platform and makes it easier to go through the applications as they might be fully customized for the needs 

## Architecture

As a good programming practice layer architecture is used. 
All the code is divided into parts:
* models -> definition of tables in DB 
* repositories -> communication with the DB through ORM
* services -> actual business logic
* utils -> utility functions
* handlers -> the main flow of the app (divided into user and admin)
* keyboards -> predefined built buttons that are later being appended to the messages 

The separations ensures independetness of the functional parts and improves code readability 

## Tech stack 

* aiogram — async Telegram bot framework, previously used Telebot, this one is slightly more complex but is also more flexible
* Tortoise ORM — async ORM
* Aerich — database migration tool for Tortoise
* MySQL — relational database needed to store the strucutred data
* pydantic-settings — typed config loaded from .env


## Functionality description 

