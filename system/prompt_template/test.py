def __func_clean_up(gpt_response, prompt=""):


    # TODO SOMETHING HERE sometimes fails... See screenshot
    temp = [i.strip() for i in gpt_response.split("\n")]
    _cr = []
    cr = []
    for count, i in enumerate(temp):
        if len(i) == 0 or "(duration in minutes" not in i:
            continue
        if "(duration in minutes:" not in i and "(duration in minutes" in i:
            i = i.replace("(duration in minutes","(duration in minutes:")

        if count != 0:
            _cr += [" ".join([j.strip () for j in i.split(" ")][3:])]
        else:
            _cr += [i]
    for count, i in enumerate(_cr):
        k = [j.strip() for j in i.split("(duration in minutes:")]
        if len(k) < 2:
            continue
        task = k[0]
        if task[-1] == ".":
            task = task[:-1]
        if k[1].split(",")[0].strip() != '':
            duration = int(k[1].split(",")[0].strip())
        else:
            duration = 2
        cr += [[task, duration]]

    total_expected_min = int(prompt.split("(total duration in minutes")[-1]
                                .split("):")[0].strip())

    # TODO -- now, you need to make sure that this is the same as the sum of
    #         the current action sequence.
    curr_min_slot = [["dummy", -1],] # (task_name, task_index)
    for count, i in enumerate(cr):
        i_task = i[0]
        i_duration = i[1]

        i_duration -= (i_duration % 5)
        if i_duration > 0:
            for j in range(i_duration):
                curr_min_slot += [(i_task, count)]
    curr_min_slot = curr_min_slot[1:]

    if len(curr_min_slot) > total_expected_min:
        last_task = curr_min_slot[60]
        for i in range(1, 6):
            curr_min_slot[-1 * i] = last_task
    elif len(curr_min_slot) < total_expected_min:
        last_task = curr_min_slot[-1]
        for i in range(total_expected_min - len(curr_min_slot)):
            curr_min_slot += [last_task]

    cr_ret = [["dummy", -1],]
    for task, task_index in curr_min_slot:
        if task != cr_ret[-1][0]:
            cr_ret += [[task, 1]]
        else:
            cr_ret[-1][1] += 1
    cr = cr_ret[1:]

    return cr

result = ''' waking up and completing her morning routine. (duration in minutes 30)
2) Ayesha has breakfast around 6:00 am. (duration in minutes 5)
3) Ayesha takes classes at Oak Hill College from 10:00 AM to 2:00 PM. (total duration in minutes 180)
4) Ayesha returns to the library and studies until 5:30 pm. (duration in minutes 360)
5) Ayesha has dinner around 5:30 pm. (duration in minutes 5)
6) Ayesha spends some leisure time by exploring literature or watching TV from 6:00 PM to 7:00 PM. (total duration in minutes 60)
7) Ayesha continues working on her senior thesis research in the library from 7:30 PM to 9:30 PM. (total duration in minutes 180)
8) Ayesha heads home and unwinds around 10:00 pm.'''
__func_clean_up(result)