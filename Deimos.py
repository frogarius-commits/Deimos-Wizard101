import asyncio
import traceback
#import requests
import queue
import threading
import wizwalker
from src.minimap import MiniMap
from wizwalker import Keycode, HotkeyListener, ModifierKeys, utils, XYZ, Orient
from wizwalker.utils import get_all_wizard_handles, get_foreground_window
from wizwalker.client_handler import ClientHandler, Client
from wizwalker.extensions.scripting import teleport_to_friend_from_list
from wizwalker.memory.memory_objects.camera_controller import DynamicCameraController, ElasticCameraController
from wizwalker.memory.memory_objects.window import Window
from wizwalker.memory.memory_objects.enums import WindowFlags
import os
import time
import sys
import ctypes
import winreg
import subprocess
from loguru import logger
import datetime
from configparser import ConfigParser
import statistics
import re
# import pypresence
from pypresence import AioPresence
from src.az_raid_fish import run_fish, window_exists
from src.command_parser import execute_flythrough, parse_command
from src.auto_pet import nomnom
from src.drop_logger import logging_loop
# from src.combat_new import Fighter
from src.stat_viewer import total_stats, every_hp
from src.teleport_math import navmap_tp, calc_Distance
from src.questing import Quester
from src.sigil import Sigil
from src.utils import index_with_str, is_visible_by_path, is_free, auto_potions, auto_potions_force_buy, to_world, collect_wisps_with_limit, try_task_coro, override_wiz_install_using_handle#, assign_pet_level
from src.paths import advance_dialog_path, decline_quest_path, play_button_path
import PySimpleGUI as gui
import pyperclip
import pywinauto.findwindows
from pywinauto.keyboard import send_keys
from src.sprinty_client import SprintyClient
from src.gui_inputs import param_input, parse_xyz
from src import discsdk
from wizwalker.extensions.wizsprinter.wiz_navigator import toZoneDisplayName, toZone
from wizwalker.extensions.wizsprinter.sprinty_combat import SprintyCombat
from src.config_combat import StrCombatConfigProvider, delegate_combat_configs, default_config
from typing import List

from src import deimosgui
from src.deimosgui import GUIKeys
from src.tokenizer import tokenize
from src.deimoslang import vm
from src.collision_tp import WorldsCollideTP

cMessageBox = ctypes.windll.user32.MessageBoxW


tool_version: str = '3.9.1'
tool_name: str = 'Deimos'
tool_author: str = 'Deimos-Wizard101'
repo_name: str = tool_name + '-Wizard101'
branch: str = 'master'
repo_path_raw: str = f'https://codeberg.org/{tool_author}/{repo_name}/raw/branch/{branch}'

type_format_dict = {
"char": "<c",
"signed char": "<b",
"unsigned char": "<B",
"bool": "?",
"short": "<h",
"unsigned short": "<H",
"int": "<i",
"unsigned int": "<I",
"long": "<l",
"unsigned long": "<L",
"long long": "<q",
"unsigned long long": "<Q",
"float": "<f",
"double": "<d",
}


def remove_if_exists(file_name : str, sleep_after : float = 0.1):
	if os.path.exists(file_name):
		os.remove(file_name)
		time.sleep(sleep_after)


def download_file(url: str, file_name : str, delete_previous: bool = False, debug : str = True):
	if delete_previous:
		remove_if_exists(file_name)
	if debug:
		print(f'Downloading {file_name}...')
	with requests.get(url, stream=True) as r:
		with open(file_name, 'wb') as f:
			for chunk in r.iter_content(chunk_size=128000):
				f.write(chunk)


# reading hotkeys from config
parser = ConfigParser()


def read_config(config_name : str):
	parser.read(config_name)

	# Settings
	global auto_updating
	global speed_multiplier
	global use_potions
	global rpc_status
	global drop_status
	global anti_afk_status
	global minimap_key
	global minimap_status
	global minimap_instance
	global minimap_task
	global hail_limbow_bool
	global fov_value
	minimap_key = parser.get('hotkeys', 'toggle_minimap', fallback='F10')
	auto_updating = parser.getboolean('settings', 'auto_updating', fallback=True)
	speed_multiplier = parser.getfloat('settings', 'speed_multiplier', fallback=5.0)
	fov_value = parser.getfloat('settings', 'default_fov_value', fallback=750.0)
	hail_limbow_bool = parser.getboolean('settings', 'all_hail_limbow', fallback=True)
	use_potions = parser.getboolean('settings', 'use_potions', fallback=True)
	rpc_status = parser.getboolean('settings', 'rich_presence', fallback=True)
	drop_status = parser.getboolean('settings', 'drop_logging', fallback=True)
	anti_afk_status = parser.getboolean('settings', 'use_anti_afk', fallback=True)


	# Hotkeys
	global x_press_key
	global cantrip_window_key
	global sync_locations_key
	global quest_teleport_key
	global mass_quest_teleport_key
	global toggle_speed_key
	global friend_teleport_key
	global kill_tool_key
	global toggle_auto_combat_key
	global toggle_auto_dialogue_key
	global toggle_auto_sigil_key
	global toggle_freecam_key
	global toggle_auto_questing_key
	global wood_chest_key
	global silver_chest_key
	global gold_chest_key
	global dog_tracy_key
	global entity_tp_key
	global snake_tp_key
	global spider_tp_key
	global crane_tp_key
	global butterfly_tp_key
	global tree_tp_key
	global custom_tp_key
	x_press_key = parser.get('hotkeys', 'x_press', fallback='X')
	cantrip_window_key = parser.get('hotkeys', 'cantrip_window', fallback='DEL')
	sync_locations_key = parser.get('hotkeys', 'sync_client_locations', fallback='F8')
	quest_teleport_key = parser.get('hotkeys', 'quest_teleport', fallback='F7')
	mass_quest_teleport_key = parser.get('hotkeys', 'mass_quest_teleport', fallback='F6')
	toggle_speed_key = parser.get('hotkeys', 'toggle_speed_multiplier', fallback='F5')
	friend_teleport_key = parser.get('hotkeys', 'friend_teleport', fallback='EIGHT')
	kill_tool_key = parser.get('hotkeys', 'kill_tool', fallback='F9')
	toggle_auto_combat_key = parser.get('hotkeys', 'toggle_auto_combat', fallback='NINE')
	toggle_auto_dialogue_key = parser.get('hotkeys', 'toggle_auto_dialogue', fallback='F4')
	toggle_auto_sigil_key = parser.get('hotkeys', 'toggle_auto_sigil', fallback='F2')
	toggle_freecam_key = parser.get('hotkeys', 'toggle_freecam', fallback='F1')
	toggle_auto_questing_key = parser.get('hotkeys', 'toggle_auto_questing', fallback='F3')


	# GUI Settings

	wood_chest_key = parser.get('hotkeys', 'wood_chest', fallback='Numeric_pad_41')
	silver_chest_key = parser.get('hotkeys', 'silver_chest', fallback='Numeric_pad_51')
	gold_chest_key = parser.get('hotkeys', 'gold_chest', fallback='Numeric_pad_61')
	dog_tracy_key = parser.get('hotkeys', 'dog_tracy', fallback='Numeric_pad_81')
	entity_tp_key = parser.get('hotkeys', 'entity_tp', fallback='Numeric_pad_20')
	snake_tp_key = parser.get('hotkeys', 'snake_tp', fallback='Numeric_pad_10')
	spider_tp_key = parser.get('hotkeys', 'spider_tp', fallback='Numeric_pad_14')
	crane_tp_key = parser.get('hotkeys', 'crane_tp', fallback='Numeric_pad_13')
	butterfly_tp_key = parser.get('hotkeys', 'butterfly_tp', fallback='Numeric_pad_11')
	tree_tp_key = parser.get('hotkeys', 'tree_tp', fallback='Numeric_pad_12')
	custom_tp_key = parser.get('hotkeys', 'custom_tp', fallback='Add')


	# GUI Settings
    
	custom_theme = {
	'BACKGROUND': "#000000",
	'TEXT': "#fbfbfb",
	'INPUT': "#040203",
	'TEXT_INPUT': '#ff7bb8',
	'SCROLL': '#b44177',
	'BUTTON': ('#ffc0cb', '#b44177'),
	'PROGRESS': ('#f278b8', '#3b1f2b'),
	'BORDER': 1,
	'SLIDER_DEPTH': 0,
	'PROGRESS_DEPTH': 0,
	'TAB': '#ff7bb8', 
	}

	gui.theme_add_new('DeimosPink', custom_theme)
    
    
	global show_gui
	global gui_on_top
	global gui_theme
	global gui_text_color
	global gui_button_color
	global gui_langcode
	show_gui = parser.getboolean('gui', 'show_gui', fallback=True)
	gui_on_top = parser.getboolean('gui', 'on_top', fallback=True)
	gui_theme = parser.get('gui', 'theme', fallback='Black')
	gui_text_color = parser.get('gui', 'text_color', fallback='white')
	gui_button_color = parser.get('gui', 'button_color', fallback='#4a019e')
	#gui_text_color = parser.get('gui', 'text_color', fallback='white')
	#gui_button_color = parser.get('gui', 'button_color', fallback='#4a019e')
	gui_text_color = custom_theme['TEXT']
	gui_button_color = custom_theme['BUTTON'][1]
	gui_langcode = parser.get('gui', 'locale', fallback='en')


	# Auto Sigil Settings
	global use_team_up
	global buy_potions
	global client_to_follow
	use_team_up = parser.getboolean('sigil', 'use_team_up', fallback=False)
	buy_potions = parser.getboolean('settings', 'buy_potions', fallback=True)
	client_to_follow = parser.get('sigil', 'client_to_follow', fallback=None)


	# Auto Questing Settings
	global client_to_boost
	global questing_friend_tp
	global gear_switching_in_solo_zones
	global hitter_client
	client_to_boost = parser.get('questing', 'client_to_boost', fallback=None)
	questing_friend_tp = parser.getboolean('questing', 'friend_teleport', fallback=False)
	gear_switching_in_solo_zones = parser.getboolean('questing', 'gear_switching_in_solo_zones', fallback=False)
	hitter_client = parser.get('questing', 'hitter_client', fallback=None)
	# empty string can falsely be read as a client.  Check if the user's config entry was valid and set to None if not
	valid_configs = ['p1', 'p2', 'p3', 'p4', '1', '2', '3', '4']
	if any(hitter_client == option for option in valid_configs):
		pass
	else:
		hitter_client = None


	# Combat Settings
	global kill_minions_first
	global automatic_team_based_combat
	global discard_duplicate_cards
	kill_minions_first = parser.getboolean('combat', 'kill_minions_first', fallback=False)
	automatic_team_based_combat = parser.getboolean('combat', 'automatic_team_based_combat', fallback=False)
	discard_duplicate_cards = parser.getboolean('combat', 'discard_duplicate_cards', fallback=True)


	# Auto Pet Settings
	global ignore_pet_level_up
	global only_play_dance_game
	ignore_pet_level_up = parser.getboolean('auto pet', 'ignore_pet_level_up', fallback=False)
	only_play_dance_game = parser.getboolean('auto pet', 'only_play_dance_game', fallback=False)


while True:
	if not os.path.exists(f'{tool_name}-config.ini'):
		# download_file(f'https://raw.githubusercontent.com/{tool_author}/{repo_name}/{branch}/{tool_name}-config.ini', f'{tool_name}-config.ini')
		download_file(f'{repo_path_raw}/{tool_name}-config.ini', f'{tool_name}-config.ini')
	time.sleep(0.1)

	read_config(f'{tool_name}-config.ini')
	break

#while True:
#	if hasattr(sys, '_MEIPASS'):
#		folder_path = os.path.join(sys._MEIPASS, 'wizwalker/extensions/wizsprinter/traversalData')
#		if not os.path.exists(folder_path):
#			os.makedirs(folder_path)
#		download_file('https://raw.githubusercontent.com/notfaj/wizsprinter/main/wizwalker/extensions/wizsprinter/traversalData/displayZones.txt', os.path.join(folder_path, 'displayZones.txt'))
#		download_file('https://raw.githubusercontent.com/notfaj/wizsprinter/main/wizwalker/extensions/wizsprinter/traversalData/gates_list.txt', os.path.join(folder_path, 'gates_list.txt'))
#		download_file('https://raw.githubusercontent.com/notfaj/wizsprinter/main/wizwalker/extensions/wizsprinter/traversalData/interactiveTeleporters.txt', os.path.join(folder_path, 'interactiveTeleporters.txt'))
#		download_file('https://raw.githubusercontent.com/notfaj/wizsprinter/main/wizwalker/extensions/wizsprinter/traversalData/objectLocations.txt', os.path.join(folder_path, 'objectLocations.txt'))
#		download_file('https://raw.githubusercontent.com/notfaj/wizsprinter/main/wizwalker/extensions/wizsprinter/traversalData/uniqueObjectLocations.txt', os.path.join(folder_path, 'uniqueObjectLocations.txt'))
#		download_file('https://raw.githubusercontent.com/notfaj/wizsprinter/main/wizwalker/extensions/wizsprinter/traversalData/zoneMap.txt', os.path.join(folder_path, 'zoneMap.txt'))
#	break


speed_status = False
combat_status = False
dialogue_status = False
sigil_status = False
freecam_status = False
hotkey_status = False
questing_status = False
auto_pet_status = False
auto_potion_status = False
side_quest_status = False
tool_status = True
minimap_status = False
minimap_instance = None
minimap_task = None
original_client_locations = dict()



hotkeys_blocked = False

sigil_leader_pid: int = None
questing_leader_pid: int = None

questing_task: asyncio.Task = None
auto_pet_task: asyncio.Task = None
sigil_task: asyncio.Task = None
dialogue_task: asyncio.Task = None
combat_task: asyncio.Task = None
tp_task: asyncio.Task = None
speed_task: asyncio.Task = None
fish_task: asyncio.Task = None
pet_task: asyncio.Task = None
hail_limbow_task: asyncio.Task = None
fov_task: asyncio.Task = None

vvr_drums_task: asyncio.Task = None

csr_drums_task: asyncio.Task = None
pods_task: asyncio.Task = None
tears_task: asyncio.Task = None
eggs_task: asyncio.Task = None

wood_tokens_task: asyncio.Task = None
silver_tokens_task: asyncio.Task = None
gold_tokens_task: asyncio.Task = None
forensic_task: asyncio.Task = None
bombshell_task: asyncio.Task = None

daemon_task: asyncio.Task = None
cabalist_task: asyncio.Task = None

bot_task: asyncio.Task = None
flythrough_task: asyncio.Task = None

def file_len(filepath) -> List[str]:
	# return the number of lines in a file
	f = open(filepath, "r")
	return len(f.readlines())


def generate_timestamp() -> str:
	# generates a timestamp and makes the symbols filename-friendly
	time = str(datetime.datetime.now())
	time_list = time.split('.')
	time_stamp = str(time_list[0])
	time_stamp = time_stamp.replace('/', '-').replace(':', '-')
	return time_stamp


