from cogs.Unbound import helperfunctions
import json
import numpy as np

############-IMPORTING UNBOUND DATA TO DICTIONARIES-###########################################################

with open("cogs/Unbound/DATA/abilities.json", encoding='utf8') as file:
    abilities_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/ability_description.json", encoding='utf8') as file:
    ability_desc_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/eggmoves.json", encoding='utf8') as file:
    eggmoves_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/helditem.json", encoding='utf8') as file:
    helditem_dict = helperfunctions.listToDict('itemname', json.load(file))

with open("cogs/Unbound/DATA/Learnsets.json", encoding='utf8') as file:
    lvlupmoves_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/megastone.json", encoding='utf8') as file:
    megastone_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/pokelocation.json", encoding='utf8') as file:
    pokelocation_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/scalemon.json", encoding='utf8') as file:
    scalemon_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/tmlocation.json", encoding='utf8') as file:
    tmlocation_dict = helperfunctions.listToDict('tmname', json.load(file))
    tm_name_number_mapping = dict(zip(np.char.mod('%d', np.arange(1, 121, 1)), tmlocation_dict.keys())) #making a number string mapping for the tm dictionary

with open("cogs/Unbound/DATA/tm_and_tutor.json", encoding='utf8') as file:
    tm_and_tutor_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/zlocation.json", encoding='utf8') as file:
    zlocation_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/movedescription.json", encoding='utf8') as file:
    move_info_dict = helperfunctions.listToDict('movename', json.load(file))

with open("cogs/Unbound/DATA/Base_Stats.json", encoding='utf8') as file:
    base_stats_dict = helperfunctions.listToDict('name', json.load(file))

with open("cogs/Unbound/DATA/gifts.json", encoding='utf8') as file:
    gifts_dict = json.load(file)

###############################################################################################################
