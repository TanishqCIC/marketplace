Secondhand Design and Art Marketplace
This is a Django-based web application that models a marketplace for secondhand design and art products. The application provides a REST API for managing categories and products, including state transitions for product listings.

Features
User Authentication: Supports user registration and login.
Category Management: Admins can create, update, and delete product categories.
Product Management: Users can create, update, and manage products with different states (draft, new, accepted, rejected, banned).
State Transitions: Implements strict rules on how products can transition between states.
Email Notifications: Sends email alerts to product creators upon state changes.
Database: Utilizes PostgreSQL for data storage.

Technologies Used
Django
Django REST Framework
PostgreSQL
Docker
Python

Getting Started

Prerequisites
1. Docker
2. Django

Clone the repository:

git clone https://github.com/TanishqCIC/marketplace.git
cd marketplace
Create a .env file:

In the root directory of the project, create a .env file with the following content:

1. EMAIL_HOST_PASSWORD
2. DB_PASSWORD

Build and run the Docker containers:

docker-compose up --build
Access the application: Open your web browser and go to http://127.0.0.1:8000/.

Create and run migrations: Open a terminal and run the following command to create the database and apply migrations:
docker-compose exec web python manage.py migrate

Create a superuser (for admin access):
docker-compose exec web python manage.py createsuperuser

API Documentation
(https://www.notion.so/API-documentation-for-Whoppah-Marketplace-12cb67c348c680d5bc2ed4f54da6be54?pvs=4)

Running Tests
To run the test suite in the Docker container, use the following command:
docker-compose exec web python manage.py test

Contributing
Contributions are welcome! Please create a pull request or submit an issue for any feature requests or bugs.
