#生成个人日程
from datetime import datetime, timedelta
from base import *
from system.plan import *
import json
from model.schdule import *


from maza.maze import Maze



def born_person_schedule(persona):
    wake_up_hour = generate_wake_up_hour(persona)
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
                    tmp1 = clean_and_parse(hour_plan)
                    hour_plan_list.extend(tmp1)
                    break
    return hour_plan_list



def clean_and_parse(raw_json: str) -> list:
    cleaned = filter_result(raw_json)
    try:
        data = json.loads(cleaned)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON decode failed,err: {e}")
        raise

def address_determine_action(persona, maze,plan_list):
    
    for i,activity in enumerate(plan_list):
        action = activity["action"]
        act_world ="the ville"
        # act_sector = maze.access_tile(persona.scratch.curr_tile)["sector"]
        act_sector = generate_action_sector(action, persona, maze)
        act_arena = generate_action_arena(action, persona, maze, act_world, act_sector)
        act_address = f"{act_world}:{act_sector}:{act_arena}"
        act_game_object = generate_action_game_object(action, act_address,
                                                  persona, maze)
        new_address = f"{act_world}:{act_sector}:{act_arena}:{act_game_object}"
        act_pron = generate_action_pronunciatio(action, persona)
        plan_list[i]['address'] = new_address
        plan_list[i]['emoji'] = act_pron
    return plan_list
       

def generate_wake_up_hour(persona):
    logger_info("get wake up hour:", persona)
    return int(run_gpt_prompt_wake_up_hour(persona)[0])

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
        prompt_ending = (f"Generate activity data for an hour from {curr_hour_str} to the following hour. It is important to break down the multiple activities generated into smaller activities with a duration of 3 to 5 minutes and output information about the smaller activities."
                         f"No need to break up into small activities at night time for bedtime, you can just output")
        prompt_ending += (f" The output is required to contain only json format content, \"duration\" time must add up to 1 hour. The value of \"duration\" must be between 3 and 5 minutes. "
                          f"The output consists of json data only and contains only five fields: name,user_id,schedule,time,duration,action.like ,\"name\": \"{persona.scratch.name}\", \"user_id\": \"{persona.scratch.user_id}\" ,\"time\": \"8:00\" ,\"duration\": \"4\", \"action\": \"do something\".\"Time\" is 24 hours, no am and pm.")
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
                 "temperature": 0.5, "top_p": 1, "stream": False,
                 "frequency_penalty": 0, "presence_penalty": 0, "stop":"#"}
    prompt_template = f"{fs_back_end}/persona/prompt_template/v2/generate_hourly_schedule_v2.txt"
    prompt_input = create_prompt_input(persona,
                                       curr_hour_str,
                                       intermission2,
                                       test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()

    output = safe_generate_response(prompt, gpt_param, 1, fail_safe,
                                    __func_validate, __func_clean_up)


    logger_info("run_gpt_prompt_generate_hourly_schedule result:",prompt_template, persona, gpt_param,
                          prompt_input, prompt, output)

    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def generate_first_daily_plan(persona, wake_up_hour):
  logger_info('get persona daily play:',persona.scratch.name)
  return run_gpt_prompt_daily_plan(persona, wake_up_hour)[0]



x = f'{root_path}/map/matrix2/all_attr.json'
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
        
#x = MemoryTree(x)


maze = Maze("the ville")


def make_persona_by_id(persona_id):

    persona_programmer = Persona({
        "scratch": {
            "user_id": persona_id,
            "s_mem":{},
            "curr_tile":(5, 21),
            # "curr_time": "March 14, 2025, 10:28:50",
            "name": "carlos gomez",
            "first_name": "carlos",
            "last_name": "gomez",
            "age": 25,
            "innate": "frindly, helpful, Intelligent",
            "learned": "carlos gomez is a poet who loves to explore his inner thoughts and feelings. He is always looking for new ways to express himself.",
            "currently": "Advocates that if capital distribution is unfair, the AI economy will exacerbate social inequality.",
            "lifestyle": "carlos gomez goes to bed around 10pm, awakes up around 7am, eats dinner around 5pm.",
            "living_area": "the ville:carlos gomez's apartment:main room",
            "daily_req":"",
        }
    })
    persona_programmer.s_mem = MemoryTree(x)
    return persona_programmer
def persona_daily_task(person_id:int):
    persona = make_persona_by_id(person_id)
    plan_list = born_person_schedule(persona)
    daily_plans = address_determine_action(persona, maze, plan_list)
    schdule_list = []
    for i,plan in enumerate(daily_plans):
        act_time = plan["time"]
        start_time = int(act_time.split(":")[0]) * 60 + int(act_time.split(":")[1])
        schdule_list.append(Schdule(
            user_id=persona.scratch.user_id,
            name=persona.scratch.name,
            start_minute=start_time,
            duration=plan["duration"],
            action=plan["action"],
            site=plan["address"],
            emoji=plan["emoji"]
        ))
    s = Schdule()
    s.session.add_all(schdule_list)
    s.session.commit()

if __name__ == "__main__":
   persona_daily_task(0)
