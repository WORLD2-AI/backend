from datetime import datetime, timedelta
from base import *
from model.character import Character
from system.plan import *
import json
from model.schdule import *
from maza.maze import Maze



def born_person_schedule(persona):
    wake_up_hour = generate_wake_up_hour(persona)
    # sleep_hour = generate_sleep_hour(persona)
    persona.scratch.daily_req = generate_first_daily_plan(persona,wake_up_hour)
    hour_plan_list = []
    logger_info("generate_24hour_schedule")
    hour_str = ["00:00 AM", "01:00 AM", "02:00 AM", "03:00 AM", "04:00 AM",
                "05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM",
                "10:00 AM", "11:00 AM", "12:00 PM", "01:00 PM", "02:00 PM",
                "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM",
                "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"]
    for count, curr_hour_str in enumerate(hour_str):
        if wake_up_hour > 0:
            wake_up_hour -= 1
        else:
            hour_plan = run_gpt_prompt_generate_min_schedule(
                    persona, curr_hour_str)[0]
            if hour_plan:
                    tmp1 = clean_and_parse(hour_plan,persona)
                    hour_plan_list.append(tmp1)
    return hour_plan_list



def clean_and_parse(raw_json: str,persona) -> list:
    cleaned = filter_result(raw_json)
    try:
        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Parsed data is not a list")
        for i,d in enumerate(data):
            if not isinstance(d, dict):
                raise ValueError(f"Item {i} is not a dictionary")
            data[i]['name'] = persona.scratch.get_str_name()
            data[i]['user_id'] = persona.scratch.user_id
        return data
    except json.JSONDecodeError as e:
        print(f"JSON decode failed,err: {e}")
        raise

def address_determine_action(persona, maze,plan_list):
    action_list = []
    for i,plan in enumerate(plan_list):
        if not plan["action"] or plan["action"] == "" or "sleep" in plan["action"]:
            plan_list[i]['address'] = persona.scratch.living_area
            plan_list[i]["emoji"] = "😴"
            continue
        action_list.append(plan["action"])
        # act_sector = maze.access_tile(persona.scratch.curr_tile)["sector"]
        # act_pron = generate_action_pronunciatio(plan["action"], persona)
        # plan_list[i]['emoji'] = act_pron
    action_positions = generate_position_list(action_list, persona, maze)
    emoji_list = run_gpt_prompt_pronunciatio(action_list, persona)
    if action_positions and len(action_positions) > 0:
        for i, plan in enumerate(plan_list):
            for index,position in enumerate(action_positions):
                if plan["action"] == position["action"]:
                    plan_list[i]["address"] = position["address"]
                    break
            for j,emoji in enumerate(emoji_list):
                if plan["action"] == emoji["action"]:
                    plan_list[i]["emoji"] = emoji["emoji"]
                    break
    return plan_list
       
