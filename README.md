# Djangoblog PP4

## DjangoBlog is a fully functional blogging platform built using Django. It allows users to create, read, update, and delete their blog posts, comment on articles, and manage their favorite posts. The project follows best practices for Django development, including user authentication, database management, and responsive design.

![Screens](/static/images/devices.jpg)

## Project Revisions & Resubmission Based on Feedback

This section outlines all improvements made after initial feedback, documenting the actions taken to address each issue before resubmitting the project for reassessment.

### 1. Full UI Customization

- Originally, the site looked very similar to the walkthrough project.
- Action Taken:
  - The navbar, colors, and menu styles were redesigned to reflect a unique identity
  - Added card-based design for post previews with shadows and borders
  - Implemented custom styling for buttons and forms
  - Added hover effects for interactive elements

### 2. Agile Workflow (Kanban)

- There was no clear issue structure or milestones.
- Action Taken:
  - A GitHub Kanban board has been created under the "Projects" tab
  - Each task or feature has been defined as an issue
  - Milestones have been created for each major feature (Favorites, Comments, About page, etc.)
  - Draft issues are no longer added to the board before implementation

### 3. Adding Docstrings and Comments

- The project lacked documentation within the codebase.
- Action Taken:
  - All key classes and functions now include clear Python docstrings using the format:  
    `"""This class/function does WXYZ..."""`
  - Important methods in views, models, and forms are now commented for clarity
  - Added comprehensive comments to HTML templates
  - Added inline comments to CSS files
  - Improved code readability with consistent documentation style

### 4. Fixing the Comment Editing Feature

- Feedback noted: "Editing comments does not work."
- Action Taken:
  - The views and templates related to comment editing were reviewed and fixed
  - The comment form now renders properly and saves updates
  - Local testing confirmed successful edit functionality
  - Added user feedback messages for successful edits

### 5. Expanding the README.md File

- The original README.md was missing essential documentation.
- Action Taken:
  - Deployment instructions for Heroku added
  - Testing instructions included
  - Added detailed feature descriptions
  - Included technology stack information
  - Added milestone tracking
  - Updated UI/UX documentation

### 6. Error Handling and Custom Pages

- Added custom 404 error page with:
  - Clear error message
  - Return to home button
  - Consistent styling with main site
  - Proper error handling in views
  - Configuration in settings.py

### 7. Social Media Integration

- Added real social media links in footer
- Implemented proper link formatting
- Added target="\_blank" for external links
- Maintained consistent styling

# Features

1. User Authentication (Signup, Login, Logout)
2. Create, Edit, and Delete Posts
3. Comment System (Add, Edit, Delete)
4. Favorites Model (Save and Manage Favorite Posts)
5. Responsive UI (Mobile-First Design)
6. Secure Authorization (Only authors can edit/delete their posts)
7. Admin Panel Integration (Manage posts, users, and comments)
8. Deployment Ready (Runs on Heroku/GitHub Pages)
9. Custom Error Pages (404)
10. Social Media Integration

# Technologies Used

- Backend: Django, Python
- Frontend: Bootstrap, HTML, CSS, JavaScript
- Database: SQLite/PostgreSQL
- Authentication: Django Allauth
- Version Control: Git, GitHub
- Deployment: Heroku/GitHub Pages

## Front-End Design

The front-end follows best practices in UI/UX design:

1. Responsive Design (Mobile-Friendly)

   - The website is designed using a mobile-first approach, ensuring it adapts to different screen sizes
   - Uses Bootstrap grid system (col-md, col-lg, col-sm) to maintain a structured layout across devices
   - Implements responsive images and media queries

2. Clean and Readable Layout

   - Consistent spacing and typography
   - Clear visual hierarchy
   - Card-based design for content
   - Proper use of white space

3. Easy Navigation and User Flow

   - Intuitive navigation bar at the top
   - Active page highlighting
   - Clear call-to-action buttons
   - Breadcrumb navigation where appropriate

4. Interactive User Actions
   - Like and Favorite Buttons
   - Comment System
   - Social Media Integration
   - Custom Error Pages

## HTML Validation

- All HTML code has been checked using official validators (e.g., W3C Validator for HTML)
- Fixed any validation errors
- Ensured semantic HTML structure

![Screens](/static/images/htmlvalidation.png)

## Deployment

Heroku Deployment [The live link is here](https://djangoblog17-173e7e5e5186.herokuapp.com/)

## Media

- The photos used on the home page are from [Sweden Herald](https://swedenherald.com/)
- Icons from [Font Awesome](https://fontawesome.com/)

## Milestones

### Milestone 1: Initial Setup & Core Features

- Set up Django project and basic app structure
- Configure environment variables and PostgreSQL on Heroku
- Add user registration/login using `django-allauth`
- Implement core blog post creation and comment system
- Setup Cloudinary for media handling  
  **Status:** Completed  
  **Completed on:** 2025-02-28

### Milestone 2: UI & UX Enhancement

- Add responsive card design for blog post previews
- Style navbar links: Login, Register, Logout, Favorites using Bootstrap classes
- Add working social links to the footer
- Highlight active navigation tabs
- Design custom 404 error page with return button
- Improve comment edit user experience and layout  
  **Status:** Completed  
  **Completed on:** 2025-03-15

### Milestone 3: Documentation, Testing & Deployment

- Add full testing instructions to `README.md`
- Add deployment steps (Heroku, env vars, Cloudinary)
- Include Wireframes, Mockups, and DB Diagram
- Set `DEBUG = False` in production
- Improve error handling and redirections  
  **Status:** In Progress  
  **Start Date:** 2025-03-15  
  **Due Date:** 2025-03-20
