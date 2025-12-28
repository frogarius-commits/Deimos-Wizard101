from enum import Enum, auto
import gettext
import queue
import re
import PySimpleGUI as gui
import pyperclip
from src.combat_objects import school_id_to_names
from src.paths import wizard_city_dance_game_path
from src.utils import assign_pet_level, get_ui_tree_text

gui.set_global_icon("..\\Deimos-logo.ico")
global inputs


class GUICommandType(Enum):
	# deimos <-> window
	Close = auto()

	# window -> deimos
	ToggleOption = auto()
	Copy = auto()
	SelectEnemy = auto()

	Teleport = auto()
	CustomTeleport = auto()
	EntityTeleport = auto()
	TokenPrinter = auto()
	ToggleFOVLoop = auto()


	XYZSync = auto()
	XPress = auto()

	GoToZone = auto()
	GoToWorld = auto()
	GoToBazaar = auto()

	RefillPotions = auto()
	AzRaidFish = auto()
	LmInformer = auto()
	WoodChestTp = auto()
	SilverChestTp = auto()
	GoldChestTp = auto()
	DogTracyTp = auto()

	AnchorCam = auto()
	SetCamToEntity = auto()
	SetCamPosition = auto()
	SetCamDistance = auto()

	ExecuteFlythrough = auto()
	KillFlythrough = auto()

	ExecuteBot = auto()
	KillBot = auto()

	SetPlaystyles = auto()

	# SetPetWorld = auto()

	SetScale = auto()

	# Raid Shit

	# VVR
	VVRDrums = auto()
	ManaChestPort = auto()
	HealthChestPort = auto()
	SpeedChestPort = auto()
	PowerStarPort = auto()
	PetTokenPort = auto()

	# CSR
	CenterPyramid = auto()
	VoiceOfDeath = auto()
	XibalbaElemental = auto()
	WestPortal = auto()
	EastPortal = auto()
	NorthPetToken = auto()
	#SouthToken = auto()
	MisfortuneTears = auto()
	CacaoPods = auto()
	CSRDrums = auto()
	QuetzalEggs = auto()

	# CRR
	RopePort = auto()
	NorthEastCatapult = auto()
	NorthWestCatapult = auto()
	SouthEastCatapult = auto()
	SouthWestCatapult = auto()
	DaemonBalls = auto()
	CabalistBalls = auto()

	# GCR
	AutoWoodTokens = auto()
	AutoSilverTokens = auto()
	AutoGoldTokens = auto()
	AutoTracyFoldersForensic = auto()
	AutoTracyFoldersBombshell = auto()
	SendMothAmon = auto()
	SendLucien = auto()
	SendMorg = auto()
	SendMime = auto()

	# deimos -> window
	UpdateWindow = auto()
	UpdateWindowValues = auto()

	ShowUITreePopup = auto()
	ShowEntityListPopup = auto()

# TODO:
# - inherit from StrEnum in 3.11 to make this nicer
# - fix naming convention, it's inconsistent
class GUIKeys:
	toggle_speedhack = "togglespeedhack"
	toggle_combat = "togglecombat"
	toggle_dialogue = "toggledialogue"
	toggle_sigil = "togglesigil"
	toggle_questing = "toggle_questing"
	toggle_auto_pet = "toggleautopet"
	toggle_auto_potion = "toggleautopotion"
	toggle_freecam = "togglefreecam"
	toggle_camera_collision = "togglecameracollision"
	toggle_fov_loop = "togglefovloop"

	hotkey_quest_tp = "hotkeyquesttp"
	hotkey_freecam_tp = "hotkeyfreecamtp"

	mass_hotkey_mass_tp = "masshotkeymasstp"
	mass_hotkey_xyz_sync = "masshotkeyxyzsync"
	mass_hotkey_x_press = "masshotkeyxpress"

	copy_position = "copyposition"
	copy_zone = "copyzone"
	copy_rotation = "copyrotation"
	copy_entity_list = "copyentitylist"
	copy_ui_tree = "copyuitree"
	copy_camera_position = "copycameraposition"
	copy_stats = "copystats"
	copy_camera_rotation = "copycamerarotation"

	button_custom_tp = "buttoncustomtp"
	button_entity_tp = "buttonentitytp"
	button_go_to_zone = "buttongotozone"
	button_mass_go_to_zone = "buttonmassgotozone"
	button_go_to_world = "buttongotoworld"
	button_mass_go_to_world = "buttonmassgotoworld"
	button_go_to_bazaar = "buttongotobazaar"
	button_mass_go_to_bazaar = "buttonmassgotobazaar"
	button_refill_potions = "buttonrefillpotions"
	button_mass_refill_potions = "buttonmassrefillpotions"
	button_az_raid_fish = "buttonazraidfish"
	button_lm_informer = "buttonlminformer"
	button_wood_chest_tp = "buttonwoodchesttp"
	button_silver_chest_tp = "buttonsilverchesttp"
	button_gold_chest_tp = "buttongoldchesttp"
	button_dog_tracy_tp = "buttondogtracytp"
	button_set_camera_position = "buttonsetcameraposition"
	button_anchor = "buttonanchor"
	button_camera_tp = "buttoncameratp"
	button_set_distance = "buttonsetdistance"
	button_view_stats = "buttonviewstats"
	button_swap_members = "buttonswapmembers"
	button_token_print = "buttontokenprint"

	button_execute_flythrough = "buttonexecuteflythrough"
	button_kill_flythrough = "buttonkillflythrough"
	button_run_bot = "buttonrunbot"
	button_kill_bot = "buttonkillbot"
	button_set_playstyles = "buttonsetplaystyles"
	button_set_scale = "buttonsetscale"

	# Raid Shit

	# VVR
	VVR_Drums = "vvrdrums"
	ManaChestPort = "manachestport"
	HealthChestPort = "healthchestport"
	SpeedChestPort = "speedchestport"
	PowerStarPort = "powerstarport"
	PetTokenPort = "pettokenport"

	# CSR
	CenterPyramid = "centerpyramid"
	VoiceOfDeath = "voiceofdeath"
	XibalbaElemental = "xibalbaelemental"
	WestPortal = "westportal"
	EastPortal = "eastportal"
	NorthPetToken = "northpettoken"
	#SouthToken = auto()
	MisfortuneTears =  "misfortunetears"
	CacaoPods = "cacaopods"
	CSRDrums = "csrdrums"
	QuetzalEggs = "quetzaleggs"

	# CRR
	RopePort = "ropeport"
	NorthEastCatapult = "northeastcatapult"
	NorthWestCatapult = "northwestcatapult"
	SouthEastCatapult = "southeastcatapult"
	SouthWestCatapult = "southwestcatapult"
	DaemonBalls = "daemonballs"
	CabalistBalls = "cabalistballs"

	# GCR
	AutoWoodTokens = "autowoodtokens"
	AutoSilverTokens = "autosilvertokens"
	AutoGoldTokens = "autogoldtokens"
	AutoTracyFoldersForensic = "autotracyfoldersforensic"
	AutoTracyFoldersBombshell = "autotracyfoldersbombshell"
	SendMothAmon = "mothamon"
	SendLucien = "lucien"
	SendMorg = "morg"
	SendMime = "mime"

	# deimos -> window
	UpdateWindow = auto()
	UpdateWindowValues = auto()

	ShowUITreePopup = auto()
	ShowEntityListPopup = auto()


