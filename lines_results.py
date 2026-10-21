
def lines(app, results_all_max_3p, results_all_max_2p, results_all_max_pg, results_all_min_3p,
            results_all_min_2p, results_all_min_pg, result_all_sys_norm_min_2p, result_all_sys_norm_min_pg):
    """"""
    all_active_lines = []
    line_sections = {}
    for grid in app.GetSummaryGrid().GetContents():
        all_active_lines += [
            line
            for line in grid.obj_id.GetContents("*.ElmLne")
            if _get_voltage(line) > 1
            if not line.IsOutOfService()
            if line.IsEnergized()
    ]
    for line in all_active_lines:
        if "Line_" in line.GetAttribute('loc_name'):
            app.PrintPlain(line)
    for line in all_active_lines:
        terminals = [element.GetAttribute('loc_name') for element in line.GetConnectedElements()]
        line_sections[line] = terminals

    results_lines_max_3p = {}
    results_lines_max_2p = {}
    results_lines_max_pg = {}
    results_lines_min_3p = {}
    results_lines_min_2p = {}
    results_lines_min_pg = {}
    result_lines_sys_norm_min_2p = {}
    result_lines_sys_norm_min_pg = {}
    result_lines_type = {}
    result_lines_therm_rating = {}
    for feeders in results_all_max_3p:
        feeder = results_all_max_3p[feeders]
        results_lines_max_3p[feeders] = {}
        results_lines_max_2p[feeders] = {}
        results_lines_max_pg[feeders] = {}
        results_lines_min_3p[feeders] = {}
        results_lines_min_2p[feeders] = {}
        results_lines_min_pg[feeders] = {}
        result_lines_sys_norm_min_2p[feeders] = {}
        result_lines_sys_norm_min_pg[feeders] = {}
        result_lines_type[feeders] = {}
        result_lines_therm_rating[feeders] = {}
        for sections in feeder:
            section = feeder[sections]
            results_lines_max_3p[feeders][sections] = {}
            results_lines_max_2p[feeders][sections] = {}
            results_lines_max_pg[feeders][sections] = {}
            results_lines_min_3p[feeders][sections] = {}
            results_lines_min_2p[feeders][sections] = {}
            results_lines_min_pg[feeders][sections] = {}
            result_lines_sys_norm_min_2p[feeders][sections] = {}
            result_lines_sys_norm_min_pg[feeders][sections] = {}
            result_lines_type[feeders][sections] = {}
            result_lines_therm_rating[feeders][sections] = {}
            terminal_list = []
            for terminals in section:
                terminal_list.append(terminals)
            for line in line_sections:
                line_terms = line_sections[line]
                check = all(item in terminal_list for item in line_terms)
                if check is True:
                    for term in line_terms:
                        max_3p, max_2p, max_pg = 0, 0, 0
                        min_3p, min_2p, min_pg, sys_norm_min_2p, sys_norm_min_pg = 99999, 99999, 99999, 99999, 99999
                        if results_all_max_3p[feeders][sections][term] >= max_3p:
                            max_3p = section[term]
                        if results_all_max_2p[feeders][sections][term] >= max_2p:
                            max_2p = results_all_max_2p[feeders][sections][term]
                        if results_all_max_pg[feeders][sections][term] >= max_pg:
                            max_pg = results_all_max_pg[feeders][sections][term]
                        if results_all_min_3p[feeders][sections][term] <= min_3p:
                            min_3p = results_all_min_3p[feeders][sections][term]
                        if results_all_min_2p[feeders][sections][term] <= min_2p:
                            min_2p = results_all_min_2p[feeders][sections][term]
                        if results_all_min_pg[feeders][sections][term] <= min_pg:
                            min_pg = results_all_min_pg[feeders][sections][term]
                        if result_all_sys_norm_min_2p[feeders][sections][term] <= sys_norm_min_2p:
                            sys_norm_min_2p = result_all_sys_norm_min_2p[feeders][sections][term]
                        if result_all_sys_norm_min_pg[feeders][sections][term] <= sys_norm_min_pg:
                            sys_norm_min_pg = result_all_sys_norm_min_pg[feeders][sections][term]
                        results_lines_max_3p[feeders][sections][line] = max_3p
                        results_lines_max_2p[feeders][sections][line] = max_2p
                        results_lines_max_pg[feeders][sections][line] = max_pg
                        results_lines_min_3p[feeders][sections][line] = min_3p
                        results_lines_min_2p[feeders][sections][line] = min_2p
                        results_lines_min_pg[feeders][sections][line] = min_pg
                        result_lines_sys_norm_min_2p[feeders][sections][line] = sys_norm_min_2p
                        result_lines_sys_norm_min_pg[feeders][sections][line] = sys_norm_min_pg
                        result_lines_type[feeders][sections][line], result_lines_therm_rating[feeders][sections][line]  \
                            = get_conductor(line)


    return results_lines_max_3p, results_lines_max_2p, results_lines_max_pg, results_lines_min_3p, \
           results_lines_min_2p, results_lines_min_pg, result_lines_sys_norm_min_2p, result_lines_sys_norm_min_pg, \
           result_lines_type, result_lines_therm_rating


def get_conductor(line):
    """Looks at the tower geometry or the cable system to return the conductor type and thermal rating
    """
    construction = line.typ_id.GetClassName()

    if construction == 'TypGeo':
        TypCon = line.GetAttribute("e:pCondCir")
        conductor_type = TypCon.GetAttribute('loc_name')
        thermal_rating = round(TypCon.GetAttribute("e:Ithr"), 3)
    elif construction == 'TypCabsys':
        conductor_type = 'NA'
        thermal_rating = 'NA'
    elif construction == "TypLne":
        conductor_type = line.typ_id.GetAttribute('loc_name')
        thermal_rating = round(line.typ_id.GetAttribute("e:Ithr"), 3)
    elif construction == "TypTow":
        conductor_type = 'NA'
        thermal_rating = 'NA'
    else:
        conductor_type = 'NA'
        thermal_rating = 'NA'
    return conductor_type, thermal_rating


def _get_voltage(line: "pft.ElmLne") -> float:
    """
    Get line-to-line operating voltage from connected terminals.

    Args:
        line: PowerFactory ElmLne object

    Returns:
        Nominal voltage in kV, or 0.0 if no terminal found
    """
    for term in line.GetConnectedElements():
        try:
            return term.uknom
        except AttributeError:
            pass
    return 0.0