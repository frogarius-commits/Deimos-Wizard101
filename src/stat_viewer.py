import asyncio
from loguru import logger
from typing import Dict, List, Tuple
from wizwalker import Client
from wizwalker.errors import MemoryInvalidated
from wizwalker.combat import CombatHandler, CombatMember
from src.combat_objects import school_to_str
from src.combat_utils import get_str_masteries, enemy_type_str, add_universal_stat, to_seperated_str_stats, to_percent

# UNFINISHED - slack

# STATS FORMAT
# NAME: example - SCHOOL: example
# POWER PIPS: X - PIPS: X
# SHADOW PIPS: X
# Boosts: Ice - 35%, Myth - 40%
# Resists: Fire - 70%, Storm - 80%
# Damages: Fire - 80%, Storm - 65%
# Criticals: Fire - 121, Storm - 272
# Blocks: Ice - 60, Myth - 50
# Masteries: Fire, Storm
# Max Possible Damage: 14000 (this won't come for a while)



async def every_hp(client: Client):
    combat = CombatHandler(client)
    client_member = await combat.get_client_member()
    members = await combat.get_members()
    client_part = await client_member.get_participant()
    client_team = await client_part.team_id()
    
    async def on_client_team(member: CombatMember):
        mem_part = await member.get_participant()
        member_team_id = await mem_part.team_id()
        return client_team == member_team_id
    
    async def get_client_team_members():
        ret = []
        for mem in members:
            if await on_client_team(mem):
                ret.append(mem)
        
        return ret
    
    async def get_enemy_team_members():
        ret = []
        for mem in members:
            if not await on_client_team(mem):
                ret.append(mem)
        
        return ret
            
    
    allies = await get_client_team_members()
    enemies = await get_enemy_team_members()
    
    ret_string = ""
    for ally in allies:
        ally: CombatMember
        name = await ally.name()
        health = await ally.health()
        max_health = await ally.max_health()
        ret_string += f"{name}: {health}/{max_health}, "
    
    ret_string = ret_string.strip(", ")
    ret_string += "\n"
    
    for enemy in enemies:
        enemy: CombatMember
        name = await enemy.name()
        health = await enemy.health()
        max_health = await enemy.max_health()
        ret_string += f"{name}: {health}/{max_health}, "

    ret_string = ret_string.strip(", ")
    
    return ret_string
        


