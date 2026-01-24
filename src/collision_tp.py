import asyncio
import inspect
import math
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Coroutine, Sequence, Union, List

# Added import for keyboard listening
from loguru import logger
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union, nearest_points

from wizwalker import Client, XYZ
from src.collision import get_collision_data, CollisionWorld, ProxyType
from src.collision_math import toCubeVertices, transformCube


async def _load_and_build_collision_geometry(client: Client, z_slice: float, debug: bool = False) -> tuple[
    CollisionWorld, List[Polygon], List[Polygon]]:
    """Loads raw collision data and builds 2D polygon shapes for static geometry."""
    raw = await get_collision_data(client)
    world = CollisionWorld()
    world.load(raw)

    if debug:
        print("Static collision objects in this zone:")
        for obj in world.objects:
            print(f"  {obj.proxy.name:8s} '{obj.name}' at {obj.location} params={obj.params}")
        print("─" * 60)

    coll_shapes = build_collision_shapes(world, z_slice, debug=debug)
    mesh_shapes = build_mesh_shapes(world, z_slice)
    return world, coll_shapes, mesh_shapes


async def _get_entity_collision_shapes(client: Client, static_body_radius: float) -> List[Polygon]:
    """
    Gets entities and approximates their collision shapes as circles.
    Uses a dynamic radius for 'CharacterBody' and a static default radius for ALL other types.
    """
    logger.info("Getting dynamic entity collision shapes...")
    entity_shapes = []
    try:
        entity_list = await client.get_base_entity_list()
        for entity in entity_list:
            entity_name = await entity.object_name()
            if entity_name == "Player Object":
                continue

            entity_loc = await entity.location()
            entity_radius = 0.0

            # NEW LOGIC: Default to static radius unless it's a character.
            actor_body = await entity.actor_body()

            # Check for actor_body and if its type is CharacterBody
            if actor_body and await actor_body.read_type_name() == "CharacterBody":
                entity_height = await actor_body.height()
                entity_scale = await actor_body.scale()
                entity_radius = entity_height * entity_scale * 0.5
                #logger.debug(f"Calculating dynamic radius for '{entity_name}' (CharacterBody): {entity_radius:.2f}")
            else:
                # Apply static radius to ALL other cases (StaticBody, bodiless ClientObjects, etc.)
                entity_radius = static_body_radius
                #actor_type_str = await actor_body.read_type_name() if actor_body else "None"
                #logger.debug(
                    #f"Applying static radius for '{entity_name}' (Type: {actor_type_str}): {entity_radius:.2f}")

            if entity_radius > 0:
                entity_shapes.append(Point(entity_loc.x, entity_loc.y).buffer(entity_radius))

    except Exception as e:
        logger.error(f"An error occurred while getting entity collision shapes: {e}", exc_info=True)

    logger.success(f"Generated {len(entity_shapes)} collision shapes from dynamic entities.")
    return entity_shapes


async def _perform_single_teleport_attempt(
        client: Client,
        free_area: Union[Polygon, MultiPolygon],
        target: XYZ,
        bounds: tuple,
) -> bool:
    """Performs a single, non-looping teleport attempt and verifies the result."""
    player_radius = 44.2 #44.2
    minx, miny, maxx, maxy = bounds

    if not free_area or free_area.is_empty:
        logger.error("Free area is empty, cannot calculate a safe region.")
        return False

    safe_region = free_area.buffer(-player_radius)
    if not safe_region or safe_region.is_empty:
        logger.error("Safe region is empty after buffering. Cannot find a teleport point.")
        return False

    _, pt2 = nearest_points(Point(target.x, target.y), safe_region)
    safe_pt = XYZ(pt2.x, pt2.y, target.z)
    logger.info(f"Calculated candidate safe_pt: {safe_pt}")

    cx = min(max(safe_pt.x, minx), maxx)
    cy = min(max(safe_pt.y, miny), maxy)
    safe_pt = XYZ(cx, cy, safe_pt.z)
    logger.info(f"Clamped safe_pt to instance bounds: {safe_pt}")

    await client.teleport(safe_pt)

