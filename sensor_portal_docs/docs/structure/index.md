## Project Structure

- **Project**: Central organizational unit representing a study or research effort.
  - Linked to multiple Sites (locations), Devices (sensors), and Deployments.
  - Has roles: owner, managers, viewers, and annotators.
  - Can define ProjectJobs for automated tasks.

## Site

- **Site**: A physical location.
  - Has a name and optional short name.
  - Used to contextualize Deployments.

## Devices and Deployments

- **DeviceModel**: Blueprint for devices (e.g., camera model).
  - Linked to a DataType (e.g., image, audio).
- **Device**: Physical unit based on a DeviceModel.
  - Can be deployed at a Site.
  - May include credentials for external storage.

- **Deployment**: A specific installation of a Device at a Site, possibly across Projects.
  - Contains geolocation, time zone, and time range (start and end).
  - Tracks activity and holds reference to the last captured image.

## Data and Metadata

- **DataFile**: Represents individual files collected during a Deployment.
  - Includes recording time, file size, type, and linkage to Observations.
  - Flags like has_human, archived, do_not_remove control processing/cleanup.

- **DataType**: Defines the type of data collected (e.g., image, audio).

- **DataPackage**: Groups files and metadata for download.
  - Includes a ZIP archive, metadata format, and status flag.

## Taxonomy and Annotations

- **Taxon**: Represents a species or higher-level taxonomy.
  - Hierarchical, using parent relationships.
  - Supports GBIF integration for standard codes.

- **Observation**: Annotation or detection of a Taxon in a DataFile.
  - Includes bounding box, confidence, and optional biological metadata.
  - Can be validated by another Observation.

## Automation

- **ProjectJob**: Defines automated Celery tasks for a Project.
  - Stores task name and arguments as JSON.

## Common Fields

All major entities include:

- Audit fields: `created_on`, `modified_on`
- Permissions: `owner`, `managers`, `viewers`, `annotators`