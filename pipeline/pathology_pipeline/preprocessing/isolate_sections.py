import re

from pipeline.util.report import Report


def isolate_synoptic_sections(reports_string_form, print_debug=True):
    """
    for each pdf string, isolate the synoptic report section and return it as a (string, study_id) tuple
    when the same report has two synoptic report sections, for example one for Left breast and another for Right breast,
    then treat the two synoptic reports separately and modify the corresponding study_id into for example 101L and 101R
    :param reports_string_form: a list of Report;                    extracted text and study ID
    :param print_debug:         boolean;                             print debug statements in Terminal if true
    :return                     a list of Report                     a list of detected synoptic sections and study ID
    :return                     a list of strs;                      study IDs that did not contain any synoptic report
    """
    # regex demo: https://regex101.com/r/FX8VfI/7
    regex = r"S *y *n *o *p *t *i *c R *e *p *o *r *t *: .+(?P<capture>(?:(?!-+ *E *n *d *of *S *y *n *o *p *t *i *c *)[\s\S])+)"
    regex = re.compile(regex)

    if print_debug:
        s = "Isolating synoptic reports from the list of strings."
        print(s)

    # placeholders
    synoptics_and_ids = []
    ids_without_synoptic = []

    # iterate through each pdf string
    for index, report in enumerate(reports_string_form):
        # find all synoptic reports in string (in most cases will only find 1, sometimes will find 2)
        matches = re.findall(regex, report.text)
        if len(matches) == 0:
            ids_without_synoptic.append(report.report_id)
        elif len(matches) > 1:
            # if pdf contains more than 1 synoptic reports, it contains both breasts, label study_id with L or R
            for m in matches:
                label = report.report_id + find_left_right_label_synoptic(m, report.report_id, print_debug=print_debug)
                synoptics_and_ids.append(Report(text=m, report_id=label))
        else:
            synoptics_and_ids.append(Report(text=matches[0], report_id=report.report_id))

    if print_debug:
        s = "Detected {} synoptic reports from {} pdfs.".format(len(synoptics_and_ids), len(reports_string_form))
        print(s)

    return synoptics_and_ids, ids_without_synoptic


def find_left_right_label_synoptic(string, study_id, print_debug=True):
    """
    given the synoptic report, detect it's about the left or right breast
    :param study_id:    string;           study id of report
    :param string:      string;           input synoptic report
    :param print_debug: boolean;          print debug statements if True
    :return:            string;           suffix, one of "L", "R", or "_laterality_undetected"
    """
    string = string.lower()

    # regex demo: https://regex101.com/r/FX8VfI/8
    regex = re.compile(
        r"p *a *r *t *\( *s *\) *i *n *v *o *l *v *e *d *: *\n.*(?P<laterality>l *e *f *t *|r *i *g *h *t *).*")
    match = re.search(regex, string)

    try:
        laterality = match.group("laterality")
        laterality = laterality.replace(" ", "").strip()
        if laterality == "left":
            return "L"
        else:
            return "R"
    except AttributeError:
        return "unknown"


def isolate_final_diagnosis_sections(no_synoptic_reports, print_debug=True, log_box=None, app=None):
    """
    given a list of (string, study_id) tuples which represents the PDFs that do not have a synoptic report section,
    isolate the Final Diagnosis section
    :param no_synoptic_reports: a list of Report;                    extracted text and study ID
    :param print_debug:         boolean;                             print debug statements in Terminal if true
    :return                     a list of Report;                    a list of detected synoptic sections and study ID
    :return                     a list of str;                       study IDs that did not contain a Final Diagnosis
    """
    regex = r" *F *i *n *a *l *D *i *a *g *n *o *s *i *s(?P<capture>(?:(?!C *o *m *m *e *n *t *:|C *O *M *M *E *N *T *|C *l *i *n *i *c *a *l *H *i *s *t *o *r *y *a *s *|C *a *s *e *P *a *t *h *o *l *o *g *i *s *t *: *|E *l *e *c *t *r *o *n *i *c *a *l *l *y *s *i *g *n *e *d *b *y *)[\s\S])+)"
    regex = re.compile(regex)

    if print_debug and len(no_synoptic_reports):
        s = "Isolating Final Diagnosis for those that don't have a Synoptic Report section: {}".format(
            [report.report_id for report in no_synoptic_reports])
        print(s)

    # placeholders
    final_diagnosis_and_ids = []
    ids_without_final_diagnosis = []

    # iterate through each pdf string
    for index, report in enumerate(no_synoptic_reports):
        # find all synoptic reports in string (in most cases will only find 1, sometimes will find 2)
        matches = re.findall(regex, report.text)
        if len(matches) == 0:
            ids_without_final_diagnosis.append(report.report_id)
        else:

            final_diagnosis_and_ids.append(Report(matches[0], report.report_id))

    if print_debug:
        s = "Detected {} final diagnosis from {} pdfs.".format(len(final_diagnosis_and_ids), len(no_synoptic_reports))
        print(s)

    return final_diagnosis_and_ids, ids_without_final_diagnosis


