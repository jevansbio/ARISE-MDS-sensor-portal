# PAM

Link to our website: ""

PAM is a dashboard where you can have an overview over deployments in the field, with their associated audio files.

## Contributors

- Johanne Burns Bergan
- Sander Stenbakk Ekanger
- Jacob Gullesen Hagen
- Ingrid Helene Kvitnes
- Noah Lund Syrdal
- Siri Arnesen
- Marius Bølset Gisleberg


# Må endre
## Table of contents
- [PAM](#pam)
  - [Contributors](#contributors)
  - [Table of contents](#table-of-contents)
  - [Environment](#environment)
    - [Setting Up the Correct Versions](#setting-up-the-correct-versions)
    - [Start development](#start-development)
  - [Login system](#login-system)
  - [Dataset](#dataset)
  - [Technologies](#technologies)
    - [Frontend](#frontend)
    - [Backend](#backend)
    - [Database](#database)
  - [Features](#features)
  - [Tests](#tests)
  - [Responsiveness](#responsiveness)
  - [HTML Web Storage API](#html-web-storage-api)
    - [LocalStorage Implementation](#localstorage-implementation)
    - [SessionStorage Implementation](#sessionstorage-implementation)
  - [Version Control](#version-control)
  - [Web accessibility](#web-accessibility)
    - [Testing with Lighthouse](#testing-with-lighthouse)
  - [Sustainable web development](#sustainable-web-development)
    - [Supporting the UN’s Sustainable Development Goals (SDGs):](#supporting-the-uns-sustainable-development-goals-sdgs)
  - [Architecture](#architecture)

## Environment

The application is designed to work with Node.js version 22.7.0 and npm version 10.8.2. We can't guarantee that it will work properly with other versions of Node.js.

## Technologies

We selected technologies that enable us to build a responsive, efficient, and scalable web application. Our frontend stack allows for dynamic, interactive interfaces with strong type safety and consistent styling. **MER OM BACKEND HER**

### Frontend
- **React**: A JavaScript library for building interactive, component-based user interfaces.
- **TypeScript**:  A superset of JavaScript that adds static typing for improved code quality and maintainability.
- **Vite**: A fast development tool that accelerates build times and hot module replacement.
- **Tailwind CSS**: A utility-first CSS framework for rapid and consistent styling.
- **TanStack Query**: A data-fetching library for web applications, but in more technical terms, it makes fetching, caching, synchronizing and updating server state in your web applications a breeze.
- **TanStack Router**: A fully type-safe router with built-in data fetching, stale-while revalidate caching and first-class search-param APIs.

# ENDRE DENNE

### Backend
- **Node.js**: A JavaScript runtime that allows for building scalable server-side applications.
- **Apollo Server**: A GraphQL server library that provides a flexible and efficient API layer.
- **TypeScript**: Adds type safety to backend code, reducing errors and improving readability.
- **GraphQL**: A query language for APIs that enables efficient data fetching and flexible queries.
- **Prettier**: Ensures consistent code formatting across the backend codebase.

# Om postgres her
### Database
- **MongoDB**: A NoSQL database that stores data in flexible, JSON-like documents, allowing for efficient storage and quick retrieval of large datasets.

## Features

To meet the requirements of our application, we have implemented key features that make it easy to find deployments. Users can filter, and sort deployments in ways that fit the purpose of the platform.

1. Deployment Discovery
    - **View lookup table of deployments**: Users are able to view a lookup table for deployments, with information about the last uploaded file.
    - **Filters**: Users can filter deployments by country and status.
    - **Sort Options**: Users can sort deployments alphabetically based on several fields.

## Tests

# MÅ GJØRE NOE HER

## Responsiveness
This was not been a huge focus, but there are some pages that are suited to smaller devices like phones.

- **Dynamic Layout**: The design adjusts automatically to different screen dimensions and orientations on select pages, ensuring a smooth and user-friendly experience on both mobile and desktop devices.
- **Testing**: During development, the application was tested on a range of screen sizes, including larger mobile screens like the iPhone 14 Pro Max, to ensure compatibility and usability.

While the application performs well on these devices, we recognize the need to refine and expand testing to include smaller screens in future iterations.

## HTML Web Storage API

# Føler ikke denne er så superviktig

The project utilizes the HTML Web Storage API for managing data persistence across user sessions. Specifically, it employs:

### LocalStorage Implementation
We have utilized localStorage to persist data on the client side, allowing it to remain available even after the browser is closed and reopened. While we acknowledge that localStorage is not the most secure method for handling sensitive data, it provides a practical approach for implementing user logic at this stage of development. Our focus has been on frontend functionality, logic, and features, making this a sufficient solution for our current needs. Below is a breakdown of how we use localStorage in the application:

**1. User Logic**: 
LocalStorage is used to store data tied to individual users. This includes information such as booklists and preferences, which are essential for creating a personalized experience. While this is not ideal for secure, large-scale applications, it demonstrates a functional approach to user logic in a frontend-focused project.

**2. Booklists**:
Each user's booklists are saved in localStorage, allowing them to access previously saved books every time they revisit the site. This feature is central to our application, enabling users to maintain their curated lists across sessions without needing a backend integration.

**3. Theme Preferences (Light/Dark Mode)**:
User-selected theme preferences are also stored in localStorage. If a user specifies a preference for light or dark mode, this choice is remembered across sessions. For first-time visitors or users who haven’t set a specific preference, the application defaults to the system's color scheme, ensuring a seamless and adaptive experience.


### SessionStorage Implementation
We have integrated sessionStorage to manage temporary data storage for user interactions within a single page session. This data is cleared when the page session ends, such as when the page is closed or reloaded. Below is a breakdown of how sessionStorage is used in the application:

**1. Search, Filtering, and Sorting**: sessionStorage is utilized to save the user's search input, selected filters, and sorting preferences in the filter menu and search functionalities. This ensures that even if the user reloads the page or navigates back after viewing a book card, their choices remain intact for the duration of the session. 

## Version Control

Our project uses Git for version control, hosted on GitHub: [https://github.com/BA07-NINA/ARISE-MDS-sensor-portal-Pam](https://github.com/BA07-NINA/ARISE-MDS-sensor-portal-Pam). We manage our codebase using:

**Branching Strategy**
"Testing": Contains the mostly stable functionality without major bugs.

Other branches: Each new feature or fix is developed on a separate branch. Each branch is connected to an issue in ClickUp. Branches are integrated into "Testing" through pull requests (PRs) with code review from a minimum of one team member, ensuring quality and consistency across the codebase.

**Tracking**

Issue Creation: Each task or bug is documented in an issue.

**Project Boards and Workflow**
To ensure an organized and efficient development process, we utilized project boards throughout the project. We structured our work into five sprints For every sprint, we created a dedicated sprint board with columns for To Do, In Progress, and Done. This visual approach helped us clearly see what needed to be done and track progress in real time.

This workflow helps us maintain a clear and organized development process, ensuring high-quality code and efficient collaboration.


-   We decided not to use videos, as they consume a lot of energy. Instead, we use images, which are more relevant to our app and essential for user experience.

## Architecture
The project is structured to maintain a clear separation of concerns and to ensure scalability and maintainability. Here is an overview of the **key** directories and files:

# Må endres
**Backend**
- `src/`: Contains the main source code for the backend.
    - `graphql/`: Handles GraphQL logic.
    - `server.ts`: Entry point for the backend server, setting up middleware and starting the application.
    - `types.ts`: TypeScript type definitions used in the backend.



**Select folders in frontend**

- `src/`: Contains the main source code for the frontend.
  - `components/`: Houses reusable React components, each in its own directory.
  - `auth/`
    - `AuthContext.d.ts`
    - `AuthContext.jsx`
  - `routes/`
    - `deployments/`
      - `$siteName/`
        - `-deploymentMapPage.tsx`
        - `-deploymentPage.tsx`: Landing page after clicking a deployment
        - `-deviceDataFilesPage.tsx`
        - `-deviceDetailPage.tsx`
        - `-siteDetailPage.tsx`
        - `$dataFieldTest.tsx`
        - `index.tsx`
      - `-deploymentsPage.tsx`: Table view of all deployments
      - `index.tsx`: 
    - `__root.tsx`: Root component used for Tanstack Router
    - `login.tsx`Login page
    - `index.tsx`: Homepage
    - `map.tsx`: Map over all deployments
  - `types.ts`
  - `index.css`: Used to define tailwind
  - `main.tsx`: Define rotuer and query provider
- `index.html`: The entry HTML file for the frontend.


This structure ensures the project is organized, with each component and asset easy to locate and manage. It supports maintainability, scalability, and a streamlined development process.