def config_update():
	config_url = f'{repo_path_raw}/{tool_name}-config.ini'

	if not os.path.exists(f'{tool_name}-config.ini'):
		download_file(url=config_url, file_name=f'{tool_name}-config.ini')
		time.sleep(0.1)

	if not os.path.exists(f'README.md'):
		download_file(f'{repo_path_raw}/README.md', 'README.md')

	download_file(url=config_url, file_name=f'{tool_name}-Testconfig.ini', delete_previous=True, debug=False)
	time.sleep(0.1)

	comparison_parser = ConfigParser()
	comparison_parser.read(f'{tool_name}-Testconfig.ini')
	comparison_sections = comparison_parser.sections()
	for i in comparison_sections:
		if not parser.has_section(i):
			print(f'Config file lacks section "{i}", adding it.')
			parser.add_section(i)

		comparison_options = comparison_parser.options(i)
		for b in comparison_options:
			if not parser.has_option(i, b):
				print(f'Config file section "{i}" lacks option "{b}", adding it and its default value.')
				parser.set(i, b, str(comparison_parser.get(i, b)))

	sections = parser.sections()
	for i in sections:
		if not comparison_parser.has_section(i):
			print(f'Config file has erroneous section "{i}", removing it.')
			parser.remove_section(i)

		options = parser.options(i)
		for b in options:
			if not comparison_parser.has_option(i, b):
				print(f'Config file section "{i}" has erroneous option "{b}", removing it.')
				parser.remove_option(i, b)

	with open(f'{tool_name}-config.ini', 'w') as new_config:
		parser.write(new_config)
	remove_if_exists(f'{tool_name}-Testconfig.ini')
	time.sleep(0.1)
	read_config(f'{tool_name}-config.ini')
	print('\n')


def run_updater():
	download_file(url=f"{repo_path_raw}/{tool_name}Updater.exe", file_name=f'{tool_name}Updater.exe', delete_previous=True)
	time.sleep(0.1)
	subprocess.Popen(f'{tool_name}Updater.exe')
	sys.exit()


def get_latest_version() -> str:
	update_server = None

	try:
		update_server = read_webpage(f"{repo_path_raw}/LatestVersion.txt")
	except:
		time.sleep(0.1)

	if len(update_server) >= 1:
		return update_server[0]
	else:
		return None


def is_version_greater(version: str, comparison_version: str) -> bool:
	# Compares the semantic version of two inputted versions and returns True if the first is greater
	version_list = version.split('.')
	comparison_version_list = comparison_version.split('.')

	for i, v in enumerate(version_list):
		current_v = int(v)
		current_comparison_v = int(comparison_version_list[i])
		if current_v > current_comparison_v:
			return True
		elif current_v < current_comparison_v:
			return False

	return False


def auto_update(latest_version: str = "3.9.1"):
	remove_if_exists(f'{tool_name}-copy.exe')
	remove_if_exists(f'{tool_name}Updater.exe')
	time.sleep(0.1)
	if auto_updating:
		if is_version_greater(latest_version, tool_version):
			run_updater()


def hotkey_button(name: str, auto_size: bool = False, text_color: str = gui_text_color, button_color: str = gui_button_color):
	return gui.Button(name, button_color=(text_color, button_color), auto_size_button=auto_size)


async def mass_key_press(foreground_client : Client, background_clients : list[Client], pressed_key_name: str, key, duration : float = 0.1, debug : bool = False):
	# sends a given keystroke to all clients, handles foreground client seperately
	if debug and foreground_client:
		key_name = str(key)
		key_name = key_name.replace('Keycode.', '')
		logger.debug(f'{pressed_key_name} key pressed, sending {key_name} key press to all clients.')
	await asyncio.gather(*[p.send_key(key=key, seconds=duration) for p in background_clients])
	# only send foreground key press if there is a client in foreground
	if foreground_client:
		await foreground_client.send_key(key=key, seconds=duration)

async def are_xyzs_within_threshold(xyz_1 : XYZ, xyz_2 : XYZ, threshold : int = 25):
	if not abs(xyz_1.x - xyz_2.x) < threshold:
		return False
	if not abs(xyz_1.y - xyz_2.y) < threshold:
		return False
	if not abs(xyz_1.z - xyz_2.z) < threshold:
		return False
	return True

async def custom_tp(foreground_client : Client, pressed_key_name: str, xyz_string: str, yaw_string: str, debug : bool = False):
	if foreground_client:
		current_pos = await foreground_client.body.position()
		current_rotation = await foreground_client.body.orientation()
		xyz_lst = parse_xyz(xyz_string, [current_pos.x, current_pos.y, current_pos.z])
		x_input = xyz_lst[0]
		y_input = xyz_lst[1]
		z_input = xyz_lst[2]
		yaw_input = param_input(yaw_string, current_rotation.yaw)

		custom_xyz = XYZ(x=x_input, y=y_input, z=z_input)
		if debug:
			logger.debug(f'{pressed_key_name} pressed. Teleporting client {foreground_client.title} to {custom_xyz}, yaw= {yaw_input}')
		await foreground_client.teleport(custom_xyz)
		await foreground_client.body.write_yaw(yaw_input)

async def entity_tp_helper(foreground_client : Client, pressed_key_name: str, entity_string: str, debug : bool = False):
	if not freecam_status:
		if entity_string:
			if foreground_client:
				sprinter = SprintyClient(foreground_client)
				entities_list = await sprinter.get_base_entities_with_vague_name(entity_string)
				entities = []
				if entities_list:
					if "inviso" in entity_string.lower():
						for entity in entities_list:
							behav = await entity.search_behavior_by_name("AnimationBehavior")
							string = await behav.read_string_from_offset(576)
							if string:
								entities.append(entity)
					elif "lightpad" in entity_string.lower():
						excluded_drums = [
							XYZ(2.0806429386138916, -1375.636962890625, 1800.2769775390625),
							XYZ(-3.881438970565796, 1346.467041015625, 1800.2769775390625),
							XYZ(-1360.4449462890625, -2.781054973602295, 1800.2769775390625),
							XYZ(1345.9990234375, 7.738836765289307, 1800.2769775390625),
							XYZ(5887.60107421875, 421.2580871582031, 428.4424133300781),
							XYZ(5687.97607421875, 223.47740173339844, 429.1733093261719),
							XYZ(5682.92822265625, -44.51580047607422, 429.1733093261719),
							XYZ(5889.703125, -250.23939514160156, 429.1733093261719),
							XYZ(6156.4619140625, -254.2375030517578, 429.1733093261719),
							XYZ(6346.72607421875, -75.12811279296875, 429.1733093261719),
							XYZ(6362.3818359375, 220.32989501953125, 429.1733093261719),
							XYZ(6171.3671875, 439.0443115234375, 429.1733093261719),
							XYZ(6007.57177734375, 110.20999908447266, 432.0935974121094),
							#XYZ(156.32049560546875, 10636.1904296875, 45.247039794921875),
							XYZ(21.287410736083984, 10961.7099609375, 39.414398193359375),
							XYZ(-171.69459533691406, 10763.9296875, 40.14535140991211),
							XYZ(-176.74240112304688, 10495.9404296875, 40.14535140991211),
							XYZ(30.03204917907715, 10290.2197265625, 40.14535140991211),
							XYZ(296.79119873046875, 10286.2197265625, 40.14535140991211),
							XYZ(487.0555114746094, 10465.330078125, 40.14535140991211),
							XYZ(502.71148681640625, 10760.7900390625, 40.14535140991211),
							XYZ(311.6960144042969, 10979.5, 40.14535140991211),
							XYZ(-7533.02099609375, 3650.97998046875, 30.14211082458496)
						]
                        
						for entity in entities_list:
							entity_pos: XYZ = await entity.location()
							check = True
							for drum in excluded_drums:
								if await are_xyzs_within_threshold(entity_pos, drum):
									check = False
									break
							if check:
								entities.append(entity)
					elif "power" in entity_string.lower():
						for entity in entities_list:
							entity_name = await entity.object_name()
							if not "PowerSource_Not" in entity_name:
								entities.append(entity)
					else:
						entities = entities_list.copy()
					
					entity = await sprinter.find_closest_of_entities(entities)
					entity_pos: XYZ = await entity.location()
					entity_name = await entity.object_name()
					if debug:
						logger.debug(f'{pressed_key_name} pressed, teleporting to {entity_name}.')
					await WorldsCollideTP(foreground_client, entity_pos, static_body_radius=0.0)
					#await foreground_client.teleport(entity_pos)

async def wood_chest_tp(foreground_client : Client, pressed_key_name: str, debug : bool = False):
	if foreground_client:
		if debug:
			logger.debug(f'{pressed_key_name} key pressed, teleporting foreground client to Wood Chest.')
		await foreground_client.teleport(XYZ(x=-2309.12158203125,y=-7644.15673828125,z=750.4605102539062))

async def silver_chest_tp(foreground_client : Client, pressed_key_name: str, debug : bool = False):
	if foreground_client:
		if debug:
			logger.debug(f'{pressed_key_name} key pressed, teleporting foreground client to Silver Chest.')		
		await foreground_client.teleport(XYZ(x=-9589.6796875,y=-8113.10546875,z=750.46044921875))

async def gold_chest_tp(foreground_client : Client, pressed_key_name: str, debug : bool = False):
	if foreground_client:
		if debug:
			logger.debug(f'{pressed_key_name} key pressed, teleporting foreground client to Gold Chest.')		
		await foreground_client.teleport(XYZ(x=-5986.38037109375,y=-3216.93310546875,z=271.3044128417969))

async def tracy_tp(foreground_client : Client, pressed_key_name: str, debug : bool = False):
	if foreground_client:
		if debug:
			logger.debug(f'{pressed_key_name} key pressed, teleporting foreground client to Dog Tracy.')		
		await foreground_client.teleport(XYZ(x=7884.54150390625,y=255.63729858398438,z=750.4606323242188))

async def cantrip_window_click(foreground_client : Client, pressed_key_name: str, debug : bool = False):
	if foreground_client:
		if debug:
			logger.debug(f'{pressed_key_name} key pressed, clicking cantrip window on foreground client.')
		async with foreground_client.mouse_handler:
			if not await window_exists(foreground_client, "PlayAsPetButton"):
				await foreground_client.mouse_handler.click_window_with_name("PetSystemButton")
			await foreground_client.mouse_handler.click_window_with_name("PlayAsPetButton")
			#await foreground_client.mouse_handler.click_window_with_name("leftButton")
			await foreground_client.mouse_handler.click_window_with_name("OpenCantripsButton")
			#await foreground_client.mouse_handler.click(200,400)

async def sync_camera(client: Client, xyz: XYZ = None, yaw: float = None):
	# Teleports the freecam to a specified position, yaw, etc.
	if not xyz:
		xyz = await client.body.position()

	if not yaw:
		yaw = await client.body.yaw()

	xyz.z += 200

	camera = await client.game_client.free_camera_controller()
	await camera.write_position(xyz)
	await camera.write_yaw(yaw)


async def xyz_sync(foreground_client : Client, background_clients : list[Client], turn_after : bool = True, debug : bool = False):
	# syncs client XYZ up with the one in foreground, doesn't work across zones or realms
	if background_clients:
		if debug:
			logger.debug(f'{sync_locations_key} key pressed, syncing client locations.')
		if foreground_client:
			xyz = await foreground_client.body.position()
			yaw = await foreground_client.body.yaw()
		else:
			first_background_client = background_clients[0]
			xyz = await first_background_client.body.position()
			yaw = await first_background_client.body.yaw()

		await asyncio.gather(*[p.teleport(xyz, yaw=yaw) for p in background_clients])
		if turn_after:
			await asyncio.gather(*[p.send_key(key=Keycode.A, seconds=0.1) for p in background_clients])
			await asyncio.gather(*[p.send_key(key=Keycode.D, seconds=0.1) for p in background_clients])
		await asyncio.sleep(0.3)


async def navmap_teleport(foreground_client : wizwalker.Client, background_clients : list[Client], mass_teleport: bool = False, debug : bool = False, xyz: XYZ = None):
	# teleports foreground client or all clients using the navmap.
	# nested function that allows for the gathering of the teleports for each client
	async def client_navmap_teleport(client: Client, xyz: XYZ = None):
		if not xyz:
			xyz = await client.quest_position.position()
		await navmap_tp(client, xyz)
		# except:
		# 	# skips teleport if there's no navmap, this should just switch to auto adjusting teleport
		# 	logger.error(f'{client.title} encountered an error during navmap tp, most likely the navmap for the zone did not exist. Skipping teleport.')

	if debug:
		if mass_teleport:
			logger.debug(f'{mass_quest_teleport_key} key pressed, teleporting all clients to quests.')
		else:
			logger.debug(f'{quest_teleport_key} key pressed, teleporting client {foreground_client.title} to quest.')
	clients_to_port = []
	if foreground_client:
		clients_to_port.append(foreground_client)
	if mass_teleport:
		for b in background_clients:
			clients_to_port.append(b)
		# decide which client's quest XYZ to obey. Chooses the most common Quest XYZ across all clients, if there is none and all clients are in the same zone then it obeys the foreground client. If the zone differs, each client obeys their own quest XYZ.
		list_modes = statistics.multimode([await c.quest_position.position() for c in clients_to_port])
		zone_names = [await p.zone_name() for p in clients_to_port]
		if len(list_modes) == 1:
			xyz = list_modes[0]
		else:
			if zone_names.count(zone_names[0]) == len(zone_names):
				if foreground_client:
					xyz = await foreground_client.quest_position.position()

	# if mass teleport is off and no client is selected, this will default to p1
	if len(clients_to_port) == 0:
		if background_clients:
			clients_to_port.append(background_clients[0])

	# all clients teleport at the same time
	await asyncio.gather(*[client_navmap_teleport(p, xyz) for p in clients_to_port])


async def friend_teleport_sync(clients : list[wizwalker.Client], debug: bool):
	# uses the util for porting to friend via the friends list. Sends every client to p1. I really don't like this function, or this code, but it works and people want it so I have to have it in here sadly. Might rewrite it someday.
	if debug:
		logger.debug(f'{friend_teleport_key} key pressed, friend teleporting all clients to p1.')
	child_clients = clients[1:]
	for p in child_clients:
		async with p.mouse_handler:
			try:
				await teleport_to_friend_from_list(client=p, icon_list=1, icon_index=50)
			except Exception as e:
				logger.error(e)
				await asyncio.sleep(0)



async def kill_tool(debug: bool):
	# raises KeyboardInterrupt, forcing the tool to exit.
	if debug:
		logger.debug(f'{kill_tool_key} key pressed, killing {tool_name}.')
	gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.Close))
	await asyncio.sleep(0)
	await asyncio.sleep(0)
	raise KeyboardInterrupt