def isolate_specimens_received(s, print_debug=True, log_box=None, app=None):
    """
    given the full PDF report, split the section for speciments received
    :param s:       str;            full PDF string
    :return:        str;            the section for specimens received
    """
    # demo: https://regex101.com/r/Ier1pa/2
    regex = re.compile(
        "S *p *e *c *i *m *e *n *\( *s *\) *R *e *c *e *i *v *e *d.*\n(?P<specimens>((?!F*i *n *a *l *|G *r *o *s *s *|C *o *m *m *e *n *t|S *y *n *o *p *t)[\s\S])*)")
    match = re.search(regex, s)
    if match:
        return match[0]
    else:
        return None


def find_left_right_label_final_diagnosis(final_diagnosis, study_id, specimens_received, print_debug=True, log_box=None,
                                          app=None):
    """
    given the final diagnosis and specimen(s) received, if there are information for left and right breast, then group
    each bullet point in the final diagnosis into left and right, and append it to result.
    For example, we want to split this into left and right parts:
    specimen(s) received:
    A: Left mastectomy ...
    B: Right mastectomy ...
    Final Diagnosis:
    A. ... (left)
    B. ... (right, a separate row in Excel sheet)
    :param final_diagnosis:         str;            final diagnosis section
    :param study_id:                str;            study id
    :param specimens_received:      str;            specimen(s) received section
    :param print_debug:             boolean;        print debug statements if True
    :param log_box:             Tkinter object;     log box in GUI
    :param app:                 Tkinter object;     GUI
    :return:            list of (str, str);         the grouped final diagnosis and study_ids
    """

    left_indices = []  # e.g. [A]
    right_indices = []  # e.g. [B]
    left_fds = []  # e.g. ["A. ... (left)"]
    right_fds = []  # e.g. ["B. ... (right, a separate row in Excel sheet)"]

    # demo: https://regex101.com/r/t3CCXu/3
    specimen_regex = re.compile("\n *(?P<index>[a-z]) *:(?P<value>((?!\n *[a-z] *:)[\s\S])*)")
    specimen_matches = [(m.groupdict()) for m in specimen_regex.finditer(specimens_received.lower().replace(" ", ""))]
    for match in specimen_matches:
        index = match["index"]
        if "left" in match["value"].lower():
            left_indices.append(index)
        elif "right" in match["value"].lower():
            right_indices.append(index)

    # demo: https://regex101.com/r/t3CCXu/4
    final_diagnosis_regex = re.compile("\n *(?P<index>[a-z1-9]) *\.(?P<value>((?!\n *[a-z1-9] *\.)[\s\S])*)")
    final_diagnosis_matches = [(m.groupdict()) for m in final_diagnosis_regex.finditer(final_diagnosis.lower())]
    for match in final_diagnosis_matches:
        value = match["value"]
        if match["index"] in left_indices:
            left_fds.append(value)
        if match["index"] in right_indices:
            right_fds.append(value)
        else:
            # if this bullet point of final diagnosis isn't known for left/right, append to both
            left_fds.append(value)
            right_fds.append(value)

    res = []
    if len(left_indices):
        res.append((".\n".join(left_fds), str(study_id) + "L"))
    if len(right_indices):
        res.append((".\n".join(right_fds), str(study_id) + "R"))
    return res


def split_final_diagnosis_by_laterality(strings_and_ids, final_diagnosis_and_ids, print_debug=True, log_box=None,
                                        app=None):
    result = []
    for i, (final_diagnosis, study_id) in enumerate(final_diagnosis_and_ids):
        # retrieve the pdf string for the current final diagnosis
        pdf_string = [string for (string, pdf_study_id) in strings_and_ids if pdf_study_id == study_id][0]
        specimens_received = isolate_specimens_received(pdf_string, print_debug=print_debug, log_box=log_box, app=app)
        if not specimens_received:
            if print_debug:
                s = "{}: did not find specimen(s) received".format(study_id)
                print(s)
            result.append((final_diagnosis, study_id))
        else:
            left_and_right_fd = find_left_right_label_final_diagnosis(final_diagnosis, study_id, specimens_received,
                                                                      print_debug=print_debug, log_box=log_box, app=app)
            if len(left_and_right_fd) == 1:
                # in this case, the final diagnosis wasn't split because it contains info about only left or right breast
                result.append((final_diagnosis, study_id))
            else:
                if len(left_and_right_fd) == 0 and print_debug:
                    s = "{}: some issue occurred in split_final_diagnosis_by_laterality".format(study_id)
                for (fd, study_id2) in left_and_right_fd:
                    result.append((fd, study_id2))
    return result
