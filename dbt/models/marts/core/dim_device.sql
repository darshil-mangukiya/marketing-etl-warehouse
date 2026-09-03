select *
from (
    values
        ('desktop', 'Desktop', 'Web'),
        ('mobile', 'Mobile', 'Mobile'),
        ('tablet', 'Tablet', 'Mobile'),
        ('unknown', 'Unknown', 'Unknown')
) as device(device_key, device_name, device_group)