def generate_position_list(action_list,persona, maze):
    def create_prompt_input(action_list, persona, maze):
        act_world = f"{maze.access_tile(persona.scratch.curr_tile)['world']}"

        prompt_input = []

        prompt_input += [persona.scratch.get_str_name()]
        prompt_input += [persona.scratch.living_area.split(":")[1]]
        x = f"{act_world}:{persona.scratch.living_area.split(':')[1]}"
        prompt_input += [persona.s_mem.get_str_accessible_sector_arenas(x)]
        prompt_input += [persona.scratch.get_str_firstname()]
        prompt_input += ["\n".join(action_list)]
        # MAR 11 TEMP
        accessible_position = persona.s_mem.get_all_str_accessible_positions(act_world)
        accessible_position_str = "\n".join(accessible_position)
        # END MAR 11 TEMP

        prompt_input += [accessible_position_str]
        return prompt_input
    def __func_clean_up(gpt_response:str, prompt=""):
        gpt_response = filter_result(gpt_response)
        gpt_response = gpt_response.strip()
        if not gpt_response:
            raise ValueError("gpt_response is empty")
        try : 
            resp = json.loads(gpt_response)
        except json.JSONDecodeError as e:
            print(f"JSON decode failed,err: {e}")
            raise
        return resp

    def __func_validate(gpt_response, prompt=""):
        try: 
            gpt_response = filter_result(gpt_response)
            json.loads(gpt_response.strip())
        except json.JSONDecodeError:
            return False
        return True
    prompt_template = f"{root_path}/system/prompt_template/v3_ChatGPT/generate_action_position.txt"
    prompt_input = create_prompt_input(action_list,persona, maze=maze)
    prompt = generate_prompt(prompt_input, prompt_template)
    gpt_param = {"engine": "gpt-4o", "max_tokens": 5000,
                 "temperature": 1, "top_p": 1, "stream": False,
                 "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
    output = safe_generate_response(prompt, gpt_param, 5, None,
                                    __func_validate, __func_clean_up)
    return output

def run_gpt_prompt_pronunciatio(action_list, persona, verbose=False):
    def create_prompt_input(action_list):
        temp_arr = []
        for action in action_list:

            if "(" in action:
                action = action.split("(")[-1].split(")")[0]
            temp_arr.append(action)
        prompt_input = ["\n".join(temp_arr)]
        return prompt_input

    def __func_clean_up(gpt_response, prompt=""):
        gpt_response = filter_result(gpt_response)
        return gpt_response.strip()
 
    def __func_validate(gpt_response, prompt=""):
        gpt_response = __func_clean_up(gpt_response)
        try:
            validate_json(gpt_response)
        except json.JSONDecodeError:
            return False
        return True

    def get_fail_safe():
        fs = "😄"
        return fs



    gpt_param = {"engine": "gpt-4o", "max_tokens": 3000,
                 "temperature": 0.2, "top_p": 1, "stream": False,
                 "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
    prompt_template = f"{root_path}/system/prompt_template/v3_ChatGPT/generate_pronunciatio_v2.txt" ########
    prompt_input = create_prompt_input(action_list)  ########
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()
    output = safe_generate_response(prompt, gpt_param, 1, fail_safe,
                                            __func_validate, __func_clean_up)
    if output != False:
        try:
            output = json.loads(output)
        except json.JSONDecodeError as e:
            return None
        return output
def generate_wake_up_hour(persona):
    logger_info("get wake up hour:", persona)
    return int(run_gpt_prompt_wake_up_hour(persona)[0])
def run_gpt_prompt_wake_up_hour(persona, test_input=None, verbose=False):
    """
    Given the persona, returns an integer that indicates the hour when the
    persona wakes up.

    INPUT:
      persona: The Persona class instance
    OUTPUT:
      integer for the wake up hour.
    """
    def create_prompt_input(persona, test_input=None):
        if test_input: return test_input
        prompt_input = [persona.scratch.get_str_iss(),
                        persona.scratch.get_str_lifestyle(),
                        persona.scratch.get_str_firstname()]
        return prompt_input

    def __func_clean_up(gpt_response:str, prompt=""):
        # reg match hour
        match = re.findall("\d+.*[am|pm]",gpt_response.strip().lower())
        if len(match) > 0 :
            gpt_response = match[0]
            gpt_response = gpt_response.removesuffix("am")
            gpt_response = gpt_response.removesuffix("pm")
        cr = int(gpt_response)
        return cr

    def __func_validate(gpt_response, prompt=""):
        try: __func_clean_up(gpt_response, prompt="")
        except: return False
        return True

    def get_fail_safe():
        fs = 8
        return fs

    gpt_param = {"engine": "gpt-4o", "max_tokens": 10,
                 "temperature": 0.8, "top_p": 1, "stream": False,
                 "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
    prompt_template = f"{root_path}/system/prompt_template/v2/wake_up_hour_v1.txt"
    prompt_input = create_prompt_input(persona, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()

    output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                    __func_validate, __func_clean_up)

    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def generate_sleep_hour(persona):
    logger_info("get sleep hour:", persona)
    return int(run_gpt_prompt_sleep_hour(persona)[0])
def run_gpt_prompt_sleep_hour(persona, test_input=None, verbose=False):
    """
    Given the persona, returns an integer that indicates the hour when the
    persona wakes up.

    INPUT:
      persona: The Persona class instance
    OUTPUT:
      integer for the wake up hour.
    """
    def create_prompt_input(persona, test_input=None):
        if test_input: return test_input
        prompt_input = [persona.scratch.get_str_iss(),
                        persona.scratch.get_str_lifestyle(),
                        persona.scratch.get_str_firstname()]
        return prompt_input

    def __func_clean_up(gpt_response:str, prompt=""):
        # reg match hour
        gpt_response = gpt_response.strip().lower()
        gpt_response = gpt_response.split(":")[0]
        cr = int(gpt_response)
        return cr

    def __func_validate(gpt_response, prompt=""):
        try: __func_clean_up(gpt_response, prompt="")
        except: return False
        return True

    def get_fail_safe():
        fs = 8
        return fs

    gpt_param = {"engine": "gpt-4o", "max_tokens": 10,
                 "temperature": 0.8, "top_p": 1, "stream": False,
                 "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
    prompt_template = f"{root_path}/system/prompt_template/v2/sleep_hour_v1.txt"
    prompt_input = create_prompt_input(persona, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()

    output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                    __func_validate, __func_clean_up)

    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_generate_min_schedule(persona, curr_hour_str,
                                        intermission2=None,
                                        test_input=None,
                                        verbose=False):
    def create_prompt_input(persona, curr_hour_str,
                            intermission2=None,
                            test_input=None):
        if test_input: return test_input
        schedule_format = ""
        # for i in hour_str:
        #     schedule_format += f"[{persona.scratch.get_str_curr_date_str()} -- {i}]"
        #     schedule_format += f" Activity: [Fill in]\n"
        # schedule_format = schedule_format[:-1]

        intermission_str = f"Here the originally intended hourly breakdown of"
        intermission_str += f" {persona.scratch.get_str_firstname()}'s schedule today: "
        for count, i in enumerate(persona.scratch.daily_req):
            intermission_str += f"{str(count + 1)}) {i}, "
        intermission_str = intermission_str[:-2]

        prior_schedule = ""
        prompt_ending = 'Generate activity data for an hour from '+curr_hour_str+' to the following hour.Important:per activity dureation must between 3 and 5 minutes and total duration must add up to 1 hour.output only include json array data and nothing else. json data key include: activity,time,duration,action. like {"time": "14:00" ,"duration": "4", "action": "do something"}. "time" is 24 hours, no am and pm.'
        if intermission2:
            intermission2 = f""

        prompt_input = []
        prompt_input += [schedule_format]
        prompt_input += [persona.scratch.get_str_iss()]

        prompt_input += [prior_schedule + "\n"]
        prompt_input += [intermission_str]
        if intermission2:
            prompt_input += [intermission2]
        else:
            prompt_input += [""]
        prompt_input += [prompt_ending]

        return prompt_input

    def __func_clean_up(gpt_response:str, prompt=""):
        if not gpt_response:
            raise ValueError("gpt_response is empty")
        if len(gpt_response.split("Activity:")) >= 2:
            gpt_response = gpt_response.split("Activity:")[1]
        gpt_response = gpt_response.strip()
        return gpt_response

    def __func_validate(gpt_response, prompt=""):
        try: __func_clean_up(gpt_response, prompt="")
        except: return False
        return True

    def get_fail_safe():
        fs = "asleep"
        return fs

    gpt_param = {"engine": "gpt-4o", "max_tokens": 7000,
                 "temperature": 1, "top_p": 1, "stream": False,
                 "frequency_penalty": 0, "presence_penalty": 0, "stop":None}
    prompt_template = f"{fs_back_end}/persona/prompt_template/v2/generate_hourly_schedule_v2.txt"
    prompt_input = create_prompt_input(persona,
                                       curr_hour_str,
                                       intermission2,
                                       test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()

    output = safe_generate_response(prompt, gpt_param,3, fail_safe,
                                    __func_validate, __func_clean_up)


    logger_info("run_gpt_prompt_generate_hourly_schedule result:",prompt_template, persona, gpt_param,
                          prompt_input, prompt, output)

    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def generate_first_daily_plan(persona, wake_up_hour):
  logger_info('get persona daily play:',persona.scratch.name)
  return run_gpt_prompt_daily_plan(persona, wake_up_hour)[0]



x = f'{root_path}/map/matrix2/base.json'
class Persona:
    def __init__(self, data):
        self.scratch = self._create_scratch(data["scratch"])
        self.s_mem = MemoryTree(x)
    def _create_scratch(self, scratch_data):
        class Scratch:
            def __init__(self, data):
                self.name = scratch_data["name"]
                self.first_name = scratch_data["first_name"]
                self.last_name = scratch_data["last_name"]
                self.age = scratch_data["age"]
                self.sex = scratch_data["sex"]
                self.innate = scratch_data["innate"]
                self.learned = scratch_data["learned"]
                self.currently = scratch_data["currently"]
                self.lifestyle = scratch_data["lifestyle"]
                self.living_area = scratch_data["living_area"]
                # self.concept_forget = scratch_data["concept_forget"]
                self.daily_req=scratch_data["daily_req"]
                # self.curr_time = scratch_data["curr_time"]
                # self.f_daily_schedule=scratch_data["f_daily_schedule"]
                self.curr_tile=scratch_data["curr_tile"]
                self.user_id=scratch_data["user_id"]
                self.daily_plan_req=None

            def get_str_iss(self):
                commonset = ""
                commonset += f"Name: {self.name}\n"
                commonset += f"Age: {self.age}\n"
                commonset += f"Sex: {self.sex}\n"
                commonset += f"Innate traits: {self.innate}\n"
                commonset += f"Learned traits: {self.learned}\n"
                commonset += f"Currently: {self.currently}\n"
                commonset += f"Lifestyle: {self.lifestyle}\n"
                commonset += f"Daily req: {self.daily_req}\n"
                # commonset += f"Curr time: {self.curr_time}\n"
                return commonset
            def get_str_lifestyle(self):
                return self.lifestyle

            def get_str_name(self):
                return self.name

            def get_str_firstname(self):
                return self.name.split()[0]  
            # def get_str_curr_date_str(self):
            #     return self.curr_time

            def get_str_daily_plan_req(self):
                return self.daily_req
            # def get_f_daily_schedule_index(self, advance=0):
            #     # We first calculate teh number of minutes elapsed today.

            #     self.curr_time = datetime.strptime(self.curr_time, "%B %d, %Y, %H:%M:%S")
            #     today_min_elapsed = 0
            #     today_min_elapsed += self.curr_time.hour * 60
            #     today_min_elapsed += self.curr_time.minute
            #     today_min_elapsed += advance
            #     curr_index = 0
            #     elapsed = 0
            #     for task, duration in self.f_daily_schedule:
            #         elapsed += duration
            #         if elapsed > today_min_elapsed:
            #             return curr_index
            #         curr_index += 1

            #     return curr_index

        return Scratch(scratch_data)




class MemoryTree:
    def __init__(self, f_saved):
        self.tree = {}
        if check_if_file_exists(f_saved):
            self.tree = json.load(open(f_saved))
    def get_str_accessible_sectors(self, curr_world):
        x = ", ".join(list(self.tree[curr_world].keys()))
        return x

    def get_str_accessible_sector_arenas(self, sector):
        curr_world, curr_sector = sector.split(":")
        if not curr_sector:
            return ""
        x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))
        return x
    def get_str_accessible_arena_game_objects(self, arena):
        curr_world, curr_sector, curr_arena = arena.split(":")

        if not curr_arena: 
            return ""
        x = None
        try: 
            data = self.tree[curr_world][curr_sector].get(curr_arena,"")
            if data is None:
                data = self.tree[curr_world][curr_sector].get(curr_arena.lower(),"")
            if data is not None:
                x = ", ".join(list(data))
        except: 
            x = None
        return x
    def get_all_str_accessible_positions(self, curr_world):
        sectors = self.get_str_accessible_sectors(curr_world)
        all_areas = []
        result_position_list = []
        for sector in sectors.split(", "):
            if sector != "":
                tmp_arr = self.get_str_accessible_sector_arenas(f"{curr_world}:{sector}").split(", ")
                for arena in tmp_arr:
                    if arena != "":
                        all_areas += [f"{curr_world}:{sector}:{arena}"]
        for i in all_areas:
            if i :
                object_list_str= self.get_str_accessible_arena_game_objects(i) 
                if object_list_str != "":
                    object_list = object_list_str.split(", ")
                    for j in object_list:
                        result_position_list += [f"{i}:{j}"]
        return result_position_list    
#x = MemoryTree(x)


maze = Maze("the ville")


def make_persona_by_id(persona_id:int):
    character = Character()
    character = character.find_by_id(id=persona_id)
    persona_programmer = Persona({
        "scratch": {
            "user_id": character.id,
            "s_mem":{},
            "curr_tile":(5, 21),
            "name": character.name,
            "first_name": character.first_name,
            "last_name": character.last_name,
            "age": character.age,
            "sex": character.sex,
            "innate": character.innate,
            "learned": character.learned,
            "currently": character.currently,
            "lifestyle": character.lifestyle,
            "living_area": "the ville:artist's co-living space:common room",
            "daily_req":"",
        }
    })
    persona_programmer.s_mem = MemoryTree(x)
    return persona_programmer


def persona_daily_task(character_id:int):
    character = Character()
    character.update_by_id(character_id,status="PROCESSING")
    persona = make_persona_by_id(character_id)
    plan_list = born_person_schedule(persona)
    # plan_list is a two-dimensional array
    s = Schedule()
    for i, plans in enumerate(plan_list):
        daily_plans = address_determine_action(persona, maze, plans)
        schdule_list = []
        for i,plan in enumerate(daily_plans):
            act_time = plan["time"]
            start_time = int(act_time.split(":")[0]) * 60 + int(act_time.split(":")[1])
            schedule = Schedule()
            schedule.user_id = plan["user_id"]
            schedule.name = plan["name"]
            schedule.start_minute = start_time
            schedule.duration = plan["duration"]
            schedule.action = plan["action"]
            schedule.site = plan.get("address", "")
            schedule.emoji = plan.get("emoji", "")
            schdule_list.append(schedule)
        s.get_session().add_all(schdule_list)
        s.get_session().commit()
    # update character table update status to sucess
    # fetch from character table where id = person_id
    # update status to success
    character = Character()
    character.update_by_id(character_id,status="COMPLETED")

if __name__ == "__main__":
    persona_daily_task(1)
    # plan_tasks = [
    #     {
    #         "name": "carlos gomez",
    #         "user_id": "0",
    #         "time": "07:51",
    #         "duration": "5",
    #         "action": "Gather writing materials for poetry"
    #     },
    #     {
    #         "name": "carlos gomez",
    #         "user_id": "0",
    #         "time": "07:56",
    #         "duration": "4",
    #         "action": "Settle into writing space and reflect"
    #     }
    # ]
    # address_determine_action(make_persona_by_id(0), maze, plan_tasks)
    # print(run_gpt_prompt_pronunciatio(["Settle into writing space and reflect","Gather writing materials for poetry"],make_persona_by_id(0)))
