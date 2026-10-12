#!/usr/bin/env python3
"""Turn converted Tabula poses into clips on the original rest rig.

Timing is an adaptation, not recovered Java animator timing. Reject incompatible
hierarchies or meshes instead of silently animating the wrong rig.
"""
import json
import math
from pathlib import Path


def load_geometry(path):
    return json.loads(Path(path).read_text())["minecraft:geometry"][0]


def delta(a, b):
    return [round(x-y, 6) for x, y in zip(a, b)]


def mesh_signature(bone):
    pivot = bone.get("pivot", [0, 0, 0])
    return [(c.get("size"), c.get("uv"), c.get("mirror", False),
             delta(c["origin"], pivot)) for c in bone.get("cubes", [])]


def convert(rest, poses, name, seconds=1.2, loop=True):
    if not poses or seconds <= 0 or not math.isfinite(seconds):
        raise ValueError("A positive finite duration and at least one pose are required")
    bones = {b["name"]: b for b in rest["bones"]}
    if len(bones) != len(rest["bones"]):
        raise ValueError("Duplicate rest bone")
    frames = []
    for pose in poses:
        frame = {b["name"]: b for b in pose["bones"]}
        if frame.keys() != bones.keys():
            raise ValueError("Pose bone names do not match rest rig")
        for key, bone in bones.items():
            if bone.get("parent") != frame[key].get("parent"):
                raise ValueError(f"{key}: changed parent")
            if mesh_signature(bone) != mesh_signature(frame[key]):
                raise ValueError(f"{key}: changed mesh/UV; requires geometry conversion")
        frames.append(frame)
    if loop:
        frames.append(frames[0])
    clips = {}
    for key, bone in bones.items():
        rotation, position = {}, {}
        for i, frame in enumerate(frames):
            t = str(round(seconds*i/max(1, len(frames)-1), 6))
            r = delta(frame[key].get("rotation", [0,0,0]), bone.get("rotation", [0,0,0]))
            # Bedrock pivots are model-space; translation channels are local.
            p = delta(frame[key].get("pivot", [0,0,0]), bone.get("pivot", [0,0,0]))
            parent = bone.get("parent")
            if parent:
                pd = delta(frame[parent].get("pivot", [0,0,0]), bones[parent].get("pivot", [0,0,0]))
                p = delta(p, pd)
            rotation[t], position[t] = r, p
        channels = {}
        if any(any(v) for v in rotation.values()): channels["rotation"] = rotation
        if any(any(v) for v in position.values()): channels["position"] = position
        if channels: clips[key] = channels
    return {"format_version": "1.8.0", "animations": {name: {
        "loop": loop, "animation_length": seconds, "bones": clips}}}
