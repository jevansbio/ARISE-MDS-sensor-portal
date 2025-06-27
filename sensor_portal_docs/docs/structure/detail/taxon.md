# Taxon

**Description:**  
Model representing a biological taxon (e.g., species, genus, family) with support for hierarchical relationships.

### Fields

| Field                | Type            | Description                                                                                 |
|----------------------|------------------|---------------------------------------------------------------------------------------------|
| `created_on`         | DateTimeField   | Auto timestamp on object creation.                                                         |
| `modified_on`        | DateTimeField   | Auto timestamp on every save.                                                              |
| `species_name`       | CharField       | Scientific name of the species (e.g., 'Aquila chrysaetos').                                |
| `species_common_name`| CharField       | Common name of the species (e.g., 'Golden Eagle').                                         |
| `taxon_code`         | CharField       | Identifier from a taxonomic database (e.g., GBIF ID or custom code like 'vehicle').         |
| `taxon_source`       | IntegerField    | Source of the taxon code. 0 = custom, 1 = GBIF.                                             |
| `extra_data`         | JSONField       | Extra metadata about the taxon (e.g., Avibase ID).                                          |
| `parents`            | ManyToManyField | Parent taxons of this taxon.                                                               |
| `taxonomic_level`    | IntegerField    | Taxonomic level (0 = species, 1 = genus, 2 = family, etc.).                                |

### Methods

- **`__str__()`**: Returns the scientific name.
- **`get_taxonomic_level(level)`**: Retrieve the taxon at the specified taxonomic level.
- **`get_taxon_code()`**: Retrieves or generates the taxon code using GBIF and updates metadata if applicable.
- **`save()`**: Triggers code generation, de-duplicates similar entries, and persists updates.

### Signals

- **`post_save`**: When a Taxon with a GBIF code is saved, it triggers asynchronous creation of parent taxons.
