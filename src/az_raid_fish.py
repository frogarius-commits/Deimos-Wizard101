import asyncio
from time import time

from wizwalker import ClientHandler, Client, Keycode
from wizwalker.memory import MemoryReader, Window
from wizwalker.memory.memory_objects.fish import Fish, FishStatusCode
from loguru import logger
from typing import Union, List





# Specifications ####################################
IS_CHEST = True                         #
SCHOOL = "Any" # "Any" means you don't care         #
RANK = 0  # 0 means you don't care                  #
ID = 0 # 0 means you don't care                     #
SIZE_MIN = 0 # 0 means you don't care               #
SIZE_MAX = 999 # big number means you don't care    #
#####################################################

async def window_exists(client, window_name: str, *, check_if_visible=True):
    w = await client.root_window.get_windows_with_name(window_name)
    if check_if_visible:
        return len(w) > 0 and await w[0].is_visible()
    else:
        return len(w) > 0

async def wait_for_window(client, window_name, *, timeout=10, check_if_visible=True):
    start = time()
    while not await window_exists(client, window_name, check_if_visible=check_if_visible):
        if time() - start >= timeout:
            break

async def wait_to_click_window_with_name(client: Client, window_name: str, *, timeout=10, check_if_visible=True):
    await wait_for_window(client, window_name, timeout=timeout, check_if_visible=check_if_visible)
    await asyncio.sleep(0.1)
    async with client.mouse_handler:
        await client.mouse_handler.click_window_with_name(window_name)

async def sell_basket(client: Client):
    await client.send_key(Keycode.V)
    while await window_exists(client, "Trash", check_if_visible=True):
        while not (await window_exists(client, "centerButton")):
            try:
                async with client.mouse_handler:
                    await client.mouse_handler.click_window_with_name("Trash")
            except ValueError:
                await asyncio.sleep(0.1)

        while await window_exists(client, "centerButton"):
            try:
                async with client.mouse_handler:
                    await client.mouse_handler.click_window_with_name("centerButton")
            except ValueError:
                await asyncio.sleep(0.1)

    await client.send_key(Keycode.V)

async def fetch_fish_list(fishing_manager):
    while True:
        try:
            return await fishing_manager.fish_list()
        except RuntimeError:
            await asyncio.sleep(0.1)

async def banish_config(fishing_manager):
    kept_fish = []
    fish_schools = {"Fire": 0, "Storm": 0, "Myth": 0, "Death": 0, "Ice": 0}
    for fish in await fetch_fish_list(fishing_manager):
        fish_temp = await fish.template()
        fish_is_accepted = True
        
        school = await fish_temp.school_name()
        
        if school not in fish_schools.keys():
            fish_is_accepted = False

        else:
            if fish_schools[school] >= 5:
                fish_is_accepted = False
            else:
                fish_schools[school] += 1

        if not fish_is_accepted:
            await fish.write_status_code(FishStatusCode.escaped)
        else:
            kept_fish.append(fish)
    return kept_fish

async def refresh_pond(client, fishing_manager):
    fish_list = await banish_config(fishing_manager)
    while len(fish_list) == 0:
        fish_windows = await client.root_window.get_windows_with_name("FishingWindow")
        while len(fish_windows) == 0:
            async with client.mouse_handler:
                await client.mouse_handler.click_window_with_name("OpenFishingButton")
            fish_windows = await client.root_window.get_windows_with_name("FishingWindow")
            await asyncio.sleep(0.2)
        fish_window: Window = fish_windows[0]
        fish_sub_window = await fish_window.get_child_by_name("FishingSubWindow")
        bottomframe = await fish_sub_window.get_child_by_name("BottomFrame")
        icon2 = await bottomframe.get_child_by_name("Icon2")
        async with client.mouse_handler:
            await client.mouse_handler.click_window(icon2)

        while True:
            try:
                if len(await fetch_fish_list(fishing_manager)) > 0:
                    break
            except RuntimeError:
                await asyncio.sleep(0.1)
        await asyncio.sleep(.5)
        fish_list = await banish_config(fishing_manager)

async def run_fish(wiz_cli):
    #handler = ClientHandler()
    client = wiz_cli
    try:
        print("Preparing")
        #await client.activate_hooks()
        #await client.mouse_handler.activate_mouseless()
        #address_bytes = await patch(client)
        print("Ready for Fish")

        fishing_manager = await client.game_client.fishing_manager()
        fish_caught = 0
        total = time()
        while True:
            start = time()
            #await refresh_pond(client, fishing_manager)
            fish_list = await banish_config(fishing_manager)
            if len(fish_list) == 0:
                break


            # Press Icon 1 (Lure)
            fish_windows = await client.root_window.get_windows_with_name("FishingWindow")

            while len(fish_windows) == 0:
                async with client.mouse_handler:
                    await client.mouse_handler.click_window_with_name("OpenFishingButton")
                fish_windows = await client.root_window.get_windows_with_name("FishingWindow")

            fish_window: Window = fish_windows[0]
            fish_sub_window = await fish_window.get_child_by_name("FishingSubWindow")
            bottomframe = await fish_sub_window.get_child_by_name("BottomFrame")
            icon1 = await bottomframe.get_child_by_name("Icon1")
            async with client.mouse_handler:
                await client.mouse_handler.click_window(icon1)
        
        

            # Check if fish hooked
            is_hooked = False
            basket_full = False
            while not is_hooked:
                if await window_exists(client, "MessageBoxModalWindow"):
                    await wait_to_click_window_with_name(client, "rightButton")
                    await sell_basket(client)
                    basket_full = False
                    break

                fish_list = await fetch_fish_list(fishing_manager)
                statuses = await asyncio.gather(*[fish.status_code() for fish in fish_list])
                for status in statuses:
                    if status == FishStatusCode.unknown2:
                        is_hooked = True
                        break
            
            if basket_full:
                continue

            # Invoke
            await client.send_key(Keycode.SPACEBAR)


            # Clear Fish Caught menu
            fish_failed = False
            timeout = time()
            while len(await client.root_window.get_windows_with_name("CaughtFishModalWindow")) == 0:
                if time() - timeout >= 10:
                    fish_failed = True
                    break
            
            if fish_failed:
                continue

            while len(await client.root_window.get_windows_with_name("CaughtFishModalWindow")) > 0:
                #caught_window: Window = (await client.root_window.get_windows_with_name("CaughtFishModalWindow"))[0]
                #caught_fish = await caught_window.get_child_by_name("CaughtFish")
                #exit_button = await caught_fish.get_child_by_name("exit")
                #async with client.mouse_handler:
                #    await client.mouse_handler.click_window(exit_button)
                await client.send_key(Keycode.SPACEBAR)
                await asyncio.sleep(0.1)

            fish_caught += 1
            
            # Empty Basket
            if fish_caught % 100 == 0 and not IS_CHEST:
                await sell_basket(client)

            total_time = round((time() - total) / 60, 2)
            print(f"Fish Caught: {fish_caught}, Number of fish in pool: {len(fish_list) - 1}, Time: {total_time} minutes, Seconds per fish: {round((total_time / fish_caught) * 60, 2)}")

    finally:
        #if address_bytes:
        #    await reset_patch(client, address_bytes)
        print("Closing")
        #await handler.close()


#if __name__ == "__main__":
#    asyncio.run(main())
