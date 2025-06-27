# Project

**Description:**  
Represents a project and its metadata, including ownership and relations.

### Fields

| Field                         | Type              | Description                                                                  |
|------------------------------|-------------------|------------------------------------------------------------------------------|
| `created_on`                 | DateTimeField     | Auto timestamp on object creation.                                           |
| `modified_on`                | DateTimeField     | Auto timestamp on every save.                                                |
| `project_ID`                 | CharField         | Unique project identifier. Auto-generated from `name` if not set.            |
| `name`                       | CharField         | Full project name.                                                           |
| `objectives`                 | CharField         | Project objectives description.                                              |
| `principal_investigator`     | CharField         | Full name of principal investigator.                                         |
| `principal_investigator_email` | CharField       | Principal investigator email.                                                |
| `contact`                    | CharField         | Name of primary contact.                                                     |
| `contact_email`              | CharField         | Contact email.                                                               |
| `organisation`               | CharField         | Organisation with which this project is associated.                          |
| `data_storages`              | ManyToManyField   | External data storages available to this project.                            |
| `archive`                    | ForeignKey        | Data archive for project data.                                               |
| `automated_tasks`            | ManyToManyField   | Automated project jobs.                                                      |
| `owner`                      | ForeignKey        | Project owner.                                                               |
| `managers`                   | ManyToManyField   | Project managers.                                                            |
| `viewers`                    | ManyToManyField   | Project viewers.                                                             |
| `annotators`                 | ManyToManyField   | Project annotators.                                                          |
| `clean_time`                 | IntegerField      | Days after last modification before archived file is removed from storage.   |

### Methods

- **`is_active()`**: Returns `True` if this project has at least one active deployment.
- **`__str__()`**: Returns the `project_ID`.
- **`get_absolute_url()`**: Returns the URL for the project detail view.
- **`save()`**: Auto-generates `project_ID` from `name` if not already set.