class GUICommand:
	def __init__(self, com_type: GUICommandType, data=None):
		self.com_type = com_type
		self.data = data


def hotkey_button(name: str, key, auto_size: bool, text_color: str, button_color: str):
	return gui.Button(name, button_color=(text_color, button_color), auto_size_button=auto_size, key=key)

def hotkey_button_sized(name: str, key, auto_size: bool, text_color: str, button_color: str, size=(None, None)):
	return gui.Button(name, button_color=(text_color, button_color), auto_size_button=auto_size, key=key, size=size)

def create_gui(gui_theme, gui_text_color, gui_button_color, tool_name, tool_version, gui_on_top, langcode):
	gui.theme(gui_theme)

	if langcode != 'en':
		translate = gettext.translation("messages", "locale", languages=[langcode])
		tl = translate.gettext
	else:
		# maybe use gettext (module) as translate instead?
		gettext.bindtextdomain('messages', 'locale')
		gettext.textdomain('messages')
		tl = gettext.gettext

	gui.popup(tl('This client was made by Hunter. For any and all concerns please go to Hunter.'), title=tl('Hunter Client'), keep_on_top=True, text_color=gui_text_color, button_color=(gui_text_color, gui_button_color))

	global hotkey_button
	original_hotkey_button = hotkey_button

	def hotkey_button(name, key, auto_size=False, text_color=gui_text_color, button_color=gui_button_color):
		return original_hotkey_button(name, key, auto_size, text_color, button_color)

	# TODO: Switch to using keys for this stuff
	toggles: list[tuple[str, str]] = [
		(tl('Speedhack'), GUIKeys.toggle_speedhack),
		(tl('Combat'), GUIKeys.toggle_combat),
		(tl('Dialogue'), GUIKeys.toggle_dialogue),
		(tl('Sigil'), GUIKeys.toggle_sigil),
		(tl('Questing'), GUIKeys.toggle_questing),
		(tl('Auto Pet'), GUIKeys.toggle_auto_pet),
		(tl('Auto Potion'), GUIKeys.toggle_auto_potion),
	]
	hotkeys: list[tuple[str, str]] = [
		(tl('Quest TP'), GUIKeys.hotkey_quest_tp),
		(tl('Freecam'), GUIKeys.toggle_freecam),
		(tl('Freecam TP'), GUIKeys.hotkey_freecam_tp),
		(tl('Wood TP'), GUIKeys.button_wood_chest_tp),
		(tl('Silver TP'), GUIKeys.button_silver_chest_tp),
		(tl('Gold TP'), GUIKeys.button_gold_chest_tp),
		(tl('Tracy TP'), GUIKeys.button_dog_tracy_tp)
	]
	mass_hotkeys = [
		(tl('Mass TP'), GUIKeys.mass_hotkey_mass_tp),
		(tl('XYZ Sync'), GUIKeys.mass_hotkey_xyz_sync), 
		(tl('X Press'), GUIKeys.mass_hotkey_x_press)
	]
	toggles_layout = [[hotkey_button(name, key), gui.Text(tl('Disabled'), key=f'{name}Status', auto_size_text=False, size=(7, 1), text_color=gui_text_color)] for name, key in toggles]
	framed_toggles_layout = gui.Frame(tl('Toggles'), toggles_layout, title_color=gui_text_color)
	hotkeys_layout = [[hotkey_button(name, key)] for name, key in hotkeys]
	framed_hotkeys_layout = gui.Frame(tl('Hotkeys'), hotkeys_layout, title_color=gui_text_color)
	mass_hotkeys_layout = [[hotkey_button(name, key)] for name, key in mass_hotkeys]
	framed_mass_hotkeys_layout = gui.Frame(tl('Mass Hotkeys'), mass_hotkeys_layout, title_color=gui_text_color)

	client_title = gui.Text(tl('Client') + ': ', key='Title', auto_size_text=False, text_color=gui_text_color)

	# TODO: Does it make any sense to translate this? Has more occurences later in the file
	x_pos = gui.Text('x: ', key='x', auto_size_text=False, text_color=gui_text_color)
	y_pos = gui.Text('y: ', key='y', auto_size_text=False, text_color=gui_text_color)
	z_pos = gui.Text('z: ', key='z', auto_size_text=False, text_color=gui_text_color)
	yaw = gui.Text(tl('Yaw') + ': ', key='Yaw', auto_size_text=False, text_color=gui_text_color)

	zone_info = gui.Text(tl('Zone') + ': ', key='Zone', auto_size_text=False, size=(62, 1), text_color=gui_text_color)

	copy_pos = hotkey_button(tl('Copy Position'), GUIKeys.copy_position)
	copy_zone = hotkey_button(tl('Copy Zone'), GUIKeys.copy_zone)
	copy_yaw = hotkey_button(tl('Copy Rotation'), GUIKeys.copy_rotation)
	tok_print = hotkey_button(tl('Print Tokens'), GUIKeys.button_token_print)

	client_info_layout = [
		[client_title],
		[zone_info],
		[x_pos],
		[y_pos],
		[z_pos],
		[yaw]
	]

	utils_layout = [
		[copy_zone],
		[copy_pos],
		[copy_yaw],
		[tok_print]
	]

	framed_utils_layout = gui.Frame(tl('Utils'), utils_layout, title_color=gui_text_color)

	dev_utils_notice = tl('The utils below are for advanced users and no support will be given on them.')

	custom_tp_layout = [
		[gui.Text(dev_utils_notice, text_color=gui_text_color)],
		[
			gui.Text('XYZ:', text_color=gui_text_color), gui.InputText(size=(28, 1), key='XYZInput'),
			#gui.Text('Y:', text_color=gui_text_color), gui.InputText(size=(6, 1), key='YInput'),
			#gui.Text('Z:', text_color=gui_text_color), gui.InputText(size=(7, 1), key='ZInput'),
			gui.Text(tl('Yaw') + ': ', text_color=gui_text_color), gui.InputText(size=(6, 1), key='YawInput'),
			hotkey_button(tl('Custom TP'), GUIKeys.button_custom_tp)
		],
		[
			gui.Text(tl('Entity Name') + ':', text_color=gui_text_color), gui.InputText(size=(36, 1), key='EntityTPInput'),
			hotkey_button(tl('Entity TP'), GUIKeys.button_entity_tp)
		]
	]

	framed_custom_tp_layout = gui.Frame(tl('TP Utils'), custom_tp_layout, title_color=gui_text_color)

	dev_utils_layout = [
		[gui.Text(dev_utils_notice, text_color=gui_text_color)],
		[
			hotkey_button(tl('Available Entities'), GUIKeys.copy_entity_list, True),
			hotkey_button(tl('Available Paths'), GUIKeys.copy_ui_tree, True),
			#hotkey_button(tl('AZ Fish'), GUIKeys.button_az_raid_fish, True),
			#gui.Text(tl('Disabled'), key=f'FishingStatus', auto_size_text=False, size=(7, 1), text_color=gui_text_color),
			#hotkey_button(tl('LM Informer'), GUIKeys.button_lm_informer, True)
		],
		[
			gui.Text(tl('Zone Name') + ':', text_color=gui_text_color), gui.InputText(size=(13, 1), key='ZoneInput'),
			hotkey_button(tl('Go To Zone'), GUIKeys.button_go_to_zone),
			hotkey_button(tl('Mass Go To Zone'), GUIKeys.button_mass_go_to_zone, True)
		],
		[
			gui.Text(tl('World Name') + ':', text_color=gui_text_color),
			# TODO: Come back with some ingenius solution for this
			gui.Combo(
				['WizardCity', 'Krokotopia', 'Marleybone', 'MooShu', 'DragonSpire', 'Grizzleheim', 'Celestia', 'Wysteria', 'Zafaria', 'Avalon', 'Azteca', 'Khrysalis', 'Polaris', 'Mirage', 'Empyrea', 'Karamelle', 'Lemuria'],
				default_value='WizardCity', readonly=True,text_color=gui_text_color, size=(13, 1), key='WorldInput'
			),
			hotkey_button(tl('Go To World'), GUIKeys.button_go_to_world, True),
			hotkey_button(tl('Mass Go To World'), GUIKeys.button_mass_go_to_world, True)
		],
		[
			hotkey_button(tl('Go To Bazaar'), GUIKeys.button_go_to_bazaar, True),
			hotkey_button(tl('Mass Go To Bazaar'), GUIKeys.button_mass_go_to_bazaar, True),
			hotkey_button(tl('Refill Potions'), GUIKeys.button_refill_potions, True),
			hotkey_button(tl('Mass Refill Potions'), GUIKeys.button_mass_refill_potions, True)
		]
	]

	framed_dev_utils_layout = gui.Frame(tl('Dev Utils'), dev_utils_layout, title_color=gui_text_color)

	camera_controls_layout = [
		[gui.Text(dev_utils_notice, text_color=gui_text_color)],
		[
			gui.Text('X:', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamXInput'),
			gui.Text('Y:', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamYInput'),
			gui.Text('Z:', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamZInput'),
			hotkey_button(tl('Set Camera Position'), GUIKeys.button_set_camera_position, True)
		],
		[
			gui.Text(tl('Yaw') + ':', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamYawInput'),
			gui.Text(tl('Roll') + ':', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamRollInput'),
			gui.Text(tl('Pitch') + ':', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamPitchInput')
		],
		[
			gui.Text(tl('Entity') + ':', text_color=gui_text_color), gui.InputText(size=(18, 1), key='CamEntityInput'),
			hotkey_button(tl('Camera TP'), GUIKeys.button_camera_tp, True, text_color=gui_text_color),
			hotkey_button(tl('Anchor'), GUIKeys.button_anchor, True, text_color=gui_text_color),
			hotkey_button(tl('Toggle Camera Collision'), GUIKeys.toggle_camera_collision, True)
		],
		[
			gui.Text(tl('Distance') + ':', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamDistanceInput'),
			gui.Text(tl('Min') + ':', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamMinInput'),
			gui.Text(tl('Max') + ':', text_color=gui_text_color), gui.InputText(size=(10, 1), key='CamMaxInput'),
			hotkey_button(tl('Set Distance'), GUIKeys.button_set_distance, True)
		],
		[
			hotkey_button(tl('Copy Camera Position'), GUIKeys.copy_camera_position, True),
			hotkey_button(tl('Copy Camera Rotation'), GUIKeys.copy_camera_rotation, True),
		],
		[
			gui.Text(tl('FOV') + ':', text_color=gui_text_color), gui.InputText(size=(18, 1), key='FOVInput'),
			hotkey_button(tl('FOV Loop'), GUIKeys.toggle_fov_loop, True),
			gui.Text(tl('Disabled'), key=f'FOVStatus', auto_size_text=False, size=(7, 1), text_color=gui_text_color)
		]
	]

	framed_camera_controls_layout = gui.Frame(tl('Camera Controls'), camera_controls_layout, title_color=gui_text_color)

	stat_viewer_layout = [
		[
            gui.Combo([i + 1 for i in range(12)], text_color=gui_text_color, size=(21, 1), default_value=1, key='IndexInput', readonly=True), 
            hotkey_button(tl('View Stats'), GUIKeys.button_view_stats, True), 
            hotkey_button(tl('Copy Stats'), GUIKeys.copy_stats, True)
        ],
		[gui.Multiline(tl('No client has been selected.'), key='stat_viewer', size=(66, 10), text_color=gui_text_color, horizontal_scroll=True)],
        [gui.Multiline(tl('No client has been selected.'), key='every_hp', size=(66, 2), text_color=gui_text_color, horizontal_scroll=True)],
	]

	framed_stat_viewer_layout = gui.Frame(tl('Stat Viewer'), stat_viewer_layout, title_color=gui_text_color)

	flythrough_layout = [
		[gui.Text(dev_utils_notice, text_color=gui_text_color)],
		[gui.Multiline(key='flythrough_creator', size=(66, 11), text_color=gui_text_color, horizontal_scroll=True)],
		[
			gui.Input(key='flythrough_file_path', visible=False), 
			gui.FileBrowse(tl('Import Flythrough'), file_types=(("Text Files", "*.txt"),), auto_size_button=True, button_color=(gui_text_color, gui_button_color)),
			gui.Input(key='flythrough_save_path', visible=False),
			gui.FileSaveAs(tl('Export Flythrough'), file_types=(("Text Files", "*.txt"),), auto_size_button=True, button_color=(gui_text_color, gui_button_color)),
			hotkey_button(tl('Execute Flythrough'), GUIKeys.button_execute_flythrough, True),
			hotkey_button(tl('Kill Flythrough'), GUIKeys.button_kill_flythrough, True)
			],
	]

	framed_flythrough_layout = gui.Frame(tl('Flythrough Creator'), flythrough_layout, title_color=gui_text_color)

	bot_creator_layout = [
		[gui.Text(dev_utils_notice, text_color=gui_text_color)],
		[gui.Multiline(key='bot_creator', size=(66, 11), text_color=gui_text_color, horizontal_scroll=True)],
		[
			gui.Input(key='bot_file_path', visible=False), 
			gui.FileBrowse('Import Bot', file_types=(("Text Files", "*.txt"),), auto_size_button=True, button_color=(gui_text_color, gui_button_color)),
			gui.Input(key='bot_save_path', visible=False),
			gui.FileSaveAs('Export Bot', file_types=(("Text Files", "*.txt"),), auto_size_button=True, button_color=(gui_text_color, gui_button_color)),
			hotkey_button(tl('Run Bot'), GUIKeys.button_run_bot, True),
			hotkey_button(tl('Kill Bot'), GUIKeys.button_kill_bot, True)
			],
	]

	framed_bot_creator_layout = gui.Frame(tl('Bot Creator'), bot_creator_layout, title_color=gui_text_color)

	combat_config_layout = [
		[gui.Text(dev_utils_notice, text_color=gui_text_color)],
		[gui.Multiline(key='combat_config', size=(66, 11), text_color=gui_text_color, horizontal_scroll=True)],
		[
			gui.Input(key='combat_file_path', visible=False), 
			gui.FileBrowse('Import Playstyle', file_types=(("Text Files", "*.txt"),), auto_size_button=True, button_color=(gui_text_color, gui_button_color)),
			gui.Input(key='combat_save_path', visible=False),
			gui.FileSaveAs('Export Playstyle', file_types=(("Text Files", "*.txt"),), auto_size_button=True, button_color=(gui_text_color, gui_button_color)),
			hotkey_button(tl('Set Playstyles'), GUIKeys.button_set_playstyles, True),
		],
	]

	framed_combat_config_layout = gui.Frame(tl('Combat Configurator'), combat_config_layout, title_color=gui_text_color)

	misc_utils_layout = [
		[gui.Text(dev_utils_notice, text_color=gui_text_color)],
		[
			gui.Text(tl('Scale') + ':', text_color=gui_text_color), gui.InputText(size=(8, 1), key='scale'),
			hotkey_button(tl('Set Scale'), GUIKeys.button_set_scale)
		],
		[gui.Text('Select a pet world:', text_color=gui_text_color), gui.Combo(['WizardCity', 'Krokotopia', 'Marleybone', 'Mooshu', 'Dragonspyre'], default_value='WizardCity', readonly=True,text_color=gui_text_color, size=(13, 1), key='PetWorldInput')], #, hotkey_button('Set Auto Pet World', True) 
	]

	framed_misc_utils_layout = gui.Frame(tl('Misc Utils'), misc_utils_layout, title_color=gui_text_color)

	# VVR_Toggles: list[tuple[str, str]] = [
	# 	(tl('VVR Drums'), GUIKeys.VVR_Drums),
	# ]

	# VVR_toggles_layout = [[hotkey_button(name, key), gui.Text(tl('Disabled'), key=f'{name}Status', auto_size_text=False, size=(7, 1), text_color=gui_text_color)] for name, key in VVR_Toggles]
	# framed_VVR_toggles_layout = gui.Frame(tl('VVR Toggles'), VVR_toggles_layout, title_color=gui_text_color)

	VVR_Hotkeys: list[tuple[str, str]] = [
		(tl('Power Star'), GUIKeys.PowerStarPort),
		(tl('Mana Chest'), GUIKeys.ManaChestPort),
		(tl('Health Chest'), GUIKeys.HealthChestPort),
		(tl('Speed Chest'), GUIKeys.SpeedChestPort),
		(tl('Pet Token TP'), GUIKeys.PetTokenPort),
	]

	VVR_hotkeys_layout = [[hotkey_button(name, key)] for name, key in VVR_Hotkeys]
	framed_VVR_hotkeys_layout = gui.Frame(tl('VVR Hotkeys'), VVR_hotkeys_layout, title_color=gui_text_color)

	CSR_Toggles: list[tuple[str, str]] = [
		(tl('Drums'), GUIKeys.CSRDrums),
		(tl('Cacao Pods'), GUIKeys.CacaoPods),
		(tl('AZ Fish'), GUIKeys.button_az_raid_fish),
		(tl('MF Tears'), GUIKeys.MisfortuneTears),
		(tl('Quetzal Eggs'), GUIKeys.QuetzalEggs),
	]

	CSR_toggles_layout = [[hotkey_button(name, key), gui.Text(tl('Disabled'), key=f'{name}Status', auto_size_text=False, size=(7, 1), text_color=gui_text_color)] for name, key in CSR_Toggles]
	framed_CSR_toggles_layout = gui.Frame(tl('VVR/CSR Toggles'), CSR_toggles_layout, title_color=gui_text_color)

	CSR_Hotkeys: list[tuple[str, str]] = [
		(tl('Center TP'), GUIKeys.CenterPyramid),
		(tl('VOD TP'), GUIKeys.VoiceOfDeath),
		(tl('XE TP'), GUIKeys.XibalbaElemental),
		(tl('West TP'), GUIKeys.WestPortal),
		(tl('East TP'), GUIKeys.EastPortal),
		(tl('Pet Token TP'), GUIKeys.NorthPetToken),
	]

	CSR_hotkeys_layout = [[hotkey_button(name, key)] for name, key in CSR_Hotkeys]


	framed_CSR_hotkeys_layout = gui.Frame(tl('CSR Hotkeys'), CSR_hotkeys_layout, title_color=gui_text_color)

	CRR_Toggles: list[tuple[str, str]] = [
		(tl('Auto Daemon'), GUIKeys.DaemonBalls),
		(tl('Auto Cabalist'), GUIKeys.CabalistBalls),
	]

	CRR_toggles_layout = [[hotkey_button(name, key), gui.Text(tl('Disabled'), key=f'{name}Status', auto_size_text=False, size=(7, 1), text_color=gui_text_color)] for name, key in CRR_Toggles]
	framed_CRR_toggles_layout = gui.Frame(tl('CRR Toggles'), CRR_toggles_layout, title_color=gui_text_color)

	CRR_hotkeys_layout = [[hotkey_button_sized('Rope TP', GUIKeys.RopePort, False, gui_text_color, gui_button_color, (8, 1))],
					   [hotkey_button_sized('NE TP', GUIKeys.NorthEastCatapult, False, gui_text_color, gui_button_color, (8, 1))], 
					   [hotkey_button_sized('NW TP', GUIKeys.NorthWestCatapult, False, gui_text_color, gui_button_color, (8, 1))], 
					   [hotkey_button_sized('SE TP', GUIKeys.SouthEastCatapult, False, gui_text_color, gui_button_color, (8, 1))], 
					   [hotkey_button_sized('SW TP', GUIKeys.SouthWestCatapult, False, gui_text_color, gui_button_color, (8, 1))]]
	framed_CRR_hotkeys_layout = gui.Frame(tl('CRR Hotkeys'), CRR_hotkeys_layout, title_color=gui_text_color)


	GCR_toggles_layout= [[hotkey_button('Wood Tokens', GUIKeys.AutoWoodTokens), gui.Text(tl('Disabled'), key='WoodTokenStatus', auto_size_text=False, size=(7, 1), text_color=gui_text_color), 
gui.Combo(['Snake', 'Spider', 'Crane', 'Butterfly', 'Tree'], default_value='Tree', readonly=True, text_color=gui_text_color, size=(13, 1), key='WoodInput')],
[hotkey_button('Silver Tokens', GUIKeys.AutoSilverTokens), gui.Text(tl('Disabled'), key='SilverTokenStatus', auto_size_text=False, size=(7, 1), text_color=gui_text_color), 
gui.Combo(['Snake', 'Spider', 'Crane', 'Butterfly', 'Tree'], default_value='Tree', readonly=True, text_color=gui_text_color, size=(13, 1), key='SilverInput')],
[hotkey_button('Gold Tokens', GUIKeys.AutoGoldTokens), gui.Text(tl('Disabled'), key='GoldTokenStatus', auto_size_text=False, size=(7, 1), text_color=gui_text_color), 
gui.Combo(['Snake', 'Spider', 'Crane', 'Butterfly', 'Tree'], default_value='Tree', readonly=True, text_color=gui_text_color, size=(13, 1), key='GoldInput')],
[hotkey_button('Forensic', GUIKeys.AutoTracyFoldersForensic), gui.Text(tl('Disabled'), key='ForensicStatus', auto_size_text=False, size=(7, 1), text_color=gui_text_color)],
[hotkey_button('Bomshell', GUIKeys.AutoTracyFoldersBombshell), gui.Text(tl('Disabled'), key='BombshellStatus', auto_size_text=False, size=(7, 1), text_color=gui_text_color)]]
	#GCR_toggles_layout = [[hotkey_button(name, key), gui.Text(tl('Disabled'), key=f'{name}Status', auto_size_text=False, size=(7, 1), text_color=gui_text_color)] for name, key in GCR_Toggles]
	framed_GCR_toggles_layout = gui.Frame(tl('GCR Toggles'), (GCR_toggles_layout), title_color=gui_text_color)

	GCR_Hotkeys: list[tuple[str, str]] = [
		(tl('4v4 Code'), GUIKeys.button_lm_informer),
		(tl('Moth / Flame'), GUIKeys.SendMothAmon),
		(tl('Lucien / Comb'), GUIKeys.SendLucien),
		(tl('Morg / Hair'), GUIKeys.SendMorg),
		(tl('Mime / Props'), GUIKeys.SendMime),
	]

	GCR_hotkeys_layout = [[hotkey_button(name, key)] for name, key in GCR_Hotkeys]
	framed_GCR_hotkeys_layout = gui.Frame(tl('GCR Hotkeys'), GCR_hotkeys_layout, title_color=gui_text_color)

	tabs = [
		[
			gui.Tab(tl('Hotkeys'), [[framed_toggles_layout, framed_hotkeys_layout, framed_mass_hotkeys_layout, framed_utils_layout]], title_color=gui_text_color),
			gui.Tab(tl('Camera'), [[framed_camera_controls_layout]], title_color=gui_text_color),
			gui.Tab(tl('Dev Utils'), [[framed_custom_tp_layout], [framed_dev_utils_layout]], title_color=gui_text_color),
			gui.Tab(tl('Stat Viewer'), [[framed_stat_viewer_layout]], title_color=gui_text_color),
			gui.Tab(tl('Flythrough'), [[framed_flythrough_layout]], title_color=gui_text_color),
			gui.Tab(tl('Bot'), [[framed_bot_creator_layout]], title_color=gui_text_color),
			gui.Tab(tl('Combat'), [[framed_combat_config_layout]], title_color=gui_text_color),
			gui.Tab(tl('Raid'), [[framed_CSR_toggles_layout, framed_GCR_toggles_layout], 
						[framed_VVR_hotkeys_layout, framed_CSR_hotkeys_layout, framed_CRR_hotkeys_layout, framed_GCR_hotkeys_layout]], title_color=gui_text_color),
			gui.Tab(tl('Misc'), [[framed_misc_utils_layout]], title_color=gui_text_color)
		]
	]

	layout = [
		[gui.Text(tl('I am going to touch you'))],
		[gui.TabGroup(tabs)],
		[client_info_layout]
	]

	#window = gui.Window(title= f'{tool_name} GUI v{67}', layout= layout, keep_on_top=gui_on_top, icon="...\\Deimos-logo.ico", finalize=True)
	window = gui.Window(title= f'Hunter Client', layout= layout, keep_on_top=gui_on_top, icon="...\\Deimos-logo.ico", finalize=True)
	return window

def show_ui_tree_popup(ui_tree_content):
    ui_tree_list = ui_tree_content.splitlines()

    path_dict = {}
    path_stack = []

    for line in ui_tree_list:
        indent = len(line) - len(line.lstrip('-'))
        clean_line = line.lstrip('- ')
        
        name_match = re.search(r'\[(.*?)\]', clean_line)
        if name_match:
            name = name_match.group(1)
        else:
            name = clean_line.split()[0]  # Fallback to the first word if no brackets

        while len(path_stack) > indent:
            path_stack.pop()
        
        current_path = path_stack.copy()
        current_path.append(name)
        
        path_dict[line] = current_path[1:] if len(current_path) > 1 else current_path
        path_stack.append(name)

    layout = [
        [gui.Text('Click the path needed to copy it to clipboard.')],
        [gui.Listbox(values=ui_tree_list, size=(80, 20), key='-TREE-', enable_events=True)],
        [gui.Input(key='-SEARCH-', enable_events=True)],
        [gui.Button('Close')]
    ]
    UITreeWindow = gui.Window('UI Tree', layout, finalize=True, icon="..\\Deimos-logo.ico")

    while True:
        event, values = UITreeWindow.read()
        if event == gui.WINDOW_CLOSED or event == 'Close':
            break
        elif event == '-SEARCH-':
            search_term = values['-SEARCH-'].lower()
            filtered_list = [line for line in ui_tree_list if search_term in line.lower()]
            UITreeWindow['-TREE-'].update(filtered_list)
        elif event == '-TREE-' and values['-TREE-']:
            selected_line = values['-TREE-'][0]
            path = path_dict[selected_line]
            UITreeWindow.close() 
            path_str = str(path)
            pyperclip.copy(path_str)
            return path_str

    UITreeWindow.close()

def show_entity_list_popup(entity_list_content):
    entity_list = entity_list_content.splitlines()

    layout = [
        [gui.Text('Click the entity needed to copy the name and location to clipboard.')],
        [gui.Listbox(values=entity_list, size=(80, 20), key='-TREE-', enable_events=True)],
        [gui.Input(key='-SEARCH-', enable_events=True)],
        [gui.Button('Close')]
    ]
    EntityListWindow = gui.Window('Entity List', layout, finalize=True, icon="..\\Deimos-logo.ico")

    while True:
        event, values = EntityListWindow.read()
        if event == gui.WINDOW_CLOSED or event == 'Close':
            break
        elif event == '-SEARCH-':
            search_term = values['-SEARCH-'].lower()
            filtered_list = [line for line in entity_list if search_term in line.lower()]
            EntityListWindow['-TREE-'].update(filtered_list)
        elif event == '-TREE-' and values['-TREE-']:
            selected_line = values['-TREE-'][0]
            EntityListWindow.close()
            pyperclip.copy(selected_line)
            return selected_line

    EntityListWindow.close()

def manage_gui(send_queue: queue.Queue, recv_queue: queue.Queue, gui_theme, gui_text_color, gui_button_color, tool_name, tool_version, gui_on_top, langcode):
	window = create_gui(gui_theme, gui_text_color, gui_button_color, tool_name, tool_version, gui_on_top, langcode)

	running = True

	while running:
		global inputs
		event, inputs = window.read(timeout=10)
		# print(inputs)

		# Program commands
		try:
			# Eat as much as the queue gives us. We will be freed by exception
			while True:
				com = recv_queue.get_nowait()
				match com.com_type:
					case GUICommandType.Close:
						running = False

					case GUICommandType.UpdateWindow:
						window[com.data[0]].update(com.data[1])

					case GUICommandType.UpdateWindowValues:
						window[com.data[0]].update(values=com.data[1])

					case GUICommandType.ShowUITreePopup:
						show_ui_tree_popup(com.data)

					case GUICommandType.ShowEntityListPopup:
						show_entity_list_popup(com.data)
						
		except queue.Empty:
			pass

		# Window events
		match event:
			case gui.WINDOW_CLOSED:
				running = False
				send_queue.put(GUICommand(GUICommandType.Close))

			case gui.WINDOW_CLOSE_ATTEMPTED_EVENT:
				running = False
				send_queue.put(GUICommand(GUICommandType.Close))

			# Toggles
			case GUIKeys.toggle_speedhack | GUIKeys.toggle_combat | GUIKeys.toggle_dialogue | GUIKeys.toggle_sigil | \
				GUIKeys.toggle_questing | GUIKeys.toggle_auto_pet | GUIKeys.toggle_auto_potion | GUIKeys.toggle_freecam | \
				GUIKeys.toggle_camera_collision | GUIKeys.VVR_Drums | GUIKeys.MisfortuneTears | GUIKeys.CacaoPods | \
				GUIKeys.CSRDrums | GUIKeys.QuetzalEggs | GUIKeys.AutoTracyFoldersForensic | GUIKeys.AutoTracyFoldersBombshell: 
				send_queue.put(GUICommand(GUICommandType.ToggleOption, event))
			
			# GCR Tokens
			case GUIKeys.AutoWoodTokens:
				send_queue.put(GUICommand(GUICommandType.AutoWoodTokens, inputs["WoodInput"]))

			case GUIKeys.AutoSilverTokens:
				send_queue.put(GUICommand(GUICommandType.AutoSilverTokens, inputs["SilverInput"]))

			case GUIKeys.AutoGoldTokens:
				send_queue.put(GUICommand(GUICommandType.AutoGoldTokens, inputs["GoldInput"]))


			# Copying
			case GUIKeys.copy_zone | GUIKeys.copy_position | GUIKeys.copy_rotation | \
				GUIKeys.copy_entity_list | GUIKeys.copy_camera_position | \
				GUIKeys.copy_camera_rotation | GUIKeys.copy_ui_tree | GUIKeys.copy_stats:
				send_queue.put(GUICommand(GUICommandType.Copy, event))

            # Token Printer
			case GUIKeys.button_token_print:
				send_queue.put(GUICommand(GUICommandType.TokenPrinter))

			# Simple teleports
			case GUIKeys.hotkey_quest_tp | GUIKeys.mass_hotkey_mass_tp | GUIKeys.hotkey_freecam_tp:
				send_queue.put(GUICommand(GUICommandType.Teleport, event))


			# Custom tp
			case GUIKeys.button_custom_tp:
				tp_inputs = [inputs['XYZInput'], inputs['YawInput']]
				if any(tp_inputs):
					send_queue.put(GUICommand(GUICommandType.CustomTeleport, {
						'XYZ': tp_inputs[0],
						'Yaw': tp_inputs[1],
					}))

			# Entity tp
			case GUIKeys.button_entity_tp:
				if inputs['EntityTPInput']:
					send_queue.put(GUICommand(GUICommandType.EntityTeleport, inputs['EntityTPInput']))

			# XYZ Sync
			case GUIKeys.mass_hotkey_xyz_sync:
				send_queue.put(GUICommand(GUICommandType.XYZSync))

			# X Press
			case GUIKeys.mass_hotkey_x_press:
				send_queue.put(GUICommand(GUICommandType.XPress))

			# Cam stuff
			case GUIKeys.button_camera_tp:
				if inputs['CamEntityInput']:
					send_queue.put(GUICommand(GUICommandType.SetCamToEntity, inputs['CamEntityInput']))
            
			case GUIKeys.button_anchor:
				send_queue.put(GUICommand(GUICommandType.AnchorCam, inputs['CamEntityInput']))

			case GUIKeys.button_set_camera_position:
				camera_inputs = [inputs['CamXInput'], inputs['CamYInput'], inputs['CamZInput'], inputs['CamYawInput'], inputs['CamRollInput'], inputs['CamPitchInput']]
				if any(camera_inputs):
					send_queue.put(GUICommand(GUICommandType.SetCamPosition, {
						'X': camera_inputs[0],
						'Y': camera_inputs[1],
						'Z': camera_inputs[2],
						'Yaw': camera_inputs[3],
						'Roll': camera_inputs[4],
						'Pitch': camera_inputs[5],
					}))

			case GUIKeys.toggle_fov_loop:
				if inputs['FOVInput']:
					#print(f"{type(inputs['FOVInput'])}: {inputs['FOVInput']}")
					send_queue.put(GUICommand(GUICommandType.ToggleFOVLoop, inputs['FOVInput']))
				else:
					send_queue.put(GUICommand(GUICommandType.ToggleFOVLoop, None))

			case GUIKeys.button_set_distance:
				distance_inputs = [inputs['CamDistanceInput'], inputs['CamMinInput'], inputs['CamMaxInput']]
				if any(distance_inputs):
					send_queue.put(GUICommand(GUICommandType.SetCamDistance, {
						"Distance": distance_inputs[0],
						"Min": distance_inputs[1],
						"Max": distance_inputs[2],
					}))

			# Gotos
			case GUIKeys.button_go_to_zone:
				if inputs['ZoneInput']:
					send_queue.put(GUICommand(GUICommandType.GoToZone, (False, str(inputs['ZoneInput']))))

			case GUIKeys.button_mass_go_to_zone:
				if inputs['ZoneInput']:
					send_queue.put(GUICommand(GUICommandType.GoToZone, (True, str(inputs['ZoneInput']))))

			case GUIKeys.button_go_to_world:
				if inputs['WorldInput']:
					send_queue.put(GUICommand(GUICommandType.GoToWorld, (False, inputs['WorldInput'])))

			case GUIKeys.button_mass_go_to_world:
				if inputs['WorldInput']:
					send_queue.put(GUICommand(GUICommandType.GoToWorld, (True, inputs['WorldInput'])))

			case GUIKeys.AutoWoodTokens:
				send_queue.put(GUICommand(GUICommandType.AutoWoodTokens, inputs['WoodInput']))

			case GUIKeys.button_go_to_bazaar:
				send_queue.put(GUICommand(GUICommandType.GoToBazaar, False))

			case GUIKeys.button_mass_go_to_bazaar:
				send_queue.put(GUICommand(GUICommandType.GoToBazaar, True))

			case GUIKeys.button_refill_potions:
				send_queue.put(GUICommand(GUICommandType.RefillPotions, False))

			case GUIKeys.button_mass_refill_potions:
				send_queue.put(GUICommand(GUICommandType.RefillPotions, True))

			case GUIKeys.button_execute_flythrough:
				send_queue.put(GUICommand(GUICommandType.ExecuteFlythrough, inputs['flythrough_creator']))

			case GUIKeys.button_kill_flythrough:
				send_queue.put(GUICommand(GUICommandType.KillFlythrough))

			case GUIKeys.button_run_bot:
				send_queue.put(GUICommand(GUICommandType.ExecuteBot, inputs['bot_creator']))

			case GUIKeys.button_az_raid_fish:
				send_queue.put(GUICommand(GUICommandType.AzRaidFish))
            
			case GUIKeys.button_lm_informer:
				send_queue.put(GUICommand(GUICommandType.LmInformer))
            
			case GUIKeys.button_wood_chest_tp:
				send_queue.put(GUICommand(GUICommandType.WoodChestTp))
                
			case GUIKeys.button_silver_chest_tp:
				send_queue.put(GUICommand(GUICommandType.SilverChestTp))
            
			case GUIKeys.button_gold_chest_tp:
				send_queue.put(GUICommand(GUICommandType.GoldChestTp))
            
			case GUIKeys.button_dog_tracy_tp:
				send_queue.put(GUICommand(GUICommandType.DogTracyTp))

			case GUIKeys.ManaChestPort:
				send_queue.put(GUICommand(GUICommandType.ManaChestPort))

			case GUIKeys.HealthChestPort:
				send_queue.put(GUICommand(GUICommandType.HealthChestPort))

			case GUIKeys.SpeedChestPort:
				send_queue.put(GUICommand(GUICommandType.SpeedChestPort))

			case GUIKeys.PowerStarPort:
				send_queue.put(GUICommand(GUICommandType.PowerStarPort))

			case GUIKeys.PetTokenPort:
				send_queue.put(GUICommand(GUICommandType.PetTokenPort))

			case GUIKeys.CenterPyramid:
				send_queue.put(GUICommand(GUICommandType.CenterPyramid))

			case GUIKeys.VoiceOfDeath:
				send_queue.put(GUICommand(GUICommandType.VoiceOfDeath))

			case GUIKeys.XibalbaElemental:
				send_queue.put(GUICommand(GUICommandType.XibalbaElemental))

			case GUIKeys.WestPortal:
				send_queue.put(GUICommand(GUICommandType.WestPortal))

			case GUIKeys.EastPortal:
				send_queue.put(GUICommand(GUICommandType.EastPortal))

			case GUIKeys.NorthPetToken:
				send_queue.put(GUICommand(GUICommandType.NorthPetToken))

			case GUIKeys.RopePort:
				send_queue.put(GUICommand(GUICommandType.RopePort))

			case GUIKeys.NorthEastCatapult:
				send_queue.put(GUICommand(GUICommandType.NorthEastCatapult))

			case GUIKeys.NorthWestCatapult:
				send_queue.put(GUICommand(GUICommandType.NorthWestCatapult))

			case GUIKeys.SouthEastCatapult:
				send_queue.put(GUICommand(GUICommandType.SouthEastCatapult))

			case GUIKeys.SouthWestCatapult:
				send_queue.put(GUICommand(GUICommandType.SouthWestCatapult))

			case GUIKeys.DaemonBalls:
				send_queue.put(GUICommand(GUICommandType.DaemonBalls))

			case GUIKeys.CabalistBalls:
				send_queue.put(GUICommand(GUICommandType.CabalistBalls))

			case GUIKeys.AutoSilverTokens:
				send_queue.put(GUICommand(GUICommandType.SilverTokens, inputs['SilverInput']))

			case GUIKeys.AutoGoldTokens:
				send_queue.put(GUICommand(GUICommandType.GoldTokens, inputs['GoldInput']))

			case GUIKeys.SendMothAmon:
				send_queue.put(GUICommand(GUICommandType.SendMothAmon))

			case GUIKeys.SendLucien:
				send_queue.put(GUICommand(GUICommandType.SendLucien))

			case GUIKeys.SendMorg:
				send_queue.put(GUICommand(GUICommandType.SendMorg))

			case GUIKeys.SendMime:
				send_queue.put(GUICommand(GUICommandType.SendMime))

			case GUIKeys.button_set_playstyles:
				send_queue.put(GUICommand(GUICommandType.SetPlaystyles, inputs["combat_config"]))

			case GUIKeys.button_kill_bot:
				send_queue.put(GUICommand(GUICommandType.KillBot))

			case GUIKeys.button_set_scale:
				send_queue.put(GUICommand(GUICommandType.SetScale, inputs['scale']))

			case GUIKeys.button_view_stats:
				index = re.sub(r'[^0-9]', '', str(inputs['IndexInput']))
				send_queue.put(GUICommand(GUICommandType.SelectEnemy, (int(index))))

			# case 'Set Auto Pet World':
			# 	if inputs['PetWorldInput']:
			# 		send_queue.put(GUICommand(GUICommandType.SetPetWorld, (False, str(inputs['PetWorldInput']))))

			# Other
			case _:
				pass

		#Updates pet world when it changes, without the need for a button press -slack
		if inputs and inputs['PetWorldInput'] != wizard_city_dance_game_path[-1]:
			assign_pet_level(inputs['PetWorldInput'])

		def import_check(input_window_str: str, output_window_str: str):
			if inputs and inputs[input_window_str]:
				with open(inputs[input_window_str]) as file:
					file_data = file.readlines()
					file_str = ''.join(file_data)
					window[output_window_str].update(file_str)
					window[input_window_str].update('')
					file.close()

		def export_check(path_window_str: str, content_window_str: str):
			if inputs and inputs[path_window_str]:
				file = open(inputs[path_window_str], 'w')
				file.write(inputs[content_window_str])
				file.close()
				window[path_window_str].update('')

		import_check('flythrough_file_path', 'flythrough_creator')
		export_check('flythrough_save_path', 'flythrough_creator')

		import_check('bot_file_path', 'bot_creator')
		export_check('bot_save_path', 'bot_creator')

		import_check('combat_file_path', 'combat_config')
		export_check('combat_save_path', 'combat_config')

	window.close()
