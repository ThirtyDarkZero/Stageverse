# Dance moves from video

Rough motion capture from an ordinary video, for blocking choreography onto a StageVerse performer.

1. `track_dancer.py` finds every person with YOLOv8, keeps the chosen dancer (colour cue on the torso
   plus frame-to-frame continuity), and runs MediaPipe Pose on her crop only. Output: 33 3D landmarks
   per frame, plus an overlay video to check that it stayed on the right dancer.
2. `retarget_meshy.py` (Blender/bpy) turns those landmarks into bone rotations on a Meshy-rigged
   character, keeps the lower foot on the floor, smooths and loops the clip, and exports an FBX animation.
3. In Unreal: `unreal/Scripts/apply_dance.py` imports it onto the performer's skeleton and plays it on loop.

Environment: Python 3.11 with `mediapipe==0.10.14 opencv-python-headless ultralytics`; bpy 5.0.1 for step 2.

Limits: single camera, so depth is estimated; class videos with crowds, cuts and camera moves give rough
results (feet slide, hands have no fingers). For show quality, record each routine solo, full body,
locked-off camera, front view (side view as a bonus).

Clips:
- `A_ArizonaRae_Telephone`: "Telephone" choreography by Nakyung (1MILLION class video, 0:18.5-0:28.5).
  Rob says the choreographer gave permission (2026-11-24); keep her written OK on file.
