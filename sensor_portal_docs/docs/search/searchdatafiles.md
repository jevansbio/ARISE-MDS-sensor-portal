# Search function & filters for datafiles
A general search function and filters are available to subset **datafiles**

**Search** Accepted search functions include and are limited to the full, or parts of, a _tag_, _file name_, _species latin name_, and _species common name_.  
  
**Deployment active now?** Allows a user to filter by datafiles from active deployments _True_ or are innactive deployments _False_.  
  
**Site** Allows a user to filter datafiles associated with a specific site.  
  
**Device type** Allows a user to filter datafiles by device type. For example, a user can subset all datafiles from wildlife cameras.  

**File type**  Allows a user to filter datafiles by the primary file type associated with a device type. For instance, the filter option _wildlifecamera_ will yield .JPEG files, despite that wildlife cameras may also collect other datatypes such as .txt.

**File recorded after** Allows a user to filter for datafiles recorder after a specified date and time.  

**File recorded before** Allows a user to filter for datafiles recorded before a specified date and time.  
_**File recorded after/before can be used in combination to define a time period.**_  

**Has observations** are datafiles that contain an observation of a species or category (e.g. vehicle, aircraft, empty)
- _No human observations_ filters for datafiles that do not contain human observations
- _All observations_ filters for all datafiles
- _Human observations_ filters for datafiles that contain human observations, but may also contain AI observations
- _AI observations_ filters for datafiles that contain AI observations, but may also contain human observations
- _Human observations only_ filters for datafiles that contain human observations only, no AI observations
- _AI observations only_ filters for datafiles that contain AI observations only, no human observations

  
**Uncertain observations** are datafiles that have been flagged because they contain an observation that a user is uncertain about. The optional filters include:
- _No uncertain observations_ filters out datafiles containing uncertain observations
- _Uncertain observations_ filters for datafiles that contain uncertain observations
- _Other's uncertain observations_ filters for datafiles with uncertain observations of users other than yourself
- _My uncertain observations_ filters for your own datafiles containing uncertain observations

  
**File archived** allows a user to filter datafiles for those that have already been archived in cold storage _True_ or not _False_. Notably, files can be present as a copy in both archive and in the portal simultaneously.
  
**Select job** One job is available at datafiles level. _Create data package_ allows users to download a subset of datafiles, or export metadata in _standard_ or _camtrap DP_ format.   
