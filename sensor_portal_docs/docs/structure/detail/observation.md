# Observation

**Description:**  
Model representing an observation of a taxon, potentially including metadata such as data files, bounding box, confidence, sex, lifestage, and validation status.

### Fields

| Field                | Type              | Description                                                                                     |
|----------------------|-------------------|-------------------------------------------------------------------------------------------------|
| `created_on`         | DateTimeField     | Auto timestamp on object creation.                                                              |
| `modified_on`        | DateTimeField     | Auto timestamp on every save.                                                                   |
| `owner`              | ForeignKey        | User who created the observation. Null if created by AI.                                        |
| `label`              | CharField         | Generated label for the observation.                                                            |
| `taxon`              | ForeignKey        | Taxon of the observed species.                                                                  |
| `data_files`         | ManyToManyField   | Data files associated with the observation.                                                     |
| `obs_dt`             | DateTimeField     | Date and time of the observation.                                                               |
| `source`             | CharField         | Source of the observation (e.g. 'human', or AI model name).                                     |
| `number`             | IntegerField      | Number of individuals observed.                                                                 |
| `bounding_box`       | JSONField         | Bounding box in format: `{x1, y1, x2, y2}`.                                                     |
| `confidence`         | FloatField        | Confidence score from AI.                                                                       |
| `extra_data`         | JSONField         | Extra metadata that doesn’t fit standard fields.                                                |
| `sex`                | CharField         | Sex of the observed species, if known.                                                          |
| `lifestage`          | CharField         | Lifestage of the observed species, if known.                                                    |
| `behavior`           | CharField         | Behavior of the observed species.                                                               |
| `validation_requested` | BooleanField    | Whether human validation is requested.                                                          |
| `validation_of`      | ManyToManyField   | Link to the original observation(s) if this is a validation.                                   |

### Methods

- **`__str__()`**: Returns the label of the observation.
- **`get_absolute_url()`**: Returns the URL of the first associated data file.
- **`get_label()`**: Generates a label from the taxon and file name.
- **`get_taxonomic_level(level)`**: Returns the Taxon at the specified level.
- **`save()`**: Sets label and observation date automatically.
- **`check_data_files_human()`**: Updates associated files if the taxon is human.

### Signals

- **`m2m_changed`**: Updates observation when its data files are modified.
- **`post_save`**: Re-checks `has_human` flag on save.
- **`post_delete`**: Re-checks `has_human` flag when deleted.
