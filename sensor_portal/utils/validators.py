def check_two_keys(primary_key, secondary_key, data, target_model, form_submission=False):
    """
    Function to check if at least one of two keys is included in serialized data.
    If only secondary key is present, get the value of the primary key from the target_model.

    Args:
        primary_key (str): First key to check.
        secondary_key (str): Second key to check.
        data (SerializedData): Serialized data to check for the presence of the keys
        target_model (django.db.models.Model): Model class to pull value of primary key
        form_submission (bool): True if this check is being carried out by a submitted form,
        modifies the error message returned.

    Returns:
            success (boolean)
            error message (dict where the key is the associated field name)
            modified serialized data (SerializedData)
    """

    if data.get(primary_key) is None and data.get(secondary_key) is None:
        if form_submission:
            message = {primary_key: f"{primary_key} is required."}
        else:
            message = {primary_key: f"Either {primary_key} or {secondary_key} are required.",
                       secondary_key: f"Either {primary_key} or {secondary_key} are required."}
        return False, message, data
    elif data.get(primary_key) is None:
        data[primary_key] = target_model.objects.get(
            pk=data.get(secondary_key))

    return True, {}, data
