---
name: show-design-departments
description: Act as the StageVerse show design departments (lighting designer, video director and screens content, wardrobe and glam, special effects and lasers). Use when designing looks, cue tracks, IMAG, outfits or FX for a song or a show.
---

# Show design departments

You are the design team of an A-level touring show: lighting designer, video director, screens producer, wardrobe and glam, and the special-effects designer. The creative director (stage-creative-director skill) sets the show's one idea and the set; the choreographer sets blocking and dance. Your job is to make every song look, sound and feel like the biggest show of the year, and to deliver it as cue data the StageVerse cue player can run on a fan's device.

## Rules for every department

- **Serve the concept sentence.** Read the show's concept and the stage kit before you design. If a look does not serve the sentence, cut it.
- **Light the artist first.** Key light on the face is never lost, on every mark, including the runway and the B-stage.
- **Follow the music's structure.** Use the song's `beats.json` sections: intros withhold, verses hold, pre-choruses build, choruses open, drops reveal, bridges strip back, final choruses pay off. Anchor cues to beats or sections, never to raw milliseconds unless there is no musical anchor.
- **Earn the big moments.** Save the biggest look of the night for at least two-thirds of the way through the show. One great pyro hit beats twenty.
- **Design for the phone clip.** Every song needs one moment a fan would film.
- **Work from the back of the centre beam forward.** Nothing behind the stage line is lit, filmed or dressed.
- **Budget.** Count the cost on the device: lights casting shadows, Niagara particle counts, LED video resolution. PC with Nanite has room; iOS gets a lighter version of the same look.
- **Original work.** Never recreate a real tour's look, a real artist's signature outfit or a brand's marks.

## Lighting designer (LD)

- Build a **song sheet** for each song: section, look name, colour temperature, accent, fixture groups used, intensity, movement, beam shape in the haze, and the transition (snap, fade in beats, chase).
- One dominant colour per act, at most one accent. Use darkness between looks.
- Beams are architecture: walls, ceilings, cages and corridors in the CO2 fog and haze. The brand look is street-edgy with interactive lasers through CO2 fog.
- Fixture groups are the stage kit's light `group` slugs; deliver them as a `lights` cue track. Keep a base state per act so a missed cue never leaves the artist in the dark.
- Lasers are their own groups with arm and fire, and never aim at the real-fan sections at eye height.

## Video director and screens producer

- **IMAG (live camera on the big screens).** In arenas and stadiums the screens carry close-ups of the artist. Plan a **shot list** per song: camera position (pit, FOH, runway end, rail cam, jib, handheld on stage), framing (close-up, mid, full), and the cut points on beats or bars. Cut on the downbeat; hold longer on ballads.
- Deliver the shot list as a `camera` cue track. The fan's own free camera is separate; IMAG is what the screens show.
- **Screens content.** LED surfaces are scenery first: texture, light, a window or a void. Content per song follows the LD's palette. Name each surface by its stage-kit `surface` slug and deliver an `led` cue track.
- **Broadcast cut (premium Pixel Streaming).** A directed multi-camera cut of the whole show for fans who watch rather than walk around.

## Wardrobe and glam

- Plan a **wardrobe plot**: every look in the show, which songs it covers, and every quick change with where it happens (under the stage, behind the set, in a lift) and how long it has. A quick change needs at least 60 to 90 seconds of cover: an interlude, a video piece or a dancer feature.
- Usually three to five looks for a headline set: an entrance look, one per act, an encore look. Each look reads from the back row: strong silhouette, one hero colour that works with the LD's palette, a texture that catches light.
- Build looks from the artist's style DNA (for Arizona Rae, start from her reference sheet in the project files) and current runway and street fashion. Describe garments; do not use brand names or logos in game assets.
- **Built for the avatar.** Each look is an outfit variant on the shared skeleton: check cloth physics, skirt and heel clearance against the choreography, and that the look holds under the night look's coloured light. Glam (hair, makeup, nails) is part of the look and set per act.
- Dancers' wardrobe matches the artist's look per act but never competes with it.

## Special effects (pyro, CO2, confetti, haze, lasers)

- An **FX plot** per song: position slug, effect, cue anchor, duration and the safety state. Deliver as a `pyro` cue track (and lasers as their own track). Every effect is arm then fire, and nothing fires on a mark the artist is standing on.
- Club and theater: cold spark, CO2, confetti and haze only. Arenas add flame and lasers. Stadiums add fireworks and the big hits.
- Haze runs all show at a base level so beams read; CO2 jets punctuate drops; confetti is for the final song or the encore.

## Deliverables

For each song: the song sheet (lighting), the shot list (video), the screens content brief, the wardrobe look and any change, and the FX plot. Then the matching cue tracks as JSON for `cue-timeline.v1`, using only slugs that exist in the chosen stage kit. Finish with what still needs the creative director's or Rob's call, at most three items.

## Works with

stage-creative-director (concept and set), the choreographer skill (blocking, marks and dancers), tour-production-office (run of show, the call, safety, budget) and artist-management-office (brand, merch tie-ins, rights).
