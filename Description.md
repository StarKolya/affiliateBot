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

The bot has 2 roles: admin and user and the user can be of type applicant or referrer or both.

Admin has the ability to create niches, and job postings. For each job posting admin has a possibility to add questions from a question bank for the applicant, set description and title and type of a posting. Later he can view the applications and change each application status to the appropriate. The admin can also see the referral statistics of each user and with overall stats.

As mentioned above, the user can be of 2 types:
Referrer is basically a talent seeker, this type of user can go to the referral tab, create link and share that link with others, he can later view his statistics per each created link, those have a functionlaity similar to utm tags. Each user referred by referrer is tracked and the referrer is being rewarded after user's application on any job posting is set to accepted. The money are sent to his internal balance and later when the referrer wants, he may create a payout request, which will later be processed by the admin

Applicant is a regular use who's using the platform to find a job opportunity, he can search through different jobs and apply for any filling in the selected questions. 


## Future improvements 

In the later versions of the project, such functionality was added:
* Sorting and filtering of application within a job posting (it became hard to navigate through lots of applications)
* Extra functionality for the referral system. On the latest version the user has an ability to manage link so it points not only to the bot itself, but directly to the selected job posting 
* Roles were introduced. There was a need to have an admin with restricted access, therefore roles were added alongside with the functionality for assigning roles 
* Questionbank. Currently the admin can select the questions from the questionbank that were injected to the DB table, however there was a need to add new quesitons to the system from the bot. The questions were also improved, before it was just text field questions, in the latest version there are yes_no, numeric and descriptive questions.