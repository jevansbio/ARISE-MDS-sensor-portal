# PAM

PAM is a dashboard where you can have an overview over deployments in the field, with their associated audio files.

## Contributors

- Johanne Burns Bergan
- Sander Stenbakk Ekanger
- Jacob Gullesen Hagen
- Ingrid Helene Kvitnes
- Noah Lund Syrdal
- Siri Arnesen
- Marius Bølset Gisleberg

## Table of contents
- [PAM](#pam)
  - [Contributors](#contributors)
  - [Table of contents](#table-of-contents)
  - [Environment](#environment)
  - [Technologies](#technologies)
    - [Frontend](#frontend)
  - [Features](#features)
  - [Tests](#tests)
  - [Responsiveness](#responsiveness)
  - [Version Control](#version-control)
  - [Architecture](#architecture)

## Environment

The application is designed to work with Node.js version 22.7.0 and npm version 10.8.2. We can't guarantee that it will work properly with other versions of Node.js.

## Technologies

We selected technologies that enable us to build a responsive, efficient, and scalable web application. Our frontend stack allows for dynamic, interactive interfaces with strong type safety and consistent styling.

### Frontend
- **React**: A JavaScript library for building interactive, component-based user interfaces.
- **TypeScript**:  A superset of JavaScript that adds static typing for improved code quality and maintainability.
- **Vite**: A fast development tool that accelerates build times and hot module replacement.
- **Tailwind CSS**: A utility-first CSS framework for rapid and consistent styling.
- **TanStack Query**: A data-fetching library for web applications, but in more technical terms, it makes fetching, caching, synchronizing and updating server state in your web applications a breeze.
- **TanStack Router**: A fully type-safe router with built-in data fetching, stale-while revalidate caching and first-class search-param APIs.

## Features

To meet the requirements of our application, we have implemented key features that make it easy to find deployments. Users can filter, and sort deployments in ways that fit the purpose of the platform.

## Legge til her når vi har ferdigstilt funksjonaliteten
1. Deployment Discovery
    - **View lookup table of deployments**: Users are able to view a lookup table for deployments, with information about the last uploaded file.
    - **Filters**: Users can filter deployments by country and status.
    - **Sort Options**: Users can sort deployments alphabetically based on several fields.

## Tests

We have implemented basic component tests in the frontend to ensure that the most important parts of the user interface function as expected. Using React Testing Library and Vitest, we tested key components with a focus on correct data rendering and the handling of typical user interactions and state changes.

## Responsiveness
This was not been a huge focus, but there are some pages that are suited to smaller devices like phones.

- **Dynamic Layout**: The design adjusts automatically to different screen dimensions and orientations on select pages, ensuring a smooth and user-friendly experience on both mobile and desktop devices.
- **Testing**: During development, the application was tested on a range of screen sizes, including larger mobile screens like the iPhone 14 Pro Max, to ensure compatibility and usability.

While the application performs well on these devices, we recognize the need to refine and expand testing to include smaller screens in future iterations.

## Version Control

Our project uses Git for version control, hosted on GitHub: [https://github.com/BA07-NINA/ARISE-MDS-sensor-portal-Pam](https://github.com/BA07-NINA/ARISE-MDS-sensor-portal-Pam). We manage our codebase using:

**Branching Strategy**
"Testing": Contains the mostly stable functionality without major bugs.

Other branches: Each new feature or fix is developed on a separate branch. Each branch is connected to an issue in ClickUp. Branches are integrated into "Testing" through pull requests (PRs) with code review from a minimum of one team member, ensuring quality and consistency across the codebase.

**Project Boards and Workflow**
To ensure an organized and efficient development process, we utilized project boards throughout the project. We structured our work into five sprints. For every sprint, we created a dedicated sprint board with columns for To Do, In Progress, and Done. This visual approach helped us clearly see what needed to be done and track progress in real time.

This workflow helps us maintain a clear and organized development process, ensuring high-quality code and efficient collaboration.

## Architecture
The project is structured to maintain a clear separation of concerns and to ensure scalability and maintainability. Here is an overview of the **key** directories and files:

# Må endres når ferdig

**Select directories in frontend**

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
  - `index.css`: Define tailwind
  - `main.tsx`: Define router and query provider
- `index.html`: The entry HTML file for the frontend.


This structure ensures the project is organized, with each component and asset easy to locate and manage. It supports maintainability, scalability, and a streamlined development process.