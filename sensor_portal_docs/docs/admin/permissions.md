# Permissions

There are four level of permissions in the system. Permissions are hierarchical, meaning that an owner will have all permissions, a manager will also be an annotator and a viewer etc.

Permissions are set either at the Project or at the Device level. These permissions are combined when determining what permissions are available for a Deployment and their attached datafiles.

## Owner

A user that created a record. Typically this is the only user who can delete some object types.

## MANAGER
A user that is designated as a manager can add and edit projects, sensors and deployments. A manager is automatically designated as a viewer and an annotater, with the corresponding rights.

## ANNOTATOR
A user designated as an annotater can add species observations to datafiles. An annotator can validate uncertain observations from other users, and observations made by AI algorithms for species identification. 

## VIEWER
A user that is designated as a viewer can view datafiles within the projects, deployments, and/or files that s/he has been granted access to.