async def total_stats(client: Client, caster_index: int) -> Tuple[List[str], List[str], int]:
    # Gets the readable relevant stats from
    combat = CombatHandler(client)
    try:
        members = await combat.get_members()
        if len(members) < caster_index:
            caster_index = len(members) - 1

        else:
            caster_index -= 1

        member = members[caster_index]

        member_id = await member.owner_id()
        participant = await member.get_participant()
        stats = await member.get_stats()

    except MemoryInvalidated:
        await asyncio.sleep(0.5)
        await total_stats(client, caster_index)

    else:
        member_names = [await m.name() for m in members]
        names_with_indexes = [f'{i + 1} - {name}' for i, name in enumerate(member_names)]
        member_name = await member.name()
        member_type = await enemy_type_str(member)
        school_id = await participant.primary_magic_school_id()

        real_school_id = await participant.primary_magic_school_id()

        school_name = school_to_str[real_school_id]

        # Pips
        pip_count = await participant.pip_count()
        pip_string = "Pips: "
        
        pips = await pip_count.generic_pips()
        if pips > 0: pip_string += f"White: {pips}, "
        
        power_pips = await pip_count.power_pips()
        if power_pips > 0: pip_string += f"Power: {power_pips}, "
        
        balance_pips = await pip_count.balance_pips()
        if balance_pips > 0: pip_string += f"Balance: {balance_pips}, "
        
        death_pips = await pip_count.death_pips()
        if death_pips > 0: pip_string += f"Death: {death_pips}, "
        
        fire_pips = await pip_count.fire_pips()
        if fire_pips > 0: pip_string += f"Fire: {fire_pips}, "
        
        ice_pips = await pip_count.ice_pips()
        if ice_pips > 0: pip_string += f"Ice: {ice_pips}, "
        
        life_pips = await pip_count.life_pips()
        if life_pips > 0: pip_string += f"Life: {life_pips}, "
        
        myth_pips = await pip_count.myth_pips()
        if myth_pips > 0: pip_string += f"Myth: {myth_pips}, "
        
        storm_pips = await pip_count.storm_pips()
        if storm_pips > 0: pip_string += f"Storm: {storm_pips}, "
        
        pip_string = pip_string.strip(", ")

        shadow_pips = await member.shadow_pips()
        
        

        health = await member.health()
        max_health = await member.max_health()

        raw_resistances = await stats.dmg_reduce_percent()
        uni_resist = await stats.dmg_reduce_percent_all()
        real_resistances = to_percent(add_universal_stat(raw_resistances, uni_resist))

        raw_damages = await stats.dmg_bonus_percent()
        uni_damage = await stats.dmg_bonus_percent_all()
        real_damages = to_percent(add_universal_stat(raw_damages, uni_damage))

        raw_pierces = await stats.ap_bonus_percent()
        uni_pierce = await stats.ap_bonus_percent_all()
        real_pierces = to_percent(add_universal_stat(raw_pierces, uni_pierce))

        raw_crits = await stats.critical_hit_rating_by_school()
        uni_crit = await stats.critical_hit_rating_all()
        real_crits = add_universal_stat(raw_crits, uni_crit)

        raw_blocks = await stats.block_rating_by_school()
        uni_block = await stats.block_rating_all()
        real_blocks = add_universal_stat(raw_blocks, uni_block)

        masteries = await get_str_masteries(member)
        masteries_str = ', '.join(masteries)

        global_effect = None
        combat_resolver = await client.duel.combat_resolver()
        if combat_resolver:
            global_effect = await combat_resolver.global_effect()
            

        resistances, raw_boosts = to_seperated_str_stats(real_resistances)

        damages, _ = to_seperated_str_stats(real_damages)
        pierces, _ = to_seperated_str_stats(real_pierces)
        crits, _ = to_seperated_str_stats(real_crits)
        blocks, _ = to_seperated_str_stats(real_blocks)        

        #if await member.is_player() and await target.is_player():
        #    total_stats = ['The stat viewer is not supported in PvP.']
        red_herring = ""
        ghastly_school = ""
        auras = await participant.aura_effects()
        shadows = await participant.shadow_spell_effects()
        for aura in auras:
            aura_id = await aura.spell_template_id()
            logger.debug(f'Aura ID: {aura_id}')
            match aura_id:
                case 600640741:
                    red_herring = "Storm"
                case 1450964216:
                    red_herring = "Myth"
                case 1297346808:
                    red_herring = "Life"
                case 949558024:
                    red_herring = "Ice"
                case 1276369144:
                    red_herring = "Fire"
                case 1864749286:
                    red_herring = "Death"
                case 973631491:
                    red_herring = "Balance"
                case 1594767102:
                    ghastly_school = "Death"
                case 394456798:
                    ghastly_school = "Fire"
                case 363805230:
                    ghastly_school = "Ice"
                case 394784382:
                    ghastly_school = "Life"
                case 401297006:
                    ghastly_school = "Myth"
                case 1513985422:
                    ghastly_school = "Storm"
        for shadow in shadows:
            shadow_id = await shadow.spell_template_id()
            match shadow_id:
                case 1594767102:
                    ghastly_school = "Death"
                case 394456798:
                    ghastly_school = "Fire"
                case 363805230:
                    ghastly_school = "Ice"
                case 394784382:
                    ghastly_school = "Life"
                case 401297006:
                    ghastly_school = "Myth"
                case 1513985422:
                    ghastly_school = "Storm"
                
        #else:
        total_stats = [
            f'Name: {member_name} - {member_type} - {school_name}',
            pip_string,
            f'Shadow Pips: {shadow_pips}',
            f'Health: {health}/{max_health} ({int((health / max_health) * 100)}%)',
            f'Resists: {dict_to_str(resistances | raw_boosts)}',
            f'Damages: {dict_to_str(damages)}',
            f'Pierces: {dict_to_str(pierces)}',
            f'Crits: {dict_to_str(crits)}',
            f'Blocks: {dict_to_str(blocks)}',
            f'Masteries: {masteries_str}',
        ]
        
        if red_herring:
            total_stats.insert(0, f'Red Herring Aura: {red_herring}')
        if ghastly_school:
            total_stats.insert(0, f'Shrike School: {ghastly_school}')

        return (total_stats, names_with_indexes, caster_index)


def dict_to_str(input_dict: Dict[str, float], seperator_1: str = ': ', seperator_2: str = ', ', take_abs: bool = False, key_blacklist: List[str] = ['WhirlyBurly', 'Gardening', 'CastleMagic', 'Cantrips', 'Fishing']) -> str:
    # Converts a str stats dict to a GUI readable list of stats
    output_str = ''
    for key in list(input_dict.keys()):
        if key not in key_blacklist:
            if not take_abs:
                output_str += f'{key}{seperator_1}{int(input_dict[key])}{seperator_2}'

            else:
                output_str += f'{key}{seperator_1}{abs(int(input_dict[key]))}{seperator_2}'

    return output_str


def to_gui_str(stats, seperator: str = '\n') -> str:
    # Converts the total stats into GUI readable strings
    str_stats_list = []
    for stat in stats:
        if type(stat) == Dict[str, float]:
            str_stats_list.append(dict_to_str(stat))

        else:
            str_stats_list.append(str(stat))

    str_stats = seperator.join(str_stats_list)

    return str_stats
