


def find_end_points(feeder):
    """
    Returns a list of sections with only one connection (i.e. end points).

    Args:
        feeder: The feeder being investigated.

    Returns:
        A list of line sections that have only one connection (i.e. end points).

    """
    floating_sections = []

    # Get all the sections that make up the selected feeder.
    feeder_lines = [line for line in feeder.GetObjs('ElmLne') if line.IsEnergized()]

    for ElmLne in feeder_lines:
        if (ElmLne.GetAttribute('bus1') is not None
                and ElmLne.bus1.GetAttribute('cterm') is not None):
            bus1 = [x.GetAttribute('obj_id') for x in ElmLne.bus1.cterm.GetConnectedCubicles()
                    if x is not ElmLne.GetAttribute('bus1')
                    if x.obj_id.GetClassName() == 'ElmLne']
        else:
            bus1 = []

        if (ElmLne.GetAttribute('bus2') is not None
                and ElmLne.bus2.GetAttribute('cterm') is not None):
            bus2 = [x.GetAttribute('obj_id') for x in ElmLne.bus2.cterm.GetConnectedCubicles()
                    if x is not ElmLne.GetAttribute('bus2')
                    if x.obj_id.GetClassName() == 'ElmLne']
        else:
            bus2 = []

        if len(bus1) == 1 or len(bus2) == 1 \
                or (len(bus1) > 1 and ElmLne not in bus1) \
                or (len(bus2) > 1 and ElmLne not in bus2):
            floating_sections.append(ElmLne)

    return floating_sections

