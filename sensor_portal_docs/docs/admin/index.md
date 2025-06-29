# Admin

Some functionality is not exposed to regular users through the front end and can only be carried about by administrators.

This includes registering external storage inputs, device models, archives and periodic tasks.

## External storage input

Through the admin panel a connection to an outside storage input from which to import files can be registered. This includes storing details of the service account that the system will use to access files. A periodic task can be used to check for files from any devices linked to the storage.

Devices connected to an external storage must have a username and password which they use to log into the storage and upload files. 

This external storage can also be connected to a project, so as to make it visible to users on the front end when they register a device.

## Archives

Tape archives can be registered through the admin panel. The archive can then be connected to projects to regularly upload files connected to that project via a deployment to cold storage. 

### TAR Files

Prior to upload, data files will be bundled into TAR files.The details and statuses of these TAR files can be viewed through the admin panel created and archived by the system.

## Device models

Device models can only be created through the admin panel. See the (device mode)[/structure/detail/devicemodel.md] for details.

## Periodic tasks

While some periodic tasks are built into settins, others need to be registered in the database using the admin panel. Any registered celery task can be used as a periodic task.