@logger.catch()
async def main():
	global tool_status
	global original_client_locations
	listener = HotkeyListener()
	foreground_client: Client = None
	background_clients = []
	await asyncio.sleep(0)
	listener.start()

	async def tool_finish():
		global minimap_instance, minimap_task, minimap_status, tool_status
    
		if not walker or len(walker.clients) == 0:
			return
    
		# Reset client speeds
		try:
			await asyncio.gather(*[p.client_object.write_speed_multiplier(client_speeds[p.process_id]) for p in walker.clients])
		except Exception:
			pass
    
		# Reset client cameras and titles
		for p in walker.clients:
			try:
				p.title = 'Wizard101'
				# Reset camera
				if await p.game_client.is_freecam():
					await p.camera_elastic()
				else:
					camera = await p.game_client.elastic_camera_controller()
					client_object = await p.body.parent_client_object()
					await camera.write_attached_client_object(client_object)
					await camera.write_check_collisions(True)
					await camera.write_distance_target(300.0)
					await camera.write_distance(300.0)
					await camera.write_min_distance(150.0)
					await camera.write_max_distance(450.0)
					await camera.write_zoom_resolution(150.0)
				await p.body.write_scale(1.0)
			except Exception:
				pass
    
		# Stop minimap
		if 'minimap_instance' in globals() and minimap_instance:
			try:
				await minimap_instance.stop()
				minimap_instance = None
				minimap_status = False
			except Exception:
				pass
    
		# Cancel minimap task
		if 'minimap_task' in globals() and minimap_task:
			try:
				minimap_task.cancel()
				minimap_task = None
			except Exception:
				pass
    
		# Clear hotkey listener
		try:
			await listener.clear()
		except Exception:
			pass
    
		# Close clients
		for p in walker.clients:
			try:
				await p.close()
			except Exception:
				pass
    
		await asyncio.sleep(0)
		tool_status = False

	async def minimap_hotkey():
		logger.debug(f"Minimap hotkey ({minimap_key}) pressed!")
		try:
			await toggle_minimap(walker.clients, debug=True)
		except Exception as e:
			logger.error(f"Error in minimap_hotkey: {e}")
			import traceback
			logger.error(traceback.format_exc())

	async def toggle_minimap_hotkey():
		if not freecam_status and not hotkeys_blocked:
			await toggle_minimap(walker.clients, debug=True)

	async def x_press_hotkey():
		await mass_key_press(foreground_client, background_clients, x_press_key, Keycode.X, duration=0.1, debug=True)

	async def cantrip_window_hotkey():
		await cantrip_window_click(foreground_client, cantrip_window_key, debug=True)
    
	async def wood_chest_hotkey():
		await wood_chest_tp(foreground_client, wood_chest_key, debug=True)
    
	async def silver_chest_hotkey():
		await silver_chest_tp(foreground_client, silver_chest_key, debug=True)
    
	async def gold_chest_hotkey():
		await gold_chest_tp(foreground_client, gold_chest_key, debug=True)
    
	async def tracy_tp_hotkey():
		await tracy_tp(foreground_client, dog_tracy_key, debug=True)
    
	async def snake_tp_hotkey():
		await entity_tp_helper(foreground_client, snake_tp_key, "snake_pu", debug=True)
    
	async def spider_tp_hotkey():
		await entity_tp_helper(foreground_client, spider_tp_key, "spider_pu", debug=True)
    
	async def crane_tp_hotkey():
		await entity_tp_helper(foreground_client, crane_tp_key, "crane_pu", debug=True)
    
	async def butterfly_tp_hotkey():
		await entity_tp_helper(foreground_client, butterfly_tp_key, "butterfly_pu", debug=True)

	async def tree_tp_hotkey():
		await entity_tp_helper(foreground_client, tree_tp_key, "tree_pu", debug=True)

	async def print_tokens():
		if foreground_client:
			entities = await foreground_client.get_base_entity_list()
			for entity in entities:
				obj_name = await entity.object_name()
				if "Coins" in obj_name:
					if obj_name == "RAID-Coins-Elements-PET_01":
						behav = await entity.search_behavior_by_name("AnimationBehavior")
						string = await behav.read_string_from_offset(576)
						if string != "00_Hidden":
							print(obj_name)
							print(hex(await behav.read_base_address()))
							entity_pos = await entity.location()
							print(f"XYZ({entity_pos.x}, {entity_pos.y}, {entity_pos.z})")
							print(f"{string}\n")
					else:
						behav = await entity.search_behavior_by_name("AnimationBehavior")
						string = await behav.read_string_from_offset(576)
						if string:
							print(obj_name)
							print(hex(await behav.read_base_address()))
							entity_pos = await entity.location()
							print(f"XYZ({entity_pos.x}, {entity_pos.y}, {entity_pos.z})")
							print(f"{string}\n")
    
	async def xyz_sync_hotkey():
		await xyz_sync(foreground_client, background_clients, turn_after=True, debug=True)


	async def navmap_teleport_hotkey():
		if not freecam_status:
			#xyz = await foreground_client.quest_position.position()
			#await WorldsCollideTP(foreground_client, xyz)
			await navmap_teleport(foreground_client, background_clients, mass_teleport=False, debug=True)


	async def mass_navmap_teleport_hotkey():
		if not freecam_status:
			#async def mass_tp_to_quest(client: Client):
			#	xyz = await client.quest_position.position()
			#	await WorldsCollideTP(client, xyz)
            
			#await asyncio.gather(*[mass_tp_to_quest(p) for p in walker.clients])
			await navmap_teleport(foreground_client, background_clients, mass_teleport=True, debug=True)


	async def toggle_speed_hotkey():
		global speed_task
		global gui_send_queue

		if not freecam_status:
			if speed_task is not None and not speed_task.cancelled():
				speed_task.cancel()
				speed_task = None
				logger.debug(f'{toggle_speed_key} key pressed, disabling speed multiplier.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('SpeedhackStatus', 'Disabled')))
				for client in walker.clients:
					await client.client_object.write_speed_multiplier(client_speeds[client.process_id])

			else:
				logger.debug(f'{toggle_speed_key} key pressed, enabling speed multiplier.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('SpeedhackStatus', 'Enabled')))
				speed_task = asyncio.create_task(try_task_coro(speed_switching, walker.clients))

	async def toggle_fov_hotkey():
		global fov_task
		global gui_send_queue

		if not freecam_status:
			if fov_task is not None and not fov_task.cancelled():
				fov_task.cancel()
				fov_task = None
				logger.debug(f"FOV Loop Disabled.")
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('FOVStatus', 'Disabled')))
				for client in walker.clients:
					elastic = await client.game_client.elastic_camera_controller()
					if elastic:
						await elastic.write_min_distance(300.0)
			else:
				logger.debug(f"FOV Loop Enabled.")
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('FOVStatus', 'Enabled')))
				fov_task = asyncio.create_task(try_task_coro(fov_check_loop, walker.clients))

	async def friend_teleport_sync_hotkey():
		if not freecam_status:
			await friend_teleport_sync(walker.clients, debug=True)


	async def kill_tool_hotkey():
		await kill_tool(debug=True)

	# Raid Shit

	# VVR

	# Hotkeys
	async def mana_chest_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Mana Chest.')
			await foreground_client.teleport(XYZ(x=9672.3232421875,y=9134.353515625,z=80.6832275390625))

	async def health_chest_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Health Chest.')
			await foreground_client.teleport(XYZ(x=9667.7001953125,y=17160.01171875,z=30.011474609375))

	async def speed_chest_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Speed Chest.')
			await foreground_client.teleport(XYZ(x=16265.126953125,y=26540.64453125,z=39.994598388671875))

	async def power_star_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Power Star.')
			await entity_tp_helper(foreground_client, "Temp", "raid_powersource", debug=True)

	async def pet_token_hotkey():
		print("check")
		if foreground_client:
			entities = await foreground_client.get_base_entity_list()
			for entity in entities:
				obj_name = await entity.object_name()
				if "Coins" in obj_name:
					if obj_name == "RAID-Coins-Wildlife-PET_01":
						behav = await entity.search_behavior_by_name("AnimationBehavior")
						string = await behav.read_string_from_offset(576)
						if string != "00_Hidden":
							print(obj_name)
							print(hex(await behav.read_base_address()))
							entity_pos = await entity.location()
							await WorldsCollideTP(foreground_client, entity_pos)
							print(f"Teleporting client to token at XYZ({entity_pos.x}, {entity_pos.y}, {entity_pos.z})")
							print(f"{string}\n")

	# Toggles

	async def vvr_drums_loop(clients: list[Client]):
		try:
			while True:
				await entity_tp_helper(foreground_client, "poopy", "lightpad", debug=True)
				await asyncio.sleep(0.1)

		except asyncio.CancelledError:
			await asyncio.sleep(0.1) # Do nothing

	async def toggle_vvr_drums_hotkey():
		global vvr_drums_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if vvr_drums_task is not None and not vvr_drums_task.cancelled():
			vvr_drums_task.cancel()
			vvr_drums_task = None

			logger.debug("Drums Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("DrumsStatus", "Disabled")))
			return

		logger.debug("Drums Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("DrumsStatus", "Enabled")))
		vvr_drums_task = asyncio.create_task(vvr_drums_loop((walker.clients)[0]))

	


	# CSR Hotkeys

	async def center_pyramid_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Center Pyramid.')
			await foreground_client.teleport(XYZ(-854.392578125, -808.9772338867188, 1832.6253662109375))

	async def voice_of_death_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Voice of Death.')
			await foreground_client.teleport(XYZ(x=-1079.9241943359375,y=-23360.068359375,z=1602.2117919921875))

	async def xibalba_elemental_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Xibalba Elemental.')
			await foreground_client.teleport(XYZ(-6406.0693359375, 22017.552734375, 1881.552490234375))

	async def west_portal_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to West.')
			await foreground_client.teleport(XYZ(-21779.3125, -6190.5888671875, 321.2557373046875))

	async def east_portal_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to East.')
			# Update Coordiantes
			await foreground_client.teleport(XYZ(-854.392578125, -808.9772338867188, 1832.6253662109375))

	async def north_pet_hotkey():
		print("check")
		if foreground_client:
			entities = await foreground_client.get_base_entity_list()
			for entity in entities:
				obj_name = await entity.object_name()
				if "Coins" in obj_name:
					# Update North Pet Token entity 
					if obj_name == "RAID-Coins-Elements-PET_01":
						behav = await entity.search_behavior_by_name("AnimationBehavior")
						string = await behav.read_string_from_offset(576)
						if string != "00_Hidden":
							print(obj_name)
							print(hex(await behav.read_base_address()))
							entity_pos = await entity.location()
							await WorldsCollideTP(foreground_client, entity_pos)
							print(f"Teleporting client to token at XYZ({entity_pos.x}, {entity_pos.y}, {entity_pos.z})")
							print(f"{string}\n")

	# Toggles
	async def cacao_pods_loop(clients: list[Client]):
		try:
			while True:
				await entity_tp_helper(foreground_client, "poopy", "Raid_AZ_Cacao", debug=True)
				await is_visible_by_path(foreground_client, ['WorldView', 'NPCRangeWin', 'imgBackground'])
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport('insert Pod Collector location')
				await asyncio.sleep(0.1)

		except asyncio.CancelledError:
			logger.debug("Cacao Pods task cancelled.")

	async def toggle_cacao_pods_hotkey():
		global pods_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if pods_task is not None and not pods_task.cancelled():
			pods_task.cancel()
			pods_task = None

			logger.debug("Cacao Pods Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("Cacao PodsStatus", "Disabled")))
			return

		logger.debug("Cacao Pods Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("Cacao PodsStatus", "Enabled")))
		pods_task = asyncio.create_task(cacao_pods_loop(foreground_client))

	async def misfortune_tears_loop(clients: list[Client]):
		try:
			while True:
				await entity_tp_helper(foreground_client, "poopy", "Raid_Jewel_Reagent", debug=True)
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport('insert tear Collector location') # Update this location
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await asyncio.sleep(0.1)

		except asyncio.CancelledError:
			logger.debug("Misfortune Tears task cancelled.")

	async def toggle_misfortune_tears_hotkey():
		global tears_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if tears_task is not None and not tears_task.cancelled():
			tears_task.cancel()
			tears_task = None

			logger.debug("Misfortune Tears Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("MF TearsStatus", "Disabled")))
			return

		logger.debug("Misfortune Tears Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("MF TearsStatus", "Enabled")))
		tears_task = asyncio.create_task(misfortune_tears_loop(foreground_client))

	async def quetzal_eggs_loop(clients: list[Client]):
		try:
			while True:
				await entity_tp_helper(foreground_client, "poopy", "Raid_AZ_QuetzalEgg", debug=True)
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport(XYZ(25435.779296875, 13407.9599609375, -329.5671081542969))
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await asyncio.sleep(0.1)
				await p.send_key(Keycode.X, 0.2)
				await asyncio.sleep(0.1)

		except asyncio.CancelledError:
			logger.debug("Quetzal Eggs task cancelled.")

	async def toggle_quetzal_eggs_hotkey():
		global eggs_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if eggs_task is not None and not eggs_task.cancelled():
			eggs_task.cancel()
			eggs_task = None

			logger.debug("Quetzal Eggs Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("Quetzal EggsStatus", "Disabled")))
			return

		logger.debug("Quetzal Eggs Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("Quetzal EggsStatus", "Enabled")))
		eggs_task = asyncio.create_task(quetzal_eggs_loop(foreground_client))

	# CRR

	async def rope_port_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to Rope.')
			await entity_tp_helper(foreground_client, "Temp", "Raid-PL-Gear", debug=True)

	async def north_east_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to NE.')
			await foreground_client.teleport(XYZ(x=15521.919,y=31776.859,z=1501.999))

	async def north_west_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to NW.')
			await foreground_client.teleport(XYZ(x=-15055.607,y=31933.933,z=1501.999))

	async def south_east_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to SE.')
			await foreground_client.teleport(XYZ(x=13955.243,y=7032.375,z=2.000))

	async def south_west_hotkey():
		if foreground_client:
			logger.debug(f'Teleporting client to SW.')
			await foreground_client.teleport(XYZ(x=-13815.256,y=8860.154,z=2.000))

	# GCR

	async def moth_amon_hotkey():
		if foreground_client:
			logger.debug(f'Collecting Moth Amon evidence.')
			await entity_tp_helper(foreground_client, "Temp", "Raid_LM_Folder_Flames", debug=True)
			await is_visible_by_path(foreground_client, ['WorldView', 'NPCRangeWin', 'imgBackground'])
			await asyncio.sleep(0.2)
			await p.send_key(Keycode.X, 0.2)
			await p.send_key(Keycode.X, 0.2)
			# Update this to cauldron location
			await foreground_client.teleport(XYZ(-2798.93701171875, 1090.9080810546875, -699.418701171875))
	
	async def lucien_hotkey():
		if foreground_client:
			logger.debug(f'Collecting Hierarch Lucien evidence.')
			await entity_tp_helper(foreground_client, "Temp", "Raid_LM_Folder_Comb", debug=True)
			await is_visible_by_path(foreground_client, ['WorldView', 'NPCRangeWin', 'imgBackground'])
			await asyncio.sleep(0.2)
			await p.send_key(Keycode.X, 0.2)
			await p.send_key(Keycode.X, 0.2)
			# Update this to cauldron location
			await foreground_client.teleport(XYZ(1144.9696044921875, 1094.712890625, -699.418701171875))

	async def morg_hotkey():
		if foreground_client:
			logger.debug(f'Collecting Morg the Merciless evidence.')
			await entity_tp_helper(foreground_client, "Temp", "Raid_LM_Folder_Mustache", debug=True)
			await asyncio.sleep(0.2)
			await p.send_key(Keycode.X, 0.2)
			await p.send_key(Keycode.X, 0.2)
			# Update this to cauldron location
			await foreground_client.teleport(XYZ(-2727.752197265625, 83.66287994384766, -699.418701171875))

	async def mime_hotkey():
		if foreground_client:
			logger.debug(f'Collecting Crime Mime evidence evidence.')
			await entity_tp_helper(foreground_client, "Temp", "Raid_LM_Folder_Props", debug=True)
			await is_visible_by_path(foreground_client, ['WorldView', 'NPCRangeWin', 'imgBackground'])
			await asyncio.sleep(0.2)
			await p.send_key(Keycode.X, 0.2)
			await p.send_key(Keycode.X, 0.2)
			# Update this to cauldron location
			await foreground_client.teleport(XYZ(1126.2415771484375, -73.92024230957031, -699.418701171875))

	# GCR Toggles

	async def toggle_wood_tokens_hotkey(token):
		global wood_tokens_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if wood_tokens_task is not None and not wood_tokens_task.cancelled():
			wood_tokens_task.cancel()
			wood_tokens_task = None

			logger.debug(f"Wood Tokens ({token}) Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("WoodTokenStatus", "Disabled")))
			return

		logger.debug(f"Wood Tokens ({token}) Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("WoodTokenStatus", "Enabled")))
		wood_tokens_task = asyncio.create_task(wood_chest_loop(foreground_client, token))

	async def wood_chest_loop(clients: list[Client], token):
		try:
			while True:
				match token:
					case 'Snake':
						entityname = "Raid_Coin_Snake_PU"
					case 'Spider':
						entityname = "Raid_Coin_Spider_PU"
					case 'Crane':
						entityname = "Raid_Coin_Crane_PU"
					case 'Butterfly':
						entityname = "Raid_Coin_Butterfly_PU"
					case 'Tree':
						entityname = "Raid_Coin_Tree_PU"
				await entity_tp_helper(foreground_client, "poopy", entityname, debug=False)
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport(XYZ(x=-2309.12158203125,y=-7644.15673828125,z=750.4605102539062))
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)

		except asyncio.CancelledError:
			logger.debug("Forensic Evidence task cancelled.")

	async def toggle_silver_tokens_hotkey(token):
		global silver_tokens_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if silver_tokens_task is not None and not silver_tokens_task.cancelled():
			silver_tokens_task.cancel()
			silver_tokens_task = None

			logger.debug(f"Silver Tokens ({token}) Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("SilverTokenStatus", "Disabled")))
			return

		logger.debug(f"Silver Tokens ({token}) Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("SilverTokenStatus", "Enabled")))
		silver_tokens_task = asyncio.create_task(silver_chest_loop(foreground_client, token))

	async def silver_chest_loop(clients: list[Client], token):
		try:
			while True:
				match token:
					case 'Snake':
						entityname = "Raid_Coin_Snake_PU"
					case 'Spider':
						entityname = "Raid_Coin_Spider_PU"
					case 'Crane':
						entityname = "Raid_Coin_Crane_PU"
					case 'Butterfly':
						entityname = "Raid_Coin_Butterfly_PU"
					case 'Tree':
						entityname = "Raid_Coin_Tree_PU"
				await entity_tp_helper(foreground_client, "poopy", entityname, debug=False)
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport(XYZ(x=-2309.12158203125,y=-7644.15673828125,z=750.4605102539062))
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)

		except asyncio.CancelledError:
			logger.debug("Forensic Evidence task cancelled.")

	async def toggle_gold_tokens_hotkey(token):
		global gold_tokens_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if gold_tokens_task is not None and not gold_tokens_task.cancelled():
			gold_tokens_task.cancel()
			gold_tokens_task = None

			logger.debug(f"Gold Tokens ({token}) Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("GoldTokenStatus", "Disabled")))
			return

		logger.debug(f"Gold Tokens ({token}) Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("GoldTokenStatus", "Enabled")))
		gold_tokens_task = asyncio.create_task(gold_chest_loop(foreground_client, token))

	async def gold_chest_loop(clients: list[Client], token):
		try:
			while True:
				match token:
					case 'Snake':
						entityname = "Raid_Coin_Snake_PU"
					case 'Spider':
						entityname = "Raid_Coin_Spider_PU"
					case 'Crane':
						entityname = "Raid_Coin_Crane_PU"
					case 'Butterfly':
						entityname = "Raid_Coin_Butterfly_PU"
					case 'Tree':
						entityname = "Raid_Coin_Tree_PU"
				await entity_tp_helper(foreground_client, "poopy", entityname, debug=False)
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport(XYZ(x=-2309.12158203125,y=-7644.15673828125,z=750.4605102539062))
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)

		except asyncio.CancelledError:
			logger.debug("Forensic Evidence task cancelled.")

	async def toggle_forensic_hotkey():
		global forensic_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if forensic_task is not None and not forensic_task.cancelled():
			forensic_task.cancel()
			forensic_task = None

			logger.debug("Forensic Evidence Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("ForensicStatus", "Disabled")))
			return

		logger.debug("Forensic Evidence Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("ForensicStatus", "Enabled")))
		forensic_task = asyncio.create_task(forensic_loop(foreground_client))

	async def forensic_loop(clients: list[Client]):
		try:
			while True:
				await entity_tp_helper(foreground_client, "poopy", "Raid_LM_Folder_B", debug=False)
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport(XYZ(7870.747, 373.754, 750.909))
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)

		except asyncio.CancelledError:
			logger.debug("Forensic Evidence task cancelled.")

	async def toggle_bombshell_hotkey():
		global bombshell_task
		global gui_send_queue

		if freecam_status:
			logger.debug("Disable freecam before running")
			return

		if bombshell_task is not None and not bombshell_task.cancelled():
			bombshell_task.cancel()
			bombshell_task = None

			logger.debug("Bombshell Evidence Disabled")
			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("BombshellStatus", "Disabled")))
			return

		logger.debug("Bombshell Evidence Enabled")
		gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,("BombshellStatus", "Enabled")))
		bombshell_task = asyncio.create_task(bombshell_loop(foreground_client))

	async def bombshell_loop(clients: list[Client]):
		try:
			while True:
				if await entity_tp_helper(foreground_client, "poopy", "Raid_LM_Folder_C", debug=False): # update this to flame entity
					await foreground_client.teleport(XYZ(7870.747, 373.754, 750.909)) # update this to somewhere in oil
					await asyncio.sleep(0.2)
				await entity_tp_helper(foreground_client, "poopy", "Raid_LM_Folder_C", debug=False)
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)
				await foreground_client.teleport(XYZ(7870.747, 373.754, 750.909))
				await asyncio.sleep(0.2)
				await p.send_key(Keycode.X, 0.2)

		except asyncio.CancelledError:
			logger.debug("Forensic Evidence task cancelled.")

	async def toggle_minimap(clients, debug: bool = False):
		global minimap_status, minimap_instance, minimap_task
		
		if minimap_status:
			# Turn off minimap
			try:
				if minimap_instance:
					await minimap_instance.stop()
					minimap_instance = None
				
				if minimap_task and not minimap_task.done():
					minimap_task.cancel()
					minimap_task = None
					
				minimap_status = False
				if debug:
					logger.debug(f'{minimap_key} key pressed, disabling minimap.')
			except Exception:
				pass
		else:
			# Turn on minimap
			try:
				if not minimap_instance:
					minimap_instance = MiniMap(clients)
					
				if not minimap_task or minimap_task.done():
					minimap_task = asyncio.create_task(minimap_instance.start())
					
				minimap_status = True
				if debug:
					logger.debug(f'{minimap_key} key pressed, enabling minimap.')
			except Exception:
				minimap_status = False
		
		return minimap_status

	async def custom_tp_hotkey(debug: bool = True):
		if deimosgui.inputs['XYZInput'] or deimosgui.inputs['YawInput']:
			await custom_tp(foreground_client, custom_tp_key, deimosgui.inputs['XYZInput'], deimosgui.inputs['YawInput'], debug=debug)
    
	async def entity_tp_hotkey(debug: bool = True):
		if deimosgui.inputs['EntityTPInput']:
			await entity_tp_helper(foreground_client, entity_tp_key, deimosgui.inputs['EntityTPInput'], debug=debug)

	async def toggle_combat_hotkey(debug: bool = True):
		global combat_task
		global gui_send_queue

		for client in walker.clients:
			client.combat_status ^= True

		if not freecam_status:
			if combat_task is not None and not combat_task.cancelled():
				combat_task.cancel()
				combat_task = None
				if debug:
					logger.debug(f'{toggle_auto_combat_key} key pressed, disabling auto combat.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('CombatStatus', 'Disabled')))

			else:
				if debug:
					logger.debug(f'{toggle_auto_combat_key} key pressed, enabling auto combat.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('CombatStatus', 'Enabled')))
				combat_task = asyncio.create_task(try_task_coro(combat_loop, walker.clients, True))


	async def toggle_dialogue_hotkey(side_quests: bool = False):
		global dialogue_task
		global gui_send_queue
		global side_quest_status

		if not freecam_status:
			if dialogue_task is not None and not dialogue_task.cancelled():
				side_quest_status = False
				dialogue_task.cancel()
				dialogue_task = None
				logger.debug(f'{toggle_auto_dialogue_key} key pressed, disabling auto dialogue.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('DialogueStatus', 'Disabled')))

			else:
				side_quest_log_str = ""
				side_quest_status = side_quests
				if side_quest_status:
					side_quest_log_str += " and auto side quests functionality"
				logger.debug(f'{toggle_auto_dialogue_key} key pressed, enabling auto dialogue{side_quest_log_str}.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('DialogueStatus', 'Enabled')))
				dialogue_task = asyncio.create_task(try_task_coro(dialogue_loop, walker.clients, True))


	async def toggle_dialogue_side_quests_hotkey():
		await toggle_dialogue_hotkey(True)



	async def toggle_sigil_hotkey():
		global sigil_task
		global questing_status
		global questing_task
		global gui_send_queue

		if not freecam_status:
			for p in walker.clients:
				p.sigil_status ^= True
				if p.sigil_status:
					p.questing_status = False
					p.auto_pet_status = False

			if sigil_task is not None and not sigil_task.cancelled():
				sigil_task.cancel()
				sigil_task = None
				logger.debug(f'{toggle_auto_sigil_key} key pressed, disabling auto sigil.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('SigilStatus', 'Disabled')))

			else:
				logger.debug(f'{toggle_auto_sigil_key} key pressed, enabling auto sigil.')
				if questing_task is not None and not questing_task.cancelled():
					logger.debug(f'{toggle_auto_questing_key} key pressed, disabling auto questing.')
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('QuestingStatus', 'Disabled')))
					questing_task.cancel()
					for p in walker.clients:
						p.questing_status = False
					questing_status = False
					questing_task = None

				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('SigilStatus', 'Enabled')))
				sigil_task = asyncio.create_task(try_task_coro(sigil_loop, walker.clients, True))



	async def toggle_freecam_hotkey(debug: bool = True):
		global freecam_status
		if foreground_client:
			if await is_free(foreground_client):
				if await foreground_client.game_client.is_freecam():
					if debug:
						logger.debug(f'{toggle_freecam_key} key pressed, disabling freecam.')
					await foreground_client.camera_elastic()
					freecam_status = False

				else:
					if debug:
						logger.debug(f'{toggle_freecam_key} key pressed, enabling freecam.')

					freecam_status = True
					await sync_camera(foreground_client)
					await foreground_client.camera_freecam()


	async def tp_to_freecam_hotkey():
		if foreground_client:
			logger.debug(f'Shift + {toggle_freecam_key} key pressed, teleporting foreground client to freecam position.')
			if await foreground_client.game_client.is_freecam():
				camera = await foreground_client.game_client.free_camera_controller()
				camera_pos = await camera.position()
				await toggle_freecam_hotkey(False)
				#await WorldsCollideTP(foreground_client, camera_pos, static_body_radius=0.0)
				await foreground_client.teleport(camera_pos, wait_on_inuse=True, purge_on_after_unuser_fixer=True)


	async def toggle_questing_hotkey():
		global sigil_task
		global questing_task
		global questing_status
		global sigil_status
		global gui_send_queue

		if not freecam_status:
			questing_status ^= True
			for p in walker.clients:
				p.questing_status ^= True

			if questing_task is not None and not questing_task.cancelled():
				logger.debug(f'{toggle_auto_questing_key} key pressed, disabling auto questing.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('QuestingStatus', 'Disabled')))
				questing_task.cancel()
				questing_task = None

			else:
				for p in walker.clients:
					p.sigil_status = False

				if sigil_task is not None and not sigil_task.cancelled():
					logger.debug(f'{toggle_auto_sigil_key} key pressed, disabling auto sigil.')
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('SigilStatus', 'Disabled')))
					sigil_task.cancel()
					sigil_task = None
					for p in walker.clients:
						p.sigil_status = False
					sigil_status = False

				logger.debug(f'{toggle_auto_questing_key} key pressed, enabling auto questing.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('QuestingStatus', 'Enabled')))
				questing_task = asyncio.create_task(try_task_coro(questing_loop, walker.clients, True))


	async def toggle_auto_pet_hotkey():
		global auto_pet_task
		global auto_pet_status

		if not freecam_status:
			auto_pet_status ^= True
			for p in walker.clients:
				p.auto_pet_status ^= True

			if auto_pet_task is not None and not auto_pet_task.cancelled():
				logger.debug(f'Disabling auto pet.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Auto PetStatus', 'Disabled')))
				auto_pet_task.cancel()
				auto_pet_task = None

			else:
				logger.debug(f'Enabling auto pet.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Auto PetStatus', 'Enabled')))
				auto_pet_task = asyncio.create_task(try_task_coro(auto_pet_loop, walker.clients, True))


	async def toggle_auto_potion_hotkey():
		global auto_potion_status
		
		if not freecam_status:
			auto_potion_status ^= True
			
			if auto_potion_status:
				logger.debug(f'Enabling auto potion.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Auto PotionStatus', 'Enabled')))
			else:
				logger.debug(f'Disabling auto potion.')
				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Auto PotionStatus', 'Disabled')))


	# async def toggle_side_quests():
	# 	global side_quest_status

	# 	if side_quest_status is not None:
	# 		if side_quest_status:
	# 			logger.debug('Disabling side quests.')
	# 			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Side QuestsStatus', 'Disabled')))

	# 		else:
	# 			logger.debug('Enabling side quests.')
	# 			gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Side QuestsStatus', 'Enabled')))

	# 		side_quest_status = not side_quest_status
	# 	else:
	# 		logger.debug('This config variable has not yet been initialized, enabling the option now.')
	# 		side_quest_status = True


	async def enable_hotkeys(exclude_freecam: bool = False, debug: bool = False):
		# adds every hotkey
		global hotkey_status
		if not hotkey_status:
			if debug:
				logger.debug('Client selected, starting hotkey listener.')
			await listener.add_hotkey(Keycode[minimap_key], minimap_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[x_press_key], x_press_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[cantrip_window_key], cantrip_window_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[wood_chest_key], wood_chest_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[silver_chest_key], silver_chest_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[gold_chest_key], gold_chest_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[dog_tracy_key], tracy_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[entity_tp_key], entity_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[snake_tp_key], snake_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[spider_tp_key], spider_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[crane_tp_key], crane_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[butterfly_tp_key], butterfly_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[tree_tp_key], tree_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[custom_tp_key], custom_tp_hotkey, modifiers=ModifierKeys.NOREPEAT)
			# await listener.add_hotkey(Keycode[space_press_key], space_press_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[sync_locations_key], xyz_sync_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[quest_teleport_key], navmap_teleport_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[mass_quest_teleport_key], mass_navmap_teleport_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[toggle_speed_key], toggle_speed_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[friend_teleport_key], friend_teleport_sync_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[toggle_auto_combat_key], toggle_combat_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[toggle_auto_dialogue_key], toggle_dialogue_hotkey, modifiers=ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[toggle_auto_dialogue_key], toggle_dialogue_side_quests_hotkey, modifiers=ModifierKeys.SHIFT | ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[toggle_auto_sigil_key], toggle_sigil_hotkey, modifiers=ModifierKeys.NOREPEAT)
			if not exclude_freecam:
				await listener.add_hotkey(Keycode[toggle_freecam_key], toggle_freecam_hotkey, modifiers=ModifierKeys.NOREPEAT)
				await listener.add_hotkey(Keycode[toggle_freecam_key], tp_to_freecam_hotkey, modifiers=ModifierKeys.SHIFT | ModifierKeys.NOREPEAT)
			await listener.add_hotkey(Keycode[toggle_auto_questing_key], toggle_questing_hotkey, modifiers=ModifierKeys.NOREPEAT)
			hotkey_status = True


	async def disable_hotkeys(exclude_freecam: bool = False, debug: bool = False, exclude_kill: bool = True):
		# removes every hotkey
		global hotkey_status
		if hotkey_status:
			if debug:
				logger.debug('Client not selected, stopping hotkey listener.')
			await listener.remove_hotkey(Keycode[minimap_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[x_press_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[cantrip_window_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[wood_chest_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[silver_chest_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[gold_chest_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[dog_tracy_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[entity_tp_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[snake_tp_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[spider_tp_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[crane_tp_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[butterfly_tp_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[tree_tp_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[custom_tp_key], modifiers=ModifierKeys.NOREPEAT)
			# await listener.remove_hotkey(Keycode[space_press_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[sync_locations_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[quest_teleport_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[mass_quest_teleport_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[toggle_speed_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[friend_teleport_key], modifiers=ModifierKeys.NOREPEAT)
			if not exclude_kill:
				await listener.remove_hotkey(Keycode[kill_tool_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[toggle_auto_combat_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[toggle_auto_dialogue_key], modifiers=ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[toggle_auto_dialogue_key], modifiers=ModifierKeys.SHIFT | ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[toggle_auto_sigil_key], modifiers=ModifierKeys.NOREPEAT)
			if not exclude_freecam:
				await listener.remove_hotkey(Keycode[toggle_freecam_key], modifiers=ModifierKeys.NOREPEAT)
				await listener.remove_hotkey(Keycode[toggle_freecam_key], modifiers=ModifierKeys.SHIFT | ModifierKeys.NOREPEAT)
			await listener.remove_hotkey(Keycode[toggle_auto_questing_key], modifiers=ModifierKeys.NOREPEAT)
			hotkey_status = False

	def get_foreground_client():
		foreground = [c for c in walker.clients if c.is_foreground]
		if len(foreground) > 0:
			return foreground[0]
		if not foreground_client:
			return walker.clients[0]
		return foreground_client

	def get_background_clients():
		return [c for c in walker.clients if not c.is_foreground]

	async def foreground_client_switching():
		await asyncio.sleep(2)
		# enable hotkeys if a client is selected, disable if none are
		while True:
			await asyncio.sleep(0.1)
			foreground_client_list = [c for c in walker.clients if c.is_foreground]
			if foreground_client_list:
				await enable_hotkeys(debug = True)
			else:
				await disable_hotkeys(debug = True)


	async def assign_foreground_clients():
		# assigns the foreground client and a list of background clients
		nonlocal foreground_client
		nonlocal background_clients
		while True:
			foreground_client = get_foreground_client()
			background_clients = get_background_clients()
			await asyncio.sleep(0.1)

	async def hail_limbow():
		async def limbow_hail(client: Client):
			while True:
				txt_windows = await client.root_window.get_windows_with_name("txtTestRealmText")
				if len(txt_windows) > 0:
					txt_window = txt_windows[0]
					curr_flags = await txt_window.flags() - WindowFlags.disabled
					if curr_flags >= 0:
						await txt_window.write_maybe_text("All Hail Limbow")
						await txt_window.write_flags(WindowFlags(curr_flags + WindowFlags.visible))
				await asyncio.sleep(0.1)
		await asyncio.gather(*[limbow_hail(p) for p in walker.clients])
    
	async def speed_switching():
		# handles updating the speed multiplier if a zone or realm change happens
		modified_speed = (int(speed_multiplier) - 1) * 100
		while True:
			await asyncio.sleep(0.1)
			# if speed multiplier is enabled, rewrite the multiplier value if the speed changes. If speed mult is disabled, rewrite the original untouched speed multiplier only if it equals the multiplier speed
			if not freecam_status:
				await asyncio.sleep(0.2)
				for c in walker.clients:
					if await c.client_object.speed_multiplier() != modified_speed:
						await c.client_object.write_speed_multiplier(modified_speed)


	async def is_client_in_combat_loop():
		async def async_in_combat(client: Client):
			# battle = Fighter(client)
			# while True:
			# 	if await battle.is_fighting():
			# 		client.in_combat = True
			# 	else:
			# 		client.in_combat = False
			# 	await asyncio.sleep(0.1)
			while True:
				# print(await client.game_client.is_freecam())
				if not freecam_status:
					client.in_combat = await client.in_battle()
				await asyncio.sleep(0.1)

		await asyncio.gather(*[async_in_combat(p) for p in walker.clients])

	async def fish_loop():
		if foreground_client:
			await run_fish(foreground_client)
	
	async def fov_check_loop():
		global fov_value
		async def async_fov_check(client: Client):
			while True:
				if not freecam_status:
					if not await client.in_battle():
						elastic = await client.game_client.elastic_camera_controller()
						if elastic:
							if await elastic.min_distance() != fov_value:
								await elastic.write_min_distance(fov_value)
				await asyncio.sleep(0.5)
		await asyncio.gather(*[async_fov_check(p) for p in walker.clients])

	async def combat_loop():
		logger.catch()
		# waits for combat for every client and handles them seperately.
		async def async_combat(client: Client):
			while True:
				await asyncio.sleep(1)
				if not freecam_status:
					while not await client.in_battle():
						await asyncio.sleep(1)

					if await client.in_battle():
						logger.debug(f'Client {client.title} in combat, handling combat.')

						#CONFIG COMBAT
						global battle
						battle = SprintyCombat(client, StrCombatConfigProvider(client.combat_config), True)
						await battle.wait_for_combat()

		await asyncio.gather(*[async_combat(p) for p in walker.clients])

	async def dialogue_loop():
		# auto advances dialogue for every client, individually and concurrently
		async def async_dialogue(client: Client):
			while True:
				if not freecam_status:
					if await is_visible_by_path(client, advance_dialog_path):
						if await is_visible_by_path(client, decline_quest_path) and not side_quest_status:
							await client.send_key(key=Keycode.ESC)
							await asyncio.sleep(0.1)
							await client.send_key(key=Keycode.ESC)
						else:
							await client.send_key(key=Keycode.SPACEBAR)
				await asyncio.sleep(0.1)

		await asyncio.gather(*[async_dialogue(p) for p in walker.clients])

	# logger.catch()
	async def questing_loop():
		# Auto questing on a per client basis.
		async def async_questing(client: Client):
			client.character_level = await client.stats.reference_level()

			while True:
				await asyncio.sleep(1)

				if client in walker.clients and questing_status:
					if questing_leader_pid is not None and len(walker.clients) > 1:
						if client.process_id == questing_leader_pid:
							# if follow leader is off, quest on all clients, passing through only the leader
							logger.debug(f'Client {client.title} - Handling questing for all clients.')
							questing = Quester(client, walker.clients, questing_leader_pid)
							await questing.auto_quest_leader(questing_friend_tp, gear_switching_in_solo_zones, hitter_client, ignore_pet_level_up, only_play_dance_game)
					else:
						# if follow leader is off, quest on all clients, passing through only the leader
						logger.debug(f'Client {client.title} - Handling questing.')
						questing = Quester(client, walker.clients, None)
						await questing.auto_quest(ignore_pet_level_up, only_play_dance_game)

		await asyncio.gather(*[async_questing(p) for p in walker.clients])

	async def anti_afk_questing_loop():
		async def async_afk_questing(client: Client):
			while True:
				global questing_task

				await asyncio.sleep(0.1)
				if not freecam_status:
					client_xyz = await client.body.position()
					await asyncio.sleep(120)
					client_xyz_2 = await client.body.position()
					distance_moved = calc_Distance(client_xyz, client_xyz_2)
					if distance_moved < 5.0 and not await client.in_battle() and not client.feeding_pet_status and not client.entity_detect_combat_status:

						# During questing, one or more clients may be waiting outside while the others are completing a solo zone quest - we do not want to restart in these cases
						client_in_solo_zone = False
						for p in walker.clients:
							if p.in_solo_zone:
								client_in_solo_zone = True

						# restart questing
						if questing_task is not None and not questing_task.cancelled() and not client_in_solo_zone:
								logger.debug(f'Questing appears to have halted - restarting.')
								questing_task.cancel()
								questing_task = None
								await asyncio.sleep(1.0)

								if questing_task is None:
									questing_task = asyncio.create_task(try_task_coro(questing_loop, walker.clients, True))


		await asyncio.gather(*[async_afk_questing(p) for p in walker.clients])

	# logger.catch()
	async def auto_pet_loop():
		# Auto questing on a per client basis.
		async def async_auto_pet(client: Client):
			while True:
				await asyncio.sleep(1)

				if client in walker.clients and auto_pet_status:
					await nomnom(client, ignore_pet_level_up=ignore_pet_level_up, only_play_dance_game=only_play_dance_game)


		await asyncio.gather(*[async_auto_pet(p) for p in walker.clients])

	async def nearest_duel_circle_distance_and_xyz(sprinter: SprintyClient):
		min_distance = None
		circle_xyz = None

		try:
			entities = await sprinter.get_base_entity_list()
		except ValueError:
			return None, None

		for entity in entities:
			try:
				entity_name = await entity.object_name()
			except wizwalker.MemoryReadError:
				entity_name = ''

			if entity_name == 'Duel Circle':
				entity_pos = await entity.location()
				distance = calc_Distance(entity_pos, await sprinter.client.body.position())

				if min_distance is None:
					min_distance = distance
					circle_xyz = entity_pos
				elif distance < min_distance:
					min_distance = distance
					circle_xyz = entity_pos
				# print('distance to duel circle: ', distance)

		return min_distance, circle_xyz

	async def is_duel_circle_joinable(p: Client):
		sprinter = SprintyClient(p)
		await asyncio.sleep(7)

		distance, duel_circle_xyz = await nearest_duel_circle_distance_and_xyz(sprinter)
		# if after 7 seconds we are not in a battle position, we either teleported while invincible or teleported to a non-joinable fight
		if distance is not None:
			if not (590 < distance < 610):
				logger.debug('Bad teleport.  Returning ' + p.title + ' to safe location.')
				if p.original_location_before_combat is not None:
					await p.teleport(p.original_location_before_combat)
					p.original_location_before_combat = None
				else:
					position = await p.body.position()
					await p.teleport(XYZ(position.x, position.y, position.z - 350))

				p.entity_detect_combat_status = False

				return False

			return True
		else:
			return False

	async def entity_detect_combat_loop():
		async def detect_combat(p: Client):
			global original_client_locations
			sprinter = SprintyClient(p)

			other_clients = []
			for c in walker.clients:
				if c != p:
					other_clients.append(c)

			safe_distance = 620
			while True:
				await asyncio.sleep(.5)

				if p.questing_status:
					if p.just_entered_combat is not None:
						# 5 seconds have passed since the client entered combat
						if time.time() >= (p.just_entered_combat + 7):
							# we are actually in combat
							if await p.in_battle():
								p.just_entered_combat = None
							# if we aren't in combat after 7 seconds, something went wrong - duel circle is likely not joinable
							else:
								# client_being_helped is None when you are the client that is being helped
								if p.client_being_helped is not None:
									is_circle_joinable = await is_duel_circle_joinable(p)
									# check_duel_circle_joinable = [asyncio.create_task(is_duel_circle_joinable(helper)) for helper in p.helper_clients]
									# done, pending = await asyncio.wait(check_duel_circle_joinable)
									#
									# is_circle_joinable = True
									# for d in done:
									# 	is_circle_joinable = d.result()


									if not is_circle_joinable:
										p.client_being_helped.duel_circle_joinable = False
										logger.debug('Client ' + p.client_being_helped.title + ' - ' + 'Duel circle not joinable - teleports halted.')
										p.client_being_helped = None

					if p.just_entered_combat is None:
						if True:
							distance, duel_circle_xyz = await nearest_duel_circle_distance_and_xyz(sprinter)

							if distance is None:
								if p.entity_detect_combat_status:
									p.just_left_combat = True
								else:
									p.entity_detect_combat_status = False

							# When fully in combat (once running animation occurs and selection phase begins) clients in any battle order are ~600 away from the center of the duel circle
							# extra leeway on this allows clients to teleport more quickly to ensure that they arrive before the selection phase even starts
							elif distance < safe_distance:
									p.entity_detect_combat_status = True

									# original_client_locations = dict()
									all_fighting_clients = [p]

									# don't teleport clients to duel circles that are closed off, and don't teleport clients if they are in separate instances
									if p.duel_circle_joinable and not p.in_solo_zone:
										p.helper_clients = []
										none_in_solo_zone = True
										all_already_in_battle = False
										for c in other_clients:
											client_is_hitter_client = False
											if hitter_client is not None:
												if hitter_client in c.title:
													client_is_hitter_client = True
													all_already_in_battle = True
													for cl in walker.clients:
														if hitter_client not in cl.title:
															if not cl.entity_detect_combat_status:
																all_already_in_battle = False

															if cl.in_solo_zone:
																none_in_solo_zone = False

											# if we are the hitter client, we've confirmed that we are the last to teleport, and no one is in a solo zone, or we are not the hitter client, then we can teleport
											if (client_is_hitter_client and all_already_in_battle and none_in_solo_zone) or not client_is_hitter_client:
												if await is_free(c) and not c.entity_detect_combat_status and not c.invincible_combat_timer and c.just_entered_combat is None:
													# player_distance = calc_Distance(await c.body.position(), await p.body.position())
													# print('player distance between [', c.title, '] and [', p.title, '] is: ', player_distance)

													if hitter_client is not None:
														if all_already_in_battle and hitter_client in c.title:
															# slight delay to ensure hitter makes it to the circle last
															await asyncio.sleep(1.0)

													if await c.zone_name() == await p.zone_name():
														if not c.entity_detect_combat_status:
															c.entity_detect_combat_status = True
															c.just_entered_combat = time.time()
															c.original_location_before_combat = await c.body.position()
															original_client_locations.update({c.process_id: await c.body.position()})
															c.client_being_helped = p
															if c not in p.helper_clients:
																p.helper_clients.append(c)
																all_fighting_clients.append(c)

															logger.debug('Combat detected from client ' + p.title + ' - teleporting client ' + c.title)
															try:
																await c.teleport(duel_circle_xyz)
																# just_entered_combat = True
															except ValueError:
																c.just_entered_combat = None
																pass
									helper_clients = []


							else:
								if p.entity_detect_combat_status:
									p.just_left_combat = True
								else:
									p.entity_detect_combat_status = False

							if p.just_left_combat and await is_free(p):
								p.just_left_combat = False
								# collect wisps, up to a certain number
								await collect_wisps_with_limit(p, limit=2)
								await asyncio.sleep(.3)

								# return helper clients to their previous safe location
								if p.process_id in original_client_locations:
									logger.debug('Client ' + p.title + ' - ' + 'Returning to safe location. ')

									try:
										await p.teleport(original_client_locations.get(p.process_id))
										original_client_locations.pop(p.process_id)
									except ValueError:
										print(traceback.print_exc())
										p.original_location_before_combat = None



								# just_left_combat = False

								# Mark wizard as invincible, as clients can get stuck standing in the middle of another client's battle circle due to teleporting while invincibile
								logger.debug('Client ' + p.title + ' - ' + 'Battle teleports off while invulnerable')
								p.invincible_combat_timer = True
								p.entity_detect_combat_status = False
								p.duel_circle_joinable = True
								p.client_being_helped = None
								# p.just_entered_combat = None

								# Timer seems to be about 6.5 seconds to become draggable again
								await asyncio.sleep(6.5)
								logger.debug('Client ' + p.title + ' - ' + 'Battle teleports re-enabled')
								p.invincible_combat_timer = False

		await asyncio.gather(*[detect_combat(p) for p in walker.clients])


	async def sigil_loop():
		# Auto sigil on a per client basis.
		async def async_sigil(client: Client):
			while True:
				await asyncio.sleep(1)
				if client in walker.clients and client.sigil_status and not freecam_status:
					sigil = Sigil(client, walker.clients, sigil_leader_pid)
					await sigil.wait_for_sigil()

		await asyncio.gather(*[async_sigil(p) for p in walker.clients])


	async def anti_afk_loop():
		# anti AFK implementation on a per client basis.
		if not anti_afk_status:
			return

		async def async_anti_afk(client: Client):
			# await client.root_window.debug_print_ui_tree()
			# print(await client.body.position())
			while True:
				global questing_task

				await asyncio.sleep(0.1)
				if not freecam_status and await client.zone_name() and not await client.is_loading():
					client_xyz = await client.body.position()
					await asyncio.sleep(350)
					if not freecam_status and await client.zone_name() and not await client.is_loading():
						client_xyz_2 = await client.body.position()
						distance_moved = calc_Distance(client_xyz, client_xyz_2)
						if distance_moved < 5.0 and not await client.in_battle() and not client.feeding_pet_status and not client.entity_detect_combat_status and not sigil_status:
							logger.debug(f"Client {client.title} - AFK client detected, moving slightly.")
							await client.send_key(key=Keycode.A)
							await asyncio.sleep(0.1)
							await client.send_key(key=Keycode.D)

		await asyncio.gather(*[async_anti_afk(p) for p in walker.clients])


	async def handle_gui():

		async def handle_coord_error(error: wizwalker.errors.MemoryReadError):
			if await is_visible_by_path(foreground_client, play_button_path):
				return
			if await foreground_client.is_loading():
				return
			if await foreground_client.zone_name() is None:
				return
			raise wizwalker.errors.MemoryReadError(f"{error} (Occurred in zone: {current_zone})") from error

		if show_gui:
			global gui_send_queue
			global bot_task
			global flythrough_task
			gui_send_queue = queue.Queue()
			recv_queue = queue.Queue()

			# swap queue order because sending from window means receiving from here
			gui_thread = threading.Thread(
				target=deimosgui.manage_gui,
				args=(recv_queue, gui_send_queue, gui_theme, gui_text_color, gui_button_color, tool_name, tool_version, gui_on_top, gui_langcode)
			)
			gui_thread.daemon = True
			gui_thread.start()

			enemy_stats = []

			while True:
				if foreground_client:
					current_zone = await foreground_client.zone_name()
					#try:
					if current_zone and not await foreground_client.is_loading(): #and not await is_visible_by_path(foreground_client, play_button_path):
						if parent := await foreground_client.client_object.parent():
							if await parent.object_name() == "Player Object":
								children = await parent.children()
								for pet_object in children:
									current_pos = await pet_object.location()
									current_rotation = await pet_object.orientation()
							else:
								current_pos = await foreground_client.body.position()
								current_rotation = await foreground_client.body.orientation()
					else:
						current_pos = XYZ(0,0,0)
						current_rotation = Orient(0,0,0)
					#except wizwalker.errors.MemoryReadError as e:
					#	await handle_coord_error(e)
						
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Title', f'Client: {foreground_client.title}')))
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Zone', f'Zone: {current_zone}')))
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('x', f'X: {current_pos.x}')))
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('y', f'Y: {current_pos.y}')))
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('z', f'Z: {current_pos.z}')))
					gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Yaw', f'Yaw: {current_rotation.yaw}')))

				# Stuff sent by the window
				try:
				# Eat as much as the queue gives us. We will be freed by exception
					while True:
						com = recv_queue.get_nowait()
						match com.com_type:
							case deimosgui.GUICommandType.Close:
								await kill_tool_hotkey()

							case deimosgui.GUICommandType.ToggleOption:
								match com.data:
									case GUIKeys.toggle_speedhack:
										await toggle_speed_hotkey()

									case GUIKeys.toggle_combat:
										await toggle_combat_hotkey()

									case GUIKeys.toggle_dialogue:
										await toggle_dialogue_hotkey()

									case GUIKeys.toggle_sigil:
										await toggle_sigil_hotkey()

									case GUIKeys.toggle_questing:
										await toggle_questing_hotkey()

									case GUIKeys.toggle_auto_pet:
										await toggle_auto_pet_hotkey()

									case GUIKeys.toggle_auto_potion:
										await toggle_auto_potion_hotkey()

									case GUIKeys.toggle_freecam:
										await toggle_freecam_hotkey()

									case GUIKeys.CSRDrums:
										await toggle_vvr_drums_hotkey()

									case GUIKeys.CacaoPods:
										await toggle_cacao_pods_hotkey()

									case GUIKeys.MisfortuneTears:
										await toggle_misfortune_tears_hotkey()

									case GUIKeys.QuetzalEggs:
										await toggle_quetzal_eggs_hotkey()

									case GUIKeys.DaemonBalls:
										await toggle_cacao_pods_hotkey()

									case GUIKeys.CabalistBalls:
										await toggle_cacao_pods_hotkey()

									case GUIKeys.AutoWoodTokens:
										gui_send_queue.put(deimosgui.GUICommandType.AutoWoodTokens)

									case GUIKeys.AutoSilverTokens:
										gui_send_queue.put(deimosgui.GUICommandType.AutoSilverTokens)

									case GUIKeys.AutoGoldTokens:
										gui_send_queue.put(deimosgui.GUICommandType.AutoGoldTokens)

									case GUIKeys.AutoTracyFoldersForensic:
										await toggle_forensic_hotkey()

									case GUIKeys.AutoTracyFoldersBombshell:
										await toggle_bombshell_hotkey()


									# case 'Side Quests':
									# 	await toggle_side_quests()

									case GUIKeys.toggle_camera_collision:
										if foreground_client:
											camera: ElasticCameraController = await foreground_client.game_client.elastic_camera_controller()

											collision_status = await camera.check_collisions()
											collision_status ^= True

											logger.debug(f'Camera Collisions {bool_to_string(collision_status)}')
											await camera.write_check_collisions(collision_status)
									case _:
										logger.debug(f'Unknown window toggle: {com.data}')

							case deimosgui.GUICommandType.Copy:
								match com.data:
									case GUIKeys.copy_zone:
										logger.debug('Copied Zone')
										pyperclip.copy(current_zone)

									case GUIKeys.copy_position:
										logger.debug('Copied Position')
										pyperclip.copy(f'XYZ({current_pos.x}, {current_pos.y}, {current_pos.z})')

									case GUIKeys.copy_rotation:
										logger.debug('Copied Rotation')
										pyperclip.copy(f'Orient({current_rotation.pitch}, {current_rotation.roll}, {current_rotation.yaw})')

									case GUIKeys.copy_entity_list:
										if foreground_client:
											logger.debug('Copied Entity List')
											sprinter = SprintyClient(foreground_client)
											entities = await sprinter.get_base_entity_list()
											entities_info = ''
											for entity in entities:
												entity_pos = await entity.location()
												entity_name = await entity.object_name()
												entities_info += f'{entity_name}, XYZ({entity_pos.x}, {entity_pos.y}, {entity_pos.z})\n\n'
											pyperclip.copy(entities_info)

											if entities_info:
												logger.success("Available Nearby Entities:")
												gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.ShowEntityListPopup, (entities_info)))
											else:
												logger.error("Failed to load Entity list. Please try again.")

									case GUIKeys.copy_camera_position:
										if foreground_client:
											camera = await foreground_client.game_client.selected_camera_controller()
											camera_pos = await camera.position()

											logger.debug('Copied Selected Camera Position')
											pyperclip.copy(f'XYZ({camera_pos.x}, {camera_pos.y}, {camera_pos.z})')

									case GUIKeys.copy_camera_rotation:
										if foreground_client:
											camera = await foreground_client.game_client.selected_camera_controller()
											camera_pitch, camera_roll, camera_yaw = await camera.orientation()
											logger.debug('Copied Camera Rotations')
											pyperclip.copy(f'Orient({camera_pitch}, {camera_roll}, {camera_pitch})')

									case GUIKeys.copy_ui_tree:
										if foreground_client:
											foreground: Client = foreground_client
											ui_tree = ''

											async def get_ui_tree(window: Window, depth: int = 0, depth_symbol: str = '-', seperator: str = '\n'):
												nonlocal ui_tree
												ui_tree += f"{depth_symbol * depth} [{await window.name()}] {await window.maybe_read_type_name()}{seperator}"

												for child in await utils.wait_for_non_error(window.children):
													await get_ui_tree(child, depth + 1)

											await get_ui_tree(foreground.root_window)

											logger.debug(f'Copied UI Tree for client {foreground.title}')
											pyperclip.copy(ui_tree)
											with open('ui_tree.txt', 'w') as f:
												f.write(ui_tree)

											if ui_tree:
												logger.success("Available UI Paths:")
												gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.ShowUITreePopup, (ui_tree)))
											else:
												logger.error("Failed to load UI tree. Please try again.")

									case GUIKeys.copy_stats:
										if enemy_stats:
											logger.debug('Copied Stats')
											pyperclip.copy('\n'.join(enemy_stats))
										else:
											logger.info('No stats are loaded. Select an enemy index corresponding to its position on the duel circle, then click the copy button.')

									case _:
										logger.debug(f'Unknown copy value: {com.data}')

							case deimosgui.GUICommandType.Teleport:
								match com.data:
									case GUIKeys.hotkey_quest_tp:
										await navmap_teleport_hotkey()
									case GUIKeys.mass_hotkey_mass_tp:
										await mass_navmap_teleport_hotkey()
									case GUIKeys.hotkey_freecam_tp:
										await tp_to_freecam_hotkey()
									case _:
										logger.debug(f'Unknown teleport type: {com.data}')

							case deimosgui.GUICommandType.CustomTeleport:
								if foreground_client:
									xyz_lst = parse_xyz(com.data['XYZ'], [current_pos.x, current_pos.y, current_pos.z])
									x_input = xyz_lst[0]
									y_input = xyz_lst[1]
									z_input = xyz_lst[2]
									yaw_input = param_input(com.data['Yaw'], current_rotation.yaw)

									custom_xyz = XYZ(x=x_input, y=y_input, z=z_input)
									logger.debug(f'Teleporting client {foreground_client.title} to {custom_xyz}, yaw= {yaw_input}')
									await foreground_client.teleport(custom_xyz)
									await foreground_client.body.write_yaw(yaw_input)

							case deimosgui.GUICommandType.EntityTeleport:
								# Teleports to closest entity with vague name, using WizSprinter
								if foreground_client:
									sprinter = SprintyClient(foreground_client)
									entities = await sprinter.get_base_entities_with_vague_name(com.data)
									if entities:
										entity = await sprinter.find_closest_of_entities(entities)
										entity_pos: XYZ = await entity.location()
										await WorldsCollideTP(foreground_client, entity_pos)
										#await foreground_client.teleport(entity_pos)

							case deimosgui.GUICommandType.SelectEnemy:
								if foreground_client and await foreground_client.in_battle():
									caster_index = com.data

									hp_string = await every_hp(foreground_client)
									enemy_stats, names_list, caster_i = await total_stats(foreground_client, caster_index)
									gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('stat_viewer', '\n'.join(enemy_stats))))
									gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('every_hp', hp_string)))
									gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindowValues, ('IndexInput', names_list)))
									gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('IndexInput', names_list[caster_i])))

								else:
									logger.info('Last selected client is not currently in combat. You must be in combat to use the stat viewer.')

							case deimosgui.GUICommandType.XYZSync:
								await xyz_sync_hotkey()

							case deimosgui.GUICommandType.XPress:
								await x_press_hotkey()

							case deimosgui.GUICommandType.AnchorCam:
								if foreground_client:
									if freecam_status:
										await toggle_freecam_hotkey()

									camera = await foreground_client.game_client.elastic_camera_controller()

									sprinter = SprintyClient(foreground_client)
									entities = await sprinter.get_base_entities_with_vague_name(com.data)
									entity_pos: XYZ = None
									if entities:
										entity = await sprinter.find_closest_of_entities(entities)
										entity_name = await entity.object_name()
										logger.debug(f'Anchoring camera to entity {entity_name}')
										await camera.write_attached_client_object(entity)

							# case deimosgui.GUICommandType.SetPetWorld:
							# 	if (com.data[1] is None):
							# 		logger.debug('Invalid pet world selected!')
							# 	else:
							# 		logger.debug(f'Setting Auto Pet World to {com.data[1]}')
							# 		assign_pet_level(com.data[1])

							case deimosgui.GUICommandType.SetCamToEntity:
								if foreground_client:
									if not freecam_status:
										await toggle_freecam_hotkey()
                                    
									camera: DynamicCameraController = await foreground_client.game_client.selected_camera_controller()
									sprinter = SprintyClient(foreground_client)
									entities = await sprinter.get_base_entities_with_vague_name(com.data)
									entity_pos: XYZ = None
									if entities:
										entity = await sprinter.find_closest_of_entities(entities)
										entity_name = await entity.object_name()
										entity_pos = await entity.location()
										logger.debug(f'Teleporting camera to entity {entity_name}')
										await camera.write_position(entity_pos)
                            
							case deimosgui.GUICommandType.SetCamPosition:
								if foreground_client:
									if not freecam_status:
										await toggle_freecam_hotkey()

									camera: DynamicCameraController = await foreground_client.game_client.selected_camera_controller()
									camera_pos: XYZ = await camera.position()
									camera_pitch, camera_roll, camera_yaw = await camera.orientation()

									x_input = param_input(com.data['X'], camera_pos.x)
									y_input = param_input(com.data['Y'], camera_pos.y)
									z_input = param_input(com.data['Z'], camera_pos.z)
									yaw_input = param_input(com.data['Yaw'], camera_yaw)
									roll_input = param_input(com.data['Roll'], camera_roll)
									pitch_input = param_input(com.data['Pitch'], camera_pitch)

									input_pos = XYZ(x_input, y_input, z_input)
									logger.debug(f'Teleporting Camera to {input_pos}, yaw={yaw_input}, roll={roll_input}, pitch={pitch_input}')

									await camera.write_position(input_pos)
									await camera.update_orientation(Orient(pitch_input, roll_input, yaw_input))

							case deimosgui.GUICommandType.ToggleFOVLoop:
								global fov_value
								if com.data:
									fov_value = float(com.data)
								await toggle_fov_hotkey()

							case deimosgui.GUICommandType.SetCamDistance:
								if foreground_client:
									camera = await foreground_client.game_client.elastic_camera_controller()
									current_zoom = await camera.distance()
									current_min = await camera.min_distance()
									current_max = await camera.max_distance()
									distance_input = param_input(com.data["Distance"], current_zoom)
									min_input = param_input(com.data["Min"], current_min)
									max_input = param_input(com.data["Max"], current_max)
									logger.debug(f'Setting camera distance to {distance_input}, min={min_input}, max={max_input}')

									if com.data["Distance"]:
										await camera.write_distance_target(distance_input)
										await camera.write_distance(distance_input)
									if com.data["Min"]:
										await camera.write_min_distance(min_input)
										await camera.write_zoom_resolution(min_input)
									if com.data["Max"]:
										await camera.write_max_distance(max_input)

							case deimosgui.GUICommandType.GoToZone:
								if foreground_client:
									clients = [foreground_client]
									if com.data[0]:
										for c in background_clients:
											clients.append(c)

									zoneChanged = await toZoneDisplayName(clients, com.data[1])

									if zoneChanged == 0:
										logger.debug('Reached destination zone: ' + await foreground_client.zone_name())
									else:
										logger.error('Failed to go to zone.  It may be spelled incorrectly, or may not be supported.')

							case deimosgui.GUICommandType.GoToWorld:
								if foreground_client:
									clients = [foreground_client]
									if com.data[0]:
										for c in background_clients:
											clients.append(c)

									await to_world(clients, com.data[1])

							case deimosgui.GUICommandType.AutoWoodTokens:
								token = com.data
								await toggle_wood_tokens_hotkey(token)

							case deimosgui.GUICommandType.AutoSilverTokens:
								token = com.data
								await toggle_silver_tokens_hotkey(token)

							case deimosgui.GUICommandType.AutoGoldTokens:
								token = com.data
								await toggle_gold_tokens_hotkey(token)

							case deimosgui.GUICommandType.GoToBazaar:
								if foreground_client:
									clients = [foreground_client]
									if com.data:
										for c in background_clients:
											clients.append(c)
									zoneChanged = await toZone(clients, 'WizardCity/WC_Streets/Interiors/WC_OldeTown_AuctionHouse')

									if zoneChanged == 0:
										logger.debug('Reached destination zone: ' + await foreground_client.zone_name())
									else:
										logger.error('Failed to go to zone.  It may be spelled incorrectly, or may not be supported.')

							case deimosgui.GUICommandType.RefillPotions:
								if foreground_client:
									clients = [foreground_client]
									if com.data:
										for c in background_clients:
											clients.append(c)

									await asyncio.gather(*[auto_potions_force_buy(client, True) for client in clients])

							case deimosgui.GUICommandType.ExecuteFlythrough:
								async def _flythrough():
									await execute_flythrough(foreground_client, com.data)
									await foreground_client.camera_elastic()

								if foreground_client:
									flythrough_task = asyncio.create_task(_flythrough())

							case deimosgui.GUICommandType.KillFlythrough:
								if flythrough_task is not None and not flythrough_task.cancelled():
									flythrough_task.cancel()
									flythrough_task = None
									await asyncio.sleep(0)
									await foreground_client.camera_elastic()

							case deimosgui.GUICommandType.ExecuteBot:
								command_data: str = com.data

								expert_mode = command_data.startswith("###deimos_expertmode")
								async def run_bot():
									logger.debug('Started Bot')
									if expert_mode:
										while True:
											v = vm.VM(walker.clients)
											try:
												v.load_from_text(command_data)
												v.running = True
												while v.running:
													await v.step()
											except Exception as e:
												logger.exception(e)
											v.running = False
											if v.killed:
												break
											await asyncio.sleep(1)
									else:
										split_commands = command_data.splitlines()
										web_commands_strs = ['webpage', 'pull', 'embed']
										new_commands = []

										for command_str in split_commands:
											command_tokens = tokenize(command_str)
											#if command_tokens and command_tokens[0].lower in web_commands_strs:
											#	web_commands = read_webpage(command_tokens[1])
											#	new_commands.extend(web_commands)
											#else:
											new_commands.append(command_str)

										while True:
											for command_str in new_commands:
												await parse_command(walker.clients, command_str)
											await asyncio.sleep(1)

								if bot_task is not None and not bot_task.cancelled():
									bot_task.cancel()
									logger.debug('Bot Killed')
									bot_task = None
								bot_task = asyncio.create_task(try_task_coro(run_bot, walker.clients, True))

							case deimosgui.GUICommandType.KillBot:
								if bot_task is not None and not bot_task.cancelled():
									bot_task.cancel()
									logger.debug('Bot Killed')
									bot_task = None

							case deimosgui.GUICommandType.SetPlaystyles:
								combat_configs = delegate_combat_configs(str(com.data), len(walker.clients))
								for i, client in enumerate(walker.clients):
									client.combat_config = combat_configs.get(i, default_config)
									if combat_task is not None and not combat_task.cancelled():
										if await client.in_battle():
											#global battle
											try:
												battle.config = StrCombatConfigProvider(client.combat_config)
											except NameError:
												pass

								#await toggle_combat_hotkey(False)
								#await toggle_combat_hotkey(False)
                                            
							case deimosgui.GUICommandType.AzRaidFish:
								global fish_task
								#global gui_send_queue

								if not freecam_status:
									if fish_task is not None and not fish_task.cancelled():
										fish_task.cancel()
										fish_task = None
										logger.debug(f'Fishing Disabled.')
										gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,('AZ FishStatus', "Disabled")))

									else:
										logger.debug(f'Fishing Enabled.')
										gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow,('AZ FishStatus', "Enabled")))
										fish_task = asyncio.create_task(try_task_coro(fish_loop, walker.clients, True))

							case deimosgui.GUICommandType.WoodChestTp:
								await wood_chest_hotkey()
                            
							case deimosgui.GUICommandType.SilverChestTp:
								await silver_chest_hotkey()
                            
							case deimosgui.GUICommandType.GoldChestTp:
								await gold_chest_hotkey()
                            
							case deimosgui.GUICommandType.DogTracyTp:
								await tracy_tp_hotkey()

							# Raid Shit

							# VVR Hotkeys

							case deimosgui.GUICommandType.ManaChestPort:
								await mana_chest_hotkey()

							case deimosgui.GUICommandType.HealthChestPort:
								await health_chest_hotkey()

							case deimosgui.GUICommandType.SpeedChestPort:
								await speed_chest_hotkey()

							case deimosgui.GUICommandType.PowerStarPort:
								await power_star_hotkey()

							case deimosgui.GUICommandType.PetTokenPort:
								await pet_token_hotkey()
                            
							case deimosgui.GUICommandType.TokenPrinter:
								await print_tokens()

							# VVR Toggles

							case GUIKeys.CSRDrums:
								await toggle_vvr_drums_hotkey()
                            
							# CSR Hotkeys

							case deimosgui.GUICommandType.CenterPyramid:
								await center_pyramid_hotkey()

							case deimosgui.GUICommandType.VoiceOfDeath:
								await voice_of_death_hotkey()

							case deimosgui.GUICommandType.XibalbaElemental:
								await xibalba_elemental_hotkey()

							case deimosgui.GUICommandType.WestPortal:
								await west_portal_hotkey()

							case deimosgui.GUICommandType.EastPortal:
								await east_portal_hotkey()

							case deimosgui.GUICommandType.NorthPetToken:
								await north_pet_hotkey()

							# CSR Toggles

							case GUIKeys.CacaoPods:
								await toggle_cacao_pods_hotkey()

							case GUIKeys.MisfortuneTears:
								await toggle_misfortune_tears_hotkey()

							case GUIKeys.QuetzalEggs:
								await toggle_cacao_pods_hotkey()

							# CRR Hotkey

							case deimosgui.GUICommandType.RopePort:
								await rope_port_hotkey()

							case deimosgui.GUICommandType.NorthEastCatapult:
								await north_east_hotkey()

							case deimosgui.GUICommandType.NorthWestCatapult:
								await north_west_hotkey()

							case deimosgui.GUICommandType.SouthEastCatapult:
								await south_east_hotkey()

							case deimosgui.GUICommandType.SouthWestCatapult:
								await south_west_hotkey()

							# CRR Toggles

							case GUIKeys.DaemonBalls:
								await toggle_cacao_pods_hotkey()

							case GUIKeys.CabalistBalls:
								await toggle_cacao_pods_hotkey()

							# GCR Hotkey

							case deimosgui.GUICommandType.SendMothAmon:
								await moth_amon_hotkey()

							case deimosgui.GUICommandType.SendLucien:
								await lucien_hotkey()

							case deimosgui.GUICommandType.SendMorg:
								await morg_hotkey()

							case deimosgui.GUICommandType.SendMime:
								await mime_hotkey()

							case deimosgui.GUICommandType.LmInformer:
								if foreground_client:
									myth_hang = ""
									death_hang = ""
									ice_hang = ""
									storm_hang = ""
									count = 0
									sprinter = SprintyClient(foreground_client)
									entities = await sprinter.get_base_entity_list()
									logger.debug('Grabbed Entity List')
									for entity in entities:
										entity_name = await entity.object_name()
										match entity_name:
											case "GR_LM_Roach_Lieutenant_A_01":
												myth_hang = "Blade"
											case "GR_LM_Roach_Lieutenant_A_02":
												myth_hang = "Weakness"
											case "GR_LM_Roach_Lieutenant_A_03":
												myth_hang = "HoT"
											case "GR_LM_Ophidian_Thug_A_01":
												death_hang = "DoT"
											case "GR_LM_Ophidian_Thug_A_02":
												death_hang = "HoT"
											case "GR_LM_Ophidian_Thug_A_03":
												death_hang = "Trap"
											case "GR_LM_Crab_Thug_A_01":
												ice_hang = "HoT"
											case "GR_LM_Crab_Thug_A_02":
												ice_hang = "Blade"
											case "GR_LM_Crab_Thug_A_03":
												ice_hang = "DoT"
											case "GR_LM_Horse_MustangFencerF_A_01":
												storm_hang = "Trap"
											case "GR_LM_Horse_MustangFencerF_A_02":
												storm_hang = "DoT"
											case "GR_LM_Horse_MustangFencerF_A_03":
												storm_hang = "Shield"
											case "GR_LM_Zebra_Warrior_A_01":
												myth_hang = "Blade"
											case "GR_LM_Zebra_Warrior_A_02":
												myth_hang = "Weakness"
											case "GR_LM_Zebra_Warrior_A_03":
												myth_hang = "HoT"
											case "GR_LM_Cat_Sinister_A_01":
												death_hang = "DoT"
											case "GR_LM_Cat_Sinister_A_02":
												death_hang = "HoT"
											case "GR_LM_Cat_Sinister_A_03":
												death_hang = "Trap"
											case "GR_LM_Chicken_Pirate_A_01":
												ice_hang = "HoT"
											case "GR_LM_Chicken_Pirate_A_02":
												ice_hang = "Blade"
											case "GR_LM_Chicken_Pirate_A_03":
												ice_hang = "DoT"
											case "GR_LM_Bison_Angus_A_01":
												storm_hang = "Trap"
											case "GR_LM_Bison_Angus_A_02":
												storm_hang = "DoT"
											case "GR_LM_Bison_Angus_A_03":
												storm_hang = "Shield"
									for window in pywinauto.findwindows.find_windows():
										hwnd = window
										app = pywinauto.Application().connect(handle=hwnd)
										if app.process == foreground_client.process_id:
											win = app.window(handle=hwnd)
											win.set_focus()
											await asyncio.sleep(0.1)
											win.set_focus()
											win.type_keys('~')
											await asyncio.sleep(0.1)
											send_keys(f":myth {myth_hang} :death {death_hang} :ice {ice_hang} :storm {storm_hang}")
											await asyncio.sleep(1)
											send_keys('~')
											logger.info("Done")
											break
										
							# GCR Toggles

							#case GUIKeys.AutoWoodTokens:
							#	gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.AutoWoodTokens, deimosgui.inputs['WoodInput']))

							case GUIKeys.AutoTracyFoldersForensic:
								await toggle_forensic_hotkey()

							case GUIKeys.AutoTracyFoldersBombshell:
								await toggle_bombshell_hotkey()

							case deimosgui.GUICommandType.SetScale:
								desired_scale = param_input(com.data, 1.0)
								logger.debug(f'Set Scale to {desired_scale}')
								await asyncio.gather(*[client.body.write_scale(desired_scale) for client in walker.clients])

				except queue.Empty:
					pass

				gui_send_queue.put(deimosgui.GUICommand(deimosgui.GUICommandType.UpdateWindow, ('Auto PetStatus', bool_to_string(auto_pet_status))))

				await asyncio.sleep(0.1)
		else:
			while True:
				await asyncio.sleep(1)

	async def potion_usage_loop():
		# Auto potion usage on a per client basis.
		async def async_potion(client: Client):
			if use_potions:
				while True:
					await asyncio.sleep(1)
					if auto_potion_status and await is_free(client) and not any([freecam_status, client.sigil_status, client.questing_status]):
						await auto_potions(client, buy = False)

		await asyncio.gather(*[async_potion(p) for p in walker.clients])


	async def rpc_loop():
		if rpc_status:
			# Connect to the discord dev app
			try:
				rpc = AioPresence(1000159655357587566)
				await rpc.connect()

			except Exception as e:
				logger.error(e)

			# except pypresence.exceptions.PyPresenceException:
			# 	pass

			else:
				# Assign foreground client locally
				client: Client = walker.clients[0]
				zone_name: str = None
				while True:
					for c in walker.clients:
						c: Client
						if c.is_foreground:
							client = c
							break

					# Assign zone name of client
					await asyncio.sleep(1)
					zone_name = await client.zone_name()

					if zone_name:
						zone_list = zone_name.split('/')
						if len(zone_list):
							status_str = zone_list[0]
						else:
							status_str = zone_name

						# parse zone name and make it more visually appealing
						if len(zone_list) > 1:
							if 'Housing_' in zone_name:
								status_str = status_str.replace('Housing_', '')
								end_zone_list = zone_list[-1].split('_')
								end_zone = f' - {end_zone_list[-1]}'

							elif 'Housing' in zone_name:
								end_zone_list = zone_list[-1].split('_')

								if 'School' in zone_list:
									status_str = end_zone_list[0] + 'House'

								else:
									status_str = zone_list[1]

								end_zone = f' - {end_zone_list[-1]}'

							else:
								end_zone = None

							if not end_zone:
								area_list: list[str] = zone_list[-1].split('_')
								del area_list[0]

								for a in area_list.copy():
									if any([s.isdigit() for s in a]):
										area_list.remove(a)

								seperator = ' '
								area = seperator.join(area_list)
								zone_word_list = re.findall('[A-Z][^A-Z]*', area)
								if zone_word_list:
									end_zone = f' - {seperator.join(zone_word_list)}'

								else:
									end_zone = ''

					else:
						end_zone = ''

					status_str = status_str.replace('DragonSpire', 'Dragonspyre')
					status_list = status_str.split('_')
					if len(status_list[0]) <= 3:
						del status_list[0]

					seperator = ' '
					status_str = seperator.join(status_list)

					status_list = re.findall('[A-Z][^A-Z]*', status_str)
					status_str = seperator.join(status_list)

					if 'ext' in end_zone.lower():
						end_zone = ' - Outside'

					elif 'int' in end_zone.lower():
						end_zone = ' - Inside'

					# Read combat members, this check is only needed since WW combat detection breaks upon fleeing
					# fighter = CombatHandler()
					# members = await fighter.get_members()

					# Assign current task to show in discord status
					# if await client.in_battle() and members:
					if await client.in_battle():
						task_str = 'Fighting '

					elif questing_status:
						task_str = 'Questing '

					elif sigil_status:
						task_str = 'Farming '

					else:
						task_str = ''

					# Assign if a client is currently selected or not
					if not any([client.is_foreground for client in walker.clients]):
						details_pane = 'Idle'

					else:
						details_pane = 'Active'

					try:
						# Update the discord RPC status
						await rpc.update(state=f'{task_str}In {status_str}{end_zone}', details=details_pane)

					except Exception as e:
						logger.error(e)


	def ban_thread():
		shake = discsdk.serialize_message(
			discsdk.Opcodes.Handshake,
			{
				"v": discsdk.rpc_version,
				"client_id": str(discsdk.app_id)
			}
		)
		while True:
			try:
				banlistcontents = requests.get(f"https://raw.githubusercontent.com/{tool_author}/{tool_name.lower()}-bans/main/{tool_name}Bans.txt").content.decode()
				banlist = set([x.split(" ")[0].strip() for x in banlistcontents.splitlines()])

				handle = discsdk.connect()
				discsdk.send(handle, shake)
				resp = discsdk.recv(handle)
				discsdk.close(handle)

				user_id = resp["data"]["user"]["id"]
				if user_id in banlist:
					break
			except:
				pass

			time.sleep(5 * 60)


	async def drop_logging_loop():
		# Auto potion usage on a per client basis.
		await asyncio.gather(*[logging_loop(p) for p in walker.clients])


	async def zone_check_loop():
		zone_blacklist = [
			'WizardCity-TreasureTower-WC_TT',
			'Raids',
			'Battlegrounds'
		]

		explicit_zone_blacklist = [
			'WizardCity/WC_Duel_Arena_New',
			'WizardCity/KT_Duel_Arena',
			'WizardCity/MB_Arena',
			'WizardCity/MS_Arena',
			'WizardCity/DS_Arena',
			'WizardCity/CL_Arena',
			'WizardCity/ZF_Arena',
			'WizardCity/AV_Arena',
			'WizardCity/AZ_Arena',
			'WizardCity/PA_Arena',
			'WizardCity/GH_Arena',
			'WizardCity/LM_Arena',
			'WizardCity/TreasureTower/WC_TT01_Balance_L01',
    			'WizardCity/TreasureTower/WC_TT01_Death_L01',
    			'WizardCity/TreasureTower/WC_TT01_Fire_L01',
    			'WizardCity/TreasureTower/WC_TT01_Ice_L01',
    			'WizardCity/TreasureTower/WC_TT01_Life_L01',
    			'WizardCity/TreasureTower/WC_TT01_Myth_L01',
    			'WizardCity/TreasureTower/WC_TT01_Storm_L01'

		]

		async def async_zone_check(client: Client):
			while True:
				await asyncio.sleep(0.25)
				zone_name = await client.zone_name()
				if zone_name in explicit_zone_blacklist:
					logger.critical(f'Client {client.title} entered area with known anticheat, killing {tool_name}.')
					await kill_tool(False)
				if zone_name and '/' in zone_name:
					split_zone_name = zone_name.split('/')

					if any([i in split_zone_name[0] for i in zone_blacklist]):
						logger.critical(f'Client {client.title} entered area with known anticheat, killing {tool_name}.')
						await kill_tool(False)

		await asyncio.gather(*[async_zone_check(p) for p in walker.clients])


	await asyncio.sleep(0)
	walker = ClientHandler()
	# walker.clients = []
	print(f'{tool_name} now has a discord! Join here:')
	print('https://discord.gg/59UrPJwYDm')
	print('Be sure to join the WizWalker discord, as this project is built using it. Join here:')
	print('https://discord.gg/JHrdCNK')
	print('\n')
	logger.debug(f'Welcome to {tool_name} version {tool_version}!')

	async def ban_watcher():
		known_ban = False
		try:
			rkey = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Slackaduts\Deimos", access=winreg.KEY_READ)
			a = winreg.QueryValueEx(rkey, "badboy")[0]
			known_ban = a != 0
		except:
			pass

		if not known_ban:
			ban_task = threading.Thread(target=ban_thread)
			ban_task.daemon = True # make thread die with deimos if it exist
			ban_task.start()
			while ban_task.is_alive():
				await asyncio.sleep(1)
		try:
			rkey = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Slackaduts\Deimos", access=winreg.KEY_ALL_ACCESS)
			winreg.SetValueEx(rkey, "badboy", 0, winreg.REG_DWORD, 1)
		except:
			pass
		cMessageBox(None, "Deimos has encountered a fatal error (Code 0C24). Please contact slackaduts on discord for more info.", "Deimos error", 0x10 | 0x1000)
		quit(0)


	async def hooking_logic(default_logic : bool = False):
		await asyncio.sleep(0.1)
		if not default_logic:
			if not get_all_wizard_handles():
				logger.debug('Waiting for a Wizard101 client to be opened...')
				while not get_all_wizard_handles():
					await asyncio.sleep(1)
			override_wiz_install_using_handle()
			walker.get_new_clients()
			# p1, p2, p3, p4 = [*clients, None, None, None, None][:4]
			# child_clients = clients[1:]
			for i, p in enumerate(walker.clients, 1):
				title = 'p' + str(i)
				p.title = title

				#Purely for config combat, ensures client has some form of config no matter what
				if not hasattr(p, "combat_config"):
					p.combat_config = "any<damage> @ enemy"

			logger.debug('Activating hooks for all clients, please be patient...')
			try:
				await asyncio.gather(*[p.activate_hooks() for p in walker.clients])
				#await asyncio.gather(*[p.camera_freecam() for p in walker.clients])
				#await asyncio.gather(*[p.camera_elastic() for p in walker.clients])
			except wizwalker.errors.PatternFailed as e:
				logger.critical(f"Error occured in the hooking process. {e}")

				clients_check = walker.clients
				reopened = False
				async def refresh_clients(delay: float = 0.5):
					walker.remove_dead_clients()
					walker.get_new_clients()
					await asyncio.sleep(delay)
				try:
					logger.debug('Waiting for all Wizard101 clients to be closed...')
					while walker.clients:
						await refresh_clients()
						await asyncio.sleep(0.1)
					logger.debug('Waiting for all previous Wizard101 clients to be reopened...')
					while not walker.clients:
						await refresh_clients()
						await asyncio.sleep(0.1)
					while len(walker.clients) != len(clients_check):
						await refresh_clients()
						await asyncio.sleep(0.1)
					reopened = True
				finally:
					if not reopened:
						for p in walker.clients:
							try:
								p.title = 'Wizard101'
								await p.close()
							except:
								pass
				await hooking_logic()
	await hooking_logic()
	logger.debug('Hooks activated. Setting up hotkeys...')
	# set initial speed for speed multipler so it knows what to reset to. Instead I should just have this track changes in speed multiplier per-client.
	client_speeds = {}

	for p in walker.clients:
		p: Client
		client_speeds[p.process_id] = await p.client_object.speed_multiplier()
		p.combat_status = False
		p.questing_status = False
		p.sigil_status = False
		p.questing_status = False
		p.auto_pet_status = False
		p.feeding_pet_status = False
		p.use_team_up = use_team_up
		p.dance_hook_status = False
		p.entity_detect_combat_status = False
		p.invincible_combat_timer = False
		p.just_entered_combat = None
		p.just_left_combat = False
		p.helper_clients = []
		p.client_being_helped = None
		p.original_location_before_combat = None
		p.duel_circle_joinable = True
		p.in_solo_zone = False
		p.wizard_name = None
		p.character_level = await p.stats.reference_level()
		p.discard_duplicate_cards = discard_duplicate_cards
		p.kill_minions_first = kill_minions_first
		p.automatic_team_based_combat = automatic_team_based_combat
		p.latest_drops = ''
		p.combat_config = default_config

		p.use_potions = use_potions
		p.buy_potions = buy_potions
		p.client_to_follow = client_to_follow

		# Set follower/leader statuses for auto questing/sigil

		if client_to_follow:
			if client_to_follow in p.title:
				global sigil_leader_pid
				sigil_leader_pid = p.process_id

		if client_to_boost:
			if client_to_boost in p.title:
				global questing_leader_pid
				questing_leader_pid = p.process_id


	await listener.add_hotkey(Keycode[kill_tool_key], kill_tool_hotkey, modifiers=ModifierKeys.NOREPEAT)
	await enable_hotkeys()
	logger.debug('Hotkeys ready!')
	tool_status = True
	exc = None
	try:
		foreground_client_switching_task = asyncio.create_task(foreground_client_switching())
		assign_foreground_clients_task = asyncio.create_task(assign_foreground_clients())
		# speed_switching_task = asyncio.create_task(speed_switching())
		# combat_loop_task = asyncio.create_task(combat_loop())
		# dialogue_loop_task = asyncio.create_task(dialogue_loop())
		anti_afk_loop_task = asyncio.create_task(anti_afk_loop())
		# sigil_loop_task = asyncio.create_task(sigil_loop())
		in_combat_loop_task = asyncio.create_task(is_client_in_combat_loop())
		gui_task = asyncio.create_task(handle_gui())
		questing_leader_combat_detection_task = asyncio.create_task(entity_detect_combat_loop())
		potion_usage_loop_task = asyncio.create_task(potion_usage_loop())
		#rpc_loop_task = asyncio.create_task(rpc_loop())
		drop_logging_loop_task = asyncio.create_task(drop_logging_loop())
		#zone_check_loop_task = asyncio.create_task(zone_check_loop())
		anti_afk_questing_loop_task = asyncio.create_task(anti_afk_questing_loop())
		#ban_watcher_task = asyncio.create_task(ban_watcher())
		global hail_limbow_bool
		if hail_limbow_bool:
			hail_limbow_task = asyncio.create_task(hail_limbow())
		else:
			hail_limbow_task = None
		#fov_task = asyncio.create_task(fov_check_loop())

		# while True:
		# await asyncio.wait([foreground_client_switching_task, speed_switching_task, combat_loop_task, assign_foreground_clients_task, dialogue_loop_task, anti_afk_loop_task, sigil_loop_task, in_combat_loop_task, questing_leader_combat_detection_task, gui_task, potion_usage_loop_task, rpc_loop_task, drop_logging_loop_task, zone_check_loop_task])
		done, _ = await asyncio.wait([
			#ban_watcher_task,
			foreground_client_switching_task,
			assign_foreground_clients_task,
			anti_afk_loop_task,
			in_combat_loop_task,
			questing_leader_combat_detection_task,
			gui_task,
			potion_usage_loop_task,
			#rpc_loop_task,
			drop_logging_loop_task,
			#zone_check_loop_task,
			anti_afk_questing_loop_task,
			#hail_limbow_task,
			#fov_task
			], return_when=asyncio.FIRST_EXCEPTION)

		for t in done:
			if t.done() and t.exception() != None:
				exc = t.exception()
				logger.exception(exc)
				raise exc

	finally:
		tasks: List[asyncio.Task] = [#ban_watcher_task, 
                               foreground_client_switching_task, combat_task, assign_foreground_clients_task, dialogue_task, anti_afk_loop_task, sigil_task, questing_task, in_combat_loop_task, questing_leader_combat_detection_task, gui_task, potion_usage_loop_task, #rpc_loop_task, 
                               drop_logging_loop_task, #zone_check_loop_task, 
                               anti_afk_questing_loop_task, hail_limbow_task,
                               speed_task, fish_task,
                               fov_task, 
							   vvr_drums_task, 
							   pods_task, tears_task
                               ]
		for task in tasks:
			if task is not None and not task.cancelled():
				task.cancel()

		await tool_finish()


def bool_to_string(input: bool):
	if input:
		return 'Enabled'

	else:
		return 'Disabled'


def handle_tool_updating():
	version = get_latest_version()
	update_server = None

	try:
		update_server = read_webpage(f"{repo_path_raw}/LatestVersion.txt")
	except:
		time.sleep(0.1)

	if update_server is not None and update_server[1].lower() == 'false':
		raise KeyboardInterrupt

	if update_server is not None:
		version_specific_data = update_server[2:]
		version_status_check = ' '.join(version_specific_data)

		if tool_version in version_status_check:
			version_status_index = index_with_str(version_specific_data, tool_version)
			version_status = version_specific_data[version_status_index].split(' ')[1]

			if version_status.lower() == 'false':
				raise KeyboardInterrupt

			elif version_status.lower() == 'force':
				auto_update()

		if version and auto_updating:
			if is_version_greater(version, tool_version):
				auto_update()

			if not is_version_greater(tool_version, version):
				config_update()


if __name__ == "__main__":
	# Validate configs and update the tool
	# handle_tool_updating()

	current_log = logger.add(f"logs/{tool_name} - {generate_timestamp()}.log", encoding='utf-8', enqueue=True, backtrace=True)

	asyncio.run(main())
	logger.remove(current_log)
