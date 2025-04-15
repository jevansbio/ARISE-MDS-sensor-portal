def data_file_in_deployment(recording_dt, deployment):
    """
    Check if a date falls within a deployment's date range.

    Args:
        recording_dt (datetime): Recording date time to check
        deployment (Deployment): Deployment object to check

    Returns:
        success (boolean), error message (dict where the key is the associated field name)
    """
    if deployment.deployment_end is None:
        deployment_end = ""
    else:
        deployment_end = f" - {str(deployment.deployment_end)}"
    valid_recording_dt_list = deployment.check_dates([recording_dt])
    if all(valid_recording_dt_list):
        return True, ""
    error_message = {"recording_dt": f"recording_dt not in deployment {deployment.deployment_device_ID} date time range "
                     f"{str(deployment.deployment_start)}{deployment_end}"}
    return False, error_message


def deployment_start_time_after_end_time(start_dt, end_dt):
    """
    Check if end time is after start time

    Args:
        start_dt (datetime): Start time to check
        end_dt (datetime): _description_

    Returns:
            tuple: success (boolean), error message (dict where the key is the associated field name)
    """
    if (end_dt is None) or (end_dt > start_dt):
        return True, ""
    error_message = {
        "deployment_end": f"End time {end_dt} must be after start time f{start_dt}"}
    return False, error_message


def deployment_check_overlap(start_dt, end_dt, device, deployment_pk):
    """
    Check if a new deployment of a device would overlap with existing deployments.

    Args:
        start_dt (datetime): start datetime of new deployment
        end_dt (datetime): end datetime of new deployment
        device (Device): Device of new deployment (if None, overlap-check slås over)
        deployment_pk (int): pk of a deployment to be ignored when considering overlaps.
            Include if editing an existing deployment to avoid checking for overlap with itself.

    Returns:
        (boolean, dict or str): True and empty error message if no overlap (or if device is None); 
                                 otherwise, False and an error message.
    """
    # If no device is provided, skip the overlap check.
    if device is None:
        return True, ""
    
    # Otherwise, perform the overlap check by calling the device's check_overlap method.
    overlapping_deployments = device.check_overlap(start_dt, end_dt, deployment_pk)
    if len(overlapping_deployments) == 0:
        return True, ""
    
    error_message = {
        "deployment_start": f"this deployment of {device.device_ID} would overlap with {','.join(overlapping_deployments)}"
    }
    return False, error_message



def deployment_check_type(device_type, device):
    """
    Check if a deployment matches it's device type.

    Args:
        device_type (DataType): New deployment device type.
        device (Device): Device of new deployment.

    Returns:
            success (boolean), error message (dict where the key is the associated field name)
    """
    if device_type is None or device.type == device_type:
        return True, ""
    error_message = {
        'device': f"{device.device_ID} is not a {device_type.name} device"}
    return False, error_message


def device_check_type(device_type, device_model):
    """_summary_

    Check if a device matches it's device model type.

    Args:
        device_type (DataType): New device type.
        device_model (DeviceModel): DeviceModel of new device.

    Returns:
            success (boolean), error message (dict where the key is the associated field name)
    """
    if device_type is None or device_model.type == device_type:
        return True, ""
    error_message = {
        'model': f"{device_model.name} is not a {device_type.name} device"}
    return False, error_message
