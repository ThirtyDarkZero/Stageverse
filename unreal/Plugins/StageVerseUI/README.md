# StageVerse UI plugin

The front end: CommonUI root layout and screens, the brand style asset, sample show data, and the
laser and CO₂ controller that runs behind the menus.

- Approved look and flow: `docs/brand/stageverse-front-end.html` (open it in a browser; tabs for prototype, user flow, brand sheet).
- Build plan: "StageVerse Front-End Build Plan" doc in the project.

## What is in C++ (this plugin)

| Class | Job |
| --- | --- |
| `USVStyleAsset` | Every brand color, font and motion timing. Defaults match the brand sheet. |
| `USVUISettings` | Project Settings > Game > StageVerse UI: style asset, root layout class, screen classes, FX parameter collection, reduced motion. |
| `USVRootLayout` | Base for `WBP_RootLayout`: Menu, HUD and Modal stacks, glitch cut on every screen change, CO₂ flash. |
| `USVScreen` | Base for every screen: router id, laser mode, rail on/off, default focus. |
| `USVUISubsystem` | Router per local player: `ShowFrontEnd`, `GoTo`, `Back`, `OpenShow`, `JoinSelectedShow`, laser aim, `FireCO2`. |
| `ASVShowFXController` | Place in the front-end level. Eases the laser fan toward the cursor or stick, pulses on the BPM, fires CO₂ jets and boosts fog. |
| `USVUILibrary` | Sample shows, JSON parsing, poster colors, date and watcher formatting, Tonight hero pick. |

## Editor setup (Rob)

1. Copy this folder to `<Project>/Plugins/StageVerseUI`, regenerate project files, build. Enable CommonUI if the editor asks.
2. Project Settings > General > Game Viewport Client Class: `CommonGameViewportClient`.
3. Fonts (all free, OFL, from Google Fonts): Archivo (variable), Anton, UnifrakturMaguntia, Space Mono. Import into `/Game/UI/Fonts`, make one composite font each.
4. Create `DA_StageVerseStyle` (Data Asset > SVStyleAsset). Colors are already filled in; set the five fonts.
5. Create `MPC_StageVerseFX` with scalars `Glitch`, `CO2Flash`, `Beat`, and `PP_StreetGlitch` (RGB split, scanlines and grain scaled by `Glitch`; white lift by `CO2Flash`). Add it to the front-end post-process volume.
6. Create `WBP_RootLayout` (parent `SVRootLayout`) with an Overlay holding, bottom to top: a `CommonActivatableWidgetStack` named `MenuStack`, one named `HudStack`, one named `ModalStack`. Optional widget named `Rail` for the left rail. Keep the background transparent: the arena shows through.
7. Create screens with parent `SVScreen`: `WBP_Title`, `WBP_Tonight`, `WBP_Shows`, `WBP_ShowPage`, `WBP_DoorsOpen`, `WBP_LiveHUD`, `WBP_Studio`. Set `ScreenId` and `LaserMode` on each, and name the primary button `DefaultFocus`.
8. Project Settings > Game > StageVerse UI: set Style, Root Layout Class, FX Collection, and the Screens map (`Title`, `Tonight`, `Shows`, `ShowPage`, `DoorsOpen`, `LiveHUD`, `Studio`, ...).
9. In `L_FrontEnd`: place laser emitters (Niagara systems that read the user parameters `Spread`, `Aim`, `Tilt`, `Beat`, `Intensity`, `CO2`), two CO₂ jet systems, Exponential Height Fog with Volumetric Fog on, and one `SVShowFXController` pointing at them.
10. Front-end player controller, BeginPlay: `Get StageVerse UI subsystem > Show Front End (Self, "Title")`. Each tick (or on mouse move / right stick): `Set Laser Aim` with the cursor position divided by the viewport size. Bind A on empty fog and the CO₂ input action to `Fire CO2`.

## Rules the code keeps

- The primary action is always the default focus. B always goes back one level.
- Rail items clear the menu stack, so nothing is ever more than two levels deep.
- Reduced motion turns off the glitch cut, the strobe and the laser beat pulse.
