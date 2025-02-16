# Djangoblog PP4

## DjangoBlog is a fully functional blogging platform built using Django. It allows users to create, read, update, and delete their blog posts, comment on articles, and manage their favorite posts. The project follows best practices for Django development, including user authentication, database management, and responsive design.

![Screens](/static/images/devices.jpg)

# What is an Original Custom Model in my DjangoBlog Project?

## The Favorites Model in my DjangoBlog project allows users to save their favorite posts for easy access later. This feature enhances the user experience by enabling them to bookmark posts they find interesting or useful.

## How Does the Favorites Model Work?
Users can mark posts as "Favorite".
Favorite posts are stored in the database.
Users can view their saved posts on a dedicated "Favorites" page.
They can also remove posts from their favorites list.

## Add or Remove a Favorite
If a post is not already in favorites, it is added.

If a post is already in favorites, it is removed.

In the favorites.html template, you display the list of saved posts.

In views.py, there is the logic for adding, displaying, and removing favorite posts.

Retrieves all favorite posts for the logged-in user.

Passes them to the favorites.html template for display.

# Features 
 1. User Authentication (Signup, Login, Logout)
 2. Create, Edit, and Delete Posts
 3. Comment System (Add, Edit, Delete)
 4. Favorites Model (Save and Manage Favorite Posts)
 4. Responsive UI (Mobile-First Design)
 5. Secure Authorization (Only authors can edit/delete their posts)
 6. Admin Panel Integration (Manage posts, users, and comments)
 7. Deployment Ready (Runs on Heroku/GitHub Pages)

# Technologies Used 
- Backend: Django, Python
- Frontend: Bootstrap, HTML, CSS, JavaScript
- Database: SQLite/PostgreSQL
- Authentication: Django Allauth
- Version Control: Git, GitHub
- Deployment: Heroku/GitHub Pages


## Front-End Design
The front-end follows  practices in UI/UX design :

 1. Responsive Design (Mobile-Friendly)
- The website is designed using a mobile-first approach, ensuring it adapts to different screen sizes.
- Uses Bootstrap grid system (col-md, col-lg, col-sm) to maintain a structured layout across devices.

2. Clean and Readable Layout

3. Easy Navigation and User Flow

- An Easy navigation bar at the top allows easy access to different sections.
- Active page highlighting in the navbar helps users identify their current location.
- Users can quickly access home, posts, login, signup, and favorites pages.

 4. Interactive User Actions

Like and Favorite Buttons: Users can like and save posts for later reference.
Comment System: Users can interact with posts by leaving comments, improving engagement.

 ## HTML Validation

- All HTML, code has been checked using official validators (e.g., W3C Validator for HTML.

![Screens](/static/images/htmlvalidation.png)


## Deployment; Heroku Deployment [The live link is here](https://djangoblog17-173e7e5e5186.herokuapp.com/)

 - the page will be automatically refreshed with a detailed ribbon display to indicate the successful deployment.


## Media
- The photos used on the home page are from This site and only for test [Font Awesome](https://swedenherald.com/)