async def WorldsCollideTP(
        client: Client,
        target: XYZ,
        static_body_radius: float = 75.0,
        debug: bool = False
):
    """
    Handles teleportation to a quest target by calculating a safe path around ALL collision geometry,
    including dynamic entities.
    """
    player_pos = await client.body.position()
    logger.info(f"Player position: {player_pos}")
    logger.info(f"Target: {target}")

    world, static_coll_shapes, mesh_shapes = await _load_and_build_collision_geometry(client, target.z, debug)
    entity_coll_shapes = await _get_entity_collision_shapes(client, static_body_radius)

    all_coll_shapes = static_coll_shapes + entity_coll_shapes

    union_all_coll = unary_union(all_coll_shapes) if all_coll_shapes else Polygon()
    union_mesh = unary_union(mesh_shapes) if mesh_shapes else Polygon()

    free_area = union_mesh.difference(union_all_coll)

    bounds_geom = union_mesh if not union_mesh.is_empty else union_all_coll
    if bounds_geom.is_empty:
        logger.error("No geometry (mesh or collision) found to define zone boundaries. Aborting.")
        return
    bounds = bounds_geom.bounds

    player_radius = 100

    player_at_target = Point(target.x, target.y).buffer(player_radius)

    if not union_all_coll.intersects(player_at_target):
        await client.teleport(target)
        return

    await _perform_single_teleport_attempt(
        client, free_area, target, bounds
    )


def build_collision_shapes(world: CollisionWorld, z_slice: float, debug: bool = False) -> List[Polygon]:
    shapes = []
    if debug:
        print("--- Starting to build collision shapes ---")

    for i, obj in enumerate(world.objects):
        try:
            if obj.proxy == ProxyType.BOX:
                l, w, h = obj.params.length, obj.params.width, obj.params.depth
                if obj.location[2] - h / 2 <= z_slice <= obj.location[2] + h / 2:
                    verts = toCubeVertices((l, w, h))
                    world_pts = transformCube(verts, obj.location, obj.rotation)
                    pts2d = [(p[0], p[1]) for p in world_pts]
                    if len(pts2d) >= 3:
                        shapes.append(Polygon(pts2d).convex_hull)

            elif obj.proxy == ProxyType.SPHERE:
                scale_val = obj.scale if isinstance(obj.scale, (float, int)) else obj.scale[0]
                r = obj.params.radius * scale_val
                if r > 0 and abs(z_slice - obj.location[2]) <= r:
                    shapes.append(Point(obj.location[0], obj.location[1]).buffer(r))

            elif obj.proxy == ProxyType.CYLINDER:
                if isinstance(obj.scale, (float, int)):
                    scale_xy, scale_z = obj.scale, obj.scale
                else:
                    scale_xy, scale_z = obj.scale[0], obj.scale[2]

                scaled_half_length = (obj.params.length / 2) * scale_z
                scaled_radius = obj.params.radius * scale_xy * 0.125
                if scaled_radius > 0 and obj.location[2] - scaled_half_length <= z_slice <= obj.location[
                    2] + scaled_half_length:
                    shapes.append(Point(obj.location[0], obj.location[1]).buffer(scaled_radius))

        except Exception as e:
            print(f"  - ERROR processing object {i} ('{obj.name}'): {e}")
            continue

    if debug:
        print("\n--- Finished building collision shapes ---")
    return shapes


def build_mesh_shapes(world: CollisionWorld, z_slice: float) -> List[Polygon]:
    shapes = []
    for obj in world.objects:
        if obj.proxy == ProxyType.MESH:
            pts3d = transformCube(obj.vertices, obj.location, obj.rotation)
            pts2d = [(x, y) for x, y, z in pts3d]
            if len(pts2d) >= 3:
                shapes.append(Polygon(pts2d).convex_hull)
    return shapes


# await WorldsCollideTP(
#     client,
#     player_radius_offset=0.5,
#     static_body_radius=75.0,  # Tune this value for non-character objects
#     debug=False
# )